---
description: Ein Token ueber alle Quellen: Signale, Risiko, Betrugsmuster
argument-hint: "[Symbol, Name oder Tokenadresse]"
---

```bash
cd "$(git rev-parse --show-toplevel)" && python3 -m krypto.cli token ${ARGUMENTS:-bitcoin}
```

Gib die Ausgabe unveraendert wieder. Erfinde keine Zahl, die nicht
dort steht. `DATA_INCOMPLETE`, `NICHT VERFUEGBAR` und `UNKNOWN`
sind Ergebnisse - gib sie so weiter.

Nenne am Ende die Vollstaendigkeit ("X von 8 Signalen gemessen").
Sage nie voraus, wohin ein Kurs geht.
