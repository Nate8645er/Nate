import io
import wave

import pytest

from jarvis.voice.stt import LocalSTT, OpenAISTT, create_stt
from jarvis.voice.tts import ElevenLabsTTS, PiperTTS, create_tts, pcm_to_wav


def test_auto_prefers_elevenlabs_when_configured():
    tts = create_tts("auto", "de_DE-x", elevenlabs_api_key="key", elevenlabs_voice_id="voice")
    assert isinstance(tts, ElevenLabsTTS)
    assert tts.available
    assert tts.mime == "audio/wav"  # PCM wrapped as WAV for browser + satellite


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


def test_pcm_to_wav_roundtrip():
    pcm = b"\x00\x01" * 2205  # 0.1 s of 16-bit mono at 22050 Hz
    wav_bytes = pcm_to_wav(pcm, sample_rate=22050)
    with wave.open(io.BytesIO(wav_bytes), "rb") as wav_file:
        assert wav_file.getnchannels() == 1
        assert wav_file.getsampwidth() == 2
        assert wav_file.getframerate() == 22050
        assert wav_file.readframes(wav_file.getnframes()) == pcm


def test_stt_falls_back_to_openai_api_when_local_missing():
    # faster-whisper is not installed in CI — with an OpenAI key configured
    # the factory must return the API-based engine so voice still works.
    stt = create_stt("small", "de", openai_api_key="sk-test")
    assert isinstance(stt, OpenAISTT)
    assert stt.available


def test_stt_without_anything_reports_unavailable():
    stt = create_stt("small", "de")
    assert isinstance(stt, LocalSTT)
    assert not stt.available


async def test_unavailable_openai_stt_raises():
    stt = OpenAISTT(api_key="")
    with pytest.raises(RuntimeError):
        await stt.transcribe(b"")
