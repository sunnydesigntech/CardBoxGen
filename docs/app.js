// Runs the Python generator in the browser via Pyodide.
// This site is intended for GitHub Pages hosting (no backend).

import { loadPyodide } from "https://cdn.jsdelivr.net/pyodide/v0.25.1/full/pyodide.mjs";

const APP_VERSION = "0.6";
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

function tFromDict(d, key, vars = null) {
  const raw = getPath(d, key);
  const base = typeof raw === "string" ? raw : key;
  if (!vars) return base;
  return base.replace(/\{\{(\w+)\}\}/g, (_, name) => (vars[name] ?? ""));
}

const i18nCache = new Map();
async function getI18nDict(lang) {
  const safeLang = ["en", "zh-Hant", "zh-Hans"].includes(lang) ? lang : "en";
  if (i18nCache.has(safeLang)) return i18nCache.get(safeLang);
  const resp = await fetch(`./i18n/${safeLang}.json`, { cache: "no-store" });
  if (!resp.ok) throw new Error(`Failed to load i18n: ${resp.status}`);
  const d = await resp.json();
  i18nCache.set(safeLang, d);
  return d;
}

async function loadLanguage(lang) {
  const safeLang = ["en", "zh-Hant", "zh-Hans"].includes(lang) ? lang : "en";
  const resp = await fetch(`./i18n/${safeLang}.json`, { cache: "no-store" });
  if (!resp.ok) throw new Error(`Failed to load i18n: ${resp.status}`);
  dict = await resp.json();
  i18nCache.set(safeLang, dict);
  currentLang = safeLang;
  localStorage.setItem(LANG_STORAGE_KEY, safeLang);
  document.documentElement.lang = safeLang.startsWith("zh") ? "zh" : "en";
  applyTranslations();
  rebuildHelpContent();
  rebuildFaqData();
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

  // v0.6 Step 1 — Client & context
  clientContext: document.getElementById("clientContext"),
  problemStatement: document.getElementById("problemStatement"),
  constraintNoCoins: document.getElementById("constraintNoCoins"),
  constraintNoLiquids: document.getElementById("constraintNoLiquids"),
  constraintPersonalUse: document.getElementById("constraintPersonalUse"),
  constraintChecks: document.querySelectorAll("#constraintNoCoins, #constraintNoLiquids, #constraintPersonalUse"),

  dispenseType: document.getElementById("dispenseType"),
  dispenseTargetType: document.getElementById("dispenseTargetType"),
  storageTarget: document.getElementById("storageTarget"),
  dispenseTarget: document.getElementById("dispenseTarget"),

  // v0.6 Step 2 — Requirements
  irregularShape: document.getElementById("irregularShape"),
  metricJam: document.getElementById("metricJam"),
  metricConsistency: document.getElementById("metricConsistency"),
  metricRefill: document.getElementById("metricRefill"),
  metricDurability: document.getElementById("metricDurability"),
  successMetrics: document.querySelectorAll("#metricJam, #metricConsistency, #metricRefill, #metricDurability"),

  // v0.6 Step 3 — Recommendation + justification
  mechanismRecs: document.getElementById("mechanismRecs"),
  mechanismJustification: document.getElementById("mechanismJustification"),

  mechanism: document.getElementById("mechanism"),

  // v0.5 Student item inputs
  cardWidth: document.getElementById("cardWidth"),
  cardHeight: document.getElementById("cardHeight"),
  capacityCards: document.getElementById("capacityCards"),
  maxPieceSize: document.getElementById("maxPieceSize"),

  // v0.5 mechanism params
  dividerBays: document.getElementById("dividerBays"),
  pocketCount: document.getElementById("pocketCount"),
  axleDiameter: document.getElementById("axleDiameter"),
  rampCount: document.getElementById("rampCount"),
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

  // v0.6 Step 4 — Reasoning + export
  reasoningInternal: document.getElementById("reasoningInternal"),
  reasoningExternal: document.getElementById("reasoningExternal"),
  reasoningOpenings: document.getElementById("reasoningOpenings"),
  exportAllLanguages: document.getElementById("exportAllLanguages"),

  step1Badge: document.getElementById("step1Badge"),
  step2Badge: document.getElementById("step2Badge"),
  step3Badge: document.getElementById("step3Badge"),
  step4Badge: document.getElementById("step4Badge"),

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
  const str = String(s ?? "");
  return str.replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;");
}

function escapeHtmlWithBreaks(s) {
  return escapeHtml(s).replaceAll("\n", "<br>");
}

let pyodide = null;
let lastSvg = null;
let lastParams = null;
let lastDownloadFilename = null;
let lastDownloadUrl = null;
let pythonWarnings = [];
let calibrationGeneratedOnce = false;

let lastDerived = null;
let lastAutoMechanism = null;
let studentMechanismManuallyChosen = false;

const FIT_PRESETS = [0.0, 0.1, 0.2];

const HELP_CATEGORY_ORDER = [
  "Project",
  "Dimensions",
  "Laser fit",
  "Tabs",
  "Layout",
  "Preset options",
  "Export",
  "Troubleshooting",
];

const HELP_CATEGORY_BY_KEY = {
  clientContext: "Project",
  problemStatement: "Project",
  constraints: "Project",
  dispenseType: "Project",
  dispenseTargetType: "Project",
  irregularShape: "Project",
  successMetrics: "Project",
  cardWidth: "Project",
  cardHeight: "Project",
  capacityCards: "Project",
  maxPieceSize: "Project",
  storageTarget: "Project",
  dispenseTarget: "Project",
  mechanism: "Project",
  mechanismJustification: "Project",
  exportAllLanguages: "Export",
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

  dividerBays: "Preset options",
  pocketCount: "Preset options",
  axleDiameter: "Preset options",
  rampCount: "Preset options",

  troubleshooting: "Troubleshooting",
};

let helpContent = {};

