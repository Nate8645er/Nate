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

Der Belegschaft-Betrieb startet **automatisch** beim Start (abschaltbar mit
`JARVIS_WORKFORCE=0` bzw. `--no-workforce`); auf der Seite `/mitarbeiter` lässt
er sich zusätzlich per Button steuern. Ein Hintergrund-Scheduler fegt in rollenden
Wellen durch den **gesamten** 100-Milliarden-Adressraum, materialisiert und
aktiviert die Mitarbeiter fortlaufend (real gemessen ~50–60 Tsd./Sekunde je
nach CPU). Damit ist die komplette Organisation *in Betrieb*. Das Dashboard zeigt
live: durchlaufene Mitarbeiter, echte Rate/Sekunde und Abdeckung des Adressraums.

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

### Echter 24/7-Dauerbetrieb (Windows)

Damit JARVIS im Hintergrund läuft — automatisch bei jedem Windows-Start, mit
aktivem Autopilot und Selbst-Neustart bei Absturz:

```powershell
powershell -ExecutionPolicy Bypass -File .\jarvis\Install-Jarvis-Service.ps1
```

Das registriert eine geplante Aufgabe „JARVIS 24/7", die sich bei jeder Anmeldung
unsichtbar startet. Dashboard jederzeit unter http://127.0.0.1:8787. Wieder
entfernen:

```powershell
powershell -ExecutionPolicy Bypass -File .\jarvis\Install-Jarvis-Service.ps1 -Uninstall
```

Alternativ manuell mit Autopilot starten: `python -m jarvis.run --autopilot`.
Ehrlich: „24/7" gilt, solange dein PC eingeschaltet ist. Für Dauerbetrieb rund
um die Uhr auch bei ausgeschaltetem PC bräuchte es einen immer laufenden
Rechner oder kleinen Server.

**Was dieses System NICHT tut:** Geld generieren. Es gibt keine
Geld-Generier-Funktion und keinen simulierten Umsatz-Ticker — das
Business-Panel zeigt ausschließlich echte Betriebsdaten (0.00 CHF, bis eine
echte Datenquelle wie ein Buchhaltungs-Export angebunden ist). Demo-Aufgaben
sind im Ticker klar als `DEMO` markiert.

## Start (Windows)

**Einfachster Weg — für den eigenen PC (empfohlen):** Einmal `JARVIS-PC-Einrichten.cmd`
doppelklicken. Das installiert alles, schaltet die PC-Steuerung frei (Programme,
Maus, Tastatur, Bildschirm, Browser), legt ein Desktop-Symbol **„JARVIS starten"**
an und startet JARVIS. Danach genügt der Doppelklick auf das Desktop-Symbol (oder
`JARVIS-Starten.cmd`).

Nur starten (ohne Neu-Einrichtung):

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

## Viele Modelle über OpenRouter (Werkzeug „modelle")

JARVIS kann zusätzlich **viele KI-Modelle** über einen einzigen OpenRouter-Key
nutzen (Claude, GPT, Gemini, Grok, Llama, Mistral, DeepSeek, Qwen …):

```powershell
setx OPENROUTER_API_KEY "sk-or-..."   # Key von openrouter.ai/keys
```

Im Chat/per Sprache:

- `modell gpt: erkläre mir Rekursion` — ein bestimmtes Modell fragen
- `frage gemini: schreibe ein Haiku` — dito
- `vergleiche die modelle: was ist die beste Strategie?` — mehrere Modelle
  parallel fragen und die Antworten nebeneinander sehen

Das ist ein **neutraler Multi-Modell-Zugang** — kein „Jailbreak", keine
Prompt-Verschleierung, keine Umgehung von Modell-Sicherheiten. Ohne Key meldet
das Werkzeug das ehrlich und tut nichts.

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

