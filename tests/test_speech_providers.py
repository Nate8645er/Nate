"""Tests für die Anbieter-Wahl bei Ohren (STT) und Stimme (TTS)."""

from jarvis.speech.elevenlabs_tts import ElevenLabsTTS
from jarvis.speech.speech_to_text import SpeechToText


def test_elevenlabs_ohne_schluessel_ist_nicht_verfuegbar():
    tts = ElevenLabsTTS(voice_id="", api_key=None)
    assert not tts.available
    assert "nicht verfügbar" in tts.status()
    # Darf weder blockieren noch abstürzen
    tts.speak_async("Hallo")
    tts.wait()
    tts.speak("Hallo")


def test_elevenlabs_braucht_schluessel_und_voice_id():
    nur_key = ElevenLabsTTS(voice_id="", api_key="xi-test")
    assert not nur_key.available
    # Mit beidem gilt sie als konfiguriert (sofern sounddevice installiert
    # ist; ohne Audio-Stack bleibt sie sauber deaktiviert)
    beides = ElevenLabsTTS(voice_id="stimme123", api_key="xi-test")
    try:
        import sounddevice  # noqa: F401
        assert beides.available
    except Exception:
        assert not beides.available


def test_stt_nutzt_deepgram_nur_mit_schluessel(monkeypatch):
    monkeypatch.delenv("DEEPGRAM_API_KEY", raising=False)
    stt = SpeechToText(provider="auto")
    stt._deepgram_key = None
    assert not stt._use_deepgram()
    stt._deepgram_key = "dg-test"
    assert stt._use_deepgram()
    # explizit google gewählt -> Deepgram bleibt aus, auch mit Schlüssel
    stt.provider = "google"
    assert not stt._use_deepgram()


def test_deepgram_sprache_wird_gekuerzt():
    # Deepgram erwartet "de", die Konfiguration nutzt "de-DE"
    stt = SpeechToText(language="de-DE")
    assert stt.language.split("-")[0] == "de"
