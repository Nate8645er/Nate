# Blin als Siri-Kurzbefehl (iPhone)

„Hey Siri, Blin" — du sprichst, Blin denkt (Claude/Fable 5), Blin antwortet
mit deiner ElevenLabs-Stimme. Der sichere, offizielle Weg auf dem iPhone.

## Sicherheit zuerst (bitte lesen)

- Deine **API-Keys** (Anthropic + ElevenLabs) gibst du **nur in die
  Kurzbefehle-App auf deinem iPhone** ein — nie an mich, nie ins Repo.
- **Teile den Kurzbefehl nicht** mit sichtbarem Key: wer ihn bekommt, hat
  deine Keys. Wenn du teilen willst, vorher die Text-Felder mit den Keys
  leeren.
- Voice-ID ist nicht geheim; Keys schon.

## Was du brauchst

1. **Anthropic API-Key** (`sk-ant-…`) von console.anthropic.com
2. **ElevenLabs API-Key** + deine **Voice-ID** `e3bIMyLemdwvh75g9Vpt`
3. iPhone mit der App **Kurzbefehle** (vorinstalliert)

## Kurzbefehl bauen (Schritt für Schritt)

Kurzbefehle-App → **+** (neuer Kurzbefehl) → Aktionen in dieser Reihenfolge
hinzufügen (oben suchen und antippen):

1. **„Text"** → trage deinen Anthropic-Key ein.
   Danach: **„Variable festlegen"** → Name `ANTHROPIC_KEY`.
2. **„Text"** → trage deinen ElevenLabs-Key ein.
   Danach: **„Variable festlegen"** → Name `ELEVEN_KEY`.
3. **„Diktat"** (Text diktieren) → Sprache Deutsch. Das ist deine Frage an Blin.
   Danach: **„Variable festlegen"** → Name `FRAGE`.
4. **„Wörterbuch"** (JSON-Body für Claude) mit diesen Einträgen:
   - `model` (Text) → `claude-fable-5`
   - `max_tokens` (Zahl) → `1024`
   - `system` (Text) → `Du bist Blin, ein hilfreicher, direkter Sprachassistent. Antworte kurz und gesprochen, in maximal 3 Sätzen.`
   - `messages` (Array) → 1 Eintrag vom Typ **Wörterbuch**:
     - `role` (Text) → `user`
     - `content` (Text) → Variable **FRAGE**
5. **„Inhalte von URL abrufen"** → auf **Anzeigen**/Pfeil tippen:
   - **URL**: `https://api.anthropic.com/v1/messages`
   - **Methode**: `POST`
   - **Header** (drei Stück):
     - `x-api-key` → Variable `ANTHROPIC_KEY`
     - `anthropic-version` → `2023-06-01`
     - `content-type` → `application/json`
   - **Anfragetext**: **JSON** → wähle das **Wörterbuch** aus Schritt 4
6. **„Wörterbuchwert abrufen"** → Schlüssel `content` aus der Antwort.
   Dann nochmal **„Wörterbuchwert abrufen"** → Schlüssel `text` (erstes
   Element). Ergebnis: **„Variable festlegen"** → Name `ANTWORT`.
   (Blins Textantwort.)
7. **ElevenLabs-Stimme** — **„Wörterbuch"** für den Sprach-Body:
   - `text` (Text) → Variable **ANTWORT**
   - `model_id` (Text) → `eleven_multilingual_v2`
8. **„Inhalte von URL abrufen"**:
   - **URL**: `https://api.elevenlabs.io/v1/text-to-speech/e3bIMyLemdwvh75g9Vpt`
   - **Methode**: `POST`
   - **Header**:
     - `xi-api-key` → Variable `ELEVEN_KEY`
     - `content-type` → `application/json`
     - `accept` → `audio/mpeg`
   - **Anfragetext**: **JSON** → das Wörterbuch aus Schritt 7
9. **„Audio abspielen"** (oder „Ton abspielen") → nimmt das Ergebnis von
   Schritt 8 (die MP3). Blin spricht mit deiner Stimme.

Kurzbefehl oben **„Blin"** nennen. Fertig.

## Starten per Stimme

- Sag **„Hey Siri, Blin"** → sprich deine Frage → Blin antwortet mit Stimme.
- Beim ersten Mal fragt iOS nach **Mikrofon** und **Netzwerk** → erlauben.

## Falls es klemmt (ehrlich)

- **Kein Ton, aber Text kommt:** ElevenLabs-Schritt prüfen (Key, Voice-ID,
  Header `accept: audio/mpeg`). Zur Not Schritt 7–9 weglassen und stattdessen
  **„Text vorlesen"** mit Variable `ANTWORT` nehmen — dann spricht die
  iPhone-Stimme (funktioniert immer, klingt aber nicht wie ElevenLabs).
- **Fehler 401 bei Claude:** Anthropic-Key falsch/leer.
- **Fehler 404 bei Claude:** dein Key hat kein Fable 5 — im Wörterbuch
  (Schritt 4) `model` auf ein Modell ändern, das dein Key nutzen darf
  (z. B. `claude-sonnet-5`).
- **Fehler 401 bei ElevenLabs:** ElevenLabs-Key falsch.

## Was Blin per Siri kann — und was nicht

- ✅ Zuhören, denken (echtes Claude/Fable 5), mit deiner Stimme antworten.
- ✅ Erweiterbar: weitere Kurzbefehl-Aktionen (Nachricht senden, App öffnen,
  Wecker stellen, Kalender, Standort) hinzufügen — Blin kann sie ausloesen.
- ⚠️ Er steuert nicht beliebige fremde Apps „von innen"; er nutzt nur, was
  die Kurzbefehle-App an Aktionen erlaubt. Das ist Apples Sicherheitsgrenze.
