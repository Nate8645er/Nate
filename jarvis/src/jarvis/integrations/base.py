"""Shared plumbing for third-party service integrations.

Every integration is a small async client over a public REST API (or a
stdlib protocol such as SMTP/IMAP). This module provides the common parts:

* a lazily created :class:`httpx.AsyncClient` with a 30 second timeout,
* :meth:`IntegrationClient._request` with uniform error wrapping into
  :class:`~jarvis.core.errors.IntegrationError`,
* bearer/token authorization header support,
* output truncation helpers so tool results never flood the model context.

Clients are configured exclusively through environment variables (documented
per client class) and register their tools only when configured, so a bare
install never exposes broken tools.
"""

from __future__ import annotations

import json
import os
from typing import Any, Self

import httpx

from jarvis.core.errors import IntegrationError
from jarvis.core.logging import get_logger

logger = get_logger("integrations")

DEFAULT_TIMEOUT_SECONDS = 30.0
MAX_OUTPUT_CHARS = 6000


def env(name: str) -> str | None:
    """Return a non-empty environment variable value, else ``None``."""
    value = os.environ.get(name, "").strip()
    return value or None


def has_env(*names: str) -> bool:
    """True when every named environment variable is set and non-empty."""
    return all(env(name) is not None for name in names)


def truncate(text: str, limit: int = MAX_OUTPUT_CHARS) -> str:
    """Clamp *text* to *limit* characters, appending a truncation marker."""
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n... [truncated {len(text) - limit} chars]"


def truncate_json(data: Any, limit: int = MAX_OUTPUT_CHARS) -> str:
    """Serialize *data* as JSON and clamp it for tool output."""
    try:
        text = json.dumps(data, ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        text = str(data)
    return truncate(text, limit)


def register_tool(
    app: Any,
    *,
    name: str,
    description: str,
    handler: Any,
    parameters: dict[str, Any] | None = None,
    service: str,
    capability: str | None = None,
) -> None:
    """Register *handler* on the app's tool registry with integration tags."""
    app.tools.register_function(
        name,
        description,
        handler,
        parameters=parameters or {"type": "object", "properties": {}},
        tags={"integrations", service},
        capability=capability,
        source="integrations",
    )


class IntegrationClient:
    """Base class for async REST integration clients.

    Subclasses set :attr:`service` (used as tool tag and in error messages),
    pass connection details to ``__init__`` and implement
    :meth:`register_tools` plus :meth:`from_env`.
    """

    service: str = "integration"

    def __init__(
        self,
        *,
        base_url: str = "",
        token: str | None = None,
        auth_scheme: str = "Bearer",
        headers: dict[str, str] | None = None,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._base_url = base_url
        self._token = token
        self._auth_scheme = auth_scheme
        self._headers = dict(headers or {})
        self._timeout = timeout
        self._transport = transport
        self._client: httpx.AsyncClient | None = None

    # -- construction -----------------------------------------------------

    @classmethod
    def from_env(cls) -> Self | None:
        """Build the client from environment variables, or ``None`` if unset."""
        raise NotImplementedError

    # -- HTTP helpers -------------------------------------------------------

    @property
    def client(self) -> httpx.AsyncClient:
        """The shared async HTTP client, created on first use."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self._timeout,
                follow_redirects=True,
                transport=self._transport,
            )
        return self._client

    def _auth_headers(self) -> dict[str, str]:
        """Authorization header derived from the configured token, if any."""
        if not self._token:
            return {}
        return {"Authorization": f"{self._auth_scheme} {self._token}"}

    def _url(self, url: str) -> str:
        if url.startswith(("http://", "https://")):
            return url
        return self._base_url.rstrip("/") + "/" + url.lstrip("/")

    async def _request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str | None] | None = None,
        allowed_statuses: tuple[int, ...] = (),
        **kwargs: Any,
    ) -> httpx.Response:
        """Send a request, wrapping transport and HTTP errors.

        Per-call *headers* override the client defaults; a ``None`` value
        removes a default header. Raises :class:`IntegrationError` on
        connection failures and on any status >= 400 that is not listed in
        *allowed_statuses*.
        """
        combined: dict[str, str | None] = {
            **self._headers,
            **self._auth_headers(),
            **(headers or {}),
        }
        merged = {key: value for key, value in combined.items() if value is not None}
        full_url = self._url(url)
        try:
            response = await self.client.request(method, full_url, headers=merged, **kwargs)
        except httpx.HTTPError as exc:
            raise IntegrationError(
                f"{self.service}: request to {full_url} failed: {exc}", cause=exc
            ) from exc
        if response.status_code >= 400 and response.status_code not in allowed_statuses:
            detail = response.text[:300]
            raise IntegrationError(
                f"{self.service}: HTTP {response.status_code} for {method} {full_url}: {detail}"
            )
        return response

    async def aclose(self) -> None:
        """Dispose of the underlying HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    # -- tool registration ---------------------------------------------------

    def register_tools(self, app: Any) -> None:
        """Register this integration's tools on the app registry."""
        raise NotImplementedError

    def _register_tool(
        self,
        app: Any,
        *,
        name: str,
        description: str,
        handler: Any,
        parameters: dict[str, Any] | None = None,
        capability: str | None = None,
    ) -> None:
        register_tool(
            app,
            name=name,
            description=description,
            handler=handler,
            parameters=parameters,
            service=self.service,
            capability=capability,
        )
