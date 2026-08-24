"""Discord integration via webhook and/or bot token.

Environment variables (either one enables the integration):

* ``DISCORD_WEBHOOK_URL`` -- incoming webhook URL; enables ``discord_send``
  to the webhook's channel.
* ``DISCORD_BOT_TOKEN`` -- bot token; enables sending to arbitrary channels
  and ``discord_read_channel`` (reading requires the bot, not the webhook).
"""

from __future__ import annotations

from typing import Any, Self

from jarvis.core.errors import IntegrationError
from jarvis.integrations.base import IntegrationClient, env, truncate

_API_BASE = "https://discord.com/api/v10"


class DiscordClient(IntegrationClient):
    """Discord webhook/bot client (see module docstring for env vars)."""

    service = "discord"

    def __init__(
        self,
        *,
        webhook_url: str | None = None,
        bot_token: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(base_url=_API_BASE, token=bot_token, auth_scheme="Bot", **kwargs)
        self.webhook_url = webhook_url
        self._bot_token = bot_token

    @classmethod
    def from_env(cls) -> Self | None:
        webhook_url = env("DISCORD_WEBHOOK_URL")
        bot_token = env("DISCORD_BOT_TOKEN")
        if webhook_url is None and bot_token is None:
            return None
        return cls(webhook_url=webhook_url, bot_token=bot_token)

    # -- operations ---------------------------------------------------------------

    async def send(self, content: str, channel_id: str | None = None) -> dict[str, Any]:
        """Send a message to a channel (bot) or to the configured webhook."""
        if channel_id:
            if not self._bot_token:
                raise IntegrationError(
                    "discord: sending to a channel id requires DISCORD_BOT_TOKEN"
                )
            response = await self._request(
                "POST", f"/channels/{channel_id}/messages", json={"content": content}
            )
            message = response.json()
            return {"sent": True, "channel_id": channel_id, "message_id": message.get("id")}
        if not self.webhook_url:
            raise IntegrationError(
                "discord: no channel_id given and DISCORD_WEBHOOK_URL is not configured"
            )
        # Webhooks authenticate through the URL itself; suppress the bot header.
        await self._request(
            "POST", self.webhook_url, json={"content": content}, headers={"Authorization": None}
        )
        return {"sent": True, "via": "webhook"}

    async def read_channel(self, channel_id: str, limit: int = 10) -> list[dict[str, Any]]:
        """Read the latest messages of a channel (requires the bot token)."""
        if not self._bot_token:
            raise IntegrationError("discord: reading channels requires DISCORD_BOT_TOKEN")
        response = await self._request(
            "GET",
            f"/channels/{channel_id}/messages",
            params={"limit": max(1, min(int(limit), 50))},
        )
        return [
            {
                "id": message.get("id"),
                "author": message.get("author", {}).get("username", ""),
                "content": truncate(message.get("content", ""), 500),
                "timestamp": message.get("timestamp", ""),
            }
            for message in response.json()
        ]

    # -- tools -----------------------------------------------------------------------

    def register_tools(self, app: Any) -> None:
        self._register_tool(
            app,
            name="discord_send",
            description=(
                "Send a Discord message. Provide channel_id to use the bot; "
                "omit it to post to the configured webhook."
            ),
            handler=self.send,
            parameters={
                "type": "object",
                "properties": {
                    "content": {"type": "string"},
                    "channel_id": {"type": "string", "description": "Optional channel id"},
                },
                "required": ["content"],
            },
            capability="integrations.send",
        )
        if self._bot_token:
            self._register_tool(
                app,
                name="discord_read_channel",
                description="Read the latest messages from a Discord channel (bot token).",
                handler=self.read_channel,
                parameters={
                    "type": "object",
                    "properties": {
                        "channel_id": {"type": "string"},
                        "limit": {"type": "integer", "default": 10, "minimum": 1, "maximum": 50},
                    },
                    "required": ["channel_id"],
                },
            )
