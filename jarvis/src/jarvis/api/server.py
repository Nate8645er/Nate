"""FastAPI server exposing JARVIS over HTTP and WebSocket.

Endpoints:

* ``GET  /health``            - liveness + status
* ``POST /chat``              - non-streaming answer
* ``POST /chat/stream``       - Server-Sent-Events token stream
* ``WS   /ws``                - bidirectional chat + event push
* ``GET  /agents`` ``/models`` ``/tools`` ``/plugins`` - introspection
* ``POST /plugins/{name}/reload``                       - hot reload
* ``GET/POST /memory/facts``  - long-term memory management
* ``GET/PUT  /permissions``   - security policies

If ``api.auth_token`` is configured, every route requires
``Authorization: Bearer <token>``.
"""

from __future__ import annotations

import asyncio
import json
import secrets
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from jarvis import __version__
from jarvis.agents.base import AgentResult
from jarvis.app import JarvisApp
from jarvis.core.logging import get_logger

logger = get_logger("api.server")


class ChatRequest(BaseModel):
    text: str
    orchestrate: bool = True


class ChatReply(BaseModel):
    text: str
    success: bool = True
    steps: list[dict[str, Any]] = Field(default_factory=list)


class FactIn(BaseModel):
    content: str
    category: str = "general"


class PolicyIn(BaseModel):
    capability: str
    policy: str  # allow | ask | deny


