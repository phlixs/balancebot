// ============================================================
// deadzone_id/main.cpp -- Motor-Totzone-Identifikation
//
// Rampt den Duty-Cycle beider Motoren langsam von 0 auf MAX_SWEEP hoch.
// Gibt pro Schritt Duty und Encoder-Geschwindigkeit als CSV aus.
//
// Auswertung in Python:
//   - Plot: Encoder-Geschwindigkeit vs. Duty
//   - Totzone = Duty unterhalb dem die Motoren anlaufen
//   - Ggf. unterschiedliche Totzone M1 vs. M2 (separate Messung)
//
// Wichtig:
//   - RAEDER IN DER LUFT lassen!
//   - Motoren einzeln testen (M1_ONLY oder M2_ONLY definieren)
//   - Mehrere Laeufe aufzeichnen (Mittelung)
//
// CSV-Format:
//   t_ms,duty,enc1_cps,enc2_cps
// ============================================================

#include <Arduino.h>
#include <SPI.h>
#include <ArduinoMotorCarrier.h>

// Maximal getesteter Duty-Wert
// Haelt die MAX_DUTY-Grenze aus ADR-0003 ein (Treiber 500 mA):
// die Totzone liegt ohnehin weit unterhalb von 45
static const int MAX_SWEEP = 45;
// Schrittgroesse [Duty-Einheiten]
static const int STEP_SIZE = 1;
// Wartezeit pro Schritt [ms] -- lang genug damit Encoder-Geschwindigkeit stabil
static const int STEP_DELAY_MS = 200;
// Anzahl Wiederholungen fuer Mittelung pro Schritt
static const int REPS_PER_STEP = 5;

void setup() {
    Serial.begin(115200);
    while (!Serial) delay(10);

    Serial.println("=== Motor Totzone-Identifikation ===");
    Serial.println("RAEDER IN DER LUFT!");
    delay(2000);

    if (!controller.begin()) {
        Serial.println("FEHLER: Motor Carrier nicht gefunden!");
        while (1) delay(100);
    }
    controller.reboot();
    delay(500);

    M1.setDuty(0);
    M2.setDuty(0);
    encoder1.resetCounter(0);
    encoder2.resetCounter(0);

    Serial.println("t_ms,duty,enc1_cps,enc2_cps");
    delay(500);

    // --- Rampe vorwaerts ---
    Serial.println("# Rampe vorwaerts");
    for (int duty = 0; duty <= MAX_SWEEP; duty += STEP_SIZE) {
        // Beide Motoren vorwaerts (Richtung USB-Buchse)
        // Konvention hw_check 2026-08-07: vorwaerts = M1(+), M2(-)
        M1.setDuty(duty);
        M2.setDuty(-duty);

        // Stabil werden lassen
        delay(STEP_DELAY_MS);

        // Mehrere Messungen pro Schritt mitteln
        long sum1 = 0, sum2 = 0;
        for (int r = 0; r < REPS_PER_STEP; r++) {
            controller.ping();
            sum1 += encoder1.getCountPerSecond();
            sum2 += encoder2.getCountPerSecond();
            delay(10);
        }

        Serial.print(millis()); Serial.print(',');
        Serial.print(duty);     Serial.print(',');
        Serial.print(sum1 / REPS_PER_STEP); Serial.print(',');
        Serial.println(sum2 / REPS_PER_STEP);
    }

    // Pause zwischen Rampen
    M1.setDuty(0);
    M2.setDuty(0);
    controller.ping();
    Serial.println("# Pause zwischen Rampen");
    delay(1000);

    // --- Rampe rueckwaerts ---
    Serial.println("# Rampe rueckwaerts (negatives Duty)");
    for (int duty = 0; duty <= MAX_SWEEP; duty += STEP_SIZE) {
        // Rueckwaerts: umgekehrte Vorzeichen zur Vorwaerts-Rampe
        M1.setDuty(-duty);
        M2.setDuty(duty);

        delay(STEP_DELAY_MS);

        long sum1 = 0, sum2 = 0;
        for (int r = 0; r < REPS_PER_STEP; r++) {
            controller.ping();
            sum1 += encoder1.getCountPerSecond();
            sum2 += encoder2.getCountPerSecond();
            delay(10);
        }

        Serial.print(millis()); Serial.print(',');
        Serial.print(-duty);    Serial.print(',');  // Negatives Duty markieren
        Serial.print(sum1 / REPS_PER_STEP); Serial.print(',');
        Serial.println(sum2 / REPS_PER_STEP);
    }

    // Motoren ausschalten
    M1.setDuty(0);
    M2.setDuty(0);
    controller.ping();

    Serial.println("# Messung abgeschlossen");
}

void loop() {
    controller.ping();
    delay(100);
}
