// Runs the Python generator in the browser via Pyodide.
// This site is intended for GitHub Pages hosting (no backend).

import { loadPyodide } from "https://cdn.jsdelivr.net/pyodide/v0.25.1/full/pyodide.mjs";

const els = {
  studentMode: document.getElementById("studentMode"),
  wizard: document.getElementById("wizard"),
  dispenseType: document.getElementById("dispenseType"),
  storageTarget: document.getElementById("storageTarget"),
  dispenseTarget: document.getElementById("dispenseTarget"),
  mechanism: document.getElementById("mechanism"),
  preset: document.getElementById("preset"),
  dimMode: document.getElementById("dimMode"),
  innerWidth: document.getElementById("innerWidth"),
  innerDepth: document.getElementById("innerDepth"),
  innerHeight: document.getElementById("innerHeight"),
  thickness: document.getElementById("thickness"),
  fit: document.getElementById("fit"),
  fitReadout: document.getElementById("fitReadout"),
  sizeReadout: document.getElementById("sizeReadout"),
  kerf: document.getElementById("kerf"),
  clearance: document.getElementById("clearance"),
  jointRule: document.getElementById("jointRule"),
  calSet: document.getElementById("calSet"),
  fingerWidth: document.getElementById("fingerWidth"),
  minFingers: document.getElementById("minFingers"),
  sheetWidth: document.getElementById("sheetWidth"),
  marginMm: document.getElementById("marginMm"),
  paddingMm: document.getElementById("paddingMm"),
  strokeMm: document.getElementById("strokeMm"),
  labels: document.getElementById("labels"),
  lid: document.getElementById("lid"),
  holdingTabs: document.getElementById("holdingTabs"),
  tabWidth: document.getElementById("tabWidth"),
  frontHeight: document.getElementById("frontHeight"),
  scoop: document.getElementById("scoop"),
  scoopRadius: document.getElementById("scoopRadius"),
  scoopDepth: document.getElementById("scoopDepth"),
  slotWidth: document.getElementById("slotWidth"),
  slotHeight: document.getElementById("slotHeight"),
  slotY: document.getElementById("slotY"),
  btnGenerate: document.getElementById("btnGenerate"),
  btnCalibration: document.getElementById("btnCalibration"),
  btnBundle: document.getElementById("btnBundle"),
  status: document.getElementById("status"),
  preview: document.getElementById("preview"),
  download: document.getElementById("download"),
  warnings: document.getElementById("warnings"),

  zoomOut: document.getElementById("zoomOut"),
  zoomIn: document.getElementById("zoomIn"),
  fitView: document.getElementById("fitView"),
  showCut: document.getElementById("showCut"),
  showLabels: document.getElementById("showLabels"),
};

function setStatus(msg) {
  els.status.textContent = msg;
}

function num(el, fallback = null) {
  const v = el.value.trim();
  if (v === "") return fallback;
  const n = Number(v);
  return Number.isFinite(n) ? n : fallback;
}

function escapeHtml(s) {
  return s.replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;");
}

let pyodide = null;
let lastSvg = null;
let lastParams = null;

const FIT_PRESETS = [0.0, 0.1, 0.2];

function computeDerived() {
  const t = num(els.thickness, 3);
  const kerf = num(els.kerf, 0.2);
  const c = num(els.clearance, 0.1);
  const drawnSlot = t + c - kerf;
  const expectedFinalSlot = t + c;
  els.jointRule.textContent = `Joint rule: drawn slot depth = thickness + clearance − kerf = ${drawnSlot.toFixed(2)}mm. Expected final slot ≈ thickness + clearance = ${expectedFinalSlot.toFixed(2)}mm.`;

  const w = num(els.innerWidth, 135);
  const d = num(els.innerDepth, 90);
  const h = num(els.innerHeight, 225);
  if (els.dimMode.value === "internal") {
    const outerW = w + 2 * t;
    const outerD = d + 2 * t;
    const outerH = h + t;
    els.sizeReadout.textContent = `Computed external size ≈ W ${outerW.toFixed(1)} × D ${outerD.toFixed(1)} × H ${outerH.toFixed(1)} (mm)`;
  } else {
    const innerW = w - 2 * t;
    const innerD = d - 2 * t;
    const innerH = h - t;
    els.sizeReadout.textContent = `Computed internal size ≈ W ${innerW.toFixed(1)} × D ${innerD.toFixed(1)} × H ${innerH.toFixed(1)} (mm)`;
  }
}

