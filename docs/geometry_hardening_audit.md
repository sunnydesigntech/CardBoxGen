# Geometry Hardening Audit

Date: 2026-05-05

Baseline commit at start of pass: `59e988c3421001dc13e855284b4c86edab39c4b4`

## Fresh Baseline Verification

From a clean `git pull --ff-only` on `main`:

```text
python -m pip install -r requirements-dev.txt
  OK; existing dev requirements installed.

python -m pytest -q
  19 passed

python -m cardboxgen --preset tray_open_front --inner-width 135 --inner-depth 90 --inner-height 80 --thickness 3 --kerf 0.2 --clearance 0.15 --out /tmp/tray.svg
  Wrote /tmp/tray.svg

python -m cardboxgen --preset dispenser_slot_front --inner-width 135 --inner-depth 90 --inner-height 80 --thickness 3 --kerf 0.2 --clearance 0.15 --out /tmp/dispenser.svg
  Wrote /tmp/dispenser.svg

python -m cardboxgen --preset window_front --inner-width 135 --inner-depth 90 --inner-height 80 --thickness 3 --kerf 0.2 --clearance 0.15 --out /tmp/window.svg
  Wrote /tmp/window.svg

python -m cardboxgen --preset box_with_lid --inner-width 135 --inner-depth 90 --inner-height 80 --thickness 3 --kerf 0.2 --clearance 0.15 --out /tmp/box_lid.svg
  Wrote /tmp/box_lid.svg

python -m cardboxgen --preset divider_rack --inner-width 135 --inner-depth 90 --inner-height 80 --thickness 3 --kerf 0.2 --clearance 0.15 --out /tmp/divider.svg
  Wrote /tmp/divider.svg

python -m cardboxgen --preset card_shoe --card-width 63 --card-height 88 --card-thickness 0.35 --capacity 60 --thickness 3 --kerf 0.2 --clearance 0.15 --out /tmp/card_shoe.svg
  Wrote /tmp/card_shoe.svg

python -m cardboxgen --preset candy_machine_rotary_layered --max-piece 18 --thickness 3 --kerf 0.2 --clearance 0.15 --out /tmp/candy.svg
  Wrote /tmp/candy.svg

python -m cardboxgen --calibration --thickness 3 --kerf 0.2 --out /tmp/calibration.svg
  Wrote /tmp/calibration.svg

python examples/generate_examples.py
  OK

python tools/sync_docs.py --check
  docs/cardboxgen_bundle.py is fresh
```

Bundle path checks:

```text
grep -R "cardboxgen_bundle.py" docs/app.js tests || true
  docs/app.js and tests referenced cardboxgen_bundle.py.

! grep -R "cardboxgen_v0_7_templates" docs/app.js tests
  Initially matched a test string and local pycache, not docs/app.js runtime code.
  The test string was rewritten to avoid false-positive source grep matches.
```

Public source and Pages check at baseline:

- Raw `docs/app.js` loaded `cardboxgen_bundle.py`.
- Live Pages app showed the v0.8.0 UI and the same first-class preset set.
- No browser cache result was used; checks read raw GitHub and Pages URLs directly.

## Baseline Risks Found

- The baseline smoke tests proved that files were generated, but did not check assembly correctness deeply.
- Kerf and clearance formulas were partly implemented in `joints.py` and documented, but there was no dedicated fabrication model module with sign-convention tests.
- Invalid geometry could still return visually plausible SVG unless the caller interpreted warning severity correctly.
- Cutouts, layout, and edge-pair metadata were not checked by an independent assembly oracle.
- The default calibration file did not include both width-fit and depth-fit checks plus a known-size reference part.
- The browser could disable export for warning severity, but Python API/CLI needed a stronger non-exportable diagnostic contract.

## Hardening Changes

- Added `cardboxgen.fabrication` with explicit full-width kerf formulas and inverse tests.
- Added `cardboxgen.validation.validate_template_params()` returning normalized parameters, structured messages, blocking state, and computed limits.
- Changed `generate_svg()` to return diagnostic non-exportable SVG for blocking validation errors.
- Changed CLI behavior so blocking validation exits nonzero and does not write exportable SVG unless `--allow-diagnostic-svg` is passed.
- Added corner relief around adjacent fingered edges using the actual drawn joint depths.
- Added cutout bbox hints so tests can distinguish closed contained cutouts from intentional calibration slots.
- Added JSON metadata embedding in exported SVG.
- Added assembly-oracle tests for edge-pair metadata, complement masks, final fit estimates, cutout containment, panel self-intersection, and layout non-overlap.
- Added Hypothesis valid-domain coverage and deterministic slow geometry sweep.
- Added calibration reference rectangle and depth-fit notches.
- Added mechanical assumptions metadata for the rotary candy-machine prototype.
- Updated web fit readout to show Python-computed tab, slot, and depth model values.

## Current Verification Snapshot

After the hardening changes and bundle regeneration:

```text
python tools/sync_docs.py && rm -rf tests/__pycache__ && python -m pytest -q
  Synced package API bundle -> docs/cardboxgen_bundle.py
  31 passed
```

Final release verification commands are recorded in the release notes and final task response.
