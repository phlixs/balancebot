"""
cog_measurement_sketch.py -- BalanceBot: Skizze zur CoG-Hoehenmessung (Phase 4, Messung 1)

Erzeugt die Abbildung, die im Inbetriebnahmeplan das Messverfahren fuer L
erklaert -- die Hoehe des Koerperschwerpunkts ueber der Radachse.

Warum NICHT die klassische Schneidenmethode: Der Bot hat keine ausgedehnte
Flaeche senkrecht zu y. Das breiteste Bauteil ist die Rahmenplatte, und ihre
Kante ist nur so dick wie die Platte (~3 mm). Stellt man den Bot darauf, reicht
die Auflage in z-Richtung nur ueber diese 3 mm, waehrend der Schwerpunkt bei
etwa 9 mm liegt -- also ausserhalb. Der Bot kippt zwangslaeufig um und kann
dort gar nicht erst stehen (Panel 3).

Stattdessen Auslenkungsmethode: Der Bot haengt an den Motorwellen wie beim
Schwingversuch, eine bekannte Masse an bekanntem Hebel dreht ihn um phi.

Benutzung:
    python python/cog_measurement_sketch.py --out messungen/results/phase4_cog_messung_skizze.png
"""

import argparse

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Arc, FancyArrowPatch, Polygon, Rectangle  # noqa: E402

# Schematische Bauteillagen ueber der Radachse [mm]: (Name, z0, z1, Breite in y).
STACK = [
    ("Motoren", -20, -7, 62, "#9e9e9e"),
    ("Akku", -13, 0, 74, "#4caf50"),
    ("Rahmenplatte", 0, 6, 104, "#1f5fbf"),
    ("Motor Carrier", 6, 22, 84, "#2f7d32"),
    ("Nano", 22, 42, 46, "#424242"),
]
L_SHOWN = 9.0      # erwarteter Messwert, rein illustrativ
PHI_DEG = 43.0     # Auslenkung bei ca. 25 g an der Plattenkante
Y_P, Z_P = 52.0, 3.0   # Anhaengepunkt: Kante der Rahmenplatte

C_Z, C_Y, C_X = "#d62728", "#1f77b4", "#2ca02c"
C_MEAS, C_CoG = "#7b1fa2", "#ef6c00"


def rot(phi_deg: float):
    """Einheitsvektoren der Botachsen in Weltkoordinaten bei Auslenkung phi.

    Bei phi = 0 haengt der Bot mit +z senkrecht nach unten.
    """
    p = np.radians(phi_deg)
    return np.array([np.cos(p), -np.sin(p)]), np.array([-np.sin(p), -np.cos(p)])


def draw_stack(ax, upright: bool = True, phi: float | None = None, labels: bool = True):
    y_hat, z_hat = rot(phi) if phi is not None else (np.array([1.0, 0.0]),
                                                    np.array([0.0, 1.0]))
    for name, z0, z1, width, color in STACK:
        if phi is None and upright:
            ax.add_patch(Rectangle((-width / 2, z0), width, z1 - z0, facecolor=color,
                                   edgecolor="k", lw=0.8, alpha=0.9, zorder=2))
            if labels:
                ax.text(width / 2 + 4, (z0 + z1) / 2, name, fontsize=7.5,
                        ha="left", va="center", color="#333", zorder=3)
        elif phi is None:                      # 90 Grad gekippt, z waagerecht
            ax.add_patch(Rectangle((z0, -width / 2), z1 - z0, width, facecolor=color,
                                   edgecolor="k", lw=0.8, alpha=0.9, zorder=2))
        else:
            corners = [(-width / 2, z0), (width / 2, z0), (width / 2, z1), (-width / 2, z1)]
            pts = np.array([y * y_hat + z * z_hat for y, z in corners])
            ax.add_patch(Polygon(pts, facecolor=color, edgecolor="k", lw=0.8,
                                 alpha=0.9, zorder=2))


def mark_axle(ax, pos=(0, 0)):
    ax.plot(*pos, "o", ms=14, mfc="#ffd400", mec="k", mew=1.6, zorder=6)
    ax.plot(*pos, "x", ms=8, color="k", mew=1.6, zorder=7)


