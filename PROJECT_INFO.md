# Project Info: CardBoxGen

CardBoxGen is a parametric SVG generator for laser-cut card storage, dispensing trays, simple boxes, divider racks, card shoes, and a layered rotary dry-goods dispenser prototype.

The project is browser-first but Python-backed:

- CLI: `python -m cardboxgen`
- Compatibility CLI: `python cardboxgen_v0_1.py`
- Web app: `docs/`, using Pyodide plus generated `docs/cardboxgen_bundle.py`

## Source Layout

`cardboxgen/` is the only source of truth for generator logic.

- `version.py`: package version
- `fabrication.py`: full-width kerf model and fit compensation formulas
- `validation.py`: parameter normalization, blocking errors, and computed limits
- `models.py`: dataclasses and structured warnings/results
- `geometry.py`: points, paths, bboxes, cutout path helpers
- `joints.py`: deterministic shared `FingerPlan` edge pairs
- `panels.py`: panel and cut-path primitives
- `layout.py`: sheet layout
- `svg.py`: SVG writer with layer conventions and metadata
- `presets/`: tray, dispenser, window box, lid box, divider rack, card shoe, candy machine, calibration
- `api.py`: JSON-safe browser/API entry point
- `cli.py`: command line interface

## Supported Presets

- `tray_open_front`
- `dispenser_slot_front`
- `window_front`
- `box_with_lid`
- `divider_rack`
- `card_shoe`
- `candy_machine_rotary_layered`
- `calibration`

Legacy aliases emit warnings and map to supported presets.

## Geometry and Fit

Inner dimensions are authoritative for box/tray presets. The generated panels add material thickness around those dimensions, then produce mating finger joints from shared edge-pair plans.

CardBoxGen uses `kerf` as full laser cut width, so burn radius is `kerf / 2`.

- External tabs shrink after cutting.
- Internal slots and holes grow after cutting.
- Drawn tab depth targets final material thickness.
- Drawn slot depth targets `thickness + clearance`.
- Tab/slot segment widths are compensated and normalized to exact edge length.

The validation layer blocks impossible or unsafe configurations before export. Examples include negative thickness, kerf greater than material thickness, too-small internal dimensions, even finger counts, tiny finger pitch, unsafe windows/slots, excessive divider count, invalid screw margins, and rotary pockets colliding with axle or rim.

## Student Mode Notes

The web app includes a student mode for mechanism selection and project-pack export. It can recommend templates, auto-fill safe starting dimensions, display Python warnings/errors, show computed fit values, and export:

- `cut.svg`
- `project_summary.md`
- `assembly_guide.md`
- `bom.md`
- `params.json`
- `metadata.json`
- `teacher_notes.md` when student mode is active

## Project Handoff and Camera Notes

The web app can hand off projects with share links, pasteable `CBG1:` project/location codes, and optional QR scanning. QR scanning uses browser camera APIs and only works when the page is opened in a browser that grants camera permission and supports QR decoding. If camera access is blocked, the project code import path remains the reliable fallback.

The direct Pages entry point is:

- <https://sunnydesigntech.github.io/CardBoxGen/>
- <https://sunnydesigntech.github.io/CardBoxGen/exec/> for execution/classroom launchers

Mechanism templates are mechanically plausible starting points, not certified manufactured products. The candy machine preset is for dry flowing solids only and should be prototyped before classroom or public use.

## Generated Docs Bundle

Run:

```bash
python tools/sync_docs.py
```

This rebuilds `docs/cardboxgen_bundle.py` from the package. CI checks freshness with:

```bash
python tools/sync_docs.py --check
```
