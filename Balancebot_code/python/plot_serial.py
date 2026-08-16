import time
import serial
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import deque

PORT = "COM12"
BAUD = 9600
MAX_POINTS = 200

ser = serial.Serial(PORT, BAUD, timeout=1)
time.sleep(2)
ser.reset_input_buffer()
times = deque(maxlen=MAX_POINTS)
pitches = deque(maxlen=MAX_POINTS)
sample = 0

fig, ax = plt.subplots()
(line,) = ax.plot([], [])
ax.set_xlabel("Sample")
ax.set_ylabel("Pitch (deg)")
ax.set_title("BNO055 Pitch - Live")


def update(frame):
    global sample
    while ser.in_waiting:
        raw = ser.readline().decode("utf-8", errors="ignore").strip()
        if raw.startswith("Pitch:"):
            try:
                value = float(raw.split(":")[1].replace("deg", "").strip())
                times.append(sample)
                pitches.append(value)
                sample += 1
            except ValueError:
                pass

    if times:
        line.set_data(list(times), list(pitches))
        ax.set_xlim(times[0], times[-1] + 1)
        ax.set_ylim(min(pitches) - 5, max(pitches) + 5)
    return (line,)


ani = animation.FuncAnimation(fig, update, interval=50, blit=True)
plt.tight_layout()
plt.show()
ser.close()
