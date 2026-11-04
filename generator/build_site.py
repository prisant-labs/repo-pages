#!/usr/bin/env python3
"""
Build the repo-browser site for GitHub Pages.

Copies every published tracked file into the output folder at its own path,
adds the viewer from .github/site/, and writes site-data.json with each
file's size, last change and first add (from one `git log` pass), Markdown
front matter, and a map of renamed paths.

Uses only the Python standard library. Needs the full git history: in
GitHub Actions, check out with fetch-depth: 0.

Local usage:
    python3 .github/scripts/build_site.py --out _site
    python3 -m http.server 8000 --directory _site
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


SITE_DIR = Path(".github/site")
CONFIG_FILE = SITE_DIR / "config.json"
VIEWER_DIR = "_viewer"
DATA_FILE = "site-data.json"
RESERVED = {"index.html", DATA_FILE}
DATA_VERSION = 1

DEFAULT_EXCLUDE = [".github/**", "**/.DS_Store", "**/.gitkeep"]


# ── Globs ──


def glob_to_regex(pattern: str) -> re.Pattern[str]:
    """gitignore-style glob: ** spans folders, * and ? stay inside one."""
    out, i = "", 0
    while i < len(pattern):
        c = pattern[i]
        if pattern.startswith("**/", i):
            out += "(?:.*/)?"
            i += 3
        elif pattern.startswith("**", i):
            out += ".*"
            i += 2
        elif c == "*":
            out += "[^/]*"
            i += 1
        elif c == "?":
            out += "[^/]"
            i += 1
        else:
            out += re.escape(c)
            i += 1
    return re.compile("^" + out + "$")


def is_published(path: str, exclude: list[re.Pattern[str]], include_hidden: bool) -> bool:
    if not include_hidden and any(seg.startswith(".") for seg in path.split("/")):
        return False
    return not any(p.match(path) for p in exclude)


# ── Git ──


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-c", "core.quotepath=off", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result.stdout


def tracked_files(repo: Path) -> list[str]:
    return [p for p in git(repo, "ls-files", "-z").split("\0") if p]


def read_log(repo: Path) -> list[dict]:
    """Every commit, newest first, with its name-status changes."""
    raw = git(
        repo,
        "log",
        "-z",
        "-M",
        "--name-status",
        "--format=%x1e%H%x1f%h%x1f%an%x1f%aI%x1f%s%x1f",
    )
    commits = []
    for chunk in raw.split("\x1e"):
        if not chunk.strip("\0\n"):
            continue
        head, _, rest = chunk.rpartition("\x1f")
        sha, short, author, date, subject = head.split("\x1f", 4)
        tokens = [t for t in rest.lstrip("\0\n").split("\0")]
        changes, i = [], 0
        while i < len(tokens):
            status = tokens[i].strip("\n")
            if not status:
                i += 1
                continue
            if status[0] in "RC":
                changes.append((status[0], tokens[i + 1], tokens[i + 2]))
                i += 3
            else:
                changes.append((status[0], tokens[i + 1], None))
                i += 2
        utc = datetime.fromisoformat(date).astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        commits.append(
            {"sha": sha, "short": short, "author": author, "date": utc, "subject": subject, "changes": changes}
        )
    return commits


def history(files: list[str], commits: list[dict]) -> tuple[dict, dict, dict]:
    """
    Walk the log newest first. For each live path, the first commit that
    touches it is its last change; the first add found (following renames
    back) is its first add. Returns last, added (path -> commit index) and
    renames (old path -> live path).
    """
    live = set(files)
    alias = {p: p for p in files}  # path as it appears in older commits -> live path
    last: dict[str, int] = {}
    added: dict[str, int] = {}
    renames: dict[str, str] = {}
    for idx, c in enumerate(commits):
        for status, a, b in c["changes"]:
            if status == "R":
                cur = alias.pop(b, None)
                if cur is None:
                    continue
                last.setdefault(cur, idx)
                alias[a] = cur
                if a not in live:
                    renames.setdefault(a, cur)
            elif status == "C":
                cur = alias.pop(b, None)
                if cur is not None:
                    last.setdefault(cur, idx)
                    added.setdefault(cur, idx)
            else:
                cur = alias.get(a)
                if cur is None:
                    continue
                if status != "D":
                    last.setdefault(cur, idx)
                if status == "A":
                    added.setdefault(cur, idx)
                    del alias[a]  # older commits on this path belong to an earlier file
    return last, added, renames


# ── Front matter ──


def front_matter(text: str) -> dict:
    """Read description and tags from simple YAML front matter."""
    m = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n", text, re.S)
    if not m:
        return {}
    out: dict = {}
    key = None
    for line in m.group(1).splitlines():
        item = re.match(r"^\s+-\s+(.*)$", line)
        if item and key == "tags":
            out.setdefault("tags", []).append(unquote(item.group(1)))
            continue
        kv = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if not kv:
            continue
        key, value = kv.group(1), kv.group(2).strip()
        if key == "description" and value:
            out["description"] = unquote(value)
        elif key == "tags" and value:
            inner = value[1:-1] if value.startswith("[") and value.endswith("]") else value
            out["tags"] = [unquote(t) for t in inner.split(",") if t.strip()]
    return out


def unquote(s: str) -> str:
    s = s.strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in "\"'":
        return s[1:-1]
    return s


# ── Config ──


def repo_url(repo: Path) -> str:
    server = os.environ.get("GITHUB_SERVER_URL")
    name = os.environ.get("GITHUB_REPOSITORY")
    if server and name:
        return f"{server}/{name}"
    try:
        url = git(repo, "remote", "get-url", "origin").strip()
    except subprocess.CalledProcessError:
        return ""
    url = re.sub(r"^git@([^:]+):", r"https://\1/", url)
    return re.sub(r"\.git$", "", url)


def branch_name(repo: Path) -> str:
    return os.environ.get("GITHUB_REF_NAME") or git(repo, "rev-parse", "--abbrev-ref", "HEAD").strip()


def run_url() -> str:
    server, name, run = (os.environ.get(k) for k in ("GITHUB_SERVER_URL", "GITHUB_REPOSITORY", "GITHUB_RUN_ID"))
    return f"{server}/{name}/actions/runs/{run}" if server and name and run else ""


def load_config(repo: Path) -> dict:
    path = repo / CONFIG_FILE
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


# ── Build ──


def build(repo: Path, out: Path) -> dict:
    cfg = load_config(repo)
    exclude = [glob_to_regex(p) for p in DEFAULT_EXCLUDE + cfg.get("exclude", [])]
    files = sorted(p for p in tracked_files(repo) if is_published(p, exclude, cfg.get("includeHidden", False)))
    clash = [p for p in files if p in RESERVED or p.startswith(VIEWER_DIR + "/")]
    if clash:
        raise SystemExit(f"These files collide with the viewer's own paths: {', '.join(clash)}")

    commits = read_log(repo)
    last, added, renames = history(files, commits)

    # Keep only the commits a file points at, newest first, plus the recent ones.
    keep = sorted(set(last.values()) | set(added.values()) | set(range(min(len(commits), 50))))
    remap = {old: new for new, old in enumerate(keep)}
    head = 0 if commits else None

    file_rows = []
    for p in files:
        src = repo / p
        row: dict = {"path": p, "bytes": src.stat().st_size}
        l_idx = last.get(p, head)
        a_idx = added.get(p, l_idx)
        if l_idx is not None:
            row["last"] = remap[l_idx]
            row["added"] = remap[a_idx]
        if p.lower().endswith(".md"):
            row.update(front_matter(src.read_text(encoding="utf-8", errors="replace")))
        file_rows.append(row)

    data = {
        "version": DATA_VERSION,
        "config": {
            "title": cfg.get("title") or repo.resolve().name,
            "description": cfg.get("description", ""),
            "repoUrl": repo_url(repo),
            "branch": branch_name(repo),
            "builtAt": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "sha": commits[0]["sha"] if commits else "",
            "runUrl": run_url(),
            "sandboxHtml": bool(cfg.get("sandboxHtml", False)),
        },
        "commits": [
            [commits[i]["sha"], commits[i]["short"], commits[i]["author"], commits[i]["date"], commits[i]["subject"]]
            for i in keep
        ],
        "files": file_rows,
        "renames": {old: new for old, new in sorted(renames.items()) if new in set(files)},
    }

    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    for p in files:
        dest = out / p
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(repo / p, dest)
    shutil.copy2(repo / SITE_DIR / "index.html", out / "index.html")
    vendor = repo / SITE_DIR / "vendor"
    if vendor.is_dir():
        shutil.copytree(vendor, out / VIEWER_DIR / "vendor")
    (out / DATA_FILE).write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--repo", default=".", help="repository root (default: current folder)")
    parser.add_argument("--out", default="_site", help="output folder, replaced on each run (default: _site)")
    args = parser.parse_args(argv)
    data = build(Path(args.repo), Path(args.out))
    print(
        f"Built {len(data['files'])} files, {len(data['commits'])} commits, "
        f"{len(data['renames'])} renames into {args.out}/",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
