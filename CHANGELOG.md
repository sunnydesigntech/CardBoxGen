# Changelog

## v0.8.0

- Rebuilt the generator around the `cardboxgen` package with one source of truth for CLI, examples, tests, and Pyodide.
- Added first-class API support for `tray_open_front`, `dispenser_slot_front`, `window_front`, `box_with_lid`, `divider_rack`, `card_shoe`, `candy_machine_rotary_layered`, and `calibration`.
- Replaced phase-based template drift with shared `FingerPlan` mating edge metadata for box-like presets.
- Added generated `docs/cardboxgen_bundle.py` and a `tools/sync_docs.py --check` freshness gate.
- Updated the static web app to load the generated bundle and export `params.json` plus `metadata.json`.
- Normalized English, Traditional Chinese, and Simplified Chinese i18n key structure and aligned all version strings.
- Added package metadata, CLI smoke tests, API tests, layout checks, SVG layer checks, docs sync checks, and i18n consistency tests.

## v0.6

- Project Pack export: ZIP contains cut files + docs + config + share link
- Student Mode workflow expanded into a learning scaffold (requirements, success metrics, justification)
- Deterministic guidance checks and export-ready documentation templates (EN / 繁 / 简)

## v0.5

- Student Mode auto-design: item inputs drive mechanism + dimensions
- New dispenser presets for cards and flowing solids (candy-style)
- Help + FAQ expanded and aligned with Student Mode + mechanisms

## v0.4

- Info popover hover + click-to-pin stability (popover stays open when moving into it)
- Help drawer upgrades: shared helpContent, category grouping, and search
- New FAQ drawer: searchable Q&A with links into Help topics
- Calibration moved to optional Fit tools (Fit Test) instead of a primary action
- Preview zoom behavior improved: clamped zoom and smarter auto-fit on resize

## v0.3.1

- Documentation refresh (README + Pages docs + changelog)

## v0.3

- Multilingual web UI (EN / 繁體中文 / 简体中文) with persisted language selection
- Inline per-parameter help: injected “i” buttons, popovers, and a help drawer
- Student-friendly flow: step badges, calibration checklist, translated warnings
- Responsive layout: desktop/two-column, tablet drawer, mobile sticky actions
- Export UX: clearer “ready” state and safer download handling
- Generator metadata/version stamping aligned across root + `docs/` copy

## v0.2

- Deterministic finger-joint edge pairing (mates always match)
- Kerf + clearance compensation model for practical fit
