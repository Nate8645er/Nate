"""Always-on wake-word listener ("Jarvis!") using the local microphone.

Runs only when the optional voice stack (openwakeword + sounddevice) is
installed and a microphone exists — i.e. on the user's own machine, not in
Docker. The browser dashboard has its own wake-word loop via the Web
Speech API, so this module is an enhancement, not a requirement.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Awaitable, Callable

log = logging.getLogger(__name__)


class WakeWordListener:
    def __init__(self, wake_word: str = "jarvis", threshold: float = 0.5) -> None:
        self.wake_word = wake_word
        self.threshold = threshold
        self.available = False
        self._stop = asyncio.Event()
        try:
            import numpy  # noqa: F401
            import openwakeword  # noqa: F401
            import sounddevice  # noqa: F401

            self.available = True
        except ImportError:
            log.info("Wake-word stack not installed — mic listener disabled "
                     "(browser wake word still works)")

    async def run(self, on_wake: Callable[[], Awaitable[None]]) -> None:
        """Listen forever; call on_wake() each time the wake word fires."""
        if not self.available:
            return
        import numpy as np
        import sounddevice as sd
        from openwakeword.model import Model

        model = Model(wakeword_models=["hey_jarvis"], inference_framework="onnx")
        queue: asyncio.Queue[bytes] = asyncio.Queue(maxsize=8)
        loop = asyncio.get_running_loop()

        def callback(indata, frames, time_info, status) -> None:  # noqa: ANN001
            with_data = bytes(indata)
            try:
                loop.call_soon_threadsafe(queue.put_nowait, with_data)
            except RuntimeError:
                pass

        with sd.RawInputStream(
            samplerate=16000, blocksize=1280, dtype="int16", channels=1, callback=callback
        ):
            log.info("Wake-word listener active (say '%s')", self.wake_word)
            while not self._stop.is_set():
                chunk = await queue.get()
                audio = np.frombuffer(chunk, dtype=np.int16)
                prediction = model.predict(audio)
                if max(prediction.values(), default=0.0) >= self.threshold:
                    model.reset()
                    await on_wake()

    def stop(self) -> None:
        self._stop.set()
