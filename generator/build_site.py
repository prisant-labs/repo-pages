#!/usr/bin/env python3
# Repo Pages: https://github.com/prisant-labs/repo-pages
#
# MIT License
#
# Copyright (c) 2026 Prisant Labs / Jonathan Prisant
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Build the repo-pages site for GitHub Pages.

Copies every published tracked file into the output folder at its own path,
adds the viewer, and writes site-data.json with each file's size, last change
and first add (from one `git log` pass), Markdown front matter, and a map of
renamed paths. It also writes _viewer/refs.json, which lists for each file the
Markdown documents that link to it. The viewer comes from --viewer, or from
.github/site/ without it.

Uses only the Python standard library. Needs the full git history: in
GitHub Actions, check out with fetch-depth: 0.

Local usage, from the repository you want to publish:
    python3 path/to/repo-pages/generator/build_site.py --viewer path/to/repo-pages/viewer --out _site
    python3 -m http.server 8000 --directory _site
"""

from __future__ import annotations

import argparse
import bisect
import html
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path


SITE_DIR = Path(".github/site")
CONFIG_FILES = [Path(".github/repo-pages.json"), SITE_DIR / "config.json"]
VIEWER_DIR = "_viewer"
DATA_FILE = "site-data.json"
RESERVED = {"index.html", DATA_FILE}
DATA_VERSION = 1

DEFAULT_EXCLUDE = [".github/**", "**/.DS_Store", "**/.gitkeep"]
REGULAR_MODES = {"100644", "100755"}


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


def ls_files(repo: Path) -> list[tuple[str, str]]:
    """Every tracked path with its git mode, symlinks and submodules included."""
    rows = []
    for row in git(repo, "ls-files", "-s", "-z").split("\0"):
        if row:
            meta, path = row.split("\t", 1)
            rows.append((meta.split(" ", 1)[0], path))
    return rows


def tracked_files(repo: Path, rows: list[tuple[str, str]] | None = None) -> list[str]:
    """Tracked regular files only.

    A symlink is skipped because copying it would publish its target, which can
    be outside the repository or a file that `exclude` hides. A submodule is
    skipped because it has no content of its own here.
    """
    return [path for mode, path in (ls_files(repo) if rows is None else rows) if mode in REGULAR_MODES]


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


# ── Markdown scan ──
#
# One pass over a Markdown file finds its headings and its inline links and images,
# skipping front matter, fenced code and code spans. Referenced by uses it now; search
# and the agent index can reuse it. A browser check compares its links with the links
# marked renders on the sample, so the two cannot drift apart unnoticed.

FRONT_MATTER = re.compile(r"^---\r?\n[\s\S]*?\r?\n---\r?\n?")
FENCE = re.compile(r"^\s*(`{3,}|~{3,})(.*)$")  # any indent: a fence in a list item is code too
ATX = re.compile(r"^ {0,3}(#{1,6})(?:[ \t]+(.*?))?(?:[ \t]+#+)?[ \t]*$")
LIST_ITEM = re.compile(r"^\s*(?:[-*+]|\d{1,9}[.)])\s+")
TABLE_ROW = re.compile(r"^\s{0,3}\|")
TABLE_RULE = re.compile(r"^\s*\|?\s*:?-{1,}:?\s*(?:\|\s*:?-{1,}:?\s*)*\|?\s*$")
SCHEME = re.compile(r"^[a-z][a-z0-9+.-]*:", re.I)
SCAN_LINE_CHARS = 10_000  # a hostile file cannot stall the build with one huge line
SCAN_BLOCK_CHARS = 20_000  # nor with a paragraph of many long lines
DEST_CHARS = 2_000  # a link destination or title longer than this is not read
EXCERPT_CHARS = 160


def code_spans(s: str) -> list[tuple[int, int]]:
    """Ranges of inline code spans: a run of backticks closed by a run of the same length."""
    return [m.span() for m in re.finditer(r"(?<!`)(`+)(?!`).{0,2000}?(?<!`)\1(?!`)", s, re.S)]


def in_spans(spans: list[tuple[int, int]], i: int) -> bool:
    """Whether i falls inside one of the sorted, non-overlapping spans."""
    k = bisect.bisect_right(spans, (i, float("inf"))) - 1
    return k >= 0 and spans[k][0] <= i < spans[k][1]


def bracket_pairs(s: str) -> dict[int, int]:
    """For each [ that is closed, the index of its ]. One pass, so hostile text stays linear."""
    stack: list[int] = []
    pairs: dict[int, int] = {}
    j = 0
    while j < len(s):
        c = s[j]
        if c == "\\":
            j += 2
            continue
        if c == "[":
            stack.append(j)
        elif c == "]" and stack:
            pairs[stack.pop()] = j
        j += 1
    return pairs


def link_destination(s: str, i: int) -> tuple[str, int] | None:
    """Read `(dest "title")` starting at the ( at i. Returns the destination and the index after )."""
    limit = min(len(s), i + DEST_CHARS)
    j = i + 1
    while j < limit and s[j] in " \t":
        j += 1
    if j < limit and s[j] == "<":
        end = s.find(">", j, limit)
        if end < 0 or "\n" in s[j:end]:
            return None
        dest, j = s[j + 1:end], end + 1
    else:
        start, depth = j, 0
        while j < limit and not s[j].isspace():
            c = s[j]
            if c == "\\" and j + 1 < limit:
                j += 2
                continue
            if c == "(":
                depth += 1
            elif c == ")":
                if depth == 0:
                    break
                depth -= 1
            j += 1
        dest = s[start:j]
    while j < limit and s[j] in " \t":
        j += 1
    if j < limit and s[j] in "\"'(":
        close = {"\"": "\"", "'": "'", "(": ")"}[s[j]]
        end = s.find(close, j + 1, limit)
        if end < 0:
            return None
        j = end + 1
        while j < limit and s[j] in " \t":
            j += 1
    if j >= limit or s[j] != ")":
        return None
    return re.sub(r"\\([!-/:-@\[-`{-~])", r"\1", dest), j + 1


def inline_links(s: str, nested: bool = True) -> list[dict]:
    """Inline links and images in one block, in order.

    An image inside a link label, the usual badge pattern, counts too. Only one level is
    read, so deeply nested brackets cannot exhaust the stack.
    """
    code = code_spans(s)
    pairs = bracket_pairs(s)
    found, i = [], 0
    while True:
        i = s.find("[", i)
        if i < 0:
            return found
        end = pairs.get(i, -1)
        if (i and s[i - 1] == "\\") or in_spans(code, i) or end < 0 or end + 1 >= len(s) or s[end + 1] != "(":
            i += 1
            continue
        got = link_destination(s, end + 1)
        if not got:
            i += 1
            continue
        dest, after = got
        image = i > 0 and s[i - 1] == "!" and not (i > 1 and s[i - 2] == "\\")
        label = s[i + 1:end]
        found.append({"start": i - 1 if image else i, "end": after, "label": label, "dest": dest, "image": image})
        if nested:
            found.extend(dict(inner, start=inner["start"] + i + 1, end=inner["end"] + i + 1) for inner in inline_links(label, False))
        i = after


HTML_LINK = re.compile(r"<(a|img)\b[^>]{0,500}?\s(href|src)\s*=\s*(?:\"([^\"]{0,2000})\"|'([^']{0,2000})'|([^\s\"'>]{1,2000}))", re.I)
HTML_ALT = re.compile(r"\salt\s*=\s*(?:\"([^\"]{0,500})\"|'([^']{0,500})')", re.I)


def html_links(s: str) -> list[dict]:
    """<a href> and <img src> written as HTML inside Markdown, as READMEs often do for images."""
    code = code_spans(s)
    found = []
    for m in HTML_LINK.finditer(s):
        tag, attr = m.group(1).lower(), m.group(2).lower()
        if (tag == "a") != (attr == "href") or in_spans(code, m.start()):
            continue
        value = next(v for v in m.group(3, 4, 5) if v is not None)
        found.append({"start": m.start(), "end": m.end(), "label": "", "dest": html.unescape(value), "image": tag == "img"})
    return found


def img_alt(m: re.Match) -> str:
    """An HTML image tag as its alt text, so an excerpt around a screenshot is not empty."""
    alt = HTML_ALT.search(m.group(0))
    return f" {html.unescape(alt.group(1) or alt.group(2) or '')} " if alt else ""


def plain_text(s: str, nested: bool = True) -> str:
    """Markdown syntax removed, for headings and excerpts. Link labels and image alt text are kept."""
    out, i = [], 0
    for link in inline_links(s, False):
        if link["start"] < i:
            continue
        out.append(s[i:link["start"]])
        out.append(plain_text(link["label"], False) if nested else link["label"])
        i = link["end"]
    out.append(s[i:])
    text = "".join(out)
    text = re.sub(r"<img\b[^>]{0,500}>", img_alt, text, flags=re.I)
    text = re.sub(r"<[^>\n]{0,500}>", "", text)
    text = re.sub(r"(?<!\w)[*_~]+|[*_~]+(?!\w)", "", text)
    text = text.replace("`", "")
    text = re.sub(r"\\([!-/:-@\[-`{-~])", r"\1", text)
    return " ".join(text.split())


def scan_markdown(text: str) -> dict:
    """Headings and inline links of a Markdown file.

    headings: [{"level", "text", "line"}], in order.
    links: [{"dest", "image", "heading", "block", "start", "line"}], where heading is the
    index of the nearest heading above the link (-1 for none), block is the raw text of
    the paragraph, list item, table row or heading that holds it, start is the link's
    offset in block, and line is the file line it sits on.
    """
    fm = FRONT_MATTER.match(text)
    offset = text[:fm.end()].count("\n") if fm else 0
    lines = text[fm.end():].splitlines() if fm else text.splitlines()
    headings: list[dict] = []
    links: list[dict] = []
    block: list[str] = []
    block_line = 0
    fence: str | None = None
    mermaid = False

    def flush() -> None:
        if block:
            raw = "\n".join(block)[:SCAN_BLOCK_CHARS]
            found = sorted(inline_links(raw) + html_links(raw), key=lambda x: x["start"])
            breaks = [i for i, c in enumerate(raw) if c == "\n"] if found else []
            links.extend({"dest": x["dest"], "image": x["image"], "heading": len(headings) - 1, "block": raw,
                          "start": x["start"], "line": block_line + bisect.bisect_left(breaks, x["start"])}
                         for x in found)
            block.clear()

    def add(text: str, n: int) -> None:
        nonlocal block_line
        if not block:
            block_line = n
        block.append(text)

    for n, line in enumerate(lines, start=offset + 1):
        line = line[:SCAN_LINE_CHARS]
        if fence:
            stripped = line.strip()
            if stripped.startswith(fence[0] * len(fence)) and not stripped.strip(fence[0]):
                fence = None
            continue
        f = FENCE.match(line)
        if f and not (f.group(1)[0] == "`" and "`" in f.group(2)):
            flush()
            fence = f.group(1)
            mermaid = mermaid or f.group(2).strip().lower().startswith("mermaid")
            continue
        if not line.strip():
            flush()
            continue
        h = ATX.match(line)
        if h:
            flush()
            headings.append({"level": len(h.group(1)), "text": plain_text(h.group(2) or ""), "line": n})
            add(h.group(2) or "", n)
            flush()
            continue
        if TABLE_ROW.match(line):
            flush()
            if not TABLE_RULE.match(line):
                add(line, n)
                flush()
            continue
        if LIST_ITEM.match(line):
            flush()
        add(line, n)
    flush()
    return {"headings": headings, "links": links, "mermaid": mermaid}


def excerpt(block: str, start: int) -> str:
    """About EXCERPT_CHARS of plain text from the block, centered on the link that starts at start."""
    mark = "\x01"
    lo = max(0, start - 1000)  # only the text near the link, however long the block
    raw = block[lo:start] + mark + block[start:start + 1000]
    if TABLE_ROW.match(raw):
        raw = " | ".join(c.strip() for c in raw.strip().strip("|").split("|"))
    raw = LIST_ITEM.sub("", raw, count=1)
    raw = re.sub(r"^\s{0,3}>\s?", "", raw, flags=re.M)
    text = plain_text(raw)
    at = max(text.find(mark), 0)
    text = text.replace(mark, "")
    if len(text) <= EXCERPT_CHARS:
        return text.strip()
    lo = max(0, min(at - EXCERPT_CHARS // 2, len(text) - EXCERPT_CHARS))
    hi = lo + EXCERPT_CHARS
    if lo:
        lo = text.find(" ", lo) + 1 or lo
    if hi < len(text):
        hi = text.rfind(" ", lo, hi) if text.rfind(" ", lo, hi) > lo else hi
    return ("… " if lo else "") + text[lo:hi].strip() + (" …" if hi < len(text) else "")


def resolve_rel(base: str, href: str) -> str:
    """The viewer's resolveRel: join href to the folder base, following . and .."""
    parts = [] if href.startswith("/") else (base.split("/") if base else [])
    for seg in href.split("/"):
        if seg == "..":
            if parts:
                parts.pop()
        elif seg and seg != ".":
            parts.append(seg)
    return "/".join(parts)


