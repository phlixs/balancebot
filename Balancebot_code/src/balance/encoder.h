#pragma once

// ============================================================
// encoder.h -- BalanceBot: Encoder-Abstraktion
//
// Liest beide Encoder (Enc1 / Enc2), berechnet:
//   - Position: Mittelwert beider Encoder (Geradeausfahrt)
//   - Geschwindigkeit: Counts pro Sekunde (fuer Stall-Erkennung)
//
// Vorzeichenkonvention (aus Diagnose-Sketch verifiziert):
//   Vorwaerts fahren: Enc1 negativ, Enc2 positiv
//   Position = (Enc2 - Enc1) / 2  --> positiv bei Vorwaertsfahrt
// ============================================================

#include <Arduino.h>

class Encoder {
public:
    // Initialisierung -- Zaehler auf 0 setzen
    void begin();

    // Encoder-Werte lesen und Geschwindigkeit berechnen
    // Muss einmal pro Regelzyklus aufgerufen werden
    // dt: Zeit seit letztem Aufruf [Sekunden]
    void update(float dt);

    // Gemittelte Position (Vorwaerts positiv) [Counts]
    int position() const { return _position; }

    // Position in Metern [m]
    float positionM() const;

    // Mittlere Encoder-Geschwindigkeit [Counts/s]
    // Absolutwert beider Encoder gemittelt -- fuer Stall-Erkennung
    int speedCps() const { return _speedCps; }

    // Encoder-Zaehler zuruecksetzen (z.B. bei Uebergang nach BALANCING)
    void reset();

private:
    int _position  = 0;   // Gemittelte Position [Counts]
    int _speedCps  = 0;   // Mittlere Geschwindigkeit [Counts/s]
    int _prevPos   = 0;   // Vorherige Position fuer Geschwindigkeitsberechnung
};
