---
description: The Initech sample repo, its commit script, and the script that builds the self-contained repo-pages demo from them.
tags: [examples, sample-data, demo, fixture, initech]
---

# Examples

A sample repo for building, testing and showing repo-pages. It is a parody of the 1999 film *Office Space*, and it is not affiliated with the film or its owners. Every person and address in it is fictional.

| Path | What it is |
|---|---|
| [initech/](initech/) | 88 files: the intranet of Initech, a parody software company. Markdown with front matter, CSV, JSON, YAML, Python, SQL, shell, a Makefile, SVG, PNG, PDF, a zip and two HTML pages with paired notes |
| [initech-history.json](initech-history.json) | The commit script: 41 commits by 9 authors, including a rename and a delete. Paths are the names at the time of the commit; dates are days before the build |
| [build_demo.py](build_demo.py) | Replays the history into a temporary git repo, runs the real generator, and writes one self-contained page to `_site/index.html` |

## Build the demo

```bash
python3 examples/build_demo.py --viewer viewer --generator generator/build_site.py
```

`--viewer` is the folder with the viewer's `index.html` and `vendor/`. `--generator` is `build_site.py`. The build needs only the Python standard library and git. It swaps three lines in the viewer so files load from the page instead of the server, and it stops if any of those lines has changed. It also adds a `noindex` tag, which stays until the project is announced.

## Changing the sample

- **Edit a file:** change it under `initech/` and rebuild. Its final content is what the demo shows.
- **Add a file:** add it under `initech/`. It arrives in the first commit unless a commit in the history adds it.
- **Give a file a history:** name it in a commit's `add` or `modify` list. A file added later must not also be in the first commit; the script handles that.
- **Rename:** add `"rename": [["old/path.md", "new/path.md"]]` to a commit, and use the old path in earlier commits.
- **A file that no longer exists:** use `"create": {"path": "text"}` and a later `"delete"`.

The build stops if the history names a file that is not in `initech/`, or if the replay does not end with the same bytes as `initech/`.

## Content rules

- Parody, written for this sample. No dialogue from the film, beyond a few words.
- Fake addresses only: `@initech.example.com` and `example.com` links.
- No em dashes, and no real company or product names beyond the film parody.
