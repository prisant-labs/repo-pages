---
description: What the repo-pages viewer and generator do today, what is deliberately not built yet, and the design rules that keep the viewer maintainable.
tags: [features, viewer, generator, status, repo-pages]
---

# Features

This list describes [viewer/index.html](../viewer/index.html) and [generator/build_site.py](../generator/build_site.py) as they are now. Change it in the same branch as the code.

## Built

### Layout and navigation

- A docked sidebar that collapses with `[` and resizes from 200 to 550px, with the width remembered.
- A floating Browse panel when the sidebar is collapsed. It is the same element as the docked panel, so the two cannot drift.
- A slide-in drawer on phones that closes after a pick.
- Tabs for Folders, New, Updated, Authors and History. Updated groups files by commit.
- A type filter, a name filter, and Expand and Collapse links.
- Breadcrumb menus that list each folder's folders and files.
- Previous and next arrows, a counter such as "3 / 6", and a jump list. The Left and Right arrow keys step through files, and `?` opens the list.
- Folder pages, a home page with recent lists, a command palette (`/` or Cmd+K) and a search page.
- Thin scrollbars in theme colors.

### Reading

- Markdown rendered with vendored `marked`, with every result passed through vendored DOMPurify.
- Front matter `description` and `tags`, shown under the title and fed to search.
- An "On this page" outline, and reader controls for text size, width and document theme.
- Views for CSV (sortable and filterable), code, JSON, YAML, images, PDF and HTML, with download cards for other types.
- Paired notes, in `hide` and `sidebar` modes.
- GitHub, Raw and History links, a last-commit stamp, a "Built from" line and a data load error banner.

### Reader settings

The gear opens a popover with four sections. [settings-spec.md](settings-spec.md) has every value and default.

| Section | Settings |
|---|---|
| Appearance | Theme (Light, Dark or System), Interface text |
| Tree | Tree text, Folder indentation, Row density, Sort, Vertical guide lines, Alternating row colors, Folder icons, File type badges, Item counts on folders, Wrap long names, Reveal the open file |
| Lists | Start on tab, New and Updated show |
| Documents | Text, Width, Doc theme |

### Build

- A generator with its own tests, and a rename map that makes links in docs and old `#/p/` links follow renames.
- Hash routes in the form `#/p/path`, `#/f/folder` and `#/search?q=`.
- A one-page demo built from the real viewer and generator.
- 64 browser checks for settings behavior.
- A workflow that runs the tests and checks on every relevant change, and publishes the demo from `main`.
- A GitHub Action that publishes any repository from one workflow file, with checks before it publishes and a list of what went public.
- Versioned releases, with a major tag that adopters can follow.

## Not built yet

- Row hover actions, more quick-link chips and a home page fragment.
- Notes modes `overlay` and `page`, and the `nav=` and `notes=` URL parameters.
- Share with a direct-file link. Share copies the current URL today.
- Mermaid rendering. Diagrams show as labelled source.
- Full-text search. Search covers names, paths, descriptions and tags.
- `404.html` recovery of old paths and split data files.
- An automated hash test for the vendored libraries. The hashes are recorded in [viewer/vendor/README.md](../viewer/vendor/README.md).
- Browser checks beyond settings behavior, such as one per file type.

[settings-spec.md](settings-spec.md#known-gaps) records any known gaps in what is built. [ideas.md](ideas.md) lists other features worth considering.

## Design rules

| Rule | Why |
|---|---|
| Never keep two renderers of the same panel | Copies drift, so the Browse panel reuses the docked panel element |
| Use one SVG sprite, and render lists over 200 rows on scroll | The page stays small on large repositories |
| Use real buttons and links, with tree roles | The tree works with a keyboard and a screen reader |
| Close the phone drawer after a pick | The page stays visible |
| Generate key tables from the key registry where possible | Docs stay in step with the code |
| Validate everything read from browser storage | A bad stored value must not break the layout |
| Never link a URL that changes state | A link must be safe to follow |
| Build with full git history | A shallow clone misreports authors and dates |
