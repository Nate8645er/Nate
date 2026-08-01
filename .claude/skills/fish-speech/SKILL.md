---
name: fish-speech
description: Steuert Fish Speech (Fish Audio S2) fuer Text-to-Speech und Stimmklonen - Installation, Modellgewichte, Gradio-WebUI, HTTP-API-Server und api_client. Aktivieren bei Anfragen zu Fish Speech, S2-Pro, lokalem TTS, Sprachsynthese auf eigener Hardware, Stimmklonen mit Referenzaudio, oder wenn ein laufender Fish-Speech-Server angesprochen werden soll.
---

# Fish Speech (Fish Audio S2)

Lokales Text-to-Speech mit Stimmklonen. Laeuft auf eigener Hardware, nicht in
der Cloud. Dieser Skill deckt Installation, Start und Ansteuerung ab.

Quelle: https://github.com/fishaudio/fish-speech

## Zuerst pruefen: Lizenz

Fish Speech steht unter der **Fish Audio Research License**, nicht unter MIT
oder Apache. Der Unterschied ist erheblich:

- Forschung und nicht-kommerzielle Nutzung (privat, Evaluation, Testen): frei
- **Jede kommerzielle Nutzung braucht einen separaten schriftlichen Vertrag
  mit Fish Audio.**

"Commercial Purpose" ist in der Lizenz weit gefasst und schliesst ausdruecklich
interne Geschaeftsablaeufe und alles ein, was direkt oder indirekt Umsatz
erzeugt. Fuer Werbespots, Produktvideos, Shop-Inhalte oder Kundenkommunikation
reicht die Gratis-Lizenz also nicht.

Wenn der Nutzer Fish Speech fuer etwas Geschaeftliches einsetzen will: darauf
hinweisen, bevor Aufwand in das Setup fliesst. Kontakt fuer eine kommerzielle
Lizenz steht in der LICENSE-Datei des Repos.

## Hardware-Realitaet

- **24 GB VRAM** werden fuer Inferenz empfohlen
- Offiziell unterstuetzt: Linux und WSL
- CPU-Betrieb ist installierbar (`.[cpu]`), aber sehr langsam
- AMD ROCm (RDNA3/RDNA4) und Intel Arc XPU werden unterstuetzt

Reicht die Hardware nicht, ist das ein Blocker und kein Konfigurationsproblem.
Ehrlich sagen statt Workarounds bauen.

## Installation

Systempakete zuerst:

```bash
apt install portaudio19-dev libsox-dev ffmpeg
```

Dann per Conda:

```bash
conda create -n fish-speech python=3.12
conda activate fish-speech
pip install -e .[cu129]     # CUDA-Variante: cu126, cu128 oder cu129
pip install -e .[cpu]       # alternativ nur CPU
```

Oder per UV (schneller):

```bash
uv sync --python 3.12 --extra cu129
```

Bei einem pyaudio-Fehler waehrend der Installation: `conda install pyaudio`,
danach `pip install -e .` erneut.

## Modellgewichte laden

Ohne die Gewichte startet nichts. Sie sind mehrere Gigabyte gross und liegen
nicht im Repo:

```bash
hf download fishaudio/s2-pro --local-dir checkpoints/s2-pro
```

## Betrieb

### Gradio-WebUI

```bash
python tools/run_webui.py            # --compile fuer Beschleunigung
```

### API-Server

```bash
python tools/api_server.py \
  --llama-checkpoint-path checkpoints/s2-pro \
  --decoder-checkpoint-path checkpoints/s2-pro/codec.pth \
  --listen 0.0.0.0:8080
```

Weitere Optionen: `--compile` (torch.compile), `--half` (fp16),
`--api-key` (Bearer-Token erzwingen), `--workers` (Prozesse).

### Docker

```bash
docker compose --profile webui up      # WebUI auf Port 7860
docker compose --profile server up     # API auf Port 8080
COMPILE=1 docker compose --profile server up
BACKEND=cpu docker compose --profile webui up
```

Volumes: `./checkpoints:/app/checkpoints` und `./references:/app/references`.

## Ansteuern

Immer zuerst pruefen, ob der Server ueberhaupt laeuft:

```bash
curl -X GET http://127.0.0.1:8080/v1/health
# erwartet: {"status":"ok"}
```

Antwortet er nicht, ist das die Ursache jedes Folgefehlers. Nicht weiter
debuggen, bevor der Health-Check gruen ist.

Endpunkte:

- `POST /v1/tts` — Sprachsynthese
- `POST /v1/vqgan/encode` — Referenzaudio in VQ-Tokens
- `POST /v1/vqgan/decode` — VQ-Tokens zurueck zu Audio

Mitgelieferter Client:

```bash
python tools/api_client.py \
  --url http://127.0.0.1:8080/v1/tts \
  --text "Text der gesprochen werden soll" \
  --output ausgabe
```

Mit gespeicherter Referenzstimme:

```bash
python tools/api_client.py \
  --url http://127.0.0.1:8080/v1/tts \
  --text "Text" \
  --reference_id mein-sprecher \
  --output ausgabe
```

Das Basismodell wird beim **Serverstart** festgelegt, nicht pro Anfrage.
`--reference_id` waehlt die Stimme, nicht das Modell.

### Wichtige Client-Parameter

| Parameter | Standard | Bedeutung |
|---|---|---|
| `--format` | `wav` | auch `pcm`, `mp3`, `opus` |
| `--temperature` | `0.8` | Variabilitaet |
| `--top_p` | `0.8` | Top-p-Sampling |
| `--repetition_penalty` | `1.1` | gegen Wiederholungen |
| `--max_new_tokens` | `1024` | `0` = ohne Limit |
| `--chunk_length` | `300` | Segmentlaenge |
| `--rate` | `44100` | Samplerate |
| `--seed` | keiner | gesetzt = deterministisch; fixiert **nicht** die Klangfarbe |
| `--no-play` | — | Abspielen unterdruecken (Standard ist abspielen) |
| `--streaming` | aus | Streaming-Antwort |
| `--api_key` | — | noetig wenn der Server mit `--api-key` laeuft |

## Stimmklonen ueber die Kommandozeile

Nur noetig, wenn ohne Server gearbeitet wird. Drei Schritte:

```bash
# 1. VQ-Tokens aus Referenzaudio -> erzeugt fake.npy und fake.wav
python fish_speech/models/dac/inference.py \
    -i "referenz.wav" \
    --checkpoint-path "checkpoints/s2-pro/codec.pth"

# 2. Semantische Tokens aus Text -> erzeugt codes_0.npy
python fish_speech/models/text2semantic/inference.py \
    --text "Zieltext" \
    --prompt-text "Text der Referenzaufnahme" \
    --prompt-tokens "fake.npy"

# 3. Audio erzeugen -> fake.wav
python fish_speech/models/dac/inference.py -i "codes_0.npy"
```

Bei GPUs ohne bf16-Unterstuetzung `--half` ergaenzen.

## Grenzen

- `--compile` funktioniert nicht unter Windows und macOS ohne manuell
  installiertes Triton
- `--seed` macht die Ausgabe reproduzierbar, aber die Klangfarbe damit nicht
  konstant — dafuer braucht es eine Referenzstimme
- Die Gewichte kommen von HuggingFace und muessen vor dem ersten Start
  vollstaendig geladen sein; Docker-Container erwarten sie unter
  `/app/checkpoints`

## Was dieser Skill nicht kann

Er startet nichts von selbst. Fish Speech braucht eine Maschine mit GPU, auf
der es installiert ist. Ist keine da, ist der ehrliche Rat ein gehosteter
TTS-Dienst und nicht dieses Repo.
