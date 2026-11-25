# cec-bridge enclosure — fit notes & assumptions to verify first

## Measurements applied (from calipers)
- **J2 HDMI height (`hdmi_h = 6.3 mm`):** measured `7.9 mm` from board bottom (`- 1.6 mm` PCB).
- **J2 shell-leg protrusion (`hdmi_leg = 0.8 mm`):** measured `~0.7 mm` below board bottom (`+0.1 mm` margin; shifted STL model gives `0.72 mm`). With `standoff_h = 3.0 mm`, leg tips clear the `2.0 mm` floor by `2.2–2.3 mm`, so no floor relief pockets are cut.
- **J1 USB-C height (`usb_h = 3.4 mm`):** measured `5.0 mm` from board bottom (`- 1.6 mm` PCB).
- **J3 JST-PH height (`jst_h = 5.7 mm`):** measured `7.3 mm` from board bottom (`- 1.6 mm` PCB).
- **U4 IR receiver lens (`u4_lens_up = true`):** confirmed dome perpendicular to the board plane (`+Z`), aperture centred on the STL dome at `(31.5, 3.2)`.

## Fit assumptions to test first
1. **HDMI plug overmould size (`hdmi_mould_w = 20.0`, `hdmi_mould_h = 10.0`):**
   - `J2` sits `0.35 mm` behind the board edge (`y = 47.65`) and the case cavity adds `0.3 mm` clearance (`y = 48.3`), so the front wall cutout is sized for the plug's plastic overmould rather than just the metal barrel.
   - Measure your actual HDMI cable overmould before printing if it is wider than `20 mm` or taller than `10 mm`. At `10 mm` tall, the top of the overmould cutout (`z_bt + 8.15`) notches `0.2 mm` past the lid top (`z_bt + 7.95`) at the front edge (`y = 48.3–49.9`).
2. **HDMI backing rib & rear clearance (`hdmi_rear_y = 36.55`, `rib_gap = 0.15`, `rib_clear = 1.7`):**
   - Derived by shifting the supplier STL model (`+7.25 mm` Y, `+2.91 mm` Z) onto the PCB's through-hole slots. Verify that the rear housing of `J2` sits flush against/within `0.15 mm` of the lid's backing rib (`y = 33.90–36.40`) without stressing the `1.54 mm` component at `x 8.6–11.4, y 31.55–34.45`.
3. **USB-C chunky overmould (`usb_open_w = 12.5`, `usb_open_h = 7.0`):**
   - Centred on `J1` (`x = 32.0`, `z_bt + 1.7`). Test-fit your USB-C power cable plug before closing the case.
4. **Single-sided M3 × 8 mm SHCS (`lugs = [[-5.5, 10.0], [-5.5, 38.0]]`) + outside-stem right-side hooks:**
   - Both `M3 × 8 mm` bolts sit on the connector-free left side (`53.7 mm` overall width including right hook stems, `>= 11.5 mm` from the PCB antenna overhang), threading top-down into `M3 × 5.7 × 4.6` heat-set inserts (`insert_hole_d = 4.0 mm` with `4.6 × 0.6 mm` lead-in chamfer and `0.6 mm` melt relief leaving `1.3 mm` solid plastic below).
   - **Option (b) outside-stem hooks (`y = 6–12` and `33–40`, straddling `J3`):** The lid hook stems (`1.1 mm` thick) drop down *outside* the base right wall (`x = 42.1–43.2`, `0.2 mm` clear of `41.9`) with `45°` flares/ramps (support-free in `lid_print`). The catches reach `1.2 mm` inward (`x = 40.7`, stopping `0.7 mm` clear of the PCB edge `40.0`) into the `z = 3.6–5.8 mm` base wall windows below the `1.6 mm` solid lintels.
   - **Assembly with board installed:** Seat the PCB on the base standoffs/locating pins, lower the lid shifted `+1.4 mm` to the right (`+X`, clearing the `41.9 mm` outer wall, the `Ø4` clamp post beside `H2` at `(36.6, 30.5)` whose right edge is `x = 38.6 <= 38.7`, and the recessed antenna half-lap tongue `x = 5.5–35.5` inside the `x = 3.5–37.0` lid pocket), then slide `-1.4 mm` left (`-X`) so the hooks engage under the lintels and tighten the two left M3 bolts.
   - **Quick right-edge test prints:** Render `part="test_hook_base"` / `part="test_hook_lid"` (`x = 38.5–46, y = 4–15`) for the upper hook, and `part="test_h2_hook_base"` / `part="test_h2_hook_lid"` (`x = 33.5–46, y = 27–42`) for the lower hook + `H2` pin/post/right-wall clearance before printing the full enclosure.
   - `H1` (`Ø5` at `(21.5, 22.8)`) and `H2` (`Ø4` beside `H2` at `(36.6, 30.5)`) clamp posts and the `2.0 mm` base locating pins are **plastic-only** (zero metal near the PCB).
   - `make_outputs.sh` enforces non-empty check exports (no `|| true`) and `< 0.01 mm³` intersection volume across `lid_keepout_check`, `base_keepout_check`, `base_lid_overlap_check`, and all 10 `insertion_check` poses (`dx = +1.4` at `dz = 10, 5, 2, 1, 0.5, 0`; `dz = 0` at `dx = 1.0, 0.6, 0.2, 0`).
5. **Half-lap snap / split fit (`clr = 0.3`, `lap_clr = 0.15`):**
   - Check how snug the PCB sits against the top-edge stops (`y = -0.3`) and side walls (`clr = 0.3 mm`), and whether the `0.15 mm` half-lap clearance binds on your printer/filament (Bambu P1S/A1, 0.4 mm nozzle, PLA/PETG, print without supports).
6. **IR receiver (`U4`) & emitter (`D2`) optical isolation:**
   - `U4` (`d = 4.5 mm` at `(31.5, 3.2)`) and `D2` (`d = 5.0 mm` at `(36.5, 10.0)`) have separate cylindrical shrouds with `>= 1.0 mm` air between their outer walls; confirm `U4` receives normal remote signals through the `4.5 mm` lid tube and does not saturate from `D2` scatter.
7. **Keyholes (`keyholes = [[9, 23], [31, 23]]`, `kh_slot_l = 6.0`):**
   - Sized for `<= 8.0 mm` screw heads (`kh_head_d = 8.2`, `kh_slot_w = 4.2`, `kh_lip = 1.2`, `kh_cavity = 2.2`). Even with screws slid to the upper slot end (`y = 17`), the nearest screw-head edge stays `12.9 mm` from the PCB antenna overhang (`>= 10 mm` rule).
