"""Third-party service integrations subsystem.

Exposes the ``register(app)`` hook consumed by :class:`jarvis.app.JarvisApp`.
Each integration is a small async client over a public REST API (or SMTP/
IMAP), configured purely through environment variables. Tools are only
registered for integrations whose required environment variables are present,
so a bare install exposes no broken tools. ``register`` never raises: every
integration is guarded individually and failures are logged.

The always-available ``integrations_status`` tool reports which integrations
are configured (environment variable *names* only, never their values).
"""

from __future__ import annotations

import os
from typing import Any

from jarvis.core.logging import get_logger
from jarvis.integrations.base import IntegrationClient, register_tool
from jarvis.integrations.calendar_client import GoogleCalendarClient, LocalCalendarClient
from jarvis.integrations.discord_client import DiscordClient
from jarvis.integrations.email_client import EmailClient
from jarvis.integrations.gdrive_client import GoogleDriveClient
from jarvis.integrations.github_client import GitHubClient
from jarvis.integrations.notion_client import NotionClient
from jarvis.integrations.onedrive_client import OneDriveClient
from jarvis.integrations.spotify_client import SpotifyClient
from jarvis.integrations.telegram_client import TelegramClient
from jarvis.integrations.whatsapp_client import WhatsAppClient

logger = get_logger("integrations")

# Client classes with a ``from_env()`` factory, tried in registration order.
_CLIENT_CLASSES: list[type[IntegrationClient]] = [
    EmailClient,
    GoogleCalendarClient,
    SpotifyClient,
    DiscordClient,
    TelegramClient,
    GitHubClient,
    NotionClient,
    GoogleDriveClient,
    OneDriveClient,
    WhatsAppClient,
]

# service -> alternative groups of env vars; configured when ANY group is
# fully present. An empty list means "always available" (no env needed).
_SERVICE_ENV: dict[str, list[list[str]]] = {
    "calendar": [],
    "email": [["EMAIL_SMTP_HOST"], ["EMAIL_IMAP_HOST"]],
    "gcal": [["GOOGLE_OAUTH_TOKEN"]],
    "spotify": [
        ["SPOTIFY_ACCESS_TOKEN"],
        ["SPOTIFY_CLIENT_ID", "SPOTIFY_CLIENT_SECRET", "SPOTIFY_REFRESH_TOKEN"],
    ],
    "discord": [["DISCORD_WEBHOOK_URL"], ["DISCORD_BOT_TOKEN"]],
    "telegram": [["TELEGRAM_BOT_TOKEN"]],
    "github": [["GITHUB_TOKEN"]],
    "notion": [["NOTION_TOKEN"]],
    "gdrive": [["GOOGLE_OAUTH_TOKEN"]],
    "onedrive": [["MSGRAPH_ACCESS_TOKEN"]],
    "whatsapp": [["WHATSAPP_TOKEN", "WHATSAPP_PHONE_ID"]],
}


def integrations_status() -> dict[str, Any]:
    """Report which integrations are configured, by env var *names* only."""
    report: dict[str, Any] = {}
    for service, groups in sorted(_SERVICE_ENV.items()):
        configured = not groups or any(
            all(os.environ.get(var, "").strip() for var in group) for group in groups
        )
        report[service] = {
            "configured": configured,
            "required_env": [" + ".join(group) for group in groups] or ["(none, always on)"],
        }
    return report


def _register_status_tool(app: Any) -> None:
    register_tool(
        app,
        name="integrations_status",
        description=(
            "Show which service integrations are configured and which environment "
            "variables would enable the rest (names only, no secret values)."
        ),
        handler=integrations_status,
        service="status",
    )


def register(app: Any) -> None:
    """Register all configured integrations on the app. Never raises."""
    try:
        _register_status_tool(app)
    except Exception:
        logger.exception("Failed to register integrations_status tool")

    # Local ICS calendar: needs no env vars, lives in the app data directory.
    try:
        LocalCalendarClient(app.config.data_dir / "calendar.ics").register_tools(app)
    except Exception:
        logger.exception("Local calendar integration failed to register")

    for client_class in _CLIENT_CLASSES:
        name = client_class.service
        try:
            client = client_class.from_env()
            if client is None:
                logger.debug("Integration '%s' not configured; skipping", name)
                continue
            client.register_tools(app)
            container = getattr(app, "container", None)
            if container is not None:
                container.on_close(client.aclose)
            logger.info("Integration '%s' registered", name)
        except Exception:
            logger.exception("Integration '%s' failed to register", name)
