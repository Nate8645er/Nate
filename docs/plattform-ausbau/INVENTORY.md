# INVENTORY.md — Bestandsaufnahme (Phase 0, rein lesend)

Stand: Analyse am aktuellen `HEAD` von Branch `claude/ki-system-redesign-rollout-5nhzzg`.
Alle Angaben sind an den echten Dateien geprüft; nicht Verifizierbares ist als solches markiert.

## 1. Monorepo-Überblick

Wurzel `/home/user/Nate` enthält mehrere unabhängige Projekte. Das **„KI-System"** im Sinne des
Auftrags ist ausschließlich **`ai-command-center/`**. Die übrigen Verzeichnisse sind nicht Teil des
auszubauenden Produkts und bleiben unberührt.

| Verzeichnis | Was | Bezug zum Ausbau |
|---|---|---|
| `ai-command-center/` | Verkauftes SaaS (Next.js). **Das KI-System.** | **Kern** (`core/` im Zielbild) |
| `websites/` | Shop-Theme (Shopify) + Agentur-Site (GitHub Pages) | Verkauf/Marketing, kein Code-Bezug |
| `tools/modell-rat-mcp/` | Interner MCP-Server (Node, dependency-frei) | Nur Dev-Werkzeug |
| `tools/agent-frameworks/`, `tools/integrations/` | Notizen/Requirements | Referenz |
| `ki-agentur-setup/` | Windows-Setup + Plugin-Doku | Kein Bezug |
| `javier-mobile/` | Separate Python-App (Render, `render.yaml`) | **Nicht** das KI-System |
| `ultra-enterprise-os/` | Claude-Code-Plugin (Agents/Skills) | Nur Dev-Werkzeug |
| `.claude/` | Agents, Skills, Hooks, Memory | Nur Dev-Werkzeug |

> Klarstellung: Die `render.yaml` in der Wurzel deployt **javier-mobile**, nicht das KI-System.
> Das KI-System deployt auf **Vercel** (siehe §5).

## 2. Sprachen & Laufzeit (ai-command-center)

- **TypeScript 5**, **Next.js 16.2.10** (App Router, Turbopack), **React 19.2.4**.
- **Tailwind CSS v4** (`@tailwindcss/postcss`), Vitest 3.2.7 als Testrunner.
- Paketmanager laut `vercel.json`: **pnpm**. Node-Server-APIs in Gebrauch (`node:async_hooks`,
  `node:child_process` in Tools).
- Umfang: **~21.300 Zeilen** in `lib/` + `app/` (`.ts`/`.tsx`).

Laufzeit-Abhängigkeiten (`package.json`) sind bewusst schlank:

```
dependencies:    next 16.2.10 · react 19.2.4 · react-dom 19.2.4 · pdf-parse ^2.4.5
devDependencies: tailwindcss ^4 · @tailwindcss/postcss ^4 · vitest ^3.2.7 · typescript ^5
                 · eslint ^9 · eslint-config-next 16.2.10 · @types/{node,react,react-dom}
```

Es gibt **keine** LLM-SDKs, kein LangChain, kein ORM als Dependency: LLM-Aufrufe, Supabase und
Stripe laufen über **direktes `fetch`** gegen die jeweiligen REST-APIs (dependency-frei, siehe
`ARCHITECTURE-AS-IS.md`).

## 3. Einstiegspunkte

**API-Routen** (`app/api/**/route.ts`, 14 Stück):

```
mission          POST  SSE-Stream einer Multi-Agent-Mission (Kernpfad; maxDuration 300 s)
chat             POST  Kurz-Assistent (KI-Chat)
email            POST  E-Mail-Entwurf/-Antwort
bild             POST  Bild-Beschreibung/OCR (Vision)
extract          POST  Dokument-Text-Extraktion (pdf-parse)
license          -     Lizenz-Erzeugung/-Prüfung (LICENSE_SECRET)
mein-abo         GET   Abo-Status-Lookup
portal           POST  Stripe-Kundenportal-Link
checkout         POST  Stripe-Checkout-Session
stripe/webhook   POST  Zahlungs-Events → Supabase `abos`
shopify/webhook  POST  Shopify-Kauf → Lizenz erzeugen + mailen
auth/login       POST  Supabase-GoTrue-Login
auth/register    POST  Supabase-GoTrue-Registrierung
admin/generate   POST  Admin-Generierung (ADMIN_SECRET)
```

**UI-Seiten** (`app/*/page.tsx`, 28 Stück): `dashboard, assistent, chat, kunden, email,
faehigkeiten, workflows, freigabe, onboarding, studio, werkzeuge, berichte, analysen, agenten,
team, benutzer, einstellungen, integrationen, erweiterungen, konto, kamera, sicherheit, status,
admin, preise, kontakt, produkt/[id]` (+ Landing `/`).

## 4. Kern-Bibliotheken (`lib/`)