def panel_axes(ax):
    ax.set_title("1 — Achsen am aufrechten Bot", fontsize=11.5, fontweight="bold", pad=14)
    draw_stack(ax)
    mark_axle(ax)
    ax.annotate("", xy=(0, 74), xytext=(0, 48),
                arrowprops=dict(arrowstyle="-|>", lw=2.4, color=C_Z))
    ax.text(6, 63, "z  Hochachse\n(Achse → Nano)", fontsize=9, color=C_Z, va="center")
    ax.annotate("", xy=(86, -34), xytext=(26, -34),
                arrowprops=dict(arrowstyle="-|>", lw=2.4, color=C_Y))
    ax.text(56, -41, "y  Fahrtrichtung", fontsize=9, color=C_Y, ha="center", va="top")
    ax.plot(-64, -34, "o", ms=13, mfc="w", mec=C_X, mew=2.4, zorder=5)
    ax.plot(-64, -34, "o", ms=4.5, color=C_X, zorder=6)
    ax.text(-64, -43, "x  Radachse\n(aus dem Bild)", fontsize=9, color=C_X,
            ha="center", va="top")
    ax.text(0, -62, "L = Höhe des Schwerpunkts über der Achse,\nalso entlang z. Das ist der gesuchte Wert.",
            fontsize=8.5, ha="center", va="top", style="italic", color="#333")
    ax.set_xlim(-105, 118)
    ax.set_ylim(-80, 84)


def panel_tilt(ax):
    ax.set_title("2 — Messung: Auslenkung am hängenden Bot  ✔ empfohlen",
                 fontsize=11.5, fontweight="bold", pad=14, color="#1b5e20")
    y_hat, z_hat = rot(PHI_DEG)

    # Pfeiler (steht hinter dem Bot, deshalb blass)
    ax.add_patch(Rectangle((-30, -150), 60, 150, facecolor="#d5d5d5",
                           edgecolor="#888", lw=1.0, zorder=0))
    ax.text(0, -158, "Pfeiler (flache Oberseite)", fontsize=8, ha="center", va="top")
    draw_stack(ax, phi=PHI_DEG)
    mark_axle(ax)

    # Lot und Botachse
    ax.plot([0, 0], [8, -140], ls=(0, (5, 4)), color="#555", lw=1.3, zorder=3)
    ax.text(3, -104, "Lot", fontsize=8.5, color="#555")
    tip = 78 * z_hat
    ax.plot([0, tip[0]], [0, tip[1]], ls=(0, (5, 4)), color=C_Z, lw=1.6, zorder=3)
    ax.text(tip[0] - 5, tip[1] - 5, "z", fontsize=12, color=C_Z, ha="right", va="top")
    ax.add_patch(Arc((0, 0), 132, 132, theta1=270 - PHI_DEG, theta2=270,
                     color=C_MEAS, lw=2.6, zorder=5))
    ax.text(-22, -76, "φ", fontsize=18, fontweight="bold", color=C_MEAS)

    cog = L_SHOWN * z_hat
    ax.plot(*cog, "*", ms=17, mfc=C_CoG, mec="k", mew=0.8, zorder=8)
    ax.annotate("Schwerpunkt\n(Abstand L)", xy=tuple(cog), xytext=(-92, -34),
                fontsize=8.5, color=C_CoG, ha="center",
                arrowprops=dict(arrowstyle="->", color=C_CoG, lw=1.2))

    # Zusatzmasse an der Plattenkante
    p = Y_P * y_hat + Z_P * z_hat
    ax.plot([p[0], p[0]], [p[1], p[1] - 46], color="k", lw=1.4, zorder=6)
    ax.plot(p[0], p[1] - 55, "o", ms=18, mfc="#616161", mec="k", zorder=7)
    ax.annotate("bekannte Masse m_a,\nangehängt an der Plattenkante\n(Hebel y_p, Höhe z_p)",
                xy=(p[0], p[1] - 55), xytext=(p[0] + 56, p[1] - 92),
                fontsize=8.5, ha="center", color="#333",
                arrowprops=dict(arrowstyle="->", color="#333", lw=1.2))

    ax.text(-130, 84, "tan φ = m_a·y_p / (m·L + m_a·z_p)\n\n"
                      "→   L = m_a·(y_p/tan φ − z_p) / m",
            fontsize=11, family="monospace", color=C_MEAS, va="top",
            bbox=dict(boxstyle="round,pad=0.45", fc="#f3e5f5", ec=C_MEAS, lw=1.2))
    ax.text(-138, -78, "φ aus einem Foto messen —\ngenau wie bei der Ruhelage,\n"
                       "Pfeilerkante als Lot.\n\n25–30 g ergibt φ ≈ 45°:\n"
                       "der genaueste Bereich.\n\nGenauigkeit ≈ 2 % auf L.",
            fontsize=8.5, va="top", color="#333")
    ax.set_xlim(-146, 152)
    ax.set_ylim(-176, 108)


