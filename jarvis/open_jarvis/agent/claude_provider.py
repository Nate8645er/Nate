"""Claude/Fable-Provider fuer den JARVIS-Agenten (Anthropic Messages API).

Ermoeglicht dem Agenten, mit Claude-Modellen inkl. **Fable 5** zu planen.
Verwendet nur ``requests`` (bereits eine JARVIS-Abhaengigkeit) und die
oeffentliche Messages-API.

Ehrlich: Braucht einen Anthropic-API-Schluessel in ``ANTHROPIC_API_KEY``.
Fehlt der Schluessel, meldet der Provider sauber ``unavailable`` — der Agent
faellt dann automatisch auf den lokalen Planer zurueck.
"""

from __future__ import annotations

import json
import os
from typing import Any

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
DEFAULT_TIMEOUT = 60


class ClaudePlannerError(RuntimeError):
    """Fehler beim Planen mit einem Claude-Modell."""


def _extract_json_object(text: str) -> dict[str, Any]:
    """Erstes JSON-Objekt aus einer Modellantwort ziehen (robust gegen Codebloecke)."""

    value = (text or "").strip()
    if "```" in value:
        parts = value.split("```")
        for part in parts:
            candidate = part[4:].strip() if part.startswith("json") else part.strip()
            if "{" in candidate:
                value = candidate
                break
    start = value.find("{")
    end = value.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ClaudePlannerError("Keine JSON-Antwort vom Modell erhalten.")
    return json.loads(value[start : end + 1])


class ClaudeProvider:
    """Planer-Provider auf Basis der Anthropic Messages API."""

    name = "claude"

    def __init__(
        self,
        *,
        model_id: str,
        api_key: str | None = None,
        env_key: str = "ANTHROPIC_API_KEY",
        transport: Any = None,
        max_tokens: int = 1024,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> None:
        self.model_id = model_id
        self.api_key = (api_key if api_key is not None else os.getenv(env_key, "")).strip()
        self._transport = transport  # fuer Tests injizierbar; sonst requests.post
        self.max_tokens = max_tokens
        self.timeout = timeout

    def available(self) -> bool:
        return bool(self.api_key)

    def _post(self, payload: dict[str, Any], headers: dict[str, str]) -> dict[str, Any]:
        if self._transport is not None:
            return self._transport(ANTHROPIC_URL, payload, headers)
        try:
            import requests
        except ImportError as exc:  # pragma: no cover
            raise ClaudePlannerError("Das Paket 'requests' ist nicht installiert.") from exc
        response = requests.post(ANTHROPIC_URL, json=payload, headers=headers, timeout=self.timeout)
        if response.status_code != 200:
            raise ClaudePlannerError(f"API-Fehler {response.status_code}")
        return response.json()

    def plan(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        """Einen Plan (JSON) vom Modell anfordern."""

        if not self.available():
            raise ClaudePlannerError("Kein Anthropic-API-Schluessel gesetzt.")
        payload = {
            "model": self.model_id,
            "max_tokens": self.max_tokens,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}],
        }
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": ANTHROPIC_VERSION,
            "content-type": "application/json",
        }
        data = self._post(payload, headers)
        # Messages-API: content ist eine Liste von Bloecken mit {type:"text", text:...}
        blocks = data.get("content") or []
        text = "".join(block.get("text", "") for block in blocks if isinstance(block, dict))
        if not text.strip():
            raise ClaudePlannerError("Leere Antwort vom Modell.")
        return _extract_json_object(text)
