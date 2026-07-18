"""OpenRouter-Anschluss: JARVIS nutzt viele KI-Modelle über einen Key.

Legitimer, neutraler Multi-Modell-Zugang — KEIN Jailbreak, keine
Prompt-Verschleierung, keine „liberated"-Umgehung von Modell-Sicherheiten.
Einfach: mit deinem eigenen OpenRouter-Key ein beliebiges Modell fragen
(Claude, GPT, Gemini, Grok, Llama, Mistral, DeepSeek, Qwen …) oder mehrere
Modelle parallel vergleichen und die Antworten nebeneinander sehen.

Aktiviert, sobald OPENROUTER_API_KEY gesetzt ist (Key von openrouter.ai/keys).
Ohne Key meldet das Plugin das ehrlich und tut nichts.
"""

from __future__ import annotations

import concurrent.futures
import json
import os
import urllib.error
import urllib.request

from .plugins import Plugin

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# Anbieter-Katalog: Firma -> Liste (Anzeigename, OpenRouter-ID).
# Nur Zugang, keine vorgefertigten Prompts. Beliebige OpenRouter-IDs sind
# ebenfalls direkt nutzbar (z. B. model=anthropic/claude-opus-4.8).
#
# EHRLICH: Ein Teil dieser Modelle ist sehr neu bzw. noch nicht veröffentlicht.
# Ist eine ID bei OpenRouter (noch) nicht verfügbar, liefert der Aufruf eine
# ehrliche Fehlermeldung — es wird nichts erfunden. Die jeweils aktuell
# verfügbaren IDs stehen auf openrouter.ai/models.
PROVIDERS: dict[str, list[tuple[str, str]]] = {
    "Anthropic": [
        ("Claude Mythos 5", "anthropic/claude-mythos-5"),
        ("Claude Fable 5", "anthropic/claude-fable-5"),
        ("Claude Opus 4.8", "anthropic/claude-opus-4.8"),
        ("Claude Sonnet 5", "anthropic/claude-sonnet-5"),
        ("Claude Haiku 4.5", "anthropic/claude-haiku-4.5"),
    ],
    "OpenAI": [
        ("GPT-5.6 Sol Ultra", "openai/gpt-5.6-sol-ultra"),
        ("GPT-5.6 Sol", "openai/gpt-5.6-sol"),
        ("GPT-5.6 Terra", "openai/gpt-5.6-terra"),
        ("GPT-5.6 Luna", "openai/gpt-5.6-luna"),
        ("GPT-5.5", "openai/gpt-5.5"),
        ("GPT-5", "openai/gpt-5"),
        ("o3", "openai/o3"),
        ("o4-mini-high", "openai/o4-mini-high"),
        ("o4-mini", "openai/o4-mini"),
    ],
    "Google": [
        ("Gemini 3.5 Pro", "google/gemini-3.5-pro"),
        ("Gemini 3.5 Flash", "google/gemini-3.5-flash"),
        ("Gemini 2.5 Pro", "google/gemini-2.5-pro"),
        ("Gemini 2.5 Flash", "google/gemini-2.5-flash"),
    ],
    "xAI": [
        ("Grok 4.5", "x-ai/grok-4.5"),
        ("Grok 4", "x-ai/grok-4"),
        ("Grok 3", "x-ai/grok-3"),
    ],
    "DeepSeek": [
        ("DeepSeek R1", "deepseek/deepseek-r1"),
        ("DeepSeek V3.1", "deepseek/deepseek-v3.1"),
        ("DeepSeek V3", "deepseek/deepseek-v3"),
    ],
    "Qwen": [
        ("Qwen 3.7 Plus", "qwen/qwen3.7-plus"),
        ("Qwen 3", "qwen/qwen3"),
        ("Qwen 2.5", "qwen/qwen-2.5-72b-instruct"),
    ],
    "Zhipu AI": [
        ("GLM-5.2", "z-ai/glm-5.2"),
        ("GLM-5", "z-ai/glm-5"),
    ],
    "MiniMax": [
        ("MiniMax M3", "minimax/minimax-m3"),
    ],
    "Moonshot AI": [
        ("Kimi K2", "moonshotai/kimi-k2"),
        ("Kimi K1.5", "moonshotai/kimi-k1.5"),
    ],
}


def _norm(s: str) -> str:
    return s.lower().replace(" ", "").replace("-", "").replace(".", "").replace("_", "")


# normalisierter Anzeigename -> ID (für die Auflösung von "modell <name>: …")
_CATALOG: dict[str, str] = {}
for _prov, _models in PROVIDERS.items():
    for _disp, _mid in _models:
        _CATALOG[_norm(_disp)] = _mid

