# CardBoxGen

![CI](https://github.com/sunnydesigntech/CardBoxGen/actions/workflows/static.yml/badge.svg)
![GitHub Pages](https://github.com/sunnydesigntech/CardBoxGen/actions/workflows/pages.yml/badge.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)
![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB.svg)

Current version: **v0.8.1**

CardBoxGen generates millimeter SVG cut files for laser-cut card trays, boxes, dispensers, divider racks, card shoes, and a layered rotary dry-goods dispenser prototype. It runs as a Python CLI and as a static GitHub Pages app powered by Pyodide.

Live app: <https://sunnydesigntech.github.io/CardBoxGen/>

Direct classroom/execution entry: <https://sunnydesigntech.github.io/CardBoxGen/exec/>

## What This Repo Provides

- A Python generator package with deterministic geometry, validation, and SVG export.
- A static browser app that runs the same Python API in Pyodide.
- GitHub Pages deployment from `docs/`.
- Checked example SVG files for every first-class template.
- Test coverage for fabrication formulas, assembly edge pairing, panel corners, validation, CLI, docs sync, i18n, and web asset smoke checks.
- Wiki-ready documentation sources in `docs/wiki/`.

## Quick Start

Use the live app when you only need a cut file:

1. Open <https://sunnydesigntech.github.io/CardBoxGen/>.
2. Pick a template.
3. Enter measured material thickness, kerf, clearance, and dimensions.
4. Check warnings/errors.
5. Download the project pack.

Use the CLI when you want repeatable generation:

```bash
python -m pip install -r requirements-dev.txt
python -m cardboxgen --preset tray_open_front --inner-width 135 --inner-depth 90 --inner-height 80 --thickness 3 --kerf 0.2 --clearance 0.15 --out tray.svg
```

Cut calibration first:

```bash
python -m cardboxgen --calibration --thickness 3 --kerf 0.2 --out calibration.svg
```

## Repository Status

The active source of truth is the `cardboxgen/` Python package. The old root-level generator filenames are compatibility wrappers only. The web app loads the generated bundle `docs/cardboxgen_bundle.py`, which CI checks against the package source.

Current production focus:

- mechanically correct panel geometry for valid supported dimensions;
- explicit blocking validation for impossible or unsafe dimensions;
- reliable static-web deployment and project handoff without a backend;
- clear documentation for calibration, kerf convention, and classroom use.

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

## Project Handoff, QR, and Camera Access

The web app includes a Project handoff panel:

- Copy share link: creates a URL containing the current project configuration.
- Copy project code: creates a pasteable `CBG1:` code for the same project.
- Import code: accepts a share link or project/location code.
- Scan QR: optional camera-based QR import when the browser permits camera access.

Camera access cannot be forced by CardBoxGen. If QR scanning is blocked in an embedded browser, open the live app directly in Safari/Chrome or use the pasteable project code. The `/exec/` entry point redirects to the app for classroom/execution launchers:

<https://sunnydesigntech.github.io/CardBoxGen/exec/>

See [docs/camera_qr_sharing.md](docs/camera_qr_sharing.md) for permission troubleshooting and privacy notes.

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

## Documentation Map

- [docs/README.md](docs/README.md): GitHub Pages and static app operations.
- [docs/fabrication_model.md](docs/fabrication_model.md): kerf, clearance, corner zones, and calibration model.
- [docs/camera_qr_sharing.md](docs/camera_qr_sharing.md): camera permission, QR scanning, share links, and project/location codes.
- [docs/wiki/](docs/wiki/): versioned source pages for the GitHub Wiki.
- [CONTRIBUTING.md](CONTRIBUTING.md): development workflow and PR checklist.
- [SUPPORT.md](SUPPORT.md): what to include in geometry and web bug reports.
- [SECURITY.md](SECURITY.md): security and privacy reporting notes.

## GitHub Repository Setup

Recommended GitHub settings:

- About description: browser-first Python/Pyodide SVG generator for laser-cut card trays, boxes, dispensers, mechanisms, and calibration fit tests.
- Homepage: <https://sunnydesigntech.github.io/CardBoxGen/>
- Topics: `laser-cutting`, `svg-generator`, `box-generator`, `finger-joints`, `pyodide`, `github-pages`, `cad`, `fabrication`, `python`.
- Pages source: GitHub Actions.
- Issues and Wiki enabled.

The GitHub Wiki source pages are kept in `docs/wiki/` so they can be reviewed and versioned with the codebase.

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
