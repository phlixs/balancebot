#pragma once

// ============================================================
// command.h -- BalanceBot: Parser fuer Laufzeit-Tuning-Befehle
//
// Zeilenformat: "<Key>=<Wert>", Keys: Kp, Ki, Kd, Sp
// Beispiele:  Kp=3.5   Kd=0.25   Sp=-1.2
//
// Grossbuchstaben-Keys sind Absicht: die Einzelzeichen-Befehle
// (s/q/r/h/p) bleiben klein und kollidieren so nicht mit dem
// Zeilenpuffer (siehe main.cpp).
//
// Header-only, ohne Arduino-Abhaengigkeit -- nativ testbar
// (pio test -e native).
// ============================================================

#include <string.h>
#include <stdlib.h>

enum class TuneKey : unsigned char { NONE, KP, KI, KD, SP };

struct TuneCommand {
    TuneKey key;
    float   value;
};

// Parst eine abgeschlossene Zeile. key == NONE bei ungueltiger Eingabe.
inline TuneCommand parseTuneCommand(const char* line) {
    TuneCommand cmd{TuneKey::NONE, 0.0f};
    if (line == nullptr) return cmd;

    const char* eq = strchr(line, '=');
    if (eq == nullptr || (eq - line) != 2) return cmd;

    if      (strncmp(line, "Kp", 2) == 0) cmd.key = TuneKey::KP;
    else if (strncmp(line, "Ki", 2) == 0) cmd.key = TuneKey::KI;
    else if (strncmp(line, "Kd", 2) == 0) cmd.key = TuneKey::KD;
    else if (strncmp(line, "Sp", 2) == 0) cmd.key = TuneKey::SP;
    else return cmd;

    char* end = nullptr;
    float v = strtof(eq + 1, &end);
    if (end == eq + 1) {                       // keine Zahl nach '='
        cmd.key = TuneKey::NONE;
        return cmd;
    }
    while (*end == ' ' || *end == '\t' || *end == '\r' || *end == '\n') end++;
    if (*end != '\0') {                        // Muell hinter der Zahl
        cmd.key = TuneKey::NONE;
        return cmd;
    }

    cmd.value = v;
    return cmd;
}