def link_target(base: str, dest: str, renames: dict) -> tuple[str, str] | None:
    """Where a relative link in a document opens, with the viewer's rewriteLink rules.

    Returns (path, fragment), or None for an outside link or a bare #anchor.
    """
    if SCHEME.match(dest) or dest.startswith("//"):
        return None
    path, _, frag = dest.partition("#")
    if not path:
        return None
    try:
        frag = urllib.parse.unquote(frag, errors="strict")
    except UnicodeDecodeError:
        pass
    try:
        target = resolve_rel(base, urllib.parse.unquote(path.split("?")[0], errors="strict"))
    except UnicodeDecodeError:
        target = resolve_rel(base, path)
    return renames.get(target, target), frag


# ── Referenced by ──

REFS_FILE = f"{VIEWER_DIR}/refs.json"
REFS_MENTIONS = 3  # per referring file
REFS_PER_TARGET = 25  # referring files listed per file; the rest are counted


def folders_of(paths) -> set[str]:
    """Every folder that holds one of paths, at any depth."""
    out: set[str] = set()
    for p in paths:
        parts = p.split("/")[:-1]
        for i in range(1, len(parts) + 1):
            out.add("/".join(parts[:i]))
    return out


def collect_refs(repo: Path, files: list[str], renames: dict, tracked: list[str] | None = None) -> tuple[dict, list[dict]]:
    """For each published file, the published Markdown files that link to it, and the broken links.

    Links to unpublished files are never recorded in refs, so an excluded name cannot leak.
    The broken links are for the run summary only and never go into the site.
    """
    published = set(files)
    published_dirs = folders_of(files)
    in_repo = set(tracked if tracked is not None else files)
    repo_dirs = folders_of(in_repo)
    by_lower = {p.lower(): p for p in files}
    found: dict[str, dict[str, list[dict]]] = {}
    broken: dict[tuple[str, str], dict] = {}
    for src in files:
        if not src.lower().endswith((".md", ".markdown")):
            continue
        scan = scan_markdown((repo / src).read_text(encoding="utf-8", errors="replace"))
        base = src.rsplit("/", 1)[0] if "/" in src else ""
        seen: set[tuple[str, str]] = set()
        for link in scan["links"]:
            got = link_target(base, link["dest"], renames)
            if not got or got[0] == src:
                continue
            if got[0] not in published:
                kind = broken_kind(got[0], link["image"], in_repo, repo_dirs, published_dirs)
                if kind:
                    entry = broken.setdefault((src, link["dest"]), {
                        "src": src, "line": link["line"], "dest": link["dest"], "target": got[0],
                        "kind": kind, "count": 0, "hint": by_lower.get(got[0].lower(), "") if kind == "missing" else ""})
                    entry["count"] += 1
                continue
            target, frag = got
            if (target, link["block"]) in seen:
                continue  # one mention per block, however often the block links the file
            seen.add((target, link["block"]))
            mentions = found.setdefault(target, {}).setdefault(src, [])
            if len(mentions) < REFS_MENTIONS:
                heading = scan["headings"][link["heading"]]["text"] if link["heading"] >= 0 else ""
                mentions.append({"h": heading, "x": excerpt(link["block"], link["start"]), "a": frag, "k": "i" if link["image"] else "l"})
    refs, more = {}, {}
    for target in sorted(found):
        sources = sorted(found[target])
        refs[target] = [[s, found[target][s]] for s in sources[:REFS_PER_TARGET]]
        if len(sources) > REFS_PER_TARGET:
            more[target] = len(sources) - REFS_PER_TARGET
    order = sorted(broken.values(), key=lambda b: (b["src"], b["line"], b["dest"]))
    return {"version": 1, "refs": refs, "more": more}, order


