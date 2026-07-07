"""Text-to-speech via Piper (optional dependency).

synthesize() returns WAV bytes for a sentence. Missing dependency ->
unavailable; the dashboard then uses the browser's speechSynthesis.
"""

from __future__ import annotations

import asyncio
import io
import logging
import wave

log = logging.getLogger(__name__)


class TextToSpeech:
    def __init__(self, voice: str = "de_DE-thorsten-medium") -> None:
        self.voice_name = voice
        self._voice = None
        self.available = False
        try:
            from piper import PiperVoice  # optional dependency
            from piper.download import ensure_voice_exists, find_voice, get_voices

            data_dir = "."
            try:
                voices_info = get_voices(data_dir, update_voices=False)
                ensure_voice_exists(voice, [data_dir], data_dir, voices_info)
            except Exception:  # noqa: BLE001 - voice may already exist locally
                pass
            model, config = find_voice(voice, [data_dir])
            self._voice = PiperVoice.load(model, config)
            self.available = True
            log.info("TTS ready: piper (%s)", voice)
        except ImportError:
            log.info("piper-tts not installed — server-side TTS disabled "
                     "(browser speechSynthesis still works)")
        except Exception as exc:  # noqa: BLE001
            log.warning("TTS init failed: %s", exc)

    async def synthesize(self, text: str) -> bytes:
        if not self.available or self._voice is None:
            raise RuntimeError(
                "Lokale Sprachausgabe nicht installiert. "
                "Aktiviere sie mit: pip install 'jarvis-ai-os[voice]'"
            )

        def run() -> bytes:
            buf = io.BytesIO()
            with wave.open(buf, "wb") as wav_file:
                self._voice.synthesize(text, wav_file)
            return buf.getvalue()

        return await asyncio.to_thread(run)
