import asyncio

import httpx
import pytest

from jarvis.api.app import create_app
from jarvis.config import Settings
from jarvis.kernel import Kernel


@pytest.fixture
async def client(test_settings: Settings):
    kernel = Kernel(test_settings)
    app = create_app(kernel)
    await kernel.start()
    kernel.bus.subscribe("*", lambda e: asyncio.sleep(0))  # keep parity with prod wiring
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c, kernel
    await kernel.stop()


async def test_status(client):
    c, _ = client
    resp = await c.get("/api/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["assistant"] == "Jarvis"
    assert len(data["agents"]) >= 19
    assert data["llm"] == "echo"


async def test_chat_creates_task(client):
    c, kernel = client
    resp = await c.post("/api/chat", json={"text": "hallo"})
    assert resp.status_code == 200
    task_id = resp.json()["task_id"]
    for _ in range(100):
        tasks = kernel.agents.get("ceo").tasks
        if task_id in tasks and tasks[task_id].status == "done":
            break
        await asyncio.sleep(0.02)
    assert kernel.agents.get("ceo").tasks[task_id].status == "done"


async def test_hire_fire_via_api(client):
    c, _ = client
    resp = await c.post("/api/agents", json={
        "name": "support", "title": "Support Agent", "department": "support",
    })
    assert resp.status_code == 200
    resp = await c.get("/api/agents")
    assert any(a["name"] == "support" for a in resp.json())
    resp = await c.delete("/api/agents/support")
    assert resp.status_code == 200
    resp = await c.delete("/api/agents/support")
    assert resp.status_code == 404


async def test_memory_endpoints(client):
    c, _ = client
    resp = await c.post("/api/memory", json={"subject": "stadt", "content": "Bern"})
    assert resp.status_code == 200
    resp = await c.get("/api/memory", params={"query": "Bern"})
    assert any(f["subject"] == "stadt" for f in resp.json())
    resp = await c.get("/api/memory/search", params={"query": "Bern Stadt"})
    assert resp.status_code == 200


async def test_workflow_endpoints(client):
    c, _ = client
    resp = await c.post("/api/workflows", json={
        "name": "api-test",
        "steps": [{"name": "s", "skill": "system_stats", "args": {}}],
    })
    assert resp.status_code == 200
    resp = await c.post("/api/workflows/api-test/run")
    assert resp.status_code == 200
    assert resp.json()["status"] == "done"
    resp = await c.delete("/api/workflows/api-test")
    assert resp.status_code == 200


async def test_skill_toggle_endpoint(client):
    c, _ = client
    resp = await c.post("/api/skills/system_stats/enabled", params={"enabled": False})
    assert resp.status_code == 200
    resp = await c.get("/api/skills")
    entry = next(s for s in resp.json() if s["name"] == "system_stats")
    assert entry["enabled"] is False


async def test_company_org_chart(client):
    c, _ = client
    resp = await c.get("/api/company")
    chart = resp.json()["departments"]
    assert "engineering" in chart
    assert any(a["name"] == "coding" for a in chart["engineering"])
