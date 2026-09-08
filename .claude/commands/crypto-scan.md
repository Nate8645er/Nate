---
description: Marktscan mit Volumen- und Marktkapitalfilter
argument-hint: "[Anzahl Werte, Vorgabe 50]"
---

```bash
cd "$(git rev-parse --show-toplevel)" && python3 -m krypto.cli scan --anzahl ${ARGUMENTS:-50} --ausfuehrlich
```

Fuehre den Befehl aus und gib die Ausgabe unveraendert wieder.
Erfinde keine Zahl, die nicht in der Ausgabe steht. Steht dort
"NICHT VERFUEGBAR", "NICHT BERECHENBAR" oder "NOT VERIFIED", dann
gib genau das weiter - ohne Schaetzung, ohne Ersatzwert.

Dieses System stellt keine echten Orders. Live-Handel ist gesperrt.
