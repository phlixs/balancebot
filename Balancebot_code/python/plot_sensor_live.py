"""
plot_sensor_live.py -- Live-Plot: Rohes vs. gefiltertes Pitch-Signal

Benutzung:
    python plot_sensor_live.py

Zeigt in Echtzeit wie stark der Filter das Signal verzögert.
Beenden: Fenster schliessen oder Ctrl+C.
"""

import serial
import time
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import deque

PORT = "COM12"
BAUD = 115200
FENSTER = 500  # Anzahl Datenpunkte im Fenster

# Datenpuffer
zeit = deque(maxlen=FENSTER)
roh = deque(maxlen=FENSTER)
gefiltert = deque(maxlen=FENSTER)

print(f"Verbinde mit {PORT} ...")
ser = serial.Serial(PORT, BAUD, timeout=1)
time.sleep(2)
ser.reset_input_buffer()
print("Verbunden!")

fig, ax = plt.subplots(figsize=(10, 5))
linie_roh, = ax.plot([], [], linewidth=1, label="Pitch roh", alpha=0.6)
linie_filt, = ax.plot([], [], linewidth=2, label="Pitch gefiltert")
ax.axhline(y=0, color="red", linestyle="--", linewidth=0.5)
ax.set_ylabel("Neigung (Grad)")
ax.set_xlabel("Zeit (ms)")
ax.set_title("Sensor-Signal: Roh vs. Gefiltert (Alpha=0.2)")
ax.legend()
ax.grid(True)

startzeit = None

def update(frame):
    global startzeit
    # Mehrere Zeilen pro Frame lesen (Buffer leeren)
    for _ in range(10):
        try:
            line = ser.readline().decode("utf-8", errors="ignore").strip()
            teile = line.split(",")
            if len(teile) == 3:
                ms = float(teile[0])
                if startzeit is None:
                    startzeit = ms
                zeit.append((ms - startzeit) / 1000.0)
                roh.append(float(teile[1]))
                gefiltert.append(float(teile[2]))
        except (ValueError, IndexError):
            pass

    if len(zeit) > 1:
        linie_roh.set_data(list(zeit), list(roh))
        linie_filt.set_data(list(zeit), list(gefiltert))
        ax.set_xlim(zeit[0], zeit[-1])
        ax.set_ylim(-50, 50)
    return linie_roh, linie_filt

ani = animation.FuncAnimation(fig, update, interval=50, blit=False, cache_frame_data=False)
plt.tight_layout()
plt.show()
ser.close()
