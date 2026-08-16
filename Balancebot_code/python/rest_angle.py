"""
rest_angle.py -- BalanceBot: Ruhelagenwinkel des haengenden Bots aus einem Foto
(Phase 4, Messung 3a)

Der haengende Bot stellt sich so ein, dass der Schwerpunkt unter der Radachse
steht. Eine 180-Grad-Drehung um die (waagerechte) Radachse bildet eine
waagerechte Ebene wieder auf eine waagerechte ab -- steht die Rahmenplatte im
aufrechten Gleichgewicht waagerecht, dann auch im haengenden. Die gemessene
Abweichung von der Waagerechten ist dann der Gleichgewichts-Trimm.

Zwei Referenzen werden gebraucht, und beide stehen im Bild:
  1. Das Lot: die senkrechten Kanten des Pfeilers, auf dem der Bot liegt.
     Damit faellt ein Rollwinkel der Kamera heraus.
  2. Die Platte selbst: der Pfeiler verdeckt ihre Mitte, ihre beiden Enden
     sind aber frei sichtbar und definieren die Gerade.

Benutzung:
    python python/rest_angle.py ruhelage.jpg --out messungen/results/rest_angle.png

Vorbehalte, die das Verfahren nicht aufloesen kann: dass die Platte in der
Soll-Aufrechtlage wirklich waagerecht steht, und dass die Kamera entlang der
Radachse ausgerichtet war. Der belastbare Ersatz ist die IMU -- Bot haengend
einschalten, hw_check flashen, 'i' druecken, statischen Pitch ablesen; die
Abweichung von 180 Grad ist der Trimm.
"""

import argparse

import matplotlib
import numpy as np
from PIL import Image

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

# Blaumaske wie in swing_analysis.py -- Kanalabstaende statt fester Schwellen
BLUE_VS_RED, BLUE_VS_GREEN, BLUE_MIN = 25, 15, 60
# Pfeiler im Gegenlicht: dunkel und farbneutral
PILLAR_MAX_SAT, PILLAR_MAX_VAL = 18, 70
MIN_ROW_PIXELS = 300


def load(path: str) -> np.ndarray:
    return np.array(Image.open(path).convert("RGB")).astype(int)


def plumb_from_pillar(im: np.ndarray, box: tuple) -> tuple[float, np.ndarray, np.ndarray]:
    """Kamerarollwinkel aus der senkrechten Pfeilerkante.

    Ausgewertet wird die Kante mit dem kleineren Restfehler: Die andere ist
    haeufig durch Schatten oder den Bot selbst gestoert.
    """
    y0, y1, x0, x1 = box
    sat, val = im.max(2) - im.min(2), im.mean(2)
    mask = (sat < PILLAR_MAX_SAT) & (val < PILLAR_MAX_VAL)
    keep = np.zeros_like(mask)
    keep[y0:y1, x0:x1] = True
    mask &= keep

    rows, left, right = [], [], []
    for y in range(y0, y1, 20):
        xs = np.nonzero(mask[y])[0]
        if len(xs) > MIN_ROW_PIXELS:
            rows.append(y)
            left.append(xs.min())
            right.append(xs.max())
    rows = np.array(rows)

    best = None
    for edge in (np.array(left), np.array(right)):
        coef = np.polyfit(rows, edge, 1)
        resid = float((edge - np.polyval(coef, rows)).std())
        cand = (resid, float(np.degrees(np.arctan(coef[0]))), coef, edge)
        if best is None or resid < best[0]:
            best = cand
    resid, tilt, coef, edge = best
    print(f"  Pfeilerkante: Neigung gegen Bildlot {tilt:+.3f} Grad, "
          f"Restfehler {resid:.1f} px ueber {len(rows)} Zeilen")
    return tilt, rows, np.polyval(coef, rows)


