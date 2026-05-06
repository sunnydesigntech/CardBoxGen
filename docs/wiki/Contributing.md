# Contributing

CardBoxGen accepts contributions that improve geometry correctness, validation safety, browser reliability, examples, tests, and documentation.

## Local Setup

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

## Before Submitting Changes

Run:

```bash
python -m pytest -q
python -m pytest -m slow -q
python examples/generate_examples.py
python tools/sync_docs.py --check
```

## Geometry Contribution Rules

- Preserve inner dimensions for box/tray presets.
- Use shared `FingerPlan` metadata for mating edge pairs.
- Add validation before adding hidden clamps.
- Return blocking errors for impossible geometry.
- Add tests for every new geometry invariant.
- Regenerate examples when output changes intentionally.

## Web Contribution Rules

- Keep the app static and GitHub Pages compatible.
- Keep Pyodide loading `docs/cardboxgen_bundle.py`.
- Update all i18n JSON files for new UI strings.
- Preserve project export blocking when validation returns errors.
- Keep camera/QR optional; Project Code import is the required fallback.

## Documentation Contribution Rules

Update the README, docs, wiki source pages, and changelog when behavior changes. The user-facing docs should state physical assumptions clearly rather than implying every arbitrary dimension can be cut.
