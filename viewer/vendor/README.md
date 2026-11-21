# vendor/

Third-party scripts the site viewer loads from the site itself instead of a CDN. Each file is the published build copied byte for byte from its npm tarball.

| File | Package | From the tarball | SHA-256 | License |
|------|---------|------------------|---------|---------|
| `marked-18.2.0.umd.js` | `marked@18.2.0` | `lib/marked.umd.js` | `392f4df89533b50f1dadff3f6dc0952350bd39c9f17def50a0374ef47d6147ef` | MIT |
| `purify-3.4.18.min.js` | `dompurify@3.4.18` | `dist/purify.min.js` | `8053ee2a6a09f9d50f7fcd6fb7f07072f52c7f3fa9aa12147cab4feaf65ee970` | Apache-2.0 or MPL-2.0 |

The viewer (`../index.html`) loads both on the first Markdown render and passes every `marked.parse` result through `DOMPurify.sanitize` before it reaches the page. If either file fails to load, Markdown shows as plain text.

`LICENSE-marked`, `LICENSE-dompurify-apache` and `LICENSE-dompurify-mpl` are the packages' `LICENSE` and `LICENSE-MPL` files, copied byte for byte.

## Knowing when to update

`tests/vendor-watch/package.json` lists the vendored versions. Nothing installs it. It exists so Dependabot reports new versions and security advisories for these files. A generator test checks that it matches the files here, so a Dependabot pull request fails CI until someone follows the steps below.

## Updating a library

1. In a temporary folder, run `npm pack marked@<version>` (or `dompurify@<version>`) and unpack the tarball.
2. Copy the file named above into this folder with the new version in its name, and delete the old one.
3. Run `shasum -a 256 <file>` and update the file name and hash here and the `MARKED_SRC` or `PURIFY_SRC` constant in `../index.html`.
4. Copy the package's license files over the matching `LICENSE-*` files here.
5. Update the version in `tests/vendor-watch/package.json` and `THIRD-PARTY-NOTICES.md`.
6. Build the site locally and open a few Markdown files. `node tests/run_render_check.mjs <site>` checks one of them automatically, and CI runs it on every pull request.
