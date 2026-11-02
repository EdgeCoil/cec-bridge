# SPDX-FileCopyrightText: 2026 edgecoil
# SPDX-License-Identifier: CERN-OHL-S-2.0
"""Generate the CEC bridge PCB: a KiCad schematic and an unrouted board.

An ESP32-C3 on the HDMI-CEC bus of an AV stack, for Home Assistant (ESPHome): it
plugs into a spare HDMI input of an AV receiver with an ordinary cable, uses only CEC, ground, +5 V
and hot-plug detect (no video lanes), and adds an IR blaster and receiver. Power is USB-C.

The netlist below is the single source of truth: the schematic (labels on every pin) and the board
are both written from it, and build.sh's DRC parity check compares the netlist KiCad reads back
from the schematic against the board's pads. Adapted from the tune-button generator.

    python3 gen.py cec-bridge     then ./build.sh to route, check and export
"""
import os
import sys
import uuid

import pcbnew

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "vendor"))
from edgecoil_pcb import C, C0805, LED0805, R, R0805, Config, Part, build, holes, zone  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))


W = 40.0
H = 48.0


def variant_cec():
    """ESP32-C3-WROOM-02 with its antenna over the top edge (as on tune-button c3-jst), the HDMI socket
    at the bottom left under the module's left pins (CEC, 5 V enable, hot-plug), USB-C at the bottom
    right, and the IR parts in the right column by the module's IO0/IO1."""
    mx, my = 14.0, 6.8  # module origin; the antenna (the module's top 6.35 mm) overhangs the top edge
    parts = [
        Part("U1", "RF_Module:ESP32-C3-WROOM-02", "RF_Module:ESP32-C3-WROOM-02", "ESP32-C3-WROOM-02-N4",
             {"1": "3V3", "2": "EN", "3": "CEC_IO", "4": "HDMI5V_EN", "5": "HPD_N", "6": "", "7": "IO8",
              "8": "IO9", "9": "GND", "10": "LED", "11": "RXD", "12": "TXD", "13": "USB_DN", "14": "USB_DP",
              "15": "", "16": "IO2", "17": "IR_RX", "18": "IR_TX", "19": "GND"}, (mx, my),
             mpn="ESP32-C3-WROOM-02-N4", lcsc="C2934560"),

        # ---- Power: USB-C in, 3.3 V out. Nothing runs from a battery, so the regulator is chosen for
        # its input rating, not its idle current: the LDL1117 takes 18 V (abs. max 20 V), so a USB
        # plug-in's ringing (the tune-button's RT9080 had 6.5 V to spare) has nothing to reach. It is
        # stable with ceramic capacitors (>= 4.7 uF out), unlike the AMS1117.
        Part("J1", "Connector:USB_C_Receptacle_USB2.0_16P", "Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12",
             "USB-C", {"A1": "GND", "A4": "VBUS", "A5": "CC1", "A6": "USB_DP", "A7": "USB_DN", "A8": "",
                       "A9": "VBUS", "A12": "GND", "B1": "GND", "B4": "VBUS", "B5": "CC2", "B6": "USB_DP",
                       "B7": "USB_DN", "B8": "", "B9": "VBUS", "B12": "GND", "S1": "GND"},
             (32.0, H - 3.19), mpn="HRO TYPE-C-31-M-12", lcsc="C165948"),
        R("R1", "5.1k", "CC1", "GND", (31.0, H - 15.7), 90),
        R("R2", "5.1k", "CC2", "GND", (33.0, H - 15.7), 90),
        # USB ESD: SRV05-4, its rail on 3V3 as on the tune-button.
        Part("U2", "Power_Protection:SRV05-4", "Package_TO_SOT_SMD:SOT-23-6", "SRV05-4",
             {"1": "USB_DP", "2": "GND", "3": "USB_DN", "4": "USB_DN", "5": "3V3", "6": "USB_DP"},
             (32.0, H - 11.6), 90, mpn="SRV05-4-P-T7", lcsc="C85364"),
        Part("U5", "cb:LDL1117S33R", "cb:SOT-223-4_L6.5-W3.5-P2.30-LS7.0-BR", "LDL1117S33R",
             {"1": "GND", "2": "3V3", "3": "VBUS", "4": "3V3"}, (22.5, 38.5), 90, mpn="LDL1117S33R", lcsc="C435835"),
        C("C1", "10u", "VBUS", "GND", (22.5, 45.2), 0, fp=C0805),
        # ST DS12022 6.2: an input capacitor of 1 uF or more "as close as possible to the input pin of the
        # device and returned to a clean analog ground". C1 is 10 mm of track away past the tab (accepted
        # through round 20 before the datasheet's wording was checked), so C11 sits beside pin 3: VBUS pad on a
        # 0.77 mm stub square onto pin 3's track, GND pad into the pour by its own spokes. 34.6, not lower:
        # J2's courtyard doesn't enclose its shell-leg pad 22, and at 35.0 C11's GND pad merged into it
        # (round 21); pth_inside_courtyard is an error now so that can't recur. C1 stays as the bulk.
        C("C11", "1u", "VBUS", "GND", (17.6, 34.6), 270),
        # C4's return goes through R25, fitted 0 ohm. The output network lies outside ST's characterised
        # stability region (DS12022 Fig. 20/21: ESR floor ~0.012 ohm at 22 uF; C4 is ~4.7 mohm). If 3V3
        # rings at bring-up, a 0.1-0.47 ohm 0603 in R25's place raises C4's ESR into that region, no respin.
        # Second change to the LDO block on this board (C11 was the first), so its design was reviewed again
        # (round 24): kept. The LDL1117's 20 V input rides out the ~9 V VBUS plug-in ring, which most
        # "any ceramic" LDOs (6 V absolute maximum) would not; R25 is the standard way to add output ESR.
        C("C4", "22u", "3V3", "C4_ESR", (23.0, 31.5), 0, fp=C0805),
        Part("R25", "Device:R", "Resistor_SMD:R_0603_1608Metric", "0", {"1": "C4_ESR", "2": "GND"}, (26.2, 33.0), 0,
             mpn="0603WAF0000T5E", lcsc="C21189"),
        C("C5", "10u", "3V3", "GND", (2.2, 2.0), 90),  # at the module: the 22u is 46 mm of track away

        # ---- Reset, boot and straps (as on the tune-button c3). IO2 and IO8 must read high at reset.
        R("R6", "10k", "3V3", "EN", (2.2, 5.0), 90),
        C("C6", "1u", "EN", "GND", (2.2, 8.0), 90),
        R("R7", "10k", "3V3", "IO8", (2.2, 11.0), 90),
        R("R9", "10k", "3V3", "IO2", (25.4, 4.3), 0),
        Part("SW1", "Switch:SW_Push", "Button_Switch_SMD:SW_Push_1P1T_XKB_TS-1187A", "RESET",
             {"1": "EN", "2": "GND"}, (5.7, 18.8), mpn="XKB TS-1187A-B-A-B", lcsc="C318884"),
        Part("SW2", "Switch:SW_Push", "Button_Switch_SMD:SW_Push_1P1T_XKB_TS-1187A", "BOOT",
             {"1": "IO9", "2": "GND"}, (14.6, 18.8), mpn="XKB TS-1187A-B-A-B", lcsc="C318884"),
        R("R12", "1k", "LED", "LED_A", (26.5, 15.0), 0),
        Part("D3", "Device:LED", LED0805, "LED", {"1": "GND", "2": "LED_A"}, (26.5, 17.2), 0, lcsc="C84256"),
        Part("TP1", "Connector:TestPoint", "TestPoint:TestPoint_Pad_1.0x1.0mm", "TXD", {"1": "TXD"}, (19.5, 16.0),
             note="debug UART"),
        Part("TP2", "Connector:TestPoint", "TestPoint:TestPoint_Pad_1.0x1.0mm", "RXD", {"1": "RXD"}, (22.0, 16.0),
             note="debug UART"),

        # ---- HDMI: CEC (13), its ground (17), +5 V (18) and hot-plug detect (19) only. The TMDS and
        # DDC pins stay unconnected: no video passes, and the board is a source on this port.
        Part("J2", "cb:HDMI-001", "cb:HDMI-SMD_19P-P0.50-H-F", "HDMI-A",
             {"13": "CEC", "17": "GND", "18": "HDMI_5V", "19": "HPD",
              "20": "GND", "21": "GND", "22": "GND", "23": "GND"},
             (10.0, H - 7.6), 0, mpn="HDMI-001 19PCBTP", lcsc="C138388"),
        # CEC: one bidirectional open-drain line, which the ESPHome hdmi_cec component drives from a single
        # pin. A BSS138 with its gate on 3V3 joins the two sides (the I2C level-shifter circuit): either
        # side pulling low pulls the other low through the channel or body diode. Unpowered, its gate is
        # at 0 V and it is off, so a dead bridge leaves the bus alone; wired straight to the pin, the
        # chip's protection diode would clamp CEC to an unpowered 3V3 and take the bus down for every
        # device on it (HDMI 1.4 CEC: an unpowered device may sink at most 1.8 uA).
        Part("Q1", "Transistor_FET:BSS138", "Package_TO_SOT_SMD:SOT-23", "BSS138",
             {"1": "3V3", "2": "CEC_IO", "3": "CEC"}, (5.5, 29.4), 0, mpn="BSS138LT1G", lcsc="C82045"),
        R("R10", "10k", "3V3", "CEC_IO", (5.5, 25.6), 0),
        # The bus side's own 27k pull-up (CEC's figure for every device), fed through a diode so it
        # draws nothing from the bus when unpowered. A BAV170 (both halves in parallel), not a Schottky:
        # a BAT54C's reverse leakage passes HDMI's 1.8 uA once it is warm (sim1: 2.2 uA at 40 C), the
        # BAV170's is in nA. Drawn with the BAV70 symbol: the same common-cathode SOT-23 pinout.
        Part("D1", "Diode:BAV70", "Package_TO_SOT_SMD:SOT-23", "BAV170",
             {"1": "3V3", "2": "3V3", "3": "CEC_PU"}, (9.5, 25.6), 0, mpn="BAV170,215", lcsc="C109309"),
        R("R11", "27k", "CEC_PU", "CEC", (9.5, 29.4), 0),
        # ESD on the HDMI wires, to ground only, with no supply pin to feed CEC or HPD into an unpowered
        # 3V3. A TPD4E1U06: 10 nA maximum leakage (specified at 2.5 V; CEC idles at 3.3 V, far inside
        # its 6.5 V minimum breakdown), against the 1.8 uA HDMI allows an unpowered device on CEC
        # (an SRV05-4 is only specified to 5 uA, at 5 V). Same
        # SOT-23-6 pin map as the SRV05-4 it replaced (I/O 1, 3, 4, 6; GND 2; pin 5 NC).
        Part("U3", "cb:TPD4E1U06DBV", "Package_TO_SOT_SMD:SOT-23-6", "TPD4E1U06",
             {"1": "CEC", "2": "GND", "3": "HPD", "4": "HDMI_5V", "5": "", "6": ""},
             (10.0, 33.0), 0, mpn="TPD4E1U06DBVR", lcsc="C124691"),
        # Hot-plug detect, 0-5.3 V from the sink: a BSS138 inverts it to 3.3 V logic (its gate takes 5 V
        # with no divider to tune). 100k holds it off with no cable.
        Part("Q4", "Transistor_FET:BSS138", "Package_TO_SOT_SMD:SOT-23", "BSS138",
             {"1": "HPD", "2": "GND", "3": "HPD_N"}, (5.5, 33.0), 0, mpn="BSS138LT1G", lcsc="C82045"),
        R("R13", "100k", "HPD", "GND", (2.2, 33.0), 90),
        R("R14", "10k", "3V3", "HPD_N", (2.2, 29.4), 90),
        # +5 V to the sink (pin 18), off unless asked for: some sinks only listen on a port that sees
        # it. A TPS25200 eFuse does the whole job HDMI asks of a source: current limit (R24 330k:
        # 240-350 mA by TI's min/max equations, as 330k isn't in its table; under HDMI's 0.5 A and well
        # over its 55 mA), soft start (2-3 ms rise), no back-feed into VBUS when off, and a 60 mohm
        # switch (pin 18 sits a few mV under VBUS).
        # Its input is rated to 20 V: VBUS rings to ~9 V at plug-in (sim3 s2a), which a TPS2553's 7 V
        # input could not take (audit round 17). Over 6.8-8.45 V it disconnects, and it clamps pin 18 at
        # 5.25-5.55 V. It replaced a discrete AO3401A/BSS138 switch with a polyfuse, a Miller soft start
        # and a cap to stop the soft start firing at plug-in: each fix there needed the next (sim1, round 8).
        # EN has no pull inside and IO5 (MTDI) floats through reset, so R16 holds it off; FAULT is
        # left open (an overload shows as pin 18 sagging, and the limit protects the board anyway).
        # DRVT, not DRVR: the same part on TI's small reel. JLC's DRVR stock (C128401) was oversold on
        # 2026-10-30 (79 listed, -664 orderable; round 22); the DRVT had 167 orderable.
        Part("U6", "cb:TPS25200DRV", "Package_SON:WSON-6-1EP_2x2mm_P0.65mm_EP1x1.6mm", "TPS25200DRVT",
             {"1": "HDMI_5V", "2": "ILIM", "3": "", "4": "HDMI5V_EN", "5": "GND", "6": "VBUS", "7": "GND"},
             (14.6, 26.6), 180, mpn="TPS25200DRVT", lcsc="C2653855"),
        # TI: 0.1 uF or more from IN to GND, as close to the IC as possible: C9 stands beside U6's IN
        # and GND pins, both joined on the top (audit round 15: its ground had gone through the plane).
        # R24 sits straight off ILIM on the other side (TI: keep the ILIM track short).
        C("C9", "100n", "VBUS", "GND", (12.4, 26.9), 90),
        R("R24", "330k", "ILIM", "GND", (17.5, 26.6), 0),
        # TI also wants a 0.1 uF ceramic on OUT (8.4.1), so C10. It is not bounce protection: in a VBUS
        # contact bounce with EN high, pin 18 follows the re-step ring (sim4 s16: 6.60 V worst at a
        # 5.25 V charger against OUT's 7 V abs max, 7.10 V only with an out-of-spec 5.5 V one).
        C("C10", "100n", "HDMI_5V", "GND", (17.4, 29.3), 270),
        R("R16", "100k", "HDMI5V_EN", "GND", (19.0, 31.6), 90),

        # ---- IR. The blaster: an on-board 940 nm LED and a JST-PH for a stick-on emitter on a cable
        # (to reach a device across the room), each through 47 ohm from VBUS (~80 mA pulses, inside the LED's 100 mA DC rating), switched low-side
        # by an AO3400A.
        Part("Q5", "Transistor_FET:AO3400A", "Package_TO_SOT_SMD:SOT-23", "AO3400A",
             {"1": "IR_G", "2": "GND", "3": "IR_K"}, (30.0, 10.0), 0, mpn="AO3400A", lcsc="C20917"),
        R("R17", "100", "IR_TX", "IR_G", (25.4, 8.0), 0),
        R("R18", "100k", "IR_G", "GND", (25.4, 10.0), 0),
        R("R19", "47", "VBUS", "IR_A1", (34.0, 14.0), 0, fp=R0805),
        Part("D2", "cb:P2835P1IRS7G12940NM", "cb:LED-SMD_L3.5-W2.8_CZ2835", "IR 940nm",
             {"1": "IR_K", "2": "IR_A1"}, (36.5, 10.0), 90, mpn="P2835P1IRS7G12", lcsc="C22466173"),
        R("R20", "47", "VBUS", "IR_A2", (30.5, 14.0), 0, fp=R0805),
        Part("J3", "Connector_Generic:Conn_01x02", "Connector_JST:JST_PH_S2B-PH-SM4-TB_1x02-1MP_P2.00mm_Horizontal",
             "IR out", {"1": "IR_A2", "2": "IR_K"}, (34.5, 21.0), 90, mpn="XYECONN XY-S2B-PH-SM4-TB", lcsc="C54582899"),
        # The receiver: 38 kHz, open-collector out; RC on its supply as its datasheet asks.
        Part("U4", "cb:IRM-H638T_TR2", "cb:SENSOR-SMD_IRM-H638T-TR2-TL", "IRM-H638T",
             {"1": "GND", "2": "GND", "3": "IR_RX", "4": "IR_VCC"}, (31.5, 4.0), 0, mpn="IRM-H638T/TR2",
             lcsc="C91447"),
        R("R21", "100", "3V3", "IR_VCC", (38.2, 2.4), 90),
        C("C7", "4.7u", "IR_VCC", "GND", (38.2, 6.0), 90),
        R("R22", "10k", "3V3", "IR_RX", (25.4, 6.0), 0),
    ]
    parts += holes([(21.5, 22.8), (37.5, 30.5)])
    # RESET and BOOT above the switches (the space below SW2 carries 3V3 and VBUS).
    silk = [("text", 6.1, 14.95, "RESET"), ("text", 14.6, 14.95, "BOOT"), ("text", 19.5, 17.9, "TX"),
            ("text", 22.0, 17.9, "RX"),
            ("text", 28.9, 22.0, "+")]  # J3's anode (IR_A2): the emitter's lead colours vary by supplier
    extras = {"width": W, "label_margin": 0.5,
              "back_text": [(29.8, 33.0, "cec-bridge", 1.2), (29.8, 34.9, "edgecoil.dev", 1.0), (26.1, 38.1, "rev A", 1.0)],
              # The mark (7.5 mm) and URL fit only where the frozen routing leaves room: no back track under
              # the mark, no via within 1 mm of any back artwork. "rev A" moved down to clear the vias.
              "logo": (9.0, 3.0, 7.5),
              "hide_refs": ["TP1", "TP2", "SW2", "C11"]}  # C11's label took U3's and R16's spots (round 21)
    return parts, H, [], silk, extras


