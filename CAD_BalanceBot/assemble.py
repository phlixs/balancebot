"""
BalanceBot Assembly Script — FreeCAD 1.1
Run with:  cat assemble.py | /snap/bin/freecad --console

Placements last synced from BalanceBotAssembly.FCStd (manually adjusted in GUI).

NOTE — two parts use procedural geometry (replace when native files are converted):
  Wheel_R / Wheel_L  : built from Pololu 90mm wheel published specs (dia=90, w=10mm)
                       To use the real DWG: install libredwg-tools (sudo apt install
                       libredwg-tools), then run  dwg2dxf "Pololu 90mm Wheel.dwg"
                       and import the resulting DXF into FreeCAD → export to STEP.
  Samsung_INR18650   : loaded from Samsung INR18650-25R.stp (dia≈19.98mm, L=65.85mm)
"""

import math
import os

import FreeCAD as App
import Part

# Verzeichnis dieses Skripts. Beim Aufruf ueber "cat assemble.py |
# freecad --console" ist __file__ nicht gesetzt — dann gilt das
# Arbeitsverzeichnis, aus dem gestartet wurde (CAD_BalanceBot/).
# Kein absoluter Pfad: Das Repo wird auf Linux und Windows bearbeitet.
BASE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
OUT  = BASE + "/BalanceBotAssembly.FCStd"

Vec = App.Vector
Rot = App.Rotation
Plc = App.Placement

def load_body(path):
    d = App.openDocument(path)
    s = d.getObject("Body").Shape.copy()
    App.closeDocument(d.Name)
    return s

def load_step(path):
    s = Part.Shape()
    s.read(path)
    return s

def _rot_z(shape, deg):
    mat = App.Matrix()
    mat.rotateZ(math.radians(deg))
    return shape.transformGeometry(mat)

def make_wheel_hub():
    RIM_OR = 37.0; RIM_IR = 34.0; HUB_R = 13.0
    SPOKE_W = 4.0; SPOKE_H = 4.0; SPOKE_Z = 3.0
    rim = Part.makeCylinder(RIM_OR, 10.0).cut(Part.makeCylinder(RIM_IR, 10.0))
    hub_plate = Part.makeCylinder(HUB_R, SPOKE_H, Vec(0, 0, SPOKE_Z))
    hw = SPOKE_W / 2.0
    box = Part.makeBox(RIM_IR - HUB_R, SPOKE_W, SPOKE_H, Vec(HUB_R, -hw, SPOKE_Z))
    ch = Part.makeCylinder(hw, SPOKE_H, Vec(HUB_R, 0.0, SPOKE_Z))
    cr = Part.makeCylinder(hw, SPOKE_H, Vec(RIM_IR, 0.0, SPOKE_Z))
    spoke0 = box.fuse(ch).fuse(cr)
    spokes = spoke0.copy()
    spokes = spokes.fuse(_rot_z(spoke0, 60.0))
    spokes = spokes.fuse(_rot_z(spoke0, 120.0))
    spokes = spokes.fuse(_rot_z(spoke0, 180.0))
    spokes = spokes.fuse(_rot_z(spoke0, 240.0))
    spokes = spokes.fuse(_rot_z(spoke0, 300.0))
    body = rim.fuse(hub_plate).fuse(spokes)
    body = body.cut(Part.makeCylinder(1.5, SPOKE_H + 2.0, Vec(0, 0, SPOKE_Z - 1.0)))
    body = body.cut(Part.makeBox(4.0, 0.6, SPOKE_H + 2.0, Vec(-2.0, 1.0, SPOKE_Z - 1.0)))
    hz = SPOKE_Z - 0.5; hh = SPOKE_H + 1.0
    body = body.cut(Part.makeCylinder(1.25, hh, Vec(6.35, 0.0, hz)))
    body = body.cut(Part.makeCylinder(1.25, hh, Vec(-6.35, 0.0, hz)))
    r2 = 9.55 * math.sqrt(0.5)
    body = body.cut(Part.makeCylinder(1.25, hh, Vec(r2, r2, hz)))
    body = body.cut(Part.makeCylinder(1.25, hh, Vec(-r2, r2, hz)))
    body = body.cut(Part.makeCylinder(1.25, hh, Vec(-r2, -r2, hz)))
    body = body.cut(Part.makeCylinder(1.25, hh, Vec(r2, -r2, hz)))
    return body

