"""Client für die Verbindung zu einem lokalen Ollama-Server."""

import logging

import requests

logger = logging.getLogger("jarvis.ollama")


class OllamaConnectionError(Exception):
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

    def chat(self, prompt: str) -> str:
        """Sendet eine Nachricht an das Modell und gibt die Antwort zurück."""
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        }
        try:
            logger.info("Sende Anfrage an Modell '%s' ...", self.model)
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            answer = response.json()["message"]["content"]
            logger.info("Antwort erhalten (%d Zeichen).", len(answer))
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
