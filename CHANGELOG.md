# Changelog

## v0.8.1

- Added project handoff tools: copy share link, copy `CBG1:` project/location code, import code, and optional QR scanning.
- Added camera-permission fallback handling so blocked QR scanning points users to direct Safari/Chrome access or project-code import.
- Added `/exec/` redirect entry point and camera/QR troubleshooting documentation.
- Added GitHub-facing repository documentation: contribution guide, support policy, security notes, PR template, issue forms, and expanded wiki source pages.
- Added an explicit full-width kerf fabrication model with tested tab/slot width and depth compensation formulas.
- Added `validate_template_params()` with normalized parameters, computed limits, structured field-level messages, and blocking/nonblocking severity.
- Changed API and CLI behavior so impossible geometry returns a non-exportable diagnostic result instead of silently producing a cut file.
- Added reserved no-finger corner zones and span-aware validation so adjacent fingered edges cannot overlap into square corner artifacts.
- Added transparent default tray-front height normalization when the omitted default would be too short for valid side joints.
- Added assembly-oracle, invalid-dimension, fabrication-model, property, and slow deterministic geometry tests.
- Expanded calibration output with width-fit slots, depth-fit notches, and a known-size reference rectangle.
- Updated the web app to display Python-computed fit-model values and keep export disabled for blocking errors.
- Regenerated examples and added `invalid_dimension_report.json`.
- Documented the fabrication model, hardening audit, valid-dimensions contract, and practical calibration workflow.

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
