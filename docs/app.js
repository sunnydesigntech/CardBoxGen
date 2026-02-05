// Runs the Python generator in the browser via Pyodide.
// This site is intended for GitHub Pages hosting (no backend).

import { loadPyodide } from "https://cdn.jsdelivr.net/pyodide/v0.25.1/full/pyodide.mjs";

const APP_VERSION = "0.4";
const LANG_STORAGE_KEY = "cardboxgen.lang";

let currentLang = "en";
let dict = null;

function getPath(obj, key) {
  if (!obj) return null;
  return key.split(".").reduce((acc, part) => (acc && typeof acc === "object" ? acc[part] : null), obj);
}

function t(key, vars = null) {
  const raw = getPath(dict, key);
  const base = typeof raw === "string" ? raw : key;
  if (!vars) return base;
  return base.replace(/\{\{(\w+)\}\}/g, (_, name) => (vars[name] ?? ""));
}

async function loadLanguage(lang) {
  const safeLang = ["en", "zh-Hant", "zh-Hans"].includes(lang) ? lang : "en";
  const resp = await fetch(`./i18n/${safeLang}.json`, { cache: "no-store" });
  if (!resp.ok) throw new Error(`Failed to load i18n: ${resp.status}`);
  dict = await resp.json();
  currentLang = safeLang;
  localStorage.setItem(LANG_STORAGE_KEY, safeLang);
  document.documentElement.lang = safeLang.startsWith("zh") ? "zh" : "en";
  applyTranslations();
  rebuildHelpContent();
  buildHelpDrawer();
  buildFaqDrawer();
  decorateHelpIcons();
}

function detectInitialLanguage() {
  const saved = localStorage.getItem(LANG_STORAGE_KEY);
  if (saved) return saved;
  const nav = (navigator.language || "en").toLowerCase();
  if (nav.startsWith("zh")) {
    // Heuristic: treat zh-tw/hk/mo as Hant, else Hans.
    if (nav.includes("tw") || nav.includes("hk") || nav.includes("mo") || nav.includes("hant")) return "zh-Hant";
    return "zh-Hans";
  }
  return "en";
}

function applyTranslations() {
  document.querySelectorAll("[data-i18n]").forEach((el) => {
    const key = el.getAttribute("data-i18n");
    const val = t(key);
    if (val && val !== key) el.textContent = val;
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
    const key = el.getAttribute("data-i18n-placeholder");
    const val = t(key);
    if (val && val !== key) el.setAttribute("placeholder", val);
  });
}

const els = {
  langSelect: document.getElementById("langSelect"),
  helpDrawerBtn: document.getElementById("helpDrawerBtn"),
  helpDrawer: document.getElementById("helpDrawer"),
  helpDrawerClose: document.getElementById("helpDrawerClose"),
  helpDrawerBody: document.getElementById("helpDrawerBody"),
  helpSearch: document.getElementById("helpSearch"),
  faqDrawerBtn: document.getElementById("faqDrawerBtn"),
  faqDrawer: document.getElementById("faqDrawer"),
  faqDrawerClose: document.getElementById("faqDrawerClose"),
  faqDrawerBody: document.getElementById("faqDrawerBody"),
  faqSearch: document.getElementById("faqSearch"),
  drawerOverlay: document.getElementById("drawerOverlay"),
  popover: document.getElementById("popover"),
  controlsToggle: document.getElementById("controlsToggle"),
  controlsPanel: document.getElementById("controlsPanel"),
  mobileGenerate: document.getElementById("mobileGenerate"),
  mobileDownload: document.getElementById("mobileDownload"),
  mobileBundle: document.getElementById("mobileBundle"),

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

  step1Badge: document.getElementById("step1Badge"),
  step2Badge: document.getElementById("step2Badge"),
  step3Badge: document.getElementById("step3Badge"),

  zoomOut: document.getElementById("zoomOut"),
  zoomIn: document.getElementById("zoomIn"),
  fitView: document.getElementById("fitView"),
  showCut: document.getElementById("showCut"),
  showLabels: document.getElementById("showLabels"),
};

function setStatus(msg) {
  els.status.textContent = msg;
}

