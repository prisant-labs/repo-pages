"""Compare what the setup page computes with the code it copies its rules from.

tests/run_setup_checks.mjs runs the page in a browser, collects its results as JSON and pipes
them to this script on stdin. This script recomputes each result with generator/build_site.py,
generator/preflight.py, templates/repo-pages.yml and examples/initech, prints every difference,
and exits 1 if there is any. It uses only the Python standard library.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "generator"))
import build_site as bs  # noqa: E402
import preflight as pf  # noqa: E402

CONFIG_FILE = ".github/repo-pages.json"
REPO, SERVER = "initech/intranet", "https://github.com"

# Read and write UTF-8 whatever the platform's default, because sample paths are not all ASCII.
page = json.loads(sys.stdin.buffer.read().decode("utf-8"))
sys.stdout.reconfigure(encoding="utf-8")
failures: list[str] = []
notes: list[str] = []


def expect(ok: bool, what: str) -> None:
    if not ok:
        failures.append(what)


# 1. Constants copied from build_site.py
c = page["constants"]
expect(c["DEFAULT_EXCLUDE"] == bs.DEFAULT_EXCLUDE, f"DEFAULT_EXCLUDE: page {c['DEFAULT_EXCLUDE']}, generator {bs.DEFAULT_EXCLUDE}")
expect(sorted(c["RESERVED"]) == sorted(bs.RESERVED), f"RESERVED: page {c['RESERVED']}, generator {sorted(bs.RESERVED)}")
expect(c["VIEWER_DIR"] == bs.VIEWER_DIR, f"VIEWER_DIR: page {c['VIEWER_DIR']}, generator {bs.VIEWER_DIR}")
expect(sorted(c["REGULAR_MODES"]) == sorted(bs.REGULAR_MODES), f"REGULAR_MODES: page {c['REGULAR_MODES']}, generator {sorted(bs.REGULAR_MODES)}")
generator_types = [[key, wanted] for key, (_, wanted) in bs.CONFIG_TYPES.items()]
expect(c["CONFIG_TYPES"] == generator_types, f"CONFIG_TYPES: page {c['CONFIG_TYPES']}, generator {generator_types}")

# 2. The default workflow is the template, byte for byte once line endings are normalized
template = (ROOT / "templates" / "repo-pages.yml").read_bytes().decode("utf-8").replace("\r\n", "\n")
if page["defaultWorkflow"] != template:
    a, b = page["defaultWorkflow"].split("\n"), template.split("\n")
    line = next((i + 1 for i in range(max(len(a), len(b))) if (a[i:i + 1] or [None]) != (b[i:i + 1] or [None])), 0)
    failures.append(f"The default workflow differs from templates/repo-pages.yml, first at line {line}")
expect(page["defaultConfig"] == "", "At the defaults, the page writes a repo-pages.json, but no file is needed")

# 3. The plain sample is the Initech sample's file list
sample_dir = ROOT / "examples" / "initech"
on_disk = sorted(p.relative_to(sample_dir).as_posix() for p in sample_dir.rglob("*") if p.is_file())
in_page = sorted(page["samples"]["plain"].split("\n"))
missing, extra = sorted(set(on_disk) - set(in_page)), sorted(set(in_page) - set(on_disk))
expect(not missing and not extra, f"The page's Initech sample list is stale: missing {missing[:5]}, extra {extra[:5]}")


# 4. File classification, against the generator's own order
def unquote_c(q: str) -> str:
    body, out, i = q[1:-1], bytearray(), 0
    while i < len(body):
        ch = body[i]
        if ch != "\\":
            out += ch.encode("utf-8")
            i += 1
            continue
        n = body[i + 1]
        if n in "01234567":
            out.append(int(body[i + 1:i + 4], 8))
            i += 4
            continue
        out.append({"n": 10, "t": 9, "r": 13, '"': 34, "\\": 92}.get(n, ord(n)))
        i += 2
    return out.decode("utf-8")


rows = []
for line in page["samples"]["modes"].split("\n"):
    m = re.match(r"^(\d{6}) [0-9a-f]+ \d\t(.+)$", line)
    path = m.group(2)
    rows.append((m.group(1), unquote_c(path) if path.startswith('"') and path.endswith('"') else path))

classified = 0
for case in page["classify"]:
    cfg = case["set"]
    exclude = [bs.glob_to_regex(p) for p in bs.DEFAULT_EXCLUDE + cfg.get("exclude", [])]
    hidden_ok = cfg.get("includeHidden", False)
    expected = {}
    for mode, p in rows:
        if mode not in bs.REGULAR_MODES:
            expected[p] = "skip"
        elif bs.is_published(p, exclude, hidden_ok):
            expected[p] = "stop" if p in bs.RESERVED or p.startswith(bs.VIEWER_DIR + "/") else "pub"
        elif not hidden_ok and any(seg.startswith(".") for seg in p.split("/")):
            expected[p] = "hid"
        else:
            expected[p] = "exc"
    got = {p: ("pub" if status == "flag" else status) for p, status, _ in case["rows"]}
    for p, want in expected.items():
        classified += 1
        expect(got.get(p) == want, f"Classify {p!r} with {cfg}: page {got.get(p)}, generator {want}")

# 5. Config error wording. The generator stops at its first error, so compare that one
for text, page_errors in page["configErrors"]:
    try:
        bs.check_config(json.loads(text), CONFIG_FILE)
        want = None
    except SystemExit as e:
        want = str(e)
    got = page_errors[0] if page_errors else None
    expect(got == want, f"check_config on {text}: page {got!r}, generator {want!r}")

# 6. Preflight predictions, with the real messages
for case, result in page["preflight"]:
    info = {"private": case["repoVis"] != "public", "visibility": case["repoVis"]}
    pages = {"build_type": "workflow"}
    if case["siteVis"] != "unknown":
        pages["public"] = case["siteVis"] == "public"

    def fetch(path: str, info=info, pages=pages) -> tuple[int, dict]:
        return (200, info) if path == f"repos/{REPO}" else (200, pages)

    errors = pf.check(fetch, REPO, SERVER, {"ACTIONS_ID_TOKEN_REQUEST_URL": "x"}, case["allowPrivate"], case["requirePrivate"])
    if errors:
        expect(not result["ok"] and [result["text"]] == errors, f"Preflight {case}: page {result['text']!r}, action {errors}")
    else:
        expect(result["ok"], f"Preflight {case}: page refuses with {result['text']!r}, the action publishes")

# 7. Every preset writes a config file the generator accepts
for preset, text in page["presets"]:
    if not text:
        continue
    try:
        bs.check_config(json.loads(text), CONFIG_FILE)
    except (SystemExit, json.JSONDecodeError) as e:
        failures.append(f"Preset {preset} writes a config the generator refuses: {e}")

# 8. The release the page pins is the latest release, with its peeled commit
release = c["RELEASE"]
try:
    listing = subprocess.run(["git", "-C", str(ROOT), "ls-remote", "--tags", "origin", "refs/tags/v*"],
                             capture_output=True, text=True, check=True, timeout=60).stdout
except (OSError, subprocess.SubprocessError) as e:
    notes.append(f"Release not checked, because git ls-remote failed: {e}")
else:
    peeled, versions = {}, []
    for line in listing.splitlines():
        sha, ref = line.split("\t")
        tag = ref.removeprefix("refs/tags/").removesuffix("^{}")
        if re.fullmatch(r"v\d+\.\d+\.\d+", tag):
            if ref.endswith("^{}") or tag not in peeled:
                peeled[tag] = sha
            versions.append(tuple(int(x) for x in tag[1:].split(".")))
    if not versions:
        notes.append("Release not checked, because origin lists no vX.Y.Z tags")
    else:
        latest = "v" + ".".join(map(str, max(versions)))
        expect(release["tag"] == latest, f"RELEASE.tag is {release['tag']}, but the latest release is {latest}. Update RELEASE in setup/index.html")
        expect(release["sha"] == peeled.get(release["tag"]), f"RELEASE.sha is {release['sha']}, but {release['tag']} points at {peeled.get(release['tag'])}")

for n in notes:
    print("note:", n)
for f in failures:
    print("FAIL:", f)
print(f"setup page: {classified} classifications, {len(page['configErrors'])} config cases, "
      f"{len(page['preflight'])} preflight cases, {len(page['presets'])} presets, {len(failures)} failures")
sys.exit(1 if failures else 0)
