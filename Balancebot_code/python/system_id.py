"""
system_id.py -- BalanceBot: Systemmodell und Regler-Startwerte (Phase 5)

Berechnet aus den physikalischen Parametern:
  1. Eigenfrequenz omega_0 des inversen Pendels
  2. Linearisiertes Zustandsraummodell (A, B) fuer [theta, theta_dot]
  3. Offene-Kreis-Eigenwerte (ein instabiler Pol erwartet)
  4. PD-Startwerte fuer die Firmware (Kp, Kd in Duty%/Grad-Einheiten)
     per Polvorgabe (Daempfung zeta, Bandbreite omega_c = k * omega_0)

Benutzung:
    python python/system_id.py                       # mit CAD-Prior L = 8.6 mm
    python python/system_id.py --L-mm 12.5           # Koerper-L direkt vorgeben
    # Nach Knife-Edge-Messung (Phase 4, misst GESAMT-CoM inkl. Raeder):
    python python/system_id.py --total-com-mm 6.2 --com-offset-mm -1.0

Alle Formeln mit Parametertabellen: dokumentation/auslegung/system_model.md
"""

import argparse

import numpy as np

# ============================================================
# Parameter (Quelle: Messung / Datenblatt / CAD)
# ============================================================

# Mechanik
TOTAL_MASS_KG   = 0.190    # gewogen 2026-08-09, inkl. Raeder (vorher 0.204)
WHEEL_MASS_KG   = 0.044    # gewogen 2026-08-09, beide Raeder zusammen.
                           # CAD sagte 2 x 33.65 = 67.3 g -- die alte Baugruppe
                           # ist hier deutlich zu schwer, deshalb nur wiegen.
WHEEL_RADIUS_M  = 0.045
G_M_S2          = 9.81

# CoG-Hoehe des KOERPERS (ohne Raeder) ueber der Achse.
# CAD-Prior 2026-04-12 (ohne Kabel/Schrauben, ~50 g fehlen): 8.6 mm
# --> Nach Knife-Edge-Messung (Phase 4) per --L-mm ueberschreiben!
DEFAULT_L_MM    = 8.6

# Motor/Treiber (Herleitung siehe dokumentation/auslegung/system_model.md)
KT_EFF_NM_A     = 0.0215   # Drehmomentkonstante nach Getriebe [N*m/A]
RA_OHM          = 11.65    # Ankerwiderstand [Ohm]
N_MOTORS        = 2
DEFAULT_VBAT_V  = 3.7      # nominale Akkuspannung [V]

# Regelung
LOOP_PERIOD_MS  = 10.0     # Abtastperiode der Firmware (config.h LOOP_PERIOD_MS)

# Bekannte Totzeitanteile der Regelkette [ms]:
#   Abtastung 10.0 (LOOP_PERIOD_MS) + Halteglied 5.0 (halbe Periode)
#   + I2C-Verkehr 6.4 (Phase-1-Messung, Mittelwert)
# Die interne Fusionsverzoegerung des BNO055 kommt obendrauf und ist nicht
# vermessen -- der reale Wert liegt also ueber diesem Default.
DEFAULT_DELAY_MS = 21.4

# Regelziel
ZETA            = 0.7      # Daempfungsgrad der Sollpole
BW_FACTOR       = 2.0      # omega_c = BW_FACTOR * omega_0
MAX_DUTY        = 45       # Firmware-Grenze [%]


