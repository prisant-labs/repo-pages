#!/usr/bin/env node
/* Run tests/browser_checks.js against a built demo or a live site, and fail on any failure.

   Usage:
     node tests/run_browser_checks.mjs              check the build in _site/
     node tests/run_browser_checks.mjs <folder>     check a build in another folder
     node tests/run_browser_checks.mjs <https-url>  check a deployed demo

   Install Playwright first: npm install --no-save --no-package-lock playwright
   Set RP_BROWSER_CHANNEL (for example msedge or chrome) to use an installed browser. */
import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import { dirname, join, normalize, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";

const HERE = dirname(fileURLToPath(import.meta.url));
const CHECKS = join(HERE, "browser_checks.js");
const DOC_ROUTE = "#/p/handbook/policies/tps-reports.md";
const target = process.argv[2] || "_site";
const isUrl = /^https?:\/\//.test(target);

function serve(folder) {
  const root = resolve(folder);
  const server = createServer(async (req, res) => {
    const path = decodeURIComponent(new URL(req.url, "http://localhost").pathname);
    const file = normalize(join(root, path === "/" ? "index.html" : path));
    if (!file.startsWith(root)) { res.writeHead(403).end(); return; }
    try {
      const body = await readFile(file);
      res.writeHead(200, { "content-type": file.endsWith(".html") ? "text/html; charset=utf-8" : "application/octet-stream" });
      res.end(body);
    } catch {
      res.writeHead(404).end();
    }
  });
  return new Promise(ok => server.listen(0, "127.0.0.1", () => ok(server)));
}

const server = isUrl ? null : await serve(target);
const base = isUrl ? target.replace(/\/?$/, "/") : `http://127.0.0.1:${server.address().port}/`;
const channel = process.env.RP_BROWSER_CHANNEL || undefined;
const browser = await chromium.launch({ channel });
let failed = true;
try {
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  const pageErrors = [];
  page.on("pageerror", e => pageErrors.push(e.message));
  await page.goto(base + DOC_ROUTE);
  await page.waitForSelector("#settingsBtn");
  await page.waitForFunction(() => document.title.includes("tps-reports"), null, { timeout: 15000 });
  await page.addScriptTag({ path: CHECKS });
  const raw = await page.evaluate(() => window.rpChecksResult);
  const result = JSON.parse(raw);
  console.log(`${base} ${raw}`);
  for (const e of pageErrors) console.error(`Page error: ${e}`);
  failed = result.pass === 0 || result.fail.length > 0 || pageErrors.length > 0;
} finally {
  await browser.close();
  if (server) server.close();
}
process.exit(failed ? 1 : 0);
