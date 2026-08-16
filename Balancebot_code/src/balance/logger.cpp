// ============================================================
// logger.cpp -- BalanceBot: CSV-Logger-Implementierung
// ============================================================

#include "logger.h"

void Logger::printHeader() {
    // Kommentarzeile: Python ueberspringt Zeilen die mit '#' beginnen
    Serial.println("# BalanceBot CSV-Log");
    // Spalten-Header: muss mit printData() uebereinstimmen!
    Serial.println("millis,state,pitch,pitch_rate,p,i,d,duty,pos_counts,pos_m");
}

void Logger::printData(
    unsigned long timeMs,
    State         state,
    float         pitch,
    float         pitchRate,
    float         pTerm,
    float         iTerm,
    float         dTerm,
    int           duty,
    int           positionCounts,
    float         positionM)
{
    // Kompaktes CSV-Format, 2 Nachkommastellen fuer Gleitkommazahlen
    Serial.print(timeMs);
    Serial.print(',');
    Serial.print((uint8_t)state);   // Zustand als Zahl (0=INIT, 1=CAL, ...)
    Serial.print(',');
    Serial.print(pitch,     2);
    Serial.print(',');
    Serial.print(pitchRate, 2);
    Serial.print(',');
    Serial.print(pTerm,     2);
    Serial.print(',');
    Serial.print(iTerm,     2);
    Serial.print(',');
    Serial.print(dTerm,     2);
    Serial.print(',');
    Serial.print(duty);
    Serial.print(',');
    Serial.print(positionCounts);
    Serial.print(',');
    Serial.println(positionM, 4);   // 4 Stellen fuer Meter (mm-Genauigkeit)
}

void Logger::printStateChange(State from, State to) {
    // Kommentarzeile mit Zeitstempel -- Python ueberspringt '#'-Zeilen
    Serial.print("# ");
    Serial.print(millis());
    Serial.print(" STATE: ");
    Serial.print(stateName(from));
    Serial.print(" --> ");
    Serial.println(stateName(to));
}

void Logger::printComment(const char* msg) {
    Serial.print("# ");
    Serial.println(msg);
}
