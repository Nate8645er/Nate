# Deutscher Sprachassistent — Deepgram Voice Agent Konfiguration

Konfiguration für einen deutschsprachigen Telefon-Sprachassistenten auf Basis der
[Deepgram Voice Agent API](https://developers.deepgram.com/docs/voice-agent)
(`Settings`-Nachricht, die beim Verbindungsaufbau über den WebSocket gesendet wird).

## Dateien

| Datei | Beschreibung |
|---|---|
| `settings.de.json` | **Empfohlene Konfiguration.** Vollständig deutsch: STT, TTS, Begrüßung und System-Prompt sind konsistent auf Deutsch. |
| `settings.en-prompt.json` | Ursprüngliche Variante mit englischem System-Prompt (nur als Referenz). Nicht empfohlen, da der englische Prompt mit englischen Beispielphrasen dem deutschen TTS/STT-Setup widerspricht. |

## Pipeline

| Komponente | Provider | Modell |
|---|---|---|
| Spracherkennung (listen) | Deepgram | `nova-3`, Sprache `de` |
| Sprachmodell (think) | Google | `gemini-3.1-flash-lite` |
| Sprachausgabe (speak) | Deepgram | `aura-2-lara-de` (deutsche Stimme „Lara") |

## Audio

- **Eingang:** `linear16`, 48 kHz (typisch für Browser-Mikrofone/WebRTC)
- **Ausgang:** `linear16`, 24 kHz, ohne Container (rohe PCM-Samples zum direkten Abspielen)

## Verwendung

Die JSON-Datei wird als erste Nachricht nach dem Öffnen der WebSocket-Verbindung
zu `wss://agent.deepgram.com/v1/agent/converse` gesendet:

```js
const ws = new WebSocket("wss://agent.deepgram.com/v1/agent/converse", [
  "token",
  process.env.DEEPGRAM_API_KEY,
]);
const settings = JSON.parse(fs.readFileSync("voice-assistant/settings.de.json", "utf8"));
ws.on("open", () => ws.send(JSON.stringify(settings)));
```

Der Deepgram-API-Key wird über die Umgebungsvariable `DEEPGRAM_API_KEY`
bereitgestellt und gehört nicht in dieses Repository. Für das `think`-Modell
(Google Gemini) wird der Schlüssel je nach Setup ebenfalls per Umgebungsvariable
bzw. in der Deepgram-Konsole hinterlegt.

## Hinweise zur Lokalisierung

Der System-Prompt in `settings.de.json` ist eine vollständige deutsche
Übersetzung des ursprünglichen englischen Prompts, mit lokalisierten Beispielen
(Temperaturen in Grad Celsius, 24-Stunden-Uhrzeiten, Sie-Form gegenüber
Anrufern) und dem expliziten Hinweis, ausschließlich Deutsch zu sprechen —
passend zur deutschen Begrüßung (`greeting`) und zur deutschen TTS-Stimme.
