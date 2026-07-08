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

    # ------------------------------------------------------------------
    # Aufnahme (Start/Stopp getrennt, damit Konsole UND GUI sie nutzen können)
    # ------------------------------------------------------------------

    def record_start(self) -> None:
        """Startet die Mikrofon-Aufnahme."""
        import sounddevice as sd

        self._frames: list[bytes] = []

        def callback(indata, frame_count, time_info, status):
            self._frames.append(bytes(indata))

        self._stream = sd.RawInputStream(
            samplerate=SAMPLE_RATE, channels=1, dtype="int16", callback=callback
        )
        self._stream.start()

    def record_stop(self) -> bytes:
        """Stoppt die Aufnahme und gibt die Audiodaten zurück."""
        self._stream.stop()
        self._stream.close()
        return b"".join(self._frames)

    def transcribe(self, raw: bytes) -> tuple[str | None, str]:
        """Wandelt Audiodaten in Text um. Ergebnis: (text, meldung)."""
        import speech_recognition as sr

        if len(raw) < SAMPLE_RATE * SAMPLE_WIDTH // 2:  # unter ~0,5 Sekunden
            return None, "Die Aufnahme war zu kurz."

        audio = sr.AudioData(raw, SAMPLE_RATE, SAMPLE_WIDTH)
        recognizer = sr.Recognizer()
        try:
            text = recognizer.recognize_google(audio, language=self.language)
            logger.info("Verstanden: %s", text)
            return text, ""
        except sr.UnknownValueError:
            return None, "Ich habe dich leider nicht verstanden - versuch es nochmal."
        except sr.RequestError as e:
            logger.error("Spracherkennung nicht erreichbar: %s", e)
            return None, "Die Spracherkennung braucht eine Internetverbindung."

    def listen(self, timer=None) -> str | None:
        """Konsolen-Modus: Aufnahme per Enter starten/stoppen.

        `timer` (TurnTimer, optional) startet beim Ende der Aufnahme und
        bekommt eine Marke, sobald das Transkript fertig ist - so sieht man,
        wie viel der Wartezeit auf die Spracherkennung entfällt.
        """
        if not self._ok:
            print(f"(Spracheingabe nicht verfügbar: {self._error})")
            return None
        try:
            self.record_start()
            print("🎤 Ich höre zu ... (Enter drücken, wenn du fertig gesprochen hast)")
            input()
            raw = self.record_stop()
        except Exception as e:
            logger.error("Aufnahme fehlgeschlagen: %s", e)
            print(f"(Mikrofon-Problem: {e})")
            return None

        if timer is not None:
            timer.start()  # Nullpunkt: der Nutzer ist fertig mit Sprechen
        text, message = self.transcribe(raw)
        if timer is not None:
            timer.mark("Transkript")
        if message:
            print(f"({message})")
        return text