VARIANTS = {"cec-bridge": variant_cec}


def hdmi_shell(board):
    """The HDMI socket's shell sits on the board the way the USB-C's does. LCSC's footprint draws no
    body on the fab layer, so the area is from its pads: from just in front of the signal row (whose
    pads end 2.08 mm behind the origin) to the mouth (7.6 mm ahead), between the shell legs."""
    for fp in board.Footprints():
        if fp.GetFPIDAsString().startswith("cb:HDMI"):
            c = fp.GetPosition()
            x, y = pcbnew.ToMM(c.x), pcbnew.ToMM(c.y)
            zone(board, None, pcbnew.F_Cu, [(x - 7.9, y - 1.6), (x + 7.9, y - 1.6), (x + 7.9, y + 7.6), (x - 7.9, y + 7.6)],
                 track_free=True)
            # Its pins are 0.5 mm apart, so the pour reaches a ground pin from the front only: one
            # thermal spoke where DRC wants two. Join it solid instead; it is reflowed, not hand-soldered.
            for pd in fp.Pads():
                if pd.GetNetname() == "GND" and pd.GetAttribute() == pcbnew.PAD_ATTRIB_SMD:
                    pd.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)


CFG = Config(
    project="cec-bridge", here=HERE, ns=uuid.UUID("3f6a2b4e-0c1d-4e8a-9b57-cec0b41d9e21"), variants=VARIANTS,
    width=W,
    logo_svg=os.path.join(HERE, "edgecoil-mark.svg"),
    # Parts not in KiCad's library come from LCSC's own footprints (easyeda2kicad), so they match the
    # part JLC places pad for pad.
    local_libs={"cb": ("lib", "LCSC parts via easyeda2kicad")},
    comment="Generated by hardware/cec-bridge/gen.py - edit the script, not this file",
    # GND isn't a Power net (the pours carry it), nor HDMI_5V (55 mA in use, U6's 0.24-0.35 A limit
    # into a short, which 0.25 mm carries): both have a pin in the HDMI socket's 0.5 mm-pitch row,
    # where a 0.4 mm track can't leave the pad without touching the next one.
    power_nets=("VBUS", "3V3", "IR_A1", "IR_A2", "IR_K"),
    # Courtyards of the LCSC-derived footprints don't enclose their own pads (J2's shell legs, U5's pins), so
    # courtyard overlap can't see a part placed against them; a through-hole pad inside another part's
    # courtyard is the case DRC can catch (round 21: C11 against J2's leg).
    rule_severities={"pth_inside_courtyard": "error"},
    board_hooks=(hdmi_shell,),
    # Built before blocks: the silk and labels break ties in part order, and esd_ground's via goes
    # on U2 by convention. Both kept so the board stays as ordered.
    order_free_silk=False, esd_refs=("U2",),
)


if __name__ == "__main__":
    build(CFG, sys.argv[1:])
