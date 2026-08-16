#pragma once

// ============================================================
// logger.h -- BalanceBot: CSV-Serial-Logger
//
// Gibt alle Zustandsgroessen als CSV-Zeile ueber Serial aus.
// Format (eine Zeile pro Regelzyklus):
//
//   millis,state,pitch,pitch_rate,p,i,d,duty,pos_counts,pos_m
//
// Diese Spalten werden von python/acquire.py eingelesen und
// von python/process.py verarbeitet.
//
// Zusatzfunktionen:
//   - Header auf Anfrage ausgeben (Serial-Befehl 'h')
//   - Zustandsaenderungen separat ausgeben (klar lesbar im Monitor)
// ============================================================

#include <Arduino.h>
#include "state_machine.h"

class Logger {
public:
    // CSV-Header ausgeben (beim Start oder auf Anfrage)
    static void printHeader();

    // Eine Datenzeile ausgeben
    // Alle Werte kommen direkt aus den jeweiligen Modulen
    static void printData(
        unsigned long timeMs,
        State         state,
        float         pitch,
        float         pitchRate,
        float         pTerm,
        float         iTerm,
        float         dTerm,
        int           duty,
        int           positionCounts,
        float         positionM
    );

    // Zustandsaenderung ausgeben (als Kommentar, beginnt mit '#')
    // Kommentarzeilen werden von Python uebersprungen
    static void printStateChange(State from, State to);

    // Allgemeine Statusmeldung (als Kommentar, z.B. fuer Fehlermeldungen)
    static void printComment(const char* msg);
};
