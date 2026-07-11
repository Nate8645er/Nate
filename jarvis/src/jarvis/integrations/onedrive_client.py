"""Microsoft OneDrive integration via the Microsoft Graph API.

Environment variables:

* ``MSGRAPH_ACCESS_TOKEN`` -- Microsoft Graph OAuth2 access token with
  ``Files.ReadWrite`` (or at least ``Files.Read``) scope.

Only text content is handled: downloads are decoded as UTF-8 (with
replacement) and truncated; uploads use the small-file ``PUT /content``
endpoint (max ~4 MB).
"""

from __future__ import annotations

from typing import Any, Self
from urllib.parse import quote

from jarvis.integrations.base import IntegrationClient, env, truncate


class OneDriveClient(IntegrationClient):
    """Microsoft Graph drive client (see module docstring for env vars)."""

    service = "onedrive"

    def __init__(self, token: str, **kwargs: Any) -> None:
        super().__init__(base_url="https://graph.microsoft.com/v1.0", token=token, **kwargs)

    @classmethod
    def from_env(cls) -> Self | None:
        token = env("MSGRAPH_ACCESS_TOKEN")
        return cls(token) if token else None

    # -- operations -------------------------------------------------------------

    async def list_files(self, query: str = "", limit: int = 10) -> list[dict[str, Any]]:
        """List root children, or search the drive when *query* is given."""
        top = max(1, min(int(limit), 50))
        if query:
            url = f"/me/drive/root/search(q='{quote(query)}')"
        else:
            url = "/me/drive/root/children"
        response = await self._request("GET", url, params={"$top": str(top)})
        return [
            {
                "id": item.get("id", ""),
                "name": item.get("name", ""),
                "is_folder": "folder" in item,
                "size": item.get("size"),
                "modified": item.get("lastModifiedDateTime", ""),
            }
            for item in response.json().get("value", [])[:top]
        ]

    async def read(self, item_id: str) -> dict[str, Any]:
        """Download a drive item's content as UTF-8 text (truncated)."""
        response = await self._request("GET", f"/me/drive/items/{item_id}/content")
        text = response.content.decode("utf-8", "replace")
        return {"id": item_id, "content": truncate(text)}

    async def upload(self, name: str, content: str) -> dict[str, Any]:
        """Upload a small text file named *name* into the drive root."""
        response = await self._request(
            "PUT",
            f"/me/drive/root:/{quote(name)}:/content",
            content=content.encode("utf-8"),
            headers={"Content-Type": "text/plain; charset=UTF-8"},
        )
        created = response.json()
        return {
            "id": created.get("id", ""),
            "name": created.get("name", name),
            "webUrl": created.get("webUrl", ""),
        }

    # -- tools --------------------------------------------------------------------

    def register_tools(self, app: Any) -> None:
        self._register_tool(
            app,
            name="onedrive_list",
            description="List OneDrive root files or search the drive by query.",
            handler=self.list_files,
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Optional search text"},
                    "limit": {"type": "integer", "default": 10, "minimum": 1, "maximum": 50},
                },
            },
        )
        self._register_tool(
            app,
            name="onedrive_read",
            description="Download a OneDrive file's content as text (truncated).",
            handler=self.read,
            parameters={
                "type": "object",
                "properties": {"item_id": {"type": "string"}},
                "required": ["item_id"],
            },
        )
        self._register_tool(
            app,
            name="onedrive_upload",
            description="Upload a small plain-text file to the OneDrive root folder.",
            handler=self.upload,
            parameters={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "File name in OneDrive"},
                    "content": {"type": "string"},
                },
                "required": ["name", "content"],
            },
            capability="integrations.send",
        )
