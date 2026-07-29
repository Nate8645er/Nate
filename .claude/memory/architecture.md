# Architektur
ai-command-center: Next.js 15 App Router, TS, Tailwind.
lib/agents/: types.ts, providers.ts (Claude/OpenAI/Moonshot, Timeout+Retry),
team.ts (Registry, WORKERS_BY_PLAN, MAX_DYN_AGENTS, WORKFORCE_BY_PLAN),
orchestrator.ts (Fan-out + Org-Phase, Demo-Fallback, harte Timeouts),
demo.ts. app/api/mission (SSE), app/api/license (Key->Token). lib/license.ts
(HMAC, Plan-Limits, prod erzwingt LICENSE_SECRET).
