# Karosserie-Neugestaltung — Anforderungen

Stand 2026-08-09. Gesammelte Anforderungen für die nächste Rahmenversion,
abgeleitet aus Messungen und dem Regelungsmodell (`dokumentation/auslegung/system_model.md`).

---

## Ausgangslage

Die CAD-Baugruppe (`BalanceBotAssembly.FCStd`, Analyse 2026-04-12) ist **nicht**
identisch mit dem physisch aufgebauten Bot. Bekannte Abweichungen:

| Größe | CAD | physisch | Quelle |
|-------|-----|----------|--------|
| Gesamtmasse (mit Rädern) | 155.6 g | **190 g** | gewogen 2026-08-09 |
| Räder, beide zusammen | 67.3 g | **44 g** | gewogen 2026-08-09 |
| Körpermasse ohne Räder | 88.3 g | **146 g** | Differenz |
| Oberkante Nano über Achse | ~29 mm | **42 mm** | gemessen 2026-08-09 |

Der Körper ist also um zwei Drittel schwerer als im CAD und die Räder um ein
Drittel leichter. Ein Nachpflegen der alten Baugruppe lohnt nicht, weil die
neue Karosserie ohnehin eine andere Massenverteilung bekommt. Die Zahlen stehen
hier nur, damit klar ist: **CAD-Werte der alten Baugruppe taugen nicht als
Messwerte.** Das gilt ausdrücklich auch für den CoG-Prior von 8.6 mm — der ist
aus derselben Baugruppe abgeleitet und wartet auf die Messung aus Phase 4.

---

## A1 — Schwerpunkt höher legen — **ZURÜCKGESTELLT nach Messung 2026-08-09**

**Diese Anforderung stand auf einer falschen Prämisse.** Der Schwingversuch
(`Balancebot_code/messungen/results/phase4_swing_20260809.md`, Entscheidung in
[ADR-0008](../dokumentation/entscheidungen/0008-measured-pole-over-estimated-inertia.md)) hat den
instabilen Pol direkt gemessen: **p = 12.1 1/s statt der modellierten 30.1**.
Die Verdopplungszeit beträgt 57 ms, nicht 23 ms — die Regelung hat 5.7
Abtastschritte pro Verdopplung, nicht 2.3. Die Zeitnot, die A1 begründet hat,
existiert nicht.

### Warum Ballast in geringer Höhe sogar schadet

Der ursprüngliche Gedankengang war: Schwerpunkt höher legen heißt längeres
Pendel heißt mehr Reaktionszeit. Das gilt für ein *Fadenpendel*, bei dem die
gesamte Masse am Ende sitzt. Ein Bot ist kein Fadenpendel.

Fügt man dem Körper eine Zusatzmasse m_a in der Höhe h über der Achse hinzu,
ändern sich Zähler und Nenner des Pols unterschiedlich schnell:

```
p^2 = (m*g*L + m_a*g*h) / (J + m_a*h^2)
```

| Symbol | Beschreibung | Einheit |
|--------|-------------|---------|
| p | instabiler Pol des aufrechten Bots | 1/s |
| m | bisherige Körpermasse ohne Räder, 0.146 | kg |
| L | bisherige CoG-Höhe über der Achse | m |
| J | bisheriges Trägheitsmoment um die Achse, gemessen 875 g·cm² | kg·m² |
| m_a | zugefügte Ballastmasse | kg |
| h | Höhe des Ballasts über der Achse | m |

Das rückstellende Schweremoment im Zähler wächst **linear** mit h, das
Trägheitsmoment im Nenner **quadratisch**. Für kleines h dominiert der Nenner
den Zähler noch nicht — solange `m_a·h² ≪ J`, bringt der Ballast fast keine
zusätzliche Trägheit, aber auch kaum Hebel. Genau dazwischen liegt ein Bereich,
in dem er netto **schadet**.

Der Umschlagpunkt liegt dort, wo der Ballast das vorhandene J zu dominieren
beginnt, also bei `h ≈ √(J/m_a)`. Mit den gemessenen J = 875 g·cm² = 87500 g·mm²
und m_a = 40 g sind das rund **47 mm**. Erst deutlich darüber greift die
Fadenpendel-Intuition, und im Grenzfall `m_a·h² ≫ J` geht p² → g/h, also
t₂ ∝ √h — um t₂ zu verdoppeln, braucht es die *vierfache* Höhe.

