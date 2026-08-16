# Phase 6 — Erster geschlossener Regelkreis am Boden (2026-08-10)

**Aufbau:** Bot auf dem Boden, Räder montiert, erster Versuch mit den aus dem
gemessenen Modell abgeleiteten Gains. Zwei Varianten gefahren: mit USB-Kabel
(angeleint, mit Aufzeichnung) und frei ohne Kabel.

**Gains:** `Kp=6.96  Ki=0.00  Kd=0.32  Sp=3.20`
(aus `system_id.py --L-mm 7.6 --pole 12.14`, siehe `phase4_cog_20260809.md`)

**Beobachtung am Gerät:** „Ohne Kabel schaukelt er sich sehr auf und fährt
davon. Mit Kabel stößt er auch gegen Gegenstände und stabilisiert sich
darüber. Er schwankt in jedem Fall sehr stark."

---

## Zusammenfassung

Der Versuch hat **zwei voneinander unabhängige Probleme** offengelegt. Sie
haben verschiedene Ursachen und verschiedene Gegenmittel, und man darf sie
nicht gleichzeitig zu beheben versuchen:

1. **Wegfahren** — der Setpoint `Sp=3.20` ist zu groß. Der Regler kommandiert
   dauerhaft Vorwärtsfahrt. Reiner Auslegungsfehler meinerseits.
2. **Starkes Schwanken** — ein Grenzzyklus bei 4.5 Hz. Ursache ist die
   **Totzeit der Regelkette**, die das Modell nicht kennt.

Fortschritt trotzdem: Der Bot blieb **12.3 s durchgehend im Zustand
BALANCING** (272817 → 285077). Alle vorherigen Versuche endeten nach 3–8 s.

---

## Problem 1: Der Setpoint war zu groß

### Befund

In der ruhigen Anfangsphase (272820 … 273840, gut 1 s):

| Größe | Beobachtung |
|-------|-------------|
| Pitch | 0 … +1.5°, im Mittel ≈ +0.9° |
| Duty | durchgehend **positiv**, 15 … 45 |
| Position | 0 → 1575 Counts = **0.371 m in 1.02 s** |

Der Regler fährt also permanent vorwärts. Der Grund steht direkt in der
Reglergleichung:

```
Fehler = Sp - pitch = 3.20 - 0.9 = +2.3 Grad
p-Anteil = Kp * Fehler = 6.96 * 2.3 = 16 % Duty  (dauerhaft, einseitig)
```

| Symbol | Beschreibung | Einheit |
|--------|-------------|---------|
| Sp | Winkel-Sollwert (Gleichgewichts-Trim) | ° |
| pitch | gemessener Kippwinkel | ° |
| Kp | P-Verstärkung des Winkelreglers | Duty%/° |

Der Bot versucht, einen Sollwinkel zu halten, der nicht sein Gleichgewicht
ist. Um dort hinzukommen, muss er beschleunigen — und weil er den Winkel nie
erreicht, beschleunigt er immer weiter. Das ist das beobachtete „Wegfahren".

### Warum meine Vorhersage von 3.2° falsch war

Der Wert stammte aus der Ruhelage des hängenden Bots (Phase 4): Die
Rahmenplatte stand dort 3.18° gegen die Waagerechte, und weil eine 180°-Drehung
um die waagerechte Radachse eine waagerechte Ebene wieder auf eine waagerechte
abbildet, gilt derselbe Betrag im aufrechten Gleichgewicht.

Die Argumentation ist geometrisch korrekt — sie beantwortet aber die falsche
Frage. Sie liefert den Winkel der **Rahmenplatte**. Der Regler arbeitet mit dem
Winkel, den die **IMU** meldet, und zwischen beiden liegt der Einbauwinkel des
BNO055 auf dem Motor Carrier. **Dieser Einbauwinkel wurde nie vermessen.**

