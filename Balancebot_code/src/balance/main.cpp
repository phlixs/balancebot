// ============================================================
// main.cpp -- BalanceBot: Modulare Hauptschleife mit Zustandsmaschine
//
// Zustaende: INIT --> CALIBRATING --> IDLE --> BALANCING --> FALLEN --> E_STOP
//
// Headless-Betrieb (Phase A): bootet ohne USB (Serial-Timeout),
// armiert selbststaendig wenn der Bot aufrecht+ruhig hingestellt
// wird (Auto-Arm), SafetySupervisor ueberwacht Tilt / IMU-Stale /
// Loop-Overrun / Saettigung.
//
// Serial-Befehle (ein Zeichen, optional -- alles geht auch headless):
//   's'  --> IDLE nach BALANCING (manueller Start)
//   'q'  --> BALANCING nach IDLE (quit)
//   'r'  --> E_STOP: direkter Neuinitialisierungs-Versuch
//   'h'  --> CSV-Header erneut ausgeben
//   'p'  --> Parameter ausgeben (Kp, Ki, Kd, Setpoint)
//
// TODO: Erweiterung um serielle Parameter-Aenderung (z.B. "Kp=3.5")
// ============================================================

#include <Arduino.h>
#include <SPI.h>
#include <ArduinoMotorCarrier.h>

#include "config.h"
#include "state_machine.h"
#include "imu.h"
#include "motor.h"
#include "encoder.h"
#include "pid.h"
#include "logger.h"
#include "autoarm.h"
#include "safety.h"
#include "command.h"

// ------------------------------------------------------------
// Globale Objekte
// ------------------------------------------------------------

Imu        imu;
MotorPair  motors;
Encoder    enc;

AutoArm autoArm(AUTOARM_ANGLE_DEG, AUTOARM_RATE_DPS, AUTOARM_STABLE_MS);

SafetySupervisor safety(
    FALLEN_ANGLE_DEG, IMU_STALE_CYCLES, LOOP_OVERRUN_MS,
    MAX_DUTY, SATURATION_TIMEOUT_MS
);

// Winkel-PID (innerer Regler)
Pid pidAngle(
    KP_ANGLE, KI_ANGLE, KD_ANGLE, KAW_ANGLE,
    INTEGRAL_MAX_ANGLE,
    -(float)MAX_DUTY, (float)MAX_DUTY
);

// Position-PID (aeusserer Regler -- erst nach stabilem Angle-PD aktivieren)
Pid pidPos(
    KP_POS, KI_POS, KD_POS, KAW_POS,
    20.0f, -MAX_POS_CORRECTION_DEG, MAX_POS_CORRECTION_DEG
);

// ------------------------------------------------------------
// Zustandsmaschine
// ------------------------------------------------------------

State        currentState = State::INIT;
unsigned long fallenStartMs = 0; // Zeitstempel des Eintritts in FALLEN

// Winkel-Sollwert zur Laufzeit trimmbar (Serial "Sp=1.5"), Start aus config.h.
// Gleicht den mechanischen Gleichgewichts-Offset aus, bis der
// Auto-Trim (Phase F) das uebernimmt.
float setpointAngleDeg = SETPOINT_ANGLE_DEG;

// Zustandswechsel mit Logging
void changeState(State next) {
    if (next == currentState) return;
    Logger::printStateChange(currentState, next);
    currentState = next;
}

// ------------------------------------------------------------
// Parameter-Ausgabe fuer Debugging
// ------------------------------------------------------------

void printParams() {
    Logger::printComment("--- Parameter (aenderbar: Kp=/Ki=/Kd=/Sp= + Enter) ---");
    Serial.print("# Kp=");  Serial.print(pidAngle.kp());
    Serial.print(" Ki=");   Serial.print(pidAngle.ki());
    Serial.print(" Kd=");   Serial.print(pidAngle.kd());
    Serial.print(" Sp=");   Serial.println(setpointAngleDeg);
    Serial.print("# MAX_DUTY="); Serial.println(MAX_DUTY);
}

// ------------------------------------------------------------
// Serial lesen (non-blocking):
//   - Einzelzeichen-Befehle (s/q/r/h/p) wirken sofort
//   - alles andere sammelt der Zeilenpuffer bis Enter und wird
//     als Tuning-Befehl geparst ("Kp=3.5", siehe command.h)
// ------------------------------------------------------------

