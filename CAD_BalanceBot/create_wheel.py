"""
Pololu Wheel 90×10mm — product #1439
Creates Pololu_Wheel_90x10.FCStd with two Part::Feature objects:
  Wheel_Hub  — white ABS, 6 spokes, shaft bore, mounting holes
  Wheel_Tire — black silicone, horizontal treads

Run with the script as an argument — this sets __file__, so the working
directory does not matter:

  Linux (snap):    /snap/bin/freecad.cmd create_wheel.py
  Linux (distro):  freecadcmd create_wheel.py
  Windows:         "…\\FreeCAD\\bin\\FreeCADCmd.exe" create_wheel.py

Piping still works, but leaves __file__ unset and falls back to the
working directory — then run it from CAD_BalanceBot/.

WARNING: overwrites Pololu_Wheel_90x10.FCStd, which is version-controlled.

Dimensions (from pololu.com/product/1439 + image analysis):
  Outer diameter      : 90 mm  (tire OD)
  Width               : 10 mm
  Tire radial depth   : 8 mm   → rim seat OD = 74 mm (R=37)
  Rim ring            : OD=74 mm (R=37), ID=68 mm (R=34), full 10 mm deep
  Hub plate           : R=13 mm, 4 mm axial depth, centred in wheel (Z=3..7)
  Spokes              : 6×, 60° apart, 4 mm wide (tangential), 4 mm deep (axial)
                        radial extent R=13→34, centred at Z=3..7
                        stadium profile (box + semicircular caps) for rounded ends
  Shaft bore          : 3 mm D-shaft (round bore R=1.5 — press fit)
  D-flat              : 0.5 mm cut at Y=+1.0
  Mounting holes      : 2× at r=6.35 mm (0°/180°) + 4× at r=9.55 mm (45°/135°/225°/315°)
                        all Ø2.5 mm, through full hub depth (Z=3..7, ±0.5 mm clearance)
  Tread grooves       : 12 shallow grooves (0.5 mm deep, 0.6 mm wide) on tire OD
"""

import math
import os

import FreeCAD as App
import Part

# Verzeichnis dieses Skripts. Beim Aufruf ueber "cat create_wheel.py |
# freecad --console" ist __file__ nicht gesetzt — dann gilt das
# Arbeitsverzeichnis, aus dem gestartet wurde (CAD_BalanceBot/).
# Kein absoluter Pfad: Das Repo wird auf Linux und Windows bearbeitet.
BASE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
Vec  = App.Vector

# Geometry constants
SPOKE_W  = 4.0    # tangential width of each spoke
SPOKE_H  = 4.0    # axial depth of spoke (Z direction)
SPOKE_Z  = 3.0    # Z start of spokes/hub plate (centred: Z=[3,7])
HUB_R    = 13.0   # hub plate outer radius
RIM_IR   = 34.0   # rim ring inner radius
RIM_OR   = 37.0   # rim ring outer radius (seats tire)
SPOKE_LEN = RIM_IR - HUB_R   # radial length = 21 mm


def rot_z(shape, deg):
    """Return a copy of shape rotated deg° around Z through origin."""
    mat = App.Matrix()
    mat.rotateZ(math.radians(deg))
    return shape.transformGeometry(mat)


def make_stadium_spoke():
    """
    One spoke: stadium cross-section in XY, extruded SPOKE_H in Z.
    Axis along +X from HUB_R to RIM_IR.
    Stadium = box + two semicircular end caps (half-cylinder each).
    This naturally rounds the spoke at both the hub end and the rim end.
    """
    half_w = SPOKE_W / 2.0   # = 2.0 mm

    # Central rectangular body
    box = Part.makeBox(SPOKE_LEN, SPOKE_W, SPOKE_H,
                       Vec(HUB_R, -half_w, SPOKE_Z))

    # Rounded cap at hub end (R=half_w, centred on X=HUB_R)
    cap_hub  = Part.makeCylinder(half_w, SPOKE_H, Vec(HUB_R,  0.0, SPOKE_Z))

    # Rounded cap at rim end (R=half_w, centred on X=RIM_IR)
    cap_rim  = Part.makeCylinder(half_w, SPOKE_H, Vec(RIM_IR, 0.0, SPOKE_Z))

    return box.fuse(cap_hub).fuse(cap_rim)


