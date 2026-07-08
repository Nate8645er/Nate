"""Client für das Claude API von Anthropic (Cloud-Gehirn für Jarvis).

Der API-Schlüssel wird NIE im Code oder in config.json gespeichert.
Jarvis sucht ihn in dieser Reihenfolge:
  1. Umgebungsvariable ANTHROPIC_API_KEY
  2. config/secrets.json  ->  {"anthropic_api_key": "sk-ant-..."}
     (diese Datei steht in .gitignore und landet nie auf GitHub)
"""

import json
import logging
import os

from jarvis.core.errors import LLMError
from jarvis.utils.config_loader import PROJECT_ROOT

logger = logging.getLogger("jarvis.claude")

SECRETS_PATH = PROJECT_ROOT / "config" / "secrets.json"


def _load_api_key() -> str | None:
    key = os.environ.get("ANTHROPIC_API_KEY")
    if key:
        return key
    if SECRETS_PATH.exists():
        try:
            secrets = json.loads(SECRETS_PATH.read_text(encoding="utf-8"))
            return secrets.get("anthropic_api_key") or None
        except (OSError, json.JSONDecodeError) as e:
            logger.error("secrets.json konnte nicht gelesen werden: %s", e)
    return None


class ClaudeClient:
    """Gleiche Schnittstelle wie OllamaClient - austauschbar per Konfiguration."""

    def __init__(
        self,
        model: str = "claude-fable-5",
        max_tokens: int = 16000,
        fallback_model: str | None = "claude-opus-4-8",
    ):
        self.model = model
        self.max_tokens = max_tokens
        # Springt automatisch ein, wenn das Hauptmodell eine Anfrage aus
        # Sicherheitsgründen ablehnt (relevant vor allem für Claude Fable 5).
        self.fallback_model = fallback_model if fallback_model != model else None
        self._api_key = _load_api_key()
        self._client = None
        if self._api_key:
            import anthropic
            self._client = anthropic.Anthropic(api_key=self._api_key)

    def is_available(self) -> bool:
        """Verfügbar, sobald ein API-Schlüssel gefunden wurde."""
        return self._client is not None

    def list_models(self) -> list[str]:
        import anthropic
        try:
            return [m.id for m in self._client.models.list()]
        except anthropic.APIError as e:
            raise LLMError(f"Modellliste konnte nicht geladen werden: {e}") from e

    def chat(self, prompt: str | None = None, messages: list[dict] | None = None) -> str:
        """Sendet eine Nachricht oder einen Verlauf an Claude.

        Nimmt dasselbe Nachrichtenformat wie der OllamaClient entgegen.
        Ein 'system'-Eintrag am Anfang wird in den system-Parameter des
        Claude API übersetzt.
        """
        if self._client is None:
            raise LLMError(
                "Kein Anthropic-API-Schlüssel gefunden. Trage ihn in "
                "config/secrets.json ein ({\"anthropic_api_key\": \"sk-ant-...\"}) "
                "oder setze die Umgebungsvariable ANTHROPIC_API_KEY."
            )

        import anthropic

        if messages is None:
            if prompt is None:
                raise ValueError("Entweder 'prompt' oder 'messages' angeben.")
            messages = [{"role": "user", "content": prompt}]

        system_prompt = None
        chat_messages = []
        for message in messages:
            if message["role"] == "system" and not chat_messages:
                system_prompt = message["content"]
            else:
                chat_messages.append(
                    {"role": message["role"], "content": message["content"]}
                )

        try:
            request = {
                "model": self.model,
                "max_tokens": self.max_tokens,
                "thinking": {"type": "adaptive"},
                "messages": chat_messages,
            }
            if system_prompt:
                request["system"] = system_prompt
            if self.fallback_model:
                # Server-seitiger Fallback: lehnt das Hauptmodell ab,
                # beantwortet das Ersatzmodell dieselbe Anfrage automatisch.
                response = self._client.beta.messages.create(
                    **request,
                    betas=["server-side-fallback-2026-06-01"],
                    fallbacks=[{"model": self.fallback_model}],
                )
            else:
                response = self._client.messages.create(**request)
        except anthropic.AuthenticationError as e:
            raise LLMError(
                "Der API-Schlüssel wurde abgelehnt. Bitte prüfe ihn in "
                "config/secrets.json (er beginnt mit 'sk-ant-')."
            ) from e
        except anthropic.RateLimitError as e:
            raise LLMError(
                "Das Claude API ist gerade ausgelastet (Rate-Limit). "
                "Bitte in einer Minute nochmal versuchen."
            ) from e
        except anthropic.APIConnectionError as e:
            raise LLMError(
                "Keine Verbindung zum Claude API - ist das Internet erreichbar?"
            ) from e
        except anthropic.APIStatusError as e:
            raise LLMError(f"Claude-API-Fehler ({e.status_code}): {e.message}") from e

        if response.stop_reason == "refusal":
            # Auch das Fallback-Modell hat abgelehnt (oder keins konfiguriert)
            return "Diese Anfrage kann ich aus Sicherheitsgründen nicht beantworten."

        answer = "".join(
            block.text for block in response.content if block.type == "text"
        )
        logger.debug(
            "Claude-Antwort erhalten (%d Zeichen, %d Output-Tokens).",
            len(answer), response.usage.output_tokens,
        )
        return answer
