"""GitHub REST API integration (notifications, issues/PRs, repo info).

Environment variables:

* ``GITHUB_TOKEN`` -- personal access token or fine-grained token
  (``repo`` / ``notifications`` scopes as needed).
"""

from __future__ import annotations

from typing import Any, Self

from jarvis.core.errors import IntegrationError
from jarvis.integrations.base import IntegrationClient, env, truncate


def _validate_repo(repo: str) -> str:
    repo = repo.strip().strip("/")
    if repo.count("/") != 1 or not all(repo.split("/")):
        raise IntegrationError(f"github: repo must be 'owner/name', got '{repo}'")
    return repo


class GitHubClient(IntegrationClient):
    """GitHub REST v3 client (see module docstring for env vars)."""

    service = "github"

    def __init__(self, token: str, **kwargs: Any) -> None:
        super().__init__(
            base_url="https://api.github.com",
            token=token,
            headers={
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            **kwargs,
        )

    @classmethod
    def from_env(cls) -> Self | None:
        token = env("GITHUB_TOKEN")
        return cls(token) if token else None

    # -- operations -----------------------------------------------------------

    async def notifications(self, limit: int = 10) -> list[dict[str, Any]]:
        """List unread notifications for the authenticated user."""
        response = await self._request(
            "GET", "/notifications", params={"per_page": max(1, min(int(limit), 50))}
        )
        return [
            {
                "repo": item.get("repository", {}).get("full_name", ""),
                "type": item.get("subject", {}).get("type", ""),
                "title": item.get("subject", {}).get("title", ""),
                "reason": item.get("reason", ""),
                "updated_at": item.get("updated_at", ""),
            }
            for item in response.json()
        ]

    async def issues(
        self, repo: str, state: str = "open", limit: int = 10
    ) -> list[dict[str, Any]]:
        """List issues and pull requests of ``owner/name`` (state: open|closed|all)."""
        repo = _validate_repo(repo)
        response = await self._request(
            "GET",
            f"/repos/{repo}/issues",
            params={"state": state, "per_page": max(1, min(int(limit), 50))},
        )
        return [
            {
                "number": item.get("number"),
                "title": item.get("title", ""),
                "state": item.get("state", ""),
                "author": item.get("user", {}).get("login", ""),
                "is_pull_request": "pull_request" in item,
                "url": item.get("html_url", ""),
            }
            for item in response.json()
        ]

    async def create_issue(self, repo: str, title: str, body: str = "") -> dict[str, Any]:
        """Open a new issue in ``owner/name``."""
        repo = _validate_repo(repo)
        response = await self._request(
            "POST", f"/repos/{repo}/issues", json={"title": title, "body": body}
        )
        created = response.json()
        return {
            "number": created.get("number"),
            "url": created.get("html_url", ""),
            "title": title,
        }

    async def repo_info(self, repo: str) -> dict[str, Any]:
        """Return key metadata of ``owner/name``."""
        repo = _validate_repo(repo)
        response = await self._request("GET", f"/repos/{repo}")
        data = response.json()
        return {
            "full_name": data.get("full_name", ""),
            "description": truncate(data.get("description") or "", 500),
            "default_branch": data.get("default_branch", ""),
            "language": data.get("language"),
            "stars": data.get("stargazers_count"),
            "forks": data.get("forks_count"),
            "open_issues": data.get("open_issues_count"),
            "url": data.get("html_url", ""),
        }

    # -- tools --------------------------------------------------------------------

    def register_tools(self, app: Any) -> None:
        repo_param = {"type": "string", "description": "Repository as 'owner/name'"}
        self._register_tool(
            app,
            name="github_notifications",
            description="List unread GitHub notifications of the authenticated user.",
            handler=self.notifications,
            parameters={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "default": 10, "minimum": 1, "maximum": 50}
                },
            },
        )
        self._register_tool(
            app,
            name="github_issues",
            description="List issues and pull requests of a GitHub repository.",
            handler=self.issues,
            parameters={
                "type": "object",
                "properties": {
                    "repo": repo_param,
                    "state": {"type": "string", "enum": ["open", "closed", "all"]},
                    "limit": {"type": "integer", "default": 10, "minimum": 1, "maximum": 50},
                },
                "required": ["repo"],
            },
        )
        self._register_tool(
            app,
            name="github_create_issue",
            description="Create a new issue in a GitHub repository.",
            handler=self.create_issue,
            parameters={
                "type": "object",
                "properties": {
                    "repo": repo_param,
                    "title": {"type": "string"},
                    "body": {"type": "string"},
                },
                "required": ["repo", "title"],
            },
            capability="integrations.send",
        )
        self._register_tool(
            app,
            name="github_repo",
            description="Show metadata of a GitHub repository (stars, language, ...).",
            handler=self.repo_info,
            parameters={
                "type": "object",
                "properties": {"repo": repo_param},
                "required": ["repo"],
            },
        )
