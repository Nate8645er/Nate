"""Google Drive REST integration (search, read text files, upload text).

Environment variables:

* ``GOOGLE_OAUTH_TOKEN`` -- OAuth2 access token with Drive scope
  (``https://www.googleapis.com/auth/drive`` or narrower).

Only text content is handled: downloads are decoded as UTF-8 (with
replacement) and truncated; uploads create plain-text files via the
``multipart/related`` upload endpoint built with the standard library.
"""

from __future__ import annotations

import json
import uuid
from typing import Any, Self

from jarvis.integrations.base import IntegrationClient, env, truncate

_UPLOAD_URL = "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart"


class GoogleDriveClient(IntegrationClient):
    """Google Drive v3 client (see module docstring for env vars)."""

    service = "gdrive"

    def __init__(self, token: str, **kwargs: Any) -> None:
        super().__init__(
            base_url="https://www.googleapis.com/drive/v3", token=token, **kwargs
        )

    @classmethod
    def from_env(cls) -> Self | None:
        token = env("GOOGLE_OAUTH_TOKEN")
        return cls(token) if token else None

    # -- operations ------------------------------------------------------------

    async def search(self, query: str = "", limit: int = 10) -> list[dict[str, Any]]:
        """List files; *query* filters by name (``name contains ...``)."""
        params: dict[str, str] = {
            "pageSize": str(max(1, min(int(limit), 50))),
            "fields": "files(id,name,mimeType,modifiedTime,size)",
        }
        if query:
            escaped = query.replace("\\", "\\\\").replace("'", "\\'")
            params["q"] = f"name contains '{escaped}' and trashed = false"
        else:
            params["q"] = "trashed = false"
        response = await self._request("GET", "/files", params=params)
        return [
            {
                "id": item.get("id", ""),
                "name": item.get("name", ""),
                "mimeType": item.get("mimeType", ""),
                "modifiedTime": item.get("modifiedTime", ""),
                "size": item.get("size"),
            }
            for item in response.json().get("files", [])
        ]

    async def read(self, file_id: str) -> dict[str, Any]:
        """Download a file's raw content, decoded as UTF-8 text and truncated."""
        response = await self._request("GET", f"/files/{file_id}", params={"alt": "media"})
        text = response.content.decode("utf-8", "replace")
        return {"id": file_id, "content": truncate(text)}

    async def upload(self, name: str, content: str) -> dict[str, Any]:
        """Create a plain-text file named *name* with *content*."""
        boundary = uuid.uuid4().hex
        metadata = json.dumps({"name": name, "mimeType": "text/plain"})
        body = (
            f"--{boundary}\r\n"
            "Content-Type: application/json; charset=UTF-8\r\n\r\n"
            f"{metadata}\r\n"
            f"--{boundary}\r\n"
            "Content-Type: text/plain; charset=UTF-8\r\n\r\n"
            f"{content}\r\n"
            f"--{boundary}--\r\n"
        ).encode()
        response = await self._request(
            "POST",
            _UPLOAD_URL,
            content=body,
            headers={"Content-Type": f"multipart/related; boundary={boundary}"},
        )
        created = response.json()
        return {"id": created.get("id", ""), "name": created.get("name", name)}

    # -- tools ---------------------------------------------------------------------

    def register_tools(self, app: Any) -> None:
        self._register_tool(
            app,
            name="gdrive_search",
            description="Search Google Drive files by name (empty query lists recent files).",
            handler=self.search,
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Name fragment to match"},
                    "limit": {"type": "integer", "default": 10, "minimum": 1, "maximum": 50},
                },
            },
        )
        self._register_tool(
            app,
            name="gdrive_read",
            description="Download a Google Drive file's content as text (truncated).",
            handler=self.read,
            parameters={
                "type": "object",
                "properties": {"file_id": {"type": "string"}},
                "required": ["file_id"],
            },
        )
        self._register_tool(
            app,
            name="gdrive_upload",
            description="Upload a plain-text file to Google Drive.",
            handler=self.upload,
            parameters={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "File name in Drive"},
                    "content": {"type": "string"},
                },
                "required": ["name", "content"],
            },
            capability="integrations.send",
        )
