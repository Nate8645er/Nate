"""Tests for the FastAPI layer (ASGI in-process, no sockets)."""

from __future__ import annotations

import httpx
import pytest

from jarvis.agents.base import AgentResult
from jarvis.api.server import create_api
from jarvis.app import JarvisApp
from jarvis.core.config import JarvisConfig


@pytest.fixture()
async def app(config: JarvisConfig):
    instance = await JarvisApp.create(config)
    yield instance
    await instance.aclose()


@pytest.fixture()
async def client(app: JarvisApp):
    api = create_api(app)
    transport = httpx.ASGITransport(app=api)
    async with httpx.AsyncClient(transport=transport, base_url="http://jarvis") as http:
        yield http


class TestApi:
    async def test_health(self, client: httpx.AsyncClient) -> None:
        response = await client.get("/health")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "online"
        assert "planner" in body["agents"]

    async def test_tools_listing(self, client: httpx.AsyncClient) -> None:
        response = await client.get("/tools")
        names = {t["name"] for t in response.json()}
        assert {"memory_remember", "rag_search", "run_python"} <= names

    async def test_memory_endpoints(self, client: httpx.AsyncClient) -> None:
        created = await client.post(
            "/memory/facts", json={"content": "User prefers metric units", "category": "preference"}
        )
        assert created.status_code == 200
        listed = await client.get("/memory/facts", params={"query": "metric"})
        assert any("metric" in f["content"] for f in listed.json())
        stats = await client.get("/memory/stats")
        assert stats.json()["facts"] >= 1

    async def test_permissions_endpoints(self, client: httpx.AsyncClient) -> None:
        put = await client.put(
            "/permissions", json={"capability": "code.execute", "policy": "allow"}
        )
        assert put.status_code == 200
        got = await client.get("/permissions")
        assert got.json().get("code.execute") == "allow"
        bad = await client.put("/permissions", json={"capability": "x", "policy": "maybe"})
        assert bad.status_code == 422

    async def test_chat_uses_app(self, app: JarvisApp, client: httpx.AsyncClient, monkeypatch) -> None:
        async def fake_ask(text: str, *, use_orchestrator: bool = True) -> AgentResult:
            return AgentResult(output=f"echo: {text}")

        monkeypatch.setattr(app, "ask", fake_ask)
        response = await client.post("/chat", json={"text": "hello"})
        assert response.json()["text"] == "echo: hello"


class TestApiAuth:
    async def test_bearer_required(self, config: JarvisConfig) -> None:
        from pydantic import SecretStr

        config.api.auth_token = SecretStr("s3cret")
        app = await JarvisApp.create(config)
        try:
            api = create_api(app)
            transport = httpx.ASGITransport(app=api)
            async with httpx.AsyncClient(transport=transport, base_url="http://jarvis") as http:
                denied = await http.get("/health")
                assert denied.status_code == 401
                allowed = await http.get(
                    "/health", headers={"Authorization": "Bearer s3cret"}
                )
                assert allowed.status_code == 200
        finally:
            await app.aclose()
