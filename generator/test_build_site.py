from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).resolve().parent / "build_site.py"

spec = importlib.util.spec_from_file_location("build_site", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = module
spec.loader.exec_module(module)

preflight_spec = importlib.util.spec_from_file_location("preflight", SCRIPT.parent / "preflight.py")
preflight = importlib.util.module_from_spec(preflight_spec)
assert preflight_spec and preflight_spec.loader
preflight_spec.loader.exec_module(preflight)


class GlobTests(unittest.TestCase):
    def match(self, pattern, path):
        return bool(module.glob_to_regex(pattern).match(path))

    def test_double_star_spans_folders(self):
        self.assertTrue(self.match("**/.DS_Store", ".DS_Store"))
        self.assertTrue(self.match("**/.DS_Store", "a/b/.DS_Store"))
        self.assertTrue(self.match("docs/**", "docs/a/b.md"))

    def test_single_star_stays_in_one_folder(self):
        self.assertTrue(self.match("docs/*.md", "docs/a.md"))
        self.assertFalse(self.match("docs/*.md", "docs/sub/a.md"))

    def test_hidden_segments_are_skipped_by_default(self):
        self.assertFalse(module.is_published(".claude/settings.json", [], False))
        self.assertFalse(module.is_published("a/.hidden/b.md", [], False))
        self.assertTrue(module.is_published("_unsorted/b.md", [], False))
        self.assertTrue(module.is_published(".claude/settings.json", [], True))


class FrontMatterTests(unittest.TestCase):
    def test_inline_tags_and_quoted_description(self):
        text = '---\ndescription: "A: quoted value"\ntags: [one, "two"]\n---\n# Title\n'
        self.assertEqual(module.front_matter(text), {"description": "A: quoted value", "tags": ["one", "two"]})

    def test_list_tags(self):
        text = "---\ntags:\n  - alpha\n  - beta\ntitle: x\n---\nbody"
        self.assertEqual(module.front_matter(text), {"tags": ["alpha", "beta"]})

    def test_no_front_matter(self):
        self.assertEqual(module.front_matter("# Just a heading\n"), {})


def run(repo, *args, env=None):
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, env=env)


def commit(repo, message, author, date):
    env = dict(
        os.environ,
        GIT_AUTHOR_NAME=author,
        GIT_AUTHOR_EMAIL="a@example.com",
        GIT_COMMITTER_NAME=author,
        GIT_COMMITTER_EMAIL="a@example.com",
        GIT_AUTHOR_DATE=date,
        GIT_COMMITTER_DATE=date,
    )
    run(repo, "add", "-A", env=env)
    run(repo, "commit", "-q", "-m", message, env=env)


class BuildTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name) / "repo"
        self.repo.mkdir()
        run(self.repo, "init", "-q", "-b", "main")
        (self.repo / ".github/site/vendor").mkdir(parents=True)
        (self.repo / ".github/site/index.html").write_text("<!doctype html><title>viewer</title>")
        (self.repo / ".github/site/vendor/lib.js").write_text("//")
        (self.repo / ".github/site/config.json").write_text(json.dumps({"title": "Test KB", "exclude": ["skip/**"]}))

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, path, text):
        p = self.repo / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)

    def build(self):
        out = Path(self.tmp.name) / "site"
        data = module.build(self.repo, out)
        return data, out

    def file(self, data, path):
        row = next(f for f in data["files"] if f["path"] == path)
        last, added = data["commits"][row["last"]], data["commits"][row["added"]]
        return row, last, added

    def test_authors_dates_and_renames(self):
        self.write("docs/a.md", "---\ndescription: First doc\n---\n# A\n")
        self.write("skip/hidden.md", "x")
        self.write("my notes/b c.txt", "spaces")
        commit(self.repo, "Add a", "Ann", "2026-01-01T10:00:00Z")

        self.write("docs/a.md", "---\ndescription: First doc\n---\n# A changed\n")
        commit(self.repo, "Edit a", "Bob", "2026-02-01T10:00:00Z")

        (self.repo / "guides").mkdir()
        run(self.repo, "mv", "docs/a.md", "guides/a.md")
        commit(self.repo, "Move a", "Cy", "2026-03-01T10:00:00Z")

        data, out = self.build()
        paths = [f["path"] for f in data["files"]]
        self.assertEqual(paths, ["guides/a.md", "my notes/b c.txt"])  # .github and skip/ are excluded

        row, last, added = self.file(data, "guides/a.md")
        self.assertEqual(row["description"], "First doc")
        self.assertEqual((last[2], last[4]), ("Cy", "Move a"))
        self.assertEqual((added[2], added[4]), ("Ann", "Add a"))  # followed back through the rename
        self.assertEqual(data["renames"], {"docs/a.md": "guides/a.md"})

        _, last, added = self.file(data, "my notes/b c.txt")
        self.assertEqual(last[4], "Add a")
        self.assertEqual(added[4], "Add a")

        self.assertEqual(data["config"]["title"], "Test KB")
        self.assertTrue((out / "guides/a.md").exists())
        self.assertTrue((out / "my notes/b c.txt").exists())
        self.assertTrue((out / "index.html").exists())
        self.assertTrue((out / "_viewer/vendor/lib.js").exists())
        self.assertFalse((out / "skip").exists())
        self.assertEqual(json.loads((out / "site-data.json").read_text())["version"], 1)

    def test_readded_path_counts_from_the_new_add(self):
        self.write("x.md", "one")
        commit(self.repo, "Add x", "Ann", "2026-01-01T10:00:00Z")
        (self.repo / "x.md").unlink()
        commit(self.repo, "Delete x", "Ann", "2026-01-02T10:00:00Z")
        self.write("x.md", "two")
        commit(self.repo, "Add x again", "Bob", "2026-01-03T10:00:00Z")

        data, _ = self.build()
        _, last, added = self.file(data, "x.md")
        self.assertEqual(added[4], "Add x again")
        self.assertEqual(last[4], "Add x again")

    def test_symlinks_are_not_published(self):
        outside = Path(self.tmp.name) / "outside.txt"
        outside.write_text("outside the repository")
        self.write("readme.md", "# Kept")
        run(self.repo, "config", "core.symlinks", "true")
        try:
            os.symlink(outside, self.repo / "link.txt")
        except OSError:
            self.skipTest("this machine cannot create symlinks")
        commit(self.repo, "Add a link", "Ann", "2026-01-01T10:00:00Z")
        data, out = self.build()
        self.assertEqual([f["path"] for f in data["files"]], ["readme.md"])
        self.assertFalse((out / "link.txt").exists())

    def test_reserved_paths_fail_the_build(self):
        self.write("index.html", "<p>clash</p>")
        commit(self.repo, "Add root index", "Ann", "2026-01-01T10:00:00Z")
        with self.assertRaises(SystemExit):
            self.build()


