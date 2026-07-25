"""Tests der SRT/VTT-Zeitformatierung — reine Funktionen, kein Audio/Video noetig."""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from generate_srt import fmt_srt, fmt_vtt  # noqa: E402


def test_fmt_srt_zero():
    assert fmt_srt(0.0) == "00:00:00,000"


def test_fmt_srt_seconds_and_millis():
    assert fmt_srt(5.337) == "00:00:05,337"


def test_fmt_srt_minutes():
    assert fmt_srt(65.5) == "00:01:05,500"


def test_fmt_srt_hours():
    assert fmt_srt(3661.25) == "01:01:01,250"


def test_fmt_vtt_uses_dot_not_comma():
    assert fmt_vtt(5.337) == "00:00:05.337"
    assert "," not in fmt_vtt(5.337)


def test_timing_json_produces_monotonic_non_overlapping_subtitles(tmp_path):
    import json
    from generate_srt import main
    import generate_srt

    out_dir = tmp_path
    (out_dir / "timing.json").write_text(json.dumps({
        "fps": 30,
        "scenes": [
            {"id": "a", "text": "Eins", "speech_duration_s": 1.0, "scene_duration_s": 2.0, "wav": "a.wav"},
            {"id": "b", "text": "Zwei", "speech_duration_s": 1.5, "scene_duration_s": 2.5, "wav": "b.wav"},
        ],
    }), encoding="utf-8")

    orig_out_dir = generate_srt.OUT_DIR
    generate_srt.OUT_DIR = out_dir
    try:
        main()
        srt = (out_dir / "subtitles_de.srt").read_text(encoding="utf-8")
    finally:
        generate_srt.OUT_DIR = orig_out_dir

    assert "00:00:00,000 --> 00:00:02,000" in srt
    assert "00:00:02,000 --> 00:00:04,500" in srt  # zweite Zeile beginnt exakt wo die erste endet
    assert "Eins" in srt and "Zwei" in srt