function setFitPreset(index) {
  const i = Math.max(0, Math.min(2, Number(index)));
  const c = FIT_PRESETS[i];
  els.fit.value = String(i);
  els.clearance.value = c.toFixed(2);
  els.fitReadout.textContent = i === 0 ? "Fit: Tight (harder to assemble)" : i === 1 ? "Fit: Normal" : "Fit: Loose (student-friendly)";
  computeDerived();
}

function setStudentMode(on) {
  const enabled = !!on;
  els.wizard.hidden = !enabled;
  // In student mode, keep Advanced collapsed by default.
  const adv = document.getElementById("advanced");
  if (adv) adv.open = !enabled;
}

async function init() {
  setStatus("Loading Pyodide…");
  pyodide = await loadPyodide({});

  setStatus("Loading generator module…");
  const resp = await fetch("./cardboxgen_v0_1.py", { cache: "no-store" });
  if (!resp.ok) throw new Error(`Failed to load Python module: ${resp.status}`);
  const code = await resp.text();

  // Write into the virtual FS and import as a module so it doesn't run the CLI.
  pyodide.FS.writeFile("cardboxgen_v0_1.py", code);
  await pyodide.runPythonAsync(`import importlib\ncard = importlib.import_module('cardboxgen_v0_1')`);

  els.btnGenerate.disabled = false;
  els.btnCalibration.disabled = false;
  els.btnBundle.disabled = false;
  els.btnGenerate.textContent = "Generate SVG";

  // Show something useful immediately on first load.
  try {
    await generateSvg();
  } catch (e) {
    console.error(e);
    setStatus(`Ready (auto-generate failed): ${e?.message ?? e}`);
  }
}

function buildParams() {
  const preset = els.preset.value;
  const dimMode = els.dimMode.value;

  let innerW = num(els.innerWidth, 135);
  let innerD = num(els.innerDepth, 90);
  let innerH = num(els.innerHeight, 225);
  const t = num(els.thickness, 3);

  // If user entered external sizes, convert to internal before sending to generator.
  if (dimMode === "external") {
    innerW = innerW - 2 * t;
    innerD = innerD - 2 * t;
    innerH = innerH - t;
  }

  const p = {
    preset,
    inner_width: innerW,
    inner_depth: innerD,
    inner_height: innerH,
    thickness: t,
    kerf_mm: num(els.kerf, 0.2),
    clearance_mm: num(els.clearance, 0.1),
    finger_width: num(els.fingerWidth, null),
    min_fingers: num(els.minFingers, 3),
    sheet_width: num(els.sheetWidth, 340),
    layout_margin_mm: num(els.marginMm, 10),
    layout_padding_mm: num(els.paddingMm, 12),
    stroke_mm: num(els.strokeMm, 0.2),
    labels: !!els.labels.checked,
    lid: preset === "box_with_lid" ? !!els.lid.checked : false,

    holding_tabs: !!els.holdingTabs.checked,
    tab_width_mm: num(els.tabWidth, 2.0),

    // Optional preset params
    front_height: num(els.frontHeight, null),
    scoop: !!els.scoop.checked,
    scoop_radius: num(els.scoopRadius, 22),
    scoop_depth: num(els.scoopDepth, 18),

    slot_width: num(els.slotWidth, 86),
    slot_height: num(els.slotHeight, 18),
    slot_y_from_bottom: num(els.slotY, 38),
  };
  return p;
}

async function generateSvg() {
  els.download.hidden = true;
  els.preview.textContent = "";
  els.warnings.hidden = true;
  els.warnings.innerHTML = "";

  const p = buildParams();
  setStatus("Generating SVG…");

  // Send parameters to Python.
  pyodide.globals.set("p_json", JSON.stringify(p));

  const resultJson = await pyodide.runPythonAsync(`
import json
from cardboxgen_v0_1 import BoxParams, generate_svg_with_warnings

p = BoxParams(**json.loads(p_json))
svg, warnings = generate_svg_with_warnings(p)
json.dumps({"svg": svg, "warnings": warnings})
`);

  const parsed = JSON.parse(resultJson);
  const svg = parsed.svg;
  const warnings = parsed.warnings || [];

  lastSvg = svg;
  lastParams = p;

  if (warnings.length) {
    els.warnings.hidden = false;
    els.warnings.innerHTML = `<strong>Warnings</strong><ul>${warnings.map((w) => `<li>${escapeHtml(String(w))}</li>`).join("")}</ul>`;
  }

  // Preview (inline SVG) + download.
  // Wrap for pan/zoom transforms.
  els.preview.innerHTML = `<div id="svgWrap">${svg}</div>`;
  applyLayerToggles();
  attachHoverHighlight();
  fitToView();
  const blob = new Blob([svg], { type: "image/svg+xml" });
  const url = URL.createObjectURL(blob);
  els.download.href = url;
  els.download.hidden = false;
  els.download.textContent = "Download SVG";
  els.download.download = `cardbox_${p.preset}.svg`;

  setStatus("Done.");
}

