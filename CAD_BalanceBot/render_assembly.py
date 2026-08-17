"""
BalanceBot Assembly — Three.js HTML Export

Tesselliert alle Bauteile aus BalanceBotAssembly.FCStd und bettet sie als
BufferGeometry in eine HTML-Datei ein. Der Browser zeigt eine automatische
Kamera-Umfahrt; Doppelklick pausiert die Autorotation, Ziehen mit der Maus
dreht manuell, das Mausrad zoomt.

Die erzeugte Datei enthaelt nur die Geometrie. three.js selbst laedt sie von
einem CDN, sie braucht dafuer also eine Netzverbindung. Mit ueber 60 MB ist
sie zu gross fuer das Repo und wird von .gitignore (*.html) ausgeschlossen —
Master ist dieses Skript, nicht sein Produkt.

Aufruf mit dem Skript als Argument; das setzt __file__, womit das
Arbeitsverzeichnis keine Rolle spielt:

  Linux (snap):    /snap/bin/freecad.cmd render_assembly.py
  Linux (distro):  freecadcmd render_assembly.py
  Windows:         "…\\FreeCAD\\bin\\FreeCADCmd.exe" render_assembly.py

Ueber eine Pipe funktioniert es auch, dann bleibt __file__ ungesetzt und es
gilt das Arbeitsverzeichnis — in diesem Fall aus CAD_BalanceBot/ starten.
"""

import json
import math
import os

import FreeCAD as App

# Verzeichnis dieses Skripts. Kein absoluter Pfad: Das Repo wird auf Linux
# und Windows bearbeitet, und ein Pfad einer einzelnen Maschine macht das
# Skript fuer jede andere unbrauchbar.
BASE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
ASSEMBLY = BASE + "/BalanceBotAssembly.FCStd"
HTML_OUT = BASE + "/balancebot_assembly.html"

os.makedirs(os.path.dirname(HTML_OUT), exist_ok=True)

# ---- Farben je Bauteiltyp (CSS-Hex) ----
def get_color(name):
    n = name.lower()
    if "tire" in n:
        return "#282828"        # black rubber
    if "hub" in n:
        return "#d8d8d8"        # light grey plastic
    if "n20" in n or ("motor" in n and "carrier" not in n and "halter" not in n):
        return "#404040"        # dark grey metal
    if "motorhalter" in n:
        return "#e08020"        # orange 3D-print
    if "carrier" in n:
        return "#1a8c1a"        # green PCB
    if "arduino" in n:
        return "#0060c0"        # blue PCB
    if "botframe" in n:
        return "#c0c0c0"        # light grey frame
    if "battery" in n:
        return "#b0b0b0"        # aluminium holder
    if "samsung" in n or "18650" in n:
        return "#2a2a60"        # dark blue cell
    if "com" in n or "marker" in n:
        return "#ff2020"        # red CoM marker
    return "#808890"            # default grey

def get_shininess(name):
    n = name.lower()
    glanz = {
        "tire": 5,
        "hub": 30,
        "n20": 80,
        "motorhalter": 15,
        "carrier": 40,
        "arduino": 40,
        "botframe": 25,
        "samsung": 60,
    }
    for schluessel, wert in glanz.items():
        if schluessel in n:
            return wert
    return 30

# ---- Tessellierung ----
print("Lade:", ASSEMBLY)
doc = App.openDocument(ASSEMBLY, hidden=True)

groups = []  # [{name, color, shin, v:[x,y,z,...], i:[a,b,c,...]}]

# Bounding box tracking
all_min = [1e9, 1e9, 1e9]
all_max = [-1e9, -1e9, -1e9]

