# CardBoxGen v0.7 — Update Plan (Templates-first Release)

**Status:** v0.6 has a good UI shell (Student Mode, Help/FAQ entry points), but the **templates are not mechanically valid**, so students cannot reliably laser-cut and build working dispensers.  
**v0.7 Goal:** make the *template system* correct, teachable, and exportable for classroom use.

---

## 1) v0.7 outcomes (what “done” looks like)

### Must-have (release blockers)
1. **Templates are mechanically valid** for the stated dispense type:
   - Stacking items (cards/tiles): one-at-a-time pull/dispense is physically plausible.
   - Flowing solids (candy/beans): controlled portioning mechanism exists.
2. **Each template exports a buildable cut set**:
   - SVG (laser cut paths) + labels
   - **Assembly guide** (step-by-step) + bill of materials
   - Parameter summary (what the student chose)
3. **Export is gated by validation**:
   - `error` blocks export with clear “how to fix” actions.
   - `warn` allows export but shows risks (jam/tipping/multi-feed).
4. **Student Mode actually generates**:
   - Student inputs → template selected → parameters auto-filled → preview updates.
5. **UI is stable for students**:
   - Help popovers do not disappear when moving to the tooltip.
   - Preview starts at **Fit** (not over-zoomed).
   - Responsive layout (works on laptop + classroom iPad scale).

### Nice-to-have (if time)
- “Compare templates” view (2–3 suggested mechanisms side-by-side).
- Simple 3D-ish exploded preview (even a static diagram per template).

---

## 2) Scope: v0.7 focuses on “templates as the product”

### Core change
Stop treating templates as “random box variants”.  
Instead, each template is a **mechanism specification** with:
- Required parts (panels + internal components)
- Required cutouts (slots/windows/chutes/pockets)
- Required constraints (anti-jam / anti-multi-feed / stability)
- Assembly method (finger joints / slots / glue zones)

### What v0.7 will NOT do
- No “everything dispenser” AI auto-inventor.
- No full physics simulation.
- No liquids / coin vending (still excluded by brief).

---

## 3) Template system architecture

### 3.1 Template registry (front-end)
Create a single `templates.json` (or JS object) registry that drives:
- Template name (EN/繁中/简中)
- Category (`stacking`, `flowing`, `storage`)
- Input schema (fields, min/max, default, “i” help text)
- Student Mode mapping rules
- Validation rule list (UI-friendly messages)

**Why:** UI should not hardcode per-template fields. The registry makes it scalable.

### 3.2 Template engine (Python / Pyodide)
Adopt the v0.7 prototype engine you already dropped in:
- `cardboxgen_v0_7_templates.py`

**Required integration changes**
- Import templates into Pyodide runtime.
- Expose a single callable like:
  - `generate_svg(template_id, params) -> {svg, warnings, meta, bundle_files}`

### 3.3 Validation model
Standardise warnings:

```json
{ "severity": "error|warn|info", "code": "STRING", "message": "…", "fix": "…" }
```

**Front-end rules**
- If any `severity=error`: disable “Download” and show the errors.
- If warnings exist: show them as a checklist with recommended fixes.

---

## 4) v0.7 templates (the minimum “stable” set)

> Recommendation: mark these as **Stable**; anything else stays **Experimental** until physically verified.

### 4.1 Stable templates to ship
1. `tray_open_front`  
   - Use case: easy-access storage (cards, packets, stationery).
   - Mechanism: open-front access, optional scoop notch.
2. `divider_rack`  
   - Use case: sorted stacks/packets (tea, sleeves, small envelopes).
   - Mechanism: bottom slots + tabbed dividers (students can customise compartments).
3. `window_front`  
   - Use case: storage + visibility (inventory window).
   - Mechanism: window cutout + closed box.
4. `card_shoe` (front-draw)  
   - Use case: one-at-a-time card pull / controlled access.
   - Mechanism: draw slot + retention lip + internal ramp + stabilisers.
5. `rotary_wheel` (candy/beans)  
   - Use case: portioning dry solids.
   - Mechanism: rotating pocket wheel + chute + knob/axle.

### 4.2 Template “contract” (must pass before stable)
Each stable template must:
- Export all required parts (no missing internal pieces)
- Contain at least one **anti-failure constraint**:
  - Card shoe: slot height relative to card thickness; ramp rise; tipping risk.
  - Rotary wheel: chute width vs max piece size; wall thickness between pockets.
- Provide assembly steps.

### 4.3 Kerf / fit rule (standardise)
For slots receiving tabs of thickness `t`:
- Expected final slot ≈ `t + clearance`
- Drawn slot width should be:
  - **drawn_slot = t + clearance − kerf**

Use this rule everywhere for divider slots, tab receivers, axle holes (if relevant).

---

## 5) Student Mode v0.7 (make it *do something*)

### 5.1 Student inputs (from brief)
- Client & context
- Problem statement
- Dispense type: `stacking` vs `flowing`
- Storage target (text + optional numeric)
- Dispense target (one-at-a-time / measured portion)
- Constraints toggles: no coins, no liquids, personal use

### 5.2 Mapping logic: Student Mode → Template selection
Implement a deterministic mapping (no LLM required):
- If `stacking` and “one-at-a-time” → suggest `card_shoe` (primary) + `tray_open_front` (fallback)
- If `stacking` and “organise compartments” → `divider_rack`
- If `flowing` and needs portions → `rotary_wheel` (primary)
- If “visibility/inventory” → `window_front`

**UX:** show 2–3 recommendations with short reasons:
- “Because you said one-at-a-time cards”
- “Because max piece size is Xmm”