def broken_kind(target: str, image: bool, in_repo: set, repo_dirs: set, published_dirs: set) -> str:
    """Why a link to an unpublished target fails on the site, or "" when it still works.

    Mirrors the viewer's rewriteLink: a published folder opens in the viewer, the root opens
    the home page, and anything else opens on GitHub, which works for a file in the repository.
    An image has no such fallback: unless the file is published, the site shows a broken image.
    """
    if target == "" or target in published_dirs or target in repo_dirs:
        return "folder" if image else ""
    if target in in_repo:
        return "unpublished" if image else ""
    return "missing"


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


# Each documented key and the type it must have. A wrong type fails the build rather than
# being coerced: under Python truthiness the string "false" would turn includeHidden on.
CONFIG_TYPES = {
    "title": (str, "a string"),
    "description": (str, "a string"),
    "exclude": (list, "a list of strings"),
    "includeHidden": (bool, "true or false"),
    "sandboxHtml": (bool, "true or false"),
}


def check_config(cfg: object, name: str) -> dict:
    if not isinstance(cfg, dict):
        raise SystemExit(f"{name} must hold a JSON object, not {type(cfg).__name__}.")
    for key, (kind, wanted) in CONFIG_TYPES.items():
        if key not in cfg:
            continue
        value = cfg[key]
        ok = isinstance(value, kind)
        if key == "exclude" and ok:
            ok = all(isinstance(p, str) for p in value)
        if not ok:
            raise SystemExit(f'{name}: "{key}" must be {wanted}, not {json.dumps(value)}.')
    return cfg


