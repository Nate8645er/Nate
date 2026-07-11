# Voice pipeline

```
microphone ──► wake word ──► utterance capture ──► STT (faster-whisper)
                                                        │
speaker ◄── TTS (Piper/XTTS) ◄── sentence splitter ◄── ask_stream()
        ▲                                               │
        └────────── barge-in (wake word while speaking) ┘
```

## Components

* **Wake word** — [openWakeWord](https://github.com/dscripka/openWakeWord) with
  the configured keyword (default "jarvis") and threshold. Without the
  dependency, an energy-based fallback detector is used.
* **STT** — [faster-whisper](https://github.com/SYSTRAN/faster-whisper) with
  `large-v3` by default; `stt_device: auto` picks CUDA when available
  (float16, falling back to int8/CPU automatically). End-of-speech is detected
  by ~700 ms of silence (30 s hard cap per utterance).
* **TTS** — pluggable backends, `auto` picks the first available:
  1. **Piper** — fast local neural voices (`tts_voice` = model path)
  2. **XTTS v2 / Coqui** — high-quality, multilingual, voice cloning via
     `tts_speaker_wav`, emotion presets (`neutral`, `happy`, `serious`,
     `urgent`)
  3. **Null** — logs text (headless/CI)
* **Streaming speech** — answers stream from the model; complete sentences are
  synthesized and spoken while the rest is still generating.
* **Interruption** — saying the wake word while JARVIS speaks stops playback
  immediately and starts listening (`allow_interruption`).

## Events (consumed by the GUI visualizer)

| Topic | Payload |
|---|---|
| `voice.wake` | `{}` — wake word detected |
| `voice.transcript` | `{"text"}` — recognised utterance |
| `voice.speaking` | `{"active": bool}` |
| `voice.level` | `{"level": 0..1}` — live RMS for the visualizer |

## Running

```bash
uv pip install -e ".[voice]"          # + tts-xtts extra for XTTS (Python < 3.13)
jarvis voice
```

GPU note: faster-whisper large-v3 runs comfortably on an 8 GB GPU; on CPU
choose a smaller model (`JARVIS_VOICE__STT_MODEL=small`). Piper voices are
downloaded from the [Piper voice catalog](https://github.com/rhasspy/piper/blob/master/VOICES.md).