def make_wheel_tire():
    shell = Part.makeCylinder(45.0, 10.0).cut(Part.makeCylinder(37.0, 10.0))
    sp = 10.0 / 12.0
    shell = shell.cut(Part.makeCylinder(45.0, 0.6, Vec(0,0,sp*0.5-0.3)).cut(Part.makeCylinder(44.5, 0.6, Vec(0,0,sp*0.5-0.3))))
    shell = shell.cut(Part.makeCylinder(45.0, 0.6, Vec(0,0,sp*1.5-0.3)).cut(Part.makeCylinder(44.5, 0.6, Vec(0,0,sp*1.5-0.3))))
    shell = shell.cut(Part.makeCylinder(45.0, 0.6, Vec(0,0,sp*2.5-0.3)).cut(Part.makeCylinder(44.5, 0.6, Vec(0,0,sp*2.5-0.3))))
    shell = shell.cut(Part.makeCylinder(45.0, 0.6, Vec(0,0,sp*3.5-0.3)).cut(Part.makeCylinder(44.5, 0.6, Vec(0,0,sp*3.5-0.3))))
    shell = shell.cut(Part.makeCylinder(45.0, 0.6, Vec(0,0,sp*4.5-0.3)).cut(Part.makeCylinder(44.5, 0.6, Vec(0,0,sp*4.5-0.3))))
    shell = shell.cut(Part.makeCylinder(45.0, 0.6, Vec(0,0,sp*5.5-0.3)).cut(Part.makeCylinder(44.5, 0.6, Vec(0,0,sp*5.5-0.3))))
    shell = shell.cut(Part.makeCylinder(45.0, 0.6, Vec(0,0,sp*6.5-0.3)).cut(Part.makeCylinder(44.5, 0.6, Vec(0,0,sp*6.5-0.3))))
    shell = shell.cut(Part.makeCylinder(45.0, 0.6, Vec(0,0,sp*7.5-0.3)).cut(Part.makeCylinder(44.5, 0.6, Vec(0,0,sp*7.5-0.3))))
    shell = shell.cut(Part.makeCylinder(45.0, 0.6, Vec(0,0,sp*8.5-0.3)).cut(Part.makeCylinder(44.5, 0.6, Vec(0,0,sp*8.5-0.3))))
    shell = shell.cut(Part.makeCylinder(45.0, 0.6, Vec(0,0,sp*9.5-0.3)).cut(Part.makeCylinder(44.5, 0.6, Vec(0,0,sp*9.5-0.3))))
    shell = shell.cut(Part.makeCylinder(45.0, 0.6, Vec(0,0,sp*10.5-0.3)).cut(Part.makeCylinder(44.5, 0.6, Vec(0,0,sp*10.5-0.3))))
    shell = shell.cut(Part.makeCylinder(45.0, 0.6, Vec(0,0,sp*11.5-0.3)).cut(Part.makeCylinder(44.5, 0.6, Vec(0,0,sp*11.5-0.3))))
    return shell


def add_part(doc, name, shape, color, pos=(0,0,0), rot=None):
    obj = doc.addObject("Part::Feature", name)
    obj.Shape = shape
    try:
        obj.ViewObject.ShapeColor = color
    except Exception:
        pass  # ViewObject not available in headless mode
    if rot is None:
        obj.Placement = Plc(Vec(*pos), Rot(0, 0, 0, 1))
    else:
        obj.Placement = Plc(Vec(*pos), rot)
    return obj

doc = App.newDocument("BalanceBotAssembly")

# ── 1. Bot Frame ──────────────────────────────────────────────────────────────
# Body centered at world origin. Top face Z=+2, bottom Z=-30. Unchanged.
add_part(doc, "botframe",
         load_body(BASE + "/botframe.FCStd"),
         color=(0.80, 0.80, 0.80),
         pos=(0.0, 0.0, 0.0))

# ── 2. NANO Motor Carrier PCB ─────────────────────────────────────────────────
# Exact hole alignment (< 0.25 mm residual). Unchanged.
# PCB bottom face (local Z=-1.63) on carrier top (world Z=+2.0) → dz=3.63
add_part(doc, "NANOMotorCarrier",
         load_step(BASE + "/STEP_[No Variations] for Public_NANOMotorCarrier.PcbDoc.step"),
         color=(0.10, 0.50, 0.10),
         pos=(-24.965, -39.885, 3.63))