function setStatusKey(key, vars = null) {
  setStatus(t(key, vars));
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
let lastDownloadFilename = null;
let lastDownloadUrl = null;
let pythonWarnings = [];
let calibrationGeneratedOnce = false;

const FIT_PRESETS = [0.0, 0.1, 0.2];

const HELP_CATEGORY_ORDER = [
  "Project",
  "Dimensions",
  "Laser fit",
  "Tabs",
  "Layout",
  "Preset options",
  "Troubleshooting",
];

const HELP_CATEGORY_BY_KEY = {
  dispenseType: "Project",
  storageTarget: "Project",
  dispenseTarget: "Project",
  mechanism: "Project",
  preset: "Project",

  dimensionMode: "Dimensions",
  innerWidth: "Dimensions",
  innerDepth: "Dimensions",
  innerHeight: "Dimensions",
  thickness: "Dimensions",

  fit: "Laser fit",
  kerf: "Laser fit",
  clearance: "Laser fit",
  calSet: "Laser fit",
  fingerWidth: "Laser fit",
  minTabs: "Laser fit",

  holdingTabs: "Tabs",
  tabWidth: "Tabs",

  sheetWidth: "Layout",
  margin: "Layout",
  padding: "Layout",
  stroke: "Layout",
  labelsToggle: "Layout",
  lid: "Layout",

  frontHeight: "Preset options",
  scoop: "Preset options",
  scoopRadius: "Preset options",
  scoopDepth: "Preset options",
  slotWidth: "Preset options",
  slotHeight: "Preset options",
  slotY: "Preset options",

  troubleshooting: "Troubleshooting",
};

let helpContent = {};

function arr(v) {
  return Array.isArray(v) ? v : [];
}

function rebuildHelpContent() {
  const helpObj = getPath(dict, "help") || {};
  const out = {};
  Object.keys(helpObj).forEach((k) => {
    const base = getPath(dict, `help.${k}`) || {};
    out[k] = {
      key: k,
      category: HELP_CATEGORY_BY_KEY[k] || "Other",
      title: base.title || k,
      short: base.short || "",
      meaning: base.meaning || base.what || "",
      decide: arr(base.decide),
      typical: arr(base.typical),
      pitfalls: arr(base.pitfalls),
      wrong: arr(base.wrong),
      example: base.example || "",
    };
  });

  if (!out.troubleshooting) {
    out.troubleshooting = {
      key: "troubleshooting",
      category: "Troubleshooting",
      title: t("faqUi.troubleshootingTitle"),
      short: t("faqUi.troubleshootingShort"),
      meaning: "",
      decide: [],
      typical: [],
      pitfalls: [],
      wrong: [],
      example: "",
    };
  }

  helpContent = out;
}

function computeDerived() {
  const thickness = num(els.thickness, 3);
  const kerf = num(els.kerf, 0.2);
  const c = num(els.clearance, 0.1);
  const drawnSlot = thickness + c - kerf;
  const expectedFinalSlot = thickness + c;
  els.jointRule.textContent = t("readouts.jointRule", { drawn: drawnSlot.toFixed(2), final: expectedFinalSlot.toFixed(2) });

  const w = num(els.innerWidth, 135);
  const d = num(els.innerDepth, 90);
  const h = num(els.innerHeight, 225);
  if (els.dimMode.value === "internal") {
    const outerW = w + 2 * thickness;
    const outerD = d + 2 * thickness;
    const outerH = h + thickness;
    els.sizeReadout.textContent = t("readouts.computedExternal", {
      w: outerW.toFixed(1),
      d: outerD.toFixed(1),
      h: outerH.toFixed(1),
    });
  } else {
    const innerW = w - 2 * thickness;
    const innerD = d - 2 * thickness;
    const innerH = h - thickness;
    els.sizeReadout.textContent = t("readouts.computedInternal", {
      w: innerW.toFixed(1),
      d: innerD.toFixed(1),
      h: innerH.toFixed(1),
    });
  }

  updateStepBadges();
  renderWarnings();
}

function setFitPreset(index) {
  const i = Math.max(0, Math.min(2, Number(index)));
  const c = FIT_PRESETS[i];
  els.fit.value = String(i);
  els.clearance.value = c.toFixed(2);
  els.fitReadout.textContent = i === 0 ? t("fit.tight") : i === 1 ? t("fit.normal") : t("fit.loose");
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
  setStatusKey("status.loadingPyodide");
  pyodide = await loadPyodide({});

  setStatusKey("status.loadingModule");
  const resp = await fetch("./cardboxgen_v0_1.py", { cache: "no-store" });
  if (!resp.ok) throw new Error(`Failed to load Python module: ${resp.status}`);
  const code = await resp.text();

  // Write into the virtual FS and import as a module so it doesn't run the CLI.
  pyodide.FS.writeFile("cardboxgen_v0_1.py", code);
  await pyodide.runPythonAsync(`import importlib\ncard = importlib.import_module('cardboxgen_v0_1')`);

  els.btnGenerate.disabled = false;
  if (els.btnCalibration) els.btnCalibration.disabled = false;
  els.btnBundle.disabled = false;
  els.btnGenerate.textContent = t("actions.generate");

  if (els.mobileGenerate) els.mobileGenerate.disabled = false;
  if (els.mobileBundle) els.mobileBundle.disabled = false;

  // Show something useful immediately on first load.
  try {
    await generateSvg();
  } catch (e) {
    console.error(e);
    setStatus(`${t("status.ready")} (${e?.message ?? e})`);
  }
}

function updateStepBadges() {
  const step1Complete = !!els.storageTarget.value.trim() && !!els.dispenseTarget.value.trim();
  const step2Complete = !!(els.mechanism?.value ?? "").trim();
  const thicknessSet = (els.thickness.value ?? "").trim() !== "";
  const kerfKnown = (els.kerf.value ?? "").trim() !== "";
  const step3Complete = thicknessSet && (kerfKnown || calibrationGeneratedOnce);

  if (els.step1Badge) els.step1Badge.textContent = step1Complete ? t("steps.complete") : t("steps.incomplete");
  if (els.step2Badge) els.step2Badge.textContent = step2Complete ? t("steps.complete") : t("steps.incomplete");
  if (els.step3Badge) els.step3Badge.textContent = step3Complete ? t("steps.complete") : t("steps.incomplete");
}

function collectUiWarningKeys(p) {
  const keys = [];
  if (p.kerf_mm >= p.thickness) keys.push("warnings.kerfTooBig");

  // Heuristic: for ~3mm stock, >0.4mm clearance is usually overly loose.
  if (p.thickness <= 3.5 && p.clearance_mm > 0.4) keys.push("warnings.clearanceLarge");

  if ((p.min_fingers ?? 3) < 3) keys.push("warnings.minTabs");

  if (p.preset === "dispenser_slot_front") {
    const sw = p.slot_width;
    const sh = p.slot_height;
    const sy = p.slot_y_from_bottom;
    const ok =
      Number.isFinite(sw) &&
      Number.isFinite(sh) &&
      Number.isFinite(sy) &&
      sw > 0 &&
      sh > 0 &&
      sy >= 0 &&
      sw <= p.inner_width &&
      sy + sh <= p.inner_height;
    if (!ok) keys.push("warnings.slotInvalid");
  }

  return keys;
}

function renderWarnings() {
  const p = buildParams();
  const uiKeys = collectUiWarningKeys(p);
  const uiWarnings = uiKeys.map((k) => t(k));

  const allPython = Array.isArray(pythonWarnings) ? pythonWarnings : [];
  const hasAny = uiWarnings.length || allPython.length;
  if (!hasAny) {
    els.warnings.hidden = true;
    els.warnings.innerHTML = "";
    return;
  }

  const uiList = uiWarnings.length
    ? `<div class="warnBlock"><strong>${escapeHtml(t("warnings.title"))}</strong><ul>${uiWarnings
        .map((w) => `<li>${escapeHtml(String(w))}</li>`)
        .join("")}</ul></div>`
    : "";

  const pyList = allPython.length
    ? `<div class="warnBlock"><strong>${escapeHtml(t("warnings.title"))}</strong><ul>${allPython
        .map((w) => `<li>${escapeHtml(String(w))}</li>`)
        .join("")}</ul></div>`
    : "";

  els.warnings.hidden = false;
  els.warnings.innerHTML = uiList + pyList;
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
  pythonWarnings = [];
  renderWarnings();

  const p = buildParams();
  setStatusKey("status.generatingSvg");

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
  pythonWarnings = warnings;

  renderWarnings();

  // Preview (inline SVG) + download.
  // Wrap for pan/zoom transforms.
  els.preview.innerHTML = `<div id="svgWrap">${svg}</div>`;
  applyLayerToggles();
  attachHoverHighlight();
  userZoomed = false;
  fitToView();
  const blob = new Blob([svg], { type: "image/svg+xml" });
  const url = URL.createObjectURL(blob);
  if (lastDownloadUrl) URL.revokeObjectURL(lastDownloadUrl);
  lastDownloadUrl = url;
  lastDownloadFilename = `cardbox_${p.preset}.svg`;

  els.download.href = url;
  els.download.hidden = false;
  els.download.textContent = t("actions.downloadSvg");
  els.download.download = lastDownloadFilename;

  if (els.mobileDownload) els.mobileDownload.disabled = false;

  setStatusKey("status.readyFile", { filename: lastDownloadFilename });
}

async function getCalibrationSvgString() {
  const thickness = num(els.thickness, 3);
  const kerf = num(els.kerf, 0.2);
  const calSet = els.calSet?.value ?? "student";

  calibrationGeneratedOnce = true;
  updateStepBadges();

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
  setStatusKey("status.generatingCalibration");
  const thickness = num(els.thickness, 3);
  const kerf = num(els.kerf, 0.2);
  const calSet = els.calSet?.value ?? "student";

  calibrationGeneratedOnce = true;
  updateStepBadges();

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
  userZoomed = false;
  fitToView();
  const blob = new Blob([svg], { type: "image/svg+xml" });
  const url = URL.createObjectURL(blob);
  if (lastDownloadUrl) URL.revokeObjectURL(lastDownloadUrl);
  lastDownloadUrl = url;
  lastDownloadFilename = `calibration.svg`;
  els.download.href = url;
  els.download.hidden = false;
  els.download.textContent = t("actions.downloadCalibration");
  els.download.download = lastDownloadFilename;

  if (els.mobileDownload) els.mobileDownload.disabled = false;

  setStatusKey("status.readyFile", { filename: lastDownloadFilename });
}

const MIN_SCALE = 0.1;
const MAX_SCALE = 6.0;

let userZoomed = false;
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
  const fitted = Number.isFinite(s) && s > 0 ? s : 1;
  view.scale = Math.max(MIN_SCALE, Math.min(MAX_SCALE, fitted));
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
      setStatusKey("status.hover", { name: g.id });
    });
    g.addEventListener("mouseleave", () => {
      g.classList.remove("hilite");
      setStatusKey("status.ready");
    });
  });
}

