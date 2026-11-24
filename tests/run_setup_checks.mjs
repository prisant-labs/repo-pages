#!/usr/bin/env node
/* Check the setup page against the code it copies its rules from, and fail on any difference.

   Usage:
     node tests/run_setup_checks.mjs              check setup/index.html
     node tests/run_setup_checks.mjs <folder>     check the index.html in another folder, such as _site/setup

   The page runs in a browser. Its results go to tests/setup_compare.py, which recomputes them
   with the generator, the preflight, the workflow template and the Initech sample.
   Install Playwright first: npm install --no-save --no-package-lock playwright
   Set RP_BROWSER_CHANNEL (for example msedge or chrome) to use an installed browser.
   Set PYTHON to choose the Python interpreter. The default is python3, then python. */
import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import { spawnSync } from "node:child_process";
import { dirname, join, normalize, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";

const HERE = dirname(fileURLToPath(import.meta.url));
const COMPARE = join(HERE, "setup_compare.py");
const folder = resolve(process.argv[2] || join(HERE, "..", "setup"));

function serve(root) {
  const server = createServer(async (req, res) => {
    const path = decodeURIComponent(new URL(req.url, "http://localhost").pathname);
    const file = normalize(join(root, path === "/" ? "index.html" : path));
    if (!file.startsWith(root)) { res.writeHead(403).end(); return; }
    try {
      res.writeHead(200, { "content-type": "text/html; charset=utf-8" }).end(await readFile(file));
    } catch {
      res.writeHead(404).end();
    }
  });
  return new Promise(ok => server.listen(0, "127.0.0.1", () => ok(server)));
}

// The pattern sets mix ordinary use with the gitignore habits the page warns about.
const SETS = [
  {},
  { exclude: ["memos/_drafts/**", "_archive/**", "*.md", "drafts/", "/forms/**", "**/*.csv"] },
  { includeHidden: true, exclude: ["**/*.pem", "teams/**/README.md", "!README.md", "[ab].md", "?ata/**", "**"] },
];
const CONFIGS = [
  "[]", '"x"', "null", "3", "{}", '{"title": 1}', '{"title": null}', '{"description": ["a"]}',
  '{"exclude": "a"}', '{"exclude": [1]}', '{"exclude": ["a", true]}', '{"includeHidden": "false"}',
  '{"includeHidden": 1.5}', '{"sandboxHtml": 0}', '{"title": "caf\\u00e9", "exclude": ["a"], "includeHidden": true}',
  '{"unknown": 1, "sandboxHtml": true}', '{"title": 1, "exclude": 2}',
];
const PREFLIGHT = [];
for (const repoVis of ["public", "private", "internal"])
  for (const siteVis of ["public", "private", "unknown"])
    for (const allowPrivate of [false, true])
      for (const requirePrivate of [false, true]) PREFLIGHT.push({ repoVis, siteVis, allowPrivate, requirePrivate });

const server = await serve(folder);
const base = `http://127.0.0.1:${server.address().port}/`;
const browser = await chromium.launch({ channel: process.env.RP_BROWSER_CHANNEL || undefined });
const problems = [];
let page;
try {
  page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  const pageErrors = [];
  page.on("pageerror", e => pageErrors.push(e.message));
  // The page must load nothing from the network.
  page.on("request", r => { if (!r.url().startsWith(base) && !r.url().startsWith("data:")) problems.push(`The page requested ${r.url()}`); });
  await page.goto(base);
  await page.waitForFunction(() => window.__setup && document.querySelectorAll("#form .sec").length > 0);

  const ui = await page.evaluate(() => ({
    sections: document.querySelectorAll("#form .sec").length,
    tabs: [...document.querySelectorAll("#tabs .tab")].map(t => t.dataset.tab),
    stamp: document.querySelector("#ruleStamp").textContent,
    checks: document.querySelector("#pane-checks").textContent.length,
  }));
  if (ui.sections !== 8) problems.push(`Expected 8 form sections, found ${ui.sections}`);
  if (ui.tabs.join(",") !== "summary,workflow,config,dependabot,checks,inventory") problems.push(`Unexpected tabs: ${ui.tabs.join(",")}`);
  if (!/^Rules from repo-pages v\d+\.\d+\.\d+$/.test(ui.stamp)) problems.push(`Unexpected rule stamp: ${ui.stamp}`);
  if (!ui.checks) problems.push("The Checks tab is empty");

  const data = await page.evaluate(({ SETS, CONFIGS, PREFLIGHT }) => {
    const H = window.__setup;
    H.reset();
    const out = {
      constants: { RELEASE: H.RELEASE, DEFAULT_EXCLUDE: H.DEFAULT_EXCLUDE, RESERVED: H.RESERVED, VIEWER_DIR: H.VIEWER_DIR, REGULAR_MODES: H.REGULAR_MODES, CONFIG_TYPES: H.CONFIG_TYPES },
      defaultWorkflow: H.buildWorkflow(),
      defaultConfig: H.configText(),
      samples: H.samples,
    };
    out.classify = SETS.map(set => { H.reset(); H.set(JSON.parse(JSON.stringify(set))); return { set, rows: H.classify(H.samples.modes) }; });
    out.configErrors = CONFIGS.map(text => [text, H.checkConfig(JSON.parse(text), ".github/repo-pages.json")]);
    out.preflight = PREFLIGHT.map(c => [c, H.preflight(c)]);
    out.presets = H.PRESETS.map(p => { H.reset(); H.set(JSON.parse(JSON.stringify(p.set))); return [p.id, H.configText()]; });
    H.reset();
    return out;
  }, { SETS, CONFIGS, PREFLIGHT });

  // No sideways scroll at phone width.
  await page.setViewportSize({ width: 375, height: 800 });
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  if (overflow > 0) problems.push(`The page scrolls sideways by ${overflow}px at 375px wide`);
  for (const e of pageErrors) problems.push(`Page error: ${e}`);

  const candidates = process.env.PYTHON ? [process.env.PYTHON] : ["python3", "python"];
  let run;
  for (const py of candidates) {
    run = spawnSync(py, [COMPARE], { input: JSON.stringify(data), encoding: "utf8" });
    if (!run.error) break;
  }
  if (run.error) problems.push(`Could not run Python: ${run.error.message}`);
  else {
    process.stdout.write(run.stdout);
    process.stderr.write(run.stderr);
    if (run.status !== 0) problems.push("tests/setup_compare.py found differences");
  }
} finally {
  await browser.close();
  server.close();
}
for (const p of problems) console.error(`FAIL: ${p}`);
console.log(problems.length ? `setup checks: ${problems.length} problem(s)` : "setup checks: all passed");
process.exit(problems.length ? 1 : 0);
