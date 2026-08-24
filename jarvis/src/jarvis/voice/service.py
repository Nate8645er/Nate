"""The always-on voice loop.

:class:`VoiceService` ties the voice pipeline together:

    wake word → record utterance → STT → stream answer → speak sentence-wise

It publishes progress on the event bus for the GUI ("voice.wake",
"voice.transcript", "voice.speaking", "voice.level") and supports barge-in:
when the wake word fires while the assistant is speaking (and
``voice.allow_interruption`` is enabled), playback stops and the assistant
listens again immediately.

All dependencies are injected and every audio component is created lazily,
so the service can be constructed — and partially used, e.g. with the null
TTS backend — on machines without audio hardware. Known limitation: without
echo cancellation the energy-based fallback detector may pick up the
assistant's own TTS output as a barge-in on open-speaker setups.
"""

from __future__ import annotations

import asyncio
import contextlib
import re
import time
from collections.abc import AsyncIterator, Callable
from typing import Any, cast

from jarvis.core.config import JarvisConfig
from jarvis.core.errors import VoiceError
from jarvis.core.events import EventBus
from jarvis.core.logging import get_logger
from jarvis.core.security import PermissionManager
from jarvis.voice.audio import AudioIO, rms_level
from jarvis.voice.stt import (
    FasterWhisperSTT,
    SpeechToText,
    TranscriptionResult,
    UtteranceSegmenter,
)
from jarvis.voice.tts import TTS_BACKENDS, TextToSpeech, create_tts
from jarvis.voice.wake_word import WakeWordDetector, create_wake_word_detector

logger = get_logger("voice.service")

AskStream = Callable[[str], AsyncIterator[Any]]
"""``app.ask_stream``-compatible callable: yields str deltas, then the final result."""

_LEVEL_INTERVAL_S = 0.1  # throttle for "voice.level" events (GUI visualizer)
_FRAME_POLL_S = 0.5  # how often frame waits re-check the closed flag


def _is_empty_audio(payload: Any) -> bool:
    """True for ``None`` or zero-length payloads (e.g. from :class:`NullTTS`)."""
    if payload is None:
        return True
    try:
        return len(payload) == 0
    except TypeError:
        return False