def load_config(repo: Path) -> dict:
    for name in CONFIG_FILES:
        path = repo / name
        if path.exists():
            try:
                cfg = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as error:
                raise SystemExit(f"{name.as_posix()} is not valid JSON: {error}")
            return check_config(cfg, name.as_posix())
    return {}


# ── Build ──


def build(repo: Path, out: Path, viewer: Path | None = None, broken: list | None = None) -> dict:
    """Write the site to out and return its site-data.json.

    When broken is a list, the broken links found in published Markdown are added to it.
    They go to the run summary, never into the site.
    """
    viewer = viewer or repo / SITE_DIR
    if not (viewer / "index.html").exists():
        raise SystemExit(f"No viewer found: {viewer / 'index.html'} does not exist.")
    cfg = load_config(repo)
    exclude = [glob_to_regex(p) for p in DEFAULT_EXCLUDE + cfg.get("exclude", [])]
    rows = ls_files(repo)
    files = sorted(p for p in tracked_files(repo, rows) if is_published(p, exclude, cfg.get("includeHidden", False)))
    clash = [p for p in files if p in RESERVED or p.startswith(VIEWER_DIR + "/")]
    if clash:
        raise SystemExit(
            f"These files collide with the viewer's own paths: {', '.join(clash)}. "
            "Add them to exclude in .github/repo-pages.json, or rename them."
        )

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
    # Generated side files, listed so the viewer fetches only what this build wrote.
    # Every tracked path counts as in the repository: a symlink or submodule opens on GitHub.
    refs, found_broken = collect_refs(repo, files, data["renames"], [path for _, path in rows])
    if broken is not None:
        broken.extend(found_broken)
    outputs = {"refs": REFS_FILE} if refs["refs"] else {}
    if outputs:
        data["outputs"] = outputs

    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    for p in files:
        dest = out / p
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(repo / p, dest)
    shutil.copy2(viewer / "index.html", out / "index.html")
    vendor = viewer / "vendor"
    if vendor.is_dir():
        shutil.copytree(vendor, out / VIEWER_DIR / "vendor")
    if "refs" in outputs:
        (out / VIEWER_DIR).mkdir(exist_ok=True)
        (out / REFS_FILE).write_text(json.dumps(refs, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    (out / DATA_FILE).write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return data


def safe(text: str) -> str:
    """Text from a repository file, made safe for the run summary and the log.

    HTML is escaped, and control characters, which a percent-decoded link can hold, become
    U+FFFD, so one link can never start a new line or a workflow command.
    """
    return html.escape(CONTROL.sub("�", text))


CONTROL = re.compile(r"[\x00-\x1f\x7f  ]")
BROKEN_LIMIT = 100  # broken links listed in the run summary; the rest are counted
BROKEN_CHARS = 120  # each path or destination in a listed line, so the summary stays far under its 1 MiB limit
BROKEN_WHY = {
    "missing": "no such file in the repository",
    "folder": "image points at a folder",
    "unpublished": "image is not published, so it shows as broken",
}


def clip(text: str, limit: int = BROKEN_CHARS) -> str:
    return text if len(text) <= limit else text[:limit] + "…"


def broken_line(b: dict) -> str:
    where = f"{clip(b['src'])}:{b['line']}"
    resolved = "" if b["target"] == b["dest"] else f" (resolves to {clip(b['target']) or '/'})"
    times = f", {b['count']} times" if b["count"] > 1 else ""
    hint = f"; did you mean {clip(b['hint'])}?" if b["hint"] else ""
    return safe(f"{where}  {clip(b['dest'])}{resolved}: {BROKEN_WHY[b['kind']]}{times}{hint}")


def broken_report(broken: list[dict], limit: int = BROKEN_LIMIT) -> list[str]:
    if not broken:
        return []
    n = len(broken)
    lines = [
        "", f"#### {n} broken link{'s' if n != 1 else ''} in published Markdown", "",
        "These links or images point at files a reader cannot open. The build carries on regardless.",
        "", "<details open><summary>Each broken link, by file and line</summary>", "", "<pre>",
    ]
    lines += [broken_line(b) for b in broken[:limit]]
    if n > limit:
        lines.append(f"... and {n - limit} more")
    lines += ["</pre>", "", "</details>"]
    return lines


def summary(data: dict, limit: int = 1000, broken: list[dict] | None = None) -> str:
    """Markdown for the workflow run's summary page, so a reader can check what went public."""
    paths = [f["path"] for f in data["files"]]
    folders: dict[str, int] = {}
    for p in paths:
        top = p.split("/")[0] + "/" if "/" in p else "(top level)"
        folders[top] = folders.get(top, 0) + 1
    lines = [f"### Repo Pages published {len(paths)} files", "", "| Folder | Files |", "|---|---|"]
    lines += [f"| {html.escape(name)} | {count} |" for name, count in sorted(folders.items())]
    authors = sorted({c[2] for c in data["commits"]})
    lines += ["", f"The site also shows commit subjects, and these author names: {html.escape(', '.join(authors))}."]
    if "refs" in data.get("outputs", {}):
        lines += ["", f"It also publishes `{REFS_FILE}`, which lists the links between published files."]
    lines += broken_report(broken or [])
    lines += ["", "<details><summary>Every published file</summary>", "", "<pre>"]
    lines += [html.escape(p) for p in paths[:limit]]
    if len(paths) > limit:
        lines.append(f"... and {len(paths) - limit} more")
    lines += ["</pre>", "", "</details>", ""]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--repo", default=".", help="repository root (default: current folder)")
    parser.add_argument("--out", default="_site", help="output folder, replaced on each run (default: _site)")
    parser.add_argument("--viewer", help="folder holding the viewer (default: .github/site in the repository)")
    args = parser.parse_args(argv)
    broken: list[dict] = []
    data = build(Path(args.repo), Path(args.out), Path(args.viewer) if args.viewer else None, broken)
    print(
        f"Built {len(data['files'])} files, {len(data['commits'])} commits, "
        f"{len(data['renames'])} renames into {args.out}/",
        file=sys.stderr,
    )
    step_summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if broken:
        n = len(broken)
        print(f"Found {n} broken link{'s' if n != 1 else ''} in published Markdown.", file=sys.stderr)
        if step_summary:
            print("The run summary lists them.", file=sys.stderr)
        else:  # a local run: list them here, since there is no summary page
            for b in broken[:BROKEN_LIMIT]:
                print("  " + html.unescape(broken_line(b)), file=sys.stderr)
            if n > BROKEN_LIMIT:
                print(f"  ... and {n - BROKEN_LIMIT} more", file=sys.stderr)
    if step_summary:
        with open(step_summary, "a", encoding="utf-8") as handle:
            handle.write(summary(data, broken=broken))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
