# CardBoxGen

Current version: **v0.8.1**

CardBoxGen generates millimeter SVG cut files for laser-cut card trays, boxes, dispensers, divider racks, card shoes, and a layered rotary dry-goods dispenser prototype. It runs as a Python CLI and as a static GitHub Pages app powered by Pyodide.

Live app: <https://sunnydesigntech.github.io/CardBoxGen/>

## Architecture

The generator source of truth is the Python package in `cardboxgen/`.

- `fabrication.py`: full-width kerf model and tab/slot compensation formulas
- `validation.py`: parameter normalization, computed limits, and blocking errors
- `models.py`: typed warnings, validation results, and JSON-safe result models
- `geometry.py`: point/path/bbox helpers and SVG path primitives
- `joints.py`: `FingerPlan`, mating edge pairs, and shared joint rendering
- `panels.py`: panels, cut paths, score paths, labels, and render specs
- `svg.py`: SVG writer with `CUT`, `SCORE`, `ENGRAVE`, and metadata
- `layout.py`: deterministic sheet layout without overlapping panel boxes
- `presets/`: template-specific builders
- `api.py`: `generate_svg(template_id, params)` for Pyodide and Python callers
- `cli.py`: argparse CLI used by `python -m cardboxgen`

Compatibility wrappers remain for existing users:

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

Legacy aliases are accepted with deprecation warnings:

- `card_shoe_front_draw` -> `card_shoe`
- `candy_rotary_wheel` -> `candy_machine_rotary_layered`
- `rotary_wheel` -> `candy_machine_rotary_layered`

## Valid Dimensions, Not Every Dimension

CardBoxGen guarantees generation for validated supported dimensions and returns blocking errors for impossible or unsafe geometry. It does not silently generate boxes when dimensions, kerf, clearances, windows, slots, screw holes, or finger features cannot fabricate safely.

Blocking validation returns structured messages:

```json
{
  "severity": "error",
  "code": "INNER_W_TOO_SMALL",
  "message": "inner_w 12 mm is too small for 3 mm material and 3 mm minimum features.",
  "fix": "Increase inner_w to at least 24.0 mm or reduce material thickness.",
  "field": "inner_w"
}
```

The Python API returns a diagnostic SVG with `meta.exportable=false` for blocking cases. The CLI exits nonzero and does not write the SVG unless `--allow-diagnostic-svg` is passed. The web app keeps preview helpful but disables export while blocking errors exist.

## Fabrication Model

CardBoxGen uses `kerf` as the **full width removed by the laser cut**. The burn radius is `kerf / 2`.

Sign convention:

- external tabs shrink after cutting;
- internal gaps and slots grow after cutting;
- open-edge finger depths are handled separately from closed holes;
- tab and slot segment widths are compensated, then normalized to preserve exact edge length.

Depth model for open-edge finger joints:

```text
target final tab depth  = thickness
target final slot depth = thickness + clearance
drawn tab depth         = thickness + kerf
drawn slot depth        = thickness + clearance - kerf
```

Width model:

```text
final tab width  = drawn tab width - kerf
final slot width = drawn slot width + kerf
```

Do not apply both CardBoxGen kerf compensation and cutter-software kerf compensation to the same cut file unless you intentionally use a nominal/no-kerf workflow. See [docs/fabrication_model.md](docs/fabrication_model.md).

Practical guidance:

- Measure actual sheet thickness with calipers; nominal stock labels are often wrong.
- Cut calibration strips before a full box.
- Use smaller clearance for glue or press-fit plywood, larger clearance for acrylic or classroom assembly.
- Kerf depends on machine, material, thickness, focus, airflow, direction, and settings.

## CLI

Install development requirements:

```bash
python -m pip install -r requirements-dev.txt
```

Validate parameters:

```bash
python -m cardboxgen validate --preset tray_open_front --inner-width 135 --inner-depth 90 --inner-height 80 --thickness 3 --kerf 0.2 --clearance 0.15
```

Generate a tray:

```bash
python -m cardboxgen generate --preset tray_open_front --inner-width 135 --inner-depth 90 --inner-height 80 --thickness 3 --kerf 0.2 --clearance 0.15 --out out.svg
```

Backward-compatible shorthand:

```bash
python -m cardboxgen --preset tray_open_front --inner-width 135 --inner-depth 90 --inner-height 80 --thickness 3 --kerf 0.2 --clearance 0.15 --out out.svg
```

Compatibility wrapper:

```bash
python cardboxgen_v0_1.py --preset tray_open_front --inner-width 135 --inner-depth 90 --inner-height 80 --thickness 3 --kerf 0.2 --clearance 0.15 --out out.svg
```

Calibration strips:

```bash
python -m cardboxgen --calibration --thickness 3 --kerf 0.2 --out calibration.svg
```

JSON report:

```bash
python -m cardboxgen --preset box_with_lid --inner-width 135 --inner-depth 90 --inner-height 80 --thickness 3 --kerf 0.2 --clearance 0.4 --json-report report.json --out box_with_lid.svg
```

## Python API

```python
from cardboxgen.api import generate_svg

result = generate_svg(
    "tray_open_front",
    {
        "inner_w": 135,
        "inner_d": 90,
        "inner_h": 80,
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

The app is static and GitHub Pages friendly. It loads Pyodide, imports `docs/cardboxgen_bundle.py`, renders SVG inline, supports preview zoom/pan/layer toggles, displays validation messages and fit-model values, and exports a ZIP with `cut.svg`, project docs, `params.json`, and `metadata.json`.

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
- `examples/invalid_dimension_report.json`

## Tests

```bash
python -m pytest -q
python -m pytest -m slow -q
python examples/generate_examples.py
python tools/sync_docs.py --check
```

The test suite covers fabrication formulas, finger planning, shared edge-pair metadata, assembly-oracle checks, valid-domain sweeps, invalid-dimension blocking, cutout containment, layout overlap checks, SVG XML/layer validity, CLI subprocess smoke tests, API JSON safety, docs bundle freshness, i18n key consistency, examples, and version alignment.

## GitHub Pages

GitHub Actions deploys `docs/` to Pages. In repository settings, set Pages source to **GitHub Actions**.

The CI workflow installs dev requirements, checks docs bundle freshness, runs tests, runs the slow geometry sweep, regenerates examples, and exercises all first-class CLI presets.

## Release Checklist

1. Update `cardboxgen/version.py`.
2. Update `pyproject.toml`, `docs/app.js`, `docs/index.html`, and `docs/i18n/*.json`.
3. Run `python tools/sync_docs.py`.
4. Run `python -m pytest -q`.
5. Run `python -m pytest -m slow -q`.
6. Run `python examples/generate_examples.py`.
7. Commit the source changes and generated docs bundle.
8. Tag the release.

License: MIT.
