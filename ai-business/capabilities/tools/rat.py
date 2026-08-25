#!/usr/bin/env python3
"""
rat.py - fragt mehrere fremde Modelle parallel dieselbe Frage.

Warum das existiert:
Claude, der Claude prueft, findet nichts. Am 19.8.2026 haben vier fremde
Modelle unabhaengig dasselbe geantwortet - das war der Moment, in dem eine
Antwort belastbar wurde. Dieses Werkzeug macht daraus einen Handgriff.

OmniRoute streamt SSE, auch wenn man es nicht will. Wer hier json.load()
aufruft, bekommt einen Fehler und glaubt, der Server sei kaputt. Er ist es
nicht - man muss die "data:"-Zeilen lesen.

Denkende Modelle verbrauchen ihr Budget in der Denkphase. Bei 1400 Token
kam von Kimi K3 leerer Inhalt zurueck. Darum ist die Untergrenze hier hoch.
"""

import json
import sys
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor

WOHIN = "http://localhost:20128/v1/chat/completions"

# Die Flotte. Jedes Modell aus einem anderen Haus - sonst ist es keine
# zweite Meinung, sondern dasselbe Vorurteil zweimal.
FLOTTE = {
    "GPT-5.6":      "openrouter/openai/gpt-5.6-luna-pro",
    "Kimi K3":      "openrouter/moonshotai/kimi-k3",
    "Gemini 3.7":   "openrouter/google/gemini-3.7-flash",
    "Qwen3-Max":    "openrouter/qwen/qwen3-max-thinking",
    "DeepSeek V4":  "openrouter/deepseek/deepseek-v4-pro-0813",
    "Grok 4.6":     "openrouter/x-ai/grok-4.6",
    "Mistral L":    "openrouter/mistralai/mistral-large-2512",
}


def frag(modell, frage, system=None, max_tokens=9000, temperatur=0.7):
    nachrichten = []
    if system:
        nachrichten.append({"role": "system", "content": system})
    nachrichten.append({"role": "user", "content": frage})

    koerper = json.dumps({
        "model": modell,
        "messages": nachrichten,
        "max_tokens": max_tokens,
        "temperature": temperatur,
    }).encode()

    anfrage = urllib.request.Request(
        WOHIN, data=koerper,
        headers={"Content-Type": "application/json"},
    )

    try:
        with urllib.request.urlopen(anfrage, timeout=600) as antwort:
            roh = antwort.read().decode("utf-8", "replace")
    except Exception as e:
        return f"[FEHLER {modell}: {e}]"

    # Erst der einfache Fall.
    try:
        d = json.loads(roh)
        return d["choices"][0]["message"]["content"] or "[LEER]"
    except Exception:
        pass

    # Sonst SSE.
    stuecke = []
    for zeile in roh.splitlines():
        if not zeile.startswith("data:"):
            continue
        nutzlast = zeile[5:].strip()
        if not nutzlast or nutzlast == "[DONE]":
            continue
        try:
            d = json.loads(nutzlast)
            delta = d["choices"][0].get("delta", {})
            stueck = delta.get("content")
            if stueck:
                stuecke.append(stueck)
        except Exception:
            continue
    return "".join(stuecke) or "[LEER - vermutlich hat die Denkphase das Budget aufgebraucht]"


def rat(frage, system=None, wer=None, max_tokens=9000):
    """Fragt die Flotte parallel. Gibt {name: antwort} zurueck."""
    ziele = wer or list(FLOTTE.keys())
    ergebnis = {}
    with ThreadPoolExecutor(max_workers=len(ziele)) as pool:
        auftraege = {
            pool.submit(frag, FLOTTE[n], frage, system, max_tokens): n
            for n in ziele if n in FLOTTE
        }
        for a in auftraege:
            name = auftraege[a]
            ergebnis[name] = a.result()
    return ergebnis


if __name__ == "__main__":
    frage = sys.stdin.read()
    antworten = rat(frage)
    for name, text in antworten.items():
        print(f"\n{'='*70}\n{name}\n{'='*70}\n{text}")