class ViewerAndConfigTests(unittest.TestCase):
    """The action keeps its viewer outside the repository, and adopters keep only a config."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name) / "repo"
        self.repo.mkdir()
        run(self.repo, "init", "-q", "-b", "main")
        self.viewer = Path(self.tmp.name) / "elsewhere"
        (self.viewer / "vendor").mkdir(parents=True)
        (self.viewer / "index.html").write_text("<!doctype html><title>outside</title>")
        (self.viewer / "vendor/lib.js").write_text("//")
        self.write("a.md", "# A\n")
        commit(self.repo, "Add a", "Ann", "2026-01-01T10:00:00Z")

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, path, text):
        p = self.repo / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)

    def build_outside(self):
        out = Path(self.tmp.name) / "site"
        return module.build(self.repo, out, self.viewer), out

    def test_viewer_outside_the_repository(self):
        data, out = self.build_outside()
        self.assertIn("outside", (out / "index.html").read_text())
        self.assertTrue((out / "_viewer/vendor/lib.js").exists())
        self.assertEqual([f["path"] for f in data["files"]], ["a.md"])

    def test_config_is_optional(self):
        data, _ = self.build_outside()
        self.assertEqual(data["config"]["title"], "repo")

    def test_config_at_the_public_location_is_read_and_not_published(self):
        self.write(".github/repo-pages.json", json.dumps({"title": "Mine", "exclude": ["a.md"]}))
        self.write("b.md", "# B\n")
        commit(self.repo, "Add config", "Ann", "2026-01-02T10:00:00Z")
        data, out = self.build_outside()
        self.assertEqual(data["config"]["title"], "Mine")
        self.assertEqual([f["path"] for f in data["files"]], ["b.md"])
        self.assertFalse((out / ".github").exists())

    def test_invalid_config_names_the_file(self):
        self.write(".github/repo-pages.json", "{not json")
        with self.assertRaises(SystemExit) as caught:
            self.build_outside()
        self.assertIn(".github/repo-pages.json", str(caught.exception))

    def config_with_hidden_file(self, cfg):
        self.write(".hidden-note.txt", "tracked dotfile\n")
        if cfg is not None:
            self.write(".github/repo-pages.json", json.dumps(cfg))
        commit(self.repo, "Add a dotfile", "Ann", "2026-01-02T10:00:00Z")

    def test_hidden_files_stay_out_by_default_and_with_false(self):
        for cfg in (None, {"includeHidden": False}):
            with self.subTest(cfg=cfg):
                self.config_with_hidden_file(cfg)
                data, out = self.build_outside()
                self.assertNotIn(".hidden-note.txt", [f["path"] for f in data["files"]])
                self.assertFalse((out / ".hidden-note.txt").exists())

    def test_hidden_files_are_published_with_true(self):
        self.config_with_hidden_file({"includeHidden": True})
        data, out = self.build_outside()
        self.assertIn(".hidden-note.txt", [f["path"] for f in data["files"]])
        self.assertTrue((out / ".hidden-note.txt").exists())

    def test_a_string_false_is_refused_before_the_output_is_touched(self):
        self.config_with_hidden_file({"includeHidden": "false"})
        out = Path(self.tmp.name) / "site"
        out.mkdir()
        (out / "previous.txt").write_text("earlier build")
        with self.assertRaises(SystemExit) as caught:
            module.build(self.repo, out, self.viewer)
        message = str(caught.exception)
        self.assertIn(".github/repo-pages.json", message)
        self.assertIn('"includeHidden" must be true or false', message)
        self.assertTrue((out / "previous.txt").exists())
        self.assertFalse((out / ".hidden-note.txt").exists())

    def test_wrong_types_name_the_key(self):
        cases = {
            "sandboxHtml": {"sandboxHtml": "no"},
            "exclude": {"exclude": "drafts/**"},
            "title": {"title": 7},
        }
        for key, cfg in cases.items():
            with self.subTest(key=key):
                self.write(".github/repo-pages.json", json.dumps(cfg))
                with self.assertRaises(SystemExit) as caught:
                    self.build_outside()
                self.assertIn(f'"{key}" must be', str(caught.exception))

    def test_config_must_be_an_object(self):
        self.write(".github/repo-pages.json", "[]")
        with self.assertRaises(SystemExit) as caught:
            self.build_outside()
        self.assertIn("must hold a JSON object", str(caught.exception))

    def test_missing_viewer_is_a_clear_error(self):
        with self.assertRaises(SystemExit) as caught:
            module.build(self.repo, Path(self.tmp.name) / "site")
        self.assertIn("No viewer found", str(caught.exception))

    def test_summary_lists_files_and_authors_and_escapes_them(self):
        data = {
            "files": [{"path": "a.md"}, {"path": "docs/x<b>.md"}],
            "commits": [["sha", "short", "A <script>", "date", "subject"]],
        }
        text = module.summary(data)
        self.assertIn("published 2 files", text)
        self.assertIn("| docs/ | 1 |", text)
        self.assertIn("docs/x&lt;b&gt;.md", text)
        self.assertNotIn("<b>", text)
        self.assertNotIn("<script>", text)
        self.assertIn("... and 1 more", module.summary(data, limit=1))


class PreflightTests(unittest.TestCase):
    REPO = "owner/name"
    GOOD_ENV = {"ACTIONS_ID_TOKEN_REQUEST_URL": "https://token"}

    def run_check(self, private=False, pages=(200, {"build_type": "workflow"}), repo_status=200, env=None, allow=False):
        def fetch(path):
            return pages if path.endswith("/pages") else (repo_status, {"private": private})

        return preflight.check(fetch, self.REPO, "https://github.com", self.GOOD_ENV if env is None else env, allow)

    def test_a_ready_public_repository_passes(self):
        self.assertEqual(self.run_check(), [])

    def test_a_private_repository_is_refused(self):
        errors = self.run_check(private=True)
        self.assertEqual(len(errors), 1)
        self.assertIn("private", errors[0])
        self.assertIn("allow-private-repository", errors[0])

    def test_a_private_repository_can_be_allowed(self):
        self.assertEqual(self.run_check(private=True, allow=True), [])

    def test_unknown_visibility_is_refused(self):
        self.assertIn("visibility is unknown", self.run_check(repo_status=500)[0])

    def test_pages_turned_off_says_how_to_turn_it_on(self):
        error = self.run_check(pages=(404, {}))[0]
        self.assertIn("https://github.com/owner/name/settings/pages", error)
        self.assertIn('gh api -X POST "repos/owner/name/pages" -f build_type=workflow', error)

    def test_pages_from_a_branch_is_refused(self):
        self.assertIn("publishing from a branch", self.run_check(pages=(200, {"build_type": "legacy"}))[0])

    def test_missing_permissions_are_named(self):
        self.assertIn("id-token: write", self.run_check(env={})[0])
        self.assertIn("pages: write", self.run_check(pages=(403, {}))[0])


MISSING = object()


class PrivateSiteTests(unittest.TestCase):
    """What decides publishing is whether the site is public, not whether the repository is private."""

    REPO = "owner/name"
    SETTINGS = "https://github.com/owner/name/settings/pages"
    ENV = {"ACTIONS_ID_TOKEN_REQUEST_URL": "https://token"}
    VISIBILITIES = ("public", "private", "internal")

    def fake_fetch(self, visibility, public=MISSING, pages_status=200, calls=None):
        pages = {"build_type": "workflow"}
        if public is not MISSING:
            pages["public"] = public
        repo = {"private": visibility != "public", "visibility": visibility}

        def fetch(path):
            if calls is not None:
                calls.append(path)
            if path.endswith("/pages"):
                return pages_status, pages if pages_status == 200 else {}
            return 200, repo

        return fetch

    def run_check(self, visibility="private", public=MISSING, allow=False, require=False, pages_status=200):
        fetch = self.fake_fetch(visibility, public, pages_status)
        return preflight.check(fetch, self.REPO, "https://github.com", self.ENV, allow, require_private=require)

    def test_a_public_repository_publishes_whatever_the_site_reports(self):
        for public in (True, False, MISSING, "false", None):
            with self.subTest(public=public):
                self.assertEqual(self.run_check("public", public), [])

    def test_a_private_site_publishes_without_a_flag(self):
        for visibility in ("private", "internal"):
            with self.subTest(visibility=visibility):
                self.assertEqual(self.run_check(visibility, public=False), [])

    def test_a_public_site_of_a_private_repository_is_refused(self):
        for visibility in ("private", "internal"):
            with self.subTest(visibility=visibility):
                errors = self.run_check(visibility, public=True)
                self.assertEqual(len(errors), 1)
                self.assertIn("Its GitHub Pages site is public", errors[0])
                self.assertIn(self.SETTINGS, errors[0])
                self.assertIn('set allow-private-repository to "true"', errors[0])

    def test_a_missing_or_odd_public_value_counts_as_public(self):
        for public in (MISSING, None, "false", 0, "no"):
            with self.subTest(public=public):
                errors = self.run_check("private", public)
                self.assertEqual(len(errors), 1)
                self.assertIn("did not report whether", errors[0])
                self.assertIn("treats it as public", errors[0])
                self.assertIn('set allow-private-repository to "true"', errors[0])

    def test_allow_private_repository_still_publishes_a_public_site(self):
        for visibility in ("private", "internal"):
            for public in (True, MISSING):
                with self.subTest(visibility=visibility, public=public):
                    self.assertEqual(self.run_check(visibility, public, allow=True), [])

    def test_an_internal_repository_says_it_counts_as_private(self):
        for public in (True, MISSING):
            with self.subTest(public=public):
                error = self.run_check("internal", public)[0]
                self.assertIn("This repository has internal visibility, which GitHub counts as private.", error)
        self.assertNotIn("internal", self.run_check("private", True)[0])

    def test_require_private_site_with_every_visibility_and_public_value(self):
        for visibility in self.VISIBILITIES:
            for public in (True, False, MISSING):
                with self.subTest(visibility=visibility, public=public):
                    errors = self.run_check(visibility, public, require=True)
                    if public is False:
                        self.assertEqual(errors, [])
                        continue
                    self.assertEqual(len(errors), 1)
                    self.assertIn('require-private-site is "true"', errors[0])
                    if visibility == "public":
                        self.assertIn("a site from a public repository is always public", errors[0])
                    elif public is True:
                        self.assertIn("GitHub Pages site is public", errors[0])
                        self.assertIn(self.SETTINGS, errors[0])
                        self.assertIn('gh api -X PUT "repos/owner/name/pages" -F public=false', errors[0])
                        self.assertIn("GitHub Enterprise Cloud", errors[0])
                        self.assertIn("remove require-private-site", errors[0])
                    else:
                        self.assertIn("did not report whether", errors[0])
                        self.assertIn("remove require-private-site", errors[0])

    def test_allow_private_repository_does_not_override_require_private_site(self):
        for visibility in ("private", "internal"):
            for public in (True, MISSING):
                with self.subTest(visibility=visibility, public=public):
                    errors = self.run_check(visibility, public, allow=True, require=True)
                    self.assertEqual(len(errors), 1)
                    self.assertIn("require-private-site", errors[0])
                    self.assertNotIn("allow-private-repository", errors[0])
        self.assertEqual(self.run_check("private", False, allow=True, require=True), [])

    def test_unreadable_pages_settings_still_stop_the_run_with_their_own_fix(self):
        expected = {404: "not turned on", 403: "pages: write", 500: "HTTP 500", 0: "HTTP 0"}
        for status, fix in expected.items():
            for require in (False, True):
                with self.subTest(status=status, require=require):
                    errors = self.run_check("private", pages_status=status, require=require)
                    self.assertEqual(len(errors), 1)
                    self.assertIn(fix, errors[0])

    def test_the_pages_settings_are_read_once(self):
        calls = []
        preflight.check(self.fake_fetch("private", False, calls=calls), self.REPO, "https://github.com", self.ENV, False)
        self.assertEqual(calls, ["repos/owner/name", "repos/owner/name/pages"])


class PreflightMainTests(unittest.TestCase):
    """CI runs the action in build-only mode, so preflight never runs there. These cover the wiring."""

    root = SCRIPT.parent.parent

    def run_main(self, public, require=None, allow=None):
        pages = {"build_type": "workflow", "public": public}

        def fetch(path):
            return (200, pages) if path.endswith("/pages") else (200, {"private": True, "visibility": "private"})

        env = {"GITHUB_REPOSITORY": "owner/name", "ACTIONS_ID_TOKEN_REQUEST_URL": "https://token"}
        if require is not None:
            env["REPO_PAGES_REQUIRE_PRIVATE_SITE"] = require
        if allow is not None:
            env["REPO_PAGES_ALLOW_PRIVATE"] = allow
        out = io.StringIO()
        with mock.patch.dict(os.environ, env, clear=True), \
                mock.patch.object(preflight, "github_fetch", return_value=fetch), \
                contextlib.redirect_stdout(out):
            code = preflight.main()
        return code, out.getvalue()

    def test_the_action_passes_require_private_site_to_preflight(self):
        text = (self.root / "action.yml").read_text(encoding="utf-8")
        self.assertRegex(text, r"(?m)^  require-private-site:\n    description: .+\n    default: 'false'$")
        self.assertIn("REPO_PAGES_REQUIRE_PRIVATE_SITE: ${{ inputs.require-private-site }}", text)

    def test_main_reads_require_private_site(self):
        self.assertEqual(self.run_main(public=False), (0, ""))
        self.assertEqual(self.run_main(public=False, require="false")[0], 0)
        for value in ("true", " TRUE "):
            with self.subTest(value=value):
                code, out = self.run_main(public=True, require=value, allow="true")
                self.assertEqual(code, 1)
                self.assertIn('::error title=Repo Pages::require-private-site is "true"', out)

    def test_an_unrecognized_require_private_site_value_stops_the_run(self):
        for value in ("yes", "ture", "1"):
            with self.subTest(value=value):
                code, out = self.run_main(public=False, require=value)
                self.assertEqual(code, 1)
                self.assertIn(f'require-private-site must be "true" or "false", not "{value}"', out)


class RepositoryTests(unittest.TestCase):
    root = SCRIPT.parent.parent

    def test_copied_files_carry_the_license_notice(self):
        line = next(l for l in (self.root / "LICENSE").read_text(encoding="utf-8").splitlines() if l.startswith("Copyright"))
        for path in ("viewer/index.html", "generator/build_site.py"):
            self.assertIn(line, (self.root / path).read_text(encoding="utf-8"), path)

    def test_action_keeps_history_and_hidden_files(self):
        """A shallow clone breaks authors and dates, and the upload action drops dotfiles by default."""
        text = (self.root / "action.yml").read_text(encoding="utf-8")
        self.assertIn("fetch-depth: 0", text)
        self.assertIn("persist-credentials: false", text)
        self.assertIn("include-hidden-files: true", text)

    def test_action_pins_its_inner_actions_to_commit_shas(self):
        """Adopters inherit whatever the action runs, so a moved tag must not change it."""
        text = (self.root / "action.yml").read_text(encoding="utf-8")
        uses = re.findall(r"uses: (\S+)", text)
        self.assertGreaterEqual(len(uses), 3)
        for ref in uses:
            self.assertRegex(ref, r"^[\w-]+/[\w-]+@[0-9a-f]{40}$")

    def test_template_carries_what_a_composite_action_cannot(self):
        """A composite action cannot set permissions or an environment, so the workflow must."""
        text = (self.root / "templates/repo-pages.yml").read_text(encoding="utf-8")
        for needed in ("pages: write", "id-token: write", "name: github-pages", "prisant-labs/repo-pages@v1"):
            self.assertIn(needed, text)

    def test_readme_install_commands_match_the_template_and_action(self):
        """The README is the install path, so its URL and every input it names must exist."""
        readme = (self.root / "README.md").read_text(encoding="utf-8")
        action = (self.root / "action.yml").read_text(encoding="utf-8")
        self.assertIn("repo-pages/v1/templates/repo-pages.yml", readme)
        for name in re.findall(r"^\| `([\w-]+)` \| `[^`]+` \| ", readme, flags=re.M):
            self.assertRegex(action, rf"(?m)^  {re.escape(name)}:$")

    def test_vendor_watch_matches_the_vendored_files(self):
        """A Dependabot bump to the watch list fails here until the library itself is updated."""
        watch = json.loads((self.root / "tests/vendor-watch/package.json").read_text(encoding="utf-8"))["dependencies"]
        vendor = self.root / "viewer/vendor"
        self.assertTrue((vendor / f"marked-{watch['marked']}.umd.js").exists())
        self.assertTrue((vendor / f"purify-{watch['dompurify']}.min.js").exists())


if __name__ == "__main__":
    unittest.main()
