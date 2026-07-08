"""Sprache zu Text: Jarvis hört über das Mikrofon zu.

Aufnahme per Push-to-Talk: Enter startet die Aufnahme, Enter stoppt sie.
Die Aufnahme läuft über sounddevice (funktioniert auch mit Python 3.13/3.14,
im Gegensatz zu PyAudio). Erkannt wird die Sprache über die kostenlose
Google-Web-Speech-Schnittstelle (benötigt Internet). Später kann hier ohne
Änderung am Rest von Jarvis eine Offline-Erkennung (Vosk/Whisper) rein.
"""

import logging

logger = logging.getLogger("jarvis.stt")

SAMPLE_RATE = 16000  # 16 kHz Mono ist der Standard für Spracherkennung
SAMPLE_WIDTH = 2     # int16 = 2 Bytes pro Sample


class SpeechToText:
    """Mikrofon-Aufnahme (Push-to-Talk) plus Spracherkennung."""

    def __init__(self, language: str = "de-DE"):
        self.language = language
        self._error = ""
        try:
            import sounddevice  # noqa: F401 - Verfügbarkeit prüfen
            import speech_recognition  # noqa: F401
            self._ok = True
        except Exception as e:
            self._ok = False
            self._error = str(e)
            logger.warning("Spracheingabe nicht verfügbar: %s", e)

    @property
    def available(self) -> bool:
        return self._ok

    def status(self) -> str:
        if not self._ok:
            return f"Spracheingabe nicht verfügbar ({self._error})."
        return "Spracheingabe ist bereit."

    def _record(self) -> bytes:
        """Nimmt Audio auf, bis der Nutzer Enter drückt."""
        import sounddevice as sd

        frames: list[bytes] = []

        def callback(indata, frame_count, time_info, status):
            frames.append(bytes(indata))

        print("🎤 Ich höre zu ... (Enter drücken, wenn du fertig gesprochen hast)")
        with sd.RawInputStream(
            samplerate=SAMPLE_RATE, channels=1, dtype="int16", callback=callback
        ):
            input()
        return b"".join(frames)

    def listen(self) -> str | None:
        """Nimmt auf und gibt den erkannten Text zurück (None bei Fehler)."""
        if not self._ok:
            print(f"(Spracheingabe nicht verfügbar: {self._error})")
            return None

        import speech_recognition as sr

        try:
            raw = self._record()
        except Exception as e:
            logger.error("Aufnahme fehlgeschlagen: %s", e)
            print(f"(Mikrofon-Problem: {e})")
            return None

        if len(raw) < SAMPLE_RATE * SAMPLE_WIDTH // 2:  # unter ~0,5 Sekunden
            print("(Die Aufnahme war zu kurz.)")
            return None

        audio = sr.AudioData(raw, SAMPLE_RATE, SAMPLE_WIDTH)
        recognizer = sr.Recognizer()
        try:
            text = recognizer.recognize_google(audio, language=self.language)
            logger.info("Verstanden: %s", text)
            return text
        except sr.UnknownValueError:
            print("(Ich habe dich leider nicht verstanden - versuch es nochmal.)")
            return None
        except sr.RequestError as e:
            logger.error("Spracherkennung nicht erreichbar: %s", e)
            print("(Die Spracherkennung braucht eine Internetverbindung.)")
            return None
