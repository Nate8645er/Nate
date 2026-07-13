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

## Belegschaft-Betrieb (ganze Organisation aktivieren)

Auf der Seite `/mitarbeiter` startet der Button **„GANZE BELEGSCHAFT AKTIVIEREN"**
einen kontinuierlichen Betrieb: ein Hintergrund-Scheduler fegt in rollenden
Wellen durch den **gesamten** 100-Milliarden-Adressraum, materialisiert und
aktiviert die Mitarbeiter fortlaufend (real gemessen ~1,5 Mio./Sekunde). Damit
ist die komplette Organisation *in Betrieb*. Das Dashboard zeigt live:
durchlaufene Mitarbeiter, Rate/Sekunde, Wellen und Abdeckung des Adressraums.

Ehrlich dabei: Zu jedem Zeitpunkt rechnen nur so viele *gleichzeitig*, wie die
Hardware zulässt — der Rest wird laufend durchgeschleust (echte HyperScale-
Logik). Der Betrieb macht einen leichten „Roll-Call" (Identität materialisieren),
**kein** bezahlter Modell-Aufruf pro Mitarbeiter — das wäre bei Milliarden
ruinös. Echte Fable-5-Denkarbeit bleibt den Aufgaben vorbehalten, die du gezielt
abschickst.

## 24/7-Autopilot (Seite `/autopilot`)

Der Autopilot lässt die Business-Mitarbeiter **rund um die Uhr eigene
Geschäftsideen erfinden** — jede mit Titel, Idee, Zielgruppe und konkretem
erstem Schritt. Wenn du wieder online kommst, zeigt das **Tages-Briefing**,
was heute erarbeitet wurde, plus „Profit heute (real)".

Ehrlich und wichtig: Der Autopilot erzeugt echte **Vorarbeit** (Ideen,
Konzepte, Entwürfe) — er verdient **kein Geld von allein**. „Profit heute"
zeigt ausschließlich real über das `finanzen`-Plugin erfasste Einnahmen und
bleibt 0.00 CHF, bis du echte Verkäufe einträgst. Aus einer Idee echtes Geld
zu machen, verlangt einen Menschen, der sie umsetzt (Shop, Zahlung, Verkauf).
Der Autopilot läuft nur, solange dein PC an ist; im Fable-5-Modus kostet jede
Idee einen echten Modell-Aufruf (Intervall daher gemächlich, Standard 180s).

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

## Werkzeuge, Plugins & Skills (alle aktiv)

**14 eingebaute Tools** — sichtbar und bedienbar auf der Seite `/werkzeuge`:

| Tool | Zweck |
|---|---|
| `system` | CPU/RAM/Plattform |
| `files` | Dateien im Arbeitsbereich (Sandbox) |
| `calc` | sicherer Rechner |
| `clock` | Datum/Uhrzeit |
| `aufgaben` | Aufgaben & Erinnerungen (echte Liste) |
| `finanzen` | echte Einnahmen/Ausgaben (kein simuliertes Geld) |
| `web` | Internet-Suche (DuckDuckGo) |
| `shell` | Terminal-Befehle (wie Claude Code Bash) |
| `read` | Datei lesen mit Zeilennummern (Claude Code Read) |
| `edit` | Text in Datei ersetzen (Claude Code Edit) |
| `glob` | Dateien per Muster finden (Claude Code Glob) |
| `grep` | in Dateien suchen (Claude Code Grep) |
| `webfetch` | URL abrufen und als Text zurückgeben (Claude Code WebFetch) |
| `code` | **Claude Code / Claw als Werkzeug — mit Fable 5** |

Aufgaben-Syntax: `!plugin <name> <aktion> key=wert` (Werte dürfen Leerzeichen
enthalten). Jedes Tool ist pro Team autorisiert; Tool-Aufgaben werden
automatisch an ein berechtigtes Team geroutet.

**Claude-Code-Brücke:** Das `code`-Tool findet automatisch einen installierten
Agenten-Binary (`claw`, `claude` oder `agent` im PATH oder unter
`%LOCALAPPDATA%\Programs\ClawCode`) und ruft ihn mit `--model claude-fable-5`
auf. Ohne Binary oder API-Key fällt es ehrlich auf das JARVIS-Gehirn zurück.

**Skills** (`/werkzeuge`, wie Claude.ai/Claude-Code-Skills): Markdown-Dateien in
`~/.jarvis/skills/` — mitgeliefert: `zusammenfassen`, `code-review`,
`recherche`, `projektplan`. Anwenden: `!skill <name> <aufgabentext>`. Neue
Skills einfach als `.md` mit Front-Matter (`name`, `description`) ablegen.

**Eigene Plugins:** `.py`-Datei in `jarvis/plugins/` mit einer `PLUGIN`-Instanz
ablegen — Autorisierung pro Team über `allowed_teams`.

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
