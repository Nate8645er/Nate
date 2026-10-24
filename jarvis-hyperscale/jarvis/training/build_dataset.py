"""Datensatz-Builder (Agent 3 — ML/Training).

Exportiert JARVIS' ECHTE Interaktionsdaten in ein Chat-JSONL, das direkt für
Fine-Tuning taugt (OpenAI-/Anthropic-Format: eine Zeile pro Beispiel mit
`messages`). Quellen:
  1. Gedächtnis-DB (memory.db): (Aufgabe -> Ergebnis) je Mitarbeiter.
  2. Autopilot-Ideen (ideen.jsonl): (Ideen-Prompt -> erzeugte Idee).

Jeder Text wird PII-bereinigt (training/scrub.py). Offline-Platzhalter,
Fehlerausgaben und leere/zu kurze Paare werden ausgelassen — es kommen nur
echte, brauchbare Beispiele in den Datensatz. Nichts wird erfunden.

Aufruf:
    python -m jarvis.training.build_dataset --data <JARVIS_DATA> --out dataset.jsonl
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

from .scrub import scrub

# Autopilot-Systemprompt als „user"-Seite der Ideen-Beispiele (gekürzt gespiegelt).
IDEA_USER = "Erfinde eine konkrete, umsetzbare Online-Business-Idee für eine Einzelperson."

# Ergebnisse, die keine echte Modellantwort sind, werden verworfen.
_SKIP_MARKERS = ("[OFFLINE-Modus", "[API-Fehler", "[API nicht erreichbar",
                 "[Claude-Code-Binary", "[kein API-Key", "[Fehler bei",
                 "[OpenRouter", "IndexError", "ValueError:")


def _usable(prompt: str, completion: str, min_len: int = 12) -> bool:
    if not prompt or not completion:
        return False
    if len(completion.strip()) < min_len:
        return False
    return not any(m in completion for m in _SKIP_MARKERS)


def from_memory(db_path: Path) -> list[dict]:
    out: list[dict] = []
    if not db_path.exists():
        return out
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute("SELECT task, result FROM memory").fetchall()
    except sqlite3.Error:
        return out
    finally:
        conn.close()
    for task, result in rows:
        if _usable(task, result):
            out.append({"messages": [
                {"role": "user", "content": scrub(task.strip())},
                {"role": "assistant", "content": scrub(result.strip())}]})
    return out


def from_ideas(ideas_path: Path) -> list[dict]:
    out: list[dict] = []
    if not ideas_path.exists():
        return out
    for line in ideas_path.open(encoding="utf-8"):
        try:
            e = json.loads(line)
        except Exception:
            continue
        text = (e.get("text") or "").strip()
        if _usable(IDEA_USER, text):
            out.append({"messages": [
                {"role": "user", "content": IDEA_USER},
                {"role": "assistant", "content": scrub(text)}]})
    return out


def build(data_dir: Path) -> list[dict]:
    return from_memory(data_dir / "memory.db") + from_ideas(data_dir / "ideen.jsonl")


def write_jsonl(examples: list[dict], out_path: Path) -> int:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        for ex in examples:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")
    return len(examples)


def main() -> None:
    ap = argparse.ArgumentParser(description="JARVIS-Trainingsdatensatz bauen")
    ap.add_argument("--data", default="jarvis_daten", help="JARVIS_DATA-Verzeichnis")
    ap.add_argument("--out", default="dataset.jsonl", help="Ausgabedatei (JSONL)")
    args = ap.parse_args()
    examples = build(Path(args.data))
    n = write_jsonl(examples, Path(args.out))
    print(f"{n} Beispiele geschrieben -> {args.out}")
    if n == 0:
        print("Hinweis: keine brauchbaren Beispiele gefunden. JARVIS muss erst mit "
              "echtem API-Key laufen und Aufgaben/Ideen erzeugen, damit Daten entstehen.")


if __name__ == "__main__":
    main()
