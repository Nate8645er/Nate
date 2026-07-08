"""Sprachausgabe über ElevenLabs (Cloud-Stimme, gestreamt).

Nutzt den Streaming-Endpunkt mit dem Flash-Modell (niedrigste Latenz) und
spielt die PCM-Häppchen sofort über sounddevice ab - der Satz ertönt,
während ElevenLabs noch synthetisiert. Gleiche Schnittstelle wie
TextToSpeech (speak/speak_async/wait/status), dadurch überall austauschbar.

Benötigt in config/secrets.json: "elevenlabs_api_key"
und in config.json unter speech: "elevenlabs_voice_id".
"""

import logging
import queue
import threading

import requests

from jarvis.utils.secrets import load_secret

logger = logging.getLogger("jarvis.tts")

SAMPLE_RATE = 22050  # pcm_22050: unkomprimiert, direkt abspielbar - keine Umwandlung


class ElevenLabsTTS:
    """Cloud-Sprachausgabe. Fällt sauber zurück, wenn Schlüssel/Audio fehlen."""

    def __init__(
        self,
        voice_id: str,
        model: str = "eleven_flash_v2_5",
        enabled: bool = True,
        api_key: str | None = None,
    ):
        self.enabled = enabled
        self.voice_id = voice_id
        self.model = model
        self._api_key = api_key or load_secret(
            "elevenlabs_api_key", "ELEVENLABS_API_KEY"
        )
        self._error = ""
        self._ok = bool(self._api_key and voice_id)
        if not self._ok:
            self._error = "Schlüssel oder Voice-ID fehlt"
        else:
            try:
                import sounddevice  # noqa: F401 - Abspielen der PCM-Häppchen
                logger.info("Sprachausgabe bereit: ElevenLabs (%s).", model)
            except Exception as e:
                self._ok = False
                self._error = str(e)
                logger.warning("ElevenLabs-Ausgabe nicht verfügbar: %s", e)
        self._queue: queue.Queue = queue.Queue()
        self._thread = threading.Thread(
            target=self._speaker_loop, daemon=True, name="jarvis-tts-elevenlabs"
        )
        self._thread.start()

    @property
    def available(self) -> bool:
        return self._ok

    def speak_async(self, text: str, on_start=None) -> None:
        """Reiht einen Satz zum Sprechen ein und kehrt sofort zurück."""
        if not self.enabled or not self._ok or not text.strip():
            return
        self._queue.put((text, on_start))

    def wait(self) -> None:
        """Blockiert, bis alle eingereihten Sätze gesprochen wurden."""
        self._queue.join()

    def speak(self, text: str) -> None:
        """Spricht den Text aus (blockiert, bis fertig gesprochen)."""
        self.speak_async(text)
        self.wait()

    def _speaker_loop(self) -> None:
        while True:
            text, on_start = self._queue.get()
            try:
                self._stream_and_play(text, on_start)
            except Exception as e:
                logger.error("ElevenLabs-Ausgabe fehlgeschlagen: %s", e)
            finally:
                self._queue.task_done()

    def _stream_and_play(self, text: str, on_start) -> None:
        """Holt den Satz als PCM-Stream und spielt ihn während des Ladens ab."""
        import sounddevice as sd

        with requests.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}/stream",
            params={"output_format": f"pcm_{SAMPLE_RATE}"},
            headers={"xi-api-key": self._api_key},
            json={"text": text, "model_id": self.model},
            stream=True,
            timeout=30,
        ) as response:
            response.raise_for_status()
            started = False
            leftover = b""
            with sd.RawOutputStream(
                samplerate=SAMPLE_RATE, channels=1, dtype="int16"
            ) as speaker:
                for chunk in response.iter_content(chunk_size=4096):
                    if not chunk:
                        continue
                    if not started:
                        if on_start is not None:
                            on_start()
                        started = True
                    data = leftover + chunk
                    usable = len(data) - (len(data) % 2)  # int16-Ausrichtung
                    if usable:
                        speaker.write(data[:usable])
                    leftover = data[usable:]

    def status(self) -> str:
        if not self._ok:
            return f"Sprachausgabe (ElevenLabs) nicht verfügbar ({self._error})."
        return "Sprachausgabe (ElevenLabs) ist " + ("AN" if self.enabled else "AUS")