for obj in sorted(doc.Objects, key=lambda o: o.Name):
    if not hasattr(obj, "Shape"):
        continue
    shp = obj.Shape
    if shp.isNull() or (shp.Volume <= 0 and not shp.Faces):
        continue

    # Skip CoM marker
    if "com" in obj.Name.lower() or "marker" in obj.Name.lower():
        continue

    tol = 0.3  # mm — finer tessellation for small robot parts

    try:
        pts, tris = shp.tessellate(tol)
    except Exception as ex:
        print(f"  SKIP {obj.Name}: {ex}")
        continue

    if not pts or not tris:
        continue

    # Koordinaten-Konvertierung: FreeCAD Z-up → Three.js Y-up
    # FreeCAD (x, y, z) → Three.js (x, z, -y)
    verts = []
    for p in pts:
        x, y, z = p.x, p.z, -p.y
        verts.extend([x, y, z])
        all_min[0] = min(all_min[0], x)
        all_min[1] = min(all_min[1], y)
        all_min[2] = min(all_min[2], z)
        all_max[0] = max(all_max[0], x)
        all_max[1] = max(all_max[1], y)
        all_max[2] = max(all_max[2], z)

    idx = []
    for t in tris:
        idx.extend([t[0], t[1], t[2]])

    groups.append({
        "name":  obj.Name,
        "color": get_color(obj.Name),
        "shin":  get_shininess(obj.Name),
        "v":     verts,
        "i":     idx,
    })
    print(f"  {obj.Name:<35} {len(pts):6d} pts  {len(tris):6d} tris")

App.closeDocument(doc.Name)

total_tris = sum(len(g["i"]) // 3 for g in groups)
print(f"Gruppen: {len(groups)}  |  Dreiecke gesamt: {total_tris}")

# Modell-Mittelpunkt (fuer Kamera-Orbit)
CX = (all_min[0] + all_max[0]) / 2.0
CY = (all_min[1] + all_max[1]) / 2.0
CZ = (all_min[2] + all_max[2]) / 2.0

# Orbit-Radius: etwas groesser als die Diagonale
diag = math.sqrt((all_max[0]-all_min[0])**2 + (all_max[1]-all_min[1])**2 + (all_max[2]-all_min[2])**2)
RADIUS = diag * 1.4

print(f"Center: ({CX:.1f}, {CY:.1f}, {CZ:.1f})  Radius: {RADIUS:.1f}")

groups_json = json.dumps(groups, separators=(",", ":"))

# ---- HTML / Three.js ----
html = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>BalanceBot — Assembly</title>
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  body { background:#1a2030; overflow:hidden; }
  #info {
    position:absolute; top:14px; left:16px;
    color:#c8d8e8; font:13px/1.6 system-ui,sans-serif;
    text-shadow:0 1px 3px #000a;
    pointer-events:none;
  }
  #info h1 { font-size:15px; font-weight:600; margin-bottom:2px; }
  #hint { position:absolute; bottom:12px; right:16px;
          color:#6080a0; font:11px system-ui,sans-serif; text-align:right; }
</style>
</head>
<body>
<canvas id="c"></canvas>
<div id="info">
  <h1>BalanceBot — Two-Wheeled Self-Balancing Robot</h1>
  Arduino Nano 33 IoT + Nano Motor Carrier
</div>
<div id="hint">Drag = rotate manually<br>Double-click = toggle auto-rotation<br>Scroll = zoom</div>

<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/build/three.min.js"></script>
<script>
// =====================================================================
//  Embedded geometry data
// =====================================================================
const GROUPS = """ + groups_json + """;

// =====================================================================
//  Three.js Setup
// =====================================================================
const canvas   = document.getElementById('c');
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type    = THREE.PCFSoftShadowMap;
renderer.toneMapping       = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.1;

const scene  = new THREE.Scene();
scene.background = new THREE.Color(0xf0f2f5);

const camera = new THREE.PerspectiveCamera(36, window.innerWidth/window.innerHeight, 1, 50000);

// ---- Lighting ----
const ambient = new THREE.AmbientLight(0xb0c0d8, 0.7);
scene.add(ambient);

const sun = new THREE.DirectionalLight(0xfff4e0, 1.6);
sun.position.set(""" + f"{CX + RADIUS*0.8:.1f},{CY + RADIUS*1.5:.1f},{CZ + RADIUS*0.6:.1f}" + """);
sun.castShadow  = true;
sun.shadow.mapSize.set(2048, 2048);
const sc = sun.shadow.camera;
sc.left = sc.bottom = """ + f"{-diag:.1f}" + """;
sc.right = sc.top = """ + f"{diag:.1f}" + """;
sc.near = 1; sc.far = """ + f"{RADIUS * 5:.1f}" + """;
scene.add(sun);

const fill = new THREE.DirectionalLight(0x8090c0, 0.5);
fill.position.set(""" + f"{CX - RADIUS*0.6:.1f},{CY + RADIUS*0.3:.1f},{CZ - RADIUS*0.8:.1f}" + """);
scene.add(fill);

const rim = new THREE.DirectionalLight(0xffeedd, 0.3);
rim.position.set(""" + f"{CX:.1f},{CY - RADIUS*0.5:.1f},{CZ - RADIUS:.1f}" + """);
scene.add(rim);

// ---- Ground plane (subtle shadow catcher) ----
const ground = new THREE.Mesh(
  new THREE.PlaneGeometry(""" + f"{diag*4:.0f},{diag*4:.0f}" + """),
  new THREE.ShadowMaterial({ opacity: 0.15 })
);
ground.rotation.x = -Math.PI / 2;
ground.position.set(""" + f"{CX:.1f},{all_min[1] - 1:.1f},{CZ:.1f}" + """);
ground.receiveShadow = true;
scene.add(ground);

// ---- Geometries ----
GROUPS.forEach(g => {
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute(g.v, 3));
  geo.setIndex(g.i);
  geo.computeVertexNormals();

  const mat = new THREE.MeshPhongMaterial({
    color:     new THREE.Color(g.color),
    shininess: g.shin,
    specular:  new THREE.Color('#404040'),
    side:      THREE.DoubleSide,
  });
  const mesh = new THREE.Mesh(geo, mat);
  mesh.castShadow    = true;
  mesh.receiveShadow = true;
  scene.add(mesh);
});

