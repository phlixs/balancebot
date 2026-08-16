"""
serial_to_csv.py  --  Liest serielle Daten vom BalanceBot (BNO055 Pitch)
                      und speichert sie als CSV-Datei.

Benutzung:
    python serial_to_csv.py

Beenden:  Ctrl+C druecken. Die CSV-Datei wird automatisch sauber geschlossen.
"""

import csv
import time
import serial
from datetime import datetime

# --- Einstellungen (hier anpassen!) ---
PORT = "COM12"          # Dein Arduino-Port (gleich wie in plot_serial.py)
BAUD = 115200           # Baudrate (muss zu Serial.begin() im Arduino passen)
DATEINAME = "balancebot_daten.csv"

# --- Serielle Verbindung oeffnen ---
print(f"Verbinde mit {PORT} ...")
ser = serial.Serial(PORT, BAUD, timeout=1)
time.sleep(2)                  # Arduino braucht kurz nach dem Verbinden
ser.reset_input_buffer()       # Alte Daten im Puffer wegwerfen
print("Verbunden! Aufnahme laeuft. Druecke Ctrl+C zum Beenden.\n")

# --- CSV-Datei oeffnen und Kopfzeile schreiben ---
# "newline=''" verhindert leere Zeilen zwischen den Eintraegen auf Windows
csvdatei = open(DATEINAME, "w", newline="", encoding="utf-8")
writer = csv.writer(csvdatei)
# Header passend zu balance.cpp
writer.writerow(["zeitstempel", "sekunden", "pitch", "fehler", "p_anteil", "i_anteil", "d_anteil", "v_anteil", "position", "pid_output", "motor_duty"])

zaehler = 0
startzeit = time.time()

# --- Hauptschleife: Lesen, Parsen, Speichern ---
try:
    while True:
        # Eine Zeile vom Arduino lesen
        roh = ser.readline().decode("utf-8", errors="ignore").strip()

        # Zeilen mit genau 9 Komma-getrennten Werten verarbeiten
        teile = roh.split(",")
        if len(teile) == 9:
            try:
                # Pruefen ob es Zahlen sind (filtert Textzeilen raus)
                werte = [float(t) for t in teile]

                # Zeitstempel berechnen
                jetzt = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                sekunden = round(time.time() - startzeit, 3)

                # In CSV schreiben
                writer.writerow([jetzt, sekunden] + werte)
                csvdatei.flush()

                zaehler += 1
                if zaehler % 100 == 0:
                    print(f"  {zaehler} Messungen | Pitch: {werte[0]:.1f}° | Motor: {int(werte[6])}")

            except ValueError:
                pass  # Kaputte Zeile oder Textzeile, ueberspringen

except KeyboardInterrupt:
    # Ctrl+C wurde gedrueckt -- sauber aufraumen
    print(f"\n--- Aufnahme beendet ---")
    print(f"{zaehler} Messungen in '{DATEINAME}' gespeichert.")

finally:
    csvdatei.close()
    ser.close()
