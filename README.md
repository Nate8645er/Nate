# Jarvis – Modularer KI-Assistent für Windows 11

Ein lokaler, modularer KI-Assistent auf Basis von **Python 3.12** und **Ollama**.
Alles läuft lokal auf deinem Rechner – keine Cloud, keine API-Kosten.

## Geplante Funktionen

| Modul | Funktion | Status |
|---|---|---|
| `jarvis/core` | Ollama-Anbindung, Gesprächslogik | ✅ Schritt 1+2 |
| `jarvis/speech` | Sprache zu Text, Text zu Sprache | geplant |
| `jarvis/memory` | Kurz- und Langzeitgedächtnis | ✅ Schritt 2+4 |
| `jarvis/system` | Windows-Programme öffnen und steuern | ✅ Schritt 5 |
| `jarvis/vision` | Bildschirmanalyse | geplant |
| `jarvis/web` | Internetsuche | geplant |
| `jarvis/plugins` | Plugin-System für neue Funktionen | ✅ Schritt 3 |
| `skills/` | Skill-System (Prompts als Markdown) | ✅ Schritt 3 |
| Agenten + Firma | ULTRA AI ENTERPRISE OS in Jarvis | ✅ Schritt 3 |
| `jarvis/utils` | Konfiguration, Logging | ✅ Schritt 1 |

## Projektstruktur

```
Nate/
├── main.py                     # Einstiegspunkt
├── requirements.txt            # Python-Abhängigkeiten
├── README.md
├── .gitignore
├── config/
│   └── config.json             # Zentrale Konfiguration
├── logs/                       # Logdateien (automatisch erstellt)
├── data/
│   └── memory/                 # Gedächtnis-Daten (später)
└── jarvis/                     # Hauptpaket
    ├── core/
    │   ├── ollama_client.py    # Verbindung zu Ollama
    │   └── conversation.py     # Gesprächslogik + Kurzzeitgedächtnis
    ├── speech/
    ├── memory/
    ├── system/
    ├── vision/
    ├── web/
    ├── plugins/
    └── utils/
        ├── config_loader.py    # Lädt config/config.json
        └── logger.py           # Logging (Konsole + Datei)
```

## Voraussetzungen

1. **Python 3.12** – [python.org](https://www.python.org/downloads/) (bei der Installation „Add Python to PATH" anhaken)
2. **Ollama** – [ollama.com/download](https://ollama.com/download) installieren
3. Ein Modell herunterladen (im Terminal / PowerShell):
   ```powershell
   ollama pull llama3.2
   ```

## Schnellstart (Windows 11) – empfohlen

1. Projekt als ZIP herunterladen:
   https://github.com/Nate8645er/Nate/archive/refs/heads/claude/jarvis-ai-assistant-wvvtds.zip
2. ZIP entpacken (Rechtsklick → „Alle extrahieren")
3. **Doppelklick auf `jarvis_starten.bat`**

Die Startdatei prüft Python und Ollama, erstellt beim ersten Mal die
virtuelle Umgebung, installiert die Pakete, lädt bei Bedarf das Modell
herunter und startet Jarvis. Voraussetzung: Python und Ollama sind
installiert (Links siehe oben).

## Manuelle Installation (Windows 11, PowerShell)

```powershell
# 1. In den Projektordner wechseln
cd <Pfad-zum-Projekt>

# 2. Virtuelle Umgebung erstellen
python -m venv .venv

# 3. Virtuelle Umgebung aktivieren
.\.venv\Scripts\Activate.ps1

# 4. Abhängigkeiten installieren
pip install -r requirements.txt
```

> Falls PowerShell die Aktivierung blockiert:
> `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

## Starten

```powershell
# Ollama muss laufen (Ollama-App starten oder:)
ollama serve

# In einem zweiten Terminal (mit aktivierter .venv):
python main.py
```

Jarvis startet einen interaktiven Gesprächsmodus mit Kurzzeitgedächtnis –
das Modell erinnert sich innerhalb der Sitzung an den bisherigen Verlauf.

**Befehle im Chat:**

| Befehl | Wirkung |
|---|---|
| `/hilfe` | Alle Befehle anzeigen |
| `/plugins` | Geladene Plugins und ihre Befehle |
| `/zeit`, `/datum` | Uhrzeit / Datum (Plugin) |
| `/rechne 2*(3+4)` | Taschenrechner (Plugin) |
| `/systeminfo` | Infos über deinen Rechner (Plugin) |
| `/skills` | Verfügbare Skills anzeigen |
| `/skill uebersetzen Hallo` | Skill ausführen |
| `/oeffne rechner` | Programm/Datei/Webseite öffnen (`/apps` = Liste) |
| `/schliesse rechner` | Programm beenden |
| `/apps` | Alle bekannten Programme anzeigen |
| `/merken Mein Name ist Nate` | Fakt dauerhaft speichern (Langzeitgedächtnis) |
| `/gedaechtnis` | Alle gespeicherten Fakten anzeigen |
| `/vergessen 2` | Fakt Nr. 2 löschen (`/vergessen alles` = alle) |
| `/agenten` | Alle Agenten des Unternehmens |
| `/agent ultra-architect <Frage>` | Einen Agenten direkt fragen |
| `/firma <Aufgabe>` | Aufgabe durchs komplette Unternehmen schicken |
| `/neu` | Gesprächsverlauf (Kurzzeitgedächtnis) löschen |
| `/exit` oder `/quit` | Jarvis beenden (auch `Strg+C`) |

**Eigene Plugins:** Neue `.py`-Datei in `jarvis/plugins/` mit einer
`JarvisPlugin`-Unterklasse ablegen – wird beim Start automatisch geladen.

**Eigene Skills:** Neue `.md`-Datei in `skills/` ablegen (Frontmatter mit
`name`/`description`, Body = Prompt mit `{input}`-Platzhalter).

**Das Unternehmen:** `/firma` schickt eine Aufgabe nacheinander durch die
Abteilungen des ULTRA AI ENTERPRISE OS (Orchestrator → Architekt →
Fullstack → QA, konfigurierbar in `config.json` unter `company.pipeline`).
Die Agenten-Rollen kommen direkt aus `ultra-enterprise-os/agents/`.
Hinweis: Jede Abteilung ist eine eigene Modell-Anfrage – bei lokalen
Modellen dauert `/firma` entsprechend ein paar Minuten.

## Konfiguration

Alle Einstellungen liegen in `config/config.json`:

- `ollama.base_url` – Adresse des Ollama-Servers (Standard: `http://localhost:11434`)
- `ollama.model` – verwendetes Modell (Standard: `llama3.2`)
- `logging.level` – Log-Detailgrad (`DEBUG`, `INFO`, `WARNING`, `ERROR`)

## Logs

Alle Ereignisse werden in der Konsole angezeigt und zusätzlich in
`logs/jarvis.log` gespeichert.