def plate_line(im: np.ndarray, band: tuple, drop: tuple | None):
    """Gerade durch die beiden sichtbaren Enden der Rahmenplatte."""
    y0, y1 = band
    r, g, b = im[:, :, 0], im[:, :, 1], im[:, :, 2]
    mask = (b > r + BLUE_VS_RED) & (b > g + BLUE_VS_GREEN) & (b > BLUE_MIN)
    keep = np.zeros_like(mask)
    keep[y0:y1] = True
    mask &= keep
    if drop:                       # Stoerobjekt (blauer Stecker) ausschliessen
        dy, dx = drop
        mask[dy:, dx:] = False

    ys, xs = np.nonzero(mask)
    cols, mids = [], []
    for x in range(xs.min(), xs.max() + 1, 10):
        yy, _ = np.nonzero(mask[:, x:x + 10])
        if len(yy) > 8:
            cols.append(x + 5)
            mids.append(yy.mean())
    cols, mids = np.array(cols), np.array(mids)
    coef = np.polyfit(cols, mids, 1)
    resid = float((mids - np.polyval(coef, cols)).std())
    ang = float(np.degrees(np.arctan(coef[0])))
    print(f"  Rahmenplatte: Neigung gegen Bildhorizontale {ang:+.2f} Grad, "
          f"Restfehler {resid:.1f} px ueber {len(cols)} Stuetzstellen")
    return ang, cols, np.polyval(coef, cols), mask, resid


def main():
    ap = argparse.ArgumentParser(description="Ruhelagenwinkel aus Foto (Phase 4, Messung 3a)")
    ap.add_argument("photo")
    ap.add_argument("--pillar-box", type=int, nargs=4, default=[2300, 3750, 700, 1700],
                    metavar=("Y0", "Y1", "X0", "X1"), help="Suchfenster fuer den Pfeiler")
    ap.add_argument("--plate-band", type=int, nargs=2, default=[2050, 2400],
                    metavar=("Y0", "Y1"), help="Hoehenband der Rahmenplatte")
    ap.add_argument("--drop-below-right", type=int, nargs=2, default=[2200, 1400],
                    metavar=("Y", "X"), help="Bereich rechts-unten verwerfen (blauer Stecker)")
    ap.add_argument("--out", default="messungen/results/rest_angle.png")
    args = ap.parse_args()

    im = load(args.photo)
    print(f"Bild {im.shape[1]}x{im.shape[0]}")
    roll, prows, pfit = plumb_from_pillar(im, tuple(args.pillar_box))
    ang, cols, cfit, mask, resid = plate_line(im, tuple(args.plate_band),
                                              tuple(args.drop_below_right))

    # Reine Bildrotation dreht Senkrechte und Waagerechte gleichsinnig; gemessen
    # als dx/dy bzw. dy/dx bekommen sie entgegengesetztes Vorzeichen.
    true_angle = ang + roll
    print(f"\n=== Rahmenplatte gegen die echte Waagerechte: {true_angle:+.2f} Grad ===")
    print(f"    (Kamerarollwinkel {-roll:+.2f} Grad herausgerechnet)")

    fig, ax = plt.subplots(figsize=(10, 13))
    ax.imshow(im.astype(np.uint8))
    ys, xs = np.nonzero(mask)
    ax.plot(xs, ys, ",", color="#2ca02c", alpha=0.5)
    ax.plot(cols, cfit, "-", color="#2ca02c", lw=2.5, label=f"Rahmenplatte ({ang:+.2f} Grad im Bild)")
    ax.plot(pfit, prows, "-", color="#d62728", lw=2.5, label=f"Pfeilerlot ({roll:+.2f} Grad im Bild)")

    mx, my = cols.mean(), np.polyval(np.polyfit(cols, cfit, 1), cols.mean())
    span = np.array([cols.min() - 150, cols.max() + 150])
    ax.plot(span, my + (span - mx) * np.tan(np.radians(-roll)), "--", color="#ff7f0e", lw=2,
            label="echte Waagerechte (rollkorrigiert)")
    ax.annotate(f"{abs(true_angle):.1f}$\\degree$", xy=(mx, my), xytext=(mx - 700, my - 320),
                fontsize=22, color="#ff7f0e", fontweight="bold",
                arrowprops=dict(arrowstyle="->", color="#ff7f0e", lw=2))
    ax.set_title("Phase 4, Messung 3a — Ruhelage des haengenden Bots\n"
                 f"Rahmenplatte {abs(true_angle):.1f}$\\degree$ gegen die Waagerechte "
                 f"(Fit-Restfehler {resid:.1f} px)", fontsize=12)
    ax.legend(loc="lower left", fontsize=10)
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(args.out, dpi=110)
    print(f"Abbildung geschrieben: {args.out}")


if __name__ == "__main__":
    main()
