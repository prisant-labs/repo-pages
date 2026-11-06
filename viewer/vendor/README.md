# vendor/

Third-party scripts the site viewer loads from the site itself instead of a CDN. Each file is the published build copied byte for byte from its npm tarball.

| File | Package | From the tarball | SHA-256 | License |
|------|---------|------------------|---------|---------|
| `marked-18.1.2.umd.js` | `marked@18.1.2` | `lib/marked.umd.js` | `9eb730d2362ae1a8c6201698f17009e16671be6946d3d06503ddc0575283db7c` | MIT |
| `purify-3.4.17.min.js` | `dompurify@3.4.17` | `dist/purify.min.js` | `cd37898f9782adf54820c413191b5691803f0f137c799d6edcfd38523b4c2c31` | Apache-2.0 or MPL-2.0 |

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
6. Build the site locally and open a few Markdown files.
