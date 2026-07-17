"""Tests der Trainings-Pipeline (Agent 4 — QS).

Echte Tests gegen eine temporäre Gedächtnis-DB + Ideen-Datei:
Datensatzbau, PII-Bereinigung, Filterung, Token-Statistik, Split & Eval.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path


def _make_memory(db: Path, rows):
    conn = sqlite3.connect(db)
    conn.execute("CREATE TABLE memory (address TEXT, ts REAL, task TEXT, result TEXT)")
    for addr, task, result in rows:
        conn.execute("INSERT INTO memory VALUES (?,?,?,?)", (addr, 0.0, task, result))
    conn.commit()
    conn.close()


def test_scrub_masks_pii():
    from jarvis.training.scrub import scrub, contains_pii
    s = "Mail max@test.de Key sk-ant-ABCDEFGHIJ1234567 IP 10.0.0.1 Tel +41 79 123 45 67"
    out = scrub(s)
    assert "max@test.de" not in out and "[EMAIL]" in out
    assert "sk-ant-" not in out and "[API_KEY]" in out
    assert "10.0.0.1" not in out
    assert not contains_pii(out)


def test_build_dataset_filters_and_scrubs(tmp_path: Path):
    from jarvis.training import build_dataset as bd
    _make_memory(tmp_path / "memory.db", [
        ("1", "Was ist 2+2?", "Die Antwort ist 4, klar erklärt und vollständig."),
        ("2", "Schreib was", "[OFFLINE-Modus, kein API-Key] ..."),         # -> raus
        ("3", "Kontakt?", "Schreib an chef@firma.de für Details bitte melden."),  # PII
        ("4", "kurz", "ok"),                                                # zu kurz -> raus
    ])
    (tmp_path / "ideen.jsonl").write_text(
        json.dumps({"text": "TITEL: Shop\nIDEE: Verkaufe handgemachte Seife online."}) + "\n",
        encoding="utf-8")
    ex = bd.build(tmp_path)
    # nur die 2 brauchbaren Gedächtnis-Beispiele + 1 Idee
    assert len(ex) == 3
    joined = json.dumps(ex, ensure_ascii=False)
    assert "chef@firma.de" not in joined and "[EMAIL]" in joined     # PII bereinigt
    assert "OFFLINE-Modus" not in joined                             # Offline gefiltert
    # gültiges Chat-Format
    for e in ex:
        roles = [m["role"] for m in e["messages"]]
        assert roles == ["user", "assistant"]


def test_build_dataset_empty(tmp_path: Path):
    from jarvis.training import build_dataset as bd
    assert bd.build(tmp_path) == []          # keine Quellen -> leer, kein Crash


def test_tokenize_stats(tmp_path: Path):
    from jarvis.training import tokenize_stats as ts
    ds = tmp_path / "d.jsonl"
    ds.write_text("\n".join(json.dumps({"messages": [
        {"role": "user", "content": "frage " * (i + 1)},
        {"role": "assistant", "content": "antwort text hier"}]}) for i in range(5)),
        encoding="utf-8")
    s = ts.stats(ds)
    assert s["beispiele"] == 5
    assert s["token_gesamt"] > 0 and s["token_max"] >= s["token_min"]
    assert "methode" in s and "empfehlung" in s


def test_split_deterministic_and_no_leak():
    from jarvis.training.evaluate import split
    ex = [{"messages": [{"role": "user", "content": f"prompt {i}"},
                        {"role": "assistant", "content": "a"}]} for i in range(200)]
    tr1, ho1 = split(ex, holdout_pct=20)
    tr2, ho2 = split(ex, holdout_pct=20)
    assert [e["messages"][0]["content"] for e in ho1] == \
           [e["messages"][0]["content"] for e in ho2]          # deterministisch
    train_prompts = {e["messages"][0]["content"] for e in tr1}
    hold_prompts = {e["messages"][0]["content"] for e in ho1}
    assert not (train_prompts & hold_prompts)                  # kein Leck
    assert len(tr1) + len(ho1) == 200


def test_evaluate_live_with_fake_model():
    from jarvis.training.evaluate import evaluate_live
    holdout = [{"messages": [{"role": "user", "content": "was ist vier"},
                             {"role": "assistant", "content": "vier ist eine zahl"}]}]
    # perfektes Fake-Modell -> F1 = 1.0
    r = evaluate_live(holdout, ask_fn=lambda p: "vier ist eine zahl")
    assert r["evaluiert"] == 1 and r["f1_schnitt"] == 1.0
