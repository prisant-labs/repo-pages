# Changelog

All notable changes to repo-pages are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). The project does not publish versioned releases yet.

## [Unreleased]

### Added

- **The viewer.** It is one static HTML file with views for Markdown, HTML, CSV, JSON, YAML, code, images and PDF. It also has a folder tree, commit-based tabs, breadcrumb menus, a jump list and a command palette.
- **The generator.** `generator/build_site.py` reads git history and writes the site, using only the Python standard library.
- **Reader settings in a popover.** Readers can set the theme and resize interface text and tree text separately. They can also turn on row stripes and open or closed folder icons, and change row density and tree sorting. Other settings choose the starting tab and the date range for New and Updated.
- **The Initech sample and demo.** `examples/build_demo.py` builds the real viewer and generator into one self-contained page.
- **Browser checks.** `tests/run_browser_checks.mjs` runs 48 settings behavior checks against a demo build or a live site.
- **A live demo that stays current.** `.github/workflows/demo.yml` tests the generator, builds the demo from the same commit and runs the browser checks. Pushes to `main` that pass are published to <https://projects.prisantlabs.com/repo-pages/>.
- **Project docs.** These cover features, settings, design and architecture, with third-party notices and agent instructions.
