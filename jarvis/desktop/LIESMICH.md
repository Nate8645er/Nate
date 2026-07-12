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
