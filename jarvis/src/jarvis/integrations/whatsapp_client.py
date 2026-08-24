"""WhatsApp integration via the WhatsApp Business Cloud API.

Environment variables:

* ``WHATSAPP_TOKEN`` -- Meta Cloud API access token (required).
* ``WHATSAPP_PHONE_ID`` -- the business phone number id used as sender
  (required).

Scope note: this integration uses only the official Meta Graph API for
WhatsApp Business. Automating a personal account by scraping WhatsApp Web
is against WhatsApp's terms of service and deliberately out of scope.
"""

from __future__ import annotations

from typing import Any, Self

from jarvis.integrations.base import IntegrationClient, env


class WhatsAppClient(IntegrationClient):
    """WhatsApp Business Cloud API client (see module docstring for env vars)."""

    service = "whatsapp"

    def __init__(self, token: str, phone_id: str, **kwargs: Any) -> None:
        super().__init__(base_url="https://graph.facebook.com/v19.0", token=token, **kwargs)
        self.phone_id = phone_id

    @classmethod
    def from_env(cls) -> Self | None:
        token = env("WHATSAPP_TOKEN")
        phone_id = env("WHATSAPP_PHONE_ID")
        if token is None or phone_id is None:
            return None
        return cls(token, phone_id)

    # -- operations ------------------------------------------------------------

    async def send(self, to: str, text: str) -> dict[str, Any]:
        """Send a text message to the phone number *to* (E.164, digits only)."""
        response = await self._request(
            "POST",
            f"/{self.phone_id}/messages",
            json={
                "messaging_product": "whatsapp",
                "to": to,
                "type": "text",
                "text": {"body": text},
            },
        )
        payload = response.json()
        messages = payload.get("messages", [])
        return {
            "sent": True,
            "to": to,
            "message_id": messages[0].get("id") if messages else None,
        }

    # -- tools ---------------------------------------------------------------------

    def register_tools(self, app: Any) -> None:
        self._register_tool(
            app,
            name="whatsapp_send",
            description="Send a WhatsApp text message via the Business Cloud API.",
            handler=self.send,
            parameters={
                "type": "object",
                "properties": {
                    "to": {
                        "type": "string",
                        "description": "Recipient phone number in E.164 format",
                    },
                    "text": {"type": "string"},
                },
                "required": ["to", "text"],
            },
            capability="integrations.send",
        )
