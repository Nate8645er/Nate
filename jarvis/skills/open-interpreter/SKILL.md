---
name: open-interpreter
description: Einsetzen wenn der Nutzer eine Aufgabe auf dem lokalen Rechner ueber Open Interpreter ausfuehren lassen will, "Interpreter"/"Open Interpreter" erwaehnt, oder es installieren/konfigurieren moechte.
---

## Was es ist

Open Interpreter ist ein CLI-Tool, das Claude Code-/Shell-Befehle direkt
auf dem lokalen Rechner des Nutzers ausfuehren laesst — also echte
Aktionen ausserhalb der aktuellen Claude-Code-Sitzung (Dateien anlegen,
Programme starten, Systemeinstellungen aendern usw.). Das Binary heisst
`interpreter`.

## Verfuegbarkeit pruefen

- Linux/macOS: `which interpreter`
- Windows: `where interpreter`

Falls nicht installiert:

- Linux/macOS: `pip install open-interpreter`
- Windows: PowerShell `irm https://www.openinterpreter.com/install.ps1 | iex`
  oder die mitgelieferte Datei `jarvis/desktop/Install-OpenInterpreter.bat`
  doppelklicken lassen.

## Voraussetzung: API-Key

Open Interpreter braucht `ANTHROPIC_API_KEY` als Umgebungsvariable, um
mit Claude zu sprechen. Ohne gesetzten Key funktioniert es nicht.

Konfig-Profil (optional, fuer Standardwerte):

- Linux: `~/.config/open-interpreter/profiles/default.yaml`
- Windows: das `%APPDATA%`- bzw. `%USERPROFILE%`-Aequivalent

Modell im Profil (LiteLLM-Prefix-Konvention): `anthropic/claude-opus-4-8`.

## Nutzung

Interaktiv (Nutzer bestaetigt jeden Befehl selbst):

```
interpreter
```

Nicht-interaktiv, aus Claude Code heraus delegiert:

```
interpreter -y --model anthropic/claude-opus-4-8 "<aufgabe>"
```

Achtung: `-y` fuehrt Befehle **ohne Rueckfrage** aus.

Nuetzliche Flags:

- Kostenlimit setzen: `-b <USD>`
- Guenstigeres Modell fuer einfache Aufgaben: `-m anthropic/claude-haiku-4-5`

## Sicherheitsregeln (verbindlich)

- `-y` **nur** fuer eindeutig harmlose, lesende oder rein erzeugende
  Aufgaben verwenden.
- **Niemals** `-y` fuer loeschende oder systemveraendernde Aufgaben
  einsetzen, ohne dass der Nutzer den konkreten Auftrag vorher bestaetigt
  hat.
- Vor jedem Aufruf dem Nutzer klar sagen, was genau an Open Interpreter
  uebergeben wird.
- Jede Nutzung verbraucht echte API-Tokens und verursacht echte Kosten.

## Abgrenzung zu Claude Code selbst

Innerhalb eines Repos bzw. Projekts erledigt Claude Code Aufgaben mit dem
eigenen Bash-Tool selbst — das ist billiger und direkter. Open Interpreter
nur einsetzen, wenn der Nutzer es ausdruecklich moechte oder die Aufgabe
eine eigenstaendige lokale Automatisierung ausserhalb der aktuellen
Session ist (z. B. den PC selbst steuern, Programme oeffnen, lokale
Systemaufgaben ausserhalb des Projektordners).
