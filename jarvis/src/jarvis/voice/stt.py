"""Speech-to-text.

:class:`FasterWhisperSTT` wraps ``faster-whisper`` (optional dependency,
imported lazily) behind the :class:`SpeechToText` protocol.
:class:`UtteranceSegmenter` is a dependency-free, energy-based
end-of-speech segmenter used to cut microphone frames into utterances.
"""

from __future__ import annotations

import asyncio
import math
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

from jarvis.core.errors import VoiceError
from jarvis.core.logging import get_logger
from jarvis.voice.audio import rms_level

logger = get_logger("voice.stt")


@dataclass(slots=True)
class TranscriptionResult:
    """Outcome of a speech-to-text run."""

    text: str
    language: str | None = None
    confidence: float = 0.0


@runtime_checkable
class SpeechToText(Protocol):
    """Transcribes one utterance of 16 kHz mono audio."""

    async def transcribe(
        self, audio: bytes | Any, language: str | None = None
    ) -> TranscriptionResult:
        """Transcribe int16 PCM bytes or a float32 numpy array."""
        ...


def _load_attempts(device: str) -> list[tuple[str, str]]:
    """Return (device, compute_type) combinations to try, most capable first."""
    if device == "cuda":
        return [("cuda", "float16"), ("cuda", "int8")]
    if device == "cpu":
        return [("cpu", "float16"), ("cpu", "int8")]
    return [("cuda", "float16"), ("cuda", "int8"), ("cpu", "float16"), ("cpu", "int8")]


class FasterWhisperSTT:
    """Local Whisper transcription via ``faster-whisper``.

    The model is loaded eagerly in the constructor with a device/compute-type
    fallback chain (``float16`` first, then ``int8``; ``auto`` tries CUDA
    before CPU) so misconfiguration fails fast with a clear error.
    """

    def __init__(
        self,
        model_name: str = "large-v3",
        device: str = "auto",
        sample_rate: int = 16_000,
    ) -> None:
        try:
            import numpy as np
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise VoiceError(
                "faster-whisper is not installed. "
                "Install the voice extras with `pip install 'jarvis-assistant[voice]'`.",
                cause=exc,
            ) from exc
        if device not in ("auto", "cuda", "cpu"):
            raise VoiceError(f"Unknown STT device '{device}'; expected auto, cuda or cpu.")
        self._np = np
        self.model_name = model_name
        self.sample_rate = sample_rate
        last_error: Exception | None = None
        for dev, compute_type in _load_attempts(device):
            try:
                self._model = WhisperModel(model_name, device=dev, compute_type=compute_type)
                self.device = dev
                self.compute_type = compute_type
                logger.info(
                    "Whisper model '%s' loaded (device=%s, compute_type=%s)",
                    model_name,
                    dev,
                    compute_type,
                )
                break
            except Exception as exc:  # backend raises various exception types
                last_error = exc
        else:
            raise VoiceError(
                f"Could not load Whisper model '{model_name}': {last_error}",
                cause=last_error,
            ) from last_error

    async def transcribe(
        self, audio: bytes | Any, language: str | None = None
    ) -> TranscriptionResult:
        """Transcribe one utterance; runs the model in a worker thread."""
        samples = self._as_float32(audio)
        if samples.size == 0:
            return TranscriptionResult(text="", language=language, confidence=0.0)

        def _run() -> TranscriptionResult:
            segments, info = self._model.transcribe(
                samples, language=language, beam_size=5, vad_filter=True
            )
            texts: list[str] = []
            logprobs: list[float] = []
            for segment in segments:  # generator: consumes/decodes lazily
                texts.append(segment.text.strip())
                logprobs.append(float(segment.avg_logprob))
            text = " ".join(t for t in texts if t).strip()
            confidence = 0.0
            if logprobs:
                confidence = min(1.0, max(0.0, math.exp(sum(logprobs) / len(logprobs))))
            return TranscriptionResult(
                text=text,
                language=getattr(info, "language", None) or language,
                confidence=confidence,
            )

        return await asyncio.to_thread(_run)

    def _as_float32(self, audio: bytes | Any) -> Any:
        """Convert int16 PCM bytes or a numpy array to float32 in ``[-1, 1]``."""
        np = self._np
        if isinstance(audio, (bytes, bytearray, memoryview)):
            data = bytes(audio)
            usable = len(data) - (len(data) % 2)
            if usable == 0:
                return np.empty(0, dtype=np.float32)
            return np.frombuffer(data[:usable], dtype=np.int16).astype(np.float32) / 32768.0
        values = np.asarray(audio)
        if values.ndim > 1:
            values = values.reshape(-1)
        if values.dtype == np.int16:
            return values.astype(np.float32) / 32768.0
        return values.astype(np.float32)


