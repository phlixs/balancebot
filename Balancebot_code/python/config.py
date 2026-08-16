"""
config.py -- BalanceBot: Gemeinsame Konfiguration fuer alle Python-Skripte

Alle Einstellungen werden hier zentral definiert.
Die einzelnen Skripte (acquire.py, process.py, analyze.py) importieren diese Datei.
"""

import os

# ============================================================
# Serial-Verbindung
# ============================================================

# Serieller Port des Arduino (anpassen!)
# Linux: "/dev/ttyACM0" oder "/dev/ttyUSB0"
# Windows: "COM12" (wie bisher im seriellen Monitor)
SERIAL_PORT = "/dev/ttyACM0"

# Baudrate -- muss mit SERIAL_BAUD in config.h uebereinstimmen
SERIAL_BAUD = 115200

# Timeout fuer serielle Leseoperation [s]
SERIAL_TIMEOUT = 1.0

# ============================================================
# Datei-Pfade
# ============================================================

# Basis-Verzeichnis relativ zu diesem Skript
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)

# Verzeichnis fuer rohe CSV-Aufzeichnungen
RAW_DIR = os.path.join(PROJECT_DIR, "messungen", "raw")

# Verzeichnis fuer verarbeitete Daten
PROCESSED_DIR = os.path.join(PROJECT_DIR, "messungen", "processed")

# Verzeichnis fuer Plots
PLOTS_DIR = os.path.join(PROJECT_DIR, "messungen", "plots")

# Verzeichnisse anlegen falls nicht vorhanden
for d in [RAW_DIR, PROCESSED_DIR, PLOTS_DIR]:
    os.makedirs(d, exist_ok=True)

# ============================================================
# CSV-Schema (muss mit logger.cpp uebereinstimmen!)
# ============================================================

# Spaltennamen der rohen CSV-Daten (balance-Umgebung)
BALANCE_COLUMNS = [
    "millis",       # Arduino millis() [ms]
    "state",        # Zustand (0=INIT, 1=CAL, 2=IDLE, 3=BAL, 4=FAL, 5=ESTOP)
    "pitch",        # Kippwinkel [Grad]
    "pitch_rate",   # Winkelgeschwindigkeit [Grad/s]
    "p",            # P-Anteil [% Duty]
    "i",            # I-Anteil [% Duty]
    "d",            # D-Anteil [% Duty]
    "duty",         # Tatsaechlicher Duty [%]
    "pos_counts",   # Position [Encoder-Counts]
    "pos_m",        # Position [Meter]
]

# Anzahl Spalten (fuer Validierung in acquire.py)
BALANCE_NCOLS = len(BALANCE_COLUMNS)

# Zustand-Mapping (fuer Lesbarkeit in Plots)
STATE_NAMES = {
    0: "INIT",
    1: "CALIBRATING",
    2: "IDLE",
    3: "BALANCING",
    4: "FALLEN",
    5: "E_STOP",
}

# ============================================================
# Physikalische Konstanten (aus config.h)
# ============================================================

WHEEL_DIAMETER_M   = 0.090        # Raddurchmesser [m]
WHEEL_CIRCUMFERENCE_M = 3.14159265 * WHEEL_DIAMETER_M
COUNTS_PER_WHEEL_REV = 1200       # Encoder-Ticks pro Radumdrehung
METERS_PER_COUNT   = WHEEL_CIRCUMFERENCE_M / COUNTS_PER_WHEEL_REV