# ── 3. Arduino Nano 33 IoT ────────────────────────────────────────────────────
# 180° around axis (0, 1, 1)/√2  — manually positioned in GUI.
# pos Z raised to 12.53 (was 4.53); rotation updated to match GUI result.
add_part(doc, "Arduino_Nano33IoT",
         load_step(BASE + "/Arduino Nano 33 IoT.stp"),
         color=(0.00, 0.30, 0.80),
         pos=(0.0, 0.0, 12.53),
         rot=Rot(0.000000, 0.707107, 0.707107, 0.000000))

# ── 4. 18650 Battery ─────────────────────────────────────────────────────────
# 180° around axis (1, 1, 0)/√2  — manually positioned in GUI.
# Z raised from -26.2 → -4.2 (sits higher in pocket).
add_part(doc, "Battery_18650",
         load_step(BASE + "/User Library-18650 Full.STEP"),
         color=(0.70, 0.70, 0.10),
         pos=(0.0, -27.8, -4.2),
         rot=Rot(0.707107, 0.707107, 0.000000, 0.000000))

# ── 5. Motor Holder RIGHT ─────────────────────────────────────────────────────
# 180° around X axis — manually adjusted in GUI.
# Translated to (-10, 0, -30).
add_part(doc, "motorhalter_R",
         load_body(BASE + "/motorhalter_lose.FCStd"),
         color=(0.90, 0.50, 0.10),
         pos=(-10.0, 0.0, -30.0),
         rot=Rot(1.000000, 0.000000, 0.000000, 0.000000))

# ── 6. Motor Holder LEFT ──────────────────────────────────────────────────────
# 180° around Z axis — manually adjusted in GUI.
# Translated to (10, 0, 0).
add_part(doc, "motorhalter_L",
         load_body(BASE + "/motorhalter_lose.FCStd"),
         color=(0.90, 0.50, 0.10),
         pos=(10.0, 0.0, 0.0),
         rot=Rot(0.000000, 0.000000, 1.000000, 0.000000))

# ── 7. N20 Motor RIGHT (shaft → +X, no rotation) ─────────────────────────────
# No rotation. Position manually refined in GUI.
add_part(doc, "N20_motor_R",
         load_step(BASE + "/N20 Mini Micro Metall Gear Motor DC 3-6-12V v1.step"),
         color=(0.25, 0.25, 0.25),
         pos=(36.9, -0.6, -14.7))

# ── 8. N20 Motor LEFT (shaft → -X, 180° around Z) ────────────────────────────
# 180° around Z. Position manually refined in GUI.
add_part(doc, "N20_motor_L",
         load_step(BASE + "/N20 Mini Micro Metall Gear Motor DC 3-6-12V v1.step"),
         color=(0.25, 0.25, 0.25),
         pos=(-37.9, -0.4, -14.7),
         rot=Rot(0.000000, 0.000000, 1.000000, 0.000000))

# ── 9. Wheels (Pololu 90×10mm, product #1439) ────────────────────────────────
# Loaded from Pololu_Wheel_90x10.FCStd (run create_wheel.py to regenerate).
# Wheel geometry: axis along Z, inner face at Z=0, outer face at Z=10,
#                 bore: Z=2..8 (6 mm engagement depth).
#
# Motor shaft axis (verified from N20 STEP: shaft at local Y=0, Z=0):
#   Right motor: shaft axis world Y=-0.6, Z=-14.7 — tip at world X=+55.9
#   Left  motor: shaft axis world Y=-0.4, Z=-14.7 — tip at world X=-56.9
#
# Placement strategy: bore outer end (local Z=8) coincides with shaft tip.
#   Ry(+90°):  local Z → world +X  →  bore outer end at Px+8  → Px = 55.9 - 8 = 47.9
#   Ry(-90°):  local Z → world -X  →  bore outer end at Px-8  → Px = -56.9 + 8 = -48.9
#
# Right: Px=47.9  (wheel spans X [47.9, 57.9], bore engages X [49.9, 55.9])
# Left:  Px=-48.9 (wheel spans X [-58.9, -48.9], bore engages X [-56.9, -50.9])
rot_ry_pos90 = Rot(Vec(0, 1, 0),  90)   # Z → +X
rot_ry_neg90 = Rot(Vec(0, 1, 0), -90)   # Z → -X

