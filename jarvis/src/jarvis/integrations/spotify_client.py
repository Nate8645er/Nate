"""Spotify Web API integration (search, playback status, player control).

Environment variables (either mode enables the integration):

* ``SPOTIFY_ACCESS_TOKEN`` -- a ready-made user access token (no refresh).
* ``SPOTIFY_CLIENT_ID`` + ``SPOTIFY_CLIENT_SECRET`` + ``SPOTIFY_REFRESH_TOKEN``
  -- OAuth refresh-token mode; access tokens are obtained and renewed
  automatically via ``https://accounts.spotify.com/api/token``.

Playback control requires a Spotify Premium account and an active device.
"""

from __future__ import annotations

import base64
import time
from typing import Any, Self

from jarvis.core.errors import IntegrationError
from jarvis.integrations.base import IntegrationClient, env

_TOKEN_URL = "https://accounts.spotify.com/api/token"
_CONTROL_ACTIONS: dict[str, tuple[str, str]] = {
    "play": ("PUT", "/me/player/play"),
    "pause": ("PUT", "/me/player/pause"),
    "next": ("POST", "/me/player/next"),
    "previous": ("POST", "/me/player/previous"),
}


class SpotifyClient(IntegrationClient):
    """Spotify Web API client (see module docstring for env vars)."""

    service = "spotify"

    def __init__(
        self,
        *,
        access_token: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
        refresh_token: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(base_url="https://api.spotify.com/v1", **kwargs)
        self._access_token = access_token
        self._client_id = client_id
        self._client_secret = client_secret
        self._refresh_token = refresh_token
        # A statically provided token is trusted indefinitely; refresh mode
        # fetches a token on first use.
        self._expires_at = float("inf") if access_token else 0.0

    @classmethod
    def from_env(cls) -> Self | None:
        access_token = env("SPOTIFY_ACCESS_TOKEN")
        client_id = env("SPOTIFY_CLIENT_ID")
        client_secret = env("SPOTIFY_CLIENT_SECRET")
        refresh_token = env("SPOTIFY_REFRESH_TOKEN")
        if access_token is None and not (client_id and client_secret and refresh_token):
            return None
        return cls(
            access_token=access_token,
            client_id=client_id,
            client_secret=client_secret,
            refresh_token=refresh_token,
        )

    # -- auth -------------------------------------------------------------------

    def _auth_headers(self) -> dict[str, str]:
        if not self._access_token:
            return {}
        return {"Authorization": f"Bearer {self._access_token}"}

    async def _ensure_token(self) -> None:
        """Refresh the access token when missing or expired."""
        if self._access_token and time.monotonic() < self._expires_at:
            return
        if not (self._client_id and self._client_secret and self._refresh_token):
            raise IntegrationError(
                "spotify: no valid access token and no refresh credentials configured"
            )
        basic = base64.b64encode(
            f"{self._client_id}:{self._client_secret}".encode()
        ).decode("ascii")
        response = await self._request(
            "POST",
            _TOKEN_URL,
            data={"grant_type": "refresh_token", "refresh_token": self._refresh_token},
            headers={"Authorization": f"Basic {basic}"},
        )
        payload = response.json()
        token = payload.get("access_token")
        if not token:
            raise IntegrationError("spotify: token refresh returned no access_token")
        self._access_token = token
        self._expires_at = time.monotonic() + float(payload.get("expires_in", 3600)) - 60

    # -- operations -------------------------------------------------------------

    async def search(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        """Search tracks and return name/artists/album/uri per hit."""
        await self._ensure_token()
        response = await self._request(
            "GET",
            "/search",
            params={"q": query, "type": "track", "limit": max(1, min(int(limit), 20))},
        )
        items = response.json().get("tracks", {}).get("items", [])
        return [
            {
                "name": track.get("name", ""),
                "artists": ", ".join(a.get("name", "") for a in track.get("artists", [])),
                "album": track.get("album", {}).get("name", ""),
                "uri": track.get("uri", ""),
            }
            for track in items
        ]

    async def now_playing(self) -> dict[str, Any]:
        """Return the currently playing track, or ``{"playing": False}``."""
        await self._ensure_token()
        response = await self._request("GET", "/me/player/currently-playing")
        if response.status_code == 204 or not response.content:
            return {"playing": False}
        payload = response.json()
        item = payload.get("item") or {}
        return {
            "playing": bool(payload.get("is_playing")),
            "track": item.get("name", ""),
            "artists": ", ".join(a.get("name", "") for a in item.get("artists", [])),
            "album": item.get("album", {}).get("name", ""),
            "progress_ms": payload.get("progress_ms"),
            "duration_ms": item.get("duration_ms"),
        }

    async def control(self, action: str) -> dict[str, Any]:
        """Control playback: one of play, pause, next, previous."""
        method_path = _CONTROL_ACTIONS.get(action)
        if method_path is None:
            valid = ", ".join(sorted(_CONTROL_ACTIONS))
            raise IntegrationError(f"spotify: unknown action '{action}' (valid: {valid})")
        await self._ensure_token()
        method, path = method_path
        await self._request(method, path)
        return {"ok": True, "action": action}

    # -- tools -------------------------------------------------------------------

    def register_tools(self, app: Any) -> None:
        self._register_tool(
            app,
            name="spotify_search",
            description="Search Spotify for tracks matching a query.",
            handler=self.search,
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "limit": {"type": "integer", "default": 5, "minimum": 1, "maximum": 20},
                },
                "required": ["query"],
            },
        )
        self._register_tool(
            app,
            name="spotify_now_playing",
            description="Show the track currently playing on the user's Spotify account.",
            handler=self.now_playing,
        )
        self._register_tool(
            app,
            name="spotify_control",
            description="Control Spotify playback on the active device.",
            handler=self.control,
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["play", "pause", "next", "previous"],
                    }
                },
                "required": ["action"],
            },
            capability="integrations.send",
        )
