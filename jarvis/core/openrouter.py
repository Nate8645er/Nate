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

# Kuratierte, gängige Modelle (Kurzname -> OpenRouter-ID). Nur Zugang, keine
# vorgefertigten Prompts. Eigene IDs sind ebenfalls direkt nutzbar.
KNOWN_MODELS = {
    "claude": "anthropic/claude-3.5-sonnet",
    "gpt": "openai/gpt-4o",
    "gpt4": "openai/gpt-4o",
    "gemini": "google/gemini-2.5-flash",
    "grok": "x-ai/grok-3",
    "llama": "meta-llama/llama-3.3-70b-instruct",
    "mistral": "mistralai/mistral-large",
    "deepseek": "deepseek/deepseek-chat",
    "qwen": "qwen/qwen-2.5-72b-instruct",
}

DEFAULT_COMPARE = ["anthropic/claude-3.5-sonnet", "openai/gpt-4o",
                   "google/gemini-2.5-flash"]

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
    models = models or DEFAULT_COMPARE
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
            return {"bekannt": KNOWN_MODELS,
                    "vergleich_standard": DEFAULT_COMPARE,
                    "aktiv": available(),
                    "hinweis": "eigener Key als OPENROUTER_API_KEY setzen"}
        if action in ("frage", "ask", "prompt"):
            if not prompt:
                raise ValueError("prompt= fehlt")
            mid = KNOWN_MODELS.get(model.lower().strip(), model.strip()) or DEFAULT_COMPARE[0]
            return {"modell": mid, "antwort": ask(mid, prompt)}
        if action in ("vergleich", "compare", "race", "vergleiche"):
            if not prompt:
                raise ValueError("prompt= fehlt")
            return {"vergleich": compare(prompt)}
        raise ValueError("Aktion: liste | frage model=<name> prompt=<text> | "
                         "vergleich prompt=<text>")


def register(manager, workspace=None) -> None:
    manager.plugins["modelle"] = OpenRouterPlugin()
