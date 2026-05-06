# CLI and Python API

CardBoxGen can run from the command line, from Python, or from the browser through Pyodide.

## CLI Generate

```bash
python -m cardboxgen --preset tray_open_front --inner-width 135 --inner-depth 90 --inner-height 80 --thickness 3 --kerf 0.2 --clearance 0.15 --out tray.svg
```

The explicit subcommand form is also supported:

```bash
python -m cardboxgen generate --preset tray_open_front --inner-width 135 --inner-depth 90 --inner-height 80 --thickness 3 --kerf 0.2 --clearance 0.15 --out tray.svg
```

## CLI Validate

```bash
python -m cardboxgen validate --preset tray_open_front --inner-width 135 --inner-depth 90 --inner-height 80 --thickness 3 --kerf 0.2 --clearance 0.15
```

Blocking validation errors return a nonzero exit code.

## Calibration

```bash
python -m cardboxgen --calibration --thickness 3 --kerf 0.2 --out calibration.svg
```

## JSON Report

```bash
python -m cardboxgen --preset box_with_lid --inner-width 135 --inner-depth 90 --inner-height 80 --thickness 3 --kerf 0.2 --clearance 0.4 --json-report report.json --out box_with_lid.svg
```

## Compatibility Wrappers

Existing users can still run:

```bash
python cardboxgen_v0_1.py --preset tray_open_front --inner-width 135 --inner-depth 90 --inner-height 80 --thickness 3 --kerf 0.2 --clearance 0.15 --out tray.svg
```

The old `cardboxgen_v0_7_templates.py` path remains as a deprecated compatibility wrapper.

## Python API

```python
from cardboxgen.api import generate_svg, validate_template_params

validation = validate_template_params(
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

result = generate_svg("tray_open_front", validation.normalized_params)
```

`generate_svg()` returns a JSON-safe dictionary with:

- `svg`;
- `warnings`;
- `meta`;
- `bundle_files`.

For blocking validation cases, the result is diagnostic and `meta.exportable` is false.
