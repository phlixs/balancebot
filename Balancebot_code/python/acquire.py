"""
acquire.py -- BalanceBot: Serielle Rohdaten aufzeichnen

Liest den seriellen Port und schreibt jede gueltige Datenzeile
in eine timestamped CSV-Datei. Kommentarzeilen (beginnen mit '#')
werden separat protokolliert aber nicht in die CSV geschrieben.

Benutzung:
    python acquire.py                   # Balance-Modus (Standard)
    python acquire.py --mode carrier    # Carrier-Timing-Test
    python acquire.py --mode imu        # IMU-Latenz-Test
    python acquire.py --mode deadzone   # Totzone-Identifikation

Beenden: Ctrl+C
"""

import argparse
import csv
import os
import sys
import time
from datetime import datetime

import serial

from config import BALANCE_COLUMNS, BALANCE_NCOLS, RAW_DIR, SERIAL_BAUD, SERIAL_PORT, SERIAL_TIMEOUT

# ============================================================
# Argument-Parsing
# ============================================================

parser = argparse.ArgumentParser(description="BalanceBot serielle Datenaufzeichnung")
parser.add_argument(
    "--mode",
    choices=["balance", "carrier", "imu", "deadzone"],
    default="balance",
    help="Welcher Test-Sketch laeuft (bestimmt CSV-Schema)"
)
parser.add_argument(
    "--port",
    default=SERIAL_PORT,
    help=f"Serieller Port (Standard: {SERIAL_PORT})"
)
parser.add_argument(
    "--ncols",
    type=int,
    default=None,
    help="Erwartete Spaltenanzahl (Standard: aus config.py)"
)
args = parser.parse_args()

# ============================================================
# Modus-abhaengige Einstellungen
# ============================================================

MODE_SETTINGS = {
    "balance":  {"ncols": BALANCE_NCOLS,  "columns": BALANCE_COLUMNS},
    "carrier":  {"ncols": None,           "columns": None},   # freies Format
    "imu":      {"ncols": 5,              "columns": ["i","t_us","duration_us","pitch","changed"]},
    "deadzone": {"ncols": 4,              "columns": ["t_ms","duty","enc1_cps","enc2_cps"]},
}

mode_cfg  = MODE_SETTINGS[args.mode]
ncols     = args.ncols if args.ncols is not None else mode_cfg["ncols"]
columns   = mode_cfg["columns"]

# ============================================================
# Ausgabedatei erzeugen
# ============================================================

timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")
csv_path   = os.path.join(RAW_DIR, f"{args.mode}_{timestamp}.csv")
log_path   = os.path.join(RAW_DIR, f"{args.mode}_{timestamp}.log")  # Kommentare

print(f"Verbinde mit {args.port} (Modus: {args.mode}) ...")

try:
    ser = serial.Serial(args.port, SERIAL_BAUD, timeout=SERIAL_TIMEOUT)
except serial.SerialException as e:
    print(f"FEHLER: {e}")
    print("Seriellen Port pruefen (pio device list)")
    sys.exit(1)

time.sleep(2)               # Arduino-Reset abwarten
ser.reset_input_buffer()    # Alte Daten verwerfen

print(f"Verbunden. Schreibe nach: {csv_path}")
print("Ctrl+C zum Beenden.\n")

# ============================================================
# Hauptschleife
# ============================================================

zeilen_gesamt  = 0
zeilen_ok      = 0
zeilen_fehler  = 0

with open(csv_path, "w", newline="", encoding="utf-8") as csvfile, \
     open(log_path, "w", encoding="utf-8") as logfile:

    writer = csv.writer(csvfile)

    # Header schreiben
    if columns is not None:
        writer.writerow(columns)
    # Fuer Carrier-Modus: Header wird aus erster gueltiger Textzeile genommen

    header_written = (columns is not None)

    try:
        while True:
            raw = ser.readline().decode("utf-8", errors="ignore").strip()
            zeilen_gesamt += 1

            # Kommentarzeilen (beginnen mit '#') --> nur in Log schreiben
            if raw.startswith("#"):
                logfile.write(raw + "\n")
                logfile.flush()
                print(raw)  # Kommentare auch auf Konsole ausgeben
                continue

            # Leerzeilen ueberspringen
            if not raw:
                continue

            # Carrier-Modus: Header aus erster nicht-leerer Zeile lesen
            if args.mode == "carrier" and not header_written:
                # Erste Zeile ist der Header
                logfile.write("HEADER: " + raw + "\n")
                header_written = True
                continue

            # Werte parsen
            parts = raw.split(",")

            # Spaltenanzahl pruefen (wenn bekannt)
            if ncols is not None and len(parts) != ncols:
                zeilen_fehler += 1
                continue

            try:
                values = [float(p) for p in parts]
            except ValueError:
                zeilen_fehler += 1
                continue

            # Gueltige Zeile in CSV schreiben
            writer.writerow(values)
            csvfile.flush()
            zeilen_ok += 1

            # Fortschritts-Ausgabe alle 100 Zeilen
            if zeilen_ok % 100 == 0:
                if args.mode == "balance" and len(values) >= 3:
                    pitch = values[2]
                    duty  = values[7] if len(values) > 7 else "?"
                    print(f"  {zeilen_ok:5d} Zeilen | Pitch: {pitch:+6.2f}° | Duty: {duty}")
                else:
                    print(f"  {zeilen_ok:5d} Zeilen aufgezeichnet")

    except KeyboardInterrupt:
        pass

# ============================================================
# Abschluss-Statistik
# ============================================================

ser.close()
print("\n--- Aufzeichnung beendet ---")
print(f"  Gesamt eingelesen:  {zeilen_gesamt}")
print(f"  Datenzeilen (ok):   {zeilen_ok}")
print(f"  Fehlzeilen:         {zeilen_fehler}")
print(f"  Gespeichert unter:  {csv_path}")
print(f"  Kommentarlog:       {log_path}")
print(f"\nWeiterverarbeitung: python process.py {csv_path}")
