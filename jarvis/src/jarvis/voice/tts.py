"""Text-to-speech backends.

Three backends behind the :class:`TextToSpeech` protocol:

* :class:`PiperTTS` — fast local synthesis via ``piper-tts``.
* :class:`XttsTTS` — Coqui XTTS with voice cloning (``speaker_wav``).
* :class:`NullTTS` — logs the text instead of speaking (headless/tests).

All heavy imports happen lazily inside the constructors.
:func:`create_tts` selects the backend from :class:`VoiceConfig`; the
``"auto"`` backend picks the first importable one (piper → xtts → null).
The ``emotion`` parameter maps to prosody parameters (speed/temperature)
where a backend supports them and is ignored gracefully otherwise.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from jarvis.core.config import VoiceConfig
from jarvis.core.errors import VoiceError
from jarvis.core.logging import get_logger

logger = get_logger("voice.tts")

SynthResult = tuple[int, Any]
"""``(sample_rate, payload)`` where payload is int16 PCM bytes or a float numpy array."""

TTS_BACKENDS: frozenset[str] = frozenset({"auto", "piper", "xtts", "coqui", "none"})
"""Backend names accepted by :func:`create_tts` (mirrors ``VoiceConfig.tts_backend``)."""


@dataclass(frozen=True, slots=True)
class EmotionPreset:
    """Prosody parameters approximating an emotional tone."""

    speed: float = 1.0
    temperature: float = 0.65


EMOTION_PRESETS: dict[str, EmotionPreset] = {
    "neutral": EmotionPreset(speed=1.0, temperature=0.65),
    "happy": EmotionPreset(speed=1.08, temperature=0.8),
    "serious": EmotionPreset(speed=0.94, temperature=0.5),
    "urgent": EmotionPreset(speed=1.18, temperature=0.55),
}


def emotion_preset(emotion: str | None) -> EmotionPreset:
    """Return the preset for an emotion name; unknown or empty values map to neutral."""
    if emotion:
        preset = EMOTION_PRESETS.get(emotion.strip().lower())
        if preset is not None:
            return preset
        logger.debug("Unknown emotion '%s'; using neutral", emotion)
    return EMOTION_PRESETS["neutral"]


@runtime_checkable
class TextToSpeech(Protocol):
    """Synthesises speech for one piece of text."""

    async def synth(self, text: str, emotion: str = "neutral") -> SynthResult:
        """Return ``(sample_rate, payload)``; payload may be empty for muted backends."""
        ...


class PiperTTS:
    """Local neural TTS via ``piper-tts``; requires an ``.onnx`` voice model file.

    Emotion mapping: ``speed`` becomes Piper's ``length_scale`` (inverse);
    ``temperature`` has no Piper equivalent and is ignored.
    """

    def __init__(self, voice_path: str | None) -> None:
        if not voice_path:
            raise VoiceError(
                "Piper needs a voice model: set `voice.tts_voice` to the path of a "
                "Piper `.onnx` voice file (see https://github.com/rhasspy/piper)."
            )
        try:
            from piper.voice import PiperVoice
        except ImportError as exc:
            raise VoiceError(
                "piper-tts is not installed. "
                "Install the voice extras with `pip install 'jarvis-assistant[voice]'`.",
                cause=exc,
            ) from exc
        path = Path(voice_path).expanduser()
        if not path.is_file():
            raise VoiceError(f"Piper voice model not found: {path}")
        try:
            self._voice = PiperVoice.load(str(path))
        except Exception as exc:
            raise VoiceError(f"Could not load Piper voice '{path}': {exc}", cause=exc) from exc
        self.sample_rate = int(getattr(self._voice.config, "sample_rate", 22_050))

    async def synth(self, text: str, emotion: str = "neutral") -> SynthResult:
        """Synthesise *text* to int16 PCM bytes in a worker thread."""
        preset = emotion_preset(emotion)
        length_scale = 1.0 / preset.speed if preset.speed > 0 else 1.0

        def _run() -> bytes:
            try:
                if hasattr(self._voice, "synthesize_stream_raw"):  # piper-tts < 1.3
                    try:
                        return b"".join(
                            self._voice.synthesize_stream_raw(text, length_scale=length_scale)
                        )
                    except TypeError:  # variant without a length_scale parameter
                        return b"".join(self._voice.synthesize_stream_raw(text))
                # piper-tts >= 1.3: synthesize() yields AudioChunk objects.
                try:
                    from piper import SynthesisConfig

                    chunks = self._voice.synthesize(
                        text, syn_config=SynthesisConfig(length_scale=length_scale)
                    )
                except (ImportError, TypeError):
                    chunks = self._voice.synthesize(text)
                return b"".join(getattr(chunk, "audio_int16_bytes", b"") for chunk in chunks)
            except VoiceError:
                raise
            except Exception as exc:
                raise VoiceError(f"Piper synthesis failed: {exc}", cause=exc) from exc

        return self.sample_rate, await asyncio.to_thread(_run)


class XttsTTS:
    """Coqui XTTS backend with optional voice cloning via a reference clip.

    Emotion mapping: ``speed`` and ``temperature`` are passed to the Coqui API
    where accepted; unsupported keyword combinations are dropped one by one so
    synthesis degrades instead of failing.
    """

    DEFAULT_MODEL = "tts_models/multilingual/multi-dataset/xtts_v2"

    def __init__(
        self,
        model_name: str | None = None,
        speaker_wav: str | None = None,
        language: str = "en",
    ) -> None:
        try:
            import numpy as np
            from TTS.api import TTS
        except ImportError as exc:
            raise VoiceError(
                "coqui-tts is not installed. "
                "Install it with `pip install 'jarvis-assistant[tts-xtts]'`.",
                cause=exc,
            ) from exc
        self._np = np
        self.model_name = model_name or self.DEFAULT_MODEL
        self.speaker_wav = speaker_wav
        self.language = language
        try:
            self._tts = TTS(self.model_name)
        except Exception as exc:
            raise VoiceError(
                f"Could not load Coqui TTS model '{self.model_name}': {exc}", cause=exc
            ) from exc
        synthesizer = getattr(self._tts, "synthesizer", None)
        self.sample_rate = int(getattr(synthesizer, "output_sample_rate", 24_000) or 24_000)

    async def synth(self, text: str, emotion: str = "neutral") -> SynthResult:
        """Synthesise *text* to a float32 numpy array in a worker thread."""
        preset = emotion_preset(emotion)

        def _run() -> Any:
            base: dict[str, Any] = {"text": text}
            if self.speaker_wav:
                base["speaker_wav"] = self.speaker_wav
            if self.language:
                base["language"] = self.language
            # Most expressive first; drop unsupported keywords step by step.
            attempts: list[dict[str, Any]] = [
                {**base, "speed": preset.speed, "temperature": preset.temperature},
                {**base, "speed": preset.speed},
                base,
                {"text": text},
            ]
            last_error: Exception | None = None
            for kwargs in attempts:
                try:
                    return self._tts.tts(**kwargs)
                except TypeError as exc:  # unsupported keyword for this model
                    last_error = exc
                except Exception as exc:
                    raise VoiceError(f"XTTS synthesis failed: {exc}", cause=exc) from exc
            raise VoiceError(
                f"XTTS rejected all parameter combinations: {last_error}", cause=last_error
            ) from last_error

        wav = await asyncio.to_thread(_run)
        return self.sample_rate, self._np.asarray(wav, dtype=self._np.float32)


class NullTTS:
    """No-op backend that logs the text instead of speaking (headless mode, tests)."""

    def __init__(self, sample_rate: int = 16_000) -> None:
        self.sample_rate = sample_rate

    async def synth(self, text: str, emotion: str = "neutral") -> SynthResult:
        """Log the text and return an empty payload (nothing to play)."""
        logger.info("TTS muted (%s): %s", emotion or "neutral", text)
        return self.sample_rate, b""


def create_tts(config: VoiceConfig, *, language: str = "en") -> TextToSpeech:
    """Create the TTS backend selected by ``config.tts_backend``.

    Explicit backends (``piper``, ``xtts``/``coqui``, ``none``) raise
    :class:`VoiceError` when unavailable. ``auto`` tries piper first, then
    XTTS, and falls back to :class:`NullTTS` so the assistant keeps working
    in text-only mode. *language* is the assistant language passed to
    multilingual backends (XTTS).
    """
    backend = config.tts_backend
    if backend not in TTS_BACKENDS:
        raise VoiceError(
            f"Unknown TTS backend '{backend}'; expected one of {sorted(TTS_BACKENDS)}."
        )
    if backend == "none":
        return NullTTS(config.sample_rate)
    if backend == "piper":
        return PiperTTS(config.tts_voice)
    if backend in ("xtts", "coqui"):
        return _create_xtts(config, language)
    # "auto": first importable/configured backend wins.
    try:
        return PiperTTS(config.tts_voice)
    except VoiceError as exc:
        logger.info("Piper TTS unavailable: %s", exc.message)
    try:
        return _create_xtts(config, language)
    except VoiceError as exc:
        logger.info("XTTS unavailable: %s", exc.message)
    logger.warning("No TTS backend available; responses will be text-only.")
    return NullTTS(config.sample_rate)


def _create_xtts(config: VoiceConfig, language: str) -> XttsTTS:
    """Build an XTTS backend; ``tts_voice`` is honoured when it names a Coqui model."""
    model_name = (
        config.tts_voice
        if config.tts_voice and config.tts_voice.startswith("tts_models/")
        else None
    )
    return XttsTTS(
        model_name=model_name,
        speaker_wav=config.tts_speaker_wav,
        language=language,
    )


__all__: list[str] = [
    "EMOTION_PRESETS",
    "TTS_BACKENDS",
    "EmotionPreset",
    "NullTTS",
    "PiperTTS",
    "SynthResult",
    "TextToSpeech",
    "XttsTTS",
    "create_tts",
    "emotion_preset",
]