float clampf(float v, float lo, float hi) {
    if (v < lo) return lo;
    if (v > hi) return hi;
    return v;
}

void applyTuneCommand(const TuneCommand& tc) {
    switch (tc.key) {
        case TuneKey::KP:
            pidAngle.setKp(clampf(tc.value, 0.0f, TUNE_KP_MAX));
            break;
        case TuneKey::KI:
            pidAngle.setKi(clampf(tc.value, 0.0f, TUNE_KI_MAX));
            break;
        case TuneKey::KD:
            pidAngle.setKd(clampf(tc.value, 0.0f, TUNE_KD_MAX));
            break;
        case TuneKey::SP:
            setpointAngleDeg = clampf(tc.value, -TUNE_SP_MAX_DEG, TUNE_SP_MAX_DEG);
            break;
        default:
            Logger::printComment("Unbekannter Befehl. Format: Kp=3.5 / Ki= / Kd= / Sp=");
            return;
    }
    printParams();
}

bool isImmediateCommand(char c) {
    return c == 's' || c == 'q' || c == 'r' || c == 'h' || c == 'p';
}

char readSerialCommand() {
    static char    lineBuf[24];
    static uint8_t lineLen = 0;
    char immediate = '\0';

    while (Serial.available() > 0) {
        char c = (char)Serial.read();
        if (c == '\n' || c == '\r') {
            if (lineLen > 0) {
                lineBuf[lineLen] = '\0';
                applyTuneCommand(parseTuneCommand(lineBuf));
                lineLen = 0;
            }
        } else if (lineLen == 0 && isImmediateCommand(c)) {
            immediate = c;
        } else if (lineLen < sizeof(lineBuf) - 1) {
            lineBuf[lineLen++] = c;
        } else {
            lineLen = 0; // Overflow: Zeile verwerfen
        }
    }
    return immediate;
}

// ------------------------------------------------------------
// Uebergangs-Helfer
// ------------------------------------------------------------

// ------------------------------------------------------------
// LED-Zustandsanzeige (headless Diagnose, LED_BUILTIN)
//   Setup laeuft:  dauerhaft an (bis Zustandsmaschine uebernimmt)
//   CALIBRATING:   schnelles Blinken (10 Hz)
//   IDLE:          langsames Blinken (1 Hz)
//   BALANCING:     dauerhaft an
//   FALLEN:        Doppelblitz pro Sekunde
//   E_STOP:        kurzer Einzelblitz alle 2 s
// ------------------------------------------------------------

void updateStateLed(unsigned long nowMs) {
    bool on = false;
    unsigned long phase = nowMs % 1000;
    switch (currentState) {
        case State::CALIBRATING: on = (nowMs / 50) % 2;  break;
        case State::IDLE:        on = (nowMs / 500) % 2; break;
        case State::BALANCING:   on = true;              break;
        case State::FALLEN:
            on = (phase < 100) || (phase >= 200 && phase < 300);
            break;
        case State::E_STOP:      on = (nowMs % 2000) < 100; break;
        default:                 on = false;             break;
    }
    digitalWrite(LED_BUILTIN, on ? HIGH : LOW);
}

// Regler-Zustand loeschen und Balancieren starten (aus IDLE)
void startBalancing() {
    pidAngle.reset();
    pidPos.reset();
    enc.reset();
    motors.resetStall();
    safety.reset();
    changeState(State::BALANCING);
}

// Peripherie neu initialisieren (aus E_STOP/INIT per 'r')
bool tryReinit() {
    motors.stop();
    motors.resetStall();
    enc.reset();
    pidAngle.reset();
    pidPos.reset();
    return controller.begin() && imu.begin();
}

// ------------------------------------------------------------
// Setup
// ------------------------------------------------------------