class VoiceService:
    """Always-on voice assistant loop with barge-in support.

    Constructible without audio hardware: heavy components (microphone,
    wake-word model, Whisper, TTS) are created on first use. Test doubles can
    be injected through the keyword-only constructor arguments.
    """

    _SENTENCE_END = re.compile(r"[.!?…]+[\"'”’)\]»]*\s+|\n+")

    def __init__(
        self,
        config: JarvisConfig,
        events: EventBus,
        permissions: PermissionManager,
        ask_stream: AskStream,
        *,
        audio: AudioIO | None = None,
        stt: SpeechToText | None = None,
        tts: TextToSpeech | None = None,
        wake_detector: WakeWordDetector | None = None,
    ) -> None:
        self._config = config
        self._voice = config.voice
        self._events = events
        self._permissions = permissions
        self._ask_stream = ask_stream
        self._audio = audio
        self._stt = stt
        self._tts = tts
        self._detector = wake_detector
        self._stop_playback = asyncio.Event()
        self._running = False
        self._closed = False
        self._last_level_at = 0.0

    # -- text utilities ------------------------------------------------------

    @staticmethod
    def split_sentences(buffer: str) -> tuple[list[str], str]:
        """Split completed sentences off the front of a streaming text buffer.

        A sentence is complete once its terminator (``.!?…`` plus optional
        closing quotes/brackets) is followed by whitespace, or at a newline.
        Returns ``(sentences, remainder)``; the remainder is the still-growing
        tail (flush it once the stream ends). Trailing terminators without
        following whitespace stay in the remainder because more punctuation
        may still arrive ("..." streamed one dot at a time).
        """
        sentences: list[str] = []
        start = 0
        for match in VoiceService._SENTENCE_END.finditer(buffer):
            sentence = buffer[start : match.end()].strip()
            if sentence:
                sentences.append(sentence)
            start = match.end()
        return sentences, buffer[start:]

    # -- lazy component wiring -------------------------------------------------

    def _ensure_audio(self) -> AudioIO:
        if self._audio is None:
            self._audio = AudioIO(
                sample_rate=self._voice.sample_rate,
                input_device=self._voice.input_device,
                output_device=self._voice.output_device,
            )
        return self._audio

    def _ensure_detector(self) -> WakeWordDetector:
        if self._detector is None:
            self._detector = create_wake_word_detector(self._voice)
        return self._detector

    def _ensure_stt(self) -> SpeechToText:
        if self._stt is None:
            self._stt = FasterWhisperSTT(
                model_name=self._voice.stt_model,
                device=self._voice.stt_device,
                sample_rate=self._voice.sample_rate,
            )
        return self._stt

    def _ensure_tts(self) -> TextToSpeech:
        if self._tts is None:
            self._tts = create_tts(self._voice, language=self._config.language)
        return self._tts

    # -- public API -----------------------------------------------------------

    async def speak(self, text: str, emotion: str | None = None) -> None:
        """Synthesise *text* and play it; the null backend logs instead of playing.

        Playback honours the internal stop event, so :meth:`aclose` (or a
        barge-in from the running loop) interrupts it.
        """
        text = text.strip()
        if not text:
            return
        tts = self._ensure_tts()
        sample_rate, payload = await tts.synth(text, emotion or self._voice.tts_emotion)
        await self._events.publish("voice.speaking", {"active": True, "text": text})
        try:
            if not _is_empty_audio(payload):
                self._stop_playback.clear()
                await self._ensure_audio().play(payload, sample_rate, stop=self._stop_playback)
        finally:
            await self._events.publish("voice.speaking", {"active": False, "text": text})

    async def listen_once(self, timeout_seconds: float = 30.0) -> TranscriptionResult:
        """Record a single utterance from the microphone and transcribe it.

        Returns an empty transcript when no speech was detected within
        *timeout_seconds*. Cannot be used while :meth:`run_forever` owns the
        microphone — interrupt the loop with the wake word instead.
        """
        if timeout_seconds <= 0:
            raise VoiceError(f"timeout_seconds must be positive, got {timeout_seconds}")
        if self._running:
            raise VoiceError(
                "The voice loop is already capturing; speak the wake word instead of "
                "calling voice_listen."
            )
        stt = self._ensure_stt()  # fail fast before opening the microphone
        audio = self._ensure_audio()
        queue = audio.start_capture()
        try:
            utterance = await self._record_utterance(queue, timeout_seconds=timeout_seconds)
        finally:
            audio.stop_capture()
        if not utterance:
            return TranscriptionResult(text="")
        result = await stt.transcribe(utterance, language=self._voice.stt_language)
        await self._publish_transcript(result)
        return result

    def set_tts_backend(self, backend: str) -> None:
        """Switch the TTS backend at runtime; takes effect on the next synthesis."""
        if backend not in TTS_BACKENDS:
            raise VoiceError(
                f"Unknown TTS backend '{backend}'; expected one of {sorted(TTS_BACKENDS)}."
            )
        self._voice.tts_backend = cast(Any, backend)
        self._tts = None  # rebuilt lazily with the new setting
        logger.info("TTS backend switched to '%s'", backend)

    async def run_forever(self) -> None:
        """Run the wake-word → transcribe → answer loop until :meth:`aclose`."""
        if self._running:
            raise VoiceError("The voice loop is already running.")
        if self._closed:
            raise VoiceError("This VoiceService has been closed.")
        self._running = True
        try:
            detector = self._ensure_detector()
            stt = self._ensure_stt()
            audio = self._ensure_audio()
            queue = audio.start_capture()
            logger.info("Voice loop online (wake word: '%s')", self._voice.wake_word)
            wake_pending = False
            while not self._closed:
                if not wake_pending and not await self._wait_for_wake(queue, detector):
                    break  # closed while waiting
                wake_pending = False
                utterance = await self._record_utterance(queue)
                if self._closed:
                    break
                if not utterance:
                    continue
                result = await stt.transcribe(utterance, language=self._voice.stt_language)
                text = result.text.strip()
                if not text:
                    continue
                await self._publish_transcript(result)
                wake_pending = await self._respond(text, queue, detector)
        finally:
            self._running = False
            if self._audio is not None:
                self._audio.stop_capture()
            logger.info("Voice loop stopped")

    async def aclose(self) -> None:
        """Stop the loop and playback and release the microphone."""
        self._closed = True
        self._stop_playback.set()
        if self._audio is not None:
            self._audio.stop_capture()
        await self._events.publish("voice.stopped", {})

    # -- loop internals ---------------------------------------------------------

    async def _next_frame(self, queue: asyncio.Queue[bytes]) -> bytes | None:
        """Wait for the next microphone frame; ``None`` once the service closes."""
        while not self._closed:
            try:
                return await asyncio.wait_for(queue.get(), timeout=_FRAME_POLL_S)
            except TimeoutError:
                continue
        return None

    async def _wait_for_wake(
        self, queue: asyncio.Queue[bytes], detector: WakeWordDetector
    ) -> bool:
        """Consume frames until the wake word fires; ``False`` if closed first."""
        while True:
            frame = await self._next_frame(queue)
            if frame is None:
                return False
            await self._publish_level(frame)
            if detector.process(frame):
                detector.reset()
                await self._events.publish("voice.wake", {"wake_word": self._voice.wake_word})
                return True

    async def _record_utterance(
        self, queue: asyncio.Queue[bytes], *, timeout_seconds: float = 40.0
    ) -> bytes:
        """Collect one utterance using energy-based end-of-speech segmentation."""
        audio = self._ensure_audio()
        segmenter = UtteranceSegmenter(frame_ms=audio.frame_ms)
        loop = asyncio.get_running_loop()
        deadline = loop.time() + timeout_seconds
        while not self._closed:
            remaining = deadline - loop.time()
            if remaining <= 0:
                return segmenter.flush()
            try:
                frame = await asyncio.wait_for(queue.get(), timeout=min(remaining, _FRAME_POLL_S))
            except TimeoutError:
                continue
            await self._publish_level(frame)
            utterance = segmenter.feed(frame)
            if utterance is not None:
                return utterance
        return segmenter.flush()

    async def _respond(
        self, text: str, queue: asyncio.Queue[bytes], detector: WakeWordDetector
    ) -> bool:
        """Stream the answer and speak it sentence by sentence.

        Returns ``True`` when the user barged in (the caller should then skip
        the wake word and listen immediately). Interrupting also abandons the
        rest of the answer stream — that is the intended "stop talking"
        semantics of a barge-in.
        """
        await self._events.publish("voice.speaking", {"active": True})
        interrupted = False
        buffer = ""
        try:
            async for item in self._ask_stream(text):
                if self._closed:
                    break
                if not isinstance(item, str):
                    continue  # final AgentResult marker
                buffer += item
                sentences, buffer = self.split_sentences(buffer)
                for sentence in sentences:
                    if not await self._speak_sentence(sentence, queue, detector):
                        interrupted = True
                        break
                if interrupted:
                    break
            tail = buffer.strip()
            if not interrupted and not self._closed and tail:
                interrupted = not await self._speak_sentence(tail, queue, detector)
        except VoiceError as exc:
            # TTS/audio failures must not kill the always-on loop.
            logger.error("Speech output failed: %s", exc.message)
        finally:
            await self._events.publish(
                "voice.speaking", {"active": False, "interrupted": interrupted}
            )
        return interrupted and not self._closed

    async def _speak_sentence(
        self, sentence: str, queue: asyncio.Queue[bytes], detector: WakeWordDetector
    ) -> bool:
        """Speak one sentence; returns ``False`` when interrupted by the wake word."""
        tts = self._ensure_tts()
        sample_rate, payload = await tts.synth(sentence, self._voice.tts_emotion)
        await self._events.publish("voice.speaking", {"active": True, "text": sentence})
        if _is_empty_audio(payload):
            return True
        audio = self._ensure_audio()
        self._stop_playback.clear()
        watcher: asyncio.Task[None] | None = None
        if self._voice.allow_interruption:
            watcher = asyncio.create_task(self._watch_for_barge_in(queue, detector))
        try:
            completed = await audio.play(payload, sample_rate, stop=self._stop_playback)
        finally:
            if watcher is not None:
                watcher.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await watcher
        return completed and not self._stop_playback.is_set()

    async def _watch_for_barge_in(
        self, queue: asyncio.Queue[bytes], detector: WakeWordDetector
    ) -> None:
        """Listen for the wake word during playback and stop it when heard."""
        while True:
            frame = await self._next_frame(queue)
            if frame is None:
                return
            await self._publish_level(frame)
            if detector.process(frame):
                detector.reset()
                self._stop_playback.set()
                await self._events.publish(
                    "voice.wake", {"wake_word": self._voice.wake_word, "interrupted": True}
                )
                return

    async def _publish_level(self, frame: bytes) -> None:
        """Publish the microphone RMS level, throttled for the GUI visualizer."""
        now = time.monotonic()
        if now - self._last_level_at < _LEVEL_INTERVAL_S:
            return
        self._last_level_at = now
        await self._events.publish("voice.level", {"rms": rms_level(frame)})

    async def _publish_transcript(self, result: TranscriptionResult) -> None:
        await self._events.publish(
            "voice.transcript",
            {
                "text": result.text,
                "language": result.language,
                "confidence": result.confidence,
            },
        )


__all__: list[str] = ["AskStream", "VoiceService"]
