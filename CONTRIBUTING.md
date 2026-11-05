# Contributing

Thanks for your interest in repo-pages. Bug reports, ideas and code are all welcome.

## Ways to help

- **Report a bug.** Use the [bug form](https://github.com/prisant-labs/repo-pages/issues/new/choose). A small file or repository that shows the problem is the fastest way to a fix.
- **Suggest a feature.** Use the feature form. [docs/ideas.md](docs/ideas.md) lists ideas that have already come up, and [docs/settings-spec.md](docs/settings-spec.md) lists settings that were deliberately left out.
- **Report a security problem privately,** as [SECURITY.md](SECURITY.md) describes. Please do not open a public issue for it.

## Before you open a pull request

For anything larger than a small fix, please open an issue first. That way we can agree on the approach before you spend time on it.

The project has a few firm limits:

- **The viewer stays one file with no build step.** It loads nothing from the network.
- **The generator uses only the Python standard library.**
- **New third-party code needs a pinned version, a recorded hash and an entry in [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md).**
- **The sample stays fictional.** [examples/README.md](examples/README.md) has the content rules.

## Run it locally

You need Python 3, git, and Node 22 for the browser checks. CI uses Python 3.12. Run these from the repository root:

```bash
python3 generator/test_build_site.py
python3 examples/build_demo.py --viewer viewer --generator generator/build_site.py
npm install --no-save --no-package-lock playwright
npx playwright install chromium
node tests/run_browser_checks.mjs
```

Use `python` on Windows if `python3` is not found. To use an installed browser instead of downloading Chromium, set `RP_BROWSER_CHANNEL` to `msedge` or `chrome`.

The browser checks cover settings behavior on one Markdown file. A change to another view still needs a look in a browser:

```bash
python3 -m http.server 8000 --directory _site
```

## Pull requests

- Keep each pull request to one change, and explain why in its description.
- Add an entry under "Unreleased" in [CHANGELOG.md](CHANGELOG.md) for any change that readers will notice.
- Update the documents that describe the behavior you changed. The table at the end of [AGENTS.md](AGENTS.md) says which ones.
- Do not commit the built demo, because its dates change on every build.
- Only name real companies, products or people when they are third-party projects the code depends on.

A pull request can merge once the `build` check passes and every review conversation is resolved. If you work from a fork, a maintainer approves the workflow run on your pull request before the check starts.

## License

By contributing, you agree that your contribution is licensed under the project's [MIT license](LICENSE).
