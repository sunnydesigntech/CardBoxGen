# Validation and Testing

CardBoxGen is designed to generate correct SVGs for validated supported dimensions and to reject impossible dimensions with structured blocking errors.

## Validation Contract

Validation returns:

- `normalized_params`;
- `messages`;
- `blocking`;
- `computed_limits`.

Each message includes:

- `severity`: `info`, `warn`, or `error`;
- `code`: stable machine-readable code;
- `message`: human explanation;
- `fix`: concrete repair suggestion when available;
- `field`: UI field name when applicable.

## Blocking Examples

CardBoxGen blocks export for unsafe cases such as:

- zero or negative material thickness;
- negative kerf or clearance;
- kerf greater than or equal to material thickness;
- internal dimensions too small for material and finger pitch;
- even explicit finger counts;
- joint usable span too short after corner clearance;
- slot or window margins that remove required material;
- divider counts that make bays too narrow;
- screw holes too close to edges;
- rotary pockets colliding with axle, screw holes, or rim.

## Assembly Oracle

The test suite includes an assembly oracle that checks generated metadata and geometry:

- every mating edge has exactly one partner;
- partners share the same `FingerPlan`;
- masks are complementary;
- segment boundaries align after mirroring/reversal;
- final tab and slot widths match the fit model;
- panel outlines are simple and nonzero-area;
- cutouts are contained in parent panels;
- layout bounding boxes do not overlap.

## Required Local Checks

```bash
python -m pytest -q
python -m pytest -m slow -q
python examples/generate_examples.py
python tools/sync_docs.py --check
```

The CI workflow runs those checks and all-preset CLI smoke generation.

## Web Asset Checks

Tests also verify:

- the web app loads `cardboxgen_bundle.py`;
- deprecated browser generator copies are not used;
- all first-class presets are present in the UI;
- i18n keys match across English, Traditional Chinese, and Simplified Chinese;
- version strings match the Python package;
- camera/QR/project-code fallback UI exists.