def build_model(l_m: float, vbat: float, pole: float = None):
    """Vereinfachtes 2-Zustands-Modell [theta, theta_dot], Eingang duty%.

    Koerper als Pendel um die Radachse:
      J_b * theta_dd = m_b*g*L*theta - tau      (linearisiert, tau = Radmoment)
    Duty -> Moment (Stall-Naeherung, omega ~ 0 beim Balancieren):
      tau(duty%) = N * Kt_eff * (duty/100 * vbat) / Ra

    J_b kommt aus einer von zwei Quellen:

    a) pole gegeben (Schwingversuch, Phase 4 Messung 3) -- der bevorzugte Weg.
       Haengender und aufrechter Bot haben denselben |Eigenwert|, also gilt
       J = m_b*g*L / p^2 mit dem gemessenen p. Keine Annahme noetig.

    b) pole = None -- Rueckfall auf die Punktmasse-Naeherung 1.2*m*L^2.
       ACHTUNG: Die unterschaetzt J erheblich, sobald Masse weit von der
       Achse sitzt (2026-08-09 am Bot gemessen: Faktor ~6 zu klein).
    """
    m_body = TOTAL_MASS_KG - WHEEL_MASS_KG

    if pole is not None:
        j_body = m_body * G_M_S2 * l_m / pole**2
    else:
        j_body = 1.2 * m_body * l_m**2      # Punktmasse + 20% Verteilungszuschlag

    tau_per_duty = N_MOTORS * KT_EFF_NM_A * (vbat / 100.0) / RA_OHM  # [N*m / %]
    b = tau_per_duty / j_body               # [rad/s^2 pro Duty-%]

    a21 = m_body * G_M_S2 * l_m / j_body    # = p^2

    # Bandbreitenbezug: der tatsaechliche instabile Pol, nicht sqrt(g/L).
    # Bei gemessenem J fallen die beiden ohnehin zusammen (a21 = p^2).
    omega0 = np.sqrt(a21)

    A = np.array([[0.0, 1.0],
                  [a21, 0.0]])
    B = np.array([[0.0],
                  [-b]])                    # positives Duty faehrt vorwaerts,
                                            # wirkt negativ auf theta_dd
    return A, B, omega0, b, m_body, j_body


def pd_gains(a21: float, b: float, omega0: float):
    """PD-Startwerte per Polvorgabe.

    Geschlossener Kreis mit duty = Kp*e + Kd*de (e = -theta):
      theta_dd = (a21 - b*Kp_rad)*theta - b*Kd_rad*theta_dot
    Sollpolynom: s^2 + 2*zeta*omega_c*s + omega_c^2
    """
    omega_c = BW_FACTOR * omega0
    kp_rad = (a21 + omega_c**2) / b          # [%/rad]
    kd_rad = 2.0 * ZETA * omega_c / b        # [%/(rad/s)]
    deg = np.pi / 180.0
    return kp_rad * deg, kd_rad * deg, omega_c


def _bisect(f, lo: float, hi: float, n: int = 200) -> float:
    """Nullstelle durch Intervallhalbierung -- vermeidet eine scipy-Abhaengigkeit."""
    f_lo = f(lo)
    for _ in range(n):
        mid = 0.5 * (lo + hi)
        f_mid = f(mid)
        if (f_lo < 0) == (f_mid < 0):
            lo, f_lo = mid, f_mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def critical_delay(a21: float, b: float, kp_deg: float, kd_deg: float):
    """Kleinste Totzeit, bei der der geschlossene Kreis marginal stabil wird.

    Das Modell in build_model() kennt keine Totzeit. Die reale Kette hat aber
    welche: Abtastung, Halteglied, I2C-Verkehr und die interne Fusion des
    BNO055. Totzeit dreht Phase, und weil die Strecke einen instabilen Pol
    hat, ist die Phasenreserve von vornherein knapp.

    Charakteristische Gleichung mit Totzeit T:
        s^2 - a21 + b*(Kp_rad + Kd_rad*s) * exp(-s*T) = 0

    Marginal stabil heisst s = j*w. Aufgeteilt nach Real- und Imaginaerteil:
        Im:  Kd_rad*w*cos(w*T) - Kp_rad*sin(w*T) = 0   ->  w*T = atan(Kd_rad*w/Kp_rad)
        Re: -w^2 - a21 + b*(Kp_rad*cos(w*T) + Kd_rad*w*sin(w*T)) = 0

    Die erste Gleichung liefert die Phase, Einsetzen in die zweite ergibt eine
    Gleichung allein in w. Rueckgabe: (T_krit [s], Schwingfrequenz [Hz]).
    """
    deg = np.pi / 180.0
    kp, kd = kp_deg / deg, kd_deg / deg

    def residual(w):
        phase = np.arctan2(kd * w, kp)
        return -w * w - a21 + b * (kp * np.cos(phase) + kd * w * np.sin(phase))

    w = _bisect(residual, 1.0, 600.0)
    return float(np.arctan2(kd * w, kp) / w), float(w / (2 * np.pi))