function closePopover() {
  if (!els.popover) return;
  els.popover.hidden = true;
  els.popover.innerHTML = "";
  els.popover.dataset.anchor = "";
}

function positionPopover(anchorRect) {
  const pop = els.popover;
  if (!pop) return;
  const pad = 10;
  const w = pop.offsetWidth || 320;
  const h = pop.offsetHeight || 220;
  const maxX = window.innerWidth - pad - w;
  const maxY = window.innerHeight - pad - h;

  let x = Math.min(Math.max(pad, anchorRect.left), maxX);
  let y = anchorRect.bottom + 8;
  if (y > maxY) y = Math.max(pad, anchorRect.top - h - 8);
  pop.style.left = `${x}px`;
  pop.style.top = `${y}px`;
}

function getHelp(helpKey) {
  return helpContent?.[helpKey] || {
    key: helpKey,
    category: "Other",
    title: helpKey,
    short: "",
    meaning: "",
    decide: [],
    typical: [],
    pitfalls: [],
    wrong: [],
    example: "",
  };
}

function renderHelpListBlock(label, items) {
  if (!items || !items.length) return "";
  return (
    `<div class="popoverSection">` +
    `<div class="popoverSectionTitle">${escapeHtml(label)}</div>` +
    `<ul class="popoverList">${items.map((x) => `<li>${escapeHtml(String(x))}</li>`).join("")}</ul>` +
    `</div>`
  );
}

