# cec-bridge

An HDMI-CEC and IR bridge for Home Assistant: an ESP32-C3-WROOM-02 running ESPHome
(`Palakis/esphome-hdmi-cec`), on a short HDMI cable into a spare port on the TV or receiver. It
speaks CEC only (pin 13), reads hot-plug detect (pin 19) and can put +5 V on pin 18 for sinks that
only listen on a port that sees it. TMDS and DDC are not connected: no video, no EDID. It also blasts
IR (an on-board 940 nm LED and a JST-PH socket for a stick-on emitter) and has an IR receiver for
learning codes. Power is USB-C from a 5 V wall charger rated 1 A or more, on an always-on socket,
that holds USB's 4.75–5.25 V (simulated to 5.5 V: past 5.25 V pin 18 exceeds HDMI's 5.3 V, and a
contact bounce with pin 18 on can ring it to U6's 7 V limit).
Not the TV's or receiver's USB port: those give 500 mA and often switch off in standby, and Wi-Fi
transmit, IR and pin 18 together peak near 0.6 A (about 0.9 A with pin 18 shorted).


40 × 48 mm, two layers, every part on the top and placed by JLC; nothing to hand-solder.

## Build

```
KICAD_SYMBOL_DIR=~/.local/share/kicad-symbols/x/usr/share/kicad/symbols ./build.sh
```

`gen.py` writes the schematic and board, `route.py` replays the frozen routing in
`cec-bridge/routing.json` (move it aside to autoroute again, only after a placement change), and `build.sh` runs ERC/DRC
and writes JLC's BOM and placement files to `cec-bridge/fab/`. Reviewed in audit rounds until one came back clean, then simulated with the routed copper.

## Ordering

- JLC Standard PCBA, top side. If JLC adds rails, they go on the left and right edges: the module
  antenna overhangs the top edge and the USB-C face the bottom edge (by 0.46 mm).
- JLC's DFM check flags the USB-C shell slots (0.6 mm, below its 0.61 mm alert). They are the
  connector's own figure and JLC drills them; the alert is expected.
- The board edge runs about 0.3 mm past the HDMI socket's face (the USB-C face sits 0.46 mm proud of
  its edge). A plug's moulding tolerates about 1 mm of recess, so an enclosure wall in front of the
  socket should be thin there; seat a real cable at bring-up.
- H1 (the M2 hole beside the switches) has a 3V3 track 1.6 mm from its centre on the top, under
  mask: **nothing metal on the top there** — a nylon screw head, washer or
  standoff, or insert the screw from the back with a nylon washer on top. On the back the nearest
  copper is a 3V3 via 2.7 mm out (track 2.8 mm), so an M2 nut, 4 mm pan head or 4 mm hex standoff is
  fine on that side; not a washer (a DIN 125 sitting off-centre reaches the via).
- H2 has a VBUS track 2.85 mm from its centre on the top and ground otherwise: the same hardware as
  H1's back (M2 nut, 4 mm pan head or hex standoff), no metal washer on the top.
- The HDMI socket is held by its four shell legs. The enclosure should back the socket so plugging
  a cable in doesn't lever the board on its two M2 screws.
