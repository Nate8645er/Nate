"""Multi-agent orchestration.

The :class:`AgentOrchestrator` owns the roster of agents. For each request it
runs a plan→execute→synthesise state graph:

1. **plan** - the planner decomposes the request (or answers directly),
2. **execute** - each step runs on its specialist, results feed later steps,
3. **synthesise** - a final model call merges step results into one answer.

Agents can be registered/unregistered at runtime (plugins do this), which is
what keeps the system open for extension.
"""

from __future__ import annotations

import json
import re
from typing import Any

from jarvis.agents.base import AgentResult, BaseAgent
from jarvis.agents.graph import END, AgentGraph
from jarvis.core.errors import AgentError
from jarvis.core.events import EventBus
from jarvis.core.logging import get_logger
from jarvis.llm.base import ChatOptions, Message
from jarvis.llm.router import ModelRouter, TaskRequirements

logger = get_logger("agents.orchestrator")


def _extract_json(text: str) -> dict[str, Any]:
    """Parse the first JSON object found in the text (handles code fences)."""
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    candidate = fenced.group(1) if fenced else None
    if candidate is None:
        brace = text.find("{")
        if brace != -1:
            candidate = text[brace:]
    if candidate:
        decoder = json.JSONDecoder()
        try:
            parsed, _ = decoder.raw_decode(candidate)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass
    return {}


class AgentOrchestrator:
    """Owns the agent roster and coordinates multi-agent runs."""

    def __init__(self, router: ModelRouter, events: EventBus) -> None:
        self._router = router
        self._events = events
        self._agents: dict[str, BaseAgent] = {}

    # -- roster -----------------------------------------------------------------

    def register(self, agent: BaseAgent) -> None:
        self._agents[agent.name] = agent

    def unregister(self, name: str) -> None:
        self._agents.pop(name, None)

    def get(self, name: str) -> BaseAgent:
        agent = self._agents.get(name)
        if agent is None:
            raise AgentError(f"Unknown agent '{name}'")
        return agent

    def roster(self) -> dict[str, str]:
        return {name: agent.description for name, agent in sorted(self._agents.items())}

    # -- orchestration ------------------------------------------------------------

    async def run(self, request: str, *, context: str = "") -> AgentResult:
        """Run the full plan→execute→synthesise graph for a request."""
        graph = AgentGraph(name="orchestrator")
        graph.add_node("plan", self._plan_node)
        graph.add_node("execute", self._execute_node)
        graph.add_node("synthesise", self._synthesise_node)
        graph.set_entry("plan")
        graph.add_conditional_edge(
            "plan", lambda s: END if s.get("answer") else "execute"
        )
        graph.add_edge("execute", "synthesise")
        graph.add_edge("synthesise", END)

        state = await graph.run({"request": request, "context": context})
        return AgentResult(
            output=state.get("answer", ""),
            steps=state.get("trace", []),
            success=not state.get("failed", False),
        )

    async def _plan_node(self, state: dict[str, Any]) -> dict[str, Any]:
        planner = self._agents.get("planner")
        roster = {
            name: desc for name, desc in self.roster().items() if name != "planner"
        }
        if planner is None or not roster:
            return {"steps": [], "answer": ""} if roster else {"answer": ""}
        prompt = (
            f"Available specialists:\n{json.dumps(roster, indent=2)}\n\n"
            f"User request: {state['request']}"
        )
        result = await planner.run(prompt, context=state.get("context", ""))
        parsed = _extract_json(result.output)
        steps = [
            step
            for step in parsed.get("steps", [])
            if isinstance(step, dict) and step.get("agent") in self._agents
        ]
        direct = str(parsed.get("direct_answer") or "").strip()
        if direct and not steps:
            return {"answer": direct}
        if not steps:
            # Planner produced nothing usable: degrade to a single research/coding pass
            # or answer directly with the planner's raw output.
            return {"answer": result.output}
        await self._events.publish("orchestrator.plan", {"steps": steps})
        return {"steps": steps, "answer": ""}

    async def _execute_node(self, state: dict[str, Any]) -> dict[str, Any]:
        results: list[dict[str, str]] = []
        failed = False
        for i, step in enumerate(state.get("steps", [])):
            agent = self.get(step["agent"])
            task = str(step.get("task", state["request"]))
            prior = ""
            if results:
                prior = "Results of previous steps:\n" + "\n\n".join(
                    f"[{r['agent']}] {r['output']}" for r in results
                )
            await self._events.publish(
                "orchestrator.step", {"index": i, "agent": agent.name, "task": task}
            )
            try:
                outcome = await agent.run(task, context="\n\n".join(filter(None, [state.get("context", ""), prior])))
                results.append({"agent": agent.name, "output": outcome.output})
                failed = failed or not outcome.success
            except Exception as exc:
                logger.exception("Step %d (%s) failed", i, agent.name)
                results.append({"agent": agent.name, "output": f"Step failed: {exc}"})
                failed = True
        return {"results": results, "failed": failed}

    async def _synthesise_node(self, state: dict[str, Any]) -> dict[str, Any]:
        results = state.get("results", [])
        if len(results) == 1:
            return {"answer": results[0]["output"]}
        summary = "\n\n".join(f"### {r['agent']}\n{r['output']}" for r in results)
        response = await self._router.chat(
            [
                Message.system(
                    "You are JARVIS. Merge the specialist results below into one clear, "
                    "complete answer to the user's request. Do not mention the internal "
                    "team structure unless it aids understanding."
                ),
                Message.user(f"Request: {state['request']}\n\nSpecialist results:\n{summary}"),
            ],
            options=ChatOptions(temperature=0.4),
            requirements=TaskRequirements(),
        )
        return {"answer": response.content}
