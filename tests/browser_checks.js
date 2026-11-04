/* Settings behavior checks that run inside the viewer page.
   Open any Markdown file in the built site, then run this whole file in the page
   (a browser tool's evaluate, or the DevTools console). If you load it from a path
   instead, read window.rbChecksResult afterwards. It takes no screenshots, gives one
   short JSON string and restores your settings when it finishes.
   Failure names use the terms in docs/settings-spec.md. A "skip" means the repo has no suitable example. */
window.rbChecks = async function rbChecks() {
  const wait = ms => new Promise(r => setTimeout(r, ms));
  const res = { pass: 0, fail: [], skip: [] };
  const check = (name, ok, detail) => { if (ok) res.pass++; else res.fail.push(detail === undefined ? name : `${name}: ${detail}`); };
  const skip = name => res.skip.push(name);
  const q = s => document.querySelector(s), qa = s => [...document.querySelectorAll(s)];
  const px = (el, p = "fontSize") => parseFloat(getComputedStyle(el)[p]);
  if (typeof PREFS === "undefined" || typeof applyPrefs !== "function") return JSON.stringify({ pass: 0, fail: ["update not applied: PREFS or applyPrefs is missing"], skip: [] });

  // Keep everything so the reader's page is left as it was
  const saved = Object.fromEntries(Object.keys(localStorage).filter(k => k.startsWith("rb.")).map(k => [k, localStorage.getItem(k)]));
  const savedPrefs = { ...PREFS }, savedDoc = [mdTextScale, mdWidth, mdDocTheme], savedOpen = new Set(state.open);
  const savedView = state.view, savedHash = location.hash, savedCommits = COMMITS;
  const setPrefs = o => { Object.assign(PREFS, o); applyPrefs(); };
  const defaults = Object.fromEntries(Object.entries(PREF_SPEC).map(([k, s]) => [k, s[2]]));
  const hasHover = el => el.matches(":hover");

  try {
    Object.assign(PREFS, defaults); applyTheme(); state.view = "folders"; setPrefs({});
    DIRS.forEach(d => state.open.add(d)); renderSidebar();

    // Layout and registry
    check("footer order", [...q(".nav-footer").children].map(e => e.id || e.className).join() === "settingsBtn,buildStamp,themeToggle");
    const want = { theme: "system", uiScale: 1, treeScale: 1, indent: "default", indentCustom: 2, density: "default", sort: "name", guideLines: true, zebra: false, zebraSpan: "full", zebraStrength: "medium", folderIcons: false, iconStyle: "filled", iconColor: "accent", typeBadges: true, folderCounts: true, wrapNames: false, reveal: true, defaultTab: "folders", recentDays: 0 };
    check("defaults", JSON.stringify(Object.keys(want).map(k => defaults[k])) === JSON.stringify(Object.values(want)), Object.keys(want).filter(k => defaults[k] !== want[k]).join());
    const bad = { uiScale: "huge", zebra: "yes", recentDays: 12, defaultTab: "nope", iconColor: "amber", theme: "blue", indentCustom: 99 };
    check("stored values validated", Object.entries(bad).every(([k, v]) => !PREF_SPEC[k][1](v)));

    // Tree geometry at every size, icons on and off
    let geoBad = [], geoSeen = false;
    for (const treeScale of TEXT_SIZES) for (const folderIcons of [false, true]) {
      setPrefs({ treeScale, folderIcons });
      const lists = qa("#navView .tree-children:not(.closed)").filter(k => k.previousElementSibling);
      const list = lists[0], chev = list && list.previousElementSibling.querySelector(".chev").getBoundingClientRect();
      if (list) { const d = list.getBoundingClientRect().left - (chev.left + chev.width / 2); if (Math.abs(d) > 0.6) geoBad.push(`line ${treeScale}/${folderIcons} ${d.toFixed(1)}px`); }
      const mixed = lists.find(k => k.querySelector(":scope > .tree-file") && k.querySelector(":scope > .tree-folder"));
      if (mixed) { geoSeen = true; const d = mixed.querySelector(":scope > .tree-file .tbadge").getBoundingClientRect().left - mixed.querySelector(":scope > .tree-folder .tree-name").getBoundingClientRect().left; if (Math.abs(d) > 0.6) geoBad.push(`badge ${treeScale}/${folderIcons} ${d.toFixed(1)}px`); }
    }
    check("tree geometry", !geoBad.length, geoBad.slice(0, 3).join("; ")); if (!geoSeen) skip("badge alignment: no folder holds both files and folders");
    setPrefs({ treeScale: 1, folderIcons: false });

    // Text scales stay in their own areas
    const crumb = q(".breadcrumb"), file = q("#navView .tree-file"), body = q(".md-body");
    const base = { crumb: px(crumb), file: px(file), body: body && px(body) };
    setPrefs({ uiScale: 1.25 });
    check("interface text scales header", Math.abs(px(crumb) / base.crumb - 1.25) < 0.02);
    check("interface text leaves tree alone", Math.abs(px(q("#navView .tree-file")) - base.file) < 0.01);
    if (body) check("interface text leaves document alone", Math.abs(px(q(".md-body")) - base.body) < 0.01); else skip("document text: open a Markdown file");
    const clipped = qa(".nav-tab").filter(t => t.scrollWidth > t.clientWidth).map(t => t.textContent);
    check("tabs fit at XL", !clipped.length, clipped.join());
    setPrefs({ uiScale: 1, treeScale: 1.25 });
    check("tree text scales rows", Math.abs(px(q("#navView .tree-file")) / base.file - 1.25) < 0.02);
    check("tree text leaves header alone", Math.abs(px(crumb) - base.crumb) < 0.01);
    setPrefs({ treeScale: 1 });

    // Stripes, in both spans and strengths
    for (const zebraSpan of ["full", "indent"]) for (const zebraStrength of ["subtle", "medium"]) {
      setPrefs({ zebra: true, zebraSpan, zebraStrength });
      const label = `${zebraSpan}/${zebraStrength}`, rows = qa("#navView .tree-folder, #navView .tree-file");
      check(`stripes alternate ${label}`, rows.every((r, i) => r.classList.contains("z-odd") === (i % 2 === 1)));
      const row = rows.find(r => r.classList.contains("z-odd") && !r.classList.contains("active") && !hasHover(r));
      if (!row) { skip("stripes: too few rows"); continue; }
      const layer = getComputedStyle(row, "::before"), rowBg = getComputedStyle(row).backgroundColor;
      check(`stripe is a separate layer ${label}`, layer.content !== "none" && layer.backgroundColor !== "rgba(0, 0, 0, 0)" && rowBg === "rgba(0, 0, 0, 0)", `row background ${rowBg}`);
      check(`stripe span ${label}`, (parseFloat(layer.left) < -100) === (zebraSpan === "full"));
    }
    const act = q("#navView .tree-file.active");
    if (act) check("selected row keeps its color on stripes", getComputedStyle(act).backgroundColor !== "rgba(0, 0, 0, 0)"); else skip("selected row: open a file in the tree");
    setPrefs({ zebra: false });

    // Folder icons
    setPrefs({ folderIcons: true });
    const openRow = q("#navView .tree-folder.open");
    if (openRow) {
      const shown = c => getComputedStyle(openRow.querySelector(c)).display !== "none";
      check("open folder shows the open icon", shown(".ficon.is-open") && !shown(".ficon.is-closed"));
      check("filled icon by default", !!openRow.querySelector(".ficon.filled"));
      check("accent icon by default", getComputedStyle(openRow.querySelector(".ficon.is-open")).color === getComputedStyle(document.documentElement).getPropertyValue("--accent").trim() || q("#navPanel").classList.contains("icon-accent"));
    } else skip("folder icons: no open folder");
    setPrefs({ folderIcons: false });
    check("no icons when off", !q("#navView .ficon"));

    // Density, badges, counts, wrapping
    const pad = () => px(q("#navView .tree-file"), "paddingTop");
    const defPad = pad(); setPrefs({ density: "comfortable" }); const big = pad(); setPrefs({ density: "compact" }); const small = pad(); setPrefs({ density: "default" });
    check("row density", small < defPad && defPad < big, `${small}/${defPad}/${big}`);
    setPrefs({ typeBadges: false, folderCounts: false });
    check("badges and counts hide", getComputedStyle(q("#navView .tbadge")).display === "none" && getComputedStyle(q("#navView .count-badge")).display === "none");
    setPrefs({ typeBadges: true, folderCounts: true, wrapNames: true });
    check("wrapped names keep a minimum width", px(q("#navView .tree-name"), "minWidth") > 40 && getComputedStyle(q("#navView .tree-file")).whiteSpace === "normal");
    setPrefs({ wrapNames: false });

    // Sort follows into the arrows
    const dir = Object.values(FILES.reduce((m, f) => ((m[f.dir] = m[f.dir] || []).push(f), m), {})).find(l => new Set(l.map(fileTime)).size > 1);
    if (dir) {
      PREFS.sort = "updated"; const times = siblings(dir[0]).map(fileTime);
      check("recently updated sorts newest first", times.every((t, i) => !i || times[i - 1] >= t));
      PREFS.sort = "name"; const names = siblings(dir[0]).map(f => f.name);
      check("name sort", names.every((n, i) => !i || names[i - 1].localeCompare(n) <= 0));
    } else skip("sort: no folder with different file dates");

    // Date windows must skip an old commit, not stop at it
    const listed = (view, days) => { state.view = view; PREFS.recentDays = days; renderSidebar(); return qa("#navView .recent-item").map(r => r.dataset.file).sort().join(); };
    const times = COMMITS.map(c => Date.parse(c.date) || 0), oldest = COMMITS[times.indexOf(Math.min(...times))];
    for (const days of [7, 30, 90]) {
      const inOrder = listed("updated", days);
      COMMITS = [oldest, ...savedCommits.filter(c => c !== oldest)];
      const shuffled = listed("updated", days);
      COMMITS = savedCommits;
      check(`${days} day window skips older commits`, inOrder === shuffled, "an old commit hid newer ones");
    }
    state.view = "folders"; PREFS.recentDays = 0; renderSidebar();

    // Theme
    PREFS.theme = "dark"; applyTheme(); check("dark theme attribute", document.documentElement.getAttribute("data-theme") === "dark");
    check("stripe token in dark", !!getComputedStyle(document.documentElement).getPropertyValue("--zebra-strong").trim());
    PREFS.theme = "system"; applyTheme(); check("system removes the attribute", !document.documentElement.hasAttribute("data-theme"));

    // Popover
    q("#settingsBtn").click(); await wait(250);
    const modal = q(".settings-modal").getBoundingClientRect(), panel = q("#navPanel").getBoundingClientRect();
    check("popover stays inside the panel", modal.top >= panel.top && modal.bottom <= panel.bottom);
    check("popover has four sections", qa("#settingsBody .settings-modal-section").map(s => s.textContent).join() === "Appearance,Tree,Lists,Documents");
    check("focus on the selected option", document.activeElement.classList.contains("selected"));
    check("sub-options hidden while toggles are off", !q('#settingsBody [data-pref="zebraSpan"]') && !q('#settingsBody [data-pref="iconStyle"]'));
    q('#settingsBody [data-toggle="zebra"]').click();
    check("sub-options shown when on", !!q('#settingsBody [data-pref="zebraSpan"]'));
    check("focus stays on the pressed control", document.activeElement.dataset.toggle === "zebra");
    q('#settingsBody [data-pref="mdWidth"][data-val="narrow"]').click();
    check("document width shared with the doc footer", document.documentElement.getAttribute("data-md-width") === "narrow");
    q('#settingsBody [data-toggle="zebra"]').click();
    q("#settingsReset").click();
    check("reset restores everything", Object.keys(defaults).every(k => PREFS[k] === defaults[k]) && mdWidth === "normal" && mdTextScale === 1 && mdDocTheme === "match");
    document.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape", bubbles: true }));
    check("Esc closes and returns focus", !q("#settingsBackdrop").classList.contains("open") && document.activeElement.id === "settingsBtn");

    // Reveal off leaves the tree alone
    const target = FILES.find(f => f.dir.includes("/") && "#/p/" + f.path !== savedHash);
    if (target) {
      PREFS.reveal = false; state.open.clear(); location.hash = "#/p/" + target.path; await wait(250);
      check("reveal off opens no folders", state.open.size === 0, `${state.open.size} opened`);
      PREFS.reveal = true; location.hash = savedHash || "#/"; await wait(250);
    } else skip("reveal: no nested file");
  } catch (e) {
    res.fail.push("check stopped early: " + e.message);
  } finally {
    COMMITS = savedCommits;
    Object.assign(PREFS, savedPrefs); [mdTextScale, mdWidth, mdDocTheme] = savedDoc;
    state.view = savedView; state.open = savedOpen;
    Object.keys(localStorage).filter(k => k.startsWith("rb.")).forEach(k => localStorage.removeItem(k));
    Object.entries(saved).forEach(([k, v]) => localStorage.setItem(k, v));
    if (typeof closeSettings === "function") closeSettings();
    applyMdReaderPrefs(); applyTheme(); applyPrefs();
    if (location.hash !== savedHash) location.hash = savedHash;
  }
  return JSON.stringify(res);
};
window.rbChecksResult = window.rbChecks();
window.rbChecksResult;
