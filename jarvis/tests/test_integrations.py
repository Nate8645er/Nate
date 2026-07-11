"""Tests for the integrations subsystem (no real network: respx mocks)."""

from __future__ import annotations

import base64
import json
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from urllib.parse import parse_qs

import httpx
import pytest
import respx

from jarvis.agents.tools import ToolRegistry
from jarvis.core.config import JarvisConfig
from jarvis.core.container import ServiceContainer
from jarvis.core.security import PermissionManager
from jarvis.integrations import _SERVICE_ENV, integrations_status, register
from jarvis.integrations.calendar_client import LocalCalendarClient
from jarvis.integrations.github_client import GitHubClient
from jarvis.integrations.notion_client import NotionClient
from jarvis.integrations.spotify_client import SpotifyClient
from jarvis.integrations.telegram_client import TelegramClient

_EXTRA_ENV = [
    "EMAIL_SMTP_PORT",
    "EMAIL_SMTP_USER",
    "EMAIL_SMTP_PASSWORD",
    "EMAIL_FROM",
    "TELEGRAM_CHAT_ID",
    "NOTION_PARENT_PAGE_ID",
]
_ALL_ENV_VARS = sorted(
    {var for groups in _SERVICE_ENV.values() for group in groups for var in group}
    | set(_EXTRA_ENV)
)


def _clear_integration_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for var in _ALL_ENV_VARS:
        monkeypatch.delenv(var, raising=False)


@pytest.fixture()
def stub_app(tmp_path):
    """A minimal app double with real registry, permissions and container."""
    config = JarvisConfig(data_dir=tmp_path / "data")
    config.ensure_dirs()
    permissions = PermissionManager(config)
    return SimpleNamespace(
        config=config,
        permissions=permissions,
        tools=ToolRegistry(permissions),
        container=ServiceContainer(),
    )


# -- telegram ---------------------------------------------------------------------


@respx.mock
async def test_telegram_send_happy_path():
    route = respx.post("https://api.telegram.org/botTOKEN123/sendMessage").mock(
        return_value=httpx.Response(
            200, json={"ok": True, "result": {"message_id": 77, "chat": {"id": 42}}}
        )
    )
    client = TelegramClient(token="TOKEN123", default_chat_id="42")
    try:
        result = await client.send_message("hello world")
    finally:
        await client.aclose()

    assert route.called
    request = route.calls.last.request
    assert request.url == "https://api.telegram.org/botTOKEN123/sendMessage"
    assert json.loads(request.content) == {"chat_id": "42", "text": "hello world"}
    assert result == {"sent": True, "chat_id": "42", "message_id": 77}


@respx.mock
async def test_telegram_send_explicit_chat_overrides_default():
    route = respx.post("https://api.telegram.org/botT/sendMessage").mock(
        return_value=httpx.Response(200, json={"ok": True, "result": {"message_id": 1}})
    )
    client = TelegramClient(token="T", default_chat_id="42")
    try:
        await client.send_message("hi", chat_id="99")
    finally:
        await client.aclose()
    assert json.loads(route.calls.last.request.content)["chat_id"] == "99"


# -- github ----------------------------------------------------------------------


@respx.mock
async def test_github_issues_list_parsing():
    payload = [
        {
            "number": 1,
            "title": "Crash on start",
            "state": "open",
            "user": {"login": "alice"},
            "html_url": "https://github.com/foo/bar/issues/1",
        },
        {
            "number": 2,
            "title": "Add dark mode",
            "state": "open",
            "user": {"login": "bob"},
            "pull_request": {"url": "https://api.github.com/repos/foo/bar/pulls/2"},
            "html_url": "https://github.com/foo/bar/pull/2",
        },
    ]
    route = respx.get("https://api.github.com/repos/foo/bar/issues").mock(
        return_value=httpx.Response(200, json=payload)
    )
    client = GitHubClient("ghtoken")
    try:
        issues = await client.issues("foo/bar", state="open", limit=10)
    finally:
        await client.aclose()

    assert route.called
    request = route.calls.last.request
    assert request.headers["Authorization"] == "Bearer ghtoken"
    assert issues == [
        {
            "number": 1,
            "title": "Crash on start",
            "state": "open",
            "author": "alice",
            "is_pull_request": False,
            "url": "https://github.com/foo/bar/issues/1",
        },
        {
            "number": 2,
            "title": "Add dark mode",
            "state": "open",
            "author": "bob",
            "is_pull_request": True,
            "url": "https://github.com/foo/bar/pull/2",
        },
    ]


# -- notion -----------------------------------------------------------------------


@respx.mock
async def test_notion_search_parsing():
    payload = {
        "results": [
            {
                "id": "page-1",
                "object": "page",
                "url": "https://notion.so/page-1",
                "properties": {
                    "Name": {"type": "title", "title": [{"plain_text": "Project Plan"}]}
                },
            },
            {
                "id": "db-1",
                "object": "database",
                "url": "https://notion.so/db-1",
                "title": [{"plain_text": "Tasks"}],
            },
        ]
    }
    route = respx.post("https://api.notion.com/v1/search").mock(
        return_value=httpx.Response(200, json=payload)
    )
    client = NotionClient("secret-token")
    try:
        results = await client.search("plan", limit=5)
    finally:
        await client.aclose()

    assert route.called
    request = route.calls.last.request
    assert request.headers["Notion-Version"] == "2022-06-28"
    assert json.loads(request.content) == {"query": "plan", "page_size": 5}
    assert results[0] == {
        "id": "page-1",
        "object": "page",
        "title": "Project Plan",
        "url": "https://notion.so/page-1",
    }
    assert results[1]["title"] == "Tasks"


