---
description: Papierhandel ausfuehren (kein echtes Geld)
argument-hint: "[--trocken | --zuruecksetzen]"
---

```bash
cd "$(git rev-parse --show-toplevel)" && python3 -m krypto.cli paper ${ARGUMENTS:---trocken}
```

Fuehre den Befehl aus und gib die Ausgabe unveraendert wieder.
Erfinde keine Zahl, die nicht in der Ausgabe steht. Steht dort
"NICHT VERFUEGBAR", "NICHT BERECHENBAR" oder "NOT VERIFIED", dann
gib genau das weiter - ohne Schaetzung, ohne Ersatzwert.

Dieses System stellt keine echten Orders. Live-Handel ist gesperrt.
