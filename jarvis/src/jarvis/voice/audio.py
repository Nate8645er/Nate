"""Audio input/output over sounddevice.

:class:`AudioIO` provides asyncio-friendly microphone capture (fixed-size
16 kHz mono int16 frames delivered through an :class:`asyncio.Queue`) and
speaker playback that can be interrupted through an :class:`asyncio.Event`
(barge-in support). ``sounddevice`` is imported lazily inside the methods so
this module can always be imported, even without the optional voice extras.
"""

from __future__ import annotations

import array
import asyncio
import contextlib
import math
from typing import Any

from jarvis.core.errors import VoiceError
from jarvis.core.logging import get_logger

logger = get_logger("voice.audio")

_INSTALL_HINT = (
    "Install the voice extras with `pip install 'jarvis-assistant[voice]'` "
    "(sounddevice also needs the PortAudio system library, "
    "e.g. `apt install libportaudio2`)."
)


def _sounddevice() -> Any:
    """Import and return the sounddevice module, or raise a helpful VoiceError."""
    try:
        import sounddevice
    except ImportError as exc:
        raise VoiceError(
            f"Audio I/O is unavailable because sounddevice is not installed. {_INSTALL_HINT}",
            cause=exc,
        ) from exc
    return sounddevice


def rms_level(frame: bytes | bytearray | memoryview) -> float:
    """Return the RMS level of a 16-bit PCM frame, normalised to ``[0.0, 1.0]``.

    Uses numpy when available and falls back to a pure-Python implementation
    otherwise, so it works with core dependencies only.
    """
    data = bytes(frame)
    usable = len(data) - (len(data) % 2)
    if usable == 0:
        return 0.0
    try:
        import numpy as np
    except ImportError:
        samples = array.array("h")
        samples.frombytes(data[:usable])
        mean_square = sum(s * s for s in samples) / len(samples)
        return min(1.0, math.sqrt(mean_square) / 32768.0)
    values = np.frombuffer(data[:usable], dtype=np.int16).astype(np.float64)
    return min(1.0, float(np.sqrt(np.mean(np.square(values)))) / 32768.0)


def pcm_int16_bytes(audio: Any) -> bytes:
    """Normalise an audio payload (int16 bytes or a numpy array) to int16 PCM bytes.

    Float arrays are assumed to be in ``[-1.0, 1.0]`` and are clipped and
    scaled; integer arrays are cast to int16. Multi-dimensional arrays are
    flattened (mono is assumed throughout the voice pipeline).
    """
    if isinstance(audio, (bytes, bytearray, memoryview)):
        return bytes(audio)
    if not hasattr(audio, "dtype"):
        raise VoiceError(
            f"Unsupported audio payload of type {type(audio).__name__}; "
            "expected int16 PCM bytes or a numpy array."
        )
    import numpy as np  # payload is already a numpy array, so numpy is present

    values = np.asarray(audio)
    if values.ndim > 1:
        values = values.reshape(-1)
    if np.issubdtype(values.dtype, np.floating):
        values = (np.clip(values, -1.0, 1.0) * 32767.0).astype(np.int16)
    elif values.dtype != np.int16:
        values = values.astype(np.int16)
    return values.tobytes()


class AudioIO:
    """Asyncio-friendly microphone capture and interruptible speaker playback.

    The constructor is dependency-free; ``sounddevice`` is only imported when
    a stream is actually opened, so instances can be created on machines
    without audio hardware or the optional extras.
    """

    def __init__(
        self,
        sample_rate: int = 16_000,
        frame_ms: int = 80,
        input_device: int | None = None,
        output_device: int | None = None,
        queue_maxsize: int = 256,
    ) -> None:
        if sample_rate <= 0:
            raise VoiceError(f"sample_rate must be positive, got {sample_rate}")
        if frame_ms <= 0:
            raise VoiceError(f"frame_ms must be positive, got {frame_ms}")
        self.sample_rate = sample_rate
        self.frame_ms = frame_ms
        self.frames_per_block = sample_rate * frame_ms // 1000
        self.input_device = input_device
        self.output_device = output_device
        self._queue_maxsize = queue_maxsize
        self._stream: Any | None = None
        self._queue: asyncio.Queue[bytes] | None = None

    @property
    def capturing(self) -> bool:
        """Whether the microphone stream is currently open."""
        return self._stream is not None

    def start_capture(self) -> asyncio.Queue[bytes]:
        """Open the microphone and return a queue of int16 PCM frames.

        Each queue item is one block of ``frame_ms`` milliseconds of mono
        16-bit audio. When the queue is full the oldest frame is dropped so a
        slow consumer never blocks the audio callback. Idempotent: calling
        again while capturing returns the existing queue.
        """
        if self._stream is not None and self._queue is not None:
            return self._queue
        sd = _sounddevice()
        loop = asyncio.get_running_loop()
        queue: asyncio.Queue[bytes] = asyncio.Queue(maxsize=self._queue_maxsize)

        def _enqueue(data: bytes) -> None:
            if queue.full():
                with contextlib.suppress(asyncio.QueueEmpty):
                    queue.get_nowait()  # drop the oldest frame
            with contextlib.suppress(asyncio.QueueFull):
                queue.put_nowait(data)

        def _callback(indata: Any, frames: int, time_info: Any, status: Any) -> None:
            if status:
                logger.debug("Microphone stream status: %s", status)
            # Called from PortAudio's thread; hand the copied frame to the loop.
            loop.call_soon_threadsafe(_enqueue, bytes(indata))

        try:
            stream = sd.RawInputStream(
                samplerate=self.sample_rate,
                blocksize=self.frames_per_block,
                device=self.input_device,
                channels=1,
                dtype="int16",
                callback=_callback,
            )
            stream.start()
        except VoiceError:
            raise
        except Exception as exc:
            raise VoiceError(f"Could not open the microphone: {exc}", cause=exc) from exc
        self._stream = stream
        self._queue = queue
        return queue

    def stop_capture(self) -> None:
        """Close the microphone stream; safe to call when not capturing."""
        stream, self._stream = self._stream, None
        self._queue = None
        if stream is not None:
            with contextlib.suppress(Exception):
                stream.stop()
                stream.close()

    async def play(
        self,
        audio: Any,
        sample_rate: int,
        *,
        stop: asyncio.Event | None = None,
    ) -> bool:
        """Play int16 PCM bytes (or a numpy array) through the speakers.

        Playback runs in a worker thread and is written in ~100 ms chunks so
        that setting *stop* interrupts it promptly (barge-in). Returns ``True``
        when playback completed and ``False`` when it was interrupted.
        """
        if sample_rate <= 0:
            raise VoiceError(f"sample_rate must be positive, got {sample_rate}")
        pcm = pcm_int16_bytes(audio)
        if not pcm:
            return True
        sd = _sounddevice()
        chunk_bytes = max(2, (sample_rate // 10) * 2)  # ~100 ms of int16 samples

        def _run() -> bool:
            try:
                with sd.RawOutputStream(
                    samplerate=sample_rate,
                    channels=1,
                    dtype="int16",
                    device=self.output_device,
                ) as out:
                    for offset in range(0, len(pcm), chunk_bytes):
                        if stop is not None and stop.is_set():
                            return False
                        out.write(pcm[offset : offset + chunk_bytes])
            except Exception as exc:
                raise VoiceError(f"Audio playback failed: {exc}", cause=exc) from exc
            return True

        return await asyncio.to_thread(_run)
