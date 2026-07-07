"""Voice pipeline: wake word -> STT -> orchestrator -> TTS.

Two modes work together:
  * Server mode  — local mic + openwakeword + faster-whisper + piper
                   (install with the [voice] extra, runs on your machine).
  * Browser mode — the dashboard captures speech with the Web Speech API
                   and plays answers with speechSynthesis; the server just
                   relays text. Zero extra dependencies.

speak() publishes every utterance as a "voice.speak" event; the dashboard
voices it, and if piper is available the audio is attached as WAV (base64).
"""

from __future__ import annotations

import base64
import logging
from typing import TYPE_CHECKING

from jarvis.voice.stt import SpeechToText
from jarvis.voice.tts import create_tts
from jarvis.voice.wakeword import WakeWordListener

if TYPE_CHECKING:
    from jarvis.kernel import Kernel

log = logging.getLogger(__name__)


class VoicePipeline:
    def __init__(self, kernel: "Kernel") -> None:
        self.kernel = kernel
        cfg = kernel.settings
        self.stt = SpeechToText(model_size=cfg.stt_model, language=cfg.language)
        self.tts = create_tts(
            cfg.tts_provider,
            piper_voice=cfg.tts_voice,
            elevenlabs_api_key=cfg.elevenlabs_api_key,
            elevenlabs_voice_id=cfg.elevenlabs_voice_id,
            elevenlabs_model=cfg.elevenlabs_model,
        )
        self.wakeword = WakeWordListener(wake_word=cfg.wake_word)

    def status(self) -> dict[str, bool | str]:
        return {
            "stt_local": self.stt.available,
            "tts_backend": type(self.tts).__name__,
            "tts_available": self.tts.available,
            "wakeword_local": self.wakeword.available,
            "wake_word": self.kernel.settings.wake_word,
            "browser_fallback": True,
        }

    async def transcribe(self, wav_bytes: bytes) -> str:
        return await self.stt.transcribe(wav_bytes)

    async def speak(self, text: str) -> None:
        """Announce text to every connected UI (and synthesize if possible)."""
        if not text:
            return
        payload: dict[str, str] = {"text": text}
        if self.tts.available:
            try:
                audio = await self.tts.synthesize(text)
                payload["audio_b64"] = base64.b64encode(audio).decode()
                payload["mime"] = self.tts.mime
            except Exception as exc:  # noqa: BLE001 - never let TTS kill a reply
                log.warning("TTS synthesis failed: %s", exc)
        await self.kernel.bus.publish("voice.speak", payload, source="voice")

    async def handle_voice_input(self, wav_bytes: bytes, session: str = "default") -> str:
        """Full loop for uploaded audio: transcribe, then hand to orchestrator."""
        text = await self.transcribe(wav_bytes)
        if text:
            await self.kernel.orchestrator.handle_utterance(text, session=session)
        return text
