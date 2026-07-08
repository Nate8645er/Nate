"""Gesprächslogik mit Kurzzeitgedächtnis (Verlauf der aktuellen Sitzung)."""

import logging

from jarvis.core.ollama_client import OllamaClient

logger = logging.getLogger("jarvis.conversation")


class ConversationManager:
    """Verwaltet den Gesprächsverlauf und spricht mit dem Modell.

    Das Kurzzeitgedächtnis ist der Nachrichtenverlauf der laufenden Sitzung.
    Damit der Kontext nicht unbegrenzt wächst, werden bei Überschreitung von
    `max_history_messages` die ältesten Nachrichten (nach dem System-Prompt)
    entfernt.
    """

    def __init__(
        self,
        client: OllamaClient,
        system_prompt: str,
        max_history_messages: int = 20,
    ):
        self.client = client
        self.max_history_messages = max_history_messages
        self.messages: list[dict] = [
            {"role": "system", "content": system_prompt}
        ]

    def ask(self, user_input: str) -> str:
        """Fügt die Nutzereingabe zum Verlauf hinzu und holt die Antwort."""
        self.messages.append({"role": "user", "content": user_input})
        self._trim_history()
        answer = self.client.chat(messages=self.messages)
        self.messages.append({"role": "assistant", "content": answer})
        return answer

    def reset(self) -> None:
        """Löscht das Kurzzeitgedächtnis (behält den System-Prompt)."""
        self.messages = self.messages[:1]
        logger.info("Gesprächsverlauf zurückgesetzt.")

    def _trim_history(self) -> None:
        """Kürzt den Verlauf auf max_history_messages (System-Prompt bleibt)."""
        # +1, weil der System-Prompt nicht mitgezählt wird
        while len(self.messages) > self.max_history_messages + 1:
            removed = self.messages.pop(1)
            logger.debug(
                "Älteste Nachricht aus dem Verlauf entfernt (%s).",
                removed["role"],
            )
