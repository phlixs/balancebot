// ============================================================
// motor.cpp -- BalanceBot: Motor-Implementierung
// ============================================================

#include "motor.h"
#include "config.h"
#include "deadzone.h"
#include <ArduinoMotorCarrier.h>

void MotorPair::begin() {
    // Startposition: beide Motoren aus
    M1.setDuty(0);
    M2.setDuty(0);
    _lastDuty = 0;
    resetStall();
}

void MotorPair::setDrive(int duty) {
    // --- Slew-Rate-Begrenzung ---
    // Duty darf sich pro Schritt hoechstens um DUTY_SLEW_RATE aendern.
    // Verhindert Strom-Spikes bei abrupten Richtungswechseln.
    int delta = duty - _lastDuty;
    if (delta >  DUTY_SLEW_RATE) duty = _lastDuty + DUTY_SLEW_RATE;
    if (delta < -DUTY_SLEW_RATE) duty = _lastDuty - DUTY_SLEW_RATE;

    // --- Absolute Begrenzung (Treiberschutz) ---
    // MAX_DUTY ist so gewaehlt, dass Stallstrom unter Treibergrenze bleibt
    if (duty >  MAX_DUTY) duty =  MAX_DUTY;
    if (duty < -MAX_DUTY) duty = -MAX_DUTY;

    _lastDuty = duty;
    _applyToMotors(duty);
}

void MotorPair::stop() {
    // Sofortiger Stop ohne Slew-Rate (fuer Sicherheitszustaende)
    _lastDuty = 0;
    M1.setDuty(0);
    M2.setDuty(0);
    controller.ping(); // Watchdog-Ping benoetigt
}

void MotorPair::_applyToMotors(int duty) {
    // Vorwaerts (duty > 0, Richtung USB-Buchse): M1 positiv, M2 negativ
    // (hw_check 2026-08-07: M1(+) -> Enc1 hoch, und Enc1 hoch = vorwaerts)
    //
    // Totzonen-Kompensation PRO MOTOR-ANSCHLUSS, weil die Totzone vom
    // Duty-Vorzeichen am Anschluss abhaengt (Carrier-Treiber-Asymmetrie).
    // Bei kleinem Vorwaerts-Befehl liegt M1 auf der positiven (23 %) und
    // M2 auf der negativen Seite (17 %) -- eine gemeinsame Schwelle wuerde
    // nur eines der Raeder anlaufen lassen (Gieren).
    int m1Duty = compensateDeadzone( duty, DEADZONE_DUTY_POS, DEADZONE_DUTY_NEG);
    int m2Duty = compensateDeadzone(-duty, DEADZONE_DUTY_POS, DEADZONE_DUTY_NEG);

    M1.setDuty(m1Duty);
    M2.setDuty(m2Duty);
    controller.ping(); // Motor Carrier Watchdog-Ping (benoetigt ca. alle 100ms)
}

bool MotorPair::checkStall(int encoderSpeedCps) {
    // Stall-Bedingung: hoher Duty bei zu geringer Encoder-Geschwindigkeit
    bool condition = (abs(_lastDuty) >= STALL_DUTY_THRESHOLD) &&
                     (encoderSpeedCps <= STALL_SPEED_THRESHOLD);

    if (condition) {
        if (!_stallActive) {
            // Stall-Bedingung beginnt gerade -- Startzeit merken
            _stallActive  = true;
            _stallStartMs = millis();
        }
        // Stall-Timeout pruefen
        if ((millis() - _stallStartMs) >= (unsigned long)STALL_TIMEOUT_MS) {
            return true; // Stall bestaetigt --> E_STOP ausloesen
        }
    } else {
        // Bedingung nicht mehr erfuellt -- Zaehler zuruecksetzen
        _stallActive = false;
    }

    return false; // Kein Stall
}

void MotorPair::resetStall() {
    _stallActive  = false;
    _stallStartMs = 0;
}
