#!/usr/bin/env python3
"""Erzeugt Untertitel (SRT + WebVTT) deterministisch aus narration/out/timing.json.

Bewusst KEINE Spracherkennung (whisper) noetig: die Szenenzeiten sind bereits
exakt bekannt (dieselbe Quelle, die auch das Video-Timing in
TariffExplainer.tsx steuert) — Untertitel und Video koennen also nie
auseinanderlaufen.
"""
from __future__ import annotations

import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
OUT_DIR = HERE / "out"


def fmt_srt(t: float) -> str:
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    ms = round((s - int(s)) * 1000)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{ms:03d}"


def fmt_vtt(t: float) -> str:
    return fmt_srt(t).replace(",", ".")


def main() -> None:
    timing = json.loads((OUT_DIR / "timing.json").read_text(encoding="utf-8"))

    cursor = 0.0
    srt_lines = []
    vtt_lines = ["WEBVTT", ""]
    for i, scene in enumerate(timing["scenes"], start=1):
        start = cursor
        end = cursor + scene["scene_duration_s"]
        srt_lines += [str(i), f"{fmt_srt(start)} --> {fmt_srt(end)}", scene["text"], ""]
        vtt_lines += [f"{fmt_vtt(start)} --> {fmt_vtt(end)}", scene["text"], ""]
        cursor = end

    (OUT_DIR / "subtitles_de.srt").write_text("\n".join(srt_lines), encoding="utf-8")
    (OUT_DIR / "subtitles_de.vtt").write_text("\n".join(vtt_lines), encoding="utf-8")
    print(f"Untertitel geschrieben: {OUT_DIR / 'subtitles_de.srt'} (+ .vtt), Gesamtlaenge {cursor:.1f}s")


if __name__ == "__main__":
    main()
