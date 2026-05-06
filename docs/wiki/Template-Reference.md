# Template Reference

CardBoxGen supports these first-class template ids.

## `tray_open_front`

Open-top tray with back, left, right, bottom, and lowered front panels. The lowered front keeps bottom and side mating joints only where the front physically meets the side walls.

Typical use:

- sleeved card trays;
- deck storage;
- classroom card sorting.

Key parameters:

- `inner_w`, `inner_d`, `inner_h`;
- `front_height`;
- `scoop` or thumb cutout options;
- `thickness`, `kerf`, `clearance`.

## `dispenser_slot_front`

Box/tray front with a dispensing slot. Slot geometry is validated against side edges, top/bottom margins, and joint zones.

Typical use:

- card draw boxes;
- token or ticket dispensers;
- small classroom material organizers.

## `window_front`

Front panel with a rounded window and optional thumb notch. Window margins must leave enough structural material around the opening.

Typical use:

- visible card holders;
- display trays;
- simple front-window storage.

## `box_with_lid`

Base box plus slip lid. Lid internal dimensions are derived from the body external dimensions plus lid clearance.

Typical use:

- protected card boxes;
- storage with removable cover;
- prototype packaging.

## `divider_rack`

Tray with internal divider panels and matching divider slots.

Typical use:

- multi-bay card sorting;
- classroom organizers;
- index-card racks.

## `card_shoe`

Front-draw card dispenser derived from card width, card height, card thickness, and capacity. Includes ramp, hold-down lip, and optional follower-style support.

Mechanical assumptions:

- cards are flat and reasonably consistent thickness;
- friction depends on surface material;
- draw slot height must allow one or a small controlled stack of cards to exit.

## `candy_machine_rotary_layered`

Educational layered rotary dispenser prototype for dry flowing solids. It generates front/back plates, side plates, wheel layers, spacers, screw holes, chute, hopper pieces, and related parts.

Mechanical assumptions:

- dry flowing solids only;
- not food-safe machinery;
- must be physically prototyped for bridging, jamming, and friction;
- wheel pockets, axle holes, screw holes, and rim clearance are validation-sensitive.

## `calibration`

Fit-test strips and reference geometry for checking scale, thickness, kerf, and clearance before cutting a full project.

Run calibration when:

- changing material;
- changing laser settings;
- switching between plywood, acrylic, or board stock;
- a press fit is too loose or too tight.

## Legacy Aliases

These aliases are accepted with deprecation warnings:

- `card_shoe_front_draw` -> `card_shoe`
- `candy_rotary_wheel` -> `candy_machine_rotary_layered`
- `rotary_wheel` -> `candy_machine_rotary_layered`
