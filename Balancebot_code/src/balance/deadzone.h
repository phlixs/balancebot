#pragma once

// ============================================================
// deadzone.h -- BalanceBot: Totzonen-Kompensation (Phase 3)
//
// Hebt zu kleine Duty-Befehle auf den gemessenen Anlaufpunkt an.
// Die Totzone ist je Duty-Vorzeichen verschieden (Asymmetrie im
// Carrier-Treiber, Messung 2026-08-07: positive Seite 23 %,
// negative Seite 16-17 %) -- deshalb getrennte Schwellen und
// Anwendung PRO MOTOR-ANSCHLUSS (nach dem Richtungs-Mapping).
//
// Header-only, ohne Arduino-Abhaengigkeit -- nativ testbar
// (pio test -e native).
// ============================================================

// duty:  gewuenschter Duty am Motor-Anschluss [%]
// dzPos: Anlaufpunkt der positiven Duty-Seite [%]
// dzNeg: Anlaufpunkt der negativen Duty-Seite [%]
inline int compensateDeadzone(int duty, int dzPos, int dzNeg) {
    if (duty == 0) return 0;                          // explizit stoppen
    if (duty > 0 && duty < dzPos)  return dzPos;      // anheben
    if (duty < 0 && duty > -dzNeg) return -dzNeg;     // anheben
    return duty;                                      // stark genug
}
