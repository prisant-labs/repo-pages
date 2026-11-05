#!/usr/bin/env python3
"""
Build the repo-pages demo: one self-contained HTML file with sample content.

Replays a commit script over a sample corpus into a temporary git repo, runs
the real site generator on it, then folds the viewer, its two vendored
libraries, site-data.json and every published file into a single page. Open
the result straight from disk; nothing is fetched from the network.

The demo is always built from the current viewer, so it cannot drift from it.
Three lines in the viewer are swapped so files load from the page itself
instead of from the server. The build stops if any of them has changed.

Uses only the Python standard library and git.

Usage:
    python3 examples/build_demo.py \\
        --viewer viewer \\
        --generator generator/build_site.py
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_CORPUS = HERE / "initech"
DEFAULT_HISTORY = HERE / "initech-history.json"
DEFAULT_OUT = HERE.parent / "_site" / "index.html"

SITE_CONFIG = {
    "title": "Initech Intranet",
    "description": "Sample content for the repo-pages demo. A parody intranet; no real company is described.",
    "exclude": [],
    "includeHidden": False,
    "sandboxHtml": False,
}
REMOTE = "https://example.com/initech/intranet.git"

MIME = {
    "html": "text/html;charset=utf-8", "htm": "text/html;charset=utf-8", "svg": "image/svg+xml",
    "png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "gif": "image/gif", "webp": "image/webp",
    "pdf": "application/pdf", "zip": "application/zip", "json": "application/json;charset=utf-8",
}
TEXT = "text/plain;charset=utf-8"

# Each swap must match exactly once in the viewer. If one fails, the viewer
# changed: update the anchor here rather than loosening the check.
MAIN_SCRIPT = "<script>\n/* ───────────── Browser storage"
SWAPS = [
    ('const fileUrl = p => p.split("/").map(encodeURIComponent).join("/");',
     "const fileUrl = p => RP_EMBED.url(p);"),
    ("const ghUrl = (kind, p) => `${CONFIG.repoUrl}/${kind}/${CONFIG.branch}/${fileUrl(p)}`;",
     "const ghUrl = (kind, p) => `${CONFIG.repoUrl}/${kind}/${CONFIG.branch}/${RP_EMBED.enc(p)}`;"),
    ("${CONFIG.repoUrl}/commits/${CONFIG.branch}/${fileUrl(f.path)}",
     "${CONFIG.repoUrl}/commits/${CONFIG.branch}/${RP_EMBED.enc(f.path)}"),
]

# Serves site-data.json and every file from inside the page. Blob URLs are
# made on first use, so the iframe, images, PDF, Raw and New tab all work.
EMBED_JS = """window.RP_EMBED = (() => {
  const DATA = __DATA__;
  const FILES = __FILES__;
  const made = new Map();
  const enc = p => p.split("/").map(encodeURIComponent).join("/");
  function url(p) {
    if (made.has(p)) return made.get(p);
    const f = FILES[p];
    if (!f) return enc(p);
    const [type, kind, body] = f;
    const part = kind === "b" ? Uint8Array.from(atob(body), c => c.charCodeAt(0)) : body;
    const u = URL.createObjectURL(new Blob([part], { type }));
    made.set(p, u);
    return u;
  }
  const realFetch = window.fetch.bind(window);
  window.fetch = (input, init) => input === "site-data.json"
    ? Promise.resolve(new Response(JSON.stringify(DATA), { headers: { "Content-Type": "application/json" } }))
    : realFetch(input, init);
  return { url, enc };
})();"""


def git(repo: Path, *args: str, env: dict | None = None) -> None:
    subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "-c", "commit.gpgsign=false", "-c", "core.autocrlf=false", *args],
        cwd=repo, check=True, capture_output=True, env=env,
    )


def replay(corpus: Path, history: dict, repo: Path) -> int:
    """Commit the corpus into repo following the script. Returns the commit count."""
    commits = history["commits"]
    final = {p.relative_to(corpus).as_posix() for p in corpus.rglob("*") if p.is_file() and p.name != ".DS_Store"}

    # Renames map an early name to the final one.
    forward = {old: new for c in commits for old, new in c.get("rename", [])}

    def final_name(p: str) -> str:
        while p in forward:
            p = forward[p]
        return p

    # How many commits write each final file, so earlier writes differ from the last.
    writes: dict[str, int] = {}
    for c in commits:
        for p in c.get("add", []) + c.get("modify", []):
            writes[final_name(p)] = writes.get(final_name(p), 0) + 1
    explicit = {final_name(p) for c in commits for p in c.get("add", [])}
    initial = sorted(final - explicit)
    for p in initial:
        writes[p] = writes.get(p, 0) + 1
    missing = sorted(p for p in writes if p not in final)
    if missing:
        raise SystemExit(f"History names files that are not in the corpus: {', '.join(missing)}")

    done: dict[str, int] = {}

    def write(name_now: str) -> None:
        src = final_name(name_now)
        data = (corpus / src).read_bytes()
        done[src] = done.get(src, 0) + 1
        left = writes.get(src, 1) - done[src]
        if left:  # an earlier version: same text plus trailing newlines, so git sees a change
            if b"\0" in data:
                raise SystemExit(f"Binary file {src} can only be added once")
            data += b"\n" * left
        dest = repo / name_now
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)

    git(repo, "init", "-q", "-b", "main")
    git(repo, "remote", "add", "origin", REMOTE)
    now = int(time.time())
    imported: set[str] = set()
    all_prefixes = [x for c in commits for x in c.get("import", [])]

    def claimed(p: str) -> bool:
        return any(p.startswith(x) for x in all_prefixes)
    for i, c in enumerate(commits):
        # "import" takes the first-commit files under its folders; "initial" takes the rest.
        prefixes = c.get("import", [])
        for p in initial:
            if (any(p.startswith(x) for x in prefixes) or (c.get("initial") and not claimed(p))) and p not in imported:
                imported.add(p)
                write(p)
        for p in c.get("add", []) + c.get("modify", []):
            write(p)
        for p, text in c.get("create", {}).items():
            (repo / p).parent.mkdir(parents=True, exist_ok=True)
            (repo / p).write_text(text, encoding="utf-8")
        for old, new in c.get("rename", []):
            (repo / new).parent.mkdir(parents=True, exist_ok=True)
            git(repo, "mv", old, new)
        for p in c.get("delete", []):
            git(repo, "rm", "-q", p)
        name, email = history["authors"][c["author"]]
        when = f"@{now - c['days_ago'] * 86400 - 600 * (len(commits) - i)} +0000"
        env = {**os.environ, "GIT_AUTHOR_NAME": name, "GIT_AUTHOR_EMAIL": email, "GIT_AUTHOR_DATE": when,
               "GIT_COMMITTER_NAME": name, "GIT_COMMITTER_EMAIL": email, "GIT_COMMITTER_DATE": when}
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", c["message"], env=env)

    for p in final:
        if (repo / p).read_bytes() != (corpus / p).read_bytes():
            raise SystemExit(f"Replay left {p} different from the corpus")
    return len(commits)


def script_tag(js: str) -> str:
    return "<script>\n" + js.replace("</script", "<\\/script").replace("</SCRIPT", "<\\/SCRIPT") + "\n</script>\n"


def js_literal(value) -> str:
    # Valid JSON is a valid JS literal. Escaping "<" keeps "</script>" and "<!--" out of the page.
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")


def bundle(site: Path, out: Path) -> tuple[int, int]:
    html = (site / "index.html").read_text(encoding="utf-8")
    data = json.loads((site / "site-data.json").read_text(encoding="utf-8"))

    for old, new in SWAPS:
        if html.count(old) != 1:
            raise SystemExit(f"Viewer anchor not found exactly once, the viewer has changed:\n  {old}")
        html = html.replace(old, new)
    if html.count(MAIN_SCRIPT) != 1:
        raise SystemExit("Could not find the viewer's main <script> block")

    files = {}
    for row in data["files"]:
        p = row["path"]
        raw = (site / p).read_bytes()
        ext = p.rsplit(".", 1)[-1].lower() if "." in p.split("/")[-1] else ""
        mime = MIME.get(ext, TEXT)
        try:
            if b"\0" in raw or ext in ("png", "jpg", "jpeg", "gif", "webp", "pdf", "zip"):
                raise UnicodeDecodeError("utf-8", raw, 0, 1, "binary")
            files[p] = [mime, "t", raw.decode("utf-8")]
        except UnicodeDecodeError:
            files[p] = [mime, "b", base64.b64encode(raw).decode("ascii")]

    vendor = sorted((site / "_viewer" / "vendor").glob("*.js"))
    inject = "".join(script_tag(v.read_text(encoding="utf-8")) for v in vendor)
    inject += script_tag(EMBED_JS.replace("__DATA__", js_literal(data)).replace("__FILES__", js_literal(files)))
    html = html.replace(MAIN_SCRIPT, inject + MAIN_SCRIPT)
    # Pre-launch, like the projects hub. Remove the robots tag when the project is announced.
    html = html.replace("<title>Repo Pages</title>", f'<meta name="robots" content="noindex" />\n<title>{SITE_CONFIG["title"]} (demo)</title>', 1)

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    return len(files), len(data["commits"])


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--viewer", required=True, type=Path, help="folder with the viewer's index.html and vendor/")
    ap.add_argument("--generator", required=True, type=Path, help="path to build_site.py")
    ap.add_argument("--corpus", default=DEFAULT_CORPUS, type=Path)
    ap.add_argument("--history", default=DEFAULT_HISTORY, type=Path)
    ap.add_argument("--out", default=DEFAULT_OUT, type=Path)
    ap.add_argument("--keep", action="store_true", help="keep the temporary repo and site, and print where")
    args = ap.parse_args(argv)

    work = Path(tempfile.mkdtemp(prefix="repo-pages-demo-"))
    try:
        repo, site = work / "repo", work / "_site"
        repo.mkdir()
        n = replay(args.corpus, json.loads(args.history.read_text(encoding="utf-8")), repo)

        # The viewer goes in after the last commit: the generator reads it from disk, not from git.
        site_dir = repo / ".github" / "site"
        site_dir.mkdir(parents=True)
        shutil.copy2(args.viewer / "index.html", site_dir / "index.html")
        if (args.viewer / "vendor").is_dir():
            shutil.copytree(args.viewer / "vendor", site_dir / "vendor")
        (site_dir / "config.json").write_text(json.dumps(SITE_CONFIG, indent=2), encoding="utf-8")

        env = {k: v for k, v in os.environ.items() if not k.startswith("GITHUB_")}
        subprocess.run([sys.executable, str(args.generator.resolve()), "--repo", str(repo), "--out", str(site)],
                       check=True, env=env)
        files, commits = bundle(site, args.out)
        size = args.out.stat().st_size / 1024
        print(f"Replayed {n} commits. Wrote {args.out} ({files} files, {commits} commits, {size:.0f} KB)", file=sys.stderr)
        if args.keep:
            print(f"Kept {work}", file=sys.stderr)
    finally:
        if not args.keep:
            shutil.rmtree(work, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
