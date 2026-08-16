# Phase 3 — Motor-Totzone-Identifikation (2026-08-07)

**Sketch:** `deadzone_id` (Sweep 0→45 % in 1-%-Schritten, 200 ms Setzzeit, 5-fach-Mittelung)
**Bedingungen:** Batteriespannung **3.57 V** (Ersatzzelle), Räder in der Luft, beide Motoren gleichzeitig
**Rohdaten:** `deadzone_20260807_114836.csv` (NextCloud raw/) · Plot: `phase3_deadzone_20260807.png`

## Anlaufpunkte (erster Duty mit Encoder-Bewegung)

| Motor | Duty-Vorzeichen am Motor | Bot-Richtung | Anlauf bei |
|-------|--------------------------|--------------|-----------:|
| M1 (links)  | +duty | vorwärts   | **23 %** |
| M1 (links)  | −duty | rückwärts  | **16 %** |
| M2 (rechts) | −duty | vorwärts   | **17 %** |
| M2 (rechts) | +duty | rückwärts  | **23 %** |

## Beobachtungen

1. **Die Totzone ist deutlich größer als die bisherige Schätzung** (10 % in
   `config.h`): Worst Case 23 %, Best Case 16 %.
2. **Systematische Asymmetrie nach Duty-Vorzeichen, nicht nach Motor:** Beide
   Motoren laufen auf der positiven Duty-Seite bei 23 % an, auf der negativen
   bei 16–17 %. Das deutet auf eine Asymmetrie im Carrier-Treiber (H-Brücke/
   PWM-Ansteuerung) hin, nicht auf Motorreibung.
3. **Spannungsabhängigkeit:** Gemessen bei 3.57 V. Bei vollem Akku (4.2 V)
   skaliert der Anlauf-Duty grob mit dem Spannungsverhältnis → erwartet ~19–20 %
   Worst Case. Für Phase E/F ist eine spannungs­kompensierte Totzone sinnvoll
   (der Carrier kann die Batteriespannung messen).
4. **Einheiten-Hinweis Pipeline:** `getCountPerSecond()` des Carriers liefert
   offenbar Counts pro 10-ms-Tick, nicht Counts/s — Abgleich mit den
   Rohzähler-Differenzen aus dem hw_check-Motortest ergibt Faktor ~100.
   Für die Totzonen-Bestimmung irrelevant (nur der Anlaufpunkt zählt).

## Entscheidung (freigegeben 2026-08-07)

**Getrennte Kompensation pro Duty-Vorzeichen**, angewendet pro Motor-Anschluss
(`deadzone.h`, aufgerufen in `motor.cpp::_applyToMotors`):

```
DEADZONE_DUTY_POS = 23    DEADZONE_DUTY_NEG = 17
duty > 0 und duty < POS  → auf +POS anheben
duty < 0 und |duty| < NEG → auf −NEG anheben
```

| Symbol | Beschreibung | Einheit |
|--------|-------------|---------|
| DEADZONE_DUTY_POS | Anlaufpunkt der positiven Duty-Seite (beide Motoren) | % Duty |
| DEADZONE_DUTY_NEG | Anlaufpunkt der negativen Duty-Seite (Maximum beider Motoren) | % Duty |
| duty | Befehl am einzelnen Motor-Anschluss nach Richtungs-Mapping | % Duty |

**Warum nicht ein symmetrischer Wert:** Bei Vorwärtsfahrt liegt M1 auf der
positiven (23 %) und M2 auf der negativen Seite (17 %). Eine gemeinsame
Schwelle (z. B. 20) hätte bei kleinen Befehlen nur jeweils ein Rad anlaufen
lassen → Gieren und halbes Drehmoment genau im Arbeitsbereich des Reglers.
Exakte Anhebung auf den gemessenen Anlaufpunkt je Seite vermeidet das ohne
Überkompensation.
