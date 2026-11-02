# cec-bridge

An HDMI-CEC and IR bridge for Home Assistant: an ESP32-C3 running ESPHome that plugs into a spare
port on a TV or AV receiver, talks CEC, and blasts and learns IR. 40 × 48 mm, two layers, every
part placed by the assembler.

- [`cec-bridge/`](cec-bridge/): the board, its generator and build, and the full README (what it
  does, how to build and order it, bring-up checks, firmware notes, credits and licence).
- [`vendor/`](vendor/): the [edgecoil-pcb](https://github.com/EdgeCoil/edgecoil-pcb) toolkit the
  board is built with, vendored so the board builds on its own.

Not yet built: the design is reviewed and simulated, but no boards have been ordered.

HDMI is a trademark of HDMI Licensing Administrator, Inc. This is an independent design, not a
licensed HDMI product.
