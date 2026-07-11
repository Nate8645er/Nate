"""Voice subsystem tests that run with core dependencies only.

None of these tests require sounddevice, faster-whisper, openwakeword or a
TTS engine: they exercise the pure-Python logic (energy detector, sentence
splitting, utterance segmentation), the NullTTS fallback and the subsystem
registration contract.
"""

from __future__ import annotations

import importlib.util
import math
import struct
import types
from typing import Any

import pytest

from jarvis.agents.tools import ToolRegistry
from jarvis.core.config import JarvisConfig, VoiceConfig
from jarvis.core.container import ServiceContainer
from jarvis.core.errors import VoiceError
from jarvis.core.events import EventBus
from jarvis.core.security import PermissionManager
from jarvis.voice import register
from jarvis.voice.audio import rms_level
from jarvis.voice.service import VoiceService
from jarvis.voice.stt import UtteranceSegmenter
from jarvis.voice.tts import NullTTS, create_tts, emotion_preset
from jarvis.voice.wake_word import EnergyKeywordDetector, create_wake_word_detector

SAMPLE_RATE = 16_000
FRAME_MS = 80
FRAME_SAMPLES = SAMPLE_RATE * FRAME_MS // 1000


def _frame(amplitude: int) -> bytes:
    """One synthetic int16 frame: an alternating wave at the given amplitude."""
    values = [amplitude, -amplitude] * (FRAME_SAMPLES // 2)
    return struct.pack(f"<{FRAME_SAMPLES}h", *values)


SILENCE = _frame(0)
SPEECH = _frame(6000)  # RMS ~= 0.18, well above every threshold used below


def _has(module: str) -> bool:
    return importlib.util.find_spec(module) is not None


# -- audio helpers -------------------------------------------------------------


def test_rms_level_of_synthetic_frames() -> None:
    assert rms_level(SILENCE) == 0.0
    assert rms_level(b"") == 0.0
    assert math.isclose(rms_level(SPEECH), 6000 / 32768.0, rel_tol=1e-6)


# -- wake word ------------------------------------------------------------------


class TestEnergyKeywordDetector:
    def test_triggers_after_consecutive_voiced_frames(self) -> None:
        detector = EnergyKeywordDetector(threshold=0.05, activation_frames=3)
        assert detector.process(SPEECH) is False
        assert detector.process(SPEECH) is False
        assert detector.process(SPEECH) is True

    def test_silence_resets_the_streak(self) -> None:
        detector = EnergyKeywordDetector(threshold=0.05, activation_frames=3)
        assert detector.process(SPEECH) is False
        assert detector.process(SPEECH) is False
        assert detector.process(SILENCE) is False
        assert detector.process(SPEECH) is False
        assert detector.process(SPEECH) is False
        assert detector.process(SPEECH) is True

    def test_reset_clears_progress(self) -> None:
        detector = EnergyKeywordDetector(threshold=0.05, activation_frames=2)
        assert detector.process(SPEECH) is False
        detector.reset()
        assert detector.process(SPEECH) is False
        assert detector.process(SPEECH) is True

    def test_always_trigger_mode(self) -> None:
        detector = EnergyKeywordDetector(always_trigger=True)
        assert detector.process(SILENCE) is True

    def test_invalid_parameters_are_rejected(self) -> None:
        with pytest.raises(VoiceError):
            EnergyKeywordDetector(threshold=0.0)
        with pytest.raises(VoiceError):
            EnergyKeywordDetector(activation_frames=0)

    def test_factory_falls_back_without_openwakeword(self) -> None:
        if _has("openwakeword"):
            pytest.skip("openwakeword is installed; fallback path not reachable")
        detector = create_wake_word_detector(VoiceConfig())
        assert isinstance(detector, EnergyKeywordDetector)


# -- sentence splitting ------------------------------------------------------------


class TestSplitSentences:
    def test_incomplete_text_stays_in_remainder(self) -> None:
        assert VoiceService.split_sentences("Hello worl") == ([], "Hello worl")

    def test_completed_sentence_is_flushed(self) -> None:
        sentences, rest = VoiceService.split_sentences("Hello world. How are")
        assert sentences == ["Hello world."]
        assert rest == "How are"

    def test_multiple_terminators(self) -> None:
        sentences, rest = VoiceService.split_sentences("One. Two! Three? Four")
        assert sentences == ["One.", "Two!", "Three?"]
        assert rest == "Four"

    def test_trailing_terminator_without_whitespace_is_kept(self) -> None:
        # "..." may still be growing while the stream is live.
        assert VoiceService.split_sentences("Wait...") == ([], "Wait...")

    def test_decimal_numbers_are_not_split(self) -> None:
        sentences, rest = VoiceService.split_sentences("Pi is 3.14 roughly. Next")
        assert sentences == ["Pi is 3.14 roughly."]
        assert rest == "Next"

    def test_closing_quotes_belong_to_the_sentence(self) -> None:
        sentences, rest = VoiceService.split_sentences('He said "Stop." Then he left')
        assert sentences == ['He said "Stop."']
        assert rest == "Then he left"

    def test_newlines_are_boundaries(self) -> None:
        sentences, rest = VoiceService.split_sentences("First line\nsecond part")
        assert sentences == ["First line"]
        assert rest == "second part"

    def test_streaming_deltas_accumulate(self) -> None:
        buffer = ""
        spoken: list[str] = []
        for delta in ["Certain", "ly, sir. Runn", "ing diagnostics", ". Stand by"]:
            buffer += delta
            sentences, buffer = VoiceService.split_sentences(buffer)
            spoken.extend(sentences)
        assert spoken == ["Certainly, sir.", "Running diagnostics."]
        assert buffer == "Stand by"


# -- TTS -----------------------------------------------------------------------------


class TestCreateTts:
    async def test_null_backend_logs_and_returns_empty_payload(self) -> None:
        tts = create_tts(VoiceConfig(tts_backend="none"))
        assert isinstance(tts, NullTTS)
        sample_rate, payload = await tts.synth("Hello there.", "happy")
        assert sample_rate == VoiceConfig().sample_rate
        assert payload == b""

    def test_auto_falls_back_to_null_without_optional_deps(self) -> None:
        if _has("TTS"):
            pytest.skip("coqui-tts is installed; auto would pick XTTS")
        # Piper is skipped even when installed because no voice model is configured.
        tts = create_tts(VoiceConfig(tts_backend="auto", tts_voice=None))
        assert isinstance(tts, NullTTS)

    def test_explicit_piper_without_voice_model_fails_clearly(self) -> None:
        with pytest.raises(VoiceError, match="tts_voice"):
            create_tts(VoiceConfig(tts_backend="piper", tts_voice=None))

    def test_emotion_presets_map_unknown_to_neutral(self) -> None:
        assert emotion_preset("angry") == emotion_preset("neutral")
        assert emotion_preset(None) == emotion_preset("neutral")
        assert emotion_preset("URGENT").speed > emotion_preset("serious").speed


# -- end-of-speech segmentation -------------------------------------------------------


class TestUtteranceSegmenter:
    def _segmenter(self, **overrides: Any) -> UtteranceSegmenter:
        defaults: dict[str, Any] = {
            "frame_ms": FRAME_MS,
            "silence_threshold": 0.05,
            "silence_ms": 700,
            "max_ms": 30_000,
        }
        defaults.update(overrides)
        return UtteranceSegmenter(**defaults)

    def test_finalises_after_trailing_silence(self) -> None:
        segmenter = self._segmenter()
        for _ in range(3):  # lead-in before any speech
            assert segmenter.feed(SILENCE) is None
        for _ in range(5):
            assert segmenter.feed(SPEECH) is None
        silence_frames_needed = math.ceil(700 / FRAME_MS)
        utterance = None
        fed = 0
        while utterance is None:
            utterance = segmenter.feed(SILENCE)
            fed += 1
            assert fed <= silence_frames_needed
        assert fed == silence_frames_needed
        # 3 lead-in + 5 speech + trailing silence frames, all same size.
        assert len(utterance) == (3 + 5 + silence_frames_needed) * len(SILENCE)
        assert SPEECH in utterance

    def test_caps_utterance_at_max_duration(self) -> None:
        segmenter = self._segmenter(max_ms=800)
        max_frames = 800 // FRAME_MS
        for i in range(max_frames - 1):
            assert segmenter.feed(SPEECH) is None, f"finalised too early at frame {i}"
        utterance = segmenter.feed(SPEECH)
        assert utterance == SPEECH * max_frames

    def test_lead_in_silence_is_bounded(self) -> None:
        segmenter = self._segmenter(max_lead_ms=160)  # keep at most 2 frames of lead-in
        for _ in range(50):
            assert segmenter.feed(SILENCE) is None
        segmenter.feed(SPEECH)
        utterance = segmenter.flush()
        assert len(utterance) <= 3 * len(SILENCE)  # bounded lead-in + 1 speech frame

    def test_flush_without_speech_returns_empty(self) -> None:
        segmenter = self._segmenter()
        segmenter.feed(SILENCE)
        assert segmenter.flush() == b""
        assert segmenter.speech_started is False

    def test_resets_for_the_next_utterance(self) -> None:
        segmenter = self._segmenter(silence_ms=FRAME_MS)  # one silent frame ends speech
        assert segmenter.feed(SPEECH) is None
        assert segmenter.feed(SILENCE) is not None
        assert segmenter.speech_started is False
        assert segmenter.feed(SPEECH) is None  # a new utterance opens cleanly


# -- register(app) ----------------------------------------------------------------------


async def _ask_stream_stub(text: str) -> Any:
    yield "Certainly, sir. "
    yield "Done."


@pytest.fixture
def app(tmp_path: Any, monkeypatch: pytest.MonkeyPatch) -> types.SimpleNamespace:
    """A stub JarvisApp with the real registry, permissions, container and bus."""
    monkeypatch.setenv("JARVIS_DATA_DIR", str(tmp_path))
    config = JarvisConfig()
    permissions = PermissionManager(config)
    stub = types.SimpleNamespace(
        config=config,
        events=EventBus(),
        permissions=permissions,
        container=ServiceContainer(),
        tools=ToolRegistry(permissions),
        router=None,
        ask_stream=_ask_stream_stub,
    )
    register(stub)
    return stub


class TestRegister:
    def test_wires_container_and_tools(self, app: types.SimpleNamespace) -> None:
        assert app.container.has(VoiceService)
        names = {tool.name for tool in app.tools.all()}
        assert {"voice_speak", "voice_listen", "voice_set_backend"} <= names
        for name in ("voice_speak", "voice_listen", "voice_set_backend"):
            assert "voice" in app.tools.get(name).tags
        assert app.tools.get("voice_listen").capability == "voice.listen"
        assert app.tools.get("voice_speak").capability is None
        service = app.container.resolve(VoiceService)
        assert service is app.container.resolve(VoiceService)  # singleton

    async def test_voice_speak_works_headless_with_null_backend(
        self, app: types.SimpleNamespace
    ) -> None:
        events: list[Any] = []
        app.events.subscribe("voice.*", events.append)
        assert "switched" in await app.tools.execute("voice_set_backend", {"backend": "none"})
        result = await app.tools.execute("voice_speak", {"text": "All systems nominal."})
        assert "Spoke" in result
        topics = [event.topic for event in events]
        assert topics.count("voice.speaking") == 2  # active True + False
        assert events[0].data == {"active": True, "text": "All systems nominal."}

    async def test_voice_set_backend_rejects_unknown_backend(
        self, app: types.SimpleNamespace
    ) -> None:
        result = await app.tools.execute("voice_set_backend", {"backend": "bogus"})
        assert result.startswith("Error:")
        assert "bogus" in result

    async def test_voice_listen_is_permission_gated(self, app: types.SimpleNamespace) -> None:
        # Default policy is "ask" and the default confirmer denies headless.
        result = await app.tools.execute("voice_listen", {})
        assert result.startswith("Permission denied")

    async def test_voice_listen_reports_missing_audio_deps(
        self, app: types.SimpleNamespace
    ) -> None:
        if _has("faster_whisper") and _has("sounddevice"):
            pytest.skip("voice extras installed; missing-dependency path not reachable")
        app.permissions.set_policy("voice.listen", "allow")
        result = await app.tools.execute("voice_listen", {})
        assert result.startswith("Error:")
        assert "jarvis-assistant[voice]" in result

    async def test_service_constructs_without_audio_hardware(
        self, app: types.SimpleNamespace
    ) -> None:
        service = app.container.resolve(VoiceService)
        service.set_tts_backend("none")
        await service.speak("Quiet mode engaged.")  # NullTTS: logs, no playback
        await service.aclose()
