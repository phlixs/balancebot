// ============================================================
// BalanceBot - PID-Regler (Neustart)
//
// Verifizierte Fakten aus Diagnose:
//   - Setpoint = 0 Grad
//   - Vorwaerts kippen = negativer Pitch
//   - Vorwaerts fahren: M1(-), M2(+), Enc1 negativ, Enc2 positiv
//   - Encoder-Limit: max 1 Umdrehung (verhindert Wegfahren)
//
// Serial: millis,pitch,p,i,d,pid_out,duty,position
// ============================================================

#include <Arduino.h>
#include <SPI.h>
#include <ArduinoMotorCarrier.h>
#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BNO055.h>

Adafruit_BNO055 bno = Adafruit_BNO055(55, 0x28);

// ============================================================
// PID-Parameter (hier tunen!)
// ============================================================
float Kp = 2.0;
float Ki = 0.0;
float Kd = 0.1;
float setpoint = 0.0;

// --- Grenzen ---
const int MAX_DUTY = 30;
const float SICHERHEITS_WINKEL = 45.0;
const float INTEGRAL_MAX = 50.0;

// --- Encoder-Limit ---
// Counts fuer 1 Umdrehung. Falls unbekannt: Rad von Hand drehen,
// Wert im Live-Plot ablesen, hier eintragen.
const int COUNTS_PRO_UMDREHUNG = 1200;

// --- PID-Zustand ---
float fehler_vorher = 0.0;
float integral = 0.0;
unsigned long zeit_vorher = 0;
bool erster_durchlauf = true;

void setup() {
    Serial.begin(115200);
    while (!Serial) delay(10);

    Serial.println("=== BalanceBot PID ===");

    if (!bno.begin()) {
        Serial.println("BNO055 FEHLER");
        while (1) delay(100);
    }
    bno.setExtCrystalUse(true);

    if (!controller.begin()) {
        Serial.println("Motor Carrier FEHLER");
        while (1) delay(100);
    }
    controller.reboot();
    delay(500);

    M1.setDuty(0);
    M2.setDuty(0);
    encoder1.resetCounter(0);
    encoder2.resetCounter(0);

    Serial.println("millis,pitch,p,i,d,duty,position");
    delay(2000);
    zeit_vorher = millis();
}

void loop() {
    // --- Sensor lesen (kein Filter, BNO055 hat eigene Fusion) ---
    sensors_event_t event;
    bno.getEvent(&event);
    float pitch = event.orientation.z;

    // --- Sicherheit ---
    if (abs(pitch - setpoint) > SICHERHEITS_WINKEL) {
        M1.setDuty(0);
        M2.setDuty(0);
        controller.ping();
        integral = 0.0;
        fehler_vorher = 0.0;
        erster_durchlauf = true;
        zeit_vorher = millis();
        encoder1.resetCounter(0);
        encoder2.resetCounter(0);
        delay(500);
        return;
    }

    // --- Zeit ---
    unsigned long jetzt = millis();
    float dt = (jetzt - zeit_vorher) / 1000.0;
    if (dt < 0.01) return;  // Min 10ms zwischen Zyklen (100 Hz, nicht-blockierend)

    // --- PID ---
    float fehler = setpoint - pitch;

    float p = Kp * fehler;

    integral += fehler * dt;
    if (integral > INTEGRAL_MAX) integral = INTEGRAL_MAX;
    if (integral < -INTEGRAL_MAX) integral = -INTEGRAL_MAX;
    float i = Ki * integral;

    float d = 0.0;
    if (erster_durchlauf) {
        erster_durchlauf = false;
    } else {
        d = Kd * ((fehler - fehler_vorher) / dt);
    }

    float pid_out = p + i + d;

    // --- Duty begrenzen ---
    int duty = (int)pid_out;
    if (duty > MAX_DUTY) duty = MAX_DUTY;
    if (duty < -MAX_DUTY) duty = -MAX_DUTY;

    // --- Encoder-Position ---
    int pos1 = encoder1.getRawCount();
    int pos2 = encoder2.getRawCount();
    float position = (float)(pos2 - pos1) / 2.0;

    // --- Encoder-Limit: max 1 Umdrehung ---
    //if (position > COUNTS_PRO_UMDREHUNG && duty > 0) duty = 0;
    //if (position < -COUNTS_PRO_UMDREHUNG && duty < 0) duty = 0;

    // --- Motoren ---
    M1.setDuty(-duty);
    M2.setDuty(duty);
    controller.ping();

    // --- Serial CSV ---
    Serial.print(jetzt);
    Serial.print(",");
    Serial.print(pitch, 2);
    Serial.print(",");
    Serial.print(p, 2);
    Serial.print(",");
    Serial.print(i, 2);
    Serial.print(",");
    Serial.print(d, 2);
    Serial.print(",");
    Serial.print(duty);
    Serial.print(",");
    Serial.println((int)position);

    fehler_vorher = fehler;
    zeit_vorher = jetzt;
}
