#pragma once

// ============================================================
// config.h -- BalanceBot: Alle konfigurierbaren Parameter
//
// Alle Tuning-Parameter, Schwellwerte und Systemkonstanten
// stehen hier zentral. Nichts davon soll im Steuercode
// als Magic Number auftauchen.
// ============================================================

// ------------------------------------------------------------
// Mechanik
// ------------------------------------------------------------

// Raddurchmesser [m]
constexpr float WHEEL_DIAMETER_M       = 0.090f;
// Radradius [m]
constexpr float WHEEL_RADIUS_M         = WHEEL_DIAMETER_M / 2.0f;
// Radumfang [m]
constexpr float WHEEL_CIRCUMFERENCE_M  = 3.14159265f * WHEEL_DIAMETER_M;

// Encoder-Ticks pro Radumdrehung (inkl. 100:1 Getriebe, Quadratur)
constexpr int   COUNTS_PER_WHEEL_REV   = 1200;
// Meter pro Count
constexpr float METERS_PER_COUNT       = WHEEL_CIRCUMFERENCE_M / COUNTS_PER_WHEEL_REV;

// Schwerpunkthoehe ueber Achsmitte [m]
// Gemessen 2026-08-09 per Auslenkungsmethode: 7.6 +- 0.9 mm
// (vorher 30 mm geschaetzt -- die Schaetzung war um Faktor 4 zu gross).
// Details: messungen/results/phase4_cog_20260809.md
// Hinweis: Die Konstante wird im Steuercode derzeit nicht verwendet, sie
// dokumentiert den Modellparameter. Rechnung laeuft ueber python/system_id.py.
constexpr float COG_HEIGHT_M           = 0.0076f;

// Gesamtmasse [kg]
// Gewogen 2026-08-09: 190 g (vorheriger Wert 204 g, Aufbau seither geaendert)
constexpr float TOTAL_MASS_KG          = 0.190f;

// ------------------------------------------------------------
// Abtastzeit
// ------------------------------------------------------------

// Soll-Abtastzeit der Regelschleife [ms]
// 10 ms = 100 Hz. Nicht unter 10 ms gehen (Bandbreite des inversen Pendels)
constexpr unsigned long LOOP_PERIOD_MS = 10;

// ------------------------------------------------------------
// Motoren / Leistungselektronik
// ------------------------------------------------------------

// Maximaler Duty-Cycle [%]
// Motorstall: 1.03 A, Treibergrenze: 0.50 A
// 0.50 / 1.03 * 100 = 48.5 %  --> konservativ auf 45 % begrenzt
// Waehrend der ersten Inbetriebnahme: noch konservativer beginnen (z.B. 30)
constexpr int   MAX_DUTY               = 45;

// Mindest-Duty fuer Loslaufen (Totzone-Kompensation) [%]
// Gemessen 2026-08-07 bei 3.57 V (deadzone_id): Anlauf 23 % auf der
// positiven, 16-17 % auf der negativen Duty-Seite (beide Motoren gleich
// -- Asymmetrie liegt im Carrier-Treiber). Kompensation deshalb getrennt
// pro Duty-Vorzeichen, angewendet pro Motor-Anschluss (deadzone.h).
// Details: messungen/results/phase3_deadzone_20260807.md
constexpr int   DEADZONE_DUTY_POS      = 23;
constexpr int   DEADZONE_DUTY_NEG      = 17;

// Maximale Aenderung des Duty-Cycles pro Abtastschritt (Slew-Rate) [%/Schritt]
constexpr int   DUTY_SLEW_RATE         = 20;

// Stall-Erkennung:
// Wenn abs(duty) >= STALL_DUTY_THRESHOLD und abs(speed) <= STALL_SPEED_THRESHOLD
// fuer STALL_TIMEOUT_MS ms --> E_STOP ausloesen
constexpr int   STALL_DUTY_THRESHOLD   = 30;    // Duty-Wert ab dem Stall moeglich
constexpr int   STALL_SPEED_THRESHOLD  = 5;     // Encoder-Counts/s unter denen "zu langsam"
constexpr int   STALL_TIMEOUT_MS       = 500;   // Zeit bis Stall-E_STOP [ms]

// ------------------------------------------------------------
// Zustandsmaschine / Sicherheit
// ------------------------------------------------------------

// Sicherheits-Kippwinkel [Grad]
// Ueber diesem Winkel gilt der Bot als "gefallen" --> FALLEN-Zustand
constexpr float FALLEN_ANGLE_DEG       = 45.0f;

// Winkel fuer Rueckkehr aus FALLEN nach IDLE [Grad]
// Bot muss unter diesem Winkel stehen, bevor Motoren wieder aktiv werden
constexpr float RECOVERY_ANGLE_DEG     = 15.0f;

// Wartezeit nach FALLEN vor erneutem Versuch [ms]
constexpr unsigned long FALLEN_WAIT_MS = 1000;

// ------------------------------------------------------------
// Headless-Betrieb / Auto-Arm (Phase A)
// ------------------------------------------------------------

// Maximale Wartezeit auf Serial-Verbindung beim Boot [ms]
// Danach startet die Firmware headless (Akku-Betrieb ohne PC)
constexpr unsigned long SERIAL_WAIT_MS     = 1500;

