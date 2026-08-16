#pragma once

// ============================================================
// safety.h -- BalanceBot: SafetySupervisor (Phase A)
//
// Prueft in jedem BALANCING-Zyklus vier Fehlerklassen:
//   1. Tilt:         |pitch| > Sturzwinkel          --> FALLEN
//   2. Loop-Overrun: Regelzyklus massiv zu lang     --> E_STOP
//   3. IMU-Stale:    Pitch+Rate exakt eingefroren   --> E_STOP
//   4. Saettigung:   |duty| dauerhaft am Maximum    --> FALLEN
//
// FALLEN-Verdikte erlauben Auto-Recovery (Bot wieder aufrichten),
// E_STOP-Verdikte sind Anomalien und verlangen manuellen Reset.
//
// Header-only, ohne Arduino-Abhaengigkeit -- nativ testbar
// (pio test -e native).
// ============================================================

#include <stdint.h>

enum class SafetyVerdict : uint8_t {
    OK,
    FALLEN_TILT,        // Kippwinkel ueberschritten
    FALLEN_SATURATION,  // Stellgroesse dauerhaft am Anschlag, Bot faengt sich nicht
    ESTOP_IMU_STALE,    // IMU liefert eingefrorene Werte
    ESTOP_LOOP_OVERRUN  // Regelzyklus zu lange blind
};

class SafetySupervisor {
public:
    SafetySupervisor(float fallenAngleDeg, int staleCycleLimit,
                     unsigned long overrunMs, int maxDuty,
                     unsigned long saturationTimeoutMs)
        : _fallenAngleDeg(fallenAngleDeg),
          _staleCycleLimit(staleCycleLimit),
          _overrunMs(overrunMs),
          _maxDuty(maxDuty),
          _saturationTimeoutMs(saturationTimeoutMs) {}

    // Einmal pro BALANCING-Zyklus aufrufen, VOR der neuen Stellgroessen-
    // Berechnung. duty ist die zuletzt angewendete Stellgroesse.
    SafetyVerdict check(float pitchDeg, float pitchRateDps,
                        unsigned long elapsedMs, int duty, unsigned long nowMs) {
        // 1. Tilt -- der wichtigste Check zuerst
        if (absf(pitchDeg) > _fallenAngleDeg) return SafetyVerdict::FALLEN_TILT;

        // 2. Loop-Overrun: Regelung war zu lange blind
        if (elapsedMs > _overrunMs) return SafetyVerdict::ESTOP_LOOP_OVERRUN;

        // 3. IMU-Stale: exakt identische Floats sind beim Balancieren
        //    physikalisch unmoeglich -- deutet auf eingefrorene IMU/I2C hin
        if (pitchDeg == _prevPitch && pitchRateDps == _prevRate) {
            _staleCycles++;
            if (_staleCycles >= _staleCycleLimit) return SafetyVerdict::ESTOP_IMU_STALE;
        } else {
            _staleCycles = 0;
        }
        _prevPitch = pitchDeg;
        _prevRate  = pitchRateDps;

        // 4. Saettigung: dauerhaft am Anschlag = Bot kommt nicht mehr hoch
        if (duty >= _maxDuty || duty <= -_maxDuty) {
            if (_satStartMs == 0) {
                _satStartMs = (nowMs == 0) ? 1 : nowMs;
            }
            if ((nowMs - _satStartMs) >= _saturationTimeoutMs) {
                return SafetyVerdict::FALLEN_SATURATION;
            }
        } else {
            _satStartMs = 0;
        }

        return SafetyVerdict::OK;
    }

    // Bei jedem Eintritt in BALANCING aufrufen
    void reset() {
        _staleCycles = 0;
        _satStartMs  = 0;
        _prevPitch   = 1.0e9f; // unmoeglicher Wert: erster Zyklus nie "stale"
        _prevRate    = 1.0e9f;
    }

private:
    static float absf(float v) { return (v < 0.0f) ? -v : v; }

    float         _fallenAngleDeg;
    int           _staleCycleLimit;
    unsigned long _overrunMs;
    int           _maxDuty;
    unsigned long _saturationTimeoutMs;

    int           _staleCycles = 0;
    unsigned long _satStartMs  = 0;
    float         _prevPitch   = 1.0e9f;
    float         _prevRate    = 1.0e9f;
};