function renderHelpHtml(helpKey, { includeOpenHelp = true } = {}) {
  const c = getHelp(helpKey);
  const title = `<div class="popoverTitle">${escapeHtml(String(c.title))}</div>`;
  const short = c.short ? `<div class="popoverShort">${escapeHtml(String(c.short))}</div>` : "";
  const meaning = c.meaning ? `<div class="popoverShort">${escapeHtml(String(c.meaning))}</div>` : "";

  const decide = renderHelpListBlock(t("helpSections.decide"), c.decide);
  const typical = renderHelpListBlock(t("helpSections.typical"), c.typical);
  const pitfalls = renderHelpListBlock(t("helpSections.pitfalls"), c.pitfalls);
  const wrong = renderHelpListBlock(t("helpSections.wrong"), c.wrong);
  const example = c.example
    ? `<div class="popoverSection"><div class="popoverSectionTitle">${escapeHtml(t("helpSections.example"))}</div><div class="popoverShort">${escapeHtml(String(c.example))}</div></div>`
    : "";
  const openHelp = includeOpenHelp
    ? `<div class="popoverSection"><button type="button" class="ghostBtn" data-open-help="${escapeHtml(helpKey)}">${escapeHtml(t("mode.help"))}</button></div>`
    : "";
  return title + short + meaning + decide + typical + pitfalls + wrong + example + openHelp;
}