# handverlesene Kurznamen für schnelles Tippen
_ALIASES = {
    "claude": "anthropic/claude-opus-4.8", "opus": "anthropic/claude-opus-4.8",
    "fable": "anthropic/claude-fable-5", "mythos": "anthropic/claude-mythos-5",
    "sonnet": "anthropic/claude-sonnet-5", "haiku": "anthropic/claude-haiku-4.5",
    "gpt": "openai/gpt-5.6-sol", "sol": "openai/gpt-5.6-sol",
    "terra": "openai/gpt-5.6-terra", "luna": "openai/gpt-5.6-luna",
    "gemini": "google/gemini-3.5-pro", "gemini-flash": "google/gemini-3.5-flash",
    "grok": "x-ai/grok-4.5", "deepseek": "deepseek/deepseek-v3.1",
    "r1": "deepseek/deepseek-r1", "qwen": "qwen/qwen3.7-plus",
    "glm": "z-ai/glm-5.2", "minimax": "minimax/minimax-m3",
    "kimi": "moonshotai/kimi-k2",
}
for _k, _v in _ALIASES.items():
    _CATALOG.setdefault(_norm(_k), _v)


def resolve(name: str) -> str:
    """Anzeigename/Kurzname -> OpenRouter-ID; unbekanntes bleibt Roh-ID."""
    if not name:
        return DEFAULT_COMPARE[0]
    return _CATALOG.get(_norm(name), name.strip())


# Standard-Set für "vergleiche die modelle: …" — je ein Flaggschiff pro großem
# Anbieter. Anpassbar über JARVIS_COMPARE_MODELS (Komma-getrennt).
DEFAULT_COMPARE = ["anthropic/claude-opus-4.8", "openai/gpt-5.6-sol",
                   "google/gemini-3.5-pro", "x-ai/grok-4.5",
                   "deepseek/deepseek-r1"]


def _compare_models() -> list[str]:
    env = os.environ.get("JARVIS_COMPARE_MODELS", "").strip()
    if env:
        ids = [resolve(m) for m in env.split(",") if m.strip()]
        if ids:
            return ids
    return DEFAULT_COMPARE

# Neutraler Assistenten-Systemprompt (bewusst KEINE Jailbreak-Anweisung).
SYSTEM = ("Du bist ein hilfreicher, sachlicher Assistent in JARVIS. "
          "Antworte knapp und korrekt auf Deutsch. Erfinde keine Fakten.")


def available() -> bool:
    return bool(os.environ.get("OPENROUTER_API_KEY"))


def ask(model: str, prompt: str, system: str = SYSTEM,
        max_tokens: int = 600, timeout: int = 120) -> str:
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        return "[kein OPENROUTER_API_KEY gesetzt — Key von openrouter.ai/keys]"
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    payload = {"model": model, "messages": messages, "max_tokens": max_tokens}
    req = urllib.request.Request(
        OPENROUTER_URL, data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {key}",
                 "content-type": "application/json",
                 "HTTP-Referer": "http://localhost",
                 "X-Title": "JARVIS"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read())
        return data["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        return f"[OpenRouter {e.code}: {e.reason}]"
    except Exception as e:  # Netzwerk o. ä.: ehrlich melden statt erfinden
        return f"[OpenRouter nicht erreichbar: {type(e).__name__}]"


def compare(prompt: str, models: list[str] | None = None,
            system: str = SYSTEM, max_tokens: int = 500) -> list[dict]:
    """Fragt mehrere Modelle parallel und gibt alle Antworten zurück."""
    models = models or _compare_models()
    out: list[dict] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(5, len(models))) as ex:
        futs = {ex.submit(ask, m, prompt, system, max_tokens): m for m in models}
        for f in concurrent.futures.as_completed(futs):
            out.append({"modell": futs[f], "antwort": f.result()})
    # stabile Reihenfolge wie angefragt
    order = {m: i for i, m in enumerate(models)}
    out.sort(key=lambda r: order.get(r["modell"], 99))
    return out


class OpenRouterPlugin(Plugin):
    name = "modelle"
    description = ("Viele KI-Modelle über OpenRouter (Claude, GPT, Gemini, Grok, "
                   "Llama, Mistral, DeepSeek, Qwen) — dein eigener Key")

    def health(self) -> tuple[bool, str]:
        if available():
            return True, ""
        return False, "kein OPENROUTER_API_KEY gesetzt (Key von openrouter.ai/keys)"

    def run(self, action: str = "liste", model: str = "", prompt: str = "",
            **kwargs: object) -> object:
        if action in ("liste", "list", "modelle"):
            return {"anbieter": {p: [{"name": d, "id": i} for d, i in ms]
                                 for p, ms in PROVIDERS.items()},
                    "anzahl": sum(len(ms) for ms in PROVIDERS.values()),
                    "vergleich_standard": _compare_models(),
                    "aktiv": available(),
                    "hinweis": "eigener Key als OPENROUTER_API_KEY setzen; "
                               "Vergleichsliste über JARVIS_COMPARE_MODELS anpassbar; "
                               "sehr neue Modelle sind evtl. bei OpenRouter noch nicht live"}
        if action in ("frage", "ask", "prompt"):
            if not prompt:
                raise ValueError("prompt= fehlt")
            mid = resolve(model)
            return {"modell": mid, "antwort": ask(mid, prompt)}
        if action in ("vergleich", "compare", "race", "vergleiche"):
            if not prompt:
                raise ValueError("prompt= fehlt")
            return {"vergleich": compare(prompt)}
        raise ValueError("Aktion: liste | frage model=<name> prompt=<text> | "
                         "vergleich prompt=<text>")


def register(manager, workspace=None) -> None:
    manager.plugins["modelle"] = OpenRouterPlugin()
