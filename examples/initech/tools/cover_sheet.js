// Render a TPS cover sheet into an element. Used by the intranet print view.
const FIELDS = ["Project code", "Report date", "Tester", "Test cases run", "Test cases passed"];
const MANAGER_BOXES = 8;

export function renderCoverSheet(el, values = {}) {
  const rows = FIELDS.map(name => {
    const v = values[name] ?? "";
    return `<tr><th>${name}</th><td>${escapeHtml(String(v))}</td></tr>`;
  }).join("");
  const boxes = Array.from({ length: MANAGER_BOXES }, () => `<span class="box"></span>`).join("");
  el.innerHTML = `<div class="cover-sheet"><h1>TPS Report Cover Sheet</h1><table>${rows}</table><div class="managers">${boxes}</div></div>`;
}

function escapeHtml(s) {
  return s.replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
}

export function isMissingCoverSheet(report) {
  return !report.coverSheet || report.coverSheet.version !== "new";
}
