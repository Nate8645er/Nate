"""Text zu Sprache: Jarvis spricht seine Antworten (Windows-Stimme, offline).

Nutzt pyttsx3, das unter Windows die eingebauten SAPI5-Stimmen verwendet -
komplett offline. Deutsche Stimme wird automatisch gewählt, wenn vorhanden
(Windows 11: Einstellungen -> Zeit und Sprache -> Sprache -> Deutsch).

Die Ausgabe läuft in einem eigenen Sprech-Thread mit Warteschlange:
speak_async() reiht einen Satz ein und kehrt sofort zurück, sodass die
nächsten Sätze schon vom Modell gestreamt werden können, während Jarvis
den ersten spricht. speak() bleibt wie bisher blockierend.
"""

import logging
import queue
import threading

logger = logging.getLogger("jarvis.tts")


class TextToSpeech:
    """Sprachausgabe. Fällt sauber zurück, wenn keine Audio-Ausgabe da ist."""

    def __init__(self, rate: int = 180, language: str = "de", enabled: bool = True):
        self.enabled = enabled
        self.engine = None
        self._init_error = ""
        self._queue: queue.Queue = queue.Queue()
        self._ready = threading.Event()
        # Der Sprech-Thread besitzt die pyttsx3-Engine exklusiv (SAPI5/COM
        # mag keine Thread-Wechsel) und arbeitet die Warteschlange ab.
        self._thread = threading.Thread(
            target=self._speaker_loop, args=(rate, language),
            daemon=True, name="jarvis-tts",
        )
        self._thread.start()
        self._ready.wait(timeout=10)

    def _speaker_loop(self, rate: int, language: str) -> None:
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.setProperty("rate", rate)
            self._pick_voice(engine, language)
            self.engine = engine
            logger.info("Sprachausgabe bereit.")
        except Exception as e:
            self._init_error = str(e)
            logger.warning("Sprachausgabe nicht verfügbar: %s", e)
            self._ready.set()
            return

        self._ready.set()
        while True:
            text, on_start = self._queue.get()
            try:
                if on_start is not None:
                    on_start()
                engine.say(text)
                engine.runAndWait()
            except Exception as e:
                logger.error("Sprachausgabe fehlgeschlagen: %s", e)
            finally:
                self._queue.task_done()

    def _pick_voice(self, engine, language: str) -> None:
        """Wählt eine Stimme in der gewünschten Sprache, falls vorhanden."""
        try:
            for voice in engine.getProperty("voices"):
                haystack = f"{voice.id} {voice.name}".lower()
                if language.lower() in haystack or "german" in haystack:
                    engine.setProperty("voice", voice.id)
                    logger.info("Stimme gewählt: %s", voice.name)
                    return
            logger.info("Keine deutsche Stimme gefunden - nutze Standardstimme.")
        except Exception as e:
            logger.warning("Stimmenwahl fehlgeschlagen: %s", e)

    @property
    def available(self) -> bool:
        return self.engine is not None

    def speak_async(self, text: str, on_start=None) -> None:
        """Reiht einen Satz zum Sprechen ein und kehrt sofort zurück.

        `on_start` wird (im Sprech-Thread) aufgerufen, kurz bevor der Satz
        tatsächlich ertönt - praktisch für Latenz-Messungen.
        """
        if not self.enabled or not self.available or not text.strip():
            return
        self._queue.put((text, on_start))

    def wait(self) -> None:
        """Blockiert, bis alle eingereihten Sätze gesprochen wurden."""
        self._queue.join()

    def speak(self, text: str) -> None:
        """Spricht den Text aus (blockiert, bis fertig gesprochen)."""
        self.speak_async(text)
        self.wait()

    def status(self) -> str:
        if not self.available:
            return f"Sprachausgabe nicht verfügbar ({self._init_error})."
        return "Sprachausgabe ist " + ("AN" if self.enabled else "AUS")
