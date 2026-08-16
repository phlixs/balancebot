#pragma once

// ============================================================
// state_machine.h -- BalanceBot: Zustandsmaschine
//
// Zustaende und Uebergangsbedingungen des BalanceBots.
//
// Zustandsdiagramm (Phase A: headless + Auto-Arm):
//
//   INIT
//    |-- Carrier + IMU OK --> CALIBRATING
//    |-- Fehler           --> E_STOP
//
//   CALIBRATING
//    |-- Kalibrierung fertig UND |pitch| < RECOVERY_ANGLE --> IDLE
//
//   IDLE  (Motoren aus, Auto-Arm aktiv)
//    |-- aufrecht+ruhig fuer AUTOARM_STABLE_MS --> BALANCING (Auto-Arm)
//    |-- Serial "s" (manueller Start)          --> BALANCING
//    |-- |pitch| > FALLEN_ANGLE                --> FALLEN
//
//   BALANCING  (SafetySupervisor prueft jeden Zyklus)
//    |-- Serial "q" (quit)          --> IDLE (Motoren aus)
//    |-- |pitch| > FALLEN_ANGLE     --> FALLEN
//    |-- Duty dauerhaft am Anschlag --> FALLEN (Saettigungs-Timeout)
//    |-- IMU eingefroren            --> E_STOP
//    |-- Loop-Overrun               --> E_STOP
//
//   FALLEN  (Auto-Recovery)
//    |-- Wartezeit abgelaufen und |pitch| < RECOVERY_ANGLE --> IDLE
//        (dort armiert der Auto-Arm selbststaendig neu)
//
//   E_STOP  (nur manueller Reset -- Anomalie, Mensch soll pruefen)
//    |-- Serial "r" (reset) --> Reinit --> CALIBRATING
//    |-- Immer: Motoren sofort 0!
// ============================================================

// Aufzaehlung aller moeglichen Zustaende
enum class State : uint8_t {
    INIT,           // Systemstart, Peripherie noch nicht initialisiert
    CALIBRATING,    // IMU-Kalibrierung laeuft
    IDLE,           // Bereit, Motoren aus, wartet auf Startbefehl
    BALANCING,      // Aktive Regelschleife
    FALLEN,         // Sicherheitswinkel ueberschritten, Motoren aus
    E_STOP          // Not-Aus (Stall, Init-Fehler), Motoren aus
};

// Lesbare Bezeichnung fuer Serial-Ausgaben
inline const char* stateName(State s) {
    switch (s) {
        case State::INIT:        return "INIT";
        case State::CALIBRATING: return "CALIBRATING";
        case State::IDLE:        return "IDLE";
        case State::BALANCING:   return "BALANCING";
        case State::FALLEN:      return "FALLEN";
        case State::E_STOP:      return "E_STOP";
        default:                 return "UNKNOWN";
    }
}
