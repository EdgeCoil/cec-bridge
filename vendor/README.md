# Vendored: edgecoil_pcb

The shared board pipeline, copied from [EdgeCoil/edgecoil-pcb](https://github.com/EdgeCoil/edgecoil-pcb)
at commit `55e7265` (MIT). `gen.py` and `route.py` import it from here. Don't edit it here: change
edgecoil-pcb, copy the package over, and prove the board unchanged with
`PYTHONPATH=vendor python3 -m edgecoil_pcb.canon committed.kicad_pcb rebuilt.kicad_pcb`.