def main():
    p = argparse.ArgumentParser(description="BalanceBot Systemmodell")
    p.add_argument("--L-mm", type=float, default=None,
                   help=f"Koerper-CoG-Hoehe ueber Achse [mm] (Default: CAD-Prior {DEFAULT_L_MM})")
    p.add_argument("--total-com-mm", type=float, default=None,
                   help="Knife-Edge-Messung 1: Hoehe des GESAMT-CoM (inkl. Raeder) "
                        "ueber der Achse [mm] -- wird auf Koerper-L umgerechnet")
    p.add_argument("--com-offset-mm", type=float, default=None,
                   help="Knife-Edge-Messung 2: Vor/Zurueck-Offset des Gesamt-CoM "
                        "[mm], positiv = Richtung USB -- liefert Sp-Vorhersage")
    p.add_argument("--vbat", type=float, default=DEFAULT_VBAT_V,
                   help=f"Akkuspannung [V] (Default {DEFAULT_VBAT_V})")
    p.add_argument("--pole", type=float, default=None,
                   help="Gemessener instabiler Pol [1/s] aus dem Schwingversuch "
                        "(Phase 4 Messung 3): p = 2*pi/T. Ersetzt die "
                        "Punktmasse-Schaetzung fuer J -- dringend empfohlen.")
    p.add_argument("--period", type=float, default=None,
                   help="Alternative zu --pole: gemessene Schwingungsdauer T [s]")
    p.add_argument("--delay-ms", type=float, default=DEFAULT_DELAY_MS,
                   help=f"Angenommene Totzeit der Regelkette [ms] (Default {DEFAULT_DELAY_MS}: "
                        "Abtastung 10 + Halteglied 5 + I2C 6.4)")
    args = p.parse_args()

    pole = args.pole
    if pole is None and args.period is not None:
        pole = 2.0 * np.pi / args.period

    # Koerper-L bestimmen: direkte Vorgabe > Knife-Edge-Umrechnung > CAD-Prior.
    # Umrechnung: Raeder sitzen exakt auf Achshoehe, tragen also nichts zur
    # CoM-Hoehe bei -> h_body = h_total * m_total / m_body (gilt genauso
    # fuer den Vor/Zurueck-Offset).
    m_body_g   = (TOTAL_MASS_KG - WHEEL_MASS_KG) * 1000.0
    mass_ratio = TOTAL_MASS_KG * 1000.0 / m_body_g

    if args.L_mm is not None:
        l_mm = args.L_mm
        l_source = "direkt vorgegeben"
    elif args.total_com_mm is not None:
        l_mm = args.total_com_mm * mass_ratio
        l_source = (f"Knife-Edge: {args.total_com_mm:.1f} mm Gesamt-CoM "
                    f"x {mass_ratio:.3f} (Massenverhaeltnis)")
    else:
        l_mm = DEFAULT_L_MM
        l_source = "CAD-Prior (Raeder herausgerechnet)"

    l_m = l_mm / 1000.0
    A, B, omega0, b, m_body, j_body = build_model(l_m, args.vbat, pole)
    eigvals = np.linalg.eigvals(A)
    ctrb = np.hstack([B, A @ B])
    kp_deg, kd_deg, omega_c = pd_gains(A[1, 0], -B[1, 0], omega0)

    print("=== BalanceBot Systemmodell ===")
    print(f"L (Koerper-CoG ueber Achse) : {l_mm:.1f} mm  ({l_source})")
    print(f"Koerpermasse                : {m_body*1000:.1f} g")
    j_src = ("aus gemessenem Pol" if pole is not None
             else "GESCHAETZT 1.2*m*L^2 -- Schwingversuch machen!")
    print(f"J_koerper (um Achse)        : {j_body*1e7:.0f} g*cm^2 = {j_body:.2e} kg*m^2  ({j_src})")
    print(f"Traegheitsradius sqrt(J/m)  : {1000*np.sqrt(j_body/m_body):.1f} mm")
    print(f"omega_0                     : {omega0:.1f} rad/s  ({omega0/(2*np.pi):.2f} Hz)")
    print(f"Stellwirkung b              : {b:.1f} (rad/s^2 pro Duty-%)")
    print()
    print(f"Offene-Kreis-Eigenwerte     : {eigvals[0]:+.1f}, {eigvals[1]:+.1f}  "
          f"(instabiler Pol: {max(eigvals.real):+.1f}) ")
    print(f"Steuerbarkeitsmatrix Rang   : {np.linalg.matrix_rank(ctrb)} von 2")

    # Zeitmasse des instabilen Pols. Zeitkonstante und Verdopplungszeit
    # unterscheiden sich um ln2 -- nicht verwechseln (siehe dokumentation/auslegung/system_model.md).
    pole = max(eigvals.real)
    print(f"Zeitkonstante 1/p           : {1000/pole:.0f} ms  (Faktor e)")
    print(f"Verdopplungszeit ln2/p      : {1000*np.log(2)/pole:.0f} ms  "
          f"= {np.log(2)/pole/(LOOP_PERIOD_MS/1000):.1f} Abtastschritte bei "
          f"{LOOP_PERIOD_MS:.0f} ms Takt")
    print()
    print(f"=== PD-Startwerte (zeta={ZETA}, omega_c={BW_FACTOR}*omega_0={omega_c:.0f} rad/s) ===")
    print(f"Kp = {kp_deg:.2f}  [Duty%/Grad]")
    print(f"Kd = {kd_deg:.3f} [Duty%/(Grad/s)]")
    print(f"Saettigungswinkel bei Kp    : {MAX_DUTY/kp_deg:.1f} Grad (Duty {MAX_DUTY}%)")

    # --- Totzeitpruefung -------------------------------------------------
    # Die Polvorgabe oben rechnet OHNE Totzeit. Am Geraet entscheidet sie
    # aber darueber, ob der Entwurf haelt (Phase-6-Versuch 2026-08-10).
    t_crit, f_osz = critical_delay(A[1, 0], -B[1, 0], kp_deg, kd_deg)
    t_have = args.delay_ms / 1000.0
    print()
    print("=== Totzeitpruefung (das Modell oben rechnet ohne Totzeit) ===")
    print(f"kritische Totzeit dieses Entwurfs : {t_crit*1000:.1f} ms "
          f"-> Grenzzyklus bei {f_osz:.2f} Hz")
    print(f"angenommene Totzeit der Kette     : {args.delay_ms:.1f} ms")
    print(f"Reserve                           : {(t_crit-t_have)*1000:+.1f} ms "
          f"(Faktor {t_crit/t_have:.2f})")
    if t_crit < t_have * 1.5:
        print("WARNUNG: zu wenig Reserve. Der Entwurf schwingt am Geraet.")
        print("         Kp senken, bis die kritische Totzeit rund doppelt so")
        print("         gross ist wie die angenommene. Kd dabei NICHT erhoehen --")
        print("         mehr D-Anteil senkt die kritische Totzeit zusaetzlich.")
    print(f"Stabilisierbarkeitsgrenze p*T < 1 : p*T = {pole*t_have:.2f} "
          f"(T_max = 1/p = {1000/pole:.0f} ms)")

    # Setpoint-Vorhersage aus dem Vor/Zurueck-Offset (Knife-Edge-Messung 2):
    # Liegt der Koerper-CoG um y vor (+) der Achse, muss der Bot um
    # atan(y/L) nach HINTEN lehnen (interne Konvention: positiv), damit
    # der CoG ueber der Achse steht. Das ist der "Sp="-Startwert und
    # erklaert das beobachtete Wegfahren bei Sp=0.
    if args.com_offset_mm is not None:
        y_body_mm = args.com_offset_mm * mass_ratio
        sp_deg = np.degrees(np.arctan2(y_body_mm, l_mm))
        print()
        print("=== Setpoint-Vorhersage (Gleichgewichts-Trim) ===")
        print(f"Koerper-CoG-Offset          : {y_body_mm:+.1f} mm "
              f"(aus Messung {args.com_offset_mm:+.1f} mm x {mass_ratio:.3f})")
        print(f"Sp-Startwert                : Sp={sp_deg:+.1f}  [Grad, "
              f"positiv = lehnt rueckwaerts]")
        print("Vorzeichen am Geraet verifizieren: Bot muss im Gleichgewicht")
        print("leicht in Richtung des CoG-Offsets lehnen.")

    print()
    print("Einschraenkungen des Modells:")
    print(" - Stall-Naeherung (Gegen-EMK vernachlaessigt), Totzone nicht modelliert")
    print(" - Radtraegheit/Translation vereinfacht -> Werte sind STARTPUNKTE,")
    print("   Feintuning am Geraet per Serial (Kp=/Kd=/Sp=)")


if __name__ == "__main__":
    main()
