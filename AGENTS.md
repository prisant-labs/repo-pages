# AGENTS.md - repo-pages

Instructions for any AI agent working in this repository. `CLAUDE.md` is a thin overlay on this file and does not repeat it.

## Project map

repo-pages turns a git repository into a static website where every file is readable. [docs/architecture.md](docs/architecture.md) explains how the parts fit together.

| Path | What it is |
|---|---|
| `viewer/index.html` | The whole interface, in one file. It is about 140 KB, so search it instead of reading it all |
| `viewer/vendor/` | Vendored `marked` and DOMPurify. Follow `viewer/vendor/README.md` to update them |
| `generator/` | `build_site.py` and its tests, using only the Python standard library |
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

Use `python` on Windows if `python3` is not found. Set `RB_BROWSER_CHANNEL=msedge` or `chrome` to use an installed browser instead of downloading Chromium. All three steps must pass before a merge, and `.github/workflows/demo.yml` repeats them on pull requests. Read the results rather than assuming them.

## Rules

- **Keep the repository neutral.** Name no company, organization or private repository, other than the fictional Initech sample and third-party projects. This covers code comments, docs, sample data, commit messages, branch names and pull request text.
- **Search before merging.** If `_local/scrub-terms.txt` exists, search the whole diff with `git grep -IiE -f _local/scrub-terms.txt`. A hit blocks the merge. Never commit that file or quote its terms.
- **Keep the demo honest.** The demo must come from the current viewer and generator. Do not commit the built page, because its dates change on every build.
- **Treat the demo as public.** Pushes to `main` publish it to <https://projects.prisantlabs.com/repo-pages/>, although this repository is private. Anything in the viewer or `examples/` becomes readable by anyone.
- **Keep the viewer dependency-free.** It has no frontend build step and loads nothing from the network. Add third-party code only with a pinned version, a recorded hash and an entry in `THIRD-PARTY-NOTICES.md`.
- **Respect the registry.** Add a reader setting through `KEYS` and `PREF_SPEC`, so it gets validation and Reset. Validate everything read from browser storage.
- **Respect the rejected list.** Do not add anything under "Deliberately left out" in `docs/settings-spec.md` without a new decision.
- **Check geometry.** After changing tree CSS, confirm the default guide line still passes through the chevron center at every Tree text size. `docs/design.md` has the formulas.

## Docs to change with the code

| When you change | Update |
|---|---|
| A reader-visible feature | `docs/features.md`, `CHANGELOG.md`, and `README.md` if the summary changes |
| A setting | `docs/settings-spec.md`, and `docs/design.md` for wording or measurements |
| The build, data contract or checks | `docs/architecture.md` |
| Commands or repository rules | This file |

## Sample content

Follow the content rules in `examples/README.md`. The build stops if the commit script and `examples/initech/` disagree.
