# ARCHITECTURE-AS-IS.md — Ist-Architektur (Phase 0)

Beschreibt das KI-System `ai-command-center/` **wie es heute ist**, nicht wie es werden soll.
Grundlage für die Kollisions-Analyse gegen das Zielbild (§2 des Auftrags).

## 1. Grundform

**Eine einzige Next.js-16-App (App Router) auf Vercel (serverless).** Es gibt keinen
langlebigen Server-Prozess: Jede API-Route ist eine kurzlebige Serverless-Function
(Mission bis 300 s, sonst Vercel-Standard). Zustand liegt **außerhalb** der App
(Supabase Postgres, Upstash Redis) oder **im Client** (`localStorage`).

```
Browser (React 19, localStorage: plan/branche/firma, Lizenz-/Usage-Token)
   │  fetch + SSE
   ▼
Next.js App Router  ──►  app/api/*/route.ts (serverless functions)
   │                        │
   │                        ├─ lib/agents/*  (Orchestrator, Provider-Router, Demo, Memory)
   │                        ├─ lib/license.ts (stateless Plan-/Usage-Token, HMAC)
   │                        ├─ lib/ratelimit.ts ──► Upstash Redis (REST)  [Fallback: In-Memory]
   │                        ├─ lib/supabase.ts ──► Supabase (GoTrue Auth · Postgres · RLS)
   │                        ├─ lib/stripe.ts ──► Stripe (Checkout · Portal · Webhook)
   │                        └─ lib/mail.ts ──► Resend
   ▼
LLM-Anbieter (Cloud: Anthropic/OpenAI/… · Lokal: LOCAL_LLM_URL → Ollama/vLLM)
```

Architekturstil heute: **schlanke Schichten über direktem `fetch`**, dependency-arm, mit dem
durchgehenden Prinzip **„honest not-configured"** — jede externe Anbindung meldet ehrlich, wenn
ihr Key/URL fehlt, statt zu faken (Supabase-Login, Rate-Limit, LLM-Provider, Zahlung).

## 2. Der Missions-Kernpfad (`POST /api/mission`)

1. **Auth/Limit stateless** (`lib/license.ts`): Header `x-acc-license` (signiertes Plan-Token,
   30 Tage), `x-acc-usage` (signierter Tageszähler), `x-acc-ultra`. Kein DB-Zugriff pro Request;
   `planFromLicenseToken` → Plan, `consumeUsage` → Limit/Tag, Emit `{type:"usage",…}`.
2. **Orchestrator** (`lib/agents/orchestrator.ts`): Commander erstellt Plan → Worker
   (`WORKERS_BY_PLAN`, parallel) → Quality-Report → Synthese. Ausgabe als **SSE-Stream**
   (`status`/`final`/`usage`-Events).
3. **Token-Budget** pro Mission via `AsyncLocalStorage` (`tokenBudgetStore`), plan-abhängig.
4. **Org-Modus** (BUSINESS/ENTERPRISE): dynamische Rollen, aber nur `MAX_DYN_AGENTS`
   (12/24) rufen wirklich ein LLM; der Rest ist sichtbare, statisch generierte Belegschaft
   (keine Provider-Kosten).

## 3. Modell-Zugriff (`lib/agents/providers.ts`) — bereits ein Router

`callLLM(provider, messages)` kapselt **9 Anbieter + `local`** hinter einem Interface:

- **Cloud:** anthropic (Messages-API), openai, moonshot, google, xai, qwen, deepseek, meta
  (alle OpenAI-kompatibel; Endpoint per `<PROVIDER>_LLM_URL` überschreibbar).
- **Lokal:** `local` mit `LOCAL_LLM_URL`/`LOCAL_LLM_MODEL`, `keyOptional` → **Ollama / vLLM /
  LM-Studio** sind heute schon anbindbar.
- Eigenschaften: Timeout 90 s, ein Retry bei Netz/5xx, `max_tokens` aus Budget,
  **wirft nie** (`{ok:false,error}`), `nichtKonfiguriert(provider)` wenn Key/URL fehlt.
- **Demo-Fallback** (`lib/agents/demo.ts`): ohne konfigurierten Anbieter läuft eine Mission
  vollständig mit echt strukturierter Demo-Ausgabe (Plan, Worker-Ergebnisse, Quality-Score,
  Synthese) — kein Platzhalter-Fake, klar als „Demo-Modus" markiert.

