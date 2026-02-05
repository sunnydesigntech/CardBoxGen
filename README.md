# CardBoxGen — Laser-cut Card Tray / Dispenser SVG Generator

Parametric SVG generator for **3mm laser-cut board** card trays / dispensers / boxes.

This project focuses on:
- **Correct cavity sizing** (inner dimensions are the source of truth)
- **Reliable finger joints** that always mate (deterministic edge pairing)
- **Practical kerf + fit** handling for press-fit / friction-fit
- **Browser-first workflow** via a static Pyodide web app (GitHub Pages)

Current version: **v0.4**

Live web app:
- https://sunnydesigntech.github.io/CardBoxGen/

## Key Names (presets + parts)

### Presets (`--preset`)
- `tray_open_front`: open top, lowered/open front, optional scoop
- `dispenser_slot_front`: front present with dispense slot
- `window_front`: front with large window cutout + thumb notch
- `box_with_lid`: box + slip lid

### Panel names (SVG group IDs)
- Base: `BOTTOM`, `BACK`, `LEFT`, `RIGHT`, optional `FRONT`
- Lid (preset `box_with_lid`): `LID_TOP`, `LID_BACK`, `LID_FRONT`, `LID_LEFT`, `LID_RIGHT`

### SVG layer/group conventions
- `CUT` (red stroke, `0.2`)
- `ENGRAVE` (text/labels, black)

## How Finger Joints Are Made (no “phase guessing”)

Instead of choosing a “phase” per panel edge, the generator defines **mating edge pairs**.
Each pair shares one computed `FingerPlan` (finger count + segment widths). One side uses the plan,
the other side uses the **complement** (tabs vs slots), so the two edges always match.

Finger count is stable:

$$n = \max(\text{min\_fingers}, \lfloor L / w_{target} \rfloor)$$

Then `n` is forced odd.

Optional: force fixed counts per joint family:
- `--finger-count-outer`
- `--finger-count-vertical`

## Kerf + Clearance Model

Parameters:
- `--kerf-mm`: laser kerf (typical ~0.15–0.25mm)
- `--clearance-mm`: desired slot–tab clearance (0.00 tight → 0.25 looser)

We model in-plane finger width compensation (so tabs/slots fit after cutting):

- Tabs (external features) shrink after cutting by ~`kerf`.
- Slots (internal openings) grow after cutting by ~`kerf`.

Symmetric drawn-width rule used in the generator:

$$w_{tab,drawn} = w_{nominal} + (kerf - clearance/2)$$
$$w_{slot,drawn} = w_{nominal} + (clearance/2 - kerf)$$

Widths are normalized per edge so the total length stays exactly $L$.

## Local CLI

Acceptance example:
- `python3 cardboxgen_v0_1.py --preset tray_open_front --inner-width 135 --inner-depth 90 --inner-height 225 --thickness 3 --kerf 0.2 --clearance 0.15 --out out.svg`

Optional holding tabs (bridges so parts don’t drop out while cutting):
- `python3 cardboxgen_v0_1.py --preset tray_open_front --inner-width 135 --inner-depth 90 --inner-height 225 --thickness 3 --kerf 0.2 --clearance 0.15 --holding-tabs --tab-width 2 --out out.svg`

Calibration SVG (mating strips across clearances):
- `python3 cardboxgen_v0_1.py --calibration --kerf 0.2 --thickness 3 --out calibration.svg`

## Local Web App (recommended)

The web app runs fully in your browser via Pyodide.

1) Sync generator into the web folder:
- `python3 tools/sync_docs.py`

2) Start a local static server:
- `python3 -m http.server 8000`

3) Open:
- `http://localhost:8000/docs/`

## Examples

- `python3 examples/generate_examples.py`

Outputs in [examples/](examples/):
- `tray_open_front.svg`
- `dispenser_slot_front.svg`
- `box_with_lid.svg`
- `calibration_mating_strips.svg`

## Tests

Dev deps:
- `pip install -r requirements-dev.txt`

Run:
- `pytest -q`

## GitHub Pages

This repo includes an Actions workflow to deploy [docs/](docs/) to GitHub Pages.

Steps:
1) Push to `main` or `master`
2) GitHub repo → Settings → Pages → Source: **GitHub Actions**
3) Wait for the “Deploy GitHub Pages” workflow to finish

Your site URL will be:
- `https://<user>.github.io/<repo>/`

## Versioning + Releases

- The generator version is defined in `__version__` in [cardboxgen_v0_1.py](cardboxgen_v0_1.py).
- The web app version text lives in [docs/app.js](docs/app.js) (`APP_VERSION`) and [docs/i18n/](docs/i18n/) (`app.version`).
- The GitHub Pages app runs the copy in [docs/cardboxgen_v0_1.py](docs/cardboxgen_v0_1.py), so keep it synced.

Release checklist (for a new version):
- Bump `__version__` in both generator copies (or bump root + run `python3 tools/sync_docs.py`).
- Update `APP_VERSION` and `app.version` strings.
- Run tests: `pytest -q`
- Commit, then tag and publish:
	- `git tag -a vX.Y -m "CardBoxGen vX.Y"`
	- `git push origin vX.Y`
	- (optional) `gh release create vX.Y --title "vX.Y" --notes-file CHANGELOG.md`

See [CHANGELOG.md](CHANGELOG.md) for published versions.
