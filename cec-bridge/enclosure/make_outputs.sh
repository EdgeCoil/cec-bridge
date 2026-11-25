#!/bin/sh
set -e
cd "$(dirname "$0")"
mkdir -p previews

# 1. Clip board STL for section preview ghosts (OpenSCAD cannot CGAL-intersect non-manifold STEP/STL exports)
python3 - <<'EOF'
import math

def clip_stl(in_path, out_path, xcut):
    tris, cur = [], []
    for line in open(in_path):
        s = line.split()
        if s and s[0] == "vertex":
            cur.append((float(s[1]), float(s[2]), float(s[3])))
            if len(cur) == 3:
                tris.append(cur); cur = []
    out = []
    for t in tris:
        inside = [p for p in t if p[0] <= xcut]
        outside = [p for p in t if p[0] > xcut]
        if len(inside) == 3:
            out.append(t)
        elif len(inside) == 1:
            p0 = inside[0]
            p1 = interp(p0, outside[0], xcut)
            p2 = interp(p0, outside[1], xcut)
            out.append([p0, p1, p2])
        elif len(inside) == 2:
            p0, p1 = inside
            q = outside[0]
            a = interp(p0, q, xcut)
            b = interp(p1, q, xcut)
            out.append([p0, p1, b])
            out.append([p0, b, a])
    with open(out_path, "w") as f:
        f.write("solid clipped\n")
        for a, b, c in out:
            ux, uy, uz = b[0]-a[0], b[1]-a[1], b[2]-a[2]
            vx, vy, vz = c[0]-a[0], c[1]-a[1], c[2]-a[2]
            nx, ny, nz = uy*vz - uz*vy, uz*vx - ux*vz, ux*vy - uy*vx
            n = math.sqrt(nx*nx + ny*ny + nz*nz) or 1.0
            f.write(f" facet normal {nx/n:.6f} {ny/n:.6f} {nz/n:.6f}\n  outer loop\n")
            for p in (a, b, c):
                f.write(f"   vertex {p[0]:.6f} {p[1]:.6f} {p[2]:.6f}\n")
            f.write("  endloop\n endfacet\n")
        f.write("endsolid clipped\n")

def interp(a, b, xcut):
    t = (xcut - a[0]) / (b[0] - a[0])
    return (xcut, a[1] + t*(b[1]-a[1]), a[2] + t*(b[2]-a[2]))

clip_stl("board-model/cec-bridge-assembled.stl", "previews/ghost_x_le_10.stl", 10.0)
clip_stl("board-model/cec-bridge-assembled.stl", "previews/ghost_x_le_14.stl", 14.0)
EOF

# 2. Export print-oriented STLs
openscad -o base.stl -D 'part="base_print"' enclosure.scad
openscad -o lid.stl  -D 'part="lid_print"'  enclosure.scad

# 3. Verify zero volumetric overlap with keep-outs, closed lid, and all insertion-path poses (no || true; missing/empty = FAIL)
rm -f /tmp/lko_check.stl /tmp/bko_check.stl /tmp/base_lid_overlap.stl /tmp/ins_*.stl
openscad -o /tmp/lko_check.stl        -D 'part="lid_keepout_check"'       enclosure.scad
openscad -o /tmp/bko_check.stl        -D 'part="base_keepout_check"'      enclosure.scad
openscad -o /tmp/base_lid_overlap.stl -D 'part="base_lid_overlap_check"' enclosure.scad

POSES="1.4:10 1.4:5 1.4:2 1.4:1 1.4:0.5 1.4:0 1.0:0 0.6:0 0.2:0 0:0"
for pose in $POSES; do
  dx=${pose%:*}
  dz=${pose#*:}
  openscad -o "/tmp/ins_${dx}_${dz}.stl" -D 'part="insertion_check"' -D "lid_x_shift=$dx" -D "lid_z_shift=$dz" enclosure.scad
done

python3 - <<'EOF'
import os, sys

def stl_stats(path):
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return None, 0
    vol = 0.0
    tris = 0
    tri = []
    for line in open(path):
        s = line.split()
        if s and s[0] == "vertex":
            tri.append((float(s[1]), float(s[2]), float(s[3])))
            if len(tri) == 3:
                a, b, c = tri
                vol += (a[0]*(b[1]*c[2]-b[2]*c[1]) - a[1]*(b[0]*c[2]-b[2]*c[0]) + a[2]*(b[0]*c[1]-b[1]*c[0])) / 6.0
                tris += 1
                tri = []
    return abs(vol), tris

checks = [
    ("lid_keepout_check", "/tmp/lko_check.stl"),
    ("base_keepout_check", "/tmp/bko_check.stl"),
    ("base_lid_overlap_check", "/tmp/base_lid_overlap.stl"),
]
for pose in "1.4:10 1.4:5 1.4:2 1.4:1 1.4:0.5 1.4:0 1.0:0 0.6:0 0.2:0 0:0".split():
    dx, dz = pose.split(":")
    checks.append((f"insertion_check(dx={dx},dz={dz})", f"/tmp/ins_{dx}_{dz}.stl"))

failed = False
for label, path in checks:
    v, tris = stl_stats(path)
    if v is None or tris == 0:
        print(f"FAIL: {label} missing or empty STL ({path})", file=sys.stderr)
        failed = True
        continue
    excess = max(0.0, v - 0.001)  # subtract 0.001 mm^3 reference voxel
    print(f"CHECK {label}: volume = {excess:.4f} mm^3 (raw={v:.4f}, tris={tris})")
    if v >= 0.01:
        print(f"FAIL: {label} raw volume {v:.4f} >= 0.01 mm^3", file=sys.stderr)
        failed = True
if failed:
    sys.exit(1)
EOF

# 4. Render PNG previews (must run under xvfb-run)
xvfb-run -a openscad -o previews/assembly.png        --imgsize=1100,850 --viewall --autocenter -D 'part="assembly"' -D 'lid_lift=8' enclosure.scad
xvfb-run -a openscad -o previews/base_print.png      --imgsize=1000,750 --viewall --autocenter -D 'part="base_print"' enclosure.scad
xvfb-run -a openscad -o previews/lid_print.png       --imgsize=1000,750 --viewall --autocenter -D 'part="lid_print"' enclosure.scad
xvfb-run -a openscad -o previews/section_hdmi.png    --imgsize=1100,750 --camera=10,-24,7.5,82,0,78,88 --projection=o -D 'part="section_hdmi"' enclosure.scad
xvfb-run -a openscad -o previews/section_antenna.png --imgsize=1100,750 --camera=14,-18,7.5,82,0,78,88 --projection=o -D 'part="section_antenna"' enclosure.scad
xvfb-run -a openscad -o previews/section_hook.png    --imgsize=900,700  --camera=41,-9,6.5,85,0,20,26  --projection=o -D 'part="section_hook"' enclosure.scad
xvfb-run -a openscad -o previews/top_antenna.png     --imgsize=900,900  --camera=20,-20,120,20,-20,0 --viewall -D 'part="top_antenna"' enclosure.scad

ls -lh base.stl lid.stl previews/*.png
