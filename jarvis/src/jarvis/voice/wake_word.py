"""Wake-word detection.

Two interchangeable detectors behind the :class:`WakeWordDetector` protocol:

* :class:`OpenWakeWordDetector` — neural detection via ``openwakeword``
  (optional dependency), fed with 16 kHz mono int16 frames.
* :class:`EnergyKeywordDetector` — dependency-free fallback that detects
  voice activity by RMS energy, with an always-trigger mode for
  push-to-talk-style setups.

:func:`create_wake_word_detector` picks the best available implementation.
"""

from __future__ import annotations

import contextlib
from typing import Protocol, runtime_checkable

from jarvis.core.config import VoiceConfig
from jarvis.core.errors import VoiceError
from jarvis.core.logging import get_logger
from jarvis.voice.audio import rms_level

logger = get_logger("voice.wake_word")

# Spellings of the default wake word mapped to openwakeword's pretrained model.
_BUILTIN_MODELS: dict[str, str] = {
    "jarvis": "hey_jarvis",
    "hey jarvis": "hey_jarvis",
    "hey_jarvis": "hey_jarvis",
}


@runtime_checkable
class WakeWordDetector(Protocol):
    """Streaming detector fed with consecutive 16 kHz mono int16 PCM frames."""

    def process(self, frame: bytes) -> bool:
        """Consume one frame; return ``True`` when the wake word was detected."""
        ...

    def reset(self) -> None:
        """Clear internal state, e.g. after a detection was handled."""
        ...


class OpenWakeWordDetector:
    """Neural wake-word detection backed by ``openwakeword``.

    The configured wake word is resolved against openwakeword's pretrained
    models (``"jarvis"`` maps to ``"hey_jarvis"``); any other value is passed
    through, so custom model names or paths work as well.
    """

    def __init__(self, wake_word: str = "jarvis", threshold: float = 0.5) -> None:
        try:
            import numpy as np
            from openwakeword.model import Model
        except ImportError as exc:
            raise VoiceError(
                "openwakeword is not installed. "
                "Install the voice extras with `pip install 'jarvis-assistant[voice]'`.",
                cause=exc,
            ) from exc
        if not 0.0 < threshold <= 1.0:
            raise VoiceError(f"wake_word_threshold must be in (0, 1], got {threshold}")
        self._np = np
        self.threshold = float(threshold)
        self.model_name = _BUILTIN_MODELS.get(wake_word.strip().lower(), wake_word)
        try:
            self._model = Model(wakeword_models=[self.model_name])
        except Exception as exc:
            raise VoiceError(
                f"Could not load wake-word model '{self.model_name}': {exc}", cause=exc
            ) from exc

    def process(self, frame: bytes) -> bool:
        """Feed one int16 frame; return ``True`` if any model score passes the threshold."""
        usable = len(frame) - (len(frame) % 2)
        if usable == 0:
            return False
        samples = self._np.frombuffer(frame[:usable], dtype=self._np.int16)
        scores = self._model.predict(samples)
        return any(float(score) >= self.threshold for score in scores.values())

    def reset(self) -> None:
        """Clear the model's internal audio buffers after a detection."""
        with contextlib.suppress(Exception):
            self._model.reset()


class EnergyKeywordDetector:
    """Dependency-free fallback detector based on RMS voice activity.

    Triggers once ``activation_frames`` consecutive frames exceed
    ``threshold`` (normalised RMS in ``[0, 1]``). With ``always_trigger=True``
    every frame triggers, which turns the assistant into an always-listening
    or push-to-talk style setup without any wake-word model.
    """

    def __init__(
        self,
        threshold: float = 0.02,
        activation_frames: int = 3,
        always_trigger: bool = False,
    ) -> None:
        if not 0.0 < threshold <= 1.0:
            raise VoiceError(f"threshold must be in (0, 1], got {threshold}")
        if activation_frames < 1:
            raise VoiceError(f"activation_frames must be >= 1, got {activation_frames}")
        self.threshold = float(threshold)
        self.activation_frames = int(activation_frames)
        self.always_trigger = bool(always_trigger)
        self._voiced_streak = 0

    def process(self, frame: bytes) -> bool:
        """Consume one frame; trigger on sustained voice activity."""
        if self.always_trigger:
            return True
        if rms_level(frame) >= self.threshold:
            self._voiced_streak += 1
            if self._voiced_streak >= self.activation_frames:
                self._voiced_streak = 0
                return True
        else:
            self._voiced_streak = 0
        return False

    def reset(self) -> None:
        """Clear the voiced-frame streak."""
        self._voiced_streak = 0


def create_wake_word_detector(config: VoiceConfig) -> WakeWordDetector:
    """Create the best available detector for the given voice configuration.

    Prefers :class:`OpenWakeWordDetector`; falls back to
    :class:`EnergyKeywordDetector` (with its default RMS threshold — the
    configured ``wake_word_threshold`` is a model-confidence value and does
    not translate to an energy level) when openwakeword is unavailable.
    """
    try:
        return OpenWakeWordDetector(config.wake_word, config.wake_word_threshold)
    except VoiceError as exc:
        logger.info(
            "openwakeword unavailable (%s); falling back to energy-based voice activity",
            exc.message,
        )
        return EnergyKeywordDetector()


__all__: list[str] = [
    "EnergyKeywordDetector",
    "OpenWakeWordDetector",
    "WakeWordDetector",
    "create_wake_word_detector",
]