function renderHelpDetailsHtml(helpKey) {
  const c = getHelp(helpKey);
  const short = c.short ? `<div class="popoverShort">${escapeHtml(String(c.short))}</div>` : "";
  const meaning = c.meaning ? `<div class="popoverShort">${escapeHtml(String(c.meaning))}</div>` : "";
  const decide = renderHelpListBlock(t("helpSections.decide"), c.decide);
  const typical = renderHelpListBlock(t("helpSections.typical"), c.typical);
  const pitfalls = renderHelpListBlock(t("helpSections.pitfalls"), c.pitfalls);
  const wrong = renderHelpListBlock(t("helpSections.wrong"), c.wrong);
  const example = c.example
    ? `<div class="popoverSection"><div class="popoverSectionTitle">${escapeHtml(t("helpSections.example"))}</div><div class="popoverShort">${escapeHtml(String(c.example))}</div></div>`
    : "";
  return short + meaning + decide + typical + pitfalls + wrong + example;
}

const POPOVER_CLOSE_DELAY_MS = 150;
const popoverState = {
  key: null,
  anchorEl: null,
  pinned: false,
  hoverIcon: false,
  hoverPopover: false,
  closeTimer: null,
};

function clearPopoverCloseTimer() {
  if (popoverState.closeTimer) {
    clearTimeout(popoverState.closeTimer);
    popoverState.closeTimer = null;
  }
}

function closePopoverAndClearPin() {
  popoverState.pinned = false;
  popoverState.hoverIcon = false;
  popoverState.hoverPopover = false;
  clearPopoverCloseTimer();
  closePopover();
  popoverState.key = null;
  popoverState.anchorEl = null;
}

function schedulePopoverClose() {
  clearPopoverCloseTimer();
  popoverState.closeTimer = setTimeout(() => {
    popoverState.closeTimer = null;
    if (popoverState.pinned || popoverState.hoverIcon || popoverState.hoverPopover) return;
    closePopoverAndClearPin();
  }, POPOVER_CLOSE_DELAY_MS);
}

function openPopover(helpKey, anchorEl) {
  const pop = els.popover;
  if (!pop || !anchorEl) return;
  popoverState.key = helpKey;
  popoverState.anchorEl = anchorEl;
  pop.innerHTML = renderHelpHtml(helpKey);
  pop.hidden = false;
  pop.dataset.anchor = helpKey;
  positionPopover(anchorEl.getBoundingClientRect());
}

function decorateHelpIcons() {
  document.querySelectorAll("label[data-help]").forEach((label) => {
    if (label.querySelector(":scope > .infoBtn")) return;
    const helpKey = label.getAttribute("data-help");
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "infoBtn";
    btn.textContent = "i";
    btn.setAttribute("aria-label", `Info: ${helpKey}`);
    btn.addEventListener("pointerenter", () => {
      popoverState.hoverIcon = true;
      clearPopoverCloseTimer();
      openPopover(helpKey, btn);
    });
    btn.addEventListener("pointerleave", () => {
      popoverState.hoverIcon = false;
      if (!popoverState.pinned) schedulePopoverClose();
    });
    btn.addEventListener("focus", () => {
      popoverState.hoverIcon = true;
      clearPopoverCloseTimer();
      openPopover(helpKey, btn);
    });
    btn.addEventListener("blur", () => {
      popoverState.hoverIcon = false;
      if (!popoverState.pinned) schedulePopoverClose();
    });
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();

      const same = popoverState.key === helpKey;
      if (same && popoverState.pinned) {
        popoverState.pinned = false;
        if (!(popoverState.hoverIcon || popoverState.hoverPopover)) closePopoverAndClearPin();
        return;
      }
      popoverState.pinned = true;
      openPopover(helpKey, btn);
    });
    label.appendChild(btn);
  });
}

