// ============================================================
// hw_check/main.cpp -- Phase 0: Hardware-Verifikation
//
// Interaktives Serial-Menue fuer die Inbetriebnahme-Checkliste
// (dokumentation/inbetriebnahme/commissioning_plan.md, Phase 0):
//   v  Carrier-Firmware-Version + BNO055-Status
//   m  Motortest: M1/M2 einzeln, +/-Duty 30, je 2 s
//   e  Encoder-Livewerte (Raeder von Hand drehen)
//   i  IMU-Livewerte: Pitch/Roll + alle 3 Gyro-Achsen
//   d  Vorzeichen-Diagnose (siehe dokumentation/inbetriebnahme/sign_conventions.md)
//   s  Not-Stopp (beide Motoren Duty 0)
//
// Erwartete Vorzeichen (sign_conventions.md, vorwaerts = USB-Richtung):
//   Roh-Pitch (orientation.z): 0=aufrecht, POSITIV=vorwaerts kippen
//   Vorwaerts:                 M1(+duty), M2(-duty)
//   Encoder vorwaerts:         Enc1 hoch, Enc2 runter
//
// Kein Treiber-Code -- rein diagnostisch.
// RAEDER IN DER LUFT! Motortest fragt vorher explizit nach.
// ============================================================

#include <Arduino.h>
#include <SPI.h>
#include <ArduinoMotorCarrier.h>
#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BNO055.h>

static const int   TEST_DUTY        = 30;     // wie Checkliste: Duty=30
static const int   MOTOR_RUN_MS     = 2000;   // Laufzeit pro Richtung
static const int   LIVE_VIEW_MS     = 15000;  // Dauer der Live-Anzeigen
static const int   LIVE_PERIOD_MS   = 200;    // 5 Hz Ausgaberate

Adafruit_BNO055 bno = Adafruit_BNO055(55, 0x28);

void stopMotors() {
    M1.setDuty(0);
    M2.setDuty(0);
}

void printMenu() {
    Serial.println();
    Serial.println("=== Phase 0: Hardware-Check ===");
    Serial.println("  v  Versionen/Status (Carrier + BNO055)");
    Serial.println("  m  Motortest (fragt erst: Raeder in der Luft?)");
    Serial.println("  e  Encoder-Livewerte (15 s, Raeder von Hand drehen)");
    Serial.println("  i  IMU-Livewerte (15 s, Bot kippen)");
    Serial.println("  d  Vorzeichen-Diagnose (15 s, Bot kippen + Rad drehen)");
    Serial.println("  s  Not-Stopp (Duty 0)");
    Serial.println();
}

// Wartet auf eine Taste, verwirft Rest der Eingabe. -1 bei Timeout.
int waitForKey(uint32_t timeoutMs) {
    uint32_t t0 = millis();
    while (millis() - t0 < timeoutMs) {
        if (Serial.available()) {
            int c = Serial.read();
            delay(5);
            while (Serial.available()) Serial.read();
            return c;
        }
        delay(10);
    }
    return -1;
}

// --- Check 1: Versionen und Status ---
void checkVersions() {
    Serial.println("--- Versionen/Status ---");
    Serial.print("Carrier ping: ");
    controller.ping();
    Serial.println("OK (keine Blockade)");

    Serial.print("Carrier FW-Version: ");
    Serial.println(controller.getFWVersion());

    uint8_t sysStat, selfTest, sysErr;
    bno.getSystemStatus(&sysStat, &selfTest, &sysErr);
    Serial.print("BNO055 Status: sys=");
    Serial.print(sysStat);
    Serial.print(" selftest=0x");
    Serial.print(selfTest, HEX);
    Serial.print(" err=");
    Serial.println(sysErr);
    Serial.println("(selftest=0xF = alle Tests bestanden)");

    uint8_t calSys, calGyro, calAccel, calMag;
    bno.getCalibration(&calSys, &calGyro, &calAccel, &calMag);
    Serial.print("Kalibrierung (0-3): sys=");
    Serial.print(calSys);
    Serial.print(" gyro=");
    Serial.print(calGyro);
    Serial.print(" accel=");
    Serial.print(calAccel);
    Serial.print(" mag=");
    Serial.println(calMag);
}

// Ein Motor, eine Richtung: anlaufen lassen, Encoderdifferenz melden
template <typename MotorT, typename EncoderT>
void runMotorLeg(const char* name, MotorT& motor, EncoderT& enc,
                 int duty, const char* expected) {
    Serial.print(name);
    Serial.print(" Duty=");
    Serial.print(duty);
    Serial.print("  (erwartet: ");
    Serial.print(expected);
    Serial.println(")");

    long c0 = enc.getRawCount();
    motor.setDuty(duty);
    delay(MOTOR_RUN_MS);
    motor.setDuty(0);
    long c1 = enc.getRawCount();

    Serial.print("  Encoder-Differenz: ");
    Serial.println(c1 - c0);
    delay(500);
}