| Modul | Zweck |
|---|---|
| `agents/providers.ts` | **Provider-agnostischer LLM-Client** `callLLM` (9 Anbieter + `local`) |
| `agents/orchestrator.ts` | Mission: Commander → Worker (parallel) → Quality → Synthese, SSE-Emit |
| `agents/team.ts` | `WORKERS_BY_PLAN`, `WORKFORCE_BY_PLAN`, `ORG_MODE_PLANS`, `MAX_DYN_AGENTS` |
| `agents/demo.ts` | **Demo-Fallback** ohne LLM-Key (echte Struktur, kein Platzhalter-Fake) |
| `agents/memory.ts` | Langzeitgedächtnis (Supabase-Tabelle `gedaechtnis`) |
| `agents/browser.ts` | Browser-Agent-Bausteine |
| `agents/zuverlaessigkeit.ts` | JSON-Reparatur + Retry/Backoff (rein, testbar) |
| `agents/roster.ts`, `talentpool.ts` | Sichtbare Belegschaft (statisch generiert, keine LLM-Kosten) |
| `features.ts` | **Feature-Gating je Abo** (`BEREICH_MIN_PLAN`, `hatZugriff`) |
| `license.ts` | `PLAN_LIMITS` (Missionen/Tag je Plan), Lizenz-Signatur/-Prüfung |
| `shopify-license.ts`, `stripe.ts`, `supabase.ts` | Zahlung/Auth/DB (REST, honest not-configured) |
| `integrations/*`, `connectors.ts` | Integrations-Registry (self-hosted + SaaS), Status |
| `ratelimit.ts` | Per-IP-Rate-Limit (Upstash Redis, In-Memory-Fallback) |
| `mail.ts`, `vision.ts`, `skills.ts`, `vorlagen.ts`, `roi.ts`, `kunden.ts`, `freigabe.ts`, `onboarding.ts`, `blitz.ts`, `aufnahme.ts`, `willkommen.ts` | Fachlogik |

## 5. Deployment & Konfiguration

- **Ziel: Vercel** (`vercel.json`: `framework nextjs`, `pnpm`, `functions."app/api/mission/route.ts".maxDuration = 300`).
- **Sicherheits-Header** global in `next.config.ts` (CSP `frame-ancestors 'none'; object-src 'none'; base-uri 'self'`, HSTS, X-Frame-Options DENY, Permissions-Policy, nosniff).
- `serverExternalPackages: ["pdf-parse", "pdfjs-dist"]`.

## 6. Externe Dienste (aus `.env.example`, alle optional mit ehrlichem Fallback)

| Dienst | Env | Rolle |
|---|---|---|
| LLM-Anbieter | `ANTHROPIC/OPENAI/MOONSHOT/GOOGLE/XAI/QWEN/DEEPSEEK/MISTRAL/META_*_API_KEY`, `*_LLM_URL` | Modellzugriff (Cloud) |
| Lokales Modell | `LOCAL_LLM_URL`, `LOCAL_LLM_MODEL`, `LOCAL_LLM_API_KEY` | **Ollama/vLLM/LM-Studio** (OpenAI-kompatibel) |
| Supabase | `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY` | **Postgres + Auth (GoTrue) + RLS** |
| Upstash Redis | `UPSTASH_REDIS_REST_URL`, `UPSTASH_REDIS_REST_TOKEN` | Rate-Limit/Cache |
| Stripe | `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET` | Zahlung/Abo |
| Resend | `RESEND_API_KEY`, `MAIL_FROM` | E-Mail-Versand |
| Sonstiges | `LICENSE_SECRET`, `ADMIN_SECRET`, `APP_URL`, `VISION_MODEL` | Lizenz/Admin/Vision |

## 7. Datenmodell (`supabase/schema.sql`)

Zwei Tabellen, **Row-Level-Security aktiv**, **ohne** anon/authenticated-Policy → Zugriff nur
serverseitig über `SUPABASE_SERVICE_ROLE_KEY`:

- **`public.abos`** — `customer_id` (PK, Stripe `cus_…`), `email`, `plan_id`, `status`,
  `event_zeit` (Reihenfolge-Schutz), `license_key`, `aktualisiert_am` (Trigger). Index auf `email`.
- **`public.gedaechtnis`** — `id`, `user_id`, `text`, `zeit` (Recency), `tags text[]`, `erstellt`.
  Index `(user_id, zeit desc)`.

Es gibt **kein** explizites `tenant_id`/`org`-Konzept: „Mandant" = Stripe-`customer_id` bzw.
Supabase-`user_id`. Der Abo-Plan im UI liegt **clientseitig** (`localStorage acc-plan`); serverseitig
schützt der Mission-Pfad über Lizenz-/Usage-Token.

## 8. Tests

20 Test-Dateien in `test/` (Vitest). Abgedeckt: features, license, shopify-license, preise, roi,
mail, kunden, memory, integrations, ratelimit, vision, vorlagen, freigabe, aufnahme, blitz,
demo-org, dokumente, daten, zahlung-login, zuverlaessigkeit. Ergebnis: siehe `BASELINE.md`.

## 9. Was NICHT vorhanden ist (relevant für den Ausbau)

- Kein persistenter Server-Prozess / Worker (Vercel-Functions sind ephemer, max. 300 s).
- Keine GPU-/Compute-Abstraktion, kein lokales Modell-Scheduling (nur „URL zeigen auf externes
  lokales Modell").
- Keine Durable-Workflow-Engine (kein Temporal), kein 24/7-Agentenbetrieb.
- Keine Vektor-DB-Anbindung (Memory ist Text in Postgres, kein Embedding-Retrieval).
- Kein explizites RBAC/Mandanten-Modell über `customer_id` hinaus, kein Audit-Log-Schema.
