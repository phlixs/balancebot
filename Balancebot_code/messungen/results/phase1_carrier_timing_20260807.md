# Phase 1 — Motor Carrier I2C-Timing (2026-08-07)

**Sketch:** `carrier_timing` (1000 Iterationen pro Aufruf) · **Carrier-FW:** 0.20 · **BNO055-Modus:** NDOF (Default)

## Messwerte

| Aufruf | min [µs] | max [µs] | mean [µs] |
|--------|---------:|---------:|----------:|
| `controller.ping()` | 667 | 676 | 668.6 |
| `encoder1.getRawCount()` | 877 | 892 | 884.3 |
| `encoder2.getRawCount()` | 877 | 892 | 884.3 |
| `M1.setDuty(0)` | 667 | 675 | 668.7 |
| `M2.setDuty(0)` | 667 | 676 | 668.8 |
| `bno.getEvent(EULER)` | 948 | 2222 | 1314.4 |
| `bno.getEvent(GYRO)` | 957 | 2259 | 1339.4 |
| **Summe** | **5960** | **8292** | **6428.5** |

## Bewertung

- **Erfolgskriterium erfüllt:** Summe der Mittelwerte 6428.5 µs < 8000 µs (80 % des 10-ms-Budgets bei 100 Hz, ADR-0006). ✓
- Ein voller Regelzyklus (2× IMU-Read, 2× Encoder, 2× setDuty, 1× ping) verbraucht im Mittel **~6.4 ms von 10 ms** allein für I2C-Kommunikation — es bleiben ~3.6 ms für Regler-Rechnung, Logging und Reserve.
- **Achtung, wenig Worst-Case-Reserve:** Die IMU-Reads streuen stark (max 2.2 ms statt 1.3 ms). Im Worst Case aller Aufrufe zusammen: 8292 µs → nur ~1.7 ms Luft. Konsequenzen:
  1. Kein blockierender Code in der Regelschleife (Serial-Prints nur gepuffert, WiFi später non-blocking).
  2. Phase 2 prüft, ob der IMU-Modus (0x08, ohne Magnetometer-Fusion) die IMU-Latenz und ihre Ausreißer reduziert.
  3. `LOOP_PERIOD_MS` unter 10 ms ist definitiv nicht machbar — bestätigt die bestehende Untergrenze.
- Carrier-Aufrufe (ping, setDuty) sind mit ~670 µs sehr konstant (Jitter < 10 µs); die Encoder-Reads ebenso. Die Varianz kommt praktisch nur vom BNO055.