def make_hub():
    # ── Rim ring: seats the tire  (R=34 inner, R=37 outer, full 10 mm) ──────────
    rim = Part.makeCylinder(RIM_OR, 10.0).cut(Part.makeCylinder(RIM_IR, 10.0))

    # ── Hub plate: thin disc R=13, 4 mm axial depth centred (Z=3..7) ─────────────
    hub_plate = Part.makeCylinder(HUB_R, SPOKE_H, Vec(0, 0, SPOKE_Z))

    # ── 6 spokes: stadium profile, 60° apart ─────────────────────────────────────
    spoke_0 = make_stadium_spoke()
    spokes = spoke_0.copy()
    for i in range(1, 6):
        spokes = spokes.fuse(rot_z(spoke_0, i * 60.0))

    body = rim.fuse(hub_plate).fuse(spokes)

    # ── Shaft bore: 3 mm D-shaft through full hub plate depth (+safety) ──────────
    bore = Part.makeCylinder(1.5, SPOKE_H + 2.0, Vec(0, 0, SPOKE_Z - 1.0))
    body = body.cut(bore)

    # D-flat: 0.5 mm sliver at Y=+1.0 (standard 3 mm D-shaft)
    d_flat = Part.makeBox(4.0, 0.6, SPOKE_H + 2.0,
                          Vec(-2.0, 1.0, SPOKE_Z - 1.0))
    body = body.cut(d_flat)

    # ── Mounting holes (Ø2.5 mm, through hub plate, +0.5 mm each side) ───────────
    hole_z0 = SPOKE_Z - 0.5
    hole_h  = SPOKE_H + 1.0
    for angle in [0.0, 180.0]:
        x = 6.35 * math.cos(math.radians(angle))
        y = 6.35 * math.sin(math.radians(angle))
        body = body.cut(Part.makeCylinder(1.25, hole_h, Vec(x, y, hole_z0)))
    for angle in [45.0, 135.0, 225.0, 315.0]:
        x = 9.55 * math.cos(math.radians(angle))
        y = 9.55 * math.sin(math.radians(angle))
        body = body.cut(Part.makeCylinder(1.25, hole_h, Vec(x, y, hole_z0)))

    return body


# ── Tire (black silicone) ──────────────────────────────────────────────────────

def make_tire():
    # Solid shell: OD=90 mm (R=45), ID=74 mm (R=37), H=10 mm
    shell = Part.makeCylinder(45.0, 10.0).cut(Part.makeCylinder(RIM_OR, 10.0))

    # 12 horizontal tread grooves around circumference:
    # each is a toroidal slot 0.5 mm deep × 0.6 mm wide
    groove_depth = 0.5
    groove_w     = 0.6
    n_grooves    = 12
    spacing = 10.0 / n_grooves
    for i in range(n_grooves):
        z0 = (i + 0.5) * spacing - groove_w / 2
        outer = Part.makeCylinder(45.0, groove_w, Vec(0, 0, z0))
        inner = Part.makeCylinder(45.0 - groove_depth, groove_w, Vec(0, 0, z0))
        shell = shell.cut(outer.cut(inner))

    return shell


# ── Build and save ─────────────────────────────────────────────────────────────

doc = App.newDocument("Pololu_Wheel_90x10")

hub_obj = doc.addObject("Part::Feature", "Wheel_Hub")
hub_obj.Shape = make_hub()
try:
    hub_obj.ViewObject.ShapeColor = (0.95, 0.95, 0.95)
except Exception:
    pass

tire_obj = doc.addObject("Part::Feature", "Wheel_Tire")
tire_obj.Shape = make_tire()
try:
    tire_obj.ViewObject.ShapeColor = (0.10, 0.10, 0.10)
except Exception:
    pass

doc.recompute()
out = BASE + "/Pololu_Wheel_90x10.FCStd"
doc.saveAs(out)

bb_hub  = hub_obj.Shape.BoundBox
bb_tire = tire_obj.Shape.BoundBox
print("Wheel saved:", out)
print(f"Hub  bbox: X[{bb_hub.XMin:.1f},{bb_hub.XMax:.1f}] "
      f"Y[{bb_hub.YMin:.1f},{bb_hub.YMax:.1f}] "
      f"Z[{bb_hub.ZMin:.1f},{bb_hub.ZMax:.1f}]")
print(f"Tire bbox: X[{bb_tire.XMin:.1f},{bb_tire.XMax:.1f}] "
      f"Y[{bb_tire.YMin:.1f},{bb_tire.YMax:.1f}] "
      f"Z[{bb_tire.ZMin:.1f},{bb_tire.ZMax:.1f}]")