# -- spotify ------------------------------------------------------------------------


@respx.mock
async def test_spotify_token_refresh_flow():
    token_route = respx.post("https://accounts.spotify.com/api/token").mock(
        return_value=httpx.Response(
            200, json={"access_token": "fresh-token", "expires_in": 3600}
        )
    )
    search_route = respx.get("https://api.spotify.com/v1/search").mock(
        return_value=httpx.Response(
            200,
            json={
                "tracks": {
                    "items": [
                        {
                            "name": "Starlight",
                            "artists": [{"name": "Muse"}],
                            "album": {"name": "Black Holes"},
                            "uri": "spotify:track:xyz",
                        }
                    ]
                }
            },
        )
    )
    client = SpotifyClient(client_id="cid", client_secret="csec", refresh_token="rtok")
    try:
        tracks = await client.search("starlight", limit=1)
        # A second call reuses the cached token: no extra refresh request.
        await client.search("starlight", limit=1)
    finally:
        await client.aclose()

    assert token_route.call_count == 1
    token_request = token_route.calls.last.request
    expected_basic = base64.b64encode(b"cid:csec").decode("ascii")
    assert token_request.headers["Authorization"] == f"Basic {expected_basic}"
    form = parse_qs(token_request.content.decode())
    assert form == {"grant_type": ["refresh_token"], "refresh_token": ["rtok"]}

    assert search_route.call_count == 2
    assert search_route.calls.last.request.headers["Authorization"] == "Bearer fresh-token"
    assert tracks == [
        {
            "name": "Starlight",
            "artists": "Muse",
            "album": "Black Holes",
            "uri": "spotify:track:xyz",
        }
    ]


# -- local ICS calendar -----------------------------------------------------------


def test_ics_calendar_parse_append_roundtrip(tmp_path):
    client = LocalCalendarClient(tmp_path / "calendar.ics")
    start = (datetime.now(UTC) + timedelta(days=1)).replace(microsecond=0)
    created = client.add_event(
        "Team; Sync, planning",
        start.isoformat(),
        description="Line1\nLine2, with; punctuation",
    )
    # A second event outside the 7-day window must be filtered out.
    client.add_event("Far future", (datetime.now(UTC) + timedelta(days=30)).isoformat())

    raw = (tmp_path / "calendar.ics").read_text(encoding="utf-8")
    assert raw.startswith("BEGIN:VCALENDAR")
    assert raw.rstrip().endswith("END:VCALENDAR")
    assert "SUMMARY:Team\\; Sync\\, planning" in raw
    assert "DESCRIPTION:Line1\\nLine2\\, with\\; punctuation" in raw

    events = client.list_events(days=7)
    assert len(events) == 1
    event = events[0]
    assert event["uid"] == created["uid"]
    assert event["summary"] == "Team; Sync, planning"
    assert event["description"] == "Line1\nLine2, with; punctuation"
    assert datetime.fromisoformat(event["start"]) == start
    assert datetime.fromisoformat(event["end"]) == start + timedelta(hours=1)

    both = client.list_events(days=60)
    assert [e["summary"] for e in both] == ["Team; Sync, planning", "Far future"]


# -- status tool ---------------------------------------------------------------------


def test_integrations_status_reports_names_not_values(monkeypatch):
    _clear_integration_env(monkeypatch)
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "super-secret-token-value")

    report = integrations_status()

    assert report["telegram"]["configured"] is True
    assert report["github"]["configured"] is False
    assert report["calendar"]["configured"] is True  # always on, no env needed
    # Spotify needs either the access token or the full refresh triple.
    assert report["spotify"]["configured"] is False
    dumped = json.dumps(report)
    assert "super-secret-token-value" not in dumped
    assert "TELEGRAM_BOT_TOKEN" in dumped


# -- register(app) ----------------------------------------------------------------


async def test_register_only_configured_tools_appear(stub_app, monkeypatch):
    _clear_integration_env(monkeypatch)
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "tok")
    monkeypatch.setenv("GITHUB_TOKEN", "ghtok")

    register(stub_app)

    names = {tool.name for tool in stub_app.tools.all()}
    expected = {
        "integrations_status",
        "calendar_list_events",
        "calendar_add_event",
        "telegram_send",
        "telegram_updates",
        "github_notifications",
        "github_issues",
        "github_create_issue",
        "github_repo",
    }
    assert expected <= names
    for absent in ("spotify_search", "notion_search", "discord_send", "email_send",
                   "gcal_list_events", "gdrive_search", "onedrive_list", "whatsapp_send"):
        assert absent not in names

    telegram_send = stub_app.tools.get("telegram_send")
    assert telegram_send is not None
    assert telegram_send.capability == "integrations.send"
    assert telegram_send.tags == {"integrations", "telegram"}
    assert stub_app.tools.get("github_issues").capability is None
    assert stub_app.tools.get("github_create_issue").capability == "integrations.send"
    assert stub_app.tools.get("calendar_add_event").capability == "files.write"

    # The status tool is executable through the registry and reports services.
    output = await stub_app.tools.execute("integrations_status", {})
    assert '"telegram"' in output
    assert "tok" == "tok" and "ghtok" not in output


def test_register_with_empty_env_never_raises(stub_app, monkeypatch):
    _clear_integration_env(monkeypatch)

    register(stub_app)  # must not raise

    names = {tool.name for tool in stub_app.tools.all()}
    assert names == {"integrations_status", "calendar_list_events", "calendar_add_event"}


def test_register_never_raises_with_broken_app():
    # Even a completely wrong app object must not crash register().
    register(SimpleNamespace())
