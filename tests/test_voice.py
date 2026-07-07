import pytest

from jarvis.voice.tts import ElevenLabsTTS, PiperTTS, create_tts


def test_auto_prefers_elevenlabs_when_configured():
    tts = create_tts("auto", "de_DE-x", elevenlabs_api_key="key", elevenlabs_voice_id="voice")
    assert isinstance(tts, ElevenLabsTTS)
    assert tts.available
    assert tts.mime == "audio/mpeg"


def test_explicit_elevenlabs():
    tts = create_tts("elevenlabs", "de_DE-x", elevenlabs_api_key="key", elevenlabs_voice_id="v")
    assert isinstance(tts, ElevenLabsTTS)


def test_auto_without_keys_falls_back_to_piper():
    tts = create_tts("auto", "de_DE-x")
    assert isinstance(tts, PiperTTS)
    assert tts.mime == "audio/wav"


def test_elevenlabs_without_config_reports_unavailable():
    tts = ElevenLabsTTS(api_key="", voice_id="")
    assert not tts.available


async def test_unavailable_elevenlabs_raises():
    tts = ElevenLabsTTS(api_key="", voice_id="")
    with pytest.raises(RuntimeError):
        await tts.synthesize("hallo")