Gerechnet auf der gemessenen Basis (m = 146 g, L = 9 mm, J = 875 g·cm²):

| Ballast | Höhe über Achse | L_neu | t₂ | Gewinn |
|--------:|----------------:|------:|-----:|-------:|
| 40 g | 50 mm | 17.8 mm | 53 ms | **0.92×** (schlechter) |
| 40 g | 100 mm | 28.6 mm | 67 ms | 1.16× |
| 40 g | 150 mm | 39.3 mm | 81 ms | 1.41× |
| 60 g | 150 mm | 50.1 mm | 83 ms | 1.43× |

Die frühere Empfehlung „L auf 30 mm, also 40 g auf 10 cm" hätte demnach
16 % mehr Reaktionszeit gebracht — für einen kompletten Karosserieumbau.

**Reihenfolge:** Erst L per Knife-Edge messen, Gains aus dem gemessenen Pol
rechnen, Tuning-Sitzung fahren. Diese Anforderung nur wieder aufgreifen, wenn
sich dabei die Reaktionszeit nachweislich als limitierend erweist — und dann
mit Zielhöhe ≥ 150 mm statt 30 mm, weil darunter der Aufwand den Effekt nicht
rechtfertigt.

Die ursprüngliche Herleitung bleibt zur Nachvollziehbarkeit stehen. Sie beruht
durchgehend auf `J = 1.2·m·L²`, was am Bot als Faktor 6 zu klein nachgewiesen
wurde. Alle t₂- und θ_max-Werte darin sind entsprechend falsch.

<details>
<summary>Ursprüngliche Fassung (überholt, Punktmasse-Annahme)</summary>

**Zielwert: L = 25–35 mm, Auslegungspunkt 30 mm.**

| Symbol | Beschreibung | Einheit |
|--------|-------------|---------|
| L | Höhe des Körper-Schwerpunkts über der Radachse | mm |
| p | instabiler Pol des aufrechten Bots, √(m·g·L/J) | 1/s |
| t₂ | Verdopplungszeit des Kippfehlers, ln2/p | ms |
| θ_max | statisch haltbarer Kippwinkel bei 45 % Duty | ° |

Aktuell liegt L bei etwa 9 mm (CAD-Prior 8.6 mm, empirische Gegenprobe aus der
beobachteten Grenzzyklusfrequenz 9.1–9.7 mm). Daraus folgt t₂ ≈ 23 ms — bei
10 ms Regeltakt bleiben der Regelung **2.3 Abtastschritte pro Verdopplung des
Kippfehlers**, und davon geht laut Phase-1-Messung fast ein ganzer Schritt für
die I2C-Kommunikation drauf (6.4 ms mean, 8.3 ms worst case). Das ist kein
Tuningproblem, sondern ein zu schnelles System für diese Hardware.

| L [mm] | t₂ [ms] | Takte pro t₂ | θ_max [°] |
|-------:|--------:|-------------:|----------:|
| 9 (aktuell) | 23 | 2.3 | 27.3 |
| 20 | 34 | 3.4 | 12.3 |
| 25 | 38 | 3.8 | 9.8 |
| **30** | **42** | **4.2** | **8.2** |
| 35 | 45 | 4.5 | 7.0 |
| 40 | 48 | 4.8 | 6.1 |
| 60 | 59 | 5.9 | 4.1 |

Das Fenster 25–35 mm ergibt sich aus zwei gegenläufigen Effekten: Nach oben
begrenzt der drehmomentbegrenzte Kippwinkel θ_max ∝ 1/L, der bei etwa **41 mm**
unter das ±6°-Auto-Arm-Fenster fällt. Nach unten begrenzt die Reaktionszeit.
Dazwischen ist der Gewinn am größten — von 9 auf 30 mm verdoppelt sich t₂
nahezu, während θ_max mit 8.2° noch komfortabel über dem Arbeitsbereich liegt.
Oberhalb von 35 mm wächst t₂ nur noch schwach (ω₀ geht mit 1/√L), kostet aber
weiter Winkelreserve — und ab 41 mm reicht das Drehmoment nicht mehr, um den
Bot aus dem Auto-Arm-Fenster heraus zu fangen.

**Konstruktive Hebel** — nötige Ballasthöhe über der Achse, um L von 9 mm auf
den Zielwert zu heben:

