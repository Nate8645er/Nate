"""Client für die Verbindung zu einem lokalen Ollama-Server."""

import json
import logging

import requests

from jarvis.core.errors import LLMError

logger = logging.getLogger("jarvis.ollama")


class OllamaConnectionError(LLMError):
    """Wird ausgelöst, wenn der Ollama-Server nicht erreichbar ist."""


class OllamaClient:
    """Kapselt die HTTP-Kommunikation mit dem lokalen Ollama-Server."""

    def __init__(self, base_url: str, model: str, timeout: int = 120):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def is_available(self) -> bool:
        """Prüft, ob der Ollama-Server läuft."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def list_models(self) -> list[str]:
        """Gibt die Namen aller lokal installierten Modelle zurück."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
            return [m["name"] for m in response.json().get("models", [])]
        except requests.RequestException as e:
            raise OllamaConnectionError(
                f"Modellliste konnte nicht geladen werden: {e}"
            ) from e

    def chat(self, prompt: str | None = None, messages: list[dict] | None = None) -> str:
        """Sendet eine Nachricht oder einen Gesprächsverlauf an das Modell.

        Entweder `prompt` (einzelne Frage) oder `messages`
        (kompletter Verlauf im Format [{"role": ..., "content": ...}]) angeben.
        """
        if messages is None:
            if prompt is None:
                raise ValueError("Entweder 'prompt' oder 'messages' angeben.")
            messages = [{"role": "user", "content": prompt}]
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
        }
        try:
            logger.debug("Sende Anfrage an Modell '%s' ...", self.model)
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            answer = response.json()["message"]["content"]
            logger.debug("Antwort erhalten (%d Zeichen).", len(answer))
            return answer
        except requests.ConnectionError as e:
            raise OllamaConnectionError(
                f"Keine Verbindung zu Ollama unter {self.base_url}. "
                "Läuft der Ollama-Server? (Start mit: ollama serve)"
            ) from e
        except requests.HTTPError as e:
            raise OllamaConnectionError(
                f"Ollama-Fehler: {e.response.status_code} - {e.response.text}"
            ) from e
        except requests.RequestException as e:
            raise OllamaConnectionError(f"Anfrage fehlgeschlagen: {e}") from e

    def chat_stream(self, prompt: str | None = None, messages: list[dict] | None = None):
        """Wie chat(), aber als Generator: liefert die Antwort stückweise.

        Ollama sendet bei stream=True eine JSON-Zeile pro Text-Häppchen;
        jedes Häppchen wird sofort weitergereicht, damit die Sprachausgabe
        nicht auf die komplette Antwort warten muss.
        """
        if messages is None:
            if prompt is None:
                raise ValueError("Entweder 'prompt' oder 'messages' angeben.")
            messages = [{"role": "user", "content": prompt}]
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
        }
        try:
            logger.debug("Sende Stream-Anfrage an Modell '%s' ...", self.model)
            with requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=self.timeout,
                stream=True,
            ) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if not line:
                        continue
                    data = json.loads(line)
                    piece = data.get("message", {}).get("content", "")
                    if piece:
                        yield piece
                    if data.get("done"):
                        break
        except requests.ConnectionError as e:
            raise OllamaConnectionError(
                f"Keine Verbindung zu Ollama unter {self.base_url}. "
                "Läuft der Ollama-Server? (Start mit: ollama serve)"
            ) from e
        except requests.HTTPError as e:
            raise OllamaConnectionError(
                f"Ollama-Fehler: {e.response.status_code} - {e.response.text}"
            ) from e
        except requests.RequestException as e:
            raise OllamaConnectionError(f"Anfrage fehlgeschlagen: {e}") from e
