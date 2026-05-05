# Project Info: CardBoxGen

CardBoxGen is a parametric SVG generator for laser-cut card storage, dispensing trays, simple boxes, divider racks, card shoes, and a layered rotary dry-goods dispenser prototype.

The project is browser-first but Python-backed:

- CLI: `python -m cardboxgen`
- Compatibility CLI: `python cardboxgen_v0_1.py`
- Web app: `docs/`, using Pyodide plus generated `docs/cardboxgen_bundle.py`

## Source Layout

`cardboxgen/` is the only source of truth for generator logic.

- `version.py`: package version
- `models.py`: dataclasses and structured warnings
- `geometry.py`: points, paths, bboxes, cutout path helpers
- `joints.py`: deterministic `FingerPlan` and kerf/clearance rules
- `panels.py`: panel and cut-path primitives
- `layout.py`: sheet layout
- `svg.py`: SVG writer with layer conventions
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

Kerf and clearance are explicit:

- drawn slot depth = `thickness + clearance - kerf`
- tab/slot segment widths are compensated, then normalized to exact edge length

The SVG writer uses separate groups:

- `CUT`: red cut paths
- `SCORE`: blue score paths
- `ENGRAVE`: labels/text

## Student Mode Notes

The web app includes a student mode for mechanism selection and project-pack export. It can recommend templates, auto-fill safe starting dimensions, display Python warnings/errors, and export:

- `cut.svg`
- `project_summary.md`
- `assembly_guide.md`
- `bom.md`
- `params.json`
- `metadata.json`
- `teacher_notes.md` when student mode is active

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
