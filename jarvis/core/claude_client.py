"""Client für das Claude API von Anthropic (Cloud-Gehirn für Jarvis).

Der API-Schlüssel wird NIE im Code oder in config.json gespeichert.
Jarvis sucht ihn in dieser Reihenfolge:
  1. Umgebungsvariable ANTHROPIC_API_KEY
  2. config/secrets.json  ->  {"anthropic_api_key": "sk-ant-..."}
     (diese Datei steht in .gitignore und landet nie auf GitHub)
"""

import logging

from jarvis.core.errors import LLMError
from jarvis.utils.secrets import load_secret

logger = logging.getLogger("jarvis.claude")


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
        self._api_key = load_secret("anthropic_api_key", "ANTHROPIC_API_KEY")
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

    def _build_request(
        self, prompt: str | None, messages: list[dict] | None
    ) -> dict:
        """Baut die Claude-Anfrage aus dem Ollama-Nachrichtenformat."""
        if self._client is None:
            raise LLMError(
                "Kein Anthropic-API-Schlüssel gefunden. Trage ihn in "
                "config/secrets.json ein ({\"anthropic_api_key\": \"sk-ant-...\"}) "
                "oder setze die Umgebungsvariable ANTHROPIC_API_KEY."
            )

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

        request = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "thinking": {"type": "adaptive"},
            "messages": chat_messages,
        }
        if system_prompt:
            request["system"] = system_prompt
        return request

    @staticmethod
    def _translate_error(e: Exception) -> LLMError:
        """Übersetzt API-Fehler in verständliche deutsche Meldungen."""
        import anthropic

        if isinstance(e, anthropic.AuthenticationError):
            return LLMError(
                "Der API-Schlüssel wurde abgelehnt. Bitte prüfe ihn in "
                "config/secrets.json (er beginnt mit 'sk-ant-')."
            )
        if isinstance(e, anthropic.RateLimitError):
            return LLMError(
                "Das Claude API ist gerade ausgelastet (Rate-Limit). "
                "Bitte in einer Minute nochmal versuchen."
            )
        if isinstance(e, anthropic.APIConnectionError):
            return LLMError(
                "Keine Verbindung zum Claude API - ist das Internet erreichbar?"
            )
        if isinstance(e, anthropic.APIStatusError):
            return LLMError(f"Claude-API-Fehler ({e.status_code}): {e.message}")
        return LLMError(f"Claude-API-Fehler: {e}")

    def chat_stream(self, prompt: str | None = None, messages: list[dict] | None = None):
        """Wie chat(), aber als Generator: liefert die Antwort stückweise.

        Damit kann die Sprachausgabe mit dem ersten Satz beginnen, während
        Claude noch am Rest schreibt - statt erst zu warten, bis die
        komplette Antwort fertig ist.
        """
        import anthropic

        request = self._build_request(prompt, messages)

        try:
            if self.fallback_model:
                # Server-seitiger Fallback: lehnt das Hauptmodell ab,
                # beantwortet das Ersatzmodell dieselbe Anfrage automatisch.
                stream_context = self._client.beta.messages.stream(
                    **request,
                    betas=["server-side-fallback-2026-06-01"],
                    fallbacks=[{"model": self.fallback_model}],
                )
            else:
                stream_context = self._client.messages.stream(**request)

            got_text = False
            with stream_context as stream:
                for piece in stream.text_stream:
                    if piece:
                        got_text = True
                        yield piece
                response = stream.get_final_message()
        except anthropic.APIError as e:
            raise self._translate_error(e) from e

        if response.stop_reason == "refusal" and not got_text:
            # Auch das Fallback-Modell hat abgelehnt (oder keins konfiguriert)
            yield "Diese Anfrage kann ich aus Sicherheitsgründen nicht beantworten."
        logger.debug(
            "Claude-Antwort gestreamt (%d Output-Tokens).",
            response.usage.output_tokens,
        )

    def chat(self, prompt: str | None = None, messages: list[dict] | None = None) -> str:
        """Sendet eine Nachricht oder einen Verlauf an Claude.

        Nimmt dasselbe Nachrichtenformat wie der OllamaClient entgegen.
        Ein 'system'-Eintrag am Anfang wird in den system-Parameter des
        Claude API übersetzt.
        """
        import anthropic

        request = self._build_request(prompt, messages)

        try:
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
        except anthropic.APIError as e:
            raise self._translate_error(e) from e

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
