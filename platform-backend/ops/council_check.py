#!/usr/bin/env python3
"""Prueft, welche Modelle des KI-Teams ueber OpenRouter WIRKLICH antworten.

Schickt an jedes Modell eine minimale echte Anfrage und meldet Erfolg,
Antwortauszug, Token-Verbrauch und Fehler. Keine Behauptung ohne Beleg —
ein Modell gilt nur als "im Team", wenn es hier tatsaechlich geantwortet hat.

Nutzung:
    OPENROUTER_API_KEY=... python3 ops/council_check.py
"""
from __future__ import annotations

import asyncio
import json
import os
import sys

import httpx

# Das Team: pro Anbieter das staerkste real existierende Modell.
# IDs stammen aus dem Live-Katalog (https://openrouter.ai/api/v1/models),
# NICHT aus Vermutungen.
COUNCIL = [
    ("OpenAI",     "openai/gpt-5.6-sol-pro"),
    ("Anthropic",  "anthropic/claude-opus-4.8"),
    ("Google",     "google/gemini-3.1-pro-preview"),
    ("xAI",        "x-ai/grok-4.5"),
    ("Moonshot",   "moonshotai/kimi-k3"),
    ("DeepSeek",   "deepseek/deepseek-v4-pro"),
    ("Alibaba",    "qwen/qwen3.7-max"),
    ("Meta",       "meta-llama/llama-4-maverick"),
    ("Mistral",    "mistralai/mistral-large-2512"),
    ("Z-AI",       "z-ai/glm-5.2"),
    ("Microsoft",  "microsoft/phi-4"),
    ("Cohere",     "cohere/command-a"),
    ("NVIDIA",     "nvidia/nemotron-3-ultra-550b-a55b"),
]

PROMPT = "Antworte in genau einem kurzen deutschen Satz: Wer bist du?"


async def probe(client: httpx.AsyncClient, key: str, vendor: str, model: str) -> dict:
    try:
        r = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}"},
            json={
                "model": model,
                "messages": [{"role": "user", "content": PROMPT}],
                # Grosszuegig: Reasoning-Modelle (Gemini, Kimi, DeepSeek, GLM)
                # verbrauchen ihr Budget zuerst fuer internes Denken und lieferten
                # bei knappem Limit eine leere Antwort — das ist kein Ausfall.
                "max_tokens": 2000,
            },
            timeout=120.0,
        )
    except httpx.HTTPError as exc:
        return {"vendor": vendor, "model": model, "ok": False, "error": f"Netzwerk: {exc}"}

    if r.status_code != 200:
        detail = r.text[:160].replace("\n", " ")
        return {"vendor": vendor, "model": model, "ok": False, "error": f"HTTP {r.status_code}: {detail}"}

    data = r.json()
    answer = (data.get("choices") or [{}])[0].get("message", {}).get("content", "") or ""
    usage = data.get("usage", {}) or {}
    return {
        "vendor": vendor,
        "model": model,
        "ok": bool(answer.strip()),
        "answer": answer.strip()[:110],
        "tokens_in": usage.get("prompt_tokens", 0),
        "tokens_out": usage.get("completion_tokens", 0),
    }


async def main() -> int:
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if not key:
        print("OPENROUTER_API_KEY fehlt (aus .env laden).", file=sys.stderr)
        return 2

    async with httpx.AsyncClient() as client:
        results = await asyncio.gather(*[probe(client, key, v, m) for v, m in COUNCIL])

    ok_count = sum(1 for r in results if r["ok"])
    tin = sum(r.get("tokens_in", 0) for r in results)
    tout = sum(r.get("tokens_out", 0) for r in results)

    for r in results:
        mark = "OK  " if r["ok"] else "FEHL"
        line = f"[{mark}] {r['vendor']:10s} {r['model']:38s}"
        print(line, r.get("answer") or r.get("error", ""))

    print(f"\n{ok_count}/{len(results)} Modelle haben wirklich geantwortet.")
    print(f"Verbrauch dieses Checks: {tin} Tokens rein, {tout} raus.")

    out = {"ok": ok_count, "total": len(results), "results": results}
    pathlib_out = os.environ.get("COUNCIL_CHECK_OUT")
    if pathlib_out:
        with open(pathlib_out, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
    return 0 if ok_count == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
