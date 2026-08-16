#pragma once

// ============================================================
// autoarm.h -- BalanceBot: Auto-Arm-Detektor (Phase A)
//
// Erkennt, wann der Bot bereit zum Balancieren ist: Winkel und
// Winkelgeschwindigkeit muessen ein Stabilitaetsfenster
// (aufrecht + ruhig) ununterbrochen lange genug einhalten.
// Ein Mensch stellt den Bot aufrecht hin -- der Bot armiert selbst.
//
// Header-only, ohne Arduino-Abhaengigkeit -- nativ testbar
// (pio test -e native).
// ============================================================

#include <stdint.h>

class AutoArm {
public:
    AutoArm(float maxAngleDeg, float maxRateDps, unsigned long stableMs)
        : _maxAngleDeg(maxAngleDeg),
          _maxRateDps(maxRateDps),
          _stableMs(stableMs) {}

    // Einmal pro Regelzyklus aufrufen.
    // true sobald das Fenster AUTOARM_STABLE_MS lang gehalten wurde.
    bool update(float pitchDeg, float pitchRateDps, unsigned long nowMs) {
        bool inWindow = (absf(pitchDeg) < _maxAngleDeg) &&
                        (absf(pitchRateDps) < _maxRateDps);
        if (!inWindow) {
            _windowStartMs = 0;
            return false;
        }
        if (_windowStartMs == 0) {
            // 0 ist der Marker fuer "kein Fenster aktiv" -- falls nowMs
            // zufaellig 0 ist, um 1 ms verschieben (Fehler vernachlaessigbar)
            _windowStartMs = (nowMs == 0) ? 1 : nowMs;
        }
        return (nowMs - _windowStartMs) >= _stableMs;
    }

    // Beim Verlassen/Betreten von IDLE aufrufen, damit kein altes
    // Zeitfenster weiterlebt (sonst wuerde sofort armiert).
    void reset() { _windowStartMs = 0; }

private:
    static float absf(float v) { return (v < 0.0f) ? -v : v; }

    float         _maxAngleDeg;
    float         _maxRateDps;
    unsigned long _stableMs;
    unsigned long _windowStartMs = 0;
};
