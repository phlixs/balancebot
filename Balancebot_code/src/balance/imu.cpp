// ============================================================
// imu.cpp -- BalanceBot: IMU-Implementierung
// ============================================================

#include "imu.h"
#include "config.h"
#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BNO055.h>

bool Imu::begin() {
    // Bei einem erneuten Aufruf (tryReinit aus E_STOP) gilt der Sensor bis
    // zum erfolgreichen Abschluss wieder als nicht bereit.
    _ready = false;

    // Objekt nur beim ersten Aufruf anlegen. Frueher stand hier bei JEDEM
    // Aufruf ein "new" ohne zugehoeriges "delete" -- jeder Reinit-Versuch
    // aus dem E_STOP heraus ('r') hat damit Speicher verloren, auf einem
    // Controller mit 32 KB SRAM eine ernste Sache.
    // Siehe dokumentation/reviews/2026-04-13-code-review.md, Befund C-1.
    if (_bno == nullptr) {
        _bno = new Adafruit_BNO055(BNO055_SENSOR_ID, BNO055_I2C_ADDR);
    }

    if (!_bno->begin()) {
        // I2C-Verbindung fehlgeschlagen
        return false;
    }

    // Externen Quarz fuer bessere Genauigkeit aktivieren
    _bno->setExtCrystalUse(true);

    // IMU-Modus (IMUPLUS, 0x08): nur Gyro+Accel-Fusion, kein Magnetometer.
    // Entscheidung Phase 2 (2026-08-07, imu_latency-Sketch): Latenz identisch
    // zu NDOF (bimodal ~0.95/1.9 ms, max 2.2 ms, weit unter 5-ms-Grenze).
    // IMUPLUS gewaehlt, weil das Magnetometer direkt neben den Motoren sitzt
    // und deren Magnetfelder im NDOF-Modus Fusionsspruenge verursachen koennen.
    _bno->setMode(OPERATION_MODE_IMUPLUS);
    delay(100); // Moduswechsel abwarten (Datenblatt: 7-19 ms, konservativ)

    _ready = true;
    return true;
}

void Imu::update() {
    // Ohne erfolgreiches begin() gibt es nichts zu lesen.
    //
    // Der Fall tritt tatsaechlich auf: Schlaegt controller.begin() in setup()
    // fehl (z. B. Akku aus, Motor Carrier ohne Strom), kehrt setup() zurueck,
    // BEVOR imu.begin() jemals aufgerufen wurde. loop() ruft update() aber
    // unbedingt auf ("IMU immer lesen fuer Sicherheitscheck"). Frueher lief
    // das in eine Nullzeiger-Dereferenzierung und damit in einen HardFault --
    // das Board wirkte dann tot: LED aus, keine Serial-Antwort, USB weiter
    // angemeldet. Jetzt bleibt es sauber im E_STOP mit seinem Blinkcode.
    if (!_ready) return;

    uint32_t t0 = micros(); // Startzeit fuer Latenzmessung

    // Orientierungs-Euler-Winkel lesen
    sensors_event_t orientEvent;
    _bno->getEvent(&orientEvent);

    // Winkelgeschwindigkeit lesen (Gyro-Rohdaten)
    sensors_event_t gyroEvent;
    _bno->getEvent(&gyroEvent, Adafruit_BNO055::VECTOR_GYROSCOPE);

    uint32_t t1 = micros();
    _lastDurationUs = t1 - t0; // Dauer beider Lesezugriffe

    // Pitch-Winkel: event.orientation.z ist der Tilt um die Radachse.
    // Roh-Vorzeichen (hw_check 2026-08-07, vorwaerts = USB-Richtung):
    // Vorwaertskippen -> z POSITIV. Negation auf interne Konvention
    // (vorwaerts kippen -> pitch negativ, siehe imu.h / sign_conventions.md).
    _pitch = -orientEvent.orientation.z;

    // Pitch-Rate: Kippachse ist gyro.x (hw_check 2026-08-07: gyro.x schlaegt
    // beim Kippen bis +-1.4 rad/s aus, gyro.y bleibt ~0). Roh gilt
    // gyro.x = -d(z)/dt; nach Negation von _pitch ist d(_pitch)/dt = +gyro.x.
    // Adafruit-Event liefert rad/s -> Umrechnung auf Grad/s (wie _pitch).
    _pitchRate = gyroEvent.gyro.x * RAD_TO_DEG;

    // Kalibrierungsgrad abfragen
    uint8_t calibMag = 0; // nicht benoetigt
    _bno->getCalibration(&_calibSys, &_calibGyro, &_calibAccel, &calibMag);
}

bool Imu::isCalibrated() const {
    // Gyro UND Accelerometer muessen mindestens Stufe 2 erreicht haben
    return (_calibGyro >= 2) && (_calibAccel >= 2);
}