class UtteranceSegmenter:
    """Incremental, energy-based end-of-speech segmentation.

    Feed fixed-size PCM frames via :meth:`feed`. Frames before speech starts
    are kept only as a short lead-in buffer (so waiting does not grow
    unbounded). Once a frame exceeds ``silence_threshold`` the utterance is
    open; it is finalised after ``silence_ms`` of trailing silence or when
    ``max_ms`` of audio has accumulated, whichever comes first. Pure Python,
    no optional dependencies.
    """

    def __init__(
        self,
        frame_ms: int,
        *,
        silence_threshold: float = 0.01,
        silence_ms: int = 700,
        max_ms: int = 30_000,
        max_lead_ms: int = 1_000,
    ) -> None:
        if frame_ms <= 0:
            raise VoiceError(f"frame_ms must be positive, got {frame_ms}")
        if not 0.0 < silence_threshold <= 1.0:
            raise VoiceError(f"silence_threshold must be in (0, 1], got {silence_threshold}")
        if silence_ms <= 0 or max_ms <= 0:
            raise VoiceError("silence_ms and max_ms must be positive")
        self.frame_ms = frame_ms
        self.silence_threshold = silence_threshold
        self._silence_frames_needed = max(1, math.ceil(silence_ms / frame_ms))
        self._max_frames = max(1, max_ms // frame_ms)
        self._max_lead_frames = max(1, max_lead_ms // frame_ms)
        self._frames: list[bytes] = []
        self._speech_started = False
        self._trailing_silence = 0

    @property
    def speech_started(self) -> bool:
        """Whether voice activity has been observed since the last reset."""
        return self._speech_started

    def feed(self, frame: bytes) -> bytes | None:
        """Consume one frame; return the finished utterance once speech ended.

        Returns ``None`` while the utterance is still open (or speech has not
        started yet). After returning audio the segmenter resets itself and is
        ready for the next utterance.
        """
        voiced = rms_level(frame) >= self.silence_threshold
        self._frames.append(frame)
        if not self._speech_started:
            if voiced:
                self._speech_started = True
            elif len(self._frames) > self._max_lead_frames:
                del self._frames[0]
            return None
        self._trailing_silence = 0 if voiced else self._trailing_silence + 1
        if (
            self._trailing_silence >= self._silence_frames_needed
            or len(self._frames) >= self._max_frames
        ):
            return self._finalise()
        return None

    def flush(self) -> bytes:
        """Return whatever speech was collected so far (``b""`` if none) and reset."""
        if not self._speech_started:
            self.reset()
            return b""
        return self._finalise()

    def reset(self) -> None:
        """Discard buffered audio and start a fresh utterance."""
        self._frames.clear()
        self._speech_started = False
        self._trailing_silence = 0

    def _finalise(self) -> bytes:
        utterance = b"".join(self._frames)
        self.reset()
        return utterance


__all__: list[str] = [
    "FasterWhisperSTT",
    "SpeechToText",
    "TranscriptionResult",
    "UtteranceSegmenter",
]
