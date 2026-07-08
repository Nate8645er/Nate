# Jarvis – Modularer KI-Assistent für Windows 11

Ein lokaler, modularer KI-Assistent auf Basis von **Python 3.12** und **Ollama**.
Alles läuft lokal auf deinem Rechner – keine Cloud, keine API-Kosten.

## Geplante Funktionen

| Modul | Funktion | Status |
|---|---|---|
| `jarvis/core` | Ollama-Anbindung, Gesprächslogik | ✅ Schritt 1 |
| `jarvis/speech` | Sprache zu Text, Text zu Sprache | geplant |
| `jarvis/memory` | Kurz- und Langzeitgedächtnis | geplant |
| `jarvis/system` | Windows-Programme öffnen und steuern | geplant |
| `jarvis/vision` | Bildschirmanalyse | geplant |
| `jarvis/web` | Internetsuche | geplant |
| `jarvis/plugins` | Plugin-System für neue Funktionen | geplant |
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
    │   └── ollama_client.py    # Verbindung zu Ollama
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

## Installation (Windows 11, PowerShell)

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

Erwartete Ausgabe: Jarvis verbindet sich mit Ollama, listet die installierten
Modelle auf, stellt eine Testfrage und gibt die Antwort des Modells aus.

## Konfiguration

Alle Einstellungen liegen in `config/config.json`:

- `ollama.base_url` – Adresse des Ollama-Servers (Standard: `http://localhost:11434`)
- `ollama.model` – verwendetes Modell (Standard: `llama3.2`)
- `logging.level` – Log-Detailgrad (`DEBUG`, `INFO`, `WARNING`, `ERROR`)

## Logs

Alle Ereignisse werden in der Konsole angezeigt und zusätzlich in
`logs/jarvis.log` gespeichert.
