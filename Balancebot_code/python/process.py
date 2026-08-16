"""
process.py -- BalanceBot: Rohdaten validieren und abgeleitete Signale berechnen

Liest eine raw-CSV-Datei (aus acquire.py), pruefte die Daten
und berechnet abgeleitete Signale:
  - dt [s]: tatsaechliche Abtastzeit pro Zeile
  - t_s [s]: Zeit ab dem ersten Datenpunkt
  - pid_out [%]: ungesaettigter PID-Ausgang (p + i + d)
  - speed_rad_s [rad/s]: Winkelgeschwindigkeit in rad/s
  - pos_diff [counts]: Positionsdifferenz zwischen Encoder links und rechts

Ausgabe: Verarbeitete CSV in messungen/processed/

Benutzung:
    python process.py messungen/raw/balance_20260412_123456.csv
    python process.py messungen/raw/deadzone_20260412_125000.csv --mode deadzone
"""

import argparse
import os
import sys

import pandas as pd

from config import BALANCE_COLUMNS, PROCESSED_DIR, STATE_NAMES

# ============================================================
# Argument-Parsing
# ============================================================

parser = argparse.ArgumentParser(description="BalanceBot Datenverarbeitung")
parser.add_argument("csvfile", help="Pfad zur rohen CSV-Datei (aus acquire.py)")
parser.add_argument(
    "--mode",
    choices=["balance", "deadzone", "imu"],
    default="balance"
)
args = parser.parse_args()

if not os.path.exists(args.csvfile):
    print(f"FEHLER: Datei nicht gefunden: {args.csvfile}")
    sys.exit(1)

# ============================================================
# Daten einlesen
# ============================================================

print(f"Lese: {args.csvfile}")
df = pd.read_csv(args.csvfile, comment="#")
print(f"  {len(df)} Zeilen, {len(df.columns)} Spalten eingelesen")

# ============================================================
# Modus: Balance
# ============================================================

if args.mode == "balance":
    # Spaltennamen pruefen
    expected = set(BALANCE_COLUMNS)
    actual   = set(df.columns)
    missing  = expected - actual
    if missing:
        print(f"WARNUNG: Fehlende Spalten: {missing}")

    # NaN und Duplikate entfernen
    n_before = len(df)
    df = df.dropna()
    df = df.drop_duplicates(subset="millis")
    print(f"  Bereinigt: {n_before - len(df)} Zeilen entfernt")

    # Zeitachse berechnen
    df["t_s"]  = (df["millis"] - df["millis"].iloc[0]) / 1000.0  # [s]
    df["dt"]   = df["millis"].diff() / 1000.0                      # [s]
    df.loc[df.index[0], "dt"] = df["dt"].median()                  # Erster Wert: Median

    # Timing-Statistik ausgeben
    dt_ms = df["dt"] * 1000.0
    print("\n  Abtastzeit (dt):")
    print(f"    Soll:  {10.0:.1f} ms")
    print(f"    Ist:   mean={dt_ms.mean():.2f} ms  std={dt_ms.std():.2f} ms  max={dt_ms.max():.2f} ms")
    if dt_ms.max() > 15.0:
        print(f"  WARNUNG: Max-Jitter > 15ms! ({dt_ms.max():.1f} ms)")

    # Abgeleitete Signale
    df["pid_out"] = df["p"] + df["i"] + df["d"]          # Ungesaettigter PID-Ausgang

    # Zustand als lesbaren String
    df["state_name"] = df["state"].astype(int).map(STATE_NAMES)

    # Nur BALANCING-Phasen fuer Analyse markieren
    df["is_balancing"] = (df["state"] == 3)

    print(f"\n  Balancier-Phasen: {df['is_balancing'].sum()} Zeilen von {len(df)}")

# ============================================================
# Modus: Totzone-Identifikation
# ============================================================

elif args.mode == "deadzone":
    # Absoluten Encoder-Speed berechnen (M1 und M2 separat)
    df["enc1_abs"] = df["enc1_cps"].abs()
    df["enc2_abs"] = df["enc2_cps"].abs()

    # Mittelwert beider Encoder
    df["enc_mean_abs"] = (df["enc1_abs"] + df["enc2_abs"]) / 2.0

    # Totzone-Schatzung: erster Duty-Wert mit enc_mean_abs > 10 cps
    # TODO: Schwellwert 10 cps anpassen
    lauf = df[df["enc_mean_abs"] > 10]
    if len(lauf) > 0:
        dz = lauf["duty"].abs().min()
        print(f"\n  Geschaetzte Totzone: Duty = {dz:.0f} %")
        print("  (erster Duty mit mittlerer Encoder-Geschwindigkeit > 10 cps)")
    else:
        print("\n  WARNUNG: Kein Anlaufen erkannt -- Rampe zu kurz oder Motoren nicht kalibriert!")

# ============================================================
# Verarbeitete Datei speichern
# ============================================================

basename = os.path.splitext(os.path.basename(args.csvfile))[0]
out_path = os.path.join(PROCESSED_DIR, basename + "_proc.csv")
df.to_csv(out_path, index=False)
print(f"\nGespeichert: {out_path}")
print(f"Weiterverarbeitung: python analyze.py {out_path}")
