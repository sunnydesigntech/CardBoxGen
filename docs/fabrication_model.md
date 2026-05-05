# CardBoxGen Fabrication Model

CardBoxGen is a centerline SVG generator. It draws the paths the laser should follow, then uses an explicit kerf and fit model to predict the final material edge after cutting.

## References Used

The model follows common laser-cutting practice, but the implementation is original to this MIT project.

- Boxes.py treats material thickness as a critical measured value and warns that even small thickness changes affect finger-joint stiffness. It also distinguishes its `burn` value as a radius-style correction and recommends fit tests.
- LightBurn documents kerf as the material removed by the beam, explains that outside parts shrink and holes grow when a beam follows the centerline, and recommends kerf test cuts.
- MakerCase-style generators are useful UX references: users enter dimensions and material thickness, then export SVG/DXF with optional kerf adjustment.

Sources:

- <https://florianfesti.github.io/boxes/html/usermanual.html>
- <https://docs.lightburnsoftware.com/latest/Guides/Test-KerfOffset/>
- <https://www.dmaf-lab.com/resources/free-parametric-box-generator-for-laser-cutting>

## Parameter Convention

CardBoxGen uses:

```text
kerf_full_width_mm = full width removed by the laser cut
burn_radius_mm     = kerf_full_width_mm / 2
```

This is different from software that asks for a half-kerf or burn-radius value. If another tool uses a radius-style kerf parameter, do not copy that number directly into CardBoxGen without converting it.

## Sign Convention

For a centerline cut:

- external material tabs shrink after cutting;
- internal gaps, holes, and slots grow after cutting;
- open-edge finger recesses are modeled separately from closed rectangular holes;
- changing kerf changes drawn cut coordinates, not the requested nominal internal cavity.

## Width Formulas

For features bounded by two side cuts:

```text
final_tab_width_from_drawn(drawn, kerf)  = drawn - kerf
final_slot_width_from_drawn(drawn, kerf) = drawn + kerf

drawn_tab_width_for_target(target, kerf)  = target + kerf
drawn_slot_width_for_target(target, kerf) = target - kerf
```

CardBoxGen targets:

```text
target final tab width  = nominal segment width - clearance / 2
target final slot width = nominal segment width + clearance / 2
```

The drawn widths are normalized across the edge so the shared `FingerPlan` length remains exact. Very unbalanced kerf/clearance combinations can exceed the valid fit domain for odd shared finger plans; validation returns `FIT_COMPENSATION_UNBALANCED` instead of silently exporting those files.

## Depth Formulas

Open-edge finger-joint depth is a one-direction fit:

```text
target final tab depth  = thickness
target final slot depth = thickness + clearance
drawn tab depth         = thickness + kerf
drawn slot depth        = thickness + clearance - kerf
```

This assumes the recess is open to a cut edge. Closed holes use the width formulas because two opposing cut sides define the final dimension.

## Nominal Mechanical Model

For box-like presets, inner dimensions are the source of truth. The nominal model stores:

- material thickness;
- internal width/depth/height;
- panel specs;
- shared edge-pair joint plans;
- cutout specs;
- layout constraints;
- validation limits and warnings.

The generated metadata records the internal and external dimensions, the shared edge-pair plan ids, tab masks, drawn widths, final-width estimates, and fit-model limits.

## Laser Cut Path Model

The SVG writer emits:

- mm units and a viewBox;
- red `CUT` paths for panel outlines and cutouts;
- blue `SCORE` paths where used;
- gray `ENGRAVE` labels;
- JSON metadata embedded in `<metadata>`.

The default export mode is centerline compensated by CardBoxGen. A future nominal/no-kerf export mode can be added for workflows where laser software applies kerf compensation itself.

## Calibration Guidance

Measure actual material thickness with calipers before generating production parts. Nominal 3 mm stock may differ enough to change joint stiffness.

Cut `calibration_mating_strips.svg` on the target machine and material before cutting a full box. Use the measured result to tune:

- material thickness;
- full-width kerf;
- assembly clearance.

Use only one kerf-compensation system at a time. If CardBoxGen compensates kerf, leave cutter-software kerf offset disabled for the same file.

## Known Physical Limits

CardBoxGen rejects impossible or unsafe geometry when it can detect it:

- nonpositive thickness;
- negative kerf or clearance;
- kerf greater than or equal to thickness;
- too-small internal dimensions;
- even or tiny finger counts;
- finger pitch below minimum feature width;
- unsafe window/slot margins;
- divider bays that are too narrow;
- screw holes too close to edges;
- rotary pockets too close to axle or rim;
- candy-machine wheel layer counts that cannot assemble.

The candy-machine preset is an educational prototype for dry flowing solids. It is not food-safe machinery and must be physically prototyped for bridging, jamming, and friction.
