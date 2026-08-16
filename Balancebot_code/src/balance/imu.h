#pragma once

// ============================================================
// imu.h -- BalanceBot: IMU-Schnittstelle (BNO055)
//
// Kapselt alle BNO055-Zugriffe. Gibt einen einzigen
// Kippwinkel (pitch) und eine Winkelgeschwindigkeit (pitch_rate)
// zurueck. Keine Magic Numbers ausserhalb dieser Datei.
//
// Vorzeichenkonvention (aus Diagnose-Sketch verifiziert):
//   pitch > 0  --> Bot kippt rueckwaerts
//   pitch < 0  --> Bot kippt vorwaerts
//   pitch = 0  --> aufrecht
// ============================================================

#include <Arduino.h>

// Vorwaertsdeklaration (Adafruit-Klasse).
//
// Bewusst KEIN #include <Adafruit_BNO055.h> hier: Der Header zieht ueber
// utility/imumaths.h ein "namespace imu" herein, das mit dem globalen Objekt
// "Imu imu;" in main.cpp kollidiert. Deshalb bleibt es beim Zeiger statt beim
// Wertmember, den dokumentation/reviews/2026-04-13-code-review.md vorschlaegt --
// die Befunde C-1 und C-2 sind unten anders geloest.
class Adafruit_BNO055;

class Imu {
public:
    // Initialisierung -- gibt false zurueck bei I2C-Fehler
    bool begin();

    // Einen Messwert vom BNO055 lesen
    // Muss einmal pro Regelzyklus aufgerufen werden.
    // Vor einem erfolgreichen begin() ein No-Op (siehe _ready).
    void update();

    // true, sobald begin() erfolgreich war. Vorher liefern pitch()/pitchRate()
    // ihre Startwerte (0), und update() liest nichts.
    bool isReady() const { return _ready; }

    // Kippwinkel [Grad] -- relativ zur aufrechten Position
    float pitch() const { return _pitch; }

    // Winkelgeschwindigkeit um Kippachse [Grad/s]
    float pitchRate() const { return _pitchRate; }

    // Kalibrierungsgrad des Systems (0-3, 3 = voll kalibriert)
    // Fuer BNO055 IMU-Modus (ohne Magnetometer) zaehlt nur gyro+accel
    uint8_t calibration() const { return _calibSys; }

    // Gibt true wenn der Gyro und Accelerometer kalibriert sind (Schwelle 2/3)
    bool isCalibrated() const;

    // Nur-Gyro-Kalibrierung (Schwelle 2/3) -- fuer den Headless-Fallback:
    // Gyro kalibriert sich durch blosses Stillhalten, Accel braucht die
    // 6-Lagen-Prozedur und schafft es headless oft nicht
    bool gyroCalibrated() const { return _calibGyro >= 2; }

    // Rohe Messzeit des letzten update()-Aufrufs [Mikrosekunden]
    // Fuer Latenz-Diagnose; 0 vor erstem Aufruf
    uint32_t lastUpdateDurationUs() const { return _lastDurationUs; }

private:
    // Zeiger auf das Adafruit-Objekt. begin() legt es genau EINMAL an und
    // verwendet es bei jedem weiteren Aufruf wieder -- damit kann der Aufruf
    // aus tryReinit() nichts mehr lecken (Befund C-1).
    Adafruit_BNO055* _bno = nullptr;

    // Erst nach erfolgreichem begin() darf vom Sensor gelesen werden.
    // Schuetzt update() gegen den Fall, dass begin() nie lief (Befund C-2).
    bool      _ready          = false;
    float     _pitch          = 0.0f;
    float     _pitchRate      = 0.0f;
    uint8_t   _calibSys       = 0;
    uint8_t   _calibGyro      = 0;
    uint8_t   _calibAccel     = 0;
    uint32_t  _lastDurationUs = 0;
};
