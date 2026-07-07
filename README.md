# J.A.R.V.I.S. AI OS

Ein lokaler, sprachgesteuerter KI-Assistent, der wie ein persönliches
Betriebssystem funktioniert: modulare Agenten, Skills, Plugins, Gedächtnis,
Automatisierung und ein Iron-Man-inspiriertes HUD-Dashboard.

![CI](../../actions/workflows/ci.yml/badge.svg)

## Schnellstart

```bash
# 1. Installieren (Python 3.11+)
pip install -e .

# 2. Konfigurieren (optional — läuft auch ohne Keys im Echo-Modus)
cp .env.example .env   # API-Keys / Ollama eintragen

# 3. Starten
jarvis                 # oder: python -m jarvis
```

Dashboard: **http://127.0.0.1:8765** · API-Docs: **http://127.0.0.1:8765/docs**

### Docker

```bash
docker compose up jarvis                 # nur JARVIS
docker compose --profile full up         # + Postgres, Redis, Qdrant, Ollama
```

## Was kann JARVIS?

| Bereich | Funktion |
|---|---|
| **Sprache** | Wake Word („Jarvis …"), Speech-to-Text, Text-to-Speech — lokal (openwakeword/faster-whisper/piper via `pip install -e ".[voice]"`) oder ohne Zusatzinstallation direkt im Browser (Web Speech API) |
| **Agenten** | 19 vorkonfigurierte Spezialisten (CEO, Coding, Research, DevOps, QA, Security, Finance, Marketing, …) — beliebig erweiterbar, alle arbeiten parallel |
| **Virtuelle Firma** | Org-Chart in `jarvis/company/org.yaml`; „Mitarbeiter" jederzeit per API/Dashboard einstellen oder entlassen, ohne Obergrenze |
| **Skills** | Dateien, Shell, Git, Browser, Websuche, Kalender/Erinnerungen, E-Mail-Entwürfe, Dokumente, PDF, OCR, Medien, Gedächtnis, Workflows … |
| **Plugins** | Ordner in `plugins/` ablegen → automatisch erkannt; aktivieren/deaktivieren, versionieren, neu laden — zur Laufzeit |
| **Gedächtnis** | Kurzzeitfenster, SQLite-Langzeitgedächtnis, Vektor-Suche (ChromaDB/Qdrant, Fallback eingebaut), Gesprächs- und Projektwissen |
| **Automatisierung** | Workflow-Engine (YAML/JSON, Editor im Dashboard), Scheduler für Erinnerungen & wiederkehrende Jobs |
| **PC-Steuerung** | Programme starten, Dateien organisieren, Shell, Docker, lokale Server — **jede riskante Aktion erfordert deine Freigabe** (Modal im Dashboard + Sprachansage) |

## Sicherheit: Freigabe-System

Jeder Skill deklariert ein Risiko-Level:

| Level | Bedeutung | Beispiele |
|---|---|---|
| 0 LESEN | nur lesen | `list_files`, `web_search` |
| 1 SCHREIBEN | erstellt/ändert Daten | `write_file`, `create_reminder` |
| 2 SYSTEM | steuert den Rechner | `run_command`, `launch_app` |
| 3 KRITISCH | destruktiv/nach außen | `delete_path` |

Ab `JARVIS_APPROVAL_THRESHOLD` (Default: 1) blockiert die Aktion, bis du sie
im Dashboard erlaubst — einmalig oder für die Sitzung.

## Sprachsteuerung

1. **Browser (sofort):** Mikrofon-Button = Push-to-talk. Schalter
   „Wake-Word-Modus" in SETUP → dauerhaft zuhören, reagiert auf „Jarvis …".
   Antworten werden per `speechSynthesis` gesprochen. (Chrome/Edge)
2. **ElevenLabs (beste Stimme):** `JARVIS_ELEVENLABS_API_KEY` und
   `JARVIS_ELEVENLABS_VOICE_ID` in `.env` setzen — JARVIS spricht dann mit
   deiner ElevenLabs-Stimme (MP3 wird ans Dashboard gestreamt).
3. **Lokal (volle Privatsphäre):** `pip install -e ".[voice]"` installiert
   openwakeword (Wake Word), faster-whisper (STT) und piper (TTS). JARVIS
   nutzt sie automatisch, sobald verfügbar.

## Eigene Agenten

```bash
curl -X POST localhost:8765/api/agents -H 'Content-Type: application/json' -d '{
  "name": "legal", "title": "Legal Agent", "department": "operations",
  "description": "Prüft Verträge und fasst Risiken zusammen.",
  "skill_categories": ["files", "memory"]
}'
```

…oder dauerhaft als Eintrag in `jarvis/company/org.yaml`, oder per
„+ EINSTELLEN" im Dashboard.

## Eigene Plugins

```
plugins/mein-plugin/
├── plugin.json    # {"id": "mein-plugin", "name": "…", "version": "1.0.0"}
└── plugin.py      # def setup(kernel): kernel.skills.register(…)
```

Referenz: `plugins/weather/` (fertiges Wetter-Plugin, ohne API-Key).

## Eigene Workflows

```yaml
# workflows/mein-workflow.yaml
name: mein-workflow
steps:
  - name: recherche
    agent: research
    goal: "Fasse die neuesten KI-Nachrichten zusammen."
  - name: ablage
    skill: write_file
    args: { path: "~/notizen.md", content: "{{steps.recherche}}" }
```

## Entwicklung

```bash
pip install -e ".[dev]"
pytest -v          # Testsuite
ruff check .       # Lint
```

Architektur-Details: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

## Ehrliche Grenzen

- Ohne LLM-Key/Ollama läuft der **Echo-Modus** (System funktioniert, Antworten sind Platzhalter).
- Server-seitige Voice braucht die `[voice]`-Extras und ein Mikrofon am Host (nicht im Docker-Container).
- `draft_email` erstellt Entwürfe, versendet aber bewusst nicht ohne konfigurierten Versandweg.
- OCR/PDF/Office benötigen die `[desktop]`-Extras.
