"""Text zu Sprache: Jarvis spricht seine Antworten (Windows-Stimme, offline).

Nutzt pyttsx3, das unter Windows die eingebauten SAPI5-Stimmen verwendet -
komplett offline. Deutsche Stimme wird automatisch gewählt, wenn vorhanden
(Windows 11: Einstellungen -> Zeit und Sprache -> Sprache -> Deutsch).
"""

import logging

logger = logging.getLogger("jarvis.tts")


class TextToSpeech:
    """Sprachausgabe. Fällt sauber zurück, wenn keine Audio-Ausgabe da ist."""

    def __init__(self, rate: int = 180, language: str = "de", enabled: bool = True):
        self.enabled = enabled
        self.engine = None
        self._init_error = ""
        try:
            import pyttsx3
            self.engine = pyttsx3.init()
            self.engine.setProperty("rate", rate)
            self._pick_voice(language)
            logger.info("Sprachausgabe bereit.")
        except Exception as e:
            self._init_error = str(e)
            logger.warning("Sprachausgabe nicht verfügbar: %s", e)

    def _pick_voice(self, language: str) -> None:
        """Wählt eine Stimme in der gewünschten Sprache, falls vorhanden."""
        try:
            for voice in self.engine.getProperty("voices"):
                haystack = f"{voice.id} {voice.name}".lower()
                if language.lower() in haystack or "german" in haystack:
                    self.engine.setProperty("voice", voice.id)
                    logger.info("Stimme gewählt: %s", voice.name)
                    return
            logger.info("Keine deutsche Stimme gefunden - nutze Standardstimme.")
        except Exception as e:
            logger.warning("Stimmenwahl fehlgeschlagen: %s", e)

    @property
    def available(self) -> bool:
        return self.engine is not None

    def speak(self, text: str) -> None:
        """Spricht den Text aus (blockiert, bis fertig gesprochen)."""
        if not self.enabled or not self.available or not text.strip():
            return
        try:
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            logger.error("Sprachausgabe fehlgeschlagen: %s", e)

    def status(self) -> str:
        if not self.available:
            return f"Sprachausgabe nicht verfügbar ({self._init_error})."
        return "Sprachausgabe ist " + ("AN" if self.enabled else "AUS")
