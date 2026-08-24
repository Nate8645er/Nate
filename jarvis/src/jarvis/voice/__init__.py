"""Voice subsystem: wake word, speech-to-text, text-to-speech and the voice loop.

Activated by :class:`jarvis.app.JarvisApp` through the module-level
:func:`register` hook. Heavy optional dependencies (sounddevice,
faster-whisper, openwakeword, piper/coqui) are imported lazily inside the
submodules, so ``import jarvis.voice`` always succeeds; features degrade
gracefully with clear install hints when the extras are missing.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from jarvis.core.errors import ToolError, VoiceError
from jarvis.core.logging import get_logger

if TYPE_CHECKING:
    from jarvis.app import JarvisApp
    from jarvis.voice.service import VoiceService as _VoiceService

logger = get_logger("voice")

__all__: list[str] = ["register"]

_EMOTIONS = ["neutral", "happy", "serious", "urgent"]
_BACKENDS = ["auto", "piper", "xtts", "coqui", "none"]


def register(app: JarvisApp) -> None:
    """Register the voice service and the voice tools on the application.

    Adds a :class:`~jarvis.voice.service.VoiceService` singleton factory to
    ``app.container`` and the ``voice_speak``, ``voice_listen`` and
    ``voice_set_backend`` tools to ``app.tools``. The service (and all audio
    hardware) is only instantiated when a tool or the voice loop is used.
    """
    from jarvis.voice.service import VoiceService

    def _build(_container: Any) -> VoiceService:
        return VoiceService(
            config=app.config,
            events=app.events,
            permissions=app.permissions,
            ask_stream=app.ask_stream,
        )

    app.container.register_singleton(VoiceService, _build)

    def _service() -> _VoiceService:
        return app.container.resolve(VoiceService)

    async def voice_speak(text: str, emotion: str | None = None) -> str:
        try:
            await _service().speak(text, emotion=emotion)
        except VoiceError as exc:
            raise ToolError(exc.message, tool="voice_speak", cause=exc) from exc
        return f"Spoke {len(text)} characters aloud."

    async def voice_listen(timeout_seconds: float = 30.0) -> str:
        try:
            result = await _service().listen_once(timeout_seconds=timeout_seconds)
        except VoiceError as exc:
            raise ToolError(exc.message, tool="voice_listen", cause=exc) from exc
        return result.text or "(no speech detected)"

    async def voice_set_backend(backend: str) -> str:
        try:
            _service().set_tts_backend(backend)
        except VoiceError as exc:
            raise ToolError(exc.message, tool="voice_set_backend", cause=exc) from exc
        return f"TTS backend switched to '{backend}'."

    app.tools.register_function(
        "voice_speak",
        "Speak the given text aloud through the speakers.",
        voice_speak,
        parameters={
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "The text to speak."},
                "emotion": {
                    "type": "string",
                    "enum": _EMOTIONS,
                    "description": "Emotional tone; applied where the TTS backend supports it.",
                },
            },
            "required": ["text"],
        },
        tags={"voice"},
    )
    app.tools.register_function(
        "voice_listen",
        "Listen on the microphone for one utterance and return the transcript.",
        voice_listen,
        parameters={
            "type": "object",
            "properties": {
                "timeout_seconds": {
                    "type": "number",
                    "minimum": 1,
                    "description": "Give up after this many seconds without speech (default 30).",
                },
            },
        },
        tags={"voice"},
        capability="voice.listen",
    )
    app.tools.register_function(
        "voice_set_backend",
        "Switch the text-to-speech backend at runtime ('none' mutes speech output).",
        voice_set_backend,
        parameters={
            "type": "object",
            "properties": {
                "backend": {
                    "type": "string",
                    "enum": _BACKENDS,
                    "description": "TTS backend to use from now on.",
                },
            },
            "required": ["backend"],
        },
        tags={"voice"},
    )
    logger.debug("Voice subsystem registered")
