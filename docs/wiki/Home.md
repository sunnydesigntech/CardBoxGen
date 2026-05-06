# CardBoxGen Wiki

CardBoxGen is a browser-first Python/Pyodide SVG generator for laser-cut card trays, boxes, dispensers, divider racks, card shoes, and calibration fit tests.

Live app:

- https://sunnydesigntech.github.io/CardBoxGen/
- https://sunnydesigntech.github.io/CardBoxGen/exec/ for direct classroom/execution launchers

Repository:

- https://github.com/sunnydesigntech/CardBoxGen

## Main Pages

- [[Camera, QR, and Project Codes|Camera-QR-and-Project-Codes]]
- [[Template Reference|Template-Reference]]
- [[Validation and Testing|Validation-and-Testing]]
- [[CLI and Python API|CLI-and-Python-API]]
- [[Fabrication Model|Fabrication-Model]]
- [[Running and Deployment|Running-and-Deployment]]
- [[Contributing|Contributing]]

## Supported Templates

- `tray_open_front`
- `dispenser_slot_front`
- `window_front`
- `box_with_lid`
- `divider_rack`
- `card_shoe`
- `candy_machine_rotary_layered`
- `calibration`

## Key Guarantees

CardBoxGen works for validated supported dimensions and returns blocking validation errors for impossible or unsafe geometry. It does not claim every arbitrary dimension can become a physically correct box.

The web app runs fully client-side. It loads Pyodide, imports the generated `docs/cardboxgen_bundle.py`, renders SVG inline, and exports a project pack ZIP.

## Where to Start

- Use the live app if you want an SVG cut file without installing Python.
- Use the CLI if you want repeatable generation or scripted examples.
- Read the fabrication model before cutting production material.
- Cut calibration strips before a full box.
- Open a geometry issue if a generated export is marked valid but cannot physically assemble.
