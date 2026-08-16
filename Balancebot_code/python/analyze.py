"""
analyze.py -- BalanceBot: Daten auswerten und plotten

Liest eine verarbeitete CSV-Datei (aus process.py) und erstellt:
  - Pitch-Verlauf + PID-Anteile
  - Duty-Verlauf
  - Position
  - (Deadzone: Encoder-Speed vs. Duty)
  - (IMU: Latenz-Histogramm, Datenrate)

Benutzung:
    python analyze.py messungen/processed/balance_..._proc.csv
    python analyze.py messungen/processed/deadzone_..._proc.csv --mode deadzone
    python analyze.py messungen/raw/imu_.._.csv --mode imu
    python analyze.py --live          # Echtzeit-Plot waehrend Aufzeichnung
"""

import argparse
import os
import sys

import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import pandas as pd

from config import PLOTS_DIR

# ============================================================
# Argument-Parsing
# ============================================================

parser = argparse.ArgumentParser(description="BalanceBot Datenanalyse")
parser.add_argument("csvfile", nargs="?", help="Verarbeitete CSV-Datei")
parser.add_argument("--mode", choices=["balance", "deadzone", "imu"], default="balance")
parser.add_argument("--save", action="store_true", help="Plot speichern (PNG)")
parser.add_argument("--no-show", action="store_true", help="Plot nicht anzeigen")
args = parser.parse_args()

if not args.csvfile:
    print("FEHLER: Keine Datei angegeben.")
    print("Benutzung: python analyze.py <csvfile> [--mode MODE]")
    sys.exit(1)

df = pd.read_csv(args.csvfile, comment="#")
print(f"Analysiere: {args.csvfile}  ({len(df)} Zeilen)")

# ============================================================
# Modus: Balance
# ============================================================

def plot_balance(df: pd.DataFrame, save: bool, no_show: bool) -> None:
    # Zeitachse
    if "t_s" not in df.columns:
        df["t_s"] = (df["millis"] - df["millis"].iloc[0]) / 1000.0

    fig = plt.figure(figsize=(14, 10))
    fig.suptitle("BalanceBot -- Balance-Messung", fontsize=13)
    gs = gridspec.GridSpec(4, 1, hspace=0.4)

    # --- Subplot 1: Pitch ---
    ax1 = fig.add_subplot(gs[0])
    ax1.axhline(0, color="gray", lw=0.8, ls="--")
    ax1.plot(df["t_s"], df["pitch"], label="Pitch [°]", color="tab:blue")
    ax1.set_ylabel("Pitch [°]")
    ax1.set_ylim(-30, 30)
    ax1.legend(loc="upper right")
    ax1.set_title("Kippwinkel")

    # Balancier-Phasen gruen hinterlegen
    if "is_balancing" in df.columns:
        bal = df["is_balancing"].values
        t   = df["t_s"].values
        in_phase = False
        for i, b in enumerate(bal):
            if b and not in_phase:
                start = t[i]
                in_phase = True
            elif not b and in_phase:
                ax1.axvspan(start, t[i], color="green", alpha=0.1)
                in_phase = False
        if in_phase:
            ax1.axvspan(start, t[-1], color="green", alpha=0.1)

    # --- Subplot 2: PID-Anteile ---
    ax2 = fig.add_subplot(gs[1], sharex=ax1)
    ax2.plot(df["t_s"], df["p"], label="P",     color="tab:red",    lw=0.8)
    ax2.plot(df["t_s"], df["i"], label="I",     color="tab:orange", lw=0.8)
    ax2.plot(df["t_s"], df["d"], label="D",     color="tab:purple", lw=0.8)
    if "pid_out" in df.columns:
        ax2.plot(df["t_s"], df["pid_out"], label="PID (ung.)", color="black", lw=1.2, ls="--")
    ax2.set_ylabel("Duty [%]")
    ax2.legend(loc="upper right", ncol=4, fontsize=8)
    ax2.set_title("PID-Anteile")

    # --- Subplot 3: Duty ---
    ax3 = fig.add_subplot(gs[2], sharex=ax1)
    ax3.plot(df["t_s"], df["duty"], color="tab:green", lw=1.0)
    ax3.set_ylabel("Duty [%]")
    ax3.set_title("Motor-Duty (begrenzt)")

    # --- Subplot 4: Position ---
    ax4 = fig.add_subplot(gs[3], sharex=ax1)
    if "pos_m" in df.columns:
        ax4.plot(df["t_s"], df["pos_m"] * 100.0, color="tab:brown")
        ax4.set_ylabel("Position [cm]")
    elif "pos_counts" in df.columns:
        ax4.plot(df["t_s"], df["pos_counts"], color="tab:brown")
        ax4.set_ylabel("Position [Counts]")
    ax4.set_xlabel("Zeit [s]")
    ax4.set_title("Fahrweg")

    _save_and_show(fig, args.csvfile, save, no_show)


# ============================================================
# Modus: Totzone
# ============================================================

def plot_deadzone(df: pd.DataFrame, save: bool, no_show: bool) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle("Motor Totzone-Identifikation", fontsize=13)

    for ax, col, label in zip(axes, ["enc1_cps", "enc2_cps"], ["Motor M1 (Enc1)", "Motor M2 (Enc2)"]):
        ax.plot(df["duty"].abs(), df[col].abs(), "o", ms=3)
        ax.axvline(0, color="gray", lw=0.8)
        ax.set_xlabel("Duty [%]")
        ax.set_ylabel("Encoder-Geschwindigkeit [counts/s]")
        ax.set_title(label)
        ax.grid(True, alpha=0.3)

    _save_and_show(fig, args.csvfile, save, no_show)


# ============================================================
# Modus: IMU-Latenz
# ============================================================

def plot_imu(df: pd.DataFrame, save: bool, no_show: bool) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle("BNO055 Latenz-Test", fontsize=13)

    if "duration_us" in df.columns:
        axes[0].hist(df["duration_us"], bins=50, color="tab:blue", edgecolor="white")
        axes[0].set_xlabel("getEvent()-Dauer [µs]")
        axes[0].set_ylabel("Haeufigkeit")
        axes[0].set_title("Lateniz-Histogramm")
        axes[0].axvline(df["duration_us"].mean(), color="red", ls="--",
                        label=f"Mean: {df['duration_us'].mean():.0f} µs")
        axes[0].legend()

    if "pitch" in df.columns and "t_us" in df.columns:
        t_s = (df["t_us"] - df["t_us"].iloc[0]) / 1e6
        axes[1].plot(t_s, df["pitch"], lw=0.8)
        axes[1].set_xlabel("Zeit [s]")
        axes[1].set_ylabel("Pitch [°]")
        axes[1].set_title("Pitch-Signal")

    _save_and_show(fig, args.csvfile, save, no_show)


# ============================================================
# Hilfs-Funktion: Speichern und Anzeigen
# ============================================================

def _save_and_show(fig, csvfile, save, no_show):
    if save:
        basename = os.path.splitext(os.path.basename(csvfile))[0]
        out_path = os.path.join(PLOTS_DIR, basename + ".png")
        fig.savefig(out_path, dpi=150, bbox_inches="tight")
        print(f"Plot gespeichert: {out_path}")
    if not no_show:
        plt.show()
    plt.close(fig)


# ============================================================
# Ausfuehren
# ============================================================

if args.mode == "balance":
    plot_balance(df, args.save, args.no_show)
elif args.mode == "deadzone":
    plot_deadzone(df, args.save, args.no_show)
elif args.mode == "imu":
    plot_imu(df, args.save, args.no_show)
