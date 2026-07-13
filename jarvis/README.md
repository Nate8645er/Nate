# JARVIS HyperScale — Multi-Agenten-System mit Live-Dashboard

Ein lokales, lauffähiges Multi-Agenten-System: **100 Milliarden adressierbare
virtuelle Mitarbeiter pro Organisationsebene** (rekursiv — jeder Mitarbeiter
führt ein eigenes virtuelles Unternehmen mit wieder 100 Mrd. adressierbaren
Mitarbeitern), ausgeführt durch einen **hardware-begrenzten Agenten-Pool**,
mit **Plugin-System**, **Langzeitgedächtnis**, **Claude-Anbindung (z. B.
Fable 5)** und einem **Live-Ticker-Dashboard**.

## Wie 100 Milliarden Mitarbeiter ehrlich funktionieren

| Ebene | Was es ist | Kosten |
|---|---|---|
| **Virtuell** | Jede Identität (Name, Team, Rolle, Skills, Ziele, eigenes Unternehmen) wird **prozedural aus ihrer Adresse berechnet** — deterministisch, jederzeit reproduzierbar | 0 Byte pro inaktivem Mitarbeiter |
| **Aktiv** | Nur so viele Agenten laufen gleichzeitig, wie CPU/RAM zulassen (automatisch ermittelt, z. B. 32 Slots) | echte CPU/RAM, bei API-Modus echtes API-Guthaben |

Adressen sind hierarchisch: `17` → Mitarbeiter 17, `17/423` → Mitarbeiter 423
im Unternehmen von Nr. 17, beliebig tief. Damit ist die Organisation
theoretisch unbegrenzt — ohne dass je etwas „gespeichert" werden muss.

**Was dieses System NICHT tut:** Geld generieren. Es gibt keine
Geld-Generier-Funktion und keinen simulierten Umsatz-Ticker — das
Business-Panel zeigt ausschließlich echte Betriebsdaten (0.00 CHF, bis eine
echte Datenquelle wie ein Buchhaltungs-Export angebunden ist). Demo-Aufgaben
sind im Ticker klar als `DEMO` markiert.

## Start (Windows)

```powershell
powershell -ExecutionPolicy Bypass -File .\jarvis\Start-Jarvis.ps1 -Demo
```

Öffnet automatisch das Dashboard: **http://127.0.0.1:8787**

Start unter Linux/macOS:

```bash
pip install -r jarvis/requirements.txt
python -m jarvis.run --demo
```

## Fable 5 / Claude aktivieren

Ohne API-Key läuft alles im klar gekennzeichneten **Offline-Modus**
(regelbasierte Antworten, kostenlos). Für echte KI-Antworten der aktiven
Agenten:

```powershell
setx ANTHROPIC_API_KEY "sk-ant-..."
setx JARVIS_MODEL "claude-fable-5"   # optional, ist der Standard
```

Danach neu starten. **Achtung:** Jeder aktive Agent-Aufruf kostet dann echtes
API-Guthaben — genau deshalb ist der aktive Pool hart begrenzt und niemals
„alle 100 Milliarden".

## Dashboard (Live-Ticker)

- Adressierbare Mitarbeiter, **aktive Agenten / Hardware-Limit**, wartende
  Aufgaben, Aktivierungen gesamt, erledigt/fehlgeschlagen, Gedächtnis-Einträge
- **CPU-/RAM-Auslastung** live
- Tabelle: welcher Mitarbeiter (Name, Rolle, Team) gerade welche Aufgabe hat
- Plugin-/Skill-/Tool-Status mit Team-Autorisierung
- Logs, Aufgaben-Eingabefeld (Aufgaben direkt an die Organisation übergeben)

## API

| Endpunkt | Zweck |
|---|---|
| `GET /api/state` | kompletter Live-Zustand |
| `GET /api/employee/17/423` | Identität jedes beliebigen Mitarbeiters |
| `GET /api/org/17/423?count=10` | Auszug aus dessen virtuellem Unternehmen |
| `POST /api/task` | Aufgabe einreihen `{"beschreibung": "..."}` |
| `GET /api/business` | nur echte Kennzahlen, keine Simulationen als real |

## Plugins

Eingebaut: `system` (CPU/RAM), `files` (Sandbox-Dateizugriff), `calc`
(sicherer Rechner), `clock`. Eigene Plugins: `.py`-Datei in `jarvis/plugins/`
mit einer `PLUGIN`-Instanz ablegen — Autorisierung pro Team über
`allowed_teams`. Aufgaben-Syntax im Dashboard: `!plugin <name> <aktion> key=wert`

## Tests

```bash
python -m pytest jarvis/tests/ -q     # 7 Tests: Identität, Adressraum, Plugins, Pool-Limit
```

## Architektur

```
jarvis/
├── core/
│   ├── identity.py      # prozeduraler 100-Mrd-Adressraum, rekursive Unternehmen
│   ├── orchestrator.py  # Task-Queue, hardware-begrenzter Worker-Pool, Gedächtnis (SQLite)
│   ├── plugins.py       # Plugin-Registry mit Team-Autorisierung
│   └── brain.py         # Claude-Anbindung (api) / Offline-Modus, ehrlich getrennt
├── dashboard/           # FastAPI + Live-Ticker (Single-Page, kein Build nötig)
├── plugins/             # eigene Erweiterungen hier ablegen
├── tests/               # pytest-Suite
├── run.py               # Einstiegspunkt
└── Start-Jarvis.ps1     # Windows: Abhängigkeiten + Start + Browser
```

## Roadmap (noch nicht enthalten, ehrlich gelistet)

- 🎤 Wake Word „Hey Jarvis" + Sprachein-/-ausgabe (openWakeWord/Vosk + TTS) —
  braucht Mikrofon-Setup auf dem Ziel-PC, hier nicht testbar
- 🖥️ Windows-Steuerung (Programme/Maus/Tastatur) — sicherheitskritisch,
  gehört hinter eine explizite Freigabe-Schicht
- 📧 E-Mail-, Kalender-, Smart-Home-Plugins über das bestehende Plugin-System
