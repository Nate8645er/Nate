---
description: TRADE/NO-TRADE-Signale ueber die Beobachtungsliste
argument-hint: "[Anzahl Werte, Vorgabe 8]"
---

```bash
cd "$(git rev-parse --show-toplevel)" && python3 -m krypto.cli signals --top ${ARGUMENTS:-8}
```

Fuehre den Befehl aus und gib die Ausgabe unveraendert wieder.
Erfinde keine Zahl, die nicht in der Ausgabe steht. Steht dort
"NICHT VERFUEGBAR", "NICHT BERECHENBAR" oder "NOT VERIFIED", dann
gib genau das weiter - ohne Schaetzung, ohne Ersatzwert.

Dieses System stellt keine echten Orders. Live-Handel ist gesperrt.