Ich hatte den Vorbehalt zwar notiert („verbindlich wird der Trim erst aus der
IMU"), aber den Wert trotzdem als Startwert ausgegeben. Bei einem Bot, dessen
Sättigungswinkel 6.5° beträgt, ist ein Setpoint-Fehler von 2.3° kein
Feinheitsproblem, sondern ein Drittel des gesamten Arbeitsbereichs.

### Wie der Trim richtig bestimmt wird

Nicht über Geometrie, sondern über die Daten: **Sp ist dort richtig, wo der
mittlere Duty null wird.** Bleibt der Duty im Mittel positiv, ist Sp zu groß;
bleibt er negativ, zu klein.

Aus dem Mittelwert der Anfangsphase folgt für diesen Aufbau **Sp ≈ +0.7 … +1.0**.

Der D-Anteil stört diese Auswertung nicht: Im quasistationären Mittel ist die
Rate null, also mittelt sich `Kd·rate` heraus. Es zählt allein der P-Anteil.

---

## Problem 2: Grenzzyklus bei 4.5 Hz durch Totzeit

### Befund

Zwischen 274630 und 277710 schwingt der Bot mit klar ausgeprägter Periode.
Ausgezählte Abstände aufeinanderfolgender positiver Umkehrpunkte:

```
240, 220, 200, 220, 200, 210, 190, 200, 210, 230, 230, 250, 230, 250  [ms]
```

Mittelwert **220 ms → 4.5 Hz**. Amplitude ±20 … 25°, Duty nahezu durchgehend
an ±45 — der Steller ist also gesättigt und arbeitet praktisch als Relais.

### Warum das dem Modell widerspricht

Für `Kp=6.96 / Kd=0.32` sagt das lineare Modell (ohne Totzeit) einen gut
gedämpften geschlossenen Kreis voraus:

```
s^2 + b*Kd_rad*s + (b*Kp_rad - a21) = 0
s^2 + 33.9*s + 590.4 = 0
   ->  omega_n = 24.3 rad/s = 3.87 Hz,   zeta = 0.70
```

| Symbol | Beschreibung | Einheit |
|--------|-------------|---------|
| a21 | Instabilitätsterm der Strecke, = p² | 1/s² |
| b | Stellwirkung, Radmoment pro Duty-% geteilt durch J | rad/s² pro % |
| Kp_rad, Kd_rad | Verstärkungen in rad-Einheiten | %/rad, %/(rad/s) |
| omega_n | Eigenfrequenz des geschlossenen Kreises | rad/s |
| zeta | Dämpfungsgrad des geschlossenen Kreises | – |

Beobachtet wurde eine **Dauerschwingung**, also ζ ≈ 0 statt 0.70. Die Frequenz
liegt in derselben Größenordnung wie der Entwurf, die Dämpfung ist komplett
verschwunden. Das ist die Signatur von **Phasenverlust**, nicht von falscher
Verstärkung.

### Die Rechnung mit Totzeit

Totzeit T dreht Phase, ohne die Amplitude zu ändern. Die charakteristische
Gleichung wird zu

```
s^2 - a21 + b*(Kp_rad + Kd_rad*s) * exp(-s*T) = 0
```

Marginale Stabilität heißt s = jω. Nach Real- und Imaginärteil getrennt:

```
Im:   Kd_rad*w*cos(w*T) - Kp_rad*sin(w*T) = 0    ->  w*T = atan(Kd_rad*w / Kp_rad)
Re:  -w^2 - a21 + b*(Kp_rad*cos(w*T) + Kd_rad*w*sin(w*T)) = 0
```

Die erste Gleichung liefert die Phase, Einsetzen in die zweite ergibt eine
Gleichung allein in ω. Implementiert in `python/system_id.py`
(`critical_delay()`), Ausgabe bei jedem Lauf.

**Ergebnis für den gefahrenen Entwurf: T_krit = 28.7 ms.**

### Das Totzeitbudget der Kette

| Anteil | Wert | Quelle |
|--------|------|--------|
| Abtastung | 10.0 ms | `LOOP_PERIOD_MS`, ADR-0006 |
| Halteglied (halbe Periode) | 5.0 ms | Abtast-Halte-Charakteristik |
| I2C-Verkehr | 6.4 ms | Phase-1-Messung, Mittelwert |
| **Summe der bekannten Anteile** | **21.4 ms** | |
| BNO055-Fusionsverzögerung | nicht vermessen | kommt obendrauf |

Die bekannten 21.4 ms liegen bereits bei **75 %** der kritischen 28.7 ms.
Rechnet man die Fusionsverzögerung des BNO055 hinzu — der Sensor filtert und
fusioniert intern, bevor er den Euler-Winkel herausgibt — ist die Grenze
überschritten. Die beobachtete Dauerschwingung ist damit erklärt.

### Warum 4.5 Hz und nicht die vorhergesagten 5.7 Hz

Die lineare Rechnung sagt den Grenzzyklus bei 5.67 Hz voraus, gemessen wurden
4.5 Hz. Der Unterschied ist kein Widerspruch, sondern eine Folge der Sättigung:

Bei ±45 % Anschlag arbeitet der Steller als Relais. Seine **effektive**
Verstärkung ist dadurch kleiner als das eingestellte Kp — die Beschreibungs\-
funktion eines gesättigten Gliedes fällt mit wachsender Amplitude. Und eine
kleinere effektive Verstärkung verschiebt den Grenzzyklus zu **niedrigeren**
Frequenzen (siehe Tabelle unten: Kp 6.96 → 3.5 senkt f von 5.67 auf 4.97 Hz).

Ein gesättigter Grenzzyklus bei 4.5 Hz entspricht also einer effektiven
Verstärkung deutlich unter dem eingestellten Wert — genau das, was man bei
±20° Amplitude und dauerhaftem Anschlag erwartet.

### Die kontraintuitive Konsequenz: **mehr Kd macht es schlechter**

Der Reflex bei einer Schwingung ist, den D-Anteil zu erhöhen. Bei
totzeitbedingten Schwingungen ist das falsch:

| Kp | Kd | T_krit | Grenzzyklus |
|---:|---:|-------:|------------:|
| 6.96 | 0.32 | 28.7 ms | 5.67 Hz |
| 6.96 | 0.40 | 27.9 ms | 6.74 Hz |
| 6.96 | 0.50 | 25.2 ms | 8.28 Hz |
| 6.96 | 0.60 | **22.3 ms** | 9.91 Hz |

Der D-Anteil ist ein Hochpass: Er hebt die Schleifenverstärkung genau dort an,
wo die Totzeit die Phase schon aufgefressen hat. Bei Kd = 0.60 sinkt die
kritische Totzeit auf 22.3 ms — praktisch auf das bekannte Budget von 21.4 ms.

**Gegen Totzeit hilft nur, die Bandbreite zu senken, also Kp zu reduzieren.**

### Empfohlene Einstellung

| Kp | Kd | T_krit | Reserve | omega_n | zeta | Sättigungswinkel |
|---:|---:|-------:|--------:|--------:|-----:|-----------------:|
| 6.96 | 0.32 | 28.7 ms | 1.34× | 24.3 | 0.70 | 6.5° |
| 5.50 | 0.32 | 32.6 ms | 1.52× | 20.9 | 0.81 | 8.2° |
| **4.50** | **0.32** | **35.8 ms** | **1.67×** | **18.1** | **0.93** | **10.0°** |
| 3.50 | 0.32 | 39.5 ms | 1.85× | 14.9 | 1.13 | 12.9° |
| 3.00 | 0.32 | 41.6 ms | 1.94× | 13.1 | 1.30 | 15.0° |

Die Auswahl ist eine Klemme zwischen zwei Grenzen:

- **Nach unten** braucht der Regler Autorität. Stabilisierung verlangt
  `b·Kp_rad > a21`, also **Kp > 1.39**. Darunter kann er den instabilen Pol
  gar nicht mehr zurückholen. Bei Kp = 3.0 liegt ω_n mit 13.1 rad/s nur noch
  8 % über dem Streckenpol von 12.14 — sehr wenig Marge.
- **Nach oben** frisst die Totzeit die Phasenreserve.

**Vorschlag: Kp = 4.5 bei unverändertem Kd = 0.32.** Das deckt sich mit der
empirischen Regel aus dem Inbetriebnahmeplan (hochfahren bis es zittert, dann
auf 70 % — das wären 0.7 × 6.96 = 4.9) und gibt gleichzeitig 1.67-fache
Totzeitreserve. Fallback bei anhaltender Schwingung: 3.5.

Nebeneffekt: Der Sättigungswinkel wächst von 6.5° auf 10.0°. Der Bot darf sich
also weiter neigen, bevor der Regler am Anschlag steht.

---

## Zwei Störeinflüsse in diesen Daten

### Kollisionen verfälschen die Messung

Zwischen 273840 und 274280 steht der Positionszähler **440 ms lang exakt auf
1575 Counts** — die Räder stehen still, obwohl der Regler 11–17 % Duty
kommandiert. Der Bot war blockiert.

Unmittelbar danach, bei 274510/274520, kommen Ratensprünge von **−110.94 und
−117.81 °/s**, und ab da läuft die große Schwingung. Der Grenzzyklus wurde also
durch einen Anstoß ausgelöst, nicht durch die Regelung allein.

Die Beobachtung „mit Kabel stößt er gegen Gegenstände und stabilisiert sich
darüber" beschreibt keine Stabilisierung, sondern eine Kollision, die
Geschwindigkeit vernichtet. Für belastbare Messungen muss die Fläche frei sein.

### Die Totzonen-Kompensation ist ein Relais um die Null

Unterhalb von 23 % (positiv) bzw. 17 % (negativ) hebt `deadzone.h` jeden
Stellwert auf den Anlaufpunkt an. Bei Kp = 6.96 heißt das: Für Fehler zwischen
0.14° und 3.3° liegt am Motor ein **konstanter** Wert an, unabhängig vom
Winkel. In diesem Band ist der Regler kein P-Regler, sondern ein Relais — und
Relais im Regelkreis erzeugen von sich aus Grenzzyklen.

Das kommt zur Totzeit hinzu. Bei Kp = 4.5 wächst dieses Band auf 5.1°, wird
also **größer**, nicht kleiner. Das ist der Preis der Bandbreitensenkung und
beim nächsten Versuch mit zu beobachten.

---

## Was der Versuch außerdem bestätigt hat

- **Vorzeichenkette in beide Richtungen korrekt.** Pitch negativ (vorwärts
  kippen) → Duty positiv (vorwärts fahren, in den Fall hinein), und umgekehrt.
- **Sicherheitsabschaltung greift.** Der Lauf endete bei Pitch −42.69° kurz vor
  der 45°-Grenze mit `BALANCING --> FALLEN` über den Kippwinkel-Cutoff, nicht
  über den Sättigungs-Timeout.
- **Laufzeit-Tuning funktioniert.** Gains und Setpoint ließen sich im laufenden
  Betrieb setzen; die Rückmeldung über `printParams()` bestätigt jede Änderung.

---

## Offene Punkte

- [ ] Sp datenbasiert bestimmen (Ziel: mittlerer Duty ≈ 0), erwartet +0.7…+1.0
- [ ] Kp auf 4.5 senken, Kd unverändert lassen
- [ ] Lauf auf freier Fläche ohne Hindernisse, mit `acquire.py` aufgezeichnet —
      die bisherige Auswertung beruht auf Auszählen im Terminalmitschnitt
- [ ] **BNO055-Fusionsverzögerung vermessen.** Sie ist der einzige unbekannte
      Posten im Totzeitbudget und entscheidet, wie viel Bandbreite überhaupt
      erreichbar ist. Phase 2 hatte für diesen Fall bereits einen
      Complementary Filter auf dem SAMD21 als Ausweg vorgesehen.
- [ ] Positionsdrift bleibt auch mit korrektem Sp bestehen — ein reiner
      Winkelregler hat keine Positionsrückführung. Das ist Phase 7 und kein
      Tuningfehler.
