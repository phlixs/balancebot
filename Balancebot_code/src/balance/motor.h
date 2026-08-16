#pragma once

// ============================================================
// motor.h -- BalanceBot: Motor-Abstraktion
//
// Kapselt M1/M2 des Motor Carriers. Stellt sicher:
//   - Duty-Begrenzung auf MAX_DUTY (Treiberschutz)
//   - Totzonenkompensation (DEADZONE_DUTY)
//   - Slew-Rate-Begrenzung (DUTY_SLEW_RATE)
//   - Stall-Erkennung
//
// Vorzeichenkonvention (aus Diagnose-Sketch verifiziert):
//   Vorwaerts = setDrive(+duty)   --> intern: M1(-duty), M2(+duty)
//   Rueckwaerts = setDrive(-duty) --> intern: M1(+duty), M2(-duty)
// ============================================================

#include <Arduino.h>

class MotorPair {
public:
    // Muss nach controller.begin() aufgerufen werden
    void begin();

    // Beide Motoren mit normiertem Duty ansteuern
    // duty: -100 bis +100 (positiv = vorwaerts)
    // Wendet Slew-Rate, Totzone und MAX_DUTY intern an
    void setDrive(int duty);

    // Beide Motoren sofort stoppen (Sicherheit)
    void stop();

    // Gibt den zuletzt tatsaechlich gesetzten Duty-Wert zurueck
    // (nach Begrenzung, vor Totzonenkompensation)
    int lastDuty() const { return _lastDuty; }

    // Stall-Erkennung ausfuehren -- gibt true zurueck wenn Stall erkannt
    // encoderSpeedCps: Absolutwert der mittleren Encoder-Geschwindigkeit [Counts/s]
    bool checkStall(int encoderSpeedCps);

    // Stall-Zaehler zuruecksetzen (z.B. bei Uebergang zu IDLE)
    void resetStall();

private:
    // Letzter Duty-Wert (fuer Slew-Rate-Berechnung)
    int _lastDuty = 0;

    // Stall-Timing
    unsigned long _stallStartMs = 0;    // wann begann die Stall-Bedingung?
    bool          _stallActive  = false; // ist Stall-Bedingung gerade aktiv?

    // Internen Duty mit Totzone und Richtung auf M1/M2 ausgeben
    void _applyToMotors(int clampedDuty);
};