void setup() {
    // LED sofort an: "Strom da, setup laeuft" -- headless sichtbar
    pinMode(LED_BUILTIN, OUTPUT);
    digitalWrite(LED_BUILTIN, HIGH);

    Serial.begin(SERIAL_BAUD);
    // Begrenzt auf Serial warten -- ohne USB-Host bootet die Firmware
    // nach SERIAL_WAIT_MS headless weiter (Phase A)
    unsigned long serialWaitStart = millis();
    while (!Serial && (millis() - serialWaitStart) < SERIAL_WAIT_MS) {
        delay(10);
    }

    Logger::printComment("BalanceBot startet...");

    // Motor Carrier initialisieren
    if (!controller.begin()) {
        Logger::printComment("FEHLER: Motor Carrier nicht gefunden!");
        changeState(State::E_STOP);
        return;
    }
    controller.reboot();
    delay(500);
    motors.begin();
    enc.begin();

    // IMU initialisieren
    if (!imu.begin()) {
        Logger::printComment("FEHLER: BNO055 nicht gefunden!");
        motors.stop();
        changeState(State::E_STOP);
        return;
    }

    // Initialisierung erfolgreich --> Kalibrierung starten
    changeState(State::CALIBRATING);
    Logger::printComment("Warte auf IMU-Kalibrierung... (Gyro und Accel Stufe 2)");
    Logger::printHeader();
}

// ------------------------------------------------------------
// Hauptschleife
// ------------------------------------------------------------