async function getCalibrationSvgString() {
  const thickness = num(els.thickness, 3);
  const kerf = num(els.kerf, 0.2);
  const calSet = els.calSet?.value ?? "student";

  pyodide.globals.set("thickness", thickness);
  pyodide.globals.set("kerf", kerf);
  pyodide.globals.set("cal_set", calSet);

  return await pyodide.runPythonAsync(`
from cardboxgen_v0_1 import build_calibration_svg
path = '/tmp/calibration.svg'
named = [('tight',0.00),('normal',0.10),('loose',0.20)] if cal_set == 'student' else None
vals = [-0.10,-0.05,0.0,0.05,0.10,0.15,0.20]
build_calibration_svg(thickness=thickness, kerf_mm=kerf, clearance_values=vals, out_path=path, named_presets=named)
open(path, 'r', encoding='utf-8').read()
`);
}

function buildReadmeMarkdown(params) {
  const t = params.thickness;
  const kerf = params.kerf_mm;
  const c = params.clearance_mm;
  const drawnSlot = (t + c - kerf).toFixed(2);
  const expectedFinalSlot = (t + c).toFixed(2);

  return `# CardBoxGen Bundle\n\n` +
    `Preset: **${params.preset}**\n\n` +
    `## Joint rule\n` +
    `- Drawn slot depth = thickness + clearance − kerf = **${drawnSlot}mm**\n` +
    `- Expected final slot ≈ thickness + clearance = **${expectedFinalSlot}mm**\n\n` +
    `## Parameters\n` +
    "```json\n" + JSON.stringify(params, null, 2) + "\n```\n\n" +
    `## Fabrication checklist\n` +
    `1) If kerf is unknown: cut calibration.svg once\n` +
    `2) Pick the best-fitting label\n` +
    `3) If too tight: increase Joint clearance by 0.05mm\n` +
    `4) If too loose: reduce Joint clearance by 0.05mm\n`;
}

