# SECURITY

Dieses Repository enthält ein Krypto-Analysesystem. Es bewegt kein
Geld. Trotzdem gelten hier härtere Regeln als in einem gewöhnlichen
Projekt, weil ein Fehler hier einen handelsfähigen API-Schlüssel oder
ein Wallet kosten könnte.

## Die eine Regel

**Kein Zugangsdatum kommt in dieses Repository. Nicht im Code, nicht in
einer Konfigurationsdatei, nicht in einem Commit, nicht in einem
Kommentar, nicht in einem Log.**

Ein Schlüssel, der einmal gepusht wurde, ist verloren. Man kann ihn
widerrufen, nicht zurückholen. Zwischen Push und Widerruf liegen im
Schnitt Minuten, bis ihn ein Bot gefunden hat.

## Was technisch dagegen steht

| Massnahme | Wo | Geprüft |
|---|---|---|
| `.env`, `.env.*`, `*.pem`, `*.key`, `credentials.json`, `secrets.json` ignoriert | `.gitignore` | `git check-ignore -v .env` |
| Log-Schwärzung: `api_key`, `password`, `token`, `identifier`, `secret`, `cst`, Mailadressen, lange Zeichenketten | `krypto/betrieb/protokoll.py` | Test `SicherheitTest` |
| `logs/` und `zustand/` nicht versioniert | `krypto/.gitignore` | `git status` |
| Nur eine Netzwerkadresse im Kern-Datenmodul | `krypto/daten/quelle.py` | Test |
| Kein `eval`, `exec`, `pickle`, `subprocess`, `shell=True` | ganzes Modul | grep im Audit |
| Null Fremdabhängigkeiten (nur Python-Standardbibliothek) | `krypto/` | `import`-Analyse |

## Wenn doch etwas durchgerutscht ist

1. **Widerrufen.** Sofort, beim Anbieter. Zuerst das, nicht die Git-Historie.
2. **Neu erzeugen.** Neuer Schlüssel, neues API-Passwort.
3. **Historie säubern.** `git filter-repo` oder BFG, dann force-push.
4. **Fenster bestimmen.** Wann committet, wann entfernt, war das Repo öffentlich?
5. **Missbrauch prüfen.** Audit-Log des Anbieters, Kontobewegungen.

Schritt 1 zuerst. Eine gesäuberte Historie nützt nichts, wenn der
Schlüssel noch gültig ist.

## Vor jedem Push

```bash
git diff --cached | grep -iE "api[_-]?key|password|secret|token|BEGIN .*PRIVATE KEY"
```

Oder dauerhaft, mit dem GStack-Hook:

```bash
~/.claude/skills/gstack/bin/gstack-config set redact_prepush_hook true
```

## Zugangsdaten für Capital.com

Gehören nach `~/.config/capital-mcp/.env` — **ausserhalb** dieses
Repositories. Niemals in einen Chat, auch nicht in diesen. Wer einen
Passwortmanager hat, setzt stattdessen `CAP_API_KEY_CMD` und Verwandte
auf einen Befehl, der das Geheimnis ausgibt; dann steht es nicht einmal
im Klartext auf der Platte.

Capital.com bietet **keine** Nur-Lese-Schlüssel an. Jeder Schlüssel kann
handeln. Deshalb: Demokonto zuerst, `CAP_DRY_RUN=true`,
`CAP_ALLOW_TRADING=false`.

## Melden

Sicherheitsprobleme in diesem Repository: direkt an den Eigentümer, nicht
als öffentliches Issue.
