"""Notion API integration (search, read page text, create pages).

Environment variables:

* ``NOTION_TOKEN`` -- internal integration token (required). The integration
  must be shared with the pages it should see.
* ``NOTION_PARENT_PAGE_ID`` -- default parent page for ``notion_create_page``
  when the tool call does not specify one (optional).

Uses Notion API version ``2022-06-28``.
"""

from __future__ import annotations

from typing import Any, Self

from jarvis.core.errors import IntegrationError
from jarvis.integrations.base import IntegrationClient, env, truncate

NOTION_VERSION = "2022-06-28"


def _plain_text(rich_text: list[dict[str, Any]]) -> str:
    return "".join(part.get("plain_text", "") for part in rich_text)


def _result_title(result: dict[str, Any]) -> str:
    """Extract a human title from a search result (page or database)."""
    for prop in result.get("properties", {}).values():
        if prop.get("type") == "title":
            return _plain_text(prop.get("title", []))
    return _plain_text(result.get("title", []))


class NotionClient(IntegrationClient):
    """Notion REST client (see module docstring for env vars)."""

    service = "notion"

    def __init__(
        self, token: str, *, default_parent_page_id: str | None = None, **kwargs: Any
    ) -> None:
        super().__init__(
            base_url="https://api.notion.com/v1",
            token=token,
            headers={"Notion-Version": NOTION_VERSION},
            **kwargs,
        )
        self.default_parent_page_id = default_parent_page_id

    @classmethod
    def from_env(cls) -> Self | None:
        token = env("NOTION_TOKEN")
        if token is None:
            return None
        return cls(token, default_parent_page_id=env("NOTION_PARENT_PAGE_ID"))

    # -- operations ------------------------------------------------------------

    async def search(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """Search pages and databases shared with the integration."""
        response = await self._request(
            "POST",
            "/search",
            json={"query": query, "page_size": max(1, min(int(limit), 50))},
        )
        return [
            {
                "id": result.get("id", ""),
                "object": result.get("object", ""),
                "title": _result_title(result),
                "url": result.get("url", ""),
            }
            for result in response.json().get("results", [])
        ]

    async def read_page(self, page_id: str) -> dict[str, Any]:
        """Read a page's block children and flatten them to plain text."""
        response = await self._request(
            "GET", f"/blocks/{page_id}/children", params={"page_size": 100}
        )
        lines: list[str] = []
        for block in response.json().get("results", []):
            block_type = block.get("type", "")
            payload = block.get(block_type, {})
            text = _plain_text(payload.get("rich_text", []))
            if text:
                lines.append(text)
        return {"page_id": page_id, "text": truncate("\n".join(lines))}

    async def create_page(
        self, title: str, content: str = "", parent_page_id: str | None = None
    ) -> dict[str, Any]:
        """Create a page under a parent page (default: ``NOTION_PARENT_PAGE_ID``)."""
        parent = parent_page_id or self.default_parent_page_id
        if not parent:
            raise IntegrationError(
                "notion: no parent_page_id given and NOTION_PARENT_PAGE_ID is not configured"
            )
        children = [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": paragraph}}]},
            }
            for paragraph in content.split("\n")
            if paragraph.strip()
        ]
        response = await self._request(
            "POST",
            "/pages",
            json={
                "parent": {"page_id": parent},
                "properties": {
                    "title": {"title": [{"type": "text", "text": {"content": title}}]}
                },
                "children": children,
            },
        )
        created = response.json()
        return {"id": created.get("id", ""), "url": created.get("url", ""), "title": title}

    # -- tools ---------------------------------------------------------------------

    def register_tools(self, app: Any) -> None:
        self._register_tool(
            app,
            name="notion_search",
            description="Search Notion pages and databases by text query.",
            handler=self.search,
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "limit": {"type": "integer", "default": 10, "minimum": 1, "maximum": 50},
                },
                "required": ["query"],
            },
        )
        self._register_tool(
            app,
            name="notion_read_page",
            description="Read a Notion page's content as plain text.",
            handler=self.read_page,
            parameters={
                "type": "object",
                "properties": {"page_id": {"type": "string"}},
                "required": ["page_id"],
            },
        )
        self._register_tool(
            app,
            name="notion_create_page",
            description="Create a Notion page with paragraphs under a parent page.",
            handler=self.create_page,
            parameters={
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "content": {"type": "string", "description": "Plain text body"},
                    "parent_page_id": {
                        "type": "string",
                        "description": "Optional parent page id (defaults to NOTION_PARENT_PAGE_ID)",
                    },
                },
                "required": ["title"],
            },
            capability="integrations.send",
        )
