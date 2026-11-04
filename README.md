# repo-pages

repo-pages gives a repository a website where every file is readable. Markdown is rendered, HTML pages run, CSV files become sortable tables, and code is highlighted. The site rebuilds from git on every push and has no server.

It has two parts:

- **A viewer:** one static HTML file with two vendored libraries.
- **A generator:** a Python script, using only the standard library, that reads git history and writes the site.

## What a reader gets

- A folder tree, plus New, Updated, Authors and History tabs built from commits.
- A view for each file type: Markdown, HTML, CSV, JSON, YAML, code, images and PDF.
- Breadcrumb menus, a file jump list, folder pages and a command palette (`/` or Cmd+K).
- Paired notes, which show `page.md` beside `page.html`.
- Settings for the theme, interface text, tree text, row stripes, folder icons, sorting and more.

[docs/features.md](docs/features.md) has the full list, including what is not built.

## Try the demo

**[Open the live demo](https://projects.prisantlabs.com/repo-pages/).** It runs the real viewer and generator over the [Initech sample](examples/README.md), a parody company intranet. Every change to the viewer, generator or sample rebuilds it, so it always shows the latest version.

To build the same page yourself:

```bash
python3 examples/build_demo.py --viewer viewer --generator generator/build_site.py
python3 -m http.server 8000 --directory _site
```

Then open `http://localhost:8000`. On Windows, use `python` if `python3` is not found.

Things to try:

1. Press the gear in the lower left, and change Interface text and Tree text. The document text does not change size.
2. Turn on **Alternating row colors** and **Folder icons**, then open and close some folders.
3. Open `projects/y2k-remediation/notes/standups/day-03.md` and press `?` to open the jump list.
4. Open `data/tps-reports-filed.csv` and sort a column.

## Use it on your own repository

1. Copy `viewer/` to `.github/site/` in your repository.
2. Copy `generator/build_site.py` to `.github/scripts/build_site.py`.
3. Add `.github/site/config.json`:

   ```json
   {
     "title": "My Docs",
     "description": "What this site is for.",
     "exclude": ["drafts/**"],
     "includeHidden": false,
     "sandboxHtml": false
   }
   ```

4. Build it with full git history available, then serve it:

   ```bash
   python3 .github/scripts/build_site.py --out _site
   python3 -m http.server 8000 --directory _site
   ```

To publish it, deploy `_site/` to GitHub Pages from a workflow. Check out with `fetch-depth: 0`, because a shallow clone gives every file the same author and date.

## FAQ

**Does every tracked file get published?** Yes, apart from `.github/**`, hidden files and your `exclude` patterns. Check what you are publishing before you deploy.

**Is the site private?** Not by default. GitHub offers access-controlled Pages only on certain plans, so check GitHub's current rules before you publish anything sensitive.

**Why does the Updated tab show one author for everything?** The site was built from a shallow clone. Build with full history.

**How current is the live demo?** A workflow rebuilds it on every push to `main` that touches the viewer, generator, sample or checks. It publishes only if the tests and browser checks pass.

**Are reader settings shared between readers?** No. They live in each reader's browser storage. If storage is blocked, the defaults apply.

## Documents

| Document | Read it to learn |
|---|---|
| [docs/features.md](docs/features.md) | What the viewer does today, and what is not built |
| [docs/settings-spec.md](docs/settings-spec.md) | Every reader setting, its values, default and storage key |
| [docs/design.md](docs/design.md) | Layout values, colors, tree geometry and screenshots |
| [docs/architecture.md](docs/architecture.md) | How the viewer, generator, demo and checks fit together |
| [docs/ideas.md](docs/ideas.md) | Features worth considering |
| [examples/README.md](examples/README.md) | The Initech sample and how to change it |
| [CHANGELOG.md](CHANGELOG.md) | What changed |
| [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md) | Licenses for the vendored libraries and icon shapes |