### 5.3 Auto-fill mechanics
When student enters:
- Card width/height/thickness → auto-fill internal sizes and slot sizing
- Max piece size → auto-fill pocket diameter/chute width and validate

---

## 6) UI changes required in v0.7

### 6.1 Responsive layout
- Use CSS grid with breakpoints:
  - Desktop: 2 columns (left controls / right preview)
  - Tablet: stacked layout, preview on top, controls below
- Ensure preview container height adapts to viewport (`vh`), not fixed px.

### 6.2 Preview default zoom
- On first render or template change: automatically call **Fit**
- Provide persistent zoom controls (+/−/Fit)

### 6.3 Help (“i” tooltips) stability fix
Current issue: tooltip disappears when moving mouse from icon to tooltip.

Fix options (choose one):
1. Use a **popover** component that stays open until click outside.
2. On hover: add a small delay and keep open while either trigger OR popover is hovered.
3. On mobile: popover opens on tap (no hover).

**Requirement:** students can move mouse into tooltip to click “Help” or read content.

### 6.4 Remove “Generate calibration SVG” (per request)
- Delete button + any code paths
- Replace with:
  - “Fit / Kerf tips” section inside Help + FAQ
  - Optional “Kerf test explanation” (text-only)

### 6.5 Language switcher
Top-right:
- English
- 繁體中文
- 简体中文

Implementation:
- i18n key-value dictionary (no hardcoded strings in components)
- Help/FAQ content must also be translated (at least core sections)

---

## 7) Export: from “SVG only” → student-ready ZIP bundle

### 7.1 New default export button
Replace “Download SVG” with:
- **Download project pack (ZIP)**

### 7.2 ZIP bundle contents (minimum)
1. `cut.svg` (the laser cut file)
2. `project_summary.md` (student inputs + chosen template + derived sizes)
3. `assembly_guide.md` (step-by-step + glue notes)
4. `bom.md` (materials + optional hardware: dowel/axle/magnets if template needs)
5. `teacher_notes.md` (optional: common failure modes + troubleshooting)

### 7.3 Assembly guide content requirements
For each template:
- Cut list (parts with labels)
- Join order (bottom → walls → internals → optional stabilisers)
- Notes for fit/jam troubleshooting:
  - “If slot too tight: increase Fit slider / clearance by 0.1mm”
  - “If candy bridges: increase chute width”

---

## 8) Help + FAQ content (student-ready)

### 8.1 Help: per-field micro-guidance
For every parameter with an “i” button:
- What it means (simple)
- What happens if too big/small
- Typical values (examples)
- A “common mistake” note

**Examples**
- Thickness: measure material with calipers; do not trust label (3mm may be 2.8–3.2).
- Kerf: depends on machine/material; if unknown, use 0.15–0.25mm as a starting point.
- Fit/clearance: tight vs loose (why you might choose each).

### 8.2 FAQ sections (minimum list)
- “Why don’t my finger joints fit?”
- “What is kerf and why does it matter?”
- “Why did my dispenser jam?” (stacking vs flowing)
- “Why are two cards coming out?”
- “Why does candy bridge over the chute?”
- “My parts are too loose—what do I change?”
- “Which template should I choose for my project?”
- “How do I adapt the design for a different item size?”

---

## 9) QA & classroom reliability

### 9.1 Software QA
- Add “golden” sample parameters per template.
- Export and store `sample_*.svg` for regression checks.
- Unit tests (Python) for:
  - non-negative dimensions
  - slot widths valid
  - minimum pocket wall thickness
  - template includes required parts

### 9.2 Physical QA (minimum)
For each Stable template:
- One physical cut in 3mm board (or your target classroom material)
- Record:
  - kerf used
  - clearance used
  - failure modes and adjustments
- Update defaults accordingly.

---

## 10) Implementation checklist (what to do next)

### A. Integrate v0.7 template engine
- [ ] Import `cardboxgen_v0_7_templates.py` into Pyodide
- [ ] Wrap generator API: `generate_svg(template_id, params)`
- [ ] Surface warnings/errors in UI
- [ ] Block export on errors

### B. Replace old templates
- [ ] Remove v0.6 template dropdown options that are not implemented mechanically
- [ ] Add the 5 stable templates with correct parameter schemas

### C. Student Mode mapping
- [ ] Implement mapping rules (deterministic)
- [ ] Auto-fill parameters
- [ ] Show “Recommended templates” cards

### D. UI improvements
- [ ] Fix Help tooltip disappearing
- [ ] Remove calibration button
- [ ] Preview starts at Fit
- [ ] Responsive layout improvements

### E. i18n
- [ ] Add language toggle
- [ ] Translate UI strings + Help/FAQ core content

### F. ZIP project pack export
- [ ] ZIP assembly guide + summary + SVG
- [ ] Add template-specific assembly instructions

---

## 11) Versioning & release notes

### v0.7.0 (this release)
- Replace broken templates with mechanism-first stable set
- Validation gating + improved Student Mode mapping
- ZIP project pack export
- Help/FAQ + tooltip stability

### v0.7.1 (follow-up)
- Refine defaults based on physical tests
- Add 1–2 more experimental mechanisms (only if physically validated)

---

## Appendix: Template parameter sets (recommended defaults)

### Card shoe (front draw)
- Slot height: `card_t + 0.6mm` (min clamp at ~1.0mm)
- Slot width: `0.85 * card_w`
- Lip height: 10mm
- Ramp: 10–15° (start at 12°)

### Rotary wheel candy
- Pocket diameter: `max_piece + 1mm` (or +2mm if irregular)
- Chute width: `pocket_d + 2mm`
- Min wall between pockets: ≥2mm (block export if <2mm)

---
