"""Tokenisierungs-Statistik (Agent 3 — ML/Training, Agent 5 — Performance).

Liest ein Chat-JSONL und berechnet ECHTE Token-/Längen-Statistiken, damit man
Hyperparameter (Kontextlänge, Batch, Epochen) fundiert wählen kann.

Tokenzählung:
  - Wenn `tiktoken` installiert ist -> echte BPE-Tokenzählung (genau).
  - Sonst -> wortbasierte Schätzung (~1,3 Token/Wort), EHRLICH als Schätzung
    gekennzeichnet. Es wird nichts als „genau" ausgegeben, was geschätzt ist.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _counter():
    """Gibt (zähl_funktion, methode_str) zurück."""
    try:
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")
        return (lambda s: len(enc.encode(s)), "tiktoken/cl100k_base (genau)")
    except Exception:
        # Wortbasierte Schätzung — bewusst konservativ, klar gekennzeichnet.
        return (lambda s: max(1, int(len(s.split()) * 1.3)), "Wort-Schätzung (~1,3/Wort)")


def stats(jsonl_path: Path) -> dict:
    count_fn, method = _counter()
    n = 0
    tok_counts: list[int] = []
    for line in jsonl_path.open(encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        try:
            ex = json.loads(line)
        except Exception:
            continue
        text = " ".join(m.get("content", "") for m in ex.get("messages", []))
        tok_counts.append(count_fn(text))
        n += 1
    if not tok_counts:
        return {"beispiele": 0, "methode": method,
                "hinweis": "leerer/kein Datensatz"}
    tok_counts.sort()
    total = sum(tok_counts)
    return {
        "beispiele": n,
        "methode": method,
        "token_gesamt": total,
        "token_min": tok_counts[0],
        "token_max": tok_counts[-1],
        "token_schnitt": round(total / n, 1),
        "token_median": tok_counts[len(tok_counts) // 2],
        # praktische Empfehlung (konservativ, als Vorschlag gekennzeichnet)
        "empfehlung": {
            "kontextlaenge": 1 << max(9, (tok_counts[-1]).bit_length()),  # nächste 2er-Potenz
            "epochen_vorschlag": 3 if n < 1000 else 2,
            "hinweis": "Vorschlag, kein garantierter Optimalwert",
        },
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Token-Statistik eines JSONL-Datensatzes")
    ap.add_argument("--in", dest="inp", default="dataset.jsonl")
    args = ap.parse_args()
    p = Path(args.inp)
    if not p.exists():
        print(f"Datei nicht gefunden: {p}")
        return
    s = stats(p)
    print(json.dumps(s, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
