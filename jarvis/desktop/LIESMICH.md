# JARVIS Desktop

## Was ist das?

JARVIS Desktop ist ein lokales Mission-Control-Dashboard mit Sprachsteuerung.
Es laeuft auf deinem eigenen Rechner und wird von Claude angetrieben (Claude
Fable 5, mit automatischem Fallback auf Opus, falls Fable 5 eine Anfrage
einmal ablehnt).

## Voraussetzungen

- Windows
- Python 3.10 oder neuer
- Ein Anthropic-API-Key von https://platform.claude.com/
- Chrome oder Edge (die Spracherkennung im Browser braucht einen der beiden)

## Einrichtung

1. API-Key setzen:

   ```
   setx ANTHROPIC_API_KEY "sk-ant-..."
   ```

   Danach ein **neues** Terminalfenster oeffnen, damit die Aenderung wirksam
   wird.

2. Doppelklick auf `Start-JARVIS.bat`.

3. Der Browser oeffnet sich automatisch unter http://127.0.0.1:8737

Start-JARVIS.bat richtet dabei optional auch noch das Claude Code Plugin
fable-baton ein (wenn Claude Code installiert ist) und bietet die Installation
von Open Interpreter an.

## Sprachsteuerung

- Mikrofon-Button gedrueckt halten, um einmalig zu sprechen.
- Oder "Freihand" aktivieren und Befehle mit dem Weckwort **"Jarvis"**
  beginnen (z. B. "Jarvis, wie ist das Wetter?").
- Antworten werden vorgelesen. Mit dem Schalter "Stimme" laesst sich das
  stummschalten.
- Die Sprache der Oberflaeche und der Sprachausgabe ist Deutsch.

## Konfiguration (Umgebungsvariablen)

| Variable       | Bedeutung                          | Standardwert     |
| -------------- | ----------------------------------- | ---------------- |
| `JARVIS_MODEL` | Claude-Modell, das verwendet wird   | `claude-fable-5`  |
| `JARVIS_PORT`  | Port des lokalen Dashboards         | `8737`            |

## Kosten

Jede Anfrage geht an die Anthropic-API und kostet Tokens. Es faellt keine
zusaetzliche JARVIS-eigene Gebuehr an, aber der API-Verbrauch wird ueber
deinen Anthropic-Account abgerechnet.

## Autostart deaktivieren

Falls beim ersten Start "Ja" gewaehlt wurde, startet JARVIS automatisch mit
Windows. Zum Deaktivieren einfach diese Datei loeschen:

```
%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\JARVIS-Autostart.bat
```

## Fehlerbehebung

- **Kein Mikrofonzugriff:** Pruefe die Mikrofon-Berechtigung des Browsers
  fuer `127.0.0.1` (Chrome/Edge-Einstellungen -> Website-Berechtigungen).
- **Banner "kein API-Key":** API-Key wie oben beschrieben per `setx` setzen
  und `Start-JARVIS.bat` danach in einem neuen Terminal erneut starten.
- **Port bereits belegt:** Umgebungsvariable `JARVIS_PORT` auf einen anderen
  Port setzen, bevor `Start-JARVIS.bat` gestartet wird.

## PC bedienen: Open Interpreter (die Hände)

JARVIS Desktop ist die **Stimme und der Kopf**: Es hört zu, denkt nach und
redet mit dir - es führt aber selbst keine Befehle auf deinem PC aus.

Für die **Hände** - also damit tatsächlich etwas auf deinem PC passiert
(Programme öffnen, Dateien anlegen, Einstellungen ändern, ...) - gibt es
[Open Interpreter](https://www.openinterpreter.com/). Das ist ein separates,
eigenständiges Werkzeug: eine Kommandozeilen-KI, die echte Befehle im
Terminal ausführen kann und dich vor jedem einzelnen Befehl um Bestätigung
bittet.

### Installation

Doppelklick auf `Install-OpenInterpreter.bat` in diesem Ordner. Das Skript:

- prüft, ob `ANTHROPIC_API_KEY` gesetzt ist (derselbe Schlüssel, den auch
  JARVIS Desktop verwendet),
- installiert Open Interpreter über den offiziellen Installer,
- legt beim ersten Mal eine einfache Konfiguration an, die Claude als Modell
  verwendet.

### Benutzung

1. Ein Terminal öffnen (z. B. `cmd` oder PowerShell).
2. `interpreter` eingeben und Enter drücken.
3. Deinen Auftrag auf Deutsch beschreiben, z. B. "oeffne den Task-Manager".

### Sicherheit

Open Interpreter bestätigt jeden Befehl, bevor er ihn wirklich ausführt -
du siehst also vorher, was passieren würde, und kannst ablehnen. Trotzdem
gilt: Gib nur Aufträge, die du wirklich verstehst, und lies dir vorgeschlagene
Befehle vor der Bestätigung durch. Open Interpreter führt echte Befehle auf
deinem echten PC aus, es ist keine Simulation.

### Alternative

Wer eine vollständigere Integration möchte (Bildschirm sehen und steuern statt
nur Terminalbefehle), kann stattdessen die Claude Desktop-App mit der
"Computer Use"-Funktion verwenden.