**Claw Code / Claude Code integriert:** Das `code`-Tool findet automatisch einen
installierten Agenten-Binary (`claw.exe`, `claude`, `agent` im PATH, unter
`%LOCALAPPDATA%\Programs\ClawCode` oder im Downloads-Build) und ruft ihn mit
`--model claude-fable-5` auf. Ansprechen per Sprache/Chat: **„claw code …"**,
**„clawcode …"** oder **„claude code …"**. Liegt deine `claw.exe` woanders,
verbinde sie mit `JARVIS-ClawCode-Verbinden.cmd` (setzt `JARVIS_CLAW_PATH`).
Ohne Binary oder API-Key fällt es ehrlich auf das JARVIS-Gehirn zurück.

**Skills** (`/werkzeuge`, wie Claude.ai/Claude-Code-Skills): Markdown-Dateien in
`~/.jarvis/skills/` — mitgeliefert: `zusammenfassen`, `code-review`,
`recherche`, `projektplan`. Anwenden: `!skill <name> <aufgabentext>`. Neue
Skills einfach als `.md` mit Front-Matter (`name`, `description`) ablegen.

**Eigene Plugins:** `.py`-Datei in `jarvis/plugins/` mit einer `PLUGIN`-Instanz
ablegen — Autorisierung pro Team über `allowed_teams`.

## Sprachbefehle (natürliche Sprache → echte Aktion)

Freie Sätze im Chat oder per „Hey Jarvis" werden erkannt und wirklich ausgeführt
(PC-Steuerung muss dafür freigeschaltet sein, s. u.):

- „**öffne YouTube**" / „mach mir YouTube auf" → öffnet die Seite im Browser
- „**öffne Chrome**" / „starte Firefox" → öffnet den gewünschten Browser
- „**öffne YouTube in Chrome**" / „öffne Google in Firefox" → Seite im gewählten Browser
- „**starte den Rechner**" / „öffne Notepad" → startet das Programm
- „**schließe notepad**" → beendet das Programm
- „**mach einen Screenshot**" → nimmt ein Bildschirmfoto auf
- „**suche nach …**" → Internet-Suche

Wird kein Kommando erkannt (z. B. eine echte Frage), antwortet normal das Gehirn.

### Browser-Automatisierung (JARVIS arbeitet selbst im Web)

Über das `browser_auto`-Werkzeug (Playwright) steuert JARVIS einen echten
Browser: navigieren, Inhalt lesen, Links auflisten, klicken, in Felder tippen,
absenden, Screenshot. Sprachbefehle:

- „**navigiere zu wikipedia**" / „surfe zu github.com" → öffnet die Seite im gesteuerten Browser
- „**lies die Seite**" / „was steht auf der Seite" → liest den Seiteninhalt
- „**was ist auf dem Bildschirm**" / „was siehst du" / „analysiere den Bildschirm"
  → JARVIS macht einen Screenshot und beschreibt per Fable 5, **was** darauf zu sehen ist (Vision)
- „**welche Links gibt es**" → listet die Links
- „**im Browser klicke auf Anmelden**" → klickt das Element
- direkt: `!plugin browser_auto type feld=#suche text=Wetter`, dann `!plugin browser_auto press taste=Enter`

Nutzt bevorzugt dein installiertes Chrome/Edge (kein Extra-Download); sonst
`playwright install chromium`. Auf Windows läuft der Browser **sichtbar** (du
siehst JARVIS arbeiten), Override per `JARVIS_BROWSER_HEADLESS=1`. Gleicher
Schalter wie die PC-Steuerung: `JARVIS_ALLOW_PC=1`.

## Sicherheits-Monitor (Seite `/sicherheit`)

JARVIS überwacht deinen PC automatisch **alle 30 Minuten** über die echten
Windows-Bordmittel und schlägt bei Problemen Alarm:

- **Microsoft Defender**: aktiv? Echtzeitschutz an? Bedrohungen erkannt?
- **Firewall**: alle Profile aktiv?
- **Virensignaturen**: Alter — werden beim Check automatisch aktualisiert
- **Alarm** im Dashboard + Log, sobald etwas nicht stimmt