async function downloadBundleZip() {
  if (!pyodide) throw new Error("Pyodide not ready");
  if (!lastSvg || !lastParams) {
    await generateSvg();
  }

  // JSZip is loaded as a global from CDN.
  const JSZipLib = globalThis.JSZip;
  if (!JSZipLib) throw new Error("JSZip failed to load");
  const zip = new JSZipLib();

  const preset = lastParams.preset || "design";
  zip.file(`design_${preset}.svg`, lastSvg);

  const calSvg = await getCalibrationSvgString();
  zip.file("calibration.svg", calSvg);

  const readme = buildReadmeMarkdown(lastParams);
  zip.file("README.md", readme);

  const blob = await zip.generateAsync({ type: "blob" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `cardboxgen_bundle_${preset}.zip`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

async function generateCalibration() {
  setStatus("Generating calibration SVG…");
  const thickness = num(els.thickness, 3);
  const kerf = num(els.kerf, 0.2);
  const calSet = els.calSet?.value ?? "student";

  pyodide.globals.set("thickness", thickness);
  pyodide.globals.set("kerf", kerf);
  pyodide.globals.set("cal_set", calSet);

  const svg = await pyodide.runPythonAsync(`
import textwrap, json
from cardboxgen_v0_1 import build_calibration_svg

# build_calibration_svg writes to a file, so we call its internal logic by
# generating it to /tmp then reading.
path = '/tmp/calibration.svg'
named = [('tight',0.00),('normal',0.10),('loose',0.20)] if cal_set == 'student' else None
vals = [-0.10,-0.05,0.0,0.05,0.10,0.15,0.20]
build_calibration_svg(thickness=thickness, kerf_mm=kerf, clearance_values=vals, out_path=path, named_presets=named)
open(path, 'r', encoding='utf-8').read()
`);

  els.preview.innerHTML = `<div id="svgWrap">${svg}</div>`;
  applyLayerToggles();
  attachHoverHighlight();
  fitToView();
  const blob = new Blob([svg], { type: "image/svg+xml" });
  const url = URL.createObjectURL(blob);
  els.download.href = url;
  els.download.hidden = false;
  els.download.textContent = "Download calibration SVG";
  els.download.download = `calibration.svg`;

  setStatus("Done.");
}

let view = { scale: 1.0, tx: 0, ty: 0 };

function getSvgWrap() {
  return document.getElementById("svgWrap");
}

function applyTransform() {
  const wrap = getSvgWrap();
  if (!wrap) return;
  wrap.style.transformOrigin = "0 0";
  wrap.style.transform = `translate(${view.tx}px, ${view.ty}px) scale(${view.scale})`;
}

function fitToView() {
  const wrap = getSvgWrap();
  const svg = wrap?.querySelector("svg");
  if (!wrap || !svg) return;
  const box = svg.viewBox?.baseVal;
  const vbW = box?.width || svg.getBoundingClientRect().width;
  const vbH = box?.height || svg.getBoundingClientRect().height;
  const rect = els.preview.getBoundingClientRect();
  const pad = 20;
  const s = Math.min((rect.width - pad) / vbW, (rect.height - pad) / vbH);
  view.scale = Number.isFinite(s) && s > 0 ? s : 1;
  view.tx = 0;
  view.ty = 0;
  applyTransform();
}

function applyLayerToggles() {
  const wrap = getSvgWrap();
  const svg = wrap?.querySelector("svg");
  if (!svg) return;
  const cut = svg.querySelector("#CUT");
  const engrave = svg.querySelector("#ENGRAVE");
  if (cut) cut.style.display = els.showCut.checked ? "" : "none";
  if (engrave) engrave.style.display = els.showLabels.checked ? "" : "none";
}

function attachHoverHighlight() {
  const wrap = getSvgWrap();
  const svg = wrap?.querySelector("svg");
  if (!svg) return;
  const cut = svg.querySelector("#CUT");
  if (!cut) return;
  cut.querySelectorAll(":scope > g[id]").forEach((g) => {
    g.addEventListener("mouseenter", () => {
      g.classList.add("hilite");
      setStatus(`Hover: ${g.id}`);
    });
    g.addEventListener("mouseleave", () => {
      g.classList.remove("hilite");
      setStatus("Ready.");
    });
  });
}

els.btnGenerate.addEventListener("click", () => {
  generateSvg().catch((e) => {
    console.error(e);
    setStatus(`Error: ${e?.message ?? e}`);
    els.preview.innerHTML = `<pre>${escapeHtml(String(e?.stack ?? e))}</pre>`;
  });
});

els.btnCalibration.addEventListener("click", () => {
  generateCalibration().catch((e) => {
    console.error(e);
    setStatus(`Error: ${e?.message ?? e}`);
    els.preview.innerHTML = `<pre>${escapeHtml(String(e?.stack ?? e))}</pre>`;
  });
});

els.btnBundle?.addEventListener("click", () => {
  downloadBundleZip().catch((e) => {
    console.error(e);
    setStatus(`Error: ${e?.message ?? e}`);
    els.preview.innerHTML = `<pre>${escapeHtml(String(e?.stack ?? e))}</pre>`;
  });
});

els.studentMode?.addEventListener("change", () => setStudentMode(els.studentMode.checked));
els.mechanism?.addEventListener("change", () => {
  els.preset.value = els.mechanism.value;
});

els.fit?.addEventListener("input", () => setFitPreset(Number(els.fit.value)));
els.clearance?.addEventListener("input", () => {
  els.fitReadout.textContent = "Fit: Custom (using Joint clearance)";
  computeDerived();
});

[els.dimMode, els.innerWidth, els.innerDepth, els.innerHeight, els.thickness, els.kerf].forEach((el) => {
  el?.addEventListener("input", computeDerived);
});

els.zoomIn?.addEventListener("click", () => {
  view.scale = Math.min(6, view.scale * 1.15);
  applyTransform();
});
els.zoomOut?.addEventListener("click", () => {
  view.scale = Math.max(0.1, view.scale / 1.15);
  applyTransform();
});
els.fitView?.addEventListener("click", () => fitToView());

els.showCut?.addEventListener("change", applyLayerToggles);
els.showLabels?.addEventListener("change", applyLayerToggles);

init().catch((e) => {
  console.error(e);
  setStatus(`Failed to initialize: ${e?.message ?? e}`);
  els.preview.innerHTML = `<pre>${escapeHtml(String(e?.stack ?? e))}</pre>`;
});

// Initial UI state
setStudentMode(true);
setFitPreset(1);
computeDerived();
