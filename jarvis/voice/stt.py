"""Speech-to-text engines.

Two interchangeable backends, both exposing `available` and
`transcribe(wav_bytes) -> str`:

  * LocalSTT  — faster-whisper on your machine (optional dependency,
                full privacy).
  * OpenAISTT — Whisper via the OpenAI API; used automatically when
                faster-whisper is not installed but an OpenAI key is
                configured, so voice works with zero local models.

If neither is available, the browser dashboard still provides voice via
the Web Speech API.
"""

from __future__ import annotations

import asyncio
import io
import logging

import httpx

log = logging.getLogger(__name__)


class LocalSTT:
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
            log.info("faster-whisper not installed")
        except Exception as exc:  # noqa: BLE001 - model download/GPU issues
            log.warning("Local STT init failed: %s", exc)

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


class OpenAISTT:
    """Whisper via the OpenAI API — no local model downloads needed."""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
        language: str = "de",
        model: str = "whisper-1",
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.language = language
        self.model = model
        self.available = bool(api_key)
        if self.available:
            log.info("STT ready: OpenAI %s", model)

    async def transcribe(self, wav_bytes: bytes) -> str:
        if not self.available:
            raise RuntimeError("OpenAI-STT nicht konfiguriert (JARVIS_OPENAI_API_KEY fehlt).")
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{self.base_url}/audio/transcriptions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                data={"model": self.model, "language": self.language},
                files={"file": ("speech.wav", wav_bytes, "audio/wav")},
            )
            resp.raise_for_status()
            return (resp.json().get("text") or "").strip()


def create_stt(
    model_size: str,
    language: str,
    openai_api_key: str = "",
    openai_base_url: str = "https://api.openai.com/v1",
) -> LocalSTT | OpenAISTT:
    """Prefer local whisper; fall back to the OpenAI API when a key exists."""
    local = LocalSTT(model_size=model_size, language=language)
    if local.available:
        return local
    if openai_api_key:
        return OpenAISTT(openai_api_key, openai_base_url, language)
    return local  # unavailable, but carries the helpful error message
