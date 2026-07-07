"""Speech-to-text via faster-whisper (optional dependency).

transcribe() accepts raw audio bytes (WAV) and returns text. When the
dependency is missing the engine reports itself unavailable — the browser
dashboard then falls back to the Web Speech API, so voice keeps working.
"""

from __future__ import annotations

import asyncio
import io
import logging

log = logging.getLogger(__name__)


class SpeechToText:
    def __init__(self, model_size: str = "small", language: str = "de") -> None:
        self.language = language
        self.model_size = model_size
        self._model = None
        self.available = False
        try:
            from faster_whisper import WhisperModel  # optional dependency

            self._model = WhisperModel(model_size, device="auto", compute_type="int8")
            self.available = True
            log.info("STT ready: faster-whisper (%s)", model_size)
        except ImportError:
            log.info("faster-whisper not installed — server-side STT disabled "
                     "(browser Web Speech API still works)")
        except Exception as exc:  # noqa: BLE001 - model download/GPU issues
            log.warning("STT init failed: %s", exc)

    async def transcribe(self, wav_bytes: bytes) -> str:
        if not self.available or self._model is None:
            raise RuntimeError(
                "Lokale Spracherkennung nicht installiert. "
                "Aktiviere sie mit: pip install 'jarvis-ai-os[voice]'"
            )

        def run() -> str:
            segments, _info = self._model.transcribe(
                io.BytesIO(wav_bytes), language=self.language
            )
            return " ".join(s.text.strip() for s in segments).strip()

        return await asyncio.to_thread(run)
