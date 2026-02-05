// Runs the Python generator in the browser via Pyodide.
// This site is intended for GitHub Pages hosting (no backend).

import { loadPyodide } from "https://cdn.jsdelivr.net/pyodide/v0.25.1/full/pyodide.mjs";

const els = {
  preset: document.getElementById("preset"),
  innerWidth: document.getElementById("innerWidth"),
  innerDepth: document.getElementById("innerDepth"),
  innerHeight: document.getElementById("innerHeight"),
  thickness: document.getElementById("thickness"),
  kerf: document.getElementById("kerf"),
  clearance: document.getElementById("clearance"),
  sheetWidth: document.getElementById("sheetWidth"),
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
  status: document.getElementById("status"),
  preview: document.getElementById("preview"),
  download: document.getElementById("download"),
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
  els.btnGenerate.textContent = "Generate SVG";
  setStatus("Ready.");
}

function buildParams() {
  const preset = els.preset.value;
  const p = {
    preset,
    inner_width: num(els.innerWidth, 135),
    inner_depth: num(els.innerDepth, 90),
    inner_height: num(els.innerHeight, 225),
    thickness: num(els.thickness, 3),
    kerf_mm: num(els.kerf, 0.2),
    clearance_mm: num(els.clearance, 0.15),
    sheet_width: num(els.sheetWidth, 340),
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

  const p = buildParams();
  setStatus("Generating SVG…");

  // Send parameters to Python.
  pyodide.globals.set("p_json", JSON.stringify(p));

  const svg = await pyodide.runPythonAsync(`
import json
from cardboxgen_v0_1 import BoxParams, build_panels_for_preset, make_svg

p = BoxParams(**json.loads(p_json))
panels = build_panels_for_preset(p)
svg = make_svg(
    panels,
    meta=p.__dict__,
    sheet_width=p.sheet_width,
    labels=p.labels,
    offset_kerf=False,
    kerf_mm=p.kerf_mm,
  holding_tabs=p.holding_tabs,
  tab_width_mm=p.tab_width_mm,
)
svg
`);

  // Preview (inline SVG) + download.
  els.preview.innerHTML = svg;
  const blob = new Blob([svg], { type: "image/svg+xml" });
  const url = URL.createObjectURL(blob);
  els.download.href = url;
  els.download.hidden = false;
  els.download.textContent = "Download SVG";
  els.download.download = `cardbox_${p.preset}.svg`;

  setStatus("Done.");
}

async function generateCalibration() {
  setStatus("Generating calibration SVG…");
  const thickness = num(els.thickness, 3);
  const kerf = num(els.kerf, 0.2);

  pyodide.globals.set("thickness", thickness);
  pyodide.globals.set("kerf", kerf);

  const svg = await pyodide.runPythonAsync(`
import textwrap, json
from cardboxgen_v0_1 import build_calibration_svg

# build_calibration_svg writes to a file, so we call its internal logic by
# generating it to /tmp then reading.
path = '/tmp/calibration.svg'
build_calibration_svg(thickness=thickness, kerf_mm=kerf, clearance_values=[-0.10,-0.05,0.0,0.05,0.10,0.15,0.20], out_path=path)
open(path, 'r', encoding='utf-8').read()
`);

  els.preview.innerHTML = svg;
  const blob = new Blob([svg], { type: "image/svg+xml" });
  const url = URL.createObjectURL(blob);
  els.download.href = url;
  els.download.hidden = false;
  els.download.textContent = "Download calibration SVG";
  els.download.download = `calibration.svg`;

  setStatus("Done.");
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

init().catch((e) => {
  console.error(e);
  setStatus(`Failed to initialize: ${e?.message ?? e}`);
  els.preview.innerHTML = `<pre>${escapeHtml(String(e?.stack ?? e))}</pre>`;
});