// Auto-Arm: Bot armiert selbst, wenn er aufrecht und ruhig gehalten wird.
// Winkel- und Raten-Fenster muessen AUTOARM_STABLE_MS lang
// ununterbrochen eingehalten sein.
constexpr float         AUTOARM_ANGLE_DEG  = 6.0f;   // [Grad]
constexpr float         AUTOARM_RATE_DPS   = 20.0f;  // [Grad/s]
constexpr unsigned long AUTOARM_STABLE_MS  = 800;    // [ms]

// Kalibrierungs-Timeout: BNO055 verliert die Kalibrierung bei Stromverlust,
// und die Accel-Kalibrierung (6-Lagen-Prozedur) gelingt headless oft nicht.
// Nach dem Timeout geht es mit nur-Gyro-Kalibrierung weiter (Folge:
// evtl. wenige Grad Pitch-Offset -- faengt der Setpoint-Trim spaeter ab).
// TODO Phase E: Kalibrierungs-Offsets in FlashStorage persistieren.
constexpr unsigned long CALIB_TIMEOUT_MS   = 20000;  // [ms]

// ------------------------------------------------------------
// SafetySupervisor (Phase A)
// ------------------------------------------------------------

// IMU-Stale: exakt identische Pitch+Rate-Werte ueber so viele Zyklen
// hintereinander --> E_STOP (50 Zyklen = 500 ms bei eingefrorener IMU)
constexpr int           IMU_STALE_CYCLES      = 50;

// Loop-Overrun: einzelner Regelzyklus laenger als dieser Wert --> E_STOP
// (Regelung war 5+ Perioden blind)
constexpr unsigned long LOOP_OVERRUN_MS       = 50;

// Saettigungs-Timeout: |duty| ununterbrochen am MAX_DUTY-Anschlag [ms]
// --> Bot kann sich nicht mehr fangen --> FALLEN
// (ersetzt den Stall-Check waehrend BALANCING: hoher Duty bei ~0
// Radgeschwindigkeit ist beim Balancieren ein legitimer Zustand!)
constexpr unsigned long SATURATION_TIMEOUT_MS = 1000;

// ------------------------------------------------------------
// PID-Winkelregler (innerer Regler)
// Stellt Kippwinkel auf Sollwert (0 Grad = aufrecht)
// ------------------------------------------------------------

// Proportionalverstaerkung
// TODO: Tuning -- Startpunkt aus Modell berechnen
constexpr float KP_ANGLE               = 2.0f;

// Integralverstaerkung
// Mit Ki=0 starten bis P+D stabil balanciert!
constexpr float KI_ANGLE               = 0.0f;

// Differentialverstaerkung
constexpr float KD_ANGLE               = 0.1f;

// Anti-Windup: Tracking-Verstaerkung (Rueckkopplung bei Saettigung)
// Kaw = 1/Ti = Ki/Kp (typischer Startwert)
// Nur aktiv wenn KI_ANGLE > 0
constexpr float KAW_ANGLE              = 0.1f;

// Integralbegrenzung [%] (als absoluter Wert des Integralbeitrags)
constexpr float INTEGRAL_MAX_ANGLE     = 20.0f;

// Winkel-Sollwert [Grad]
// Kann per Serial justiert werden um mechanischen Offset auszugleichen
constexpr float SETPOINT_ANGLE_DEG     = 0.0f;

// ------------------------------------------------------------
// PID-Positionsregler (aeusserer Regler -- spaetere Phase)
// Stellt Fahrzeugposition (Encoder-Summe) auf Sollwert
// ------------------------------------------------------------

constexpr float KP_POS                 = 0.0f;   // TODO: erst nach stabilem Angle-PD tunen
constexpr float KI_POS                 = 0.0f;
constexpr float KD_POS                 = 0.0f;
constexpr float KAW_POS                = 0.0f;

// Maximaler Positionsfehler der als Winkelkorrektur aufaddiert wird [Grad]
constexpr float MAX_POS_CORRECTION_DEG = 5.0f;

// ------------------------------------------------------------
// Laufzeit-Tuning per Serial (command.h) -- Schutzgrenzen
// gegen Tippfehler ("Kp=35" statt "Kp=3.5" u.ae.)
// ------------------------------------------------------------

constexpr float TUNE_KP_MAX     = 20.0f;  // [Duty%/Grad]
constexpr float TUNE_KI_MAX     = 10.0f;  // [Duty%/(Grad*s)]
constexpr float TUNE_KD_MAX     = 5.0f;   // [Duty%/(Grad/s)]
constexpr float TUNE_SP_MAX_DEG = 15.0f;  // [Grad] max. Setpoint-Betrag

// ------------------------------------------------------------
// IMU
// ------------------------------------------------------------

// BNO055 I2C-Adresse (Adafruit-Bibliothek)
constexpr uint8_t BNO055_I2C_ADDR     = 0x28;
// Initialisierungs-ID (Adafruit-Konvention)
constexpr int     BNO055_SENSOR_ID    = 55;

// ------------------------------------------------------------
// Serielle Kommunikation / Logging
// ------------------------------------------------------------

// Baudrate
constexpr long    SERIAL_BAUD         = 115200;

// CSV-Header fuer Logging (muss mit Logger::printHeader() uebereinstimmen)
// Format: millis,state,pitch,pitch_rate,p,i,d,duty,pos_counts,pos_m
// Spaltenzahl: 10 (python/config.py BALANCE_COLUMNS erwartet genau diese)