// --- Check 2: Motortest mit Sicherheitsabfrage ---
void motorTest() {
    Serial.println("!!! RAEDER IN DER LUFT? Motortest startet beide Motoren.");
    Serial.println("    'y' = ja, starten. Jede andere Taste bricht ab.");
    int c = waitForKey(30000);
    if (c != 'y' && c != 'Y') {
        Serial.println("Abgebrochen.");
        return;
    }

    Serial.println("--- Motortest: Duty=30, je 2 s pro Richtung ---");
    runMotorLeg("M1 (links)",  M1, encoder1, +TEST_DUTY, "dreht VORWAERTS (zur USB-Seite), Enc1 zaehlt hoch");
    runMotorLeg("M1 (links)",  M1, encoder1, -TEST_DUTY, "dreht RUECKWAERTS, Enc1 zaehlt runter");
    runMotorLeg("M2 (rechts)", M2, encoder2, +TEST_DUTY, "dreht RUECKWAERTS, Enc2 zaehlt hoch");
    runMotorLeg("M2 (rechts)", M2, encoder2, -TEST_DUTY, "dreht VORWAERTS (zur USB-Seite), Enc2 zaehlt runter");
    stopMotors();
    Serial.println("Motortest fertig. Drehrichtungen mit sign_conventions.md abgleichen!");
}

// --- Check 3: Encoder-Livewerte ---
void encoderLive() {
    Serial.println("--- Encoder live (Raeder von Hand drehen) ---");
    Serial.println("Vorwaerts-Drehung (zur USB-Seite): Enc1 hoch, Enc2 runter (Taste = Abbruch)");
    Serial.println("enc1;enc2");
    uint32_t t0 = millis();
    while (millis() - t0 < LIVE_VIEW_MS && !Serial.available()) {
        Serial.print(encoder1.getRawCount());
        Serial.print(";");
        Serial.println(encoder2.getRawCount());
        delay(LIVE_PERIOD_MS);
    }
    while (Serial.available()) Serial.read();
}

// --- Check 4: IMU-Livewerte inkl. aller Gyro-Achsen ---
// Klaert auch die offene Frage: welche Gyro-Achse ist die Pitch-Rate?
// (imu.cpp nimmt bisher unverifiziert gyro.y)
void imuLive() {
    Serial.println("--- IMU live (Bot langsam vor/zurueck kippen) ---");
    Serial.println("Erwartung: vorwaerts kippen (zur USB-Seite) -> roher Pitch POSITIV.");
    Serial.println("Die Gyro-Achse, die beim Kippen ausschlaegt, ist die Pitch-Rate.");
    Serial.println("pitch;roll;gyroX;gyroY;gyroZ");
    sensors_event_t ori, gyr;
    uint32_t t0 = millis();
    while (millis() - t0 < LIVE_VIEW_MS && !Serial.available()) {
        bno.getEvent(&ori);
        bno.getEvent(&gyr, Adafruit_BNO055::VECTOR_GYROSCOPE);
        Serial.print(ori.orientation.z, 1);   // Pitch laut sign_conventions.md
        Serial.print(";");
        Serial.print(ori.orientation.y, 1);   // Roll
        Serial.print(";");
        Serial.print(gyr.gyro.x, 2);
        Serial.print(";");
        Serial.print(gyr.gyro.y, 2);
        Serial.print(";");
        Serial.println(gyr.gyro.z, 2);
        delay(LIVE_PERIOD_MS);
    }
    while (Serial.available()) Serial.read();
}

// --- Check 5: Vorzeichen-Diagnose (alles zusammen) ---
void signDiagnosis() {
    Serial.println("--- Vorzeichen-Diagnose ---");
    Serial.println("1) Bot VORWAERTS kippen (zur USB-Seite) -> roher Pitch POSITIV?");
    Serial.println("2) Rad vorwaerts drehen -> Enc1 HOCH, Enc2 RUNTER?");
    Serial.println("pitch;gyroX;enc1;enc2");
    sensors_event_t ori, gyr;
    uint32_t t0 = millis();
    while (millis() - t0 < LIVE_VIEW_MS && !Serial.available()) {
        bno.getEvent(&ori);
        bno.getEvent(&gyr, Adafruit_BNO055::VECTOR_GYROSCOPE);
        Serial.print(ori.orientation.z, 1);
        Serial.print(";");
        Serial.print(gyr.gyro.x, 2);
        Serial.print(";");
        Serial.print(encoder1.getRawCount());
        Serial.print(";");
        Serial.println(encoder2.getRawCount());
        delay(LIVE_PERIOD_MS);
    }
    while (Serial.available()) Serial.read();
}

void setup() {
    Serial.begin(115200);
    while (!Serial) delay(10);

    Serial.println("=== BalanceBot Phase-0 Hardware-Check ===");
    Serial.println("Initialisiere...");

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

    stopMotors();
    printMenu();
}

void loop() {
    int c = waitForKey(60000);
    if (c < 0) {
        stopMotors();   // Sicherheit: bei Inaktivitaet immer Duty 0
        return;
    }

    switch (c) {
        case 'v': checkVersions();  break;
        case 'm': motorTest();      break;
        case 'e': encoderLive();    break;
        case 'i': imuLive();        break;
        case 'd': signDiagnosis();  break;
        case 's':
        default:
            stopMotors();
            Serial.println("Motoren gestoppt.");
            break;
    }
    printMenu();
}
