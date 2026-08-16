# Phase A Abnahme (Teil 1) + erster Balancierversuch (2026-08-07)

**Firmware:** `balance` (Headless/Auto-Arm, IMUPLUS, per-Vorzeichen-Totzone, gemessene Vorzeichenkette)
**Aufbau:** Bot auf dem Boden, per USB-Kabel von Hand gesichert (starkes Schwingen). Akku 3.57 V.
**Hinweis Vorgehen:** Bodenkontakt war laut Commissioning-Plan erst ab Phase 5+ vorgesehen —
Versuch verlief glimpflich, weitere Tests wieder mit Rädern in der Luft bis Modell + Tuning stehen.

## Was funktioniert hat (ohne Tastendruck)

1. `CALIBRATING → IDLE` nach IMU-Kalibrierung ✓
2. **Auto-Arm** → `BALANCING` nach Aufrechtstellen ✓
3. **16+ s durchgehend BALANCING** bei exakten 100 Hz (Zeitstempel im 10-ms-Raster,
   kein Loop-Overrun), kein falscher E-STOP ✓
   (der alte Stall-Check hätte hier mehrfach fälschlich ausgelöst — Duty 45 bei
   niedriger Radgeschwindigkeit trat wiederholt auf)
4. **Vorzeichenkette im Regelbetrieb validiert:** Pitch > 0 (rückwärts kippen) →
   Duty < 0 (rückwärts fahren, in den Fall hinein) ✓
5. **Gyro-Fix validiert:** geloggte `pitch_rate` stimmt numerisch mit der
   Ableitung des Pitch überein (Achse gyro.x, Vorzeichen, °/s-Umrechnung korrekt)

## Regelverhalten (ungetunt, wie erwartet schwingend)

- Amplitude wächst von ±1.5° auf ±10–15°, zeitweise ±30°; Periode ~0.5 s
- Duty erreicht periodisch den ±45-Anschlag (Sättigung, aber nie > 1 s am Stück
  → Sättigungs-Timeout griff korrekt nicht)
- Position wandert ~0.5 m und pendelt dann — kein Positionsregler aktiv (gewollt)
- Bot fing sich wiederholt selbst, brauchte aber die Hand am Kabel als Begrenzung

**Ursachen des Schwingens (Behebung = Phase 4/5/C):**
1. Startwerte Kp=2.0 / Kd=0.1 ungetunt (Modellwerte fehlen bis CoG-Messung)
2. D-Anteil nutzt noch die verrauschte numerische Fehler-Ableitung statt der
   Gyro-Rate (TODO in pid.cpp, Phase C)
3. Totzonen-Anhebung (23/17) erzeugt ein Mindest-Drehmoment-Quantum → begünstigt
   Grenzzyklus um den Nullpunkt
4. Gleichgewichts-Setpoint = 0° ist nicht exakt (mechanischer Offset, Trim spaeter)

## Offene Abnahme-Punkte Phase A

- [x] Sturztest (2026-08-07, 2× bestanden, beide Richtungen): Cutoff exakt bei
      ±45° → FALLEN, Motoren aus; bleibt in FALLEN solange schräg; nach
      Aufrichten FALLEN → IDLE → Auto-Arm → BALANCING ohne Tastendruck.
      Sättigungsschutz feuerte korrekt nicht (Duty nur 740 ms < 1 s am
      Anschlag, dann griff der Tilt-Cutoff zuerst).
- [x] Headless-Test (2026-08-07 bestanden): Kaltstart nur mit Akku, komplette
      LED-verifizierte Kette Setup → CALIBRATING → IDLE (mit 20-s-Fallback bei
      unvollstaendiger Accel-Kalibrierung) → Auto-Arm → BALANCING → FALLEN
      (>45°, Motoren aus) → Aufrichten → Re-Arm. Kein PC, kein Tastendruck.

## Phase A: ABGENOMMEN (2026-08-07)

Erkenntnisse fuer die Folgephasen:
- BNO055 verliert Kalibrierung bei Stromverlust → Kalibrierungs-Timeout-Fallback
  eingebaut (20 s, dann nur-Gyro); sauberer Fix = Offsets in FlashStorage (Phase E)
- LED-Zustandsanzeige (LED_BUILTIN) fuer Headless-Diagnose ergaenzt
- Beobachtet am Boden (verfruehte Versuche): Aufschaukeln (ungetunt) UND
  Wegfahren in eine Richtung (Setpoint-Offset, PD ohne Positionsschleife
  integriert konstanten Winkelfehler zu Geschwindigkeit) → Phase C/F/G
- Upload-Auto-Reset (1200 bps) seit USB-Abriss unzuverlaessig; Workaround
  Doppel-Klick-Reset in Bootloader; USB-Kabel pruefen/tauschen
