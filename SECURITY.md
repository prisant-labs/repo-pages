# Security policy

## Supported versions

repo-pages has no versioned releases yet. Security fixes land on `main`, and the [live demo](https://projects.prisantlabs.com/repo-pages/) rebuilds from it. If you copied the viewer or generator into your own repository, copy them again to pick up a fix.

## Reporting a vulnerability

Please do not open a public issue for a security problem. Report it privately instead:

1. Open the repository's [Security tab](https://github.com/prisant-labs/repo-pages/security).
2. Choose **Report a vulnerability**. This opens a private advisory that only the maintainers can see.

Include the steps to reproduce the problem, the browser you used, and a small file or repository that triggers it. We will acknowledge your report and work on a fix. We will credit you in the advisory unless you would rather stay anonymous. This is a small project, so a reply can take a few days.

## What is in scope

repo-pages has no server. Its risks lie in what the generator publishes and in what the viewer does with a repository's files.

- **Files the generator should not publish.** The generator publishes tracked regular files, minus `.github/**`, hidden files and your `exclude` patterns. It skips symlinks and submodules. Anything that makes it publish something else is in scope.
- **Markdown that runs code.** The viewer passes every rendered Markdown file through DOMPurify. A Markdown file that still runs script is in scope.
- **Other file views.** CSV, JSON, YAML, code and image views treat a file's content as data. Any such file that runs script is in scope.
- **Commit data.** Author names, commit subjects and file paths appear in the page. If one of them can run script, that is in scope.
- **Browser storage.** The viewer validates everything it reads from browser storage. A stored value that breaks the page or runs script is in scope.

## What is by design

- **HTML files run.** Showing a repository's HTML pages working is a feature. With `sandboxHtml: false`, those pages run on the site's own origin, so they can read its browser storage. With `sandboxHtml: true`, they run in a sandbox with no access to that origin. Set it to `true` if you publish HTML you do not fully trust.
- **A shared domain is a shared origin.** Project sites under one custom domain share an origin. An unsandboxed HTML page on one site can read the browser storage of the others.
- **Publishing is public by default.** A GitHub Pages site can be read by anyone unless your plan offers access control. The generator publishes what you track, including any secret you committed.
- **Published sites name people.** A site shows commit author names and commit subjects. It does not publish author email addresses.

## What is out of scope

- **Bugs in `marked` or DOMPurify themselves.** Please report those to [marked](https://github.com/markedjs/marked) or [DOMPurify](https://github.com/cure53/DOMPurify). Do tell us if our vendored copy is behind a security release.
- **GitHub Pages,** which hosts the sites.
- **The Initech sample.** It is fictional, and the addresses in it use `example.com` domains.
