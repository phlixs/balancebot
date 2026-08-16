"""
plot_pid_live.py -- Live-Plot fuer BalanceBot PID-Tuning

Zeigt 3 Diagramme in Echtzeit:
  1. Neigungswinkel (Pitch)
  2. PID-Anteile (P, I, D) + Duty
  3. Position (Encoder)

Speichert beim Schliessen:
  - CSV-Datei mit Timestamp im Dateinamen
  - Plot als PNG

Benutzung:
    python plot_pid_live.py

Beenden: Fenster schliessen oder Ctrl+C
"""

import serial
import csv
import time
import os
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import deque
from datetime import datetime

PORT = "COM13"
BAUD = 115200
FENSTER = 500  # Datenpunkte im Plot-Fenster

SKRIPT_ORDNER = os.path.dirname(os.path.abspath(__file__))
AUSGABE_ORDNER = os.path.join(SKRIPT_ORDNER, "..", "messungen")
os.makedirs(AUSGABE_ORDNER, exist_ok=True)

# Timestamp fuer Dateinamen
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
CSV_DATEI = os.path.join(AUSGABE_ORDNER, f"pid_{timestamp}.csv")
PLOT_DATEI = os.path.join(AUSGABE_ORDNER, f"pid_{timestamp}.png")

# Datenpuffer (Plot zeigt nur die letzten FENSTER Punkte)
zeit = deque(maxlen=FENSTER)
pitch = deque(maxlen=FENSTER)
p_werte = deque(maxlen=FENSTER)
i_werte = deque(maxlen=FENSTER)
d_werte = deque(maxlen=FENSTER)
duty_werte = deque(maxlen=FENSTER)
position = deque(maxlen=FENSTER)

print(f"Verbinde mit {PORT} ...")
ser = serial.Serial(PORT, BAUD, timeout=1)
ser.setDTR(False)
time.sleep(0.1)
ser.setDTR(True)       # DTR-Toggle erzwingt Arduino-Reset
time.sleep(3)          # Warten bis Arduino setup() fertig ist
ser.reset_input_buffer()
print("Verbunden! Arduino wurde neu gestartet.")

# CSV oeffnen
csvdatei = open(CSV_DATEI, "w", newline="", encoding="utf-8")
writer = csv.writer(csvdatei)
writer.writerow(["zeitstempel", "sekunden", "pitch", "p", "i", "d", "duty", "position"])
print(f"CSV: {CSV_DATEI}")

fig, (ax1, ax2, ax3) = plt.subplots(3, 1, sharex=True, figsize=(12, 8))
fig.suptitle("BalanceBot PID Live")

# Plot 1: Pitch
ln_pitch, = ax1.plot([], [], "b-", linewidth=1.5, label="Pitch")
ax1.axhline(y=0, color="red", linestyle="--", linewidth=0.5)
ax1.set_ylabel("Neigung (Grad)")
ax1.legend(loc="upper right")
ax1.grid(True)

# Plot 2: PID-Anteile + Duty
ln_p, = ax2.plot([], [], "r-", linewidth=1, label="P")
ln_i, = ax2.plot([], [], "g-", linewidth=1, label="I")
ln_d, = ax2.plot([], [], "m-", linewidth=1, label="D")
ln_duty, = ax2.plot([], [], "k-", linewidth=2, label="Duty")
ax2.axhline(y=0, color="gray", linestyle="--", linewidth=0.5)
ax2.set_ylabel("PID / Duty")
ax2.legend(loc="upper right")
ax2.grid(True)

# Plot 3: Position
ln_pos, = ax3.plot([], [], "g-", linewidth=1.5, label="Position")
ax3.axhline(y=0, color="gray", linestyle="--", linewidth=0.5)
ax3.set_xlabel("Zeit (s)")
ax3.set_ylabel("Encoder Counts")
ax3.legend(loc="upper right")
ax3.grid(True)

startzeit = None
startzeit_pc = time.time()

def update(frame):
    global startzeit

    for _ in range(20):
        try:
            line = ser.readline().decode("utf-8", errors="ignore").strip()
            teile = line.split(",")
            if len(teile) == 7:
                ms = float(teile[0])
                if startzeit is None:
                    startzeit = ms
                t = (ms - startzeit) / 1000.0

                zeit.append(t)
                pitch.append(float(teile[1]))
                p_werte.append(float(teile[2]))
                i_werte.append(float(teile[3]))
                d_werte.append(float(teile[4]))
                duty_werte.append(float(teile[5]))
                position.append(float(teile[6]))

                # In CSV schreiben
                jetzt = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                writer.writerow([jetzt, round(t, 3), teile[1], teile[2],
                                 teile[3], teile[4], teile[5], teile[6]])
                csvdatei.flush()
        except (ValueError, IndexError):
            pass

    if len(zeit) < 2:
        return

    t_list = list(zeit)

    # Plot 1: Pitch
    ln_pitch.set_data(t_list, list(pitch))
    ax1.set_xlim(t_list[0], t_list[-1])
    ax1.set_ylim(-45, 45)
    ax1.set_yticks(range(-45, 46, 5))

    # Plot 2: PID + Duty
    ln_p.set_data(t_list, list(p_werte))
    ln_i.set_data(t_list, list(i_werte))
    ln_d.set_data(t_list, list(d_werte))
    ln_duty.set_data(t_list, list(duty_werte))
    alle = list(p_werte) + list(d_werte) + list(duty_werte)
    if alle:
        rand = max(abs(min(alle)), abs(max(alle)), 10) * 1.2
        ax2.set_ylim(-rand, rand)

    # Plot 3: Position
    ln_pos.set_data(t_list, list(position))
    if position:
        pmax = max(abs(min(position)), abs(max(position)), 50) * 1.2
        ax3.set_ylim(-pmax, pmax)
    ax3.set_xlim(t_list[0], t_list[-1])

    return ln_pitch, ln_p, ln_i, ln_d, ln_duty, ln_pos

ani = animation.FuncAnimation(fig, update, interval=50, blit=False, cache_frame_data=False)
plt.tight_layout()
plt.show()

# Nach Schliessen: Plot speichern und aufraeumen
fig.savefig(PLOT_DATEI, dpi=150)
csvdatei.close()
ser.close()
print(f"\nGespeichert:")
print(f"  CSV:  {CSV_DATEI}")
print(f"  Plot: {PLOT_DATEI}")
