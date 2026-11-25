#!/bin/sh
# Rebuild the assembled-board models from the KiCad board (they are gitignored: 16 MB, derived).
set -e
cd "$(dirname "$0")"
export KICAD9_3DMODEL_DIR="${KICAD9_3DMODEL_DIR:-$HOME/.local/share/kicad-3d/usr/share/kicad/3dmodels}"
kicad-cli pcb export step --subst-models -f -o cec-bridge-assembled.step ../../cec-bridge/cec-bridge.kicad_pcb
kicad-cli pcb export stl  --subst-models -f -o cec-bridge-assembled.stl  ../../cec-bridge/cec-bridge.kicad_pcb
