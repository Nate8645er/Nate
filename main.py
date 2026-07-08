"""Jarvis - Einstiegspunkt.

Schritt 2: Interaktiver Gesprächsmodus mit Kurzzeitgedächtnis.
Befehle im Chat:
  /neu     - Gesprächsverlauf zurücksetzen
  /exit    - Jarvis beenden (auch: /quit, exit, quit)
"""

import sys

from jarvis.core.conversation import ConversationManager
from jarvis.core.ollama_client import OllamaClient, OllamaConnectionError
from jarvis.utils.config_loader import load_config
from jarvis.utils.logger import setup_logger

EXIT_COMMANDS = {"/exit", "/quit", "exit", "quit"}


def build_client(config: dict) -> OllamaClient:
    ollama_cfg = config["ollama"]
    return OllamaClient(
        base_url=ollama_cfg["base_url"],
        model=ollama_cfg["model"],
        timeout=ollama_cfg.get("timeout_seconds", 120),
    )


def chat_loop(conversation: ConversationManager, logger) -> None:
    """Liest Nutzereingaben und gibt die Antworten des Modells aus."""
    print("\nJarvis ist bereit. Schreib mir etwas!")
    print("Befehle: /neu (Verlauf löschen), /exit (beenden)\n")

    while True:
        try:
            user_input = input("Du: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBis bald!")
            return

        if not user_input:
            continue
        if user_input.lower() in EXIT_COMMANDS:
            print("Bis bald!")
            return
        if user_input.lower() == "/neu":
            conversation.reset()
            print("(Verlauf gelöscht - wir fangen von vorne an.)\n")
            continue

        try:
            answer = conversation.ask(user_input)
            print(f"\nJarvis: {answer}\n")
        except OllamaConnectionError as e:
            logger.error("%s", e)
            print("(Verbindungsproblem - versuch es gleich nochmal.)\n")


def main() -> int:
    try:
        config = load_config()
    except (FileNotFoundError, ValueError) as e:
        print(f"FEHLER: {e}")
        return 1

    logger = setup_logger("jarvis", config)
    logger.info("Jarvis startet (Schritt 2: Gesprächsmodus) ...")

    client = build_client(config)

    if not client.is_available():
        logger.error(
            "Ollama ist unter %s nicht erreichbar. "
            "Bitte Ollama starten (z.B. 'ollama serve' oder die Ollama-App öffnen).",
            config["ollama"]["base_url"],
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
    except OllamaConnectionError as e:
        logger.error("%s", e)
        return 1

    assistant_cfg = config.get("assistant", {})
    conversation = ConversationManager(
        client=client,
        system_prompt=assistant_cfg.get(
            "system_prompt", "Du bist ein hilfsbereiter Assistent."
        ),
        max_history_messages=assistant_cfg.get("max_history_messages", 20),
    )

    chat_loop(conversation, logger)
    logger.info("Jarvis beendet.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