function syncOverlay() {
  if (!els.drawerOverlay) return;
  const controlsOpen = document.body.classList.contains("drawerOpen");
  const helpOpen = !!els.helpDrawer && !els.helpDrawer.hidden;
  const faqOpen = !!els.faqDrawer && !els.faqDrawer.hidden;
  els.drawerOverlay.hidden = !(controlsOpen || helpOpen || faqOpen);
}

function openHelpDrawer(targetKey = null) {
  if (!els.helpDrawer) return;
  els.helpDrawer.hidden = false;
  syncOverlay();
  if (targetKey) {
    const el = document.getElementById(`help-${targetKey}`);
    el?.scrollIntoView({ block: "start" });
  }
}
function closeHelpDrawer() {
  if (!els.helpDrawer) return;
  els.helpDrawer.hidden = true;
  syncOverlay();
}

function openFaqDrawer() {
  if (!els.faqDrawer) return;
  els.faqDrawer.hidden = false;
  syncOverlay();
}
function closeFaqDrawer() {
  if (!els.faqDrawer) return;
  els.faqDrawer.hidden = true;
  syncOverlay();
}

function helpMatchesQuery(h, q) {
  if (!q) return true;
  const hay = [
    h.key,
    h.category,
    h.title,
    h.short,
    h.meaning,
    ...(h.decide || []),
    ...(h.typical || []),
    ...(h.pitfalls || []),
    ...(h.wrong || []),
    h.example,
  ]
    .filter(Boolean)
    .join("\n")
    .toLowerCase();
  return hay.includes(q);
}

function buildHelpDrawer() {
  if (!els.helpDrawerBody) return;

  const q = (els.helpSearch?.value || "").trim().toLowerCase();
  const keys = Object.keys(helpContent || {});
  const byCategory = new Map();
  keys.forEach((k) => {
    const h = getHelp(k);
    if (!helpMatchesQuery(h, q)) return;
    const cat = h.category || "Other";
    if (!byCategory.has(cat)) byCategory.set(cat, []);
    byCategory.get(cat).push(k);
  });

  const categories = [...HELP_CATEGORY_ORDER, ...[...byCategory.keys()].filter((c) => !HELP_CATEGORY_ORDER.includes(c))];
  const html = categories
    .map((cat) => {
      const list = byCategory.get(cat) || [];
      if (!list.length) return "";
      const items = list
        .map((k) => {
          const h = getHelp(k);
          return (
            `<section class="helpTopic" id="help-${escapeHtml(k)}">` +
            `<h4>${escapeHtml(String(h.title))}</h4>` +
            `<div class="helpKeyMeta">${escapeHtml(String(cat))}</div>` +
            `<div class="helpTopicBody">${renderHelpDetailsHtml(k)}</div>` +
            `</section>`
          );
        })
        .join("");
      return `<div class="helpCategory">${escapeHtml(cat)}</div>${items}`;
    })
    .join("");

  els.helpDrawerBody.innerHTML = html || `<p class="hint">${escapeHtml(t("helpUi.noResults"))}</p>`;
}

