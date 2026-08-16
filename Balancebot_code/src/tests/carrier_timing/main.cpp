// ============================================================
// carrier_timing/main.cpp -- Motor Carrier I2C-Timing-Test
//
// Misst die Ausfuehrungszeit jedes Motor-Carrier-API-Aufrufs:
//   - controller.ping()
//   - encoder1.getRawCount()
//   - encoder2.getRawCount()
//   - M1.setDuty(0)
//   - IMU-Lesezugriff (getEvent)
//
// Methode:
//   1000 Iterationen pro Aufruf, Messung mit micros()
//   Ausgabe: min / max / mean in Mikrosekunden
//
// Ziel:
//   Pruefen ob alle Aufrufe zusammen in 10 ms (10000 us) passen.
//   Wenn ein einzelner Aufruf > 2000 us --> Risiko fuer Timing-Jitter!
//
// Kein Treiber-Code -- rein diagnostisch.
// RAEDER IN DER LUFT!
// ============================================================

#include <Arduino.h>
#include <SPI.h>
#include <ArduinoMotorCarrier.h>
#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BNO055.h>

static const int ITERATIONS = 1000;

Adafruit_BNO055 bno = Adafruit_BNO055(55, 0x28);

// Hilfsfunktion: min/max/mean messen und ausgeben
// name: Bezeichnung des gemessenen Aufrufs
// timings[]: Array mit ITERATIONS Messwerten in us
void printStats(const char* name, uint32_t* timings) {
    uint32_t sumUs = 0;
    uint32_t minUs = 0xFFFFFFFF;
    uint32_t maxUs = 0;

    for (int i = 0; i < ITERATIONS; i++) {
        sumUs += timings[i];
        if (timings[i] < minUs) minUs = timings[i];
        if (timings[i] > maxUs) maxUs = timings[i];
    }
    float meanUs = (float)sumUs / ITERATIONS;

    Serial.print(name);
    Serial.print(": min=");
    Serial.print(minUs);
    Serial.print(" us  max=");
    Serial.print(maxUs);
    Serial.print(" us  mean=");
    Serial.print(meanUs, 1);
    Serial.println(" us");
}

// Puffer fuer Messwerte (stack, kein heap)
uint32_t timings[ITERATIONS];

void setup() {
    Serial.begin(115200);
    while (!Serial) delay(10);

    Serial.println("=== Motor Carrier Timing-Test ===");
    Serial.println("Initialisiere...");

    // Motor Carrier starten
    if (!controller.begin()) {
        Serial.println("FEHLER: Motor Carrier nicht gefunden!");
        while (1) delay(100);
    }
    controller.reboot();
    delay(500);

    // BNO055 starten
    if (!bno.begin()) {
        Serial.println("FEHLER: BNO055 nicht gefunden!");
        while (1) delay(100);
    }
    bno.setExtCrystalUse(true);

    // Sicherheits-Duty auf 0 setzen
    M1.setDuty(0);
    M2.setDuty(0);

    Serial.println("Bereit. Starte Messung...");
    Serial.println();
    delay(500);

    // --- Test 1: controller.ping() ---
    Serial.println("Messe controller.ping() ...");
    for (int i = 0; i < ITERATIONS; i++) {
        uint32_t t0 = micros();
        controller.ping();
        timings[i] = micros() - t0;
    }
    printStats("controller.ping()", timings);

    // --- Test 2: encoder1.getRawCount() ---
    Serial.println("Messe encoder1.getRawCount() ...");
    for (int i = 0; i < ITERATIONS; i++) {
        uint32_t t0 = micros();
        encoder1.getRawCount();
        timings[i] = micros() - t0;
    }
    printStats("encoder1.getRawCount()", timings);

    // --- Test 3: encoder2.getRawCount() ---
    Serial.println("Messe encoder2.getRawCount() ...");
    for (int i = 0; i < ITERATIONS; i++) {
        uint32_t t0 = micros();
        encoder2.getRawCount();
        timings[i] = micros() - t0;
    }
    printStats("encoder2.getRawCount()", timings);

    // --- Test 4: M1.setDuty(0) ---
    // Achtung: Duty=0 -- kein Motorlauf
    Serial.println("Messe M1.setDuty(0) ...");
    for (int i = 0; i < ITERATIONS; i++) {
        uint32_t t0 = micros();
        M1.setDuty(0);
        timings[i] = micros() - t0;
    }
    printStats("M1.setDuty(0)", timings);

    // --- Test 5: M2.setDuty(0) ---
    Serial.println("Messe M2.setDuty(0) ...");
    for (int i = 0; i < ITERATIONS; i++) {
        uint32_t t0 = micros();
        M2.setDuty(0);
        timings[i] = micros() - t0;
    }
    printStats("M2.setDuty(0)", timings);

    // --- Test 6: bno.getEvent() (Orientierung) ---
    Serial.println("Messe bno.getEvent(VECTOR_EULER) ...");
    sensors_event_t ev;
    for (int i = 0; i < ITERATIONS; i++) {
        uint32_t t0 = micros();
        bno.getEvent(&ev);
        timings[i] = micros() - t0;
    }
    printStats("bno.getEvent(EULER)", timings);

    // --- Test 7: bno.getEvent() (Gyro) ---
    Serial.println("Messe bno.getEvent(VECTOR_GYROSCOPE) ...");
    for (int i = 0; i < ITERATIONS; i++) {
        uint32_t t0 = micros();
        bno.getEvent(&ev, Adafruit_BNO055::VECTOR_GYROSCOPE);
        timings[i] = micros() - t0;
    }
    printStats("bno.getEvent(GYRO)", timings);

    // --- Gesamtbudget-Schaetzung ---
    Serial.println();
    Serial.println("=== Ergebnis ===");
    Serial.println("Ziel: Alle Aufrufe zusammen < 8000 us (80% von 10ms Budget)");
    Serial.println("Vergleiche die Summe der Mean-Werte mit 8000 us.");
    Serial.println("Fertig.");
}

void loop() {
    // Nichts -- alle Messungen in setup()
    delay(1000);
}
