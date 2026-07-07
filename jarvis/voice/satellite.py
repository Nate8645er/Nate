"""JARVIS voice satellite — system-wide, hands-free voice, no browser needed.

Runs as a background process on the user's machine (`jarvis-voice`),
connected to the JARVIS server:

    mic → wake word ("Jarvis") → record until silence → server STT
        → orchestrator/agents → answer arrives as voice.speak → speakers

Conversation mode: after JARVIS answers, you can keep talking for a
follow-up window (default 45 s) without repeating the wake word — like
talking to a colleague. The mic is muted while JARVIS speaks so he does
not hear himself.

Requirements on the host machine (NOT needed for the browser mode):
    pip install "jarvis-ai-os[voice]"   # sounddevice, numpy, openwakeword
Speech-to-text happens on the server (faster-whisper locally, or the
OpenAI Whisper API when a key is configured), so no local STT model is
required here.
"""

from __future__ import annotations

import asyncio
import io
import json
import logging
import time
import wave

import httpx

from jarvis.config import settings

log = logging.getLogger(__name__)

SAMPLE_RATE = 16000
BLOCK = 1280  # 80 ms at 16 kHz
SILENCE_SECONDS = 1.1  # end of utterance after this much quiet
MAX_UTTERANCE_SECONDS = 15
FOLLOWUP_SECONDS = 45  # conversation window after an answer
ENERGY_THRESHOLD = 300  # int16 RMS; tune via JARVIS mic sensitivity if needed


def _pcm_chunks_to_wav(chunks: list[bytes]) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(SAMPLE_RATE)
        wav_file.writeframes(b"".join(chunks))
    return buf.getvalue()


class Satellite:
    def __init__(self, server: str | None = None) -> None:
        self.server = (server or f"http://{settings.host}:{settings.port}").rstrip("/")
        self.ws_url = self.server.replace("http", "ws", 1) + "/ws"
        self.speaking = asyncio.Event()  # set while audio is playing
        self.conversation_until = 0.0

    # ------------------------------------------------------------- playback
    async def play_wav(self, wav_bytes: bytes) -> None:
        import numpy as np
        import sounddevice as sd

        with wave.open(io.BytesIO(wav_bytes), "rb") as wav_file:
            rate = wav_file.getframerate()
            frames = wav_file.readframes(wav_file.getnframes())
        audio = np.frombuffer(frames, dtype=np.int16)
        self.speaking.set()
        try:
            sd.play(audio, rate)
            await asyncio.to_thread(sd.wait)
        finally:
            self.speaking.clear()
            self.conversation_until = time.time() + FOLLOWUP_SECONDS

    # ------------------------------------------------------- server events
    async def listen_server(self) -> None:
        """Receive voice.speak events and play them through the speakers."""
        import websockets  # bundled with the [voice] extra via uvicorn/standard

        while True:
            try:
                async with websockets.connect(self.ws_url) as ws:
                    log.info("Verbunden mit %s", self.ws_url)
                    async for raw in ws:
                        msg = json.loads(raw)
                        if msg.get("topic") == "voice.speak":
                            audio_b64 = msg.get("data", {}).get("audio_b64")
                            if audio_b64:
                                import base64

                                await self.play_wav(base64.b64decode(audio_b64))
            except Exception as exc:  # noqa: BLE001 - reconnect forever
                log.warning("Server-Verbindung verloren (%s) — neuer Versuch in 3 s", exc)
                await asyncio.sleep(3)

    # ------------------------------------------------------------ mic loop
    async def run_mic(self) -> None:
        import numpy as np
        import sounddevice as sd
        from openwakeword.model import Model

        model = Model(wakeword_models=["hey_jarvis"], inference_framework="onnx")
        queue: asyncio.Queue[bytes] = asyncio.Queue(maxsize=32)
        loop = asyncio.get_running_loop()

        def callback(indata, frames, time_info, status) -> None:  # noqa: ANN001
            try:
                loop.call_soon_threadsafe(queue.put_nowait, bytes(indata))
            except RuntimeError:
                pass

        recording: list[bytes] | None = None
        quiet_since: float | None = None
        record_started = 0.0

        with sd.RawInputStream(
            samplerate=SAMPLE_RATE, blocksize=BLOCK, dtype="int16", channels=1,
            callback=callback,
        ):
            log.info("Höre zu — sag '%s' …", settings.wake_word)
            while True:
                chunk = await queue.get()
                if self.speaking.is_set():
                    continue  # never listen to our own voice
                audio = np.frombuffer(chunk, dtype=np.int16)
                rms = float(np.sqrt(np.mean(audio.astype(np.float32) ** 2)))

                if recording is not None:
                    recording.append(chunk)
                    now = time.time()
                    if rms < ENERGY_THRESHOLD:
                        quiet_since = quiet_since or now
                        if now - quiet_since >= SILENCE_SECONDS:
                            await self._finish_utterance(recording)
                            recording, quiet_since = None, None
                    else:
                        quiet_since = None
                    if now - record_started > MAX_UTTERANCE_SECONDS:
                        await self._finish_utterance(recording)
                        recording, quiet_since = None, None
                    continue

                in_conversation = time.time() < self.conversation_until
                woke = False
                if not in_conversation:
                    prediction = model.predict(audio)
                    woke = max(prediction.values(), default=0.0) >= 0.5
                    if woke:
                        model.reset()
                        log.info("Wake Word erkannt")
                if woke or (in_conversation and rms >= ENERGY_THRESHOLD):
                    recording = [chunk]
                    quiet_since = None
                    record_started = time.time()

    async def _finish_utterance(self, chunks: list[bytes]) -> None:
        wav_bytes = _pcm_chunks_to_wav(chunks)
        if len(wav_bytes) < SAMPLE_RATE // 2:  # < 0.25 s — noise, not speech
            return
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(
                    f"{self.server}/api/voice/transcribe",
                    files={"file": ("speech.wav", wav_bytes, "audio/wav")},
                )
                resp.raise_for_status()
                text = resp.json().get("text", "")
            if text:
                log.info("Du: %s", text)
                self.conversation_until = time.time() + FOLLOWUP_SECONDS
        except httpx.HTTPStatusError as exc:
            log.error("Server-STT fehlgeschlagen: %s — %s", exc, exc.response.text[:200])
        except httpx.HTTPError as exc:
            log.error("Server nicht erreichbar: %s", exc)

    async def run(self) -> None:
        await asyncio.gather(self.listen_server(), self.run_mic())


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-7s %(message)s")
    try:
        import numpy  # noqa: F401
        import openwakeword  # noqa: F401
        import sounddevice  # noqa: F401
        import websockets  # noqa: F401
    except ImportError as exc:
        raise SystemExit(
            f"Fehlende Abhängigkeit: {exc.name}. "
            "Installiere den Voice-Stack mit: pip install 'jarvis-ai-os[voice]'"
        ) from exc
    print(
        "\n  J.A.R.V.I.S. Voice-Satellit\n"
        f"  Server: http://{settings.host}:{settings.port}\n"
        f"  Sag '{settings.wake_word}' und sprich einfach — "
        "Folgefragen brauchen kein Wake Word.\n"
    )
    asyncio.run(Satellite().run())


if __name__ == "__main__":
    main()
