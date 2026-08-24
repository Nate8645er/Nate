"""Telegram Bot API integration (send messages, poll updates).

Environment variables:

* ``TELEGRAM_BOT_TOKEN`` -- bot token from @BotFather (required).
* ``TELEGRAM_CHAT_ID`` -- default chat id for ``telegram_send`` when the
  tool call does not specify one (optional).
"""

from __future__ import annotations

from typing import Any, Self

from jarvis.core.errors import IntegrationError
from jarvis.integrations.base import IntegrationClient, env, truncate


class TelegramClient(IntegrationClient):
    """Telegram Bot API client (see module docstring for env vars)."""

    service = "telegram"

    def __init__(
        self, *, token: str, default_chat_id: str | None = None, **kwargs: Any
    ) -> None:
        # The bot token is part of the URL path, not an Authorization header.
        super().__init__(base_url=f"https://api.telegram.org/bot{token}", **kwargs)
        self.default_chat_id = default_chat_id

    @classmethod
    def from_env(cls) -> Self | None:
        token = env("TELEGRAM_BOT_TOKEN")
        if token is None:
            return None
        return cls(token=token, default_chat_id=env("TELEGRAM_CHAT_ID"))

    # -- operations -----------------------------------------------------------

    async def send_message(self, text: str, chat_id: str | None = None) -> dict[str, Any]:
        """Send a text message to *chat_id* (defaults to ``TELEGRAM_CHAT_ID``)."""
        target = chat_id or self.default_chat_id
        if not target:
            raise IntegrationError(
                "telegram: no chat_id given and TELEGRAM_CHAT_ID is not configured"
            )
        response = await self._request(
            "POST", "/sendMessage", json={"chat_id": target, "text": text}
        )
        payload = response.json()
        if not payload.get("ok"):
            raise IntegrationError(f"telegram: sendMessage failed: {payload}")
        return {
            "sent": True,
            "chat_id": target,
            "message_id": payload.get("result", {}).get("message_id"),
        }

    async def get_updates(self, limit: int = 10) -> list[dict[str, Any]]:
        """Return the latest *limit* bot updates (messages sent to the bot)."""
        response = await self._request("GET", "/getUpdates")
        payload = response.json()
        if not payload.get("ok"):
            raise IntegrationError(f"telegram: getUpdates failed: {payload}")
        updates = payload.get("result", [])[-max(1, min(int(limit), 100)) :]
        results: list[dict[str, Any]] = []
        for update in updates:
            message = update.get("message") or update.get("edited_message") or {}
            results.append(
                {
                    "update_id": update.get("update_id"),
                    "chat_id": message.get("chat", {}).get("id"),
                    "from": message.get("from", {}).get("username", ""),
                    "text": truncate(message.get("text", ""), 500),
                    "date": message.get("date"),
                }
            )
        return results

    # -- tools -------------------------------------------------------------------

    def register_tools(self, app: Any) -> None:
        self._register_tool(
            app,
            name="telegram_send",
            description="Send a Telegram message via the configured bot.",
            handler=self.send_message,
            parameters={
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "chat_id": {
                        "type": "string",
                        "description": "Optional chat id (defaults to TELEGRAM_CHAT_ID)",
                    },
                },
                "required": ["text"],
            },
            capability="integrations.send",
        )
        self._register_tool(
            app,
            name="telegram_updates",
            description="Fetch the latest messages sent to the Telegram bot.",
            handler=self.get_updates,
            parameters={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "default": 10, "minimum": 1, "maximum": 100}
                },
            },
        )
