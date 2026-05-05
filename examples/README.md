# CardBoxGen Examples

Regenerate the checked examples from the package API:

```bash
python examples/generate_examples.py
```

Outputs in this folder:

- `tray_open_front.svg`
- `dispenser_slot_front.svg`
- `window_front.svg`
- `box_with_lid.svg`
- `divider_rack.svg`
- `card_shoe.svg`
- `candy_machine_rotary_layered.svg`
- `calibration_mating_strips.svg`
- `invalid_dimension_report.json`

The invalid report is intentional. It records the structured blocking validation response for a tray that is too small to fabricate safely.
