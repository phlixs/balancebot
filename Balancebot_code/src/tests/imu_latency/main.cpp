// ============================================================
// imu_latency/main.cpp -- BNO055 Latenz- und Datenrate-Test
//
// Misst:
//   1. Latenz eines einzelnen getEvent()-Aufrufs (us)
//   2. Effektive Datenrate des BNO055 (wie oft aendert sich der Wert?)
//   3. Vergleich: NDOF-Modus vs. IMU-Modus (0x08)
//
// Methode:
//   - 500 Lesezugriffe mit micros()-Zeitstempel
//   - Zaehlt wie oft sich der Wert tatsaechlich veraendert hat
//   - Ausgabe als CSV fuer Python-Analyse
//
// Warum wichtig:
//   - BNO055 aktualisiert intern mit bestimmter ODR (Output Data Rate)
//   - Wenn getEvent() oefter aufgerufen wird als die ODR --> gleiche Werte
//   - Bekannte ODR im IMU-Modus: ~100 Hz, im NDOF-Modus: ~100 Hz
//   - Bei Routing durch ATSAMD11 koennte Latenz hoeher sein
//
// CSV-Format:
//   i,t_us,pitch,changed
//   (i: Index, t_us: micros() seit Start, pitch: Winkelwert, changed: 0/1)
// ============================================================

#include <Arduino.h>
#include <SPI.h>
#include <ArduinoMotorCarrier.h>
#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BNO055.h>

static const int N = 500; // Anzahl Messwerte

Adafruit_BNO055 bno = Adafruit_BNO055(55, 0x28);

void setup() {
    Serial.begin(115200);
    while (!Serial) delay(10);

    Serial.println("=== IMU Latenz-Test ===");

    if (!controller.begin()) {
        Serial.println("FEHLER: Motor Carrier nicht gefunden!");
        while (1) delay(100);
    }
    controller.reboot();
    delay(500);

    if (!bno.begin()) {
        Serial.println("FEHLER: BNO055 nicht gefunden!");
        while (1) delay(100);
    }
    bno.setExtCrystalUse(true);

    // Kurz warten bis BNO055 stabil laeuft
    delay(1000);

    Serial.println();
    Serial.println("--- Phase 1: NDOF-Modus (Standard) ---");
    Serial.println("i,t_us,duration_us,pitch,changed");

    float prevPitch = 0.0f;
    bool  first     = true;

    for (int i = 0; i < N; i++) {
        uint32_t tStart = micros();

        sensors_event_t ev;
        bno.getEvent(&ev);
        float pitch = ev.orientation.z;

        uint32_t duration = micros() - tStart;

        // Zaehlt als "veraendert" wenn Wert sich um mehr als 0.01 Grad geaendert hat
        int changed = 0;
        if (!first && abs(pitch - prevPitch) > 0.01f) {
            changed = 1;
        }
        prevPitch = pitch;
        first     = false;

        Serial.print(i);     Serial.print(',');
        Serial.print(tStart); Serial.print(',');
        Serial.print(duration); Serial.print(',');
        Serial.print(pitch, 3); Serial.print(',');
        Serial.println(changed);

        // 5 ms warten damit wir sicher den naechsten IMU-Zyklus erfassen
        delay(5);
    }

    Serial.println();
    Serial.println("--- Phase 2: IMU-Modus (0x08, kein Magnetometer) ---");
    Serial.println("i,t_us,duration_us,pitch,changed");

    // In IMU-Modus umschalten (Adafruit: OPERATION_MODE_IMUPLUS = 0x08)
    bno.setMode(OPERATION_MODE_IMUPLUS);
    delay(600); // BNO055 braucht ~600ms fuer Moduswechsel

    prevPitch = 0.0f;
    first     = true;

    for (int i = 0; i < N; i++) {
        uint32_t tStart = micros();

        sensors_event_t ev;
        bno.getEvent(&ev);
        float pitch = ev.orientation.z;

        uint32_t duration = micros() - tStart;

        int changed = 0;
        if (!first && abs(pitch - prevPitch) > 0.01f) {
            changed = 1;
        }
        prevPitch = pitch;
        first     = false;

        Serial.print(i);     Serial.print(',');
        Serial.print(tStart); Serial.print(',');
        Serial.print(duration); Serial.print(',');
        Serial.print(pitch, 3); Serial.print(',');
        Serial.println(changed);

        delay(5);
    }

    Serial.println();
    Serial.println("=== Test abgeschlossen ===");
    Serial.println("Daten mit python/analyze.py --mode imu_latency auswerten.");
}

void loop() {
    delay(1000);
}
