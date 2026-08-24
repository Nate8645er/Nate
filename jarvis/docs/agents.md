# Agents & orchestration

## The agent model

Every agent is a `BaseAgent`: a persona (`system_prompt`), a themed toolset
(`tool_tags` selecting from the global `ToolRegistry`) and model requirements
(`requirements()` feeding the router). The run loop is the classic tool loop:

```
messages → model → tool_calls? → execute (permission-gated) → append results → repeat
```

with `max_iterations` as a hard stop and every step traced (`AgentStep`) and
published on the event bus.

## Built-in specialists

| Agent | Tool tags | Job |
|---|---|---|
| `planner` | — | Decomposes requests into steps, assigns specialists (JSON plan) |
| `research` | browser, search, rag | Web + knowledge-base research with citations |
| `vision` | vision | Screen/webcam capture, OCR, detection, image analysis |
| `coding` | code, files, terminal | Writes and *runs* code in the sandbox before answering |
| `desktop` | desktop, files, office, terminal | Operates the computer, verifies state after actions |
| `browser` | browser, search | Drives Playwright: navigation, forms, downloads |
| `automation` | integrations, tasks | Calendar, e-mail, Spotify, GitHub, Notion, … |
| `voice` | voice | Speech phrasing and voice control |
| `memory` | memory, rag | Stores durable facts, maintains the profile |

## Orchestration

`AgentOrchestrator.run()` executes a three-node `AgentGraph`:

1. **plan** — the planner sees the roster and produces
   `{"steps": [{"agent", "task"}...], "direct_answer": ""}`. Trivial requests
   short-circuit with a direct answer.
2. **execute** — steps run sequentially; each specialist receives the results
   of previous steps as context. Failures are captured, not fatal.
3. **synthesise** — one model call merges multi-step results into a single
   answer (skipped for single-step plans).

`JarvisApp.ask()` uses the orchestrator; `ask_stream()` uses a single
streaming JARVIS agent for low-latency voice/GUI interaction.

## Writing your own agent

```python
from jarvis.agents import BaseAgent
from jarvis.llm.router import TaskRequirements

class TradingAgent(BaseAgent):
    name = "trading"
    description = "Analyses markets and portfolio data"
    tool_tags = {"finance", "rag"}
    system_prompt = "You are the Trading Agent. ..."

    def requirements(self) -> TaskRequirements:
        return TaskRequirements(needs_tools=True, min_quality=7)
```

Register it from a plugin (`context.register_agent(TradingAgent(context.router,
context.tools))`) or directly on `app.orchestrator`. The planner discovers it
automatically via the roster — no core changes required.

## AgentGraph

For custom workflows, build your own graph:

```python
from jarvis.agents.graph import AgentGraph, END

graph = AgentGraph("review")
graph.add_node("draft", draft_fn)          # (state: dict) -> dict, sync or async
graph.add_node("critique", critique_fn)
graph.add_edge("draft", "critique")
graph.add_conditional_edge("critique",
    lambda s: END if s["score"] > 8 else "draft")
state = await graph.run({"topic": "..."})
```

`to_langgraph(graph)` converts it to a compiled LangGraph `StateGraph` when
the `langchain` extra is installed, for interop with the LangChain ecosystem.
