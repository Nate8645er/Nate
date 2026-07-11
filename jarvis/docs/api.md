# HTTP / WebSocket API

Start with `jarvis serve` (default `127.0.0.1:8765`). Interactive OpenAPI docs
at `/docs`. If `api.auth_token` is set, every route requires
`Authorization: Bearer <token>` (WebSocket: `?token=<token>`).

## Chat

### `POST /chat`

```json
{"text": "Summarise my open tasks", "orchestrate": true}
```

→

```json
{"text": "...", "success": true, "steps": [{"kind": "tool_call", "tool": "tasks_list", "content": ""}]}
```

### `POST /chat/stream` — Server-Sent Events

```
data: {"type": "delta", "text": "Of"}
data: {"type": "delta", "text": " course"}
data: {"type": "done", "text": "Of course, Sir. ...", "success": true}
```

### `WS /ws`

Send `{"type": "chat", "text": "..."}` (or raw text). Receive:

* `{"type": "delta", "text": "..."}` — streamed tokens
* `{"type": "done", "text": "...", "success": true}` — final answer
* `{"type": "event", "topic": "agent.tool_call", "data": {...}}` — live
  event-bus feed (tool calls, voice levels, timers, …), ideal for HUD frontends.

## Introspection

| Route | Returns |
|---|---|
| `GET /health` | status, version, active subsystems, agents, tools, plugins |
| `GET /models` | healthy providers |
| `GET /agents` | roster with descriptions |
| `GET /tools` | every tool: name, description, tags, capability, source |
| `GET /plugins` | loaded plugins with versions |
| `POST /plugins/{name}/reload` | hot-reload one plugin |

## Memory

| Route | Effect |
|---|---|
| `GET /memory/facts?query=…` | search long-term facts (FTS5) |
| `POST /memory/facts` `{"content", "category"}` | store a fact (also vector-indexed) |
| `GET /memory/stats` | session id, window size, vector/fact counts |

## Security

| Route | Effect |
|---|---|
| `GET /permissions` | effective policy per known capability |
| `PUT /permissions` `{"capability": "desktop.terminal", "policy": "allow"}` | set + persist a policy (`allow` / `ask` / `deny`; prefix wildcards like `desktop.*` allowed) |

## Python client example

```python
import httpx, json

async with httpx.AsyncClient(base_url="http://127.0.0.1:8765") as client:
    async with client.stream("POST", "/chat/stream", json={"text": "Hello"}) as response:
        async for line in response.aiter_lines():
            if line.startswith("data:"):
                event = json.loads(line[5:])
                if event["type"] == "delta":
                    print(event["text"], end="", flush=True)
```
