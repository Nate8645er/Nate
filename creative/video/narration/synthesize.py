#!/usr/bin/env python3
"""Synthetisiert das deutsche Voiceover mit Piper (lokal, kostenlos, keine
laufenden Kosten) — pro Szene eine WAV-Datei plus eine Zeitplan-Datei mit den
ECHT GEMESSENEN Sprechdauern. TariffExplainer.tsx liest timing.json und
richtet die Sequenz-Laengen danach aus (kein Raten der Szenendauer).

Modell: .models/piper-de/de_DE-thorsten-medium.onnx (separat heruntergeladen,
nicht im Git — siehe README.md fuer den Download-Befehl).

Nutzung:
    python3 narration/synthesize.py
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import wave

HERE = pathlib.Path(__file__).resolve().parent
VIDEO_ROOT = HERE.parent
MODEL = VIDEO_ROOT / ".models" / "piper-de" / "de_DE-thorsten-medium.onnx"
OUT_DIR = HERE / "out"

# Pause zwischen dem Ende der Sprache und dem Szenenwechsel (wirkt weniger
# gehetzt als ein Hartschnitt genau auf das letzte Wort).
TAIL_PADDING_S = 0.6
# Minimale Szenendauer, auch wenn der Text kuerzer waere (visuelle Ruhe).
MIN_SCENE_S = 2.5


def synthesize_one(text: str, out_wav: pathlib.Path) -> float:
    if not MODEL.exists():
        raise FileNotFoundError(
            f"Piper-Modell fehlt: {MODEL} — siehe README.md fuer den Download-Befehl."
        )
    proc = subprocess.run(
        ["python3", "-m", "piper", "--model", str(MODEL), "--output_file", str(out_wav)],
        input=text.encode("utf-8"),
        capture_output=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"piper fehlgeschlagen: {proc.stderr.decode(errors='replace')}")
    with wave.open(str(out_wav), "rb") as w:
        return w.getnframes() / w.getframerate()


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    script = json.loads((HERE / "script_de.json").read_text(encoding="utf-8"))

    timing = []
    for scene in script["scenes"]:
        out_wav = OUT_DIR / f"{scene['id']}.wav"
        duration_s = synthesize_one(scene["text"], out_wav)
        scene_s = max(MIN_SCENE_S, duration_s + TAIL_PADDING_S)
        timing.append(
            {
                "id": scene["id"],
                "text": scene["text"],
                "speech_duration_s": round(duration_s, 3),
                "scene_duration_s": round(scene_s, 3),
                "wav": out_wav.name,
            }
        )
        print(f"{scene['id']:12s} Sprache={duration_s:5.2f}s  Szene={scene_s:5.2f}s")

    (OUT_DIR / "timing.json").write_text(
        json.dumps({"fps": 30, "scenes": timing}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\n{len(timing)} Szenen synthetisiert -> {OUT_DIR / 'timing.json'}")


if __name__ == "__main__":
    main()