def create_api(app_instance: JarvisApp) -> FastAPI:
    """Build the FastAPI application around an assembled :class:`JarvisApp`."""
    config = app_instance.config
    bearer = HTTPBearer(auto_error=False)

    async def require_auth(
        credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    ) -> None:
        token = config.api.auth_token
        if token is None:
            return
        supplied = credentials.credentials if credentials else ""
        if not secrets.compare_digest(supplied, token.get_secret_value()):
            raise HTTPException(status_code=401, detail="Invalid or missing bearer token")

    api = FastAPI(
        title="JARVIS API",
        version=__version__,
        description="HTTP/WebSocket interface of the JARVIS assistant",
        dependencies=[Depends(require_auth)],
    )
    api.add_middleware(
        CORSMiddleware,
        allow_origins=config.api.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Plugin-provided routers.
    if app_instance.plugin_loader is not None:
        for name, loaded in app_instance.plugin_loader.loaded.items():
            for router in loaded.context._api_routers:
                api.include_router(router, prefix=f"/plugins/{name}")

    # -- basics -----------------------------------------------------------------

    @api.get("/health")
    async def health() -> dict[str, Any]:
        return {"status": "online", "version": __version__, **app_instance.status()}

    @api.get("/models")
    async def models() -> dict[str, Any]:
        healthy = await app_instance.providers.healthy_providers()
        return {"healthy_providers": healthy}

    @api.get("/agents")
    async def agents() -> dict[str, str]:
        return app_instance.orchestrator.roster()

    @api.get("/tools")
    async def tools() -> list[dict[str, Any]]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "tags": sorted(t.tags),
                "capability": t.capability,
                "source": t.source,
            }
            for t in app_instance.tools.all()
        ]

    # -- chat ---------------------------------------------------------------------

    @api.post("/chat", response_model=ChatReply)
    async def chat(request: ChatRequest) -> ChatReply:
        result: AgentResult = await app_instance.ask(
            request.text, use_orchestrator=request.orchestrate
        )
        return ChatReply(
            text=result.output,
            success=result.success,
            steps=[
                {"kind": s.kind, "tool": s.tool, "content": s.content[:500]}
                for s in result.steps
            ],
        )

    @api.post("/chat/stream")
    async def chat_stream(request: ChatRequest) -> StreamingResponse:
        async def sse() -> Any:
            try:
                async for item in app_instance.ask_stream(request.text):
                    if isinstance(item, AgentResult):
                        payload = {"type": "done", "text": item.output, "success": item.success}
                    else:
                        payload = {"type": "delta", "text": item}
                    yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
            except Exception as exc:
                logger.exception("Streaming chat failed")
                yield f"data: {json.dumps({'type': 'error', 'error': str(exc)})}\n\n"

        return StreamingResponse(sse(), media_type="text/event-stream")

    # -- WebSocket -----------------------------------------------------------------

    @api.websocket("/ws")
    async def websocket(ws: WebSocket) -> None:
        token = config.api.auth_token
        if token is not None:
            supplied = ws.query_params.get("token", "")
            if not secrets.compare_digest(supplied, token.get_secret_value()):
                await ws.close(code=4401)
                return
        await ws.accept()
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()

        def forward(event: Any) -> None:
            queue.put_nowait({"type": "event", "topic": event.topic, "data": event.data})

        subscription = app_instance.events.subscribe("*", forward)

        async def pump_events() -> None:
            while True:
                item = await queue.get()
                await ws.send_json(item)

        pump = asyncio.get_running_loop().create_task(pump_events())
        try:
            while True:
                raw = await ws.receive_text()
                try:
                    incoming = json.loads(raw)
                except json.JSONDecodeError:
                    incoming = {"type": "chat", "text": raw}
                if incoming.get("type") == "chat":
                    async for item in app_instance.ask_stream(str(incoming.get("text", ""))):
                        if isinstance(item, AgentResult):
                            await ws.send_json(
                                {"type": "done", "text": item.output, "success": item.success}
                            )
                        else:
                            await ws.send_json({"type": "delta", "text": item})
        except WebSocketDisconnect:
            pass
        finally:
            pump.cancel()
            subscription.cancel()

    # -- plugins ----------------------------------------------------------------------

    @api.get("/plugins")
    async def plugins() -> list[dict[str, str]]:
        loader = app_instance.plugin_loader
        if loader is None:
            return []
        return [
            {
                "name": name,
                "version": lp.instance.manifest.version,
                "description": lp.instance.manifest.description,
                "path": str(lp.path),
            }
            for name, lp in loader.loaded.items()
        ]

    @api.post("/plugins/{name}/reload")
    async def reload_plugin(name: str) -> dict[str, str]:
        loader = app_instance.plugin_loader
        if loader is None or name not in loader.loaded:
            raise HTTPException(status_code=404, detail=f"Plugin '{name}' not loaded")
        await loader.reload(name)
        return {"status": "reloaded", "plugin": name}

    # -- memory -----------------------------------------------------------------------

    @api.get("/memory/facts")
    async def memory_facts(query: str | None = None) -> list[dict[str, Any]]:
        assert app_instance.memory is not None
        long_term = app_instance.memory.long_term
        facts = (
            await long_term.search_facts(query) if query else await long_term.all_facts()
        )
        return [
            {"id": f.id, "category": f.category, "content": f.content, "created_at": f.created_at}
            for f in facts
        ]

    @api.post("/memory/facts")
    async def memory_add_fact(fact: FactIn) -> dict[str, int]:
        assert app_instance.memory is not None
        fact_id = await app_instance.memory.remember(fact.content, category=fact.category)
        return {"id": fact_id}

    @api.get("/memory/stats")
    async def memory_stats() -> dict[str, Any]:
        assert app_instance.memory is not None
        return await app_instance.memory.stats()

    # -- security -----------------------------------------------------------------------

    @api.get("/permissions")
    async def get_permissions() -> dict[str, str]:
        capabilities = sorted(
            {t.capability for t in app_instance.tools.all() if t.capability}
        )
        return {cap: app_instance.permissions.policy_for(cap) for cap in capabilities}

    @api.put("/permissions")
    async def set_permission(policy: PolicyIn) -> dict[str, str]:
        if policy.policy not in ("allow", "ask", "deny"):
            raise HTTPException(status_code=422, detail="policy must be allow|ask|deny")
        app_instance.permissions.set_policy(policy.capability, policy.policy)  # type: ignore[arg-type]
        return {policy.capability: policy.policy}

    return api
