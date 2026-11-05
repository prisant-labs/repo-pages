# AGENTS.md - repo-pages

Instructions for any AI agent working in this repository. `CLAUDE.md` is a thin overlay on this file and does not repeat it.

## Project map

repo-pages turns a git repository into a static website where every file is readable. [docs/architecture.md](docs/architecture.md) explains how the parts fit together. Write the name as `repo-pages` in prose and code, and as "Repo Pages" in page titles and on the projects hub. Storage keys use the `rp.` prefix.

| Path | What it is |
|---|---|
| `viewer/index.html` | The whole interface, in one file. It is about 140 KB, so search it instead of reading it all |
| `viewer/vendor/` | Vendored `marked` and DOMPurify. Follow `viewer/vendor/README.md` to update them |
| `generator/` | `build_site.py` and its tests, using only the Python standard library |
| `tests/vendor-watch/` | A list of vendored versions for Dependabot. Nothing installs it |
| `templates/repo-pages.yml` | The workflow adopters copy into their own repository |
| `examples/` | The Initech parody sample, its commit script and `build_demo.py` |
| `tests/` | Browser checks and their runner |
| `docs/` | Features, settings spec, design notes, architecture and ideas |
| `_local/` | Gitignored working notes. Never commit it |

## Commands

```bash
python3 generator/test_build_site.py
python3 examples/build_demo.py --viewer viewer --generator generator/build_site.py
npm install --no-save --no-package-lock playwright
node tests/run_browser_checks.mjs
```

Use `python` on Windows if `python3` is not found. Set `RP_BROWSER_CHANNEL=msedge` or `chrome` to use an installed browser instead of downloading Chromium. All three steps must pass before a merge, and `.github/workflows/demo.yml` repeats them on every pull request. The "Protect main" ruleset blocks direct pushes to `main`, allows squash merges only, and requires the workflow's `build` check. Read the results rather than assuming them.

## Rules

- **Keep the repository neutral.** Name no company, organization or private repository, other than the fictional Initech sample and third-party projects. This covers code comments, docs, sample data, commit messages, branch names and pull request text.
- **Keep the demo honest.** The demo must come from the current viewer and generator. Do not commit the built page, because its dates change on every build.
- **Treat the demo as public.** Pushes to `main` publish it to <https://projects.prisantlabs.com/repo-pages/>. Anything in the viewer or `examples/` becomes readable by anyone.
- **Keep the viewer dependency-free.** It has no frontend build step and loads nothing from the network. Add third-party code only with a pinned version, a recorded hash and an entry in `THIRD-PARTY-NOTICES.md`. Keep the MIT and Lucide notice comments at the top of `viewer/index.html`, because built pages must carry them.
- **Respect the registry.** Add a reader setting through `KEYS` and `PREF_SPEC`, so it gets validation and Reset. Validate everything read from browser storage.
- **Respect the rejected list.** Do not add anything under "Deliberately left out" in `docs/settings-spec.md` without a new decision.
- **Check geometry.** The guide line must pass through the chevron center in every indent mode at every Tree text size, and the browser checks test this. `docs/design.md` has the formulas, so keep them in step with the tree CSS.

## Docs to change with the code

| When you change | Update |
|---|---|
| A reader-visible feature | `docs/features.md`, `CHANGELOG.md`, and `README.md` if the summary changes |
| A setting | `docs/settings-spec.md`, and `docs/design.md` for wording or measurements |
| The build, data contract or checks | `docs/architecture.md` |
| What gets published, or how untrusted files are handled | `SECURITY.md` and the README FAQ |
| A vendored library | `viewer/vendor/README.md`, `THIRD-PARTY-NOTICES.md` and `tests/vendor-watch/package.json` |
| Commands or repository rules | This file |
| The install steps, or an action version in `demo.yml` | `templates/repo-pages.yml`, and the README's Quick start and its agent prompts |

## Sample content

Follow the content rules in `examples/README.md`. The build stops if the commit script and `examples/initech/` disagree.
