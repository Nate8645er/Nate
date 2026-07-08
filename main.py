"""Jarvis - Einstiegspunkt.

Schritt 1: Verbindung zu Ollama herstellen und eine Testfrage senden.
"""

import sys

from jarvis.core.ollama_client import OllamaClient, OllamaConnectionError
from jarvis.utils.config_loader import load_config
from jarvis.utils.logger import setup_logger


def main() -> int:
    try:
        config = load_config()
    except (FileNotFoundError, ValueError) as e:
        print(f"FEHLER: {e}")
        return 1

    logger = setup_logger("jarvis", config)
    logger.info("Jarvis startet (Schritt 1: Ollama-Verbindungstest) ...")

    ollama_cfg = config["ollama"]
    client = OllamaClient(
        base_url=ollama_cfg["base_url"],
        model=ollama_cfg["model"],
        timeout=ollama_cfg.get("timeout_seconds", 120),
    )

    if not client.is_available():
        logger.error(
            "Ollama ist unter %s nicht erreichbar. "
            "Bitte Ollama starten (z.B. 'ollama serve' oder die Ollama-App öffnen).",
            ollama_cfg["base_url"],
        )
        return 1

    logger.info("Ollama-Server erreichbar.")

    try:
        models = client.list_models()
        logger.info("Installierte Modelle: %s", ", ".join(models) or "keine")
        if not any(m.startswith(client.model) for m in models):
            logger.warning(
                "Modell '%s' scheint nicht installiert zu sein. "
                "Installation mit: ollama pull %s",
                client.model,
                client.model,
            )

        frage = "Antworte in einem Satz: Wer bist du?"
        print(f"\nTestfrage an {client.model}: {frage}")
        antwort = client.chat(frage)
        print(f"\nAntwort:\n{antwort}\n")
        logger.info("Verbindungstest erfolgreich abgeschlossen.")
        return 0
    except OllamaConnectionError as e:
        logger.error("%s", e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