// =====================================================================
//  Camera orbit
// =====================================================================
const CX_C = """ + f"{CX:.1f}" + """;
const CY_C = """ + f"{CY:.1f}" + """;
const CZ_C = """ + f"{CZ:.1f}" + """;
const TARGET = new THREE.Vector3(CX_C, CY_C, CZ_C);
const ORBIT_R = """ + f"{RADIUS:.1f}" + """;

let azimuth   = 2.4;          // start angle (rad)
let elevation = 0.35;         // ~20 deg above horizon
let radius    = ORBIT_R;
let autoRot   = true;

function positionCamera() {
  camera.position.set(
    CX_C + radius * Math.cos(elevation) * Math.sin(azimuth),
    CY_C + radius * Math.sin(elevation),
    CZ_C + radius * Math.cos(elevation) * Math.cos(azimuth)
  );
  camera.lookAt(TARGET);
}

// ---- Mouse control ----
let dragging = false, lastMX = 0, lastMY = 0;

canvas.addEventListener('mousedown',  e => { dragging=true; lastMX=e.clientX; lastMY=e.clientY; autoRot=false; });
canvas.addEventListener('mousemove',  e => {
  if (!dragging) return;
  azimuth   -= (e.clientX - lastMX) * 0.006;
  elevation  = Math.max(0.05, Math.min(1.3, elevation + (e.clientY - lastMY) * 0.004));
  lastMX = e.clientX; lastMY = e.clientY;
  positionCamera();
});
canvas.addEventListener('mouseup',   () => dragging = false);
canvas.addEventListener('dblclick',  () => autoRot  = !autoRot);
canvas.addEventListener('wheel', e => {
  e.preventDefault();
  radius = Math.max(ORBIT_R * 0.3, Math.min(ORBIT_R * 3, radius + e.deltaY * 0.3));
  positionCamera();
}, {passive: false});

// Touch support
canvas.addEventListener('touchstart', e => { const t=e.touches[0]; lastMX=t.clientX; lastMY=t.clientY; autoRot=false; }, {passive:true});
canvas.addEventListener('touchmove',  e => {
  e.preventDefault();
  const t=e.touches[0];
  azimuth   -= (t.clientX - lastMX) * 0.006;
  elevation  = Math.max(0.05, Math.min(1.3, elevation + (t.clientY - lastMY) * 0.004));
  lastMX=t.clientX; lastMY=t.clientY;
  positionCamera();
}, {passive:false});

window.addEventListener('resize', () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
});

// ---- Render loop ----
function animate() {
  requestAnimationFrame(animate);
  if (autoRot) { azimuth += 0.003; positionCamera(); }
  renderer.render(scene, camera);
}
positionCamera();
animate();
</script>
</body>
</html>
"""

with open(HTML_OUT, "w", encoding="utf-8") as f:
    f.write(html)

size_kb = os.path.getsize(HTML_OUT) / 1024
print(f"Gespeichert: {HTML_OUT}  ({size_kb:.0f} KB)")
