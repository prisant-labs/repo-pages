#!/usr/bin/env node
/* Check that Markdown renders on an ordinary built site, the kind the action publishes.

   The browser checks run against the demo, which inlines marked and DOMPurify into the
   page. An ordinary site loads them from _viewer/vendor/ by URL instead, so a wrong
   MARKED_SRC or PURIFY_SRC would pass the browser checks while every published site
   fell back to plain text. This check opens one Markdown file on an ordinary build and
   fails unless both libraries load from the site and the file renders as Markdown.

   Usage:
     node tests/run_render_check.mjs <site-folder> [<route>]   default route: #/p/README.md

   Install Playwright first: npm install --no-save --no-package-lock playwright
   Set RP_BROWSER_CHANNEL (for example msedge or chrome) to use an installed browser. */
import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import { extname, join, normalize, resolve } from "node:path";
import { chromium } from "playwright";

const target = process.argv[2];
const route = process.argv[3] || "#/p/README.md";
if (!target) { console.error("Usage: node tests/run_render_check.mjs <site-folder> [<route>]"); process.exit(2); }

const TYPES = { ".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".json": "application/json", ".md": "text/markdown; charset=utf-8" };
const LIBS = { marked: /\/_viewer\/vendor\/marked-[^/]+\.js$/, DOMPurify: /\/_viewer\/vendor\/purify-[^/]+\.js$/ };

function serve(folder) {
  const root = resolve(folder);
  const server = createServer(async (req, res) => {
    const path = decodeURIComponent(new URL(req.url, "http://localhost").pathname);
    const file = normalize(join(root, path === "/" ? "index.html" : path));
    if (!file.startsWith(root)) { res.writeHead(403).end(); return; }
    try {
      const body = await readFile(file);
      res.writeHead(200, { "content-type": TYPES[extname(file)] || "application/octet-stream" });
      res.end(body);
    } catch {
      res.writeHead(404).end();
    }
  });
  return new Promise(ok => server.listen(0, "127.0.0.1", () => ok(server)));
}

const server = await serve(target);
const base = `http://127.0.0.1:${server.address().port}/`;
const browser = await chromium.launch({ channel: process.env.RP_BROWSER_CHANNEL || undefined });
const problems = [];
try {
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  const loaded = {};
  page.on("pageerror", e => problems.push(`page error: ${e.message}`));
  page.on("response", r => {
    for (const [lib, pattern] of Object.entries(LIBS)) if (pattern.test(new URL(r.url()).pathname)) loaded[lib] = r.status();
  });
  await page.goto(base + route);
  await page.waitForSelector(".md-body h1, .md-body h2, .md-plain", { timeout: 15000 });
  const seen = await page.evaluate(() => ({
    plain: document.querySelectorAll(".md-plain").length,
    heading: document.querySelector(".md-body h1, .md-body h2")?.textContent.trim() || "",
    marked: typeof window.marked !== "undefined",
    purify: typeof window.DOMPurify !== "undefined",
  }));
  for (const lib of Object.keys(LIBS)) {
    if (loaded[lib] !== 200) problems.push(`${lib} did not load from _viewer/vendor/ (${loaded[lib] ? "status " + loaded[lib] : "no matching file was fetched"})`);
  }
  if (!seen.marked || !seen.purify) problems.push("marked or DOMPurify is not defined in the page");
  if (seen.plain) problems.push("the document fell back to plain text (.md-plain)");
  if (!seen.heading) problems.push("no rendered heading in .md-body");
  console.log(`${base}${route} ${JSON.stringify({ ...seen, loaded })}`);

  // The demo serves generated side files from the page, so only an ordinary site proves
  // that each file listed under "outputs" in site-data.json loads by URL.
  const data = JSON.parse(await readFile(join(resolve(target), "site-data.json"), "utf-8"));
  const refsPath = data.outputs && data.outputs.refs;
  if (refsPath) {
    const refs = JSON.parse(await readFile(join(resolve(target), refsPath), "utf-8"));
    const [file, list] = Object.entries(refs.refs)[0];
    const status = await page.evaluate(async p => (await fetch(p)).status, refsPath);
    if (status !== 200) problems.push(`${refsPath} returned ${status}`);
    await page.goto(base + "#/p/" + file);
    const label = await page.waitForSelector("#refsBtn", { timeout: 10000 }).then(b => b.textContent(), () => "");
    if (!label.trim().endsWith(String(list.length + ((refs.more || {})[file] || 0)))) problems.push(`no Referenced by button with the right count on ${file} (got "${label.trim()}")`);
    console.log(`${base}#/p/${file} refs ${JSON.stringify({ status, label: label.trim() })}`);
  }
} catch (e) {
  problems.push(e.message);
} finally {
  await browser.close();
  server.close();
}
for (const p of problems) console.error(`FAIL: ${p}`);
if (!problems.length) console.log("PASS: Markdown renders on the ordinary site, with both libraries loaded from the site.");
process.exit(problems.length ? 1 : 0);
