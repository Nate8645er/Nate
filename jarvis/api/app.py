"""FastAPI application: REST + WebSocket + static HUD dashboard.

WebSocket protocol (JSON messages):
  client -> server: {"type": "chat", "text": "...", "session": "default"}
                    {"type": "approval", "id": "...", "approved": true, "remember": false}
  server -> client: every bus event, as {"type": "event", "topic": ..., "data": ..., ...}
"""

from __future__ import annotations

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from jarvis import __version__
from jarvis.config import Settings
from jarvis.core.events import Event
from jarvis.kernel import Kernel

log = logging.getLogger(__name__)

WEB_DIR = Path(__file__).resolve().parent.parent.parent / "web"


# --------------------------------------------------------------- API models
class ChatRequest(BaseModel):
    text: str
    session: str = "default"


class ApprovalDecision(BaseModel):
    approved: bool
    remember: bool = False


class HireRequest(BaseModel):
    name: str
    title: str
    department: str = "general"
    description: str = ""
    skill_categories: list[str] = []
    system_prompt: str = ""


class RememberRequest(BaseModel):
    subject: str
    content: str
    kind: str = "fact"


class WorkflowUpsert(BaseModel):
    name: str
    description: str = ""
    steps: list[dict[str, Any]]


def create_app(kernel: Kernel | None = None, cfg: Settings | None = None) -> FastAPI:
    kernel = kernel or Kernel(cfg)

    sockets: set[WebSocket] = set()

    async def broadcast(event: Event) -> None:
        message = json.dumps({"type": "event", **event.to_dict()}, default=str)
        dead = []
        for ws in sockets:
            try:
                await ws.send_text(message)
            except Exception:  # noqa: BLE001 - client gone
                dead.append(ws)
        for ws in dead:
            sockets.discard(ws)

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        await kernel.start()
        kernel.bus.subscribe("*", broadcast)
        yield
        await kernel.stop()

    app = FastAPI(title="JARVIS AI OS", version=__version__, lifespan=lifespan)
    app.state.kernel = kernel

    # ------------------------------------------------------------- websocket
    @app.websocket("/ws")
    async def websocket_endpoint(ws: WebSocket) -> None:
        await ws.accept()
        sockets.add(ws)
        try:
            while True:
                raw = await ws.receive_text()
                try:
                    msg = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                if msg.get("type") == "chat" and msg.get("text"):
                    asyncio.create_task(
                        kernel.orchestrator.handle_utterance(
                            msg["text"], session=msg.get("session", "default")
                        )
                    )
                elif msg.get("type") == "approval" and msg.get("id"):
                    await kernel.approvals.resolve(
                        msg["id"], bool(msg.get("approved")), bool(msg.get("remember"))
                    )
        except WebSocketDisconnect:
            pass
        finally:
            sockets.discard(ws)

    # ------------------------------------------------------------------ core
    @app.get("/api/status")
    async def status() -> dict[str, Any]:
        return {
            "assistant": kernel.settings.assistant_name,
            "version": __version__,
            "llm": kernel.llm.name,
            "agents": kernel.agents.status(),
            "plugins": kernel.plugins.status(),
            "skills": len(kernel.skills.all()),
            "voice": kernel.voice.status() if kernel.voice else {"enabled": False},
            "schedule": kernel.scheduler.upcoming(),
        }

    @app.post("/api/chat")
    async def chat(req: ChatRequest) -> dict[str, Any]:
        task = await kernel.orchestrator.handle_utterance(req.text, session=req.session)
        return {"task_id": task.id, "status": task.status}

    @app.get("/api/events")
    async def events(limit: int = 100) -> list[dict[str, Any]]:
        return [e.to_dict() for e in list(kernel.bus.history)[-limit:]]

    # ------------------------------------------------------------- approvals
    @app.get("/api/approvals")
    async def approvals() -> list[dict[str, Any]]:
        return [r.to_dict() for r in kernel.approvals.pending.values()]

    @app.post("/api/approvals/{request_id}")
    async def decide(request_id: str, decision: ApprovalDecision) -> dict[str, Any]:
        ok = await kernel.approvals.resolve(request_id, decision.approved, decision.remember)
        if not ok:
            raise HTTPException(404, "Unknown or already-resolved approval request")
        return {"resolved": True}

    # ---------------------------------------------------------------- agents
    @app.get("/api/agents")
    async def agents() -> list[dict[str, Any]]:
        return kernel.agents.status()

    @app.get("/api/company")
    async def company() -> dict[str, Any]:
        return kernel.company.org_chart()

    @app.post("/api/agents")
    async def hire(req: HireRequest) -> dict[str, Any]:
        spec = kernel.company.hire(
            req.name, req.title, req.department, req.description,
            req.skill_categories, req.system_prompt,
        )
        return spec.to_dict()

    @app.delete("/api/agents/{name}")
    async def fire(name: str) -> dict[str, Any]:
        if not await kernel.company.fire(name):
            raise HTTPException(404, f"No such agent: {name}")
        return {"fired": name}

    @app.post("/api/agents/{name}/task")
    async def submit_task(name: str, req: ChatRequest) -> dict[str, Any]:
        agent = kernel.agents.get(name)
        if agent is None:
            raise HTTPException(404, f"No such agent: {name}")
        task = await agent.submit(req.text, session=req.session)
        return task.to_dict()

    @app.get("/api/agents/{name}/tasks")
    async def agent_tasks(name: str) -> list[dict[str, Any]]:
        agent = kernel.agents.get(name)
        if agent is None:
            raise HTTPException(404, f"No such agent: {name}")
        return [t.to_dict() for t in agent.tasks.values()]

    # ---------------------------------------------------------------- skills
    @app.get("/api/skills")
    async def skills() -> list[dict[str, Any]]:
        return [s.to_dict() for s in kernel.skills.all()]

    @app.post("/api/skills/{name}/enabled")
    async def toggle_skill(name: str, enabled: bool) -> dict[str, Any]:
        if not kernel.skills.set_enabled(name, enabled):
            raise HTTPException(404, f"No such skill: {name}")
        return {"name": name, "enabled": enabled}

    # --------------------------------------------------------------- plugins
    @app.get("/api/plugins")
    async def plugins() -> list[dict[str, Any]]:
        kernel.plugins.discover()
        return kernel.plugins.status()

    @app.post("/api/plugins/{plugin_id}/enabled")
    async def toggle_plugin(plugin_id: str, enabled: bool) -> dict[str, Any]:
        if plugin_id not in kernel.plugins.plugins:
            raise HTTPException(404, f"No such plugin: {plugin_id}")
        plugin = await kernel.plugins.set_enabled(plugin_id, enabled)
        return plugin.to_dict()

    @app.post("/api/plugins/{plugin_id}/reload")
    async def reload_plugin(plugin_id: str) -> dict[str, Any]:
        if plugin_id not in kernel.plugins.plugins:
            raise HTTPException(404, f"No such plugin: {plugin_id}")
        plugin = await kernel.plugins.reload(plugin_id)
        return plugin.to_dict()

    # ---------------------------------------------------------------- memory
    @app.post("/api/memory")
    async def remember(req: RememberRequest) -> dict[str, Any]:
        fact_id = await kernel.memory.remember(req.subject, req.content, req.kind)
        return {"id": fact_id}

    @app.get("/api/memory")
    async def recall(query: str = "", kind: str | None = None, limit: int = 20) -> list[dict]:
        return await kernel.memory.long_term.recall(query=query, kind=kind, limit=limit)

    @app.get("/api/memory/search")
    async def semantic_search(query: str, limit: int = 8) -> list[dict[str, Any]]:
        return await kernel.memory.search(query, limit=limit)

    @app.get("/api/conversations/{session}")
    async def conversation(session: str, limit: int = 100) -> list[dict[str, Any]]:
        return await kernel.memory.long_term.conversation(session, limit=limit)

    # ------------------------------------------------------------- workflows
    @app.get("/api/workflows")
    async def workflows() -> list[dict[str, Any]]:
        return [w.to_dict() for w in kernel.workflows.workflows.values()]

    @app.post("/api/workflows")
    async def upsert_workflow(req: WorkflowUpsert) -> dict[str, Any]:
        from jarvis.workflows.engine import Workflow

        wf = Workflow(name=req.name, description=req.description, steps=req.steps)
        kernel.workflows.register(wf)
        return wf.to_dict()

    @app.post("/api/workflows/{name}/run")
    async def run_workflow(name: str) -> dict[str, Any]:
        if name not in kernel.workflows.workflows:
            raise HTTPException(404, f"No such workflow: {name}")
        return await kernel.workflows.run(name)

    @app.delete("/api/workflows/{name}")
    async def delete_workflow(name: str) -> dict[str, Any]:
        if not kernel.workflows.remove(name):
            raise HTTPException(404, f"No such workflow: {name}")
        return {"deleted": name}

    # ------------------------------------------------------------------ voice
    @app.post("/api/voice/transcribe")
    async def transcribe(file: UploadFile) -> dict[str, Any]:
        if kernel.voice is None:
            raise HTTPException(503, "Voice pipeline disabled")
        try:
            text = await kernel.voice.handle_voice_input(await file.read())
        except RuntimeError as exc:
            raise HTTPException(501, str(exc)) from exc
        return {"text": text}

    # -------------------------------------------------------------- dashboard
    if WEB_DIR.is_dir():
        app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")

        @app.get("/", include_in_schema=False)
        async def index() -> FileResponse:
            return FileResponse(WEB_DIR / "index.html")

    return app