const DEFAULT_FAQ_DATA = {
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

let faqData = DEFAULT_FAQ_DATA;

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

function rebuildFaqData() {
  const fromDict = getPath(dict, "faq");
  if (fromDict && typeof fromDict === "object") {
    faqData = fromDict;
    return;
  }
  faqData = DEFAULT_FAQ_DATA;
}

function computeDerived() {
  const thickness = num(els.thickness, 3);
  const kerf = num(els.kerf, 0.2);
  const c = num(els.clearance, 0.1);
  const drawnSlot = thickness + c - kerf;
  const expectedFinalSlot = thickness + c;
  els.jointRule.textContent = t("readouts.jointRule", { drawn: drawnSlot.toFixed(2), final: expectedFinalSlot.toFixed(2) });

  const rawW = num(els.innerWidth, 135);
  const rawD = num(els.innerDepth, 90);
  const rawH = num(els.innerHeight, 225);

  let internal = { w: rawW, d: rawD, h: rawH };
  let external = { w: rawW, d: rawD, h: rawH };
  if (els.dimMode.value === "internal") {
    internal = { w: rawW, d: rawD, h: rawH };
    external = { w: rawW + 2 * thickness, d: rawD + 2 * thickness, h: rawH + thickness };
    els.sizeReadout.textContent = t("readouts.computedExternal", {
      w: external.w.toFixed(1),
      d: external.d.toFixed(1),
      h: external.h.toFixed(1),
    });
  } else {
    external = { w: rawW, d: rawD, h: rawH };
    internal = { w: rawW - 2 * thickness, d: rawD - 2 * thickness, h: rawH - thickness };
    els.sizeReadout.textContent = t("readouts.computedInternal", {
      w: internal.w.toFixed(1),
      d: internal.d.toFixed(1),
      h: internal.h.toFixed(1),
    });
  }

  const openings = {
    slot_w: num(els.slotWidth, 0),
    slot_h: num(els.slotHeight, 0),
    slot_y: num(els.slotY, 0),
  };

  lastDerived = {
    thickness,
    kerf,
    clearance: c,
    joint_rule: {
      drawn_slot_depth: drawnSlot,
      expected_final_slot_depth: expectedFinalSlot,
    },
    internal,
    external,
    openings,
  };

  if (els.reasoningInternal) {
    els.reasoningInternal.textContent = t("readouts.derivedInternal", {
      w: internal.w.toFixed(1),
      d: internal.d.toFixed(1),
      h: internal.h.toFixed(1),
    });
  }
  if (els.reasoningExternal) {
    els.reasoningExternal.textContent = t("readouts.derivedExternal", {
      w: external.w.toFixed(1),
      d: external.d.toFixed(1),
      h: external.h.toFixed(1),
    });
  }
  if (els.reasoningOpenings) {
    const preset = els.preset?.value ?? "";
    els.reasoningOpenings.textContent = t("readouts.derivedOpenings", {
      preset,
      w: Number.isFinite(openings.slot_w) ? openings.slot_w.toFixed(1) : "",
      h: Number.isFinite(openings.slot_h) ? openings.slot_h.toFixed(1) : "",
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

  if (!enabled) {
    studentMechanismManuallyChosen = false;
    lastAutoMechanism = null;
  }
  setStudentItemUi();
  rebuildMechanismRecommendations();
  updateStepBadges();
}

function setStudentItemUi() {
  const itemType = els.dispenseType?.value ?? "stacking";
  const stacking = itemType !== "flowing";
  document.getElementById("studentStackingSizeRow")?.toggleAttribute("hidden", !stacking);
  document.getElementById("studentStackingSizeRow2")?.toggleAttribute("hidden", !stacking);
  document.getElementById("studentStackingCapacityRow")?.toggleAttribute("hidden", !stacking);
  document.getElementById("studentFlowingSizeRow")?.toggleAttribute("hidden", stacking);
  document.getElementById("studentFlowingFlagsRow")?.toggleAttribute("hidden", stacking);
}

function chooseMechanismFromStudentInputs() {
  return recommendMechanismsFromStudentInputs()[0]?.id ?? "tray_open_front";
}

function recommendMechanismsFromStudentInputs() {
  const itemType = els.dispenseType?.value ?? "stacking";
  const target = els.dispenseTargetType?.value ?? "";
  const irregular = !!els.irregularShape?.checked;

  const out = [];
  const push = (id, reasonKey) => out.push({ id, reasonKey });

  if (itemType === "flowing") {
    if (target === "counted" && !irregular) {
      push("candy_rotary_wheel", "recs.reason.flowingCounted");
      push("candy_plinko", "recs.reason.flowingTolerant");
    } else {
      push("candy_plinko", "recs.reason.flowingTolerant");
      push("candy_rotary_wheel", "recs.reason.flowingCounted");
    }
    // Third option: keep a simple open-front tray as a fallback for non-dispensing storage prototypes.
    push("tray_open_front", "recs.reason.fallbackPrototype");
    return out.slice(0, 3);
  }

  // Stacking (cards / flat items)
  if (target === "one") {
    push("card_shoe_front_draw", "recs.reason.stackingOne");
    push("tray_open_front", "recs.reason.stackingGrab");
    push("divider_rack", "recs.reason.stackingMulti");
    return out;
  }
  if (target === "multi") {
    push("divider_rack", "recs.reason.stackingMulti");
    push("tray_open_front", "recs.reason.stackingGrab");
    push("card_shoe_front_draw", "recs.reason.stackingOne");
    return out;
  }
  // grab / default
  push("tray_open_front", "recs.reason.stackingGrab");
  push("card_shoe_front_draw", "recs.reason.stackingOne");
  push("divider_rack", "recs.reason.stackingMulti");
  return out;
}

function rebuildMechanismRecommendations() {
  if (!els.mechanismRecs) return;
  if (!els.studentMode?.checked) {
    els.mechanismRecs.textContent = "";
    return;
  }

  const recs = recommendMechanismsFromStudentInputs();
  if (!recs.length) {
    els.mechanismRecs.textContent = "";
    return;
  }

  const html =
    `<div><strong>${escapeHtml(t("recs.title"))}</strong></div>` +
    `<ol>` +
    recs
      .map((r) => {
        const name = t(`options.mechanism.${r.id}`);
        const reason = r.reasonKey ? t(r.reasonKey) : "";
        return `<li><strong>${escapeHtml(name)}</strong>${reason ? ` — ${escapeHtml(reason)}` : ""}</li>`;
      })
      .join("") +
    `</ol>`;
  els.mechanismRecs.innerHTML = html;
}

function applyStudentAutoDesign() {
  if (!els.studentMode?.checked) return;

  rebuildMechanismRecommendations();

  const chosen = chooseMechanismFromStudentInputs();
  if (!studentMechanismManuallyChosen) {
    if (els.mechanism && els.mechanism.value !== chosen) els.mechanism.value = chosen;
    lastAutoMechanism = chosen;
  }
  // Mechanism choice always drives preset (course-friendly: one concept → one template).
  const mech = els.mechanism?.value ?? chosen;
  if (els.preset && els.preset.value !== mech) els.preset.value = mech;

  // Always design around internal dimensions for item-fit.
  if (els.dimMode) els.dimMode.value = "internal";

  const t = num(els.thickness, 3);
  const itemType = els.dispenseType?.value ?? "stacking";

  if (itemType === "flowing") {
    const s = Math.max(5, num(els.maxPieceSize, 18));
    // Simple, safe-ish default hopper/cavity sizes.
    els.innerWidth.value = String(Math.round(Math.max(80, s * 5)));
    els.innerDepth.value = String(Math.round(Math.max(80, s * 5)));
    els.innerHeight.value = String(Math.round(Math.max(120, s * 7)));

    // Encourage outlet/chute size via existing slot fields (used for legacy presets too).
    if (els.slotWidth) els.slotWidth.value = String(Math.round(Math.max(22, s * 1.6)));
    if (els.slotHeight) els.slotHeight.value = String(Math.round(Math.max(18, s * 1.2)));
    if (els.slotY) els.slotY.value = String(Math.round(Math.max(20, (s * 7) * 0.35)));
  } else {
    const cw = Math.max(10, num(els.cardWidth, 63));
    const ch = Math.max(10, num(els.cardHeight, 88));
    const cap = Math.max(1, Math.floor(num(els.capacityCards, 60)));

    const sideClear = 1.0;
    const backClear = 2.0;
    const topClear = 3.0;

    // Rough stack height estimate (mm per card). Student-friendly and deterministic.
    const perCard = 0.32;
    const stackH = cap * perCard;

    const w = cw + 2 * sideClear;
    const d = ch + backClear;
    const h = Math.max(25, stackH + topClear);

    els.innerWidth.value = String((Math.round(w * 10) / 10).toFixed(1));
    els.innerDepth.value = String((Math.round(d * 10) / 10).toFixed(1));
    els.innerHeight.value = String((Math.round(h * 10) / 10).toFixed(1));

    // For card shoe, make a reasonable draw slot.
    if (chosen === "card_shoe_front_draw") {
      if (els.slotWidth) els.slotWidth.value = String((Math.round((cw - 4) * 10) / 10).toFixed(1));
      if (els.slotHeight) els.slotHeight.value = String(18);
      if (els.slotY) els.slotY.value = String(35);
    }
  }

  // Keep divider bays in sync with student multi-category intent.
  if (mech === "divider_rack" && els.dividerBays) {
    els.dividerBays.value = String(Math.max(2, Math.floor(num(els.dividerBays, 3))));
  }

  computeDerived();
}

let autoGenTimer = null;
function scheduleStudentAutoGenerate() {
  if (!els.studentMode?.checked) return;
  if (autoGenTimer) clearTimeout(autoGenTimer);
  autoGenTimer = setTimeout(async () => {
    autoGenTimer = null;
    try {
      applyStudentAutoDesign();
      await generateSvg();
    } catch (e) {
      console.error(e);
    }
  }, 120);
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
  const inStudent = !!els.studentMode?.checked;

  const nonEmpty = (v) => String(v ?? "").trim().length > 0;
  const countChecked = (nodes) => Array.from(nodes || []).filter((n) => !!n?.checked).length;

  // Step 1: context + constraints acknowledgement.
  const contextOk = nonEmpty(els.clientContext?.value) && nonEmpty(els.problemStatement?.value);
  const constraintsOk = countChecked(els.constraintChecks) >= 2;
  const step1Complete = !inStudent || (contextOk && constraintsOk);

  // Step 2: requirements.
  const itemType = els.dispenseType?.value ?? "stacking";
  const dispTarget = els.dispenseTargetType?.value ?? "";
  const stackingOk =
    Number(num(els.cardWidth, 0)) > 0 && Number(num(els.cardHeight, 0)) > 0 && Number(num(els.capacityCards, 0)) > 0;
  const flowingOk = Number(num(els.maxPieceSize, 0)) > 0;
  const itemOk = !!dispTarget && (itemType === "flowing" ? flowingOk : stackingOk);

  const storageOk = nonEmpty(els.storageTarget?.value);
  const metricsOk = countChecked(els.successMetrics) >= 2;
  const step2Complete = !inStudent || (step1Complete && itemOk && storageOk && metricsOk);

  // Step 3: mechanism choice + justification.
  const mechOk = nonEmpty(els.mechanism?.value);
  const justificationOk = String(els.mechanismJustification?.value ?? "").trim().length >= 20;
  const step3Complete = !inStudent || (step2Complete && mechOk && justificationOk);

  // Step 4: fabrication setup + review.
  const thicknessSet = nonEmpty(els.thickness?.value);
  const kerfKnown = nonEmpty(els.kerf?.value);
  const hasCut = !!lastSvg;
  const step4Complete = !inStudent || (step3Complete && thicknessSet && (kerfKnown || calibrationGeneratedOnce) && hasCut);

  if (els.step1Badge) els.step1Badge.textContent = step1Complete ? t("steps.complete") : t("steps.incomplete");
  if (els.step2Badge) els.step2Badge.textContent = step2Complete ? t("steps.complete") : t("steps.incomplete");
  if (els.step3Badge) els.step3Badge.textContent = step3Complete ? t("steps.complete") : t("steps.incomplete");
  if (els.step4Badge) els.step4Badge.textContent = step4Complete ? t("steps.complete") : t("steps.incomplete");

  // In student mode, gate Project Pack export on Step 4.
  if (els.btnBundle) els.btnBundle.disabled = inStudent ? !step4Complete : false;
  if (els.mobileBundle) els.mobileBundle.disabled = inStudent ? !step4Complete : false;
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

  // v0.6 coach layer: deterministic design review + requirements quality checks.
  const inStudent = !!els.studentMode?.checked;

  // Quality checks: keep these non-blocking (warnings only).
  const hasNumber = (s) => /\d/.test(String(s || ""));
  const seemsVague = (s) => {
    const txt = String(s || "").trim().toLowerCase();
    if (!txt) return false;
    return /\b(a\s*lot|some|nice|better|maybe|around|stuff|things?)\b/.test(txt);
  };

  if (inStudent) {
    const cc = String(els.clientContext?.value ?? "").trim();
    const ps = String(els.problemStatement?.value ?? "").trim();
    const st = String(els.storageTarget?.value ?? "").trim();
    const dt = String(els.dispenseTarget?.value ?? "").trim();

    if (cc && (cc.length < 8 || seemsVague(cc))) keys.push("warnings.vagueClientContext");
    if (ps && (ps.length < 12 || seemsVague(ps))) keys.push("warnings.vagueProblemStatement");
    if (st && !hasNumber(st)) keys.push("warnings.vagueStorageTarget");
    if (dt && (dt.length < 8 || seemsVague(dt))) keys.push("warnings.vagueDispenseTarget");
  }

  // Design review heuristics (mechanism-aware where possible).
  const itemType = els.dispenseType?.value ?? "stacking";
  const irregular = !!els.irregularShape?.checked;

  if (itemType === "flowing" && Number.isFinite(p.max_piece_size) && p.max_piece_size > 0) {
    const funnel = Math.min(p.inner_width, p.inner_depth);
    const ratio = funnel / p.max_piece_size;
    const threshold = irregular ? 5.0 : 4.0;
    if (ratio > 0 && ratio < threshold) keys.push("warnings.flowingBridgingRisk");
  }

  if (p.preset === "candy_rotary_wheel") {
    const pc = Number(p.pocket_count ?? 0);
    if (pc >= 10 && Number.isFinite(p.inner_width) && p.inner_width > 0) {
      const estPitch = p.inner_width / pc;
      if (estPitch < p.thickness * 1.3) keys.push("warnings.rotaryPocketWallsThin");
    }
  }

  if (p.preset === "card_shoe_front_draw" && Number.isFinite(p.card_height) && p.card_height > 0) {
    const fh = Number(p.front_height ?? 0);
    if (fh > 0 && fh > p.card_height * 0.85) keys.push("warnings.cardShoeFrontTooTall");
    if (fh > 0 && fh < p.card_height * 0.35) keys.push("warnings.cardShoeFrontTooShort");
  }

  if (Number.isFinite(p.inner_height) && p.inner_height >= 200 && p.thickness <= 3.2) {
    keys.push("warnings.tallWallsFlexRisk");
  }

  if (Number.isFinite(p.layout_padding_mm) && p.layout_padding_mm > 0 && p.layout_padding_mm < 6) {
    keys.push("warnings.paddingTooSmall");
  }

  return keys;
}

const UI_WARNING_HELP_KEY = {
  "warnings.kerfTooBig": "kerf",
  "warnings.clearanceLarge": "clearance",
  "warnings.minTabs": "minTabs",
  "warnings.slotInvalid": "slotHeight",

  "warnings.vagueClientContext": "clientContext",
  "warnings.vagueProblemStatement": "problemStatement",
  "warnings.vagueStorageTarget": "storageTarget",
  "warnings.vagueDispenseTarget": "dispenseTarget",

  "warnings.flowingBridgingRisk": "maxPieceSize",
  "warnings.rotaryPocketWallsThin": "pocketCount",
  "warnings.cardShoeFrontTooTall": "frontHeight",
  "warnings.cardShoeFrontTooShort": "frontHeight",
  "warnings.tallWallsFlexRisk": "innerHeight",
  "warnings.paddingTooSmall": "padding",
};

function renderWarnings() {
  const p = buildParams();
  const uiKeys = collectUiWarningKeys(p);
  const uiWarnings = uiKeys.map((k) => ({ text: t(k), helpKey: UI_WARNING_HELP_KEY[k] || null }));

  const allPython = Array.isArray(pythonWarnings) ? pythonWarnings : [];
  const hasAny = uiWarnings.length || allPython.length;
  if (!hasAny) {
    els.warnings.hidden = true;
    els.warnings.innerHTML = "";
    return;
  }

  const uiList = uiWarnings.length
    ? `<div class="warnBlock"><strong>${escapeHtml(t("warnings.title"))}</strong><ul>${uiWarnings
        .map((w) => {
          const link = w.helpKey
            ? ` <a href="#" data-open-help="${escapeHtml(String(w.helpKey))}">${escapeHtml(t("mode.help"))}</a>`
            : "";
          return `<li>${escapeHtmlWithBreaks(String(w.text))}${link}</li>`;
        })
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

    // v0.5 mechanism params
    divider_bays: num(els.dividerBays, 3),

    card_width: num(els.cardWidth, 63),
    card_height: num(els.cardHeight, 88),
    capacity_cards: num(els.capacityCards, 60),

    max_piece_size: num(els.maxPieceSize, 18),
    pocket_count: num(els.pocketCount, 8),
    axle_diameter: num(els.axleDiameter, 6),
    ramp_count: num(els.rampCount, 6),
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
  updateStepBadges();
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

function pad2(n) {
  return String(n).padStart(2, "0");
}

function formatDateYYYYMMDD(d) {
  return `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())}`;
}

function slugify(s) {
  return String(s ?? "")
    .trim()
    .toLowerCase()
    .replace(/\s+/g, "_")
    .replace(/[^a-z0-9_\-]+/g, "")
    .slice(0, 40) || "project";
}

function base64EncodeUtf8(str) {
  // btoa expects Latin1; convert via percent-encoding.
  return btoa(unescape(encodeURIComponent(String(str))));
}

function base64DecodeUtf8(b64) {
  return decodeURIComponent(escape(atob(String(b64))));
}

function collectProjectConfig() {
  const now = new Date();
  const p = buildParams();
  const derived = lastDerived || null;
  const itemType = els.dispenseType?.value ?? "stacking";

  const constraints = {
    noCoins: !!els.constraintNoCoins?.checked,
    noLiquids: !!els.constraintNoLiquids?.checked,
    personalUse: !!els.constraintPersonalUse?.checked,
  };

  const successMetrics = Array.from(els.successMetrics || [])
    .filter((cb) => cb.checked)
    .map((cb) => cb.value);

  const mechId = (els.mechanism?.value ?? p.preset ?? "").trim();
  const recs = recommendMechanismsFromStudentInputs();

  return {
    app_version: APP_VERSION,
    language: currentLang,
    timestamp_iso: now.toISOString(),
    date_ymd: formatDateYYYYMMDD(now),

    ui: {
      studentMode: !!els.studentMode?.checked,
      dimMode: els.dimMode?.value ?? "internal",
      fitIndex: Number(els.fit?.value ?? 1),
      exportAllLanguages: !!els.exportAllLanguages?.checked,
    },

    student: {
      client_context: String(els.clientContext?.value ?? "").trim(),
      problem_statement: String(els.problemStatement?.value ?? "").trim(),
      constraints,
      requirements: {
        item_type: itemType,
        irregular_shape: !!els.irregularShape?.checked,
        storage_target: String(els.storageTarget?.value ?? "").trim(),
        dispense_target_type: String(els.dispenseTargetType?.value ?? "").trim(),
        success_metrics: successMetrics,
      },
      mechanism_choice: {
        mechanism_id: mechId,
        justification: String(els.mechanismJustification?.value ?? "").trim(),
        recommendations: recs,
      },
    },

    generator_params: p,
    derived,
    warnings: {
      ui_warning_keys: collectUiWarningKeys(p),
      python_warnings: Array.isArray(pythonWarnings) ? pythonWarnings : [],
    },
  };
}

function buildShareLink(project) {
  const url = new URL(window.location.href);
  url.searchParams.set("cfg", base64EncodeUtf8(JSON.stringify(project)));
  url.searchParams.set("lang", project?.language ?? currentLang);
  return url.toString();
}

function getDocStrings(lang) {
  const L = String(lang || "en");
  const dict = {
    en: {
      packTitle: "Project Pack",
      layerGuideTitle: "Layer guide (SVG)",
      layerGuideBody:
        "- CUT layer: cut lines (red stroke recommended)\n" +
        "- LABELS layer: optional text/labels (engrave/score or ignore)\n" +
        "\nRecommended workflow:\n" +
        "1) Import SVG into your laser software\n" +
        "2) Map CUT to cut operation\n" +
        "3) Map LABELS to engrave/score (optional)\n" +
        "4) Do a small test cut first if kerf/fit is unknown\n",
      titles: {
        s00: "Project Summary",
        s01: "Client & Problem",
        s02: "Requirements & Success Criteria",
        s03: "Mechanism Choice & Justification",
        s04: "Dimensions & Calculations",
        s05: "Build Plan (24 lessons)",
        s06: "Test Plan",
        s07: "Iteration Log",
        s08: "Assembly Guide",
        s09: "Submission Checklist",
      },
      labels: {
        clientContext: "Client & context",
        problem: "Problem statement",
        mechanism: "Mechanism",
        itemType: "Item type",
        storage: "Storage target",
        dispense: "Dispense target",
        metrics: "Success metrics",
        thickness: "Material thickness (mm)",
        kerf: "Kerf (mm)",
        fit: "Fit",
        internal: "Derived internal size (mm)",
        external: "Derived external size (mm)",
      },
      prompts: {
        evidence:
          "Evidence prompts:\n- Add photos during assembly\n- Add a short video demo of dispensing\n- Fill test tables and iteration log\n",
        justificationPrompt: "Student justification (required):",
      },
      checklist: {
        submission:
          "- Cut files included (design.svg)\n- Photos/video evidence\n- Test results table filled\n- Iteration log filled\n- Final reflection: what changed and why\n",
      },
    },
    "zh-Hant": {
      packTitle: "專案包",
      layerGuideTitle: "圖層說明（SVG）",
      layerGuideBody:
        "- CUT 圖層：切割線（建議紅色線）\n" +
        "- LABELS 圖層：文字／標籤（可雕刻／可忽略）\n" +
        "\n建議流程：\n" +
        "1) 匯入 SVG 到雷切軟體\n" +
        "2) 將 CUT 設為切割\n" +
        "3) 將 LABELS 設為雕刻／描線（選填）\n" +
        "4) 若不確定 kerf／鬆緊，先做小測試\n",
      titles: {
        s00: "專案摘要",
        s01: "客戶與問題",
        s02: "需求與成功標準",
        s03: "機構選擇與理由",
        s04: "尺寸與計算",
        s05: "24 堂製作計畫",
        s06: "測試計畫",
        s07: "迭代紀錄",
        s08: "組裝指南",
        s09: "繳交清單",
      },
      labels: {
        clientContext: "客戶／情境",
        problem: "問題描述",
        mechanism: "機構",
        itemType: "物件類型",
        storage: "儲存目標",
        dispense: "出料目標",
        metrics: "成功指標",
        thickness: "材料厚度（mm）",
        kerf: "刀縫 Kerf（mm）",
        fit: "鬆緊",
        internal: "推導內尺寸（mm）",
        external: "推導外尺寸（mm）",
      },
      prompts: {
        evidence:
          "證據提示：\n- 組裝過程照片\n- 出料展示短影片\n- 填寫測試表與迭代紀錄\n",
        justificationPrompt: "學生理由（必填）：",
      },
      checklist: {
        submission:
          "- 已包含切割檔（design.svg）\n- 照片／影片證據\n- 已填寫測試表\n- 已填寫迭代紀錄\n- 最終反思：改了什麼、為什麼\n",
      },
    },
    "zh-Hans": {
      packTitle: "项目包",
      layerGuideTitle: "图层说明（SVG）",
      layerGuideBody:
        "- CUT 图层：切割线（建议红色线）\n" +
        "- LABELS 图层：文字／标签（可雕刻／可忽略）\n" +
        "\n建议流程：\n" +
        "1) 导入 SVG 到激光软件\n" +
        "2) 将 CUT 设为切割\n" +
        "3) 将 LABELS 设为雕刻／描线（选填）\n" +
        "4) 若不确定 kerf／松紧，先做小测试\n",
      titles: {
        s00: "项目摘要",
        s01: "客户与问题",
        s02: "需求与成功标准",
        s03: "机构选择与理由",
        s04: "尺寸与计算",
        s05: "24 课制作计划",
        s06: "测试计划",
        s07: "迭代记录",
        s08: "组装指南",
        s09: "提交清单",
      },
      labels: {
        clientContext: "客户／情境",
        problem: "问题描述",
        mechanism: "机构",
        itemType: "物件类型",
        storage: "存储目标",
        dispense: "出料目标",
        metrics: "成功指标",
        thickness: "材料厚度（mm）",
        kerf: "刀缝 Kerf（mm）",
        fit: "松紧",
        internal: "推导内尺寸（mm）",
        external: "推导外尺寸（mm）",
      },
      prompts: {
        evidence:
          "证据提示：\n- 组装过程照片\n- 出料展示短视频\n- 填写测试表与迭代记录\n",
        justificationPrompt: "学生理由（必填）：",
      },
      checklist: {
        submission:
          "- 已包含切割文件（design.svg）\n- 照片／视频证据\n- 已填写测试表\n- 已填写迭代记录\n- 最终反思：改了什么、为什么\n",
      },
    },
  };

  return dict[L] || dict.en;
}

function buildProjectDocs(project, lang, dictForLang) {
  const S = getDocStrings(lang);
  const mechId = project?.student?.mechanism_choice?.mechanism_id || project?.generator_params?.preset || "";
  const mechName = tFromDict(dictForLang || dict, `options.mechanism.${mechId}`);
  const itemType = project?.student?.requirements?.item_type || "";
  const dispTarget = project?.student?.requirements?.dispense_target_type || "";
  const metrics = project?.student?.requirements?.success_metrics || [];
  const internal = project?.derived?.internal;
  const external = project?.derived?.external;

  const metricsLine = metrics.length ? metrics.join(", ") : "";
  const internalLine = internal ? `W ${internal.w.toFixed(1)} × D ${internal.d.toFixed(1)} × H ${internal.h.toFixed(1)}` : "";
  const externalLine = external ? `W ${external.w.toFixed(1)} × D ${external.d.toFixed(1)} × H ${external.h.toFixed(1)}` : "";

  const doc = {};

  const FN = {
    s00: "00_Project_Summary.md",
    s01: "01_Client_Problem.md",
    s02: "02_Requirements_and_Success_Criteria.md",
    s03: "03_Mechanism_Choice_and_Justification.md",
    s04: "04_Dimensions_and_Calculations.md",
    s05: "05_Build_Plan_24_Lessons.md",
    s06: "06_Test_Plan.md",
    s07: "07_Iteration_Log.md",
    s08: "08_Assembly_Guide.md",
    s09: "09_Submission_Checklist.md",
  };

  doc[FN.s00] =
    `# ${S.titles.s00} — ${escapeMarkdown(mechName)}\n\n` +
    `| ${S.labels.clientContext} | ${escapeMarkdown(project?.student?.client_context || "")} |\n` +
    `|---|---|\n` +
    `| ${S.labels.problem} | ${escapeMarkdown(project?.student?.problem_statement || "")} |\n` +
    `| ${S.labels.mechanism} | ${escapeMarkdown(mechName)} (${escapeMarkdown(mechId)}) |\n` +
    `| ${S.labels.itemType} | ${escapeMarkdown(itemType)} |\n` +
    `| ${S.labels.storage} | ${escapeMarkdown(project?.student?.requirements?.storage_target || "")} |\n` +
    `| ${S.labels.dispense} | ${escapeMarkdown(dispTarget)} |\n` +
    `| ${S.labels.metrics} | ${escapeMarkdown(metricsLine)} |\n` +
    `| ${S.labels.thickness} | ${escapeMarkdown(String(project?.generator_params?.thickness ?? ""))} |\n` +
    `| ${S.labels.kerf} | ${escapeMarkdown(String(project?.generator_params?.kerf_mm ?? ""))} |\n` +
    `| ${S.labels.fit} | ${escapeMarkdown(String(project?.generator_params?.clearance_mm ?? ""))} |\n\n` +
    `${S.prompts.evidence}`;

  doc[FN.s01] =
    `# ${S.titles.s01}\n\n` +
    `## ${S.labels.clientContext}\n${escapeMarkdown(project?.student?.client_context || "")}\n\n` +
    `## ${S.labels.problem}\n${escapeMarkdown(project?.student?.problem_statement || "")}\n`;

  doc[FN.s02] =
    `# ${S.titles.s02}\n\n` +
    `- ${S.labels.itemType}: **${escapeMarkdown(itemType)}**\n` +
    `- ${S.labels.storage}: **${escapeMarkdown(project?.student?.requirements?.storage_target || "")}**\n` +
    `- ${S.labels.dispense}: **${escapeMarkdown(dispTarget)}**\n\n` +
    `## ${S.labels.metrics}\n` +
    (metrics.length ? metrics.map((m) => `- ${escapeMarkdown(m)}`).join("\n") + "\n" : "- ( )\n") +
    "\n";

  const recLines = (project?.student?.mechanism_choice?.recommendations || [])
    .slice(0, 3)
    .map((r, i) => {
      const n = tFromDict(dictForLang || dict, `options.mechanism.${r.id}`);
      const why = r.reasonKey ? tFromDict(dictForLang || dict, r.reasonKey) : "";
      return `${i + 1}. **${escapeMarkdown(n)}**${why ? ` — ${escapeMarkdown(why)}` : ""}`;
    })
    .join("\n");

  doc[FN.s03] =
    `# ${S.titles.s03}\n\n` +
    (recLines ? `## Top 3\n${recLines}\n\n` : "") +
    `## ${S.labels.mechanism}\n**${escapeMarkdown(mechName)}**\n\n` +
    `## ${S.prompts.justificationPrompt}\n${escapeMarkdown(project?.student?.mechanism_choice?.justification || "")}\n`;

  doc[FN.s04] =
    `# ${S.titles.s04}\n\n` +
    `- ${S.labels.internal}: **${escapeMarkdown(internalLine)}**\n` +
    `- ${S.labels.external}: **${escapeMarkdown(externalLine)}**\n\n` +
    `## Joint rule\n` +
    `- thickness + clearance − kerf = drawn slot depth\n` +
    `- thickness + clearance ≈ expected final slot\n`;

  doc[FN.s05] =
    `# ${S.titles.s05}\n\n` +
    `## 24 lessons plan (fill-in table)\n\n` +
    `| Lesson | Goal | Task | Evidence | Notes |\n` +
    `|---:|---|---|---|---|\n` +
    Array.from({ length: 24 })
      .map((_, i) => `| ${i + 1} |  |  | ( ) photo ( ) video ( ) measurement |  |`)
      .join("\n") +
    `\n\n` +
    `## Milestones (checklist)\n` +
    `- [ ] Measure real material thickness\n` +
    `- [ ] (Optional) Fit test → choose kerf/clearance\n` +
    `- [ ] Cut design.svg\n` +
    `- [ ] Assemble base + mechanism\n` +
    `- [ ] Record first working demo (video)\n` +
    `- [ ] Run test plan and fill tables\n` +
    `- [ ] Iterate at least once and record before/after\n`;

  doc[FN.s06] =
    `# ${S.titles.s06}\n\n` +
    `## Selected success metrics\n\n` +
    (metrics.length ? metrics.map((m) => `- ${escapeMarkdown(m)}`).join("\n") + "\n\n" : "- (none selected)\n\n") +
    `## Test table\n\n` +
    `| Metric | Procedure | Target | Result | Evidence link | Notes |\n` +
    `|---|---|---|---|---|---|\n` +
    `| Jam rate | 20 dispenses | ≤ 1 jam |  |  |  |\n` +
    `| Portion consistency | 10 actions | ±1 item / ±10% |  |  |  |\n` +
    `| Refill time | Refill to target level | ≤ ___ sec |  |  |  |\n` +
    `| Durability | 100 cycles | No break |  |  |  |\n\n` +
    `## Evidence prompts\n` +
    `- Photos during assembly\n` +
    `- Short video demo of dispensing\n`;

  doc[FN.s07] =
    `# ${S.titles.s07}\n\n` +
    `| Version | Date | Change | Why | Result |\n` +
    `|---|---|---|---|---|\n` +
    `| v1 | ${escapeMarkdown(project?.date_ymd || "")} |  |  |  |\n`;

  doc[FN.s08] =
    `# ${S.titles.s08}\n\n` +
    `## Evidence prompts\n` +
    `- Step photos: (add photos here)\n` +
    `- Short video demo: (paste link here)\n\n` +
    `## Notes\n` +
    `- What was hard?\n` +
    `- What did you change after testing?\n`;

  doc[FN.s09] =
    `# ${S.titles.s09}\n\n` +
    `${S.checklist.submission}`;

  return doc;
}

function buildLayerGuideMarkdown(lang) {
  const S = getDocStrings(lang);
  return `# ${S.layerGuideTitle}\n\n${S.layerGuideBody}`;
}

function escapeMarkdown(s) {
  // Minimal escaping for tables/headings.
  return String(s ?? "").replace(/\|/g, "\\|").replace(/\r?\n/g, " ");
}

function tryParseProjectFromUrl() {
  try {
    const url = new URL(window.location.href);
    const cfg = url.searchParams.get("cfg");
    if (!cfg) return null;
    const json = base64DecodeUtf8(cfg);
    return JSON.parse(json);
  } catch {
    return null;
  }
}

function applyProjectToUi(project) {
  if (!project || typeof project !== "object") return;

  const setVal = (el, v) => {
    if (!el || v == null) return;
    el.value = String(v);
  };

  // Language handled by main() (pre-load). Here we apply fields.
  if (els.studentMode) {
    els.studentMode.checked = !!project?.ui?.studentMode;
    setStudentMode(els.studentMode.checked);
  }

  setVal(els.clientContext, project?.student?.client_context);
  setVal(els.problemStatement, project?.student?.problem_statement);
  setVal(els.storageTarget, project?.student?.requirements?.storage_target);
  setVal(els.mechanismJustification, project?.student?.mechanism_choice?.justification);

  if (els.constraintNoCoins) els.constraintNoCoins.checked = !!project?.student?.constraints?.noCoins;
  if (els.constraintNoLiquids) els.constraintNoLiquids.checked = !!project?.student?.constraints?.noLiquids;
  if (els.constraintPersonalUse) els.constraintPersonalUse.checked = !!project?.student?.constraints?.personalUse;

  const metrics = new Set(project?.student?.requirements?.success_metrics || []);
  Array.from(els.successMetrics || []).forEach((cb) => {
    cb.checked = metrics.has(cb.value);
  });

  setVal(els.dispenseType, project?.student?.requirements?.item_type);
  setStudentItemUi();
  if (els.irregularShape) els.irregularShape.checked = !!project?.student?.requirements?.irregular_shape;
  setVal(els.dispenseTargetType, project?.student?.requirements?.dispense_target_type);

  // Prefer generator_params for geometric fields.
  const p = project?.generator_params || {};
  setVal(els.preset, p.preset);
  setVal(els.innerWidth, p.inner_width);
  setVal(els.innerDepth, p.inner_depth);
  setVal(els.innerHeight, p.inner_height);
  setVal(els.thickness, p.thickness);
  setVal(els.kerf, p.kerf_mm);
  setVal(els.clearance, p.clearance_mm);
  setVal(els.sheetWidth, p.sheet_width);
  setVal(els.marginMm, p.layout_margin_mm);
  setVal(els.paddingMm, p.layout_padding_mm);
  setVal(els.strokeMm, p.stroke_mm);

  // Student item parameters
  setVal(els.cardWidth, p.card_width);
  setVal(els.cardHeight, p.card_height);
  setVal(els.capacityCards, p.capacity_cards);
  setVal(els.maxPieceSize, p.max_piece_size);
  setVal(els.dividerBays, p.divider_bays);
  setVal(els.pocketCount, p.pocket_count);
  setVal(els.axleDiameter, p.axle_diameter);
  setVal(els.rampCount, p.ramp_count);

  // Mechanism choice should be treated as manual.
  const mechId = project?.student?.mechanism_choice?.mechanism_id;
  if (mechId && els.mechanism) {
    els.mechanism.value = mechId;
    els.preset.value = mechId;
    studentMechanismManuallyChosen = true;
    lastAutoMechanism = null;
  }

  computeDerived();
  rebuildMechanismRecommendations();
  updateStepBadges();
}

async function downloadProjectPackZip() {
  if (!pyodide) throw new Error("Pyodide not ready");

  // Ensure we have a fresh SVG snapshot.
  if (!lastSvg || !lastParams) {
    await generateSvg();
  }
  if (!lastSvg || !lastParams) throw new Error("No SVG available");

  const JSZipLib = globalThis.JSZip;
  if (!JSZipLib) throw new Error("JSZip failed to load");
  const zip = new JSZipLib();

  const project = collectProjectConfig();
  const mechId = (project?.student?.mechanism_choice?.mechanism_id || project?.generator_params?.preset || "design").trim();
  const date = project?.date_ymd || formatDateYYYYMMDD(new Date());
  const rootName = `ProjectPack_${slugify(mechId)}_${date}`;

  const root = zip.folder(rootName);
  const cut = root.folder("cut_files");
  const docs = root.folder("docs");
  const config = root.folder("config");
  const assets = root.folder("assets");

  cut.file("design.svg", lastSvg);
  cut.file("layer_guide.md", buildLayerGuideMarkdown(currentLang));

  // Docs (selected language in docs/ root)
  const selectedDocs = buildProjectDocs(project, currentLang, dict);
  Object.entries(selectedDocs).forEach(([name, content]) => docs.file(name, content));

  // Optional: export all languages into docs/translations/<lang>/...
  if (els.exportAllLanguages?.checked) {
    const transRoot = docs.folder("translations");
    for (const lng of ["en", "zh-Hant", "zh-Hans"]) {
      if (lng === currentLang) continue;
      const folder = transRoot.folder(lng);
      const d = await getI18nDict(lng);
      const files = buildProjectDocs(project, lng, d);
      Object.entries(files).forEach(([name, content]) => folder.file(name, content));
    }
  }

  // Config + share link
  config.file("project.json", JSON.stringify(project, null, 2));
  config.file("share_link.txt", buildShareLink(project));

  // Assets
  assets.file("preview.svg", lastSvg);

  const blob = await zip.generateAsync({ type: "blob" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${rootName}.zip`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

async function downloadBundleZip() {
  // Backward compatible name: v0.6 repurposes this into Project Pack export.
  return downloadProjectPackZip();
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

function buildFaqDrawer() {
  if (!els.faqDrawerBody) return;
  const q = (els.faqSearch?.value || "").trim().toLowerCase();
  const cats = Object.keys(faqData || {});
  const blocks = cats
    .map((cat) => {
      const items = (faqData[cat] || []).filter((it) => {
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

els.warnings?.addEventListener("click", (e) => {
  const btn = e.target.closest("[data-open-help]");
  if (!btn) return;
  e.preventDefault();
  const k = btn.getAttribute("data-open-help");
  if (!k) return;
  openHelpDrawer(k);
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
  const v = els.mechanism.value;
  els.preset.value = v;
  if (els.studentMode?.checked) {
    if (v && v !== lastAutoMechanism) studentMechanismManuallyChosen = true;
    rebuildMechanismRecommendations();
    scheduleStudentAutoGenerate();
  }
});

els.dispenseType?.addEventListener("change", () => {
  setStudentItemUi();
  studentMechanismManuallyChosen = false;
  lastAutoMechanism = null;
  scheduleStudentAutoGenerate();
});
els.dispenseTargetType?.addEventListener("change", () => {
  studentMechanismManuallyChosen = false;
  lastAutoMechanism = null;
  scheduleStudentAutoGenerate();
});
els.cardWidth?.addEventListener("input", scheduleStudentAutoGenerate);
els.cardHeight?.addEventListener("input", scheduleStudentAutoGenerate);
els.capacityCards?.addEventListener("input", scheduleStudentAutoGenerate);
els.maxPieceSize?.addEventListener("input", scheduleStudentAutoGenerate);
els.dividerBays?.addEventListener("input", scheduleStudentAutoGenerate);
els.pocketCount?.addEventListener("input", scheduleStudentAutoGenerate);
els.axleDiameter?.addEventListener("input", scheduleStudentAutoGenerate);
els.rampCount?.addEventListener("input", scheduleStudentAutoGenerate);

// v0.6 student workflow inputs (context / checks / justification)
[els.clientContext, els.problemStatement, els.storageTarget, els.mechanismJustification].forEach((el) => {
  el?.addEventListener("input", () => {
    rebuildMechanismRecommendations();
    updateStepBadges();
  });
});

els.irregularShape?.addEventListener("change", () => {
  studentMechanismManuallyChosen = false;
  lastAutoMechanism = null;
  scheduleStudentAutoGenerate();
});

Array.from(els.constraintChecks || []).forEach((cb) => cb.addEventListener("change", updateStepBadges));
Array.from(els.successMetrics || []).forEach((cb) => cb.addEventListener("change", updateStepBadges));

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
  // Share-link support: allow cfg/lang in URL to override initial language.
  const url = new URL(window.location.href);
  const projectFromUrl = tryParseProjectFromUrl();
  const urlLang = url.searchParams.get("lang") || projectFromUrl?.language;

  currentLang = urlLang || detectInitialLanguage();
  if (els.langSelect) els.langSelect.value = currentLang;
  await loadLanguage(currentLang);

  // Apply loaded config (if any) after i18n is ready.
  if (projectFromUrl) applyProjectToUi(projectFromUrl);

  if (els.mobileDownload) els.mobileDownload.disabled = true;

  els.langSelect?.addEventListener("change", async () => {
    const v = els.langSelect.value;
    await loadLanguage(v);
    computeDerived();
    rebuildMechanismRecommendations();
  });

  updateHeaderHeightVar();
  window.addEventListener("resize", () => {
    updateHeaderHeightVar();
    if (!userZoomed) fitToView();
  });

  // Initial UI state
  if (!projectFromUrl) {
    setStudentMode(true);
    setFitPreset(1);
    computeDerived();
  } else {
    // Config already applied; just ensure derived/readouts are up to date.
    computeDerived();
  }

  await init();
}

main().catch((e) => {
  console.error(e);
  setStatusKey("status.initFailed", { message: e?.message ?? e });
});
