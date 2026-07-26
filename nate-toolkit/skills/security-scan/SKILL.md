---
name: security-scan
description: >-
  Sicherheits-Rundumcheck fuer dieses Repository: sucht Secrets/API-Keys im
  Code und in der Git-Historie und prueft Python- und JS-Abhaengigkeiten auf
  bekannte Schwachstellen (CVEs). AKTIVIEREN vor jedem Commit mit neuen
  Abhaengigkeiten, vor jedem Deploy, nach dem Hinzufuegen von API-Keys, oder
  auf Trigger: "/security-scan", "Sicherheitscheck", "sind Keys im Code",
  "pruefe die Abhaengigkeiten", "gibt es Schwachstellen".
---

# Sicherheits-Rundumcheck

Ein Befehl, vier Pruefungen — alle mit Werkzeugen, die in dieser Umgebung
wirklich laufen (verifiziert, keine Wunschliste).

## Ausfuehren

```bash
python3 tools/security_scan.py --quick   # Secrets + Git (schnell, ~20s)
python3 tools/security_scan.py           # zusaetzlich CVEs (langsamer)
```

Exit-Code 0 = sauber, 1 = Befunde. Damit auch in CI verwendbar.

## Was geprueft wird

| Pruefung | Werkzeug | Findet |
|---|---|---|
| Getrackte Secret-Dateien | `git ls-files` | versehentlich eingecheckte `.env`, `*.pem`, `*.key` |
| Key-Muster im Git-Inhalt | `git grep` | OpenRouter-, Anthropic-, Stripe-, GitHub-, AWS-Keys im Code |
| Breite Secret-Suche | `detect-secrets` | High-Entropy-Strings, weitere Key-Formate |
| Python-CVEs | `pip-audit` | bekannte Schwachstellen in jeder `requirements.txt` |
| JS-CVEs | `npm audit` | bekannte Schwachstellen in jeder `package.json` |

## Wichtig zur Interpretation

- **`.env`-Dateien werden bewusst uebersprungen.** Sie sind gitignored und
  sollen lokal Keys enthalten — dort ist ein Fund kein Befund.
- **`npm audit` braucht `node_modules`.** Fehlt der Ordner, meldet der Scan das
  als „uebersprungen" statt faelschlich „sauber". Vorher `npm ci` laufen lassen.
- **Ein Befund ist ein Befund.** Nicht wegdiskutieren — entweder beheben
  (Abhaengigkeit heben, Key rotieren) oder begruendet dokumentieren.

## Wenn ein Key gefunden wurde

1. **Key sofort rotieren** beim jeweiligen Anbieter — er gilt als kompromittiert,
   sobald er im Git liegt (auch nach dem Loeschen bleibt er in der Historie).
2. Aus dem Code entfernen, in die `.env` verschieben.
3. Pruefen, ob `.gitignore` den Pfad wirklich abdeckt: `git check-ignore -v .env`

## Warum nicht gitleaks/trivy

Die offiziellen Binaries dieser Werkzeuge liegen als GitHub-Release-Assets,
die hinter dem Proxy dieser Umgebung nicht erreichbar sind (verifiziert:
Download liefert 9 Byte Text statt Archiv). `detect-secrets` (pip) und
`pip-audit`/`npm audit` decken denselben Bedarf ab und sind hier real
installiert. Auf einer Maschine ohne diese Einschraenkung koennen gitleaks
und trivy zusaetzlich ergaenzt werden.
