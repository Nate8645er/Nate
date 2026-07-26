---
description: Sicherheits-Rundumcheck — Secrets im Code/Git + CVEs in Python- und JS-Abhaengigkeiten
---
Fuehre den Sicherheits-Rundumcheck dieses Repositories aus:

```bash
python3 tools/security_scan.py --quick   # Secrets + Git (schnell)
python3 tools/security_scan.py           # zusaetzlich CVEs
```

Werte das Ergebnis aus: Jeder mit `(NEU)` markierte Fund ist noch ungeprueft.
Bei einem gefundenen echten Key: sofort beim Anbieter rotieren (er gilt als
kompromittiert, sobald er in der Git-Historie liegt), aus dem Code entfernen,
in die `.env` verschieben und `git check-ignore -v .env` pruefen.
