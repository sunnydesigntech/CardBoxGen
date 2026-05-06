# Fabrication Model

CardBoxGen generates centerline SVG paths for laser cutting.

## Kerf Convention

CardBoxGen treats `kerf` as the full width removed by the laser cut.

```text
burn_radius_mm = kerf_full_width_mm / 2
```

Do not enter a half-kerf value unless you intentionally converted it to full width.

## Fit Rules

External material tabs shrink after cutting. Internal slots and holes grow after cutting.

Open-edge finger depth:

```text
target final tab depth  = thickness
target final slot depth = thickness + clearance
drawn tab depth         = thickness + kerf
drawn slot depth        = thickness + clearance - kerf
```

Segment width:

```text
final tab width  = drawn tab width - kerf
final slot width = drawn slot width + kerf
```

CardBoxGen compensates tab/slot widths, then normalizes each shared edge plan so the total edge length remains exact.

## Corner Rule

Fingered edges reserve a clean no-finger zone at both ends:

```text
corner_clearance = max(thickness, target_finger_width / 2, 2 * kerf) + max(drawn_tab_depth, drawn_slot_depth)
usable_joint_span = edge_length - 2 * corner_clearance
```

If the usable span cannot fit the requested odd minimum finger count at or above the minimum feature width, export is blocked with `JOINT_USABLE_SPAN_TOO_SHORT`.

## Calibration

Measure real material thickness with calipers. Cut calibration strips before a full project. Do not apply kerf compensation in both CardBoxGen and laser software at the same time.