const FAQ_DATA = {
  Project: [
    {
      q: "Internal vs external dimensions — which should I use?",
      a: "Use Internal when you care about the space that must fit your items. Use External when you must match an outside footprint. Dimension mode converts for you using material thickness.",
      links: ["dimensionMode", "thickness"],
    },
    {
      q: "How do I size W/D/H from a storage target and dispense target?",
      a: "Start with the item’s real size. Add a little clearance so items don’t jam. Decide the storage stack height and the dispense opening separately; then choose a mechanism/preset that matches the behavior you want.",
      links: ["storageTarget", "dispenseTarget", "mechanism", "preset"],
    },
    {
      q: "Which mechanism should I choose for flowing vs stacking items?",
      a: "Stacking is for flat items (cards/tiles) and is more predictable. Flowing is only for dry solids that can pour; it’s not recommended for cards.",
      links: ["dispenseType", "mechanism"],
    },
  ],
  "Laser fit": [
    {
      q: "What is kerf? Why does it matter?",
      a: "Kerf is the width of material removed by the laser cut. If you ignore it, tabs/slots won’t match the real cut size, and joints can become too tight or too loose.",
      links: ["kerf"],
    },
    {
      q: "What is joint clearance? Tight vs loose symptoms",
      a: "Clearance controls how easily joints assemble. Too tight: hard to press together, material may tear. Too loose: wobbly joints and gaps. Adjust in small steps (e.g. 0.05mm).",
      links: ["clearance", "fit"],
    },
    {
      q: "My joints are too tight / too loose — what do I change?",
      a: "Too tight: increase Joint clearance a little, or verify kerf with the Fit Test. Too loose: decrease Joint clearance. Keep thickness correct.",
      links: ["clearance", "kerf", "thickness"],
    },
  ],
  Preview: [
    {
      q: "Why preview scale looks wrong / how to check mm scale",
      a: "The preview is for layout and sanity-checking. Always verify in your laser software that units are mm and that a known dimension matches (e.g. inner width). Use the Fit button to zoom to the drawing.",
      links: ["innerWidth"],
    },
    {
      q: "Preview/export troubleshooting",
      a: "If your laser software changes size on import, confirm SVG units, viewBox handling, and any DPI import setting. Then measure a known dimension.",
      links: [],
    },
  ],
};

function buildFaqDrawer() {
  if (!els.faqDrawerBody) return;
  const q = (els.faqSearch?.value || "").trim().toLowerCase();
  const cats = Object.keys(FAQ_DATA);
  const blocks = cats
    .map((cat) => {
      const items = (FAQ_DATA[cat] || []).filter((it) => {
        if (!q) return true;
        const hay = `${it.q}\n${it.a}`.toLowerCase();
        return hay.includes(q);
      });
      if (!items.length) return "";
      const inner = items
        .map((it) => {
          const linksHtml = (it.links || []).length
            ? `<p>${it.links
                .map((k) => `<a href="#" data-open-help="${escapeHtml(k)}">${escapeHtml(getHelp(k).title || k)}</a>`)
                .join(" · ")}</p>`
            : "";
          return `<section class="faqItem"><h4>${escapeHtml(it.q)}</h4><p>${escapeHtml(it.a)}</p>${linksHtml}</section>`;
        })
        .join("");
      return `<div class="helpCategory">${escapeHtml(cat)}</div>${inner}`;
    })
    .join("");
  els.faqDrawerBody.innerHTML = blocks || `<p class="hint">${escapeHtml(t("faqUi.noResults"))}</p>`;
}

function updateHeaderHeightVar() {
  const header = document.querySelector(".header");
  const h = header ? header.getBoundingClientRect().height : 120;
  document.documentElement.style.setProperty("--header-h", `${Math.ceil(h)}px`);
}

els.btnGenerate.addEventListener("click", () => {
  generateSvg().catch((e) => {
    console.error(e);
    setStatusKey("status.error", { message: e?.message ?? e });
    els.preview.innerHTML = `<pre>${escapeHtml(String(e?.stack ?? e))}</pre>`;
  });
});

els.btnCalibration?.addEventListener("click", () => {
  generateCalibration().catch((e) => {
    console.error(e);
    setStatusKey("status.error", { message: e?.message ?? e });
    els.preview.innerHTML = `<pre>${escapeHtml(String(e?.stack ?? e))}</pre>`;
  });
});

els.btnBundle?.addEventListener("click", () => {
  downloadBundleZip().catch((e) => {
    console.error(e);
    setStatusKey("status.error", { message: e?.message ?? e });
    els.preview.innerHTML = `<pre>${escapeHtml(String(e?.stack ?? e))}</pre>`;
  });
});

els.mobileGenerate?.addEventListener("click", () => els.btnGenerate?.click());
els.mobileBundle?.addEventListener("click", () => els.btnBundle?.click());
els.mobileDownload?.addEventListener("click", () => {
  if (els.download?.hidden) return;
  els.download?.click();
});

