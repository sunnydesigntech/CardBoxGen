# Project Details — CardBoxGen

## What this project is

CardBoxGen is a parametric SVG generator for laser-cut card storage and dispensing designs.
It produces axis-aligned (Manhattan) outlines with finger joints, suitable for 3mm sheet goods
(MDF, plywood, greyboard, acrylic — with different recommended clearances).

The generator is usable in two ways:

- CLI: `cardboxgen_v0_1.py`
- Web app: static site in `docs/` that runs the same generator in-browser via Pyodide

## Design names

### Presets

- `tray_open_front`
  - Open top
  - Lowered/open front wall (front height < back height)
  - Optional scoop cutout (rounded-U)

- `dispenser_slot_front`
  - Front panel is present
  - Adds a rectangular dispense slot (width/height/position parameters)

- `window_front`
  - Front panel is present
  - Adds a large window cutout and a thumb notch

- `box_with_lid`
  - Adds a slip lid (top + four walls)
  - Lid uses `lid_clearance` to allow sliding fit

### Panel names

These are used as SVG `<g id="...">` group ids:

- Base box: `BOTTOM`, `BACK`, `LEFT`, `RIGHT`, optional `FRONT`
- Lid: `LID_TOP`, `LID_BACK`, `LID_FRONT`, `LID_LEFT`, `LID_RIGHT`

## Joint system (edge pairing)

Finger joints are generated from a shared plan (`FingerPlan`) per mating edge pair.
This prevents mismatches caused by independently rounding finger counts.

Stable finger count rule:

- `n = max(min_fingers, floor(length / target_finger_w))`
- force `n` odd

Two joint families are supported:

- OUTER: bottom-to-wall edges
- VERTICAL: wall-to-wall corner edges

Optional fixed counts:

- `finger_count_outer`
- `finger_count_vertical`

## Kerf + clearance

Inputs:

- `kerf_mm`: estimated laser kerf
- `clearance_mm`: target clearance between slot and tab after assembly

Within each finger-joint edge, segment widths are adjusted:

- tabs are drawn wider: `+ (kerf - clearance/2)`
- slots are drawn narrower: `+ (clearance/2 - kerf)`

Widths are normalized so the total edge length remains exact.

## SVG conventions

- CUT paths: red stroke, width 0.2
- TEXT/labels: black
- Output is plain SVG XML with newlines (good for Inkscape / LightBurn)

Optional:

- `--offset-kerf` uses pyclipper (if installed) to offset outer contours by `+kerf/2`
  and inner holes by `-kerf/2`.

## Holding tabs

`--holding-tabs` leaves a small gap in polygon cuts per edge to create a breakaway bridge.
This is implemented as an open path (no `Z`) so the laser doesn’t cut that short segment.

Limitations:

- applied to polygon paths (panel outlines and polygon cutouts)
- arc cutouts (thumb notch/scoop) remain fully cut

## Web app hosting

The web app is designed for GitHub Pages:

- `docs/index.html` + `docs/app.js` + `docs/style.css`
- `docs/cardboxgen_v0_1.py` is synced from the root generator with `tools/sync_docs.py`
- `.github/workflows/pages.yml` deploys `docs/` automatically
