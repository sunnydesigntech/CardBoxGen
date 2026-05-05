# CardBoxGen

Current version: **v0.8.0**

CardBoxGen generates millimeter SVG cut files for laser-cut card trays, boxes, dispensers, divider racks, card shoes, and a layered rotary dry-goods dispenser prototype. It targets sheet material around 3 mm thick and is designed to run both as a Python CLI and as a static GitHub Pages app powered by Pyodide.

Live app: <https://sunnydesigntech.github.io/CardBoxGen/>

## Architecture

The generator source of truth is the Python package in `cardboxgen/`.

- `models.py`: typed parameters, warnings, and JSON-safe result models
- `geometry.py`: point/path/bbox helpers and SVG path primitives
- `joints.py`: `FingerPlan`, mating edge pairs, and kerf/clearance compensation
- `panels.py`: panels, cut paths, score paths, labels, and render specs
- `svg.py`: SVG writer with `CUT`, `SCORE`, and `ENGRAVE` layers
- `layout.py`: deterministic sheet layout without overlapping panel boxes
- `presets/`: template-specific builders
- `api.py`: `generate_svg(template_id, params)` for Pyodide and Python callers
- `cli.py`: argparse CLI used by `python -m cardboxgen`

Compatibility wrappers remain:

- `cardboxgen_v0_1.py`
- `cardboxgen_v0_7_templates.py`

The web app loads `docs/cardboxgen_bundle.py`, a generated single-file bundle created by `python tools/sync_docs.py`. Do not hand-edit the bundle.

## Supported Presets

First-class template IDs:

- `tray_open_front`
- `dispenser_slot_front`
- `window_front`
- `box_with_lid`
- `divider_rack`
- `card_shoe`
- `candy_machine_rotary_layered`
- `calibration`

Legacy aliases are accepted with warnings:

- `card_shoe_front_draw` -> `card_shoe`
- `candy_rotary_wheel` -> `candy_machine_rotary_layered`
- `rotary_wheel` -> `candy_machine_rotary_layered`

## Geometry Rules

Inner dimensions are the source of truth for box-like presets. For material thickness `t`, base outside width/depth are `inner + 2t`, and wall panel height is `inner_h + t`.

Finger joints use shared mating plans. Each mating edge pair owns one `FingerPlan` with length, count, nominal segment widths, and a tab mask. The mate uses the complement mask, so matching edges do not independently guess phase.

Depth rule:

```text
drawn_slot_depth = thickness + clearance - kerf
```

Width rule:

```text
tab_drawn  = nominal + (kerf - clearance / 2)
slot_drawn = nominal + (clearance / 2 - kerf)
```

Segment widths are normalized per edge so the total edge length remains exact.

## CLI

Install development requirements:

```bash
python -m pip install -r requirements-dev.txt
```

Generate a tray:

```bash
python -m cardboxgen --preset tray_open_front --inner-width 135 --inner-depth 90 --inner-height 225 --thickness 3 --kerf 0.2 --clearance 0.15 --out out.svg
```

Compatibility wrapper:

```bash
python cardboxgen_v0_1.py --preset tray_open_front --inner-width 135 --inner-depth 90 --inner-height 225 --thickness 3 --kerf 0.2 --clearance 0.15 --out out.svg
```

Calibration strips:

```bash
python -m cardboxgen --calibration --thickness 3 --kerf 0.2 --out calibration.svg
```

## Python API

```python
from cardboxgen.api import generate_svg

result = generate_svg(
    "tray_open_front",
    {
        "inner_w": 135,
        "inner_d": 90,
        "inner_h": 225,
        "thickness": 3,
        "kerf": 0.2,
        "fit_clearance": 0.15,
    },
)

svg = result["svg"]
warnings = result["warnings"]
meta = result["meta"]
```

The API result is JSON-safe and includes `svg`, `warnings`, `meta`, and `bundle_files`.

## Web Preview

From the repo root:

```bash
python tools/sync_docs.py
python -m http.server 8000
```

Open <http://localhost:8000/docs/>.

The app is static and GitHub Pages friendly. It loads Pyodide, imports `docs/cardboxgen_bundle.py`, renders SVG inline, supports preview zoom/pan/layer toggles, and exports a ZIP with `cut.svg`, project docs, `params.json`, and `metadata.json`.

## Examples

Regenerate checked examples:

```bash
python examples/generate_examples.py
```

Generated files:

- `examples/tray_open_front.svg`
- `examples/dispenser_slot_front.svg`
- `examples/window_front.svg`
- `examples/box_with_lid.svg`
- `examples/divider_rack.svg`
- `examples/card_shoe.svg`
- `examples/candy_machine_rotary_layered.svg`
- `examples/calibration_mating_strips.svg`

## Tests

```bash
python -m pytest -q
python tools/sync_docs.py --check
```

The test suite covers finger planning, kerf/clearance math, preset smoke generation, SVG XML validity, layer IDs, layout overlap checks, CLI subprocess smoke tests, API JSON safety, docs bundle freshness, i18n key consistency, and version alignment.

## GitHub Pages

GitHub Actions deploys `docs/` to Pages. In repository settings, set Pages source to **GitHub Actions**.

The CI workflow runs:

```bash
python -m pip install -r requirements-dev.txt
python tools/sync_docs.py --check
python -m pytest -q
```

## Release Checklist

1. Update `cardboxgen/version.py`.
2. Update `pyproject.toml`, `docs/app.js`, `docs/index.html`, and `docs/i18n/*.json`.
3. Run `python tools/sync_docs.py`.
4. Run `python -m pytest -q`.
5. Run `python examples/generate_examples.py`.
6. Commit the source changes and generated docs bundle.
7. Tag the release.

License: MIT.