void loop() {
    // --- Timing ---
    static unsigned long prevMs = 0;
    unsigned long nowMs = millis();
    unsigned long elapsedMs = nowMs - prevMs;

    // LED-Zustandsanzeige jeden Durchlauf aktualisieren (billig, headless wichtig)
    updateStateLed(nowMs);

    // Regelzyklus einhalten: nicht vor LOOP_PERIOD_MS
    if (elapsedMs < LOOP_PERIOD_MS) return;
    float dt = (float)elapsedMs / 1000.0f; // [s]
    prevMs = nowMs;

    // --- Serial-Befehle lesen ---
    char cmd = readSerialCommand();
    if (cmd == 'h') { Logger::printHeader(); }
    if (cmd == 'p') { printParams(); }

    // --- IMU immer lesen (fuer Sicherheitscheck) ---
    imu.update();
    float pitch = imu.pitch();

    // --- Encoder lesen ---
    enc.update(dt);

    // ============================================================
    // Zustandsmaschine
    // ============================================================
    switch (currentState) {

        // ---------------------------------------------------------
        case State::INIT:
            // Sollte nach setup() nicht mehr auftreten -- Fallback wie E_STOP
            if (cmd == 'r') {
                if (tryReinit()) {
                    changeState(State::CALIBRATING);
                } else {
                    Logger::printComment("FEHLER: Reset fehlgeschlagen");
                }
            }
            break;

        // ---------------------------------------------------------
        case State::CALIBRATING: {
            static unsigned long calibratingSinceMs = 0;
            if (calibratingSinceMs == 0) calibratingSinceMs = nowMs;

            // Voll kalibriert ODER Timeout mit wenigstens Gyro-Kalibrierung
            // (Accel-Kalibrierung gelingt headless oft nicht, s. config.h)
            bool fullyCalibrated  = imu.isCalibrated();
            bool timeoutFallback  = (nowMs - calibratingSinceMs) >= CALIB_TIMEOUT_MS
                                    && imu.gyroCalibrated();

            if ((fullyCalibrated || timeoutFallback) && abs(pitch) < RECOVERY_ANGLE_DEG) {
                Logger::printComment(fullyCalibrated
                    ? "IMU kalibriert. Aufrecht hinstellen zum Auto-Arm ('s' = sofort)."
                    : "WARNUNG: Accel unkalibriert (Timeout) -- fahre mit Gyro fort.");
                calibratingSinceMs = 0;
                autoArm.reset();
                changeState(State::IDLE);
            }
            break;
        }

        // ---------------------------------------------------------
        case State::IDLE: {
            motors.stop();

            // Auto-Arm: aufrecht + ruhig fuer AUTOARM_STABLE_MS --> los
            bool armed = autoArm.update(pitch, imu.pitchRate(), nowMs);

            // Manueller Start bleibt als Override erhalten
            bool manualStart = (cmd == 's');
            if (manualStart && abs(pitch) >= RECOVERY_ANGLE_DEG) {
                Logger::printComment("FEHLER: Zu grosser Startwinkel -- aufrecht hinstellen!");
                manualStart = false;
            }

            if (armed || manualStart) {
                Logger::printComment(armed ? "Auto-Arm --> BALANCING" : "Manueller Start --> BALANCING");
                startBalancing();
                break;
            }

            if (abs(pitch) > FALLEN_ANGLE_DEG) {
                autoArm.reset();
                changeState(State::FALLEN);
            }
            break;
        }

        // ---------------------------------------------------------
        case State::BALANCING: {
            // --- SafetySupervisor: Tilt, Overrun, IMU-Stale, Saettigung ---
            // Laeuft VOR der neuen Stellgroesse; duty = zuletzt angewendeter Wert
            SafetyVerdict verdict = safety.check(
                pitch, imu.pitchRate(), elapsedMs, motors.lastDuty(), nowMs);
            if (verdict != SafetyVerdict::OK) {
                motors.stop();
                switch (verdict) {
                    case SafetyVerdict::FALLEN_TILT:
                        changeState(State::FALLEN);
                        break;
                    case SafetyVerdict::FALLEN_SATURATION:
                        Logger::printComment("SICHERHEIT: Duty dauerhaft am Anschlag --> FALLEN");
                        changeState(State::FALLEN);
                        break;
                    case SafetyVerdict::ESTOP_IMU_STALE:
                        Logger::printComment("SICHERHEIT: IMU eingefroren --> E_STOP");
                        changeState(State::E_STOP);
                        break;
                    case SafetyVerdict::ESTOP_LOOP_OVERRUN:
                        Logger::printComment("SICHERHEIT: Loop-Overrun --> E_STOP");
                        changeState(State::E_STOP);
                        break;
                    default:
                        break;
                }
                break;
            }

            // --- Quit-Befehl (manueller Override) ---
            if (cmd == 'q') {
                motors.stop();
                autoArm.reset();
                changeState(State::IDLE);
                break;
            }

            // --- Aeusserer Regler: Position --> Winkel-Sollwert ---
            // TODO: Positionsregler erst aktivieren wenn Winkelregler stabil ist!
            // Vorlaeufig: Winkel-Sollwert zur Laufzeit trimmbar ("Sp=1.5")
            float angleSp = setpointAngleDeg;
            // Wenn Positionsregler aktiv (KP_POS > 0):
            // float posError = 0.0f - enc.positionM();  // Soll: an Ort bleiben
            // float posCorrection = pidPos.compute(posError, dt);
            // angleSp = setpointAngleDeg + posCorrection;

            // --- Innerer Regler: Winkel --> Duty ---
            // D-Anteil aus der gemessenen Gyro-Rate (Phase C):
            // error = sp - pitch, sp quasi konstant --> d(error)/dt = -pitchRate
            float angleError = angleSp - pitch;
            float duty_f     = pidAngle.compute(angleError, -imu.pitchRate(), dt);
            int   duty       = (int)duty_f;

            // --- Motoren ansteuern ---
            motors.setDrive(duty);

            // Kein checkStall() hier: hoher Duty bei ~0 Radgeschwindigkeit
            // ist beim Balancieren legitim. Festhaenger faengt der
            // Saettigungs-Timeout des SafetySupervisors ab.

            // --- Logging ---
            Logger::printData(
                nowMs,
                currentState,
                pitch,
                imu.pitchRate(),
                pidAngle.pTerm(),
                pidAngle.iTerm(),
                pidAngle.dTerm(),
                motors.lastDuty(),
                enc.position(),
                enc.positionM()
            );
            break;
        }

        // ---------------------------------------------------------
        case State::FALLEN:
            motors.stop();

            if (fallenStartMs == 0) {
                fallenStartMs = nowMs; // Eintrittszeit merken
            }

            // Warten bis Wartezeit abgelaufen und Bot aufgerichtet
            if ((nowMs - fallenStartMs) >= FALLEN_WAIT_MS) {
                if (abs(pitch) < RECOVERY_ANGLE_DEG) {
                    fallenStartMs = 0;
                    pidAngle.reset();
                    autoArm.reset();
                    changeState(State::IDLE); // Auto-Arm uebernimmt von hier
                }
            }
            break;

        // ---------------------------------------------------------
        case State::E_STOP:
            // Motoren AUS -- bleibt hier bis manueller Reset ('r').
            // Bewusst KEIN Auto-Recovery: E_STOP-Ursachen sind Anomalien
            // (IMU-Ausfall, Overrun), die ein Mensch pruefen soll.
            motors.stop();

            if (cmd == 'r') {
                // Direkter Neuinitialisierungs-Versuch (frueher: doppeltes 'r'
                // noetig, weil erst nach INIT gewechselt wurde)
                if (tryReinit()) {
                    changeState(State::CALIBRATING);
                } else {
                    Logger::printComment("FEHLER: Reset fehlgeschlagen");
                }
            }
            break;
    }
}