def panel_why_not(ax):
    ax.set_title("3 — Warum die klassische Schneidenmethode an diesem Bot NICHT geht",
                 fontsize=11.5, fontweight="bold", pad=14, color="#b71c1c")
    draw_stack(ax, upright=False)
    mark_axle(ax)
    ax.plot([-40, 70], [-52, -52], color="k", lw=2.4)
    ax.text(68, -57, "Tisch", fontsize=8, ha="right", va="top")

    ax.plot([0, 6], [-52, -52], color="#b71c1c", lw=7, solid_capstyle="butt", zorder=5)
    ax.annotate("Auflage = Kante der Rahmenplatte,\nnur ~3 mm breit in z",
                xy=(3, -54), xytext=(-66, -78), fontsize=8.5, color="#b71c1c",
                ha="left", arrowprops=dict(arrowstyle="->", color="#b71c1c", lw=1.3))

    ax.plot(L_SHOWN, 0, "*", ms=17, mfc=C_CoG, mec="k", mew=0.8, zorder=8)
    ax.plot([L_SHOWN, L_SHOWN], [0, -52], ls=(0, (4, 3)), color=C_CoG, lw=1.6)
    ax.annotate("Schwerpunkt bei z ≈ 9 mm —\nsein Lot fällt NEBEN die Auflage",
                xy=(L_SHOWN, -46), xytext=(58, -92), fontsize=8.5, color=C_CoG,
                ha="left", arrowprops=dict(arrowstyle="->", color=C_CoG, lw=1.3))
    ax.add_patch(FancyArrowPatch((30, 34), (58, 14), arrowstyle="-|>",
                                 mutation_scale=17, lw=2.4, color="#b71c1c",
                                 connectionstyle="arc3,rad=-0.35"))
    ax.text(62, 22, "kippt zwangsläufig um", fontsize=10, color="#b71c1c",
            fontweight="bold", va="center")
    ax.text(24, -118, "Der Bot hat keine ausgedehnte Fläche senkrecht zu y. Ein Balancieren auf der\n"
                      "Plattenkante ist deshalb nicht nur instabil, sondern geometrisch unmöglich.",
            fontsize=8.5, ha="center", va="top", style="italic", color="#333")
    ax.set_xlim(-70, 176)
    ax.set_ylim(-142, 62)


def main():
    ap = argparse.ArgumentParser(description="Skizze zur CoG-Hoehenmessung")
    ap.add_argument("--out", default="messungen/results/phase4_cog_messung_skizze.png")
    args = ap.parse_args()

    fig = plt.figure(figsize=(15, 10.5))
    gs = fig.add_gridspec(2, 2, width_ratios=[1, 1.5], height_ratios=[1.35, 1],
                          hspace=0.26, wspace=0.06)
    panel_axes(fig.add_subplot(gs[0, 0]))
    panel_tilt(fig.add_subplot(gs[0, 1]))
    panel_why_not(fig.add_subplot(gs[1, :]))
    for ax in fig.axes:
        ax.set_aspect("equal")
        ax.axis("off")
    fig.suptitle("Phase 4 — Messung der CoG-Höhe L   (schematisch, nicht maßstäblich)",
                 fontsize=13.5, fontweight="bold")
    fig.savefig(args.out, dpi=140, bbox_inches="tight", facecolor="w")
    print(f"Abbildung geschrieben: {args.out}")


if __name__ == "__main__":
    main()