els.controlsToggle?.addEventListener("click", () => {
  document.body.classList.toggle("drawerOpen");
  syncOverlay();
});

els.drawerOverlay?.addEventListener("click", () => {
  document.body.classList.remove("drawerOpen");
  closeHelpDrawer();
  closeFaqDrawer();
  closePopoverAndClearPin();
  syncOverlay();
});

els.helpDrawerBtn?.addEventListener("click", () => openHelpDrawer());
els.helpDrawerClose?.addEventListener("click", () => closeHelpDrawer());
els.faqDrawerBtn?.addEventListener("click", () => openFaqDrawer());
els.faqDrawerClose?.addEventListener("click", () => closeFaqDrawer());

els.helpSearch?.addEventListener("input", () => buildHelpDrawer());
els.faqSearch?.addEventListener("input", () => buildFaqDrawer());

els.popover?.addEventListener("pointerenter", () => {
  popoverState.hoverPopover = true;
  clearPopoverCloseTimer();
});
els.popover?.addEventListener("pointerleave", () => {
  popoverState.hoverPopover = false;
  if (!popoverState.pinned) schedulePopoverClose();
});

els.popover?.addEventListener("click", (e) => {
  const btn = e.target.closest("[data-open-help]");
  if (btn) {
    const k = btn.getAttribute("data-open-help");
    closePopoverAndClearPin();
    openHelpDrawer(k);
  }
});

els.faqDrawerBody?.addEventListener("click", (e) => {
  const btn = e.target.closest("[data-open-help]");
  if (!btn) return;
  e.preventDefault();
  const k = btn.getAttribute("data-open-help");
  if (!k) return;
  closeFaqDrawer();
  openHelpDrawer(k);
});

document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    closePopoverAndClearPin();
    closeHelpDrawer();
    closeFaqDrawer();
    document.body.classList.remove("drawerOpen");
    syncOverlay();
  }
});

document.addEventListener("click", (e) => {
  const inPopover = els.popover && !els.popover.hidden && els.popover.contains(e.target);
  const isInfoBtn = e.target?.classList?.contains("infoBtn");
  if (!inPopover && !isInfoBtn) closePopoverAndClearPin();
});

els.studentMode?.addEventListener("change", () => setStudentMode(els.studentMode.checked));
els.mechanism?.addEventListener("change", () => {
  els.preset.value = els.mechanism.value;
});

els.fit?.addEventListener("input", () => setFitPreset(Number(els.fit.value)));
els.clearance?.addEventListener("input", () => {
  els.fitReadout.textContent = t("fit.custom");
  computeDerived();
});

[els.dimMode, els.innerWidth, els.innerDepth, els.innerHeight, els.thickness, els.kerf].forEach((el) => {
  el?.addEventListener("input", computeDerived);
});

els.zoomIn?.addEventListener("click", () => {
  userZoomed = true;
  view.scale = Math.max(MIN_SCALE, Math.min(MAX_SCALE, view.scale * 1.15));
  applyTransform();
});
els.zoomOut?.addEventListener("click", () => {
  userZoomed = true;
  view.scale = Math.max(MIN_SCALE, Math.min(MAX_SCALE, view.scale / 1.15));
  applyTransform();
});
els.fitView?.addEventListener("click", () => {
  userZoomed = false;
  fitToView();
});

els.showCut?.addEventListener("change", applyLayerToggles);
els.showLabels?.addEventListener("change", applyLayerToggles);

async function main() {
  currentLang = detectInitialLanguage();
  if (els.langSelect) els.langSelect.value = currentLang;
  await loadLanguage(currentLang);

  if (els.mobileDownload) els.mobileDownload.disabled = true;

  els.langSelect?.addEventListener("change", async () => {
    const v = els.langSelect.value;
    await loadLanguage(v);
    computeDerived();
  });

  updateHeaderHeightVar();
  window.addEventListener("resize", () => {
    updateHeaderHeightVar();
    if (!userZoomed) fitToView();
  });

  // Initial UI state
  setStudentMode(true);
  setFitPreset(1);
  computeDerived();

  await init();
}

main().catch((e) => {
  console.error(e);
  setStatusKey("status.initFailed", { message: e?.message ?? e });
});