**Das ist faktisch bereits eine LiteLLM-artige Router-Schicht mit Cloud+Lokal.**

## 4. Zuverlässigkeit

`lib/agents/zuverlaessigkeit.ts`: `jsonReparieren` (erstes balanciertes JSON extrahieren/
reparieren, nie werfen), `mitWiederholung` (Backoff, injizierbarer Sleep), deterministische
Helfer. Rein, ohne Netz/GPU testbar.

## 5. Persistenz & Identität

- **Supabase Postgres** (`supabase/schema.sql`): `abos` (Abo/Lizenz je Stripe-`customer_id`),
  `gedaechtnis` (Langzeitgedächtnis je `user_id`). **RLS aktiv, ohne Client-Policy** → Zugriff
  nur serverseitig über `SUPABASE_SERVICE_ROLE_KEY`.
- **Auth: Supabase GoTrue** (`lib/supabase.ts`) per REST, RLS-basiert, honest not-configured.
- **Abo/Plan-Herkunft:** Stripe-Webhook → `abos`; Shopify-Webhook → Lizenz erzeugen + mailen.
  Lizenz-Token signiert (HMAC, `LICENSE_SECRET`).

## 6. Sicherheit heute

- Globale **Security-Header + CSP** in `next.config.ts` (kein Framing, kein object-src, HSTS).
- **Rate-Limit** (`lib/ratelimit.ts`) über Upstash-Redis-REST (instanzübergreifend), Fallback
  In-Memory (ehrlich als schwächer dokumentiert).
- Admin/License über signierte Secrets (`ADMIN_SECRET`, `LICENSE_SECRET`).
- Kein RBAC-Modell, keine Audit-Trail-Tabelle, keine Sandbox für Code-/Tool-Ausführung.

## 7. Frontend

Vollständiges App-Router-UI (28 Seiten), einheitliches `acc-*`-Designsystem, aktuell **dunkles
Premium-Skin** (globales `globals.css`), gemeinsame `WorkNav`. **Feature-Gating** je Abo über
`lib/features.ts` + `usePlanGate`/`PlanGate` (`app/components/PlanGuard.tsx`): Premium-Seiten
zeigen bei zu tiefem Abo einen Upgrade-Hinweis. Plan liegt clientseitig (`localStorage`).

## 8. Was die Architektur heute *nicht* kann (für das Zielbild entscheidend)

| Zielbild-Fähigkeit | Ist-Zustand |
|---|---|
| Dauerlaufende Agenten (24/7) | **Fehlt** — serverless, kein Worker, kein Scheduler |
| Durable Workflows | **Fehlt** — keine Temporal-artige Engine |
| GPU-/Compute-HAL, lokales Modell-Scheduling | **Fehlt** — nur „URL auf externes lokales Modell" |
| Vektor-RAG | **Teilweise** — Memory = Text in Postgres, **kein** Embedding-Retrieval |
| Mandanten-Isolation (echtes Multi-Tenant) | **Rudimentär** — `customer_id`/`user_id` + RLS, kein `tenant`-Modell/RBAC/Audit |
| Modell-Router Cloud+Lokal | **Vorhanden** (`providers.ts`) — Ausbaubasis, kein Neubau nötig |
| Ehrliche Fallbacks / Testbarkeit | **Stark vorhanden** — Muster, das der Ausbau übernehmen sollte |

## 9. Konsequenz für den Ausbau (Kurz)

Die schweren Zielbild-Schichten (`compute/` mit vLLM/GPU, `agents/`-Runtime im Dauerbetrieb,
`automation/` mit Temporal, self-hosted Qdrant/Postgres/MinIO/Keycloak) können **nicht in der
Vercel-App** leben. Sie gehören in einen **neuen, separaten Backend-Dienst**, den die bestehende
App über eine schmale HTTP-Schnittstelle aufruft. Die vorhandene App wird dabei zum `core/`- und
`ui/`-Layer des Zielbilds — additiv erweitert, nicht ersetzt. Details in der Kollisions-Analyse
(Chat-Bericht / `PHASE-1-PLAN`).
