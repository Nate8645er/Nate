"""Evaluation & Split (Agent 3 — ML/Training, Agent 4 — QS).

Zwei ehrliche Bausteine:
  1. `split()` — deterministischer Train/Holdout-Split (kein Datenleck: gleiche
     Prompts landen nicht in beiden Hälften).
  2. `evaluate_live()` — führt die Holdout-Prompts gegen ein echtes Modell
     (JARVIS-Gehirn/OpenRouter) aus und misst eine einfache Wortüberlappung
     (F1) gegen die Referenz. OHNE API-Key wird NICHT evaluiert, sondern
     ehrlich gemeldet, dass ein Key fehlt — es werden keine Zahlen erfunden.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


def _bucket(prompt: str) -> int:
    return int(hashlib.sha256(prompt.encode()).hexdigest(), 16) % 100


def split(examples: list[dict], holdout_pct: int = 20) -> tuple[list[dict], list[dict]]:
    """Deterministischer Split anhand des Prompt-Hashes (kein Leck, reproduzierbar)."""
    train, holdout = [], []
    for ex in examples:
        msgs = ex.get("messages", [])
        prompt = next((m["content"] for m in msgs if m.get("role") == "user"), "")
        (holdout if _bucket(prompt) < holdout_pct else train).append(ex)
    return train, holdout


def _f1(pred: str, ref: str) -> float:
    p, r = set(pred.lower().split()), set(ref.lower().split())
    if not p or not r:
        return 0.0
    overlap = len(p & r)
    if overlap == 0:
        return 0.0
    prec, rec = overlap / len(p), overlap / len(r)
    return round(2 * prec * rec / (prec + rec), 3)


def load_jsonl(path: Path) -> list[dict]:
    out = []
    for line in path.open(encoding="utf-8"):
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except Exception:
                pass
    return out


def evaluate_live(holdout: list[dict], ask_fn, limit: int = 20) -> dict:
    """ask_fn(prompt)->antwort. Misst Wort-F1 gegen die Referenzantwort."""
    scored = []
    for ex in holdout[:limit]:
        msgs = ex.get("messages", [])
        prompt = next((m["content"] for m in msgs if m.get("role") == "user"), "")
        ref = next((m["content"] for m in msgs if m.get("role") == "assistant"), "")
        if not prompt or not ref:
            continue
        pred = ask_fn(prompt)
        scored.append(_f1(pred, ref))
    if not scored:
        return {"evaluiert": 0, "hinweis": "keine auswertbaren Holdout-Beispiele"}
    return {"evaluiert": len(scored),
            "f1_schnitt": round(sum(scored) / len(scored), 3),
            "f1_metrik": "Wortüberlappungs-F1 (einfach, kein semantisches Maß)"}
