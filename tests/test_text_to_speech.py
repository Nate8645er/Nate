"""Tests für die Sprachausgabe-Warteschlange (ohne echte Audio-Hardware)."""

from jarvis.speech.text_to_speech import TextToSpeech


def test_ohne_pyttsx3_faellt_die_ausgabe_sauber_zurueck():
    tts = TextToSpeech()
    if tts.available:  # auf Maschinen mit installiertem pyttsx3 nicht sinnvoll
        return
    assert "nicht verfügbar" in tts.status()
    # Darf weder blockieren noch abstürzen
    tts.speak_async("Hallo")
    tts.wait()
    tts.speak("Hallo")


def test_leerer_text_wird_nicht_eingereiht():
    tts = TextToSpeech()
    tts.speak_async("   ")
    tts.wait()  # kehrt sofort zurück, nichts in der Warteschlange
