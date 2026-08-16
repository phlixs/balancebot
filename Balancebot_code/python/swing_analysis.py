"""
swing_analysis.py -- BalanceBot: Auswertung des Schwingversuchs (Phase 4, Messung 3)

Der haengende Bot pendelt um die Radachse. Haengender und aufrechter Bot haben
denselben |Eigenwert| -- das Vorzeichen dreht sich, der Betrag nicht. Die
gemessene Schwingfrequenz ist deshalb direkt der instabile Pol des
Balancierproblems, ohne jede Annahme ueber das Traegheitsmoment.

Warum Videoauswertung statt Stoppuhr:
  Bei T ~ 0.5 s verzaehlt man sich beim Mitzaehlen. Das Video liefert 30
  Stuetzstellen pro Sekunde ueber 30+ Perioden; die Frequenz kommt aus dem
  Spektrum statt aus einer Handzaehlung.

Warum die blaue Rahmenplatte als Marker:
  Sie ist die einzige grosse, saettigungsstarke Flaeche am Bot. Wand (weiss),
  Pfeiler (neutralgrau), Tisch (braun) und Hand (Hautton) haben alle B < R,
  eine simple Kanalschwelle trennt sie also zuverlaessig ohne Modelltraining.

Benutzung:
    python python/swing_analysis.py --videos v1.mp4 v2.mp4
    python python/swing_analysis.py --videos v1.mp4 --photo ruhelage.jpg
    python python/swing_analysis.py --videos v1.mp4 --L-mm 9   # Rollkorrektur

Alle Formeln mit Parametertabellen: dokumentation/auslegung/system_model.md und
messungen/results/phase4_swing_20260809.md
"""

import argparse
import re
import subprocess

import imageio_ffmpeg
import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

# ============================================================
# Parameter
# ============================================================

# Blaumaske: Kanalabstaende statt fester Schwellen -- unempfindlich gegen
# Belichtungsunterschiede zwischen den Aufnahmen.
BLUE_VS_RED   = 25
BLUE_VS_GREEN = 15
BLUE_MIN      = 60
MIN_PIXELS    = 200      # darunter gilt der Frame als verdeckt (Hand im Bild)

# Suchband fuer die Grundschwingung [Hz]. Untergrenze schliesst die langsame
# Drift durch Abrollen aus (0.06-0.14 Hz), Obergrenze liegt unter Nyquist.
F_LO, F_HI    = 1.0, 3.5

# Mechanik fuer die Abrollkorrektur
SHAFT_RADIUS_M = 0.0015  # N20-Motorwelle, Radius
G_M_S2         = 9.81


# ============================================================
# Videodekodierung
# ============================================================

