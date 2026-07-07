"""Text-to-speech engines.

Two interchangeable backends, both exposing `available`, `mime` and
`synthesize(text) -> bytes`:

  * ElevenLabsTTS — cloud voices via the ElevenLabs API (PCM wrapped as
    WAV). Chosen when an API key + voice id are configured.
  * PiperTTS     — fully local voices via piper (WAV, optional dependency).

If neither is available the dashboard falls back to the browser's
speechSynthesis, so speech output always works.
"""

from __future__ import annotations

import asyncio
import io
import logging
import wave

import httpx

log = logging.getLogger(__name__)


def pcm_to_wav(pcm: bytes, sample_rate: int = 22050) -> bytes:
    """Wrap raw 16-bit mono PCM in a WAV container."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm)
    return buf.getvalue()


class ElevenLabsTTS:
    """Cloud TTS via ElevenLabs.

    Requests raw PCM and wraps it as WAV so browsers AND the local voice
    satellite (sounddevice) can play the same payload without an MP3 codec.
    """

    mime = "audio/wav"
    sample_rate = 22050

    def __init__(
        self,
        api_key: str,
        voice_id: str,
        model: str = "eleven_multilingual_v2",
    ) -> None:
        self.api_key = api_key
        self.voice_id = voice_id
        self.model = model
        self.available = bool(api_key and voice_id)
        if self.available:
            log.info("TTS ready: elevenlabs (voice %s)", voice_id)

    async def synthesize(self, text: str) -> bytes:
        if not self.available:
            raise RuntimeError(
                "ElevenLabs nicht konfiguriert — JARVIS_ELEVENLABS_API_KEY "
                "und JARVIS_ELEVENLABS_VOICE_ID in .env setzen."
            )
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}",
                params={"output_format": f"pcm_{self.sample_rate}"},
                headers={"xi-api-key": self.api_key},
                json={"text": text, "model_id": self.model},
            )
            resp.raise_for_status()
            return pcm_to_wav(resp.content, self.sample_rate)


class PiperTTS:
    """Local TTS via piper (optional dependency); returns WAV bytes."""

    mime = "audio/wav"

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


def create_tts(
    provider: str,
    piper_voice: str,
    elevenlabs_api_key: str = "",
    elevenlabs_voice_id: str = "",
    elevenlabs_model: str = "eleven_multilingual_v2",
) -> ElevenLabsTTS | PiperTTS:
    """Pick the TTS backend. "auto" prefers ElevenLabs when configured."""
    if provider in ("auto", "elevenlabs") and elevenlabs_api_key and elevenlabs_voice_id:
        return ElevenLabsTTS(elevenlabs_api_key, elevenlabs_voice_id, elevenlabs_model)
    if provider == "elevenlabs":
        log.warning("ElevenLabs requested but key/voice missing — trying piper")
    return PiperTTS(piper_voice)
