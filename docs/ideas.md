---
description: Idea backlog for Repo Pages, features worth considering for a general-purpose GitHub Pages documentation site, grouped by the reader they help.
tags: [ideas, backlog, github-pages, repo-pages, features]
---

# Ideas: Repo Pages

None of these are commitments. Each idea says what it would give a reader and what it would take. Ideas marked **(built)** are in the viewer. Ideas marked **(in prototype)** were sketched in an early prototype and are not built.

## Reading

| Idea | What the reader gets | What it takes |
|---|---|---|
| **Folder pages** (built) | Opening a folder shows its README, then a table of its files with type, size and last change | The generator already knows every file. The viewer renders the folder's `README.md` above the table |
| **A view for each file type** (built) | CSV as a sortable table, code with line numbers, JSON as a tree, images with zoom | One small renderer per type. No build step |
| **Document outline** (built) | A table of contents on the right of long Markdown pages | Read the headings after rendering |
| **Mermaid diagrams** | Diagrams in docs render instead of showing code | Load mermaid on the first page that has a diagram |
| **Paired notes for any file** | A CSV with a same-named `.md` gets the notes panel, the same as an HTML prototype does | Widen the pairing rule from `.html` to any type |
| **Front matter as page metadata** (built) | `description` and `tags` show under the title and feed search and filters | Parse front matter in the generator |

## Finding

| Idea | What the reader gets | What it takes |
|---|---|---|
| **Full-text search** (in prototype) | Search inside Markdown, CSV and code, with snippets and filters. The built site searches names, paths, descriptions and tags only | A generated index or Pagefind |
| **Command palette** (built) | Press `/` or Cmd+K from any page to jump to a file | A search box over the file list, which the viewer already has |
| **Tag pages** | One page per front-matter tag, listing every file that carries it | Group by tag in the generator |
| **Backlinks** | "Linked from" at the bottom of a doc | Collect relative links while the generator reads each file |

## Keeping up

| Idea | What the reader gets | What it takes |
|---|---|---|
| **Changes grouped by commit** (built) | The Updated tab shows each commit message with the files it touched | Already in `git log` output |
| **What changed since my last visit** | Files changed since the reader last opened the site are marked | Store the last visit time in the browser, compare with file dates |
| **Diff view for Markdown** | See what changed in a doc, not only that it changed | Link to the GitHub compare view first. A rendered diff later |
| **Weekly digest** | A Slack post with the files added and updated that week | A scheduled workflow that reads the data file |

## Seeing at a glance

Every idea here draws plain SVG in the viewer, so none of them loads anything from the network or needs a charting library. Map views for GeoJSON are left out, because map tiles come from a network server.

| Idea | What the reader gets | What it takes |
|---|---|---|
| **Charts for CSV files** | A Chart toggle beside the sortable table. Dates against numbers draw a line, and categories against numbers draw bars. The reader can change the columns | Guess column types from the values, which is the fiddly part. The sample's ledger, market sizing and requisition files make good test cases |
| **Repository treemap** | The whole repository as nested rectangles, sized by bytes and colored by file type or by age. Clicking opens a file or zooms into a folder | A squarified layout over the data file's paths and sizes. One large binary can dwarf the documents, so the view needs a way to cap or set aside outliers |
| **Freshness coloring** | The tree and folder tables tint each file by the age of its last change, so stale docs stand out | Each file's last-commit date is already in the data file. It is a reader setting, so it goes through `KEYS` and `PREF_SPEC`, and the tint must not disturb the tree geometry |
| **Activity heatmap** | A calendar of commits by day on the Updated or Authors tab | The data file keeps only recent commits and the commits that files point at, so a heatmap built from it would be biased. The generator would add a per-day commit count to the data file |
| **Link graph** | A small map of the documents that one file links to and that link to it | Needs the link collection that backlinks would add. Start with one file's neighborhood, because a whole-site graph turns into a tangle past about a hundred files |
| **Who last touched each folder** | A bar on a folder page showing who made the latest change to each file | The data file holds only the last author of each file, so label it as recent activity, not ownership |

## Sharing and trust

| Idea | What the reader gets | What it takes |
|---|---|---|
| **Open on GitHub, Raw, History** (built) | One click from any page to its source, its raw file and its commits | Build the URLs from `config.repoUrl` and the path |
| **Last-commit stamp** (built) | Each file shows who changed it last, when, and in which commit | From the generator's `git log` pass |
| **Broken link report** | A list of links in docs that point at missing files | Check relative links in the generator and fail or warn |
| **Private-site alert** (built) | The workflow fails loudly if the Pages site is not private. It detects exposure but cannot undo it | The action's `require-private-site` input, which reads the Pages settings on each run |

## More ideas

| Idea | What the reader gets | What it takes |
|---|---|---|
| **Page comments** | A comment thread under each page, stored as GitHub Discussions | A giscus embed keyed by path. Needs Discussions on the repo |
| **Inline annotation** | Highlight text and leave a note | The Hypothesis embed. Notes live with Hypothesis, not the repo |
| **Pinned files** | A short list of starred files at the top of the sidebar, kept in the browser | One more stored list, validated like History |
| **Cache-busting by commit** | A reader never sees a stale file after a rebuild | Add the build SHA to file URLs |
| **Split the viewer into modules** | Faster edits and reviews; no change for readers | Static ES modules served as they are, still no build step |
| **Keyboard and screen-reader support** | Every file reachable without a mouse | Tree roles, focus order, visible focus |
| **Slack post on publish** | The team hears about new and changed docs | A workflow step after deploy that posts the recent list |

## Building the viewer

| Idea | What it gives | What it takes |
|---|---|---|
| **Sample repo and one-file demo** (built) | Develop the viewer, show it, and share screenshots using only sample content | [examples/](../examples/README.md) |
| **Smoke test on the demo** | A viewer change that breaks a view fails before it ships | A Playwright script that opens each file type in the demo and checks for content and no console errors. [tests/run_browser_checks.mjs](../tests/run_browser_checks.mjs) checks settings behavior on one file so far |
| **Generator tests on the sample** | The rename, delete and backdated history are tested on a real repo, not a three-file fixture | Point `test_build_site.py` at a replay of `initech-history.json` |
| **Demo built in CI** (built) | Every push to `main` publishes the current demo, and every pull request tests it | [.github/workflows/demo.yml](../.github/workflows/demo.yml) |
| **Demo mode in the viewer** | No build-time swaps; the demo needs no anchors | The viewer reads an embedded data object when one is present. Costs a few lines in the real viewer |

## Running many sites

| Idea | What the reader gets | What it takes |
|---|---|---|
| **Setup page** (in prototype) | A guided page that writes the two config files for a new repo | A static form that renders the YAML and JSON |
| **Preview deploys for pull requests** | Reviewers see the site as it will look after the merge | Upload the built site as a workflow artifact, or deploy to a second Pages environment |
| **A hub of sites** (in prototype) | One page listing every repo that uses Repo Pages, with viewer versions, build health and privacy | A scheduled workflow reads the Pages and Actions APIs for each repo and writes the hub's data file |
| **Agent index** | An `llms.txt` and a JSON index at the site root, so agents can find and cite files | Written by the generator next to the data file |
