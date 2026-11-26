# Changelog

All notable changes to repo-pages are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow [Semantic Versioning](https://semver.org/). The action's inputs and the keys in `.github/repo-pages.json` are the public contract.

## [Unreleased]

This release adds a generated file to every site and changes no action input or config key, so it is a minor release. No workflow or `repo-pages.json` needs editing.

### Added

- **Referenced by.** A file that other documents on the site link to gets a "Referenced by" button in its header. The button works on every file type, so a PDF, a CSV or an image can say where it is used. It lists each referring document with the heading and sentence that hold the link, and each entry opens the document at that section. The generator collects the links from published Markdown, in Markdown syntax and as HTML `<a href>` and `<img src>`. It writes them to `_viewer/refs.json` and lists that file under a new `outputs` key in `site-data.json`. Links to unpublished files are never recorded, so an excluded file's name cannot appear. Each file lists at most 25 referring documents, and the button counts the rest.

### Changed

- **Images in Markdown follow renames, like links do.** An image path now drops any `?query` or `#fragment` and follows the rename map, so an image moved in git still shows. The generator uses the same rules, so Referenced by agrees with what a reader sees.

## [1.2.0] - 2026-11-24

This release changes what readers see, not how the action is set up. No action input or config key changed, so no workflow or `repo-pages.json` needs editing. A workflow on `@v1` gets it on its next rebuild. A workflow pinned to a commit gets it when the pin moves to the commit that the `v1.2.0` tag points to.

### Added

- **A setup page, at [projects.prisantlabs.com/repo-pages/setup](https://projects.prisantlabs.com/repo-pages/setup/).** It writes `.github/workflows/repo-pages.yml`, a `.github/repo-pages.json` when a default changes, and a Dependabot file for a pinned commit. It covers every action input, every config key and the common workflow choices, such as pull-request builds and a rebuild after a bot's workflow. It predicts the action's preflight with the action's own messages, and it classifies a pasted `git ls-files -s` with the generator's rules. It runs in the browser and sends nothing anywhere. It follows the latest release and names that release at the top of the page. A new check, `tests/run_setup_checks.mjs`, compares its rules with the generator, the preflight, the template and the sample on every pull request.

### Changed

- **The folder tree is tighter.** Default indentation is now `1rem` per level, down from `1.55rem`, and Compact is `0.7rem`, down from `1rem`. A file's type badge now sits in the same column as a folder icon, so turning on folder icons no longer pushes files to the right. A reader's saved indentation choice is kept, and a saved Custom value stays as it was. Only the sizes behind Default and Compact changed.
- **Document text size uses S, M, L and XL.** The Documents row in the settings is now labeled "Text size" and matches the other two text sizes. The sizes are 80%, 100%, 120% and 150%, and the doc footer's A− and A+ step through the same four. A saved size of 90%, 110% or 135% goes back to 100% until the reader picks S, M, L or XL.

### Fixed

- **Vertical guide lines are now visible.** They were drawn in the panel's border color, at about 1.2:1 contrast, which made the setting look broken. They now have their own color, at more than 2:1 in both themes.

## [1.1.0] - 2026-11-22

### Added

- **A `require-private-site` input.** Set it to `"true"` to publish only when the GitHub Pages site is private. The run stops before deploying if the site is public, or if GitHub does not say, whatever the repository's visibility. `allow-private-repository` does not override it. A value other than `"true"` or `"false"` stops the run, so a typo cannot turn it off. It replaces the guard step that some adopters wrote by hand.

### Changed

- **A private site publishes without a setting.** The action now checks whether the GitHub Pages site is public, not whether the repository is private. A private repository whose site is private, which needs GitHub Enterprise Cloud, now publishes. Before, it was refused unless `allow-private-repository` was `"true"`. A private repository whose site is public is still refused by default. If GitHub does not say whether the site is public, the action treats it as public. A repository with internal visibility counts as private, and the error messages say so.
- **`marked` is now 18.2.1.** Upstream fixes edge cases in block quotes, lazy lines, tabs, task items, link destinations in angle brackets and code spans inside link text. It also keeps trailing blank lines in fenced code. Every Markdown file in this repository renders to the same HTML as with 18.2.0, but a file that relies on one of those edge cases can render differently.

### Security

- **Hostile Markdown is even less able to slow a reader's tab.** `marked` 18.2.1 follows up the 18.1.3 fix. It closes a remaining case of quadratic parse time on runs of unmatched emphasis and strikethrough delimiters.

## [1.0.2] - 2026-11-20

### Added

- **A render check on an ordinary site.** `tests/run_render_check.mjs` opens a Markdown file on the site the action builds, which loads `marked` and DOMPurify by URL, unlike the demo. CI now fails if either library does not load or the file falls back to plain text. Before this, a wrong vendored file name passed every check while published sites lost rendered Markdown.

### Changed

- **`marked` is now 18.2.0.** The vendored Markdown library moves up from 18.1.2, taking in 18.1.3 as well. Upstream fixes edge cases in setext headings, emphasis, link labels and references, nested lists, and lazy lines after HTML blocks and tables. Every Markdown file in this repository renders exactly as it did before, but a file that relies on one of those edge cases can render differently.
- **DOMPurify is now 3.4.18.** The vendored sanitizer moves up from 3.4.17.

### Security

- **A quoted `"false"` no longer publishes hidden files.** Before this fix, `"includeHidden": "false"` in `.github/repo-pages.json` counted as on, because any non-empty string is true in Python, so tracked dotfiles were published. The generator now checks every documented config key's type before it selects files or touches the output folder. A wrong type stops the build with the file name and the key. Real `true` and `false` work as before. If your build now stops on this error, remove the quotes. If your config said `"includeHidden": "false"`, check your published site for dotfiles you did not mean to publish.
- **Hostile Markdown is less able to slow a reader's tab.** `marked` 18.1.3 removes a quadratic scan over unmatched emphasis delimiters.
- **DOMPurify hardening.** 3.4.18 fixes a direct property read in its clobbering check and drops several SVG attribute names from its element allow-list. Its `SAFE_FOR_TEMPLATES` and hook fixes do not affect repo-pages, which uses neither.

## [1.0.1] - 2026-11-06

### Changed

- **`marked` is now 18.1.2.** The vendored Markdown library moves up from 18.0.14. Upstream fixes edge cases in lists, block quotes, emphasis, link destinations and HTML blocks, and parsing is faster. Every Markdown file in this repository renders exactly as it did before, but a file that relies on one of those edge cases can render differently.

### Security

- **Hostile Markdown is less able to slow a reader's tab.** `marked` 18.1.0 fixes cubic backtracking on Unicode whitespace in a link destination. No published advisory covers this. DOMPurify still sanitizes everything `marked` produces.

## [1.0.0] - 2026-11-05

### Added

- **The viewer.** It is one static HTML file with views for Markdown, HTML, CSV, JSON, YAML, code, images and PDF. It also has a folder tree, commit-based tabs, breadcrumb menus, a jump list and a command palette.
- **The generator.** `generator/build_site.py` reads git history and writes the site, using only the Python standard library.
- **Reader settings in a popover.** Readers can set the theme and resize interface text and tree text separately. They can also turn on row stripes and open or closed folder icons, and change row density and tree sorting. Other settings choose the starting tab and the date range for New and Updated.
- **The Initech sample and demo.** `examples/build_demo.py` builds the real viewer and generator into one self-contained page.
- **Browser checks.** `tests/run_browser_checks.mjs` runs 64 settings behavior checks against a demo build or a live site.
- **A live demo that stays current.** `.github/workflows/demo.yml` tests the generator, builds the demo from the same commit and runs the browser checks. Pushes to `main` that pass are published to <https://projects.prisantlabs.com/repo-pages/>.
- **Project docs.** These cover features, settings, design and architecture, with third-party notices and agent instructions.
- **An MIT license.** The viewer and generator each carry the notice, because built sites and copies include those files without the rest of the repository. Full license texts for `marked` and DOMPurify now sit in `viewer/vendor/`.
- **Contributor and security guides.** `CONTRIBUTING.md`, `SECURITY.md`, issue forms and a pull request template.
- **Dependabot.** It reports new versions of the workflow actions and the vendored libraries.
- **A GitHub Action.** `prisant-labs/repo-pages@v1` builds a repository with full history and deploys it to GitHub Pages. Adopters add one workflow file, `templates/repo-pages.yml`, and copy nothing.
- **Checks before publishing.** The action refuses a private repository unless `allow-private-repository` is `true`. Its errors say exactly what to change when Pages is off or set to a branch, or when `id-token: write` is missing.
- **A list of what went public.** Each run's summary page shows the published files and the author names.
- **A build-only mode.** Setting `deploy` to `false` builds without publishing.
- **An agent prompt in the README.** It installs the action, and it first stops to show what would go public.

### Changed

- **A fuller README.** It now has badges, a screenshot, a table of contents, status and maintainer sections, and complete publishing steps.
- **The config moved to `.github/repo-pages.json`.** The generator still reads `.github/site/config.json` when the new file is absent.
- **The generator takes `--viewer`,** so the viewer can live outside the repository being published.
- **The browser check runner takes a route,** so it can run on any built site.
- **One name everywhere.** The default page title is now "Repo Pages", and docs, sample content and tags say repo-pages instead of "repo browser". Storage keys moved from the `rb.` prefix to `rp.`, so settings saved in a browser reset once.
- **Sort reaches menus and folder pages.** Under Recently updated, breadcrumb menus and folder pages now use the tree's order. An open folder page re-sorts as soon as the setting changes.
- **Date options have shorter labels.** New and Updated show now offers 7d, 30d and 90d, so the row stays on one line. Tooltips spell out each window.
- **The demo is marked `noindex` until launch,** which matches the projects hub.
- **Every pull request now runs the checks,** including docs-only ones.

### Security

- **DOMPurify is now 3.4.17.** This version patches GHSA-cg2g-xh64-v4q7, GHSA-mrv2-3pqr-j5jr and GHSA-c6gr-qvv4-5v3f. The viewer calls DOMPurify with its default string output and no hooks, which appears to avoid the affected modes.

### Fixed

- **Search palette rows follow Interface text.** Result names, paths and headings now grow with the rest of the palette.
- **Interface badges follow Interface text.** Type badges in the header row, menus and palette now grow with it. Badges on pages stay the same size.
- **The guide line follows the chevron in every indent mode.** Compact and Custom now use the same formula as Default, and each level moves right by exactly the chosen indent.
- **Start on tab stays on one line** at default text size in the default panel width.
- **Stripes restart at each group.** Every commit and author group now opens on the same shade.
- **The generator no longer publishes through symlinks.** It copied a tracked symlink's target into the site, even when that target was outside the repository. It now skips symlinks and submodules.