- **Stock, re-queried 2026-10-30.** U6 is a **TPS25200DRVT (C2653855)**: 484 listed, 167 orderable.
  The DRVR (C128401) listed 79 but was oversold (JLC's orderable figure -664; LCSC stock 0). Same part,
  small reel. J3 is an XYECONN XY-S2B-PH-SM4-TB (C54582899, about 5,000 orderable), a JST-PH-compatible
  2-pin SMD header; JST's own S2B-PH-SM4-TB (C295747) was down to 2. Every other line had at least
  6,397. **Check U6's orderable number (not the listed stock) before paying.**
- JLC's DFM check may flag same-net copper within 0.07 mm of a few pad openings: C11.1's opening is
  0.010 mm from its own VBUS track (also C10.2, C5.2 at 0.041 mm and TP1 at 0.051 mm). Same net,
  connected: expected.

## Bring-up checks

1. **Unpowered, it must not load the CEC bus** (HDMI 1.4: at most 1.8 µA). Every part on the line
   is chosen on its guaranteed figure: D1 is a BAV170 (a BAT54C passed 1.8 µA from about 37 °C in
   simulation) and the ESD array U3 a TPD4E1U06 (10 nA maximum at 2.5 V, where an SRV05-4 is specified to 5 µA;
   CEC idles at 3.3 V, far below its 6.5 V minimum breakdown).
   Unpowered, feed pin 13 from 3.3 V through 27 kΩ: the drop across the resistor must be under 49 mV.
2. **3V3 during Wi-Fi transmit:** scope it at the regulator and at the module. The output capacitance
   (C4, C5 and the module's own) is above the 22 µF ST characterises the LDL1117's stability for; the
   copper brings the ESR inside its range, and simulation can't prove the phase margin. Look for
   ringing on power-up and on a Wi-Fi burst, with a ground spring. Both capacitors are unlabelled:
   - **At the regulator:** C4 is the 0805 just above U5, left of R25 (the labelled 0603). **Don't
     probe across C4:** its right pad is its return (net C4_ESR), which reaches ground only through
     R25, so once R25 is swapped the probe would miss the ringing. Probe from C4's left pad (3V3) to
     R25's right pad (GND), 5.2 mm apart; U5's pin 1 (GND), 5.0 mm away, also works.
   - **At the module:** C5 is the 0603 in the top-left corner, left of the module's pin 1; its upper
     pad is GND and its lower pad 3V3, 1.55 mm apart.

   If 3V3 rings or oscillates, **swap R25** (0 Ω, in C4's return) for 0.1–0.47 Ω: that puts C4's ESR
   well inside ST's Fig. 20/21 region without a new board. Use tweezers or an iron, not hot air: C4's
   pad is 0.78 mm away and would lift too. Re-scope after the swap. If that is not enough, ST's other
   lever is C4 down to 4.7–10 µF.
3. **Pin 18 with the switch on** follows VBUS to within about 10 mV (U6, a TPS25200, is a 60 mΩ
   switch), so it is the charger's voltage: USB allows 4.75–5.25 V, so only a charger at the very
   bottom of that range puts it under HDMI's 4.8 V minimum. U6 limits the current to 240–350 mA
   (R24 330k; HDMI asks for at most 0.5 A), soft-starts in 2–3 ms, and never back-feeds VBUS while
   off (while on it conducts both ways: a sink driving pin 18 can feed the board). On a held short it
   holds the limit and cycles on its thermal shutdown; the instant a short lands, VBUS dips for
   microseconds while U6's limit catches up (sim4: 3V3 down to 3.03 V on the real copper, below
   3.0 V in a lumped model), so the ESP32 may reset once. That is acceptable for a fault.
   Its input is rated to 20 V, so VBUS ringing to about 9 V at plug-in can't hurt it; above
   6.8–8.45 V it disconnects pin 18, and it clamps pin 18 at 5.25–5.55 V.
   R16 holds it off through reset (IO5 has no pull of its own). Check: switch it on into a real sink,
   then short pin 18 to ground through an ammeter while scoping 3V3 at the module: about
   0.24–0.35 A once settled, and the board running (at most one reset as the short lands).
4. **IR**: the external emitter plugs into J3 with its anode on the pin marked "+" (pin 1, fed from
   VBUS through R20); JST-PH lead colours aren't consistent between suppliers. Each LED takes about 80 mA pulses through 47 Ω. The receiver sits 6 mm from the on-board
   LED and hears its own transmissions; ignore received codes while transmitting.

## Firmware notes

- Keep ESPHome's brown-out detector on (the default): a dropout of a few ms takes 3V3 low without
  EN ever resetting the chip.
- IR transmit: `carrier_duty_percent: 33` (ESPHome defaults to 50), which keeps R19 and R20 inside
  their 1/8 W even within a long burst.
- Debounce HPD (IO6, active low) for a few hundred ms: with a hot, low-threshold Q4 a source low
  near 0.6 V can read as half-asserted.

## Credits and licence

The footprints, symbols and 3D models in `lib/` (the HDMI socket, IR receiver, 2835 IR LED and
SOT-223 parts, and the `cb` symbols) come from the JLCEDA/EasyEDA official library
([lceda.cn](https://lceda.cn), [easyeda.com](https://easyeda.com)), converted with `easyeda2kicad`.
The 3D models are not included: fetch them with `easyeda2kicad --3d --lcsc_id=<part> --output lib/cb`
for the LCSC part numbers in the BOM.

The board design is CERN-OHL-S-2.0 and the scripts MIT, as each file's header says; `vendor/` is
the MIT-licensed [edgecoil-pcb](https://github.com/EdgeCoil/edgecoil-pcb) toolkit. The edgecoil name
and mark are not licensed.

HDMI, the HDMI logo and High-Definition Multimedia Interface are trademarks or registered trademarks
of HDMI Licensing Administrator, Inc. This is an independent hobby design, not a licensed HDMI
product, and is not affiliated with or endorsed by HDMI Licensing Administrator.
