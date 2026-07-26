---
name: dev-toolbelt
description: >-
  Was in dieser Umgebung an Werkzeugen WIRKLICH verfuegbar ist — geprueft, nicht
  vermutet: CLI-Werkzeuge, Laufzeiten, Datenbanken, Browser, Medien-Werkzeuge.
  Und was NICHT geht (und warum). AKTIVIEREN bevor ein Werkzeug eingesetzt oder
  ein Repo "installiert" werden soll, oder auf Trigger: "/toolbelt", "welche
  Werkzeuge habe ich", "ist X installiert", "kann ich X nutzen",
  "installiere dieses Repo".
---

# Werkzeugkasten — was hier wirklich laeuft

Alle Angaben durch Ausfuehren geprueft, nicht aus der Dokumentation abgeschrieben.

## Verfuegbar

| Werkzeug | Version | Wofuer |
|---|---|---|
| `rg` (ripgrep) | 14.1.0 | schnelle Codesuche (das Grep-Tool nutzt es intern) |
| `fd` | 9.0.0 | schnelle Dateisuche (Binary heisst `fdfind`, Symlink `fd` gesetzt) |
| `bat` | 0.24.0 | Datei-Anzeige mit Syntax-Hervorhebung (Binary `batcat`) |
| `uv` | vorhanden | schneller Python-Paketmanager |
| `ruff` | vorhanden | Python-Linter/Formatter |
| `pre-commit` | 4.6.1 | Git-Hooks |
| `pip-audit` | 2.10.1 | Python-CVE-Scan |
| `detect-secrets` | 1.5.0 | Secret-Scan (Ersatz fuer gitleaks) |
| `tmux` | vorhanden | Terminal-Multiplexer |
| `node` / `npm` | 22.22.2 / 10.9.7 | JS-Laufzeit, `npm audit` fuer JS-CVEs |
| `python3` | 3.11 (Umgebung), 3.12 in CI | Hauptsprache des Projekts |
| PostgreSQL | 16.13 | via `/usr/lib/postgresql/16/bin`, lokaler Testcluster moeglich |
| `redis-server` | 7.0.15 | vorinstalliert, aber standardmaessig nicht gestartet — lokal fuer Rate-Limiting (`platform-backend/app/ratelimit.py`, `REDIS_URL`) startbar, `tests/test_ratelimit_redis.py` startet/stoppt es selbst |
| `ffmpeg` | 6.1.1 | Video/Audio (Remotion-Rendering, Untertitel) |
| Chromium | vorinstalliert | `/opt/pw-browsers/chromium` (Playwright) |
| Piper TTS | 1.6.0 | deutsches lokales Voiceover |

## Nicht verfuegbar — und warum

| Was | Grund |
|---|---|
| Docker-Daemon | laeuft in dieser Umgebung nicht (`/var/run/docker.sock` fehlt). Postgres stattdessen als lokaler Cluster starten. |
| `gitleaks`, `trivy`, `syft`, `grype`, `trufflehog` | Binaries liegen als GitHub-Release-Assets, die der Proxy blockiert (Download liefert 9 Byte Text statt Archiv). Ersatz: `detect-secrets` + `pip-audit` + `npm audit`. |
| `uvicorn` als CLI | nicht im PATH — Anwendung stattdessen in-process via `fastapi.testclient.TestClient` testen. |
| Remotions Standard-Chromium | Remotion braucht eine eigene Headless-Shell: `npx remotion browser ensure` (laedt selbst, funktioniert). |

## Ein Repo ist kein Plugin

Haeufiges Missverstaendnis: Ein GitHub-Repo laesst sich **nicht** „als Skill
installieren". Ein Claude-Plugin braucht eine `.claude-plugin/plugin.json` mit
`skills/`, `agents/` oder `commands/`. Repos wie `ripgrep`, `cpython`,
`flutter`, `elasticsearch` oder `vscode` haben das nicht — das sind Programme,
Sprachen und Bibliotheken.

Was mit so einem Repo wirklich geht, haengt vom Typ ab:

| Typ | Beispiele | Weg |
|---|---|---|
| CLI-Werkzeug | ripgrep, fd, bat, ruff, uv | als Binary/Paket installieren, dann normal aufrufen |
| Python-Bibliothek | transformers, dspy, haystack, smolagents | `pip install`, dann importieren |
| MCP-Server | supabase-mcp, mcp-sdks | als MCP-Server konfigurieren |
| Anwendung/Dienst | Sentry, Airflow, Medusa, Strapi, Elasticsearch | deployen (eigener Server), per API anbinden |
| Referenz-Codebasis | LibreChat, dify, langgraph, OpenHands | Muster lesen und uebernehmen, nicht installieren |

**Der praktische Weg:** Erst klaeren, was das Repo eigentlich ist, dann den
passenden Weg waehlen. Ein Skill entsteht daraus nur, wenn man **Wissen ueber
die Nutzung** aufschreibt — so wie diese Datei.

## Nichts ueberlebt ohne Git

Diese Umgebung ist **fluechtig**: Der Container wird beim Sitzungsstart frisch
aus dem Git-Repo geklont und spaeter wieder geloescht. Alles, was installiert,
entpackt oder gebaut und **nicht committet** wird, ist beim naechsten Mal weg.

Deshalb: Was bleiben soll, gehoert ins Repo und muss gepusht werden. Genau
darum liegt dieses Plugin unter `nate-toolkit/` im Repository und nicht nur
in der Sitzung.
