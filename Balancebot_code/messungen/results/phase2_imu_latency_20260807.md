# Phase 2 — BNO055 Latenz & Modus-Entscheidung (2026-08-07)

**Sketch:** `imu_latency` (500 Reads pro Modus, `getEvent(EULER)` mit micros()-Messung) · **Bot:** ruhend, Pitch roh 39.563°

## Messwerte (duration_us eines `getEvent()`-Aufrufs)

| Modus | min [µs] | max [µs] | Verteilung |
|-------|---------:|---------:|------------|
| NDOF (Default, 9-DOF-Fusion) | 948 | 2155 | bimodal: ~950 µs und ~1900 µs, Mittel ≈ 1.4 ms |
| IMUPLUS (0x08, 6-DOF ohne Magnetometer) | 941 | 2027 | bimodal: ~942 µs und ~1890 µs, Mittel ≈ 1.4 ms |

*Werte aus Serial-Mitschnitt abgelesen (kein acquire.py-Rohfile); die bimodale
Verteilung entspricht dem BNO055-I2C-Zugriffsmuster (Clock-Stretching).*

## Entscheidung nach Regel aus dem Commissioning-Plan

Regel: Latenz < 5 ms **und** Kalibrierung stabil → NDOF OK; sonst IMU-Modus.

- Latenz: **beide Modi klar unter 5 ms** → kein Ausschlusskriterium.
- Kalibrierung: In Phase 0 zeigte NDOF beim Boot `sys=0, mag=0` (Magnetometer
  unkalibriert). Das Magnetometer sitzt zentimeternah an zwei DC-Motoren, deren
  Spulenströme beim Balancieren ständig wechseln — im NDOF-Modus fließt das
  gestörte Magnetfeld in die Fusion ein und kann Orientierungssprünge verursachen.
- Für die Balance wird nur Pitch (schwerkraftreferenziert) gebraucht; das
  Magnetometer liefert dafür keinerlei Nutzen, nur Risiko.

**→ Entscheidung: IMUPLUS (0x08).** Umgesetzt in `imu.cpp::begin()`
(`setMode(OPERATION_MODE_IMUPLUS)` + 100 ms Wartezeit nach Moduswechsel).

## Einschränkung dieser Messung

`changed=0` in allen 1000 Zeilen: Der Bot stand während des Tests still, der
Pitch blieb LSB-stabil (Auflösung 0.0625°) — die **effektive Datenrate (ODR)
konnte so nicht gemessen werden**. Falls relevant, Test mit leicht bewegtem Bot
wiederholen; ansonsten wird die reale Datenrate beim Phase-C-Logging sichtbar
(process.py erkennt Wiederholwerte).