Buttons auf der Seite: „Jetzt prüfen", „Signaturen aktualisieren", „Viren-Scan"
(Defender-Quick-Scan), „Windows-Update suchen". Der Monitor startet automatisch
(abschaltbar mit `JARVIS_SECURITY=0`). Scan/Update/Signaturen greifen ins System
ein und brauchen `JARVIS_ALLOW_PC=1`.

### Bodyguards (24/7-Wächter-Truppe)

Sechs benannte Wächter-Agenten patrouillieren **rund um die Uhr** (alle 5 Min),
jeder auf einem Posten: **Defender, Firewall, Prozesse, Signaturen, Netzwerk,
Updates**. Sie kontrollieren laufend, zeigen ihren Status (WACHSAM/ALARM) und
**beheben sichere Probleme automatisch** (Firewall/Echtzeitschutz reaktivieren,
Signaturen aktualisieren, bei Bedrohung sofort Defender-Scan) — sofern
`JARVIS_ALLOW_PC=1` gesetzt ist; sonst melden sie nur. Sichtbar auf `/sicherheit`.

**Ehrlich:** JARVIS ist kein eigener Virenscanner. Echtzeit-Erkennung und
-Blockade von Viren/Angriffen leistet **Microsoft Defender** selbst — JARVIS
orchestriert, überwacht, alarmiert und kann Scans/Updates auslösen. „Sofort auf
Hacker/Viren reagieren" heißt: Defender blockt in Echtzeit, JARVIS meldet und
handelt im 30-Minuten-Takt. Ein automatisches Installieren von Windows-Updates
(mit möglichem Neustart) passiert nur nach deiner Bestätigung.

## Sicherheit (des Programms selbst)

JARVIS wurde einem Security-Review unterzogen; folgende Schutzmaßnahmen sind aktiv:

- **Server bindet standardmäßig nur an `127.0.0.1`** (nur lokal). Bei Bindung an
  eine Netzwerk-Adresse (`--host 0.0.0.0`) erscheint eine Warnung.
- **Host-Header-Schutz** gegen DNS-Rebinding: Anfragen mit fremdem Host werden
  mit 403 abgewiesen. Für LAN-Zugriff `JARVIS_ALLOWED_HOSTS` setzen.
- **Gefährliche Werkzeuge (`shell`, `code`) sind standardmäßig gesperrt.** Sie
  erreichen das Betriebssystem und werden nur mit ausdrücklichem Opt-in
  freigeschaltet: `setx JARVIS_ALLOW_DANGEROUS 1` (Windows) bzw.
  `export JARVIS_ALLOW_DANGEROUS=1`, dann neu starten.
- **PC-Steuerung (`pc`) hat einen EIGENEN Schalter** — Programme öffnen/schließen,
  Maus, Tastatur, Screenshot. Standardmäßig aus; getrennt von Shell/Code
  freischaltbar: `setx JARVIS_ALLOW_PC 1`, dann neu starten. Aktionen:
  `open`, `close`, `apps`, `move`, `click`, `type`, `key`, `screenshot`.
  Maus/Tastatur/Screenshot brauchen `pyautogui` (unter Windows automatisch mit
  installiert) und einen echten Desktop.
- **Datei-Sandbox** (`files`, `read`, `edit`, `glob`, `grep`): Zugriff strikt auf
  den Arbeitsbereich begrenzt (`is_relative_to`-Prüfung, keine Symlinks nach außen).
- **SSRF-Schutz** in `webfetch`: interne/private/loopback-Adressen (inkl. Cloud-
  Metadaten `169.254.169.254`) werden blockiert.
- **API-Key** wird mit Dateirechten `0600` gespeichert (nicht weltlesbar) und nie
  geloggt oder in Antworten zurückgegeben.
- **XSS-Schutz**: nutzer-/modellgenerierter Text wird im Dashboard escaped.
- **Rechner** (`calc`) mit Limit gegen Ressourcen-Erschöpfung (`**`).

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