# Right wheel — hub and tire at identical placement
add_part(doc, "Wheel_R_Hub",  make_wheel_hub(),  (0.95, 0.95, 0.95),
         pos=(47.9, -0.6, -14.7), rot=rot_ry_pos90)
add_part(doc, "Wheel_R_Tire", make_wheel_tire(), (0.10, 0.10, 0.10),
         pos=(47.9, -0.6, -14.7), rot=rot_ry_pos90)

# Left wheel — hub and tire at identical placement
add_part(doc, "Wheel_L_Hub",  make_wheel_hub(),  (0.95, 0.95, 0.95),
         pos=(-48.9, -0.4, -14.7), rot=rot_ry_neg90)
add_part(doc, "Wheel_L_Tire", make_wheel_tire(), (0.10, 0.10, 0.10),
         pos=(-48.9, -0.4, -14.7), rot=rot_ry_neg90)

# ── 10. Samsung INR18650-25R battery cell ─────────────────────────────────────
# Loaded from Samsung INR18650-25R.stp
# Native bbox: long axis = Y (65.85mm), diameter = 19.98mm, centred at X=0, Z=0
#
# Placed INSIDE the Battery_18650 holder.
# Holder rotation (180° around (1,1,0)/√2) maps native-X→world-Y, so holder long
# axis is world-Y. Battery native Y is also world-Y → no rotation needed.
#
# Holder world centre: X=0, Y=0, Z=-13.15
# Battery native centre: X=0, Y=32.925, Z=0
#   → Px = 0,  Py = 0 - 32.925 = -32.925,  Pz = -13.15
#
# Clearances inside holder: X ±0.41mm, Y ±5.88mm (end-stop), Z ±2.76mm  ✓
add_part(doc, "Samsung_INR18650",
         load_step(BASE + "/Samsung INR18650-25R.stp"),
         color=(0.20, 0.20, 0.60),              # dark blue cell wrap
         pos=(0.0, -32.925, -13.15))

# ── 11. Center of Mass marker ─────────────────────────────────────────────────
DENSITY = {
    "botframe": 1.04, "NANOMotorCarrier": 1.85, "Arduino_Nano33IoT": 1.85,
    "Battery_18650": 2.70, "Samsung_INR18650": 2.75,
    "motorhalter_R": 1.04, "motorhalter_L": 1.04,
    "N20_motor_R": 4.50, "N20_motor_L": 4.50,
    "Wheel_R_Hub": 1.04, "Wheel_R_Tire": 1.15,
    "Wheel_L_Hub": 1.04, "Wheel_L_Tire": 1.15,
}

def _get_com(shape):
    if hasattr(shape, "CenterOfMass"):
        return shape.Volume, shape.CenterOfMass
    sv = 0.0; sx = sy = sz = 0.0
    for solid in shape.Solids:
        sv += solid.Volume; c = solid.CenterOfMass
        sx += c.x * solid.Volume; sy += c.y * solid.Volume; sz += c.z * solid.Volume
    return sv, Vec(sx / sv, sy / sv, sz / sv)

mcx = mcy = mcz = 0.0; mt = 0.0
for obj in doc.Objects:
    v, c = _get_com(obj.Shape)
    rho = DENSITY.get(obj.Name, 1.0)
    m = v * rho / 1000.0
    mcx += c.x * m; mcy += c.y * m; mcz += c.z * m; mt += m

com = Vec(mcx / mt, mcy / mt, mcz / mt)
print("CoM (mass-weighted): (%.2f, %.2f, %.2f)  total=%.1f g" % (com.x, com.y, com.z, mt))

com_sphere = Part.makeSphere(2.0, com)
com_cross_x = Part.makeCylinder(0.4, 20.0, Vec(com.x - 10, com.y, com.z), Vec(1, 0, 0))
com_cross_y = Part.makeCylinder(0.4, 20.0, Vec(com.x, com.y - 10, com.z), Vec(0, 1, 0))
com_cross_z = Part.makeCylinder(0.4, 20.0, Vec(com.x, com.y, com.z - 10), Vec(0, 0, 1))
com_marker = com_sphere.fuse(com_cross_x).fuse(com_cross_y).fuse(com_cross_z)
add_part(doc, "CoM_Marker", com_marker, (1.0, 0.0, 0.0), pos=(0, 0, 0))

# ── Save ──────────────────────────────────────────────────────────────────────
doc.recompute()
doc.saveAs(OUT)
print("Assembly saved: " + OUT)