def read_timestamps(path: str) -> np.ndarray:
    """Echte Praesentationszeitstempel aus dem Container lesen.

    Nicht auf die Nennframerate verlassen: Handys nehmen haeufig mit variabler
    Framerate auf, was die Frequenz systematisch verzerrt. Mit den echten
    Zeitstempeln faellt das auf und laesst sich korrigieren.
    """
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    out = subprocess.run([ff, "-i", path, "-vf", "showinfo", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    return np.array([float(m) for m in re.findall(r"pts_time:([0-9.]+)", out)])


def video_size(path: str) -> tuple[int, int]:
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    out = subprocess.run([ff, "-i", path], capture_output=True, text=True).stderr
    m = re.search(r",\s(\d+)x(\d+)[\s,]", out)
    if not m:
        raise RuntimeError(f"Aufloesung nicht lesbar: {path}")
    return int(m.group(1)), int(m.group(2))


def blue_mask(frame: np.ndarray) -> np.ndarray:
    r, g, b = frame[:, :, 0].astype(int), frame[:, :, 1].astype(int), frame[:, :, 2].astype(int)
    return (b > r + BLUE_VS_RED) & (b > g + BLUE_VS_GREEN) & (b > BLUE_MIN)


def track_plate(path: str):
    """Pro Frame Schwerpunkt und Hauptachsenwinkel der blauen Platte.

    Beide Signale werden ausgewertet: Der Schwerpunkt hat die bessere
    Statistik, der Winkel ist die physikalisch direkte Groesse. Stimmen sie
    ueberein, ist das ein Hinweis, dass wirklich die Starrkoerperschwingung
    gemessen wurde und nicht ein Trackingartefakt.
    """
    w, h = video_size(path)
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    proc = subprocess.Popen(
        [ff, "-loglevel", "error", "-i", path, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
        stdout=subprocess.PIPE)
    nbytes = w * h * 3
    cx, ang, npx = [], [], []
    while True:
        buf = proc.stdout.read(nbytes)
        if len(buf) < nbytes:
            break
        mask = blue_mask(np.frombuffer(buf, np.uint8).reshape(h, w, 3))
        ys, xs = np.nonzero(mask)
        npx.append(len(xs))
        if len(xs) < MIN_PIXELS:
            cx.append(np.nan)
            ang.append(np.nan)
            continue
        mx, my = xs.mean(), ys.mean()
        u, v = xs - mx, ys - my
        cov = np.array([[(u * u).mean(), (u * v).mean()],
                        [(u * v).mean(), (v * v).mean()]])
        eigval, eigvec = np.linalg.eigh(cov)
        d = eigvec[:, np.argmax(eigval)]
        a = np.degrees(np.arctan2(d[1], d[0]))
        a = a - 180 if a > 90 else (a + 180 if a < -90 else a)
        cx.append(mx)
        ang.append(a)
    proc.stdout.close()
    proc.wait()
    return np.array(cx), np.array(ang), np.array(npx)


# ============================================================
# Frequenzschaetzung
# ============================================================

def dominant_frequency(sig: np.ndarray, fs: float) -> float:
    """Spektralgipfel im Suchband, parabolisch interpoliert.

    Die Interpolation holt Genauigkeit unterhalb der Bin-Breite; ohne sie
    waere die Aufloesung bei ~15 s Aufnahme auf 0.067 Hz begrenzt.
    """
    y = (sig - sig.mean()) * np.hanning(len(sig))
    spec = np.abs(np.fft.rfft(y))
    freq = np.fft.rfftfreq(len(sig), 1 / fs)
    lo, hi = np.searchsorted(freq, F_LO), np.searchsorted(freq, F_HI)
    k = lo + int(np.argmax(spec[lo:hi]))
    a, b, c = spec[k - 1], spec[k], spec[k + 1]
    return (k + 0.5 * (a - c) / (a - 2 * b + c)) * fs / len(sig)


def bandpass(sig: np.ndarray, fs: float, lo: float, hi: float) -> np.ndarray:
    spec = np.fft.rfft(sig)
    freq = np.fft.rfftfreq(len(sig), 1 / fs)
    spec[(freq < lo) | (freq > hi)] = 0
    return np.fft.irfft(spec, len(sig))


def envelope(band: np.ndarray, fs: float, f0: float) -> np.ndarray:
    """Einhuellende als gleitendes Maximum ueber eine Periode."""
    half = max(1, int(fs / f0 / 2))
    pad = np.pad(np.abs(band), half, mode="edge")
    return np.array([pad[i:i + 2 * half + 1].max() for i in range(len(band))])


def excitation_window(band: np.ndarray, fs: float, f0: float) -> slice:
    """Fenster der freien Ausschwingung finden.

    Vor dem Anstoss steht der Bot still bzw. wird angefasst -- dieser Teil
    traegt kein Signal bei, verschlechtert aber das Verhaeltnis von Nutz- zu
    Stoersignal. Ausgewertet wird ab dem Amplitudenmaximum (dem Anstoss) bis
    zum Ende: genau die freie, ungestoerte Schwingung.
    """
    env = envelope(band, fs, f0)
    start = int(np.argmax(env))
    if len(band) - start < 5 * fs / f0:      # weniger als 5 Perioden uebrig
        return slice(0, len(band))
    return slice(start, len(band))


def damping_ratio(t: np.ndarray, env_a: np.ndarray, omega: float) -> float:
    """Daempfungsgrad aus dem exponentiellen Abfall der Einhuellenden.

    Gueltigkeitspruefung: Klemmt eine Welle, faellt die Amplitude schnell ab
    und die Frequenzmessung wird unbrauchbar. Bei zeta < 0.05 liegt der
    Frequenzfehler durch Daempfung unter 0.13 % -- die gemessene Frequenz
    ist dann die ungedaempfte Eigenfrequenz.
    """
    good = env_a > env_a.max() * 0.15
    if good.sum() < 5:
        return float("nan")
    slope = np.polyfit(t[good], np.log(env_a[good]), 1)[0]
    return float(-slope / omega)


def rolling_correction(p_roll: float, l_m: float, r_m: float = SHAFT_RADIUS_M) -> float:
    """Abrollen der Welle auf flacher Auflage herausrechnen.

    Die Welle rollt, statt um ihre Achse zu drehen. Momentane Drehachse ist
    die Beruehrlinie, r unter der Wellenmitte. Lagrange mit x_c = -r*th +
    d*sin(th), y_c = -d*cos(th) liefert fuer kleine Auslenkungen

        w_roll^2  = m*g*d / (J_c + m*(d-r)^2)
        w_achse^2 = m*g*d / (J_c + m*d^2)

    J_c eliminiert:  w_achse^2 = g*d / (g*d/w_roll^2 + 2*d*r - r^2)

    Das rollende Pendel schwingt SCHNELLER (kleinerer effektiver Hebel), der
    gemessene Pol ist also zu hoch. Die Korrektur ist mit rund -2 %
    praktisch unabhaengig von d.
    """
    gd = G_M_S2 * l_m
    return float(np.sqrt(gd / (gd / p_roll**2 + 2 * l_m * r_m - r_m**2)))


# ============================================================
# Auswertung eines Videos
# ============================================================

def analyse_video(path: str, t_end: float | None):
    t = read_timestamps(path)
    cx, ang, npx = track_plate(path)
    n = min(len(t), len(cx))
    t, cx, ang, npx = t[:n], cx[:n], ang[:n], npx[:n]

    dt = np.diff(t)
    fs = 1.0 / dt.mean()
    vfr = dt.std() * 1000 > 0.5

    ok = ~np.isnan(cx) & (t > 0.3)
    if t_end is not None:
        ok &= t < t_end
    grid = np.arange(t[ok][0], t[ok][-1], 1 / fs)

    res = {"path": path, "t": t, "cx": cx, "ang": ang, "npx": npx,
           "fs": fs, "vfr": vfr, "dt_std_ms": dt.std() * 1000, "grid": grid,
           "signals": {}}
    for label, sig in (("Schwerpunkt", cx), ("Winkel", ang)):
        y = np.interp(grid, t[ok], sig[ok])
        band = bandpass(y - y.mean(), fs, F_LO, F_HI)

        # Erste Schaetzung auf dem Gesamtsignal, nur um das Fenster zu finden
        win = excitation_window(band, fs, dominant_frequency(y, fs))
        # Endgueltige Schaetzung auf der freien Ausschwingung
        f = dominant_frequency(y[win], fs)
        env = envelope(band[win], fs, f)
        ts = (grid[win] - grid[win.start]) if win.start else grid - grid[0]

        res["signals"][label] = {
            "y": y, "band": band, "f": f, "win": win,
            "t_anstoss": grid[win.start] - grid[0],
            "n_perioden": (len(band[win]) / fs) * f,
            "zeta": damping_ratio(ts, env, 2 * np.pi * f),
        }
    return res


# ============================================================
# Abbildungen
# ============================================================

def plot_swing(results: list, out_path: str):
    fig, axes = plt.subplots(len(results), 2, figsize=(13, 4 * len(results)), squeeze=False)
    for row, r in enumerate(results):
        name = r["path"].split("/")[-1]
        s = r["signals"]["Schwerpunkt"]
        ts = r["grid"] - r["grid"][0]

        ax = axes[row][0]
        ax.plot(ts, s["y"] - s["y"].mean(), lw=0.8, color="#888",
                label="Rohsignal (mit Abrolldrift)")
        ax.plot(ts, s["band"], lw=1.2, color="#0057b7",
                label=f"bandpass {F_LO}-{F_HI} Hz")
        ax.axvline(s["t_anstoss"], color="#2ca02c", lw=1.5,
                   label=f"Anstoss, ab hier ausgewertet ({s['n_perioden']:.0f} Perioden)")
        ax.axvspan(0, s["t_anstoss"], color="#2ca02c", alpha=0.07)
        ax.set_xlabel("Zeit [s]")
        ax.set_ylabel("Plattenschwerpunkt x [px]")
        ax.set_title(f"{name}\nZeitverlauf  (zeta = {s['zeta']:.3f})")
        ax.legend(fontsize=8)
        ax.grid(alpha=0.3)

        ax = axes[row][1]
        y = s["y"][s["win"]]
        spec = np.abs(np.fft.rfft((y - y.mean()) * np.hanning(len(y)))) * 2 / len(y)
        freq = np.fft.rfftfreq(len(y), 1 / r["fs"])
        ax.semilogy(freq, np.maximum(spec, 1e-4), lw=1.0, color="#0057b7")
        f0 = s["f"]
        ax.axvline(f0, color="#d62728", ls="--", lw=1.2,
                   label=f"Grundschwingung {f0:.3f} Hz")
        ax.axvline(2 * f0, color="#ff7f0e", ls=":", lw=1.2,
                   label=f"2. Harmonische {2*f0:.2f} Hz")
        ax.axvline(r["fs"] / 2, color="k", ls="-.", lw=1.0,
                   label=f"Nyquist {r['fs']/2:.1f} Hz")
        ax.axvspan(0, 0.3, color="grey", alpha=0.15)
        ax.text(0.03, 0.06, "Abrolldrift", transform=ax.transAxes, fontsize=7, color="#555")
        ax.set_xlabel("Frequenz [Hz]")
        ax.set_ylabel("Amplitude [px]")
        ax.set_title("Spektrum\nHarmonische belegt: Grundschwingung, kein Oberton")
        ax.legend(fontsize=8)
        ax.grid(alpha=0.3, which="both")
    fig.tight_layout()
    fig.savefig(out_path, dpi=130)
    print(f"Abbildung geschrieben: {out_path}")


def main():
    ap = argparse.ArgumentParser(description="Schwingversuch auswerten (Phase 4, Messung 3)")
    ap.add_argument("--videos", nargs="+", required=True, help="Videodateien des Schwingversuchs")
    ap.add_argument("--t-end", type=float, default=None,
                    help="Auswertung bei dieser Sekunde abschneiden (bevor die Hand eingreift)")
    ap.add_argument("--L-mm", type=float, default=9.0,
                    help="CoG-Hoehe [mm] fuer die Abrollkorrektur (Default 9, CAD-Prior)")
    ap.add_argument("--out", default="messungen/results/phase4_swing.png")
    args = ap.parse_args()

    results = [analyse_video(v, args.t_end) for v in args.videos]

    print("=== Zeitbasis ===")
    for r in results:
        print(f"  {r['path'].split('/')[-1]}: {len(r['t'])} Frames, {r['fs']:.3f} fps, "
              f"dt-Streuung {r['dt_std_ms']:.3f} ms -> {'VFR!' if r['vfr'] else 'konstant'}")

    print("\n=== Einzelschaetzungen ===")
    est = []
    for r in results:
        for label, s in r["signals"].items():
            est.append(s["f"])
            print(f"  {r['path'].split('/')[-1]:34s} {label:12s} f = {s['f']:.4f} Hz   "
                  f"zeta = {s['zeta']:.4f}   Anstoss bei {s['t_anstoss']:.1f} s, "
                  f"{s['n_perioden']:.0f} Perioden")

    f = float(np.mean(est))
    sd = float(np.std(est))
    p_roll = 2 * np.pi * f
    p = rolling_correction(p_roll, args.L_mm / 1000.0)
    t2 = np.log(2) / p
    print("\n=== Ergebnis ===")
    print(f"  f  = {f:.3f} +- {sd:.3f} Hz  ({sd/f*100:.1f} %, {len(est)} Schaetzungen)")
    print(f"  T  = {1/f:.4f} s")
    print(f"  p (gemessen, rollend) = {p_roll:.2f} 1/s")
    print(f"  p (auf Achse korrigiert, L={args.L_mm:.0f} mm) = {p:.2f} 1/s  "
          f"({(p/p_roll-1)*100:+.1f} %)")
    print(f"  t2 = {t2*1000:.1f} ms = {t2/0.010:.1f} Abtastschritte bei 10 ms")
    print(f"\n  -> system_id.py --L-mm <Messung> --pole {p:.1f}")

    plot_swing(results, args.out)


if __name__ == "__main__":
    main()
