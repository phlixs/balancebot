"""
Center of Mass analysis for BalanceBot Assembly.

Run with the script as an argument — this sets __file__, so the working
directory does not matter:

  Linux (snap):    /snap/bin/freecad.cmd CoM_analysis.py
  Linux (distro):  freecadcmd CoM_analysis.py
  Windows:         "…\\FreeCAD\\bin\\FreeCADCmd.exe" CoM_analysis.py

Piping still works, but leaves __file__ unset and falls back to the
working directory — then run it from CAD_BalanceBot/:

  cat CoM_analysis.py | /snap/bin/freecad.cmd      (Linux)
  Get-Content CoM_analysis.py | FreeCADCmd.exe     (Windows PowerShell)

Reports per-part CoM and the assembly CoM, both volume-weighted
and mass-weighted (with material densities).

"""

import os
from datetime import datetime

import FreeCAD as App

# Verzeichnis dieses Skripts. Beim Aufruf ueber "cat CoM_analysis.py |
# freecad --console" ist __file__ nicht gesetzt — dann gilt das
# Arbeitsverzeichnis, aus dem gestartet wurde (CAD_BalanceBot/).
# Kein absoluter Pfad: Das Repo wird auf Linux und Windows bearbeitet.
BASE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
doc = App.openDocument(BASE + "/BalanceBotAssembly.FCStd")

DENSITY = {
    "botframe":          1.04,
    "NANOMotorCarrier":  1.85,
    "Arduino_Nano33IoT": 1.85,
    "Battery_18650":     2.70,
    "Samsung_INR18650":  2.75,
    "motorhalter_R":     1.04,
    "motorhalter_L":     1.04,
    "N20_motor_R":       4.50,
    "N20_motor_L":       4.50,
    "Wheel_R_Hub":       1.04,
    "Wheel_R_Tire":      1.15,
    "Wheel_L_Hub":       1.04,
    "Wheel_L_Tire":      1.15,
    "CoM_Marker":        0.00,
}

AXLE_Z = -14.7


def get_com(shape):
    if hasattr(shape, "CenterOfMass") and shape.Volume > 0:
        return shape.Volume, shape.CenterOfMass
    sv = 0.0
    sx = sy = sz = 0.0
    for solid in shape.Solids:
        sv += solid.Volume
        c = solid.CenterOfMass
        sx += c.x * solid.Volume
        sy += c.y * solid.Volume
        sz += c.z * solid.Volume
    from FreeCAD import Vector
    if sv == 0:
        return 0.0, Vector(0, 0, 0)
    return sv, Vector(sx / sv, sy / sv, sz / sv)

def run():
    vol_cx = vol_cy = vol_cz = 0.0
    vol_total = 0.0
    mass_cx = mass_cy = mass_cz = 0.0
    mass_total = 0.0
    lines = []
    lines.append("# BalanceBot Center of Mass Analysis")
    lines.append("")
    # astimezone() ohne Argument haengt die Zeitzone der Maschine an. Die
    # ausgegebene Ortszeit bleibt dieselbe — ein Messprotokoll soll die Zeit
    # des Versuchs zeigen, nicht UTC —, der Zeitstempel ist aber nicht mehr
    # zeitzonenlos und damit spaeter eindeutig zuzuordnen.
    erstellt = datetime.now().astimezone()
    lines.append(f"*Created: {erstellt:%d.%m.%Y %H:%M:%S}*  ")
    # Repo-relativ, nicht absolut: Der Herkunftsvermerk soll das Skript
    # nennen, nicht das Arbeitsverzeichnis des Rechners, auf dem es lief.
    lines.append("*Script: CAD_BalanceBot/CoM_analysis.py*")
    lines.append("")
    lines.append("| Part | Vol [mm3] | Mass [g] | CoM X [mm] | CoM Y [mm] | CoM Z [mm] |")
    lines.append("|------|-----------|----------|------------|------------|------------|")
    for obj in doc.Objects:
        v, c = get_com(obj.Shape)
        if v == 0:
            continue
        rho = DENSITY.get(obj.Name, 1.0)
        m = v * rho / 1000.0
        vol_cx += c.x * v
        vol_cy += c.y * v
        vol_cz += c.z * v
        vol_total += v
        mass_cx += c.x * m
        mass_cy += c.y * m
        mass_cz += c.z * m
        mass_total += m
        lines.append(f"| {obj.Name} | {v:.1f} | {m:.2f} | {c.x:.2f} | {c.y:.2f} | {c.z:.2f} |")
    vol_cx /= vol_total
    vol_cy /= vol_total
    vol_cz /= vol_total
    mass_cx /= mass_total
    mass_cy /= mass_total
    mass_cz /= mass_total
    lines.append(f"| **TOTAL** | **{vol_total:.1f}** | **{mass_total:.2f}** | | | |")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append("| Metric | X [mm] | Y [mm] | Z [mm] |")
    lines.append("|--------|--------|--------|--------|")
    lines.append(f"| CoM (volume-weighted) | {vol_cx:.2f} | {vol_cy:.2f} | {vol_cz:.2f} |")
    lines.append(f"| CoM (mass-weighted) | {mass_cx:.2f} | {mass_cy:.2f} | {mass_cz:.2f} |")
    lines.append("")
    lines.append(f"- Wheel axle Z = {AXLE_Z:.1f} mm")
    lines.append(f"- CoM height above axle: **{mass_cz - AXLE_Z:.2f} mm** (mass-weighted)")
    lines.append(f"- CoM Y offset from axle: **{mass_cy:.2f} mm** (positive = forward)")
    lines.append("")
    lines.append("The coordinate origin is below the botframe base plate. Check the CAD-Assembly-File in FreeCAD to verify")
    lines.append("")
    lines.append("For balancing: the CoM should be ABOVE the wheel axle (high Z) and centered on the axle in Y.")
    lines.append("")
    if mass_cz > AXLE_Z:
        lines.append("> CoM is **ABOVE** the axle (inverted pendulum, balanceable)")
    else:
        lines.append("> CoM is **BELOW** the axle (stable but not a balance bot config)")
    output = "\n".join(lines) + "\n"
    print(output)
    date_str = f"{erstellt:%Y%m%d}"
    out_path = BASE + f"/CoM_analysis_results_{date_str}.md"
    # encoding und newline explizit: Ohne sie schriebe Python unter Windows
    # in der Locale-Kodierung und mit CRLF, unter Linux in UTF-8 und mit LF —
    # dieselbe Auswertung ergaebe je nach Maschine eine andere Datei.
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(output)
    print(f"Results written to: {out_path}")
    App.closeDocument(doc.Name)

run()