| Ziel L | mit 20 g | mit 40 g | mit 60 g |
|-------:|---------:|---------:|---------:|
| 25 mm | 142 mm | 83 mm | 64 mm |
| 30 mm | 183 mm | **107 mm** | **81 mm** |
| 40 mm | 266 mm | 153 mm | 115 mm |

Der Akku allein (22 g) reicht nicht — er müsste auf 18 cm, das wird ein
wackliger Mast. Realistischer ist, Motor Carrier und Nano (zusammen ~24 g)
mit nach oben zu nehmen und gezielt Ballast zu ergänzen, oder gleich mit
rund 40 g auf 11 cm zu planen.

*Die Tabelle geht von L = 9 mm als Ausgangswert aus (CAD-Prior). Sobald die
Messung aus Phase 4 vorliegt, mit dem echten Startwert neu rechnen.*

</details>

**Nebenwirkung beachten:** Zusätzliche Masse erhöht J und damit den
Drehmomentbedarf. Jeden Entwurfskandidaten vorher durch
`python3 Balancebot_code/python/system_id.py --L-mm <Wert>` schicken.

---

## A2 — Definierter Endanschlag für den Akku

**Der Akku muss in y-Richtung formschlüssig arretiert sein.**

Aktuell wird der 18650 eingeschoben, ohne dass ein Anschlag seine Endlage in
Fahrtrichtung definiert. Die y-Position ist damit nicht reproduzierbar — und
genau diese Position bestimmt den Gleichgewichts-Setpoint.

Rechnung: Der Akku wiegt 22 g von 146 g Körpermasse, also 15 %. Verschiebt er
sich um Δy, wandert der Körperschwerpunkt um 0.15·Δy mit. Der nötige
Setpoint-Trim ist Sp = atan(y/L):

| Akku-Verschiebung Δy | CoG-Versatz | ΔSp bei L = 9 mm | ΔSp bei L = 30 mm |
|---------------------:|------------:|-----------------:|------------------:|
| 2 mm | 0.30 mm | 1.9° | 0.6° |
| 5 mm | 0.76 mm | 4.8° | 1.4° |
| 10 mm | 1.52 mm | 9.6° | 2.9° |

| Symbol | Beschreibung | Einheit |
|--------|-------------|---------|
| Δy | Verschiebung des Akkus in Fahrtrichtung | mm |
| Sp | Winkel-Setpoint (Gleichgewichts-Trim) | ° |
| L | CoG-Höhe über der Achse | mm |

Fünf Millimeter Spiel im Akkuschacht sind also bis zu 4.8° Setpoint-Drift.
Zum Vergleich: Das Auto-Arm-Fenster ist ±6° breit, und `TUNE_SP_MAX_DEG`
begrenzt den Trim auf ±15°. Ein Akku, der sich beim Transport verschiebt,
kann den Bot damit allein durch Umlagern unbalancierbar machen — und beim
Debugging sieht das exakt aus wie ein Reglerfehler.

**Diese Anforderung wird durch die Zurückstellung von A1 wichtiger, nicht
unwichtiger.** Ein höherer CoG hätte die Empfindlichkeit um etwa Faktor 3
gedämpft. Da der Bot vorerst bei L ≈ 9 mm bleibt, gilt weiter die linke
Spalte der Tabelle: 5 mm Schachtspiel sind knapp 5° Trimmdrift.

**Anforderung:** Fester Anschlag am Schachtende plus Klemmung oder Federzunge
gegen die Einschubrichtung, sodass die Endlage ohne Zutun des Monteurs
eindeutig ist.

---

## A3 — Referenzflächen fürs Vermessen

Aus der Knife-Edge-Messung 2026-08-09: Die Achslage ließ sich nur über die
Motorwellen abgreifen, und für die Winkelmessung fehlte eine definierte
Bezugsfläche.

Vorschlag: eine plane, zur Radachse parallele Fläche am Rahmen, die als
Auflage beim Kantentest und als Bezug für die Ruhelagenmessung dient. Kostet
nichts und macht jede spätere Vermessung reproduzierbar.

---

## Offene Punkte

- [x] Räder wiegen (2026-08-09: 44 g beide, CAD lag mit 67.3 g deutlich daneben)
- [ ] Zielwert L nach dem Schwingversuch (Phase 4, Messung 3) gegenprüfen —
      der misst den instabilen Pol direkt und ersetzt die J-Schätzung im Modell
- [ ] Entscheiden, ob Ballast oder Umbau der Elektronikebene
