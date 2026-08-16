"""
plot_csv.py  --  Plottet PID-Daten vom BalanceBot.

Benutzung:
    python plot_csv.py

Zeigt vier Diagramme:
  1. Pitch-Winkel
  2. Motor-Duty
  3. Geschwindigkeit (v_anteil)
  4. Position (Encoder)
"""

import csv
import os
import matplotlib.pyplot as plt

# --- Einstellungen ---
SKRIPT_ORDNER = os.path.dirname(os.path.abspath(__file__))
DATEINAME = os.path.join(SKRIPT_ORDNER, "..", "balancebot_daten.csv")

# --- CSV-Datei einlesen ---
sekunden = []
pitch = []
motor_duty = []
v_anteil = []
position = []

with open(DATEINAME, encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for zeile in reader:
        sekunden.append(float(zeile["sekunden"]))
        pitch.append(float(zeile["pitch"]))
        motor_duty.append(float(zeile["motor_duty"]))
        v_anteil.append(float(zeile.get("v_anteil", 0)))
        position.append(float(zeile.get("position", 0)))

print(f"{len(sekunden)} Messwerte eingelesen.")

# --- Plot erstellen: 4 Diagramme uebereinander ---
fig, (ax1, ax2, ax3, ax4) = plt.subplots(4, 1, sharex=True, figsize=(10, 9))

# 1. Pitch-Winkel
ax1.plot(sekunden, pitch, linewidth=1, label="Pitch")
ax1.axhline(y=0, color="red", linestyle="--", label="Ziel (0 Grad)")
ax1.set_ylabel("Neigung (Grad)")
ax1.set_title("BalanceBot PID")
ax1.legend()
ax1.grid(True)

# 2. Motor-Duty
ax2.plot(sekunden, motor_duty, linewidth=1, color="orange", label="Motor Duty")
ax2.axhline(y=0, color="gray", linestyle="--")
ax2.set_ylabel("Motor Duty (%)")
ax2.legend()
ax2.grid(True)

# 3. Geschwindigkeit (v_anteil)
ax3.plot(sekunden, v_anteil, linewidth=1, color="purple", label="v_anteil (Geschwindigkeit)")
ax3.axhline(y=0, color="gray", linestyle="--")
ax3.set_ylabel("v_anteil")
ax3.legend()
ax3.grid(True)

# 4. Position (Encoder)
ax4.plot(sekunden, position, linewidth=1, color="green", label="Position (Encoder)")
ax4.axhline(y=0, color="gray", linestyle="--")
ax4.set_xlabel("Zeit (Sekunden)")
ax4.set_ylabel("Position (Counts)")
ax4.legend()
ax4.grid(True)

plt.tight_layout()
plt.show()
