#!/usr/bin/env python3
"""Das KI-Team ("Council") — echte Zweitmeinungen von 13 Modellen aus 13 Firmen.

Anders als die Claude-Subagenten (die alle dasselbe Modell nutzen) fragt dieses
Werkzeug ueber OpenRouter WIRKLICH verschiedene Anbieter-Modelle und sammelt
ihre unabhaengigen Antworten. Jede Antwort ist belegt (Modell-ID + Tokens);
ein Modell, das nicht antwortet, wird als Ausfall gemeldet — nicht beschoenigt.

Alle Modell-IDs stammen aus dem Live-Katalog von OpenRouter und wurden per
ops/council_check.py real verifiziert (13/13 haben geantwortet).

Nutzung:
    # Alle 13 fragen:
    python3 ops/council.py "Frage..."
    # Nur bestimmte Anbieter:
    python3 ops/council.py --only OpenAI,Google,DeepSeek "Frage..."
    # Kostenschaetzung vorab, ohne zu senden:
    python3 ops/council.py --dry-run "Frage..."
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys

import httpx

# Pro Anbieter das staerkste real existierende Modell (Stand: Live-Katalog).
COUNCIL: list[tuple[str, str]] = [
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

# Reasoning-Modelle verbrauchen ihr Budget zuerst fuer internes Denken —
# ein knappes Limit erzeugt leere Antworten (kein echter Ausfall).
DEFAULT_MAX_TOKENS = 2000


def select(only: str | None) -> list[tuple[str, str]]:
    if not only:
        return COUNCIL
    wanted = {w.strip().lower() for w in only.split(",") if w.strip()}
    chosen = [(v, m) for v, m in COUNCIL if v.lower() in wanted]
    unknown = wanted - {v.lower() for v, _ in COUNCIL}
    if unknown:
        raise SystemExit(f"Unbekannte Anbieter: {', '.join(sorted(unknown))}")
    return chosen


async def ask(client: httpx.AsyncClient, key: str, vendor: str, model: str,
              question: str, max_tokens: int) -> dict:
    try:
        r = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}"},
            json={
                "model": model,
                "messages": [{"role": "user", "content": question}],
                "max_tokens": max_tokens,
            },
            timeout=300.0,
        )
    except httpx.HTTPError as exc:
        return {"vendor": vendor, "model": model, "ok": False, "error": f"Netzwerk: {exc}"}

    if r.status_code != 200:
        return {"vendor": vendor, "model": model, "ok": False,
                "error": f"HTTP {r.status_code}: {r.text[:200]}"}

    data = r.json()
    choice = (data.get("choices") or [{}])[0]
    answer = (choice.get("message", {}).get("content") or "").strip()
    usage = data.get("usage", {}) or {}
    return {
        "vendor": vendor, "model": model, "ok": bool(answer), "answer": answer,
        "tokens_in": usage.get("prompt_tokens", 0),
        "tokens_out": usage.get("completion_tokens", 0),
        "finish": choice.get("finish_reason"),
    }


async def run(question: str, members: list[tuple[str, str]], max_tokens: int) -> int:
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if not key:
        print("OPENROUTER_API_KEY fehlt (aus .env laden).", file=sys.stderr)
        return 2

    async with httpx.AsyncClient() as client:
        results = await asyncio.gather(
            *[ask(client, key, v, m, question, max_tokens) for v, m in members]
        )

    for r in results:
        print("=" * 78)
        if r["ok"]:
            print(f"{r['vendor']} — {r['model']}  ({r['tokens_in']}→{r['tokens_out']} Tokens)")
            print("-" * 78)
            print(r["answer"])
        else:
            print(f"{r['vendor']} — {r['model']}  AUSFALL: {r.get('error')}")
    print("=" * 78)

    ok = sum(1 for r in results if r["ok"])
    tin = sum(r.get("tokens_in", 0) for r in results)
    tout = sum(r.get("tokens_out", 0) for r in results)
    print(f"{ok}/{len(results)} geantwortet · Verbrauch: {tin} rein, {tout} raus")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("question", nargs="+", help="Die Frage an das Team")
    ap.add_argument("--only", help="Nur diese Anbieter (kommagetrennt), z.B. OpenAI,Google")
    ap.add_argument("--max-tokens", type=int, default=DEFAULT_MAX_TOKENS)
    ap.add_argument("--dry-run", action="store_true",
                    help="Nur zeigen, wer gefragt wuerde — nichts senden, keine Kosten")
    args = ap.parse_args()

    question = " ".join(args.question)
    members = select(args.only)

    if args.dry_run:
        print(f"Wuerde {len(members)} Modelle fragen (max_tokens={args.max_tokens} je Modell):")
        for v, m in members:
            print(f"  {v:10s} {m}")
        print("\nNichts gesendet (--dry-run), keine Kosten entstanden.")
        return 0

    return asyncio.run(run(question, members, args.max_tokens))


if __name__ == "__main__":
    raise SystemExit(main())
