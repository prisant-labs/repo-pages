# Changelog

All notable changes to repo-pages are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow [Semantic Versioning](https://semver.org/). The action's inputs and the keys in `.github/repo-pages.json` are the public contract.

## [Unreleased]

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
