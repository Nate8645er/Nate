# PHASE 0 — Risiken, Kollisionen, Phase-1-Plan

## A. Die fünf größten Risiken (mit konkreter Auswirkung)

1. **Serverless-Deploy vs. Dauerbetrieb.** Das Produkt läuft auf Vercel (ephemere Functions,
   Mission ≤ 300 s). Das Zielbild (`compute/`, 24/7-Agenten, Temporal, vLLM) braucht einen
   **langlebigen Server**. *Auswirkung:* Ohne eine zweite Laufzeit (eigener Backend-Dienst) ist
   Phase 2/5/6 nicht baubar; ein „Reinquetschen" in Vercel-Functions führt zu Timeouts und
   halbfertigen Läufen. Entscheidung über die Backend-Laufzeit ist ein Blocker für alles Schwere.

2. **Doppelte Fundamente (Zielstack vs. Ist-Stack).** Das Ist-System nutzt bereits **Supabase
   (Postgres+Auth+RLS)** und **Upstash Redis**; §3 wählt **Keycloak** und self-hosted
   Postgres/Redis. *Auswirkung:* Blind dem Zielstack folgen = funktionierende, getestete Auth/DB
   wegwerfen (verstößt gegen Regel „additiv, nie destruktiv") und doppelte Wartung. Muss vor
   Phase 1 entschieden werden (siehe Kollision C1/C2).

3. **Mandanten-Isolation nachträglich.** Heute gibt es kein `tenant`-Modell, nur
   `customer_id`/`user_id` + server-seitige RLS. Autonome Agenten mit Tool-Zugriff **vor** echter
   Isolation sind ein Datenleck-Risiko (Tenant A sieht Tenant B). *Auswirkung:* Wird Isolation
   erst in Phase 6 eingezogen, ist jeder in Phase 4/5 gebaute Agentenpfad nachträglich
   abzusichern — teuer und fehleranfällig. Der Phasenplan setzt Phase 6 bewusst vor Phase 7; das
   ist richtig, aber Agenten-Datenzugriffe in Phase 4/5 müssen schon `tenant_id`-fähig entworfen
   werden.

4. **Kostenexplosion durch Dauer-Agenten.** 24/7-Agenten erzeugen dauerhaft Tokens/Compute.
   Heute gibt es Tageslimits pro Plan (`PLAN_LIMITS`), aber **keine** Kostenobergrenze pro
   Tenant für Hintergrundläufe. *Auswirkung:* Ein fehlkonfigurierter Kunden-Agent kann unbegrenzt
   Kosten verursachen, die der Betreiber trägt. Budget-/Circuit-Breaker müssen mit dem
   Agenten-Runtime kommen (Phase 4), nicht erst in Phase 6.

5. **aarch64 / Unified-Memory-Annahmen (DGX Spark).** Die Zielhardware (GB10, ARM64, 128 GB
   unified memory) bricht zwei verbreitete Annahmen: „x86-Wheels/Images überall verfügbar" und
   „VRAM ≠ RAM". *Auswirkung:* Ein HAL, das `memory_model: dedicated` fest verdrahtet oder
   x86-only-Images voraussetzt, läuft auf genau der Zielhardware nicht. Muss ins Interface
   (`memory_model`, `arch`) — sonst Neubau in Phase 8.

## B. Kollisionen Zielbild (§2) ↔ Ist-Architektur — je eine Lösung

- **C0 — Laufzeit.** *Zielbild* legt `compute/agents/automation/platform` unter `core/`, als
  liefen alle in einem Prozess. *Ist:* `core/` = Vercel-App (serverless). **Lösung:** Zwei
  Laufzeiten. `core/` + `ui/` + `api/`-Gateway bleiben die Vercel-App; die schweren Schichten
  bilden einen **separaten Dienst** („platform-backend", eigener Container/Server), den die App
  über eine schmale HTTP/WS-Schnittstelle anspricht. Ports-&-Adapters bleibt gewahrt — die Grenze
  ist jetzt ein Netzwerk-Hop.

- **C1 — Auth: Keycloak (§3) vs. Supabase (Ist).** **Lösung/Empfehlung:** Supabase-Auth
  **behalten** (funktioniert, getestet, RLS-integriert). Keycloak erst einführen, wenn ein Kunde
  echtes Enterprise-SSO (SAML/OIDC-Federation) verlangt — dann als zusätzlicher IdP hinter einem
  `AuthProvider`-Interface, nicht als Ersatz. *(Gegenargument zu §3 — Entscheidung durch dich,
  siehe §D.)*

- **C2 — Modell-Router: LiteLLM (§B.2) vs. `providers.ts` (Ist).** **Lösung/Empfehlung:** Die
  vorhandene `callLLM`-Schicht (9 Anbieter + lokal, getestet, honest-fallback) **hinter das neue
  `models/ModelRouter`-Interface legen** und behalten. LiteLLM optional als *ein weiterer Adapter*
  im platform-backend (für lokale vLLM/Ollama-Orchestrierung dort), **nicht** als Ersatz des
  bestehenden Cloud-Pfads. Kein Wegwerfen getesteten Codes. *(Gegenargument zu §3 — siehe §D.)*

- **C3 — DB/Cache/Objektspeicher: self-hosted (§3) vs. managed (Ist: Supabase/Upstash).**
  **Lösung:** Solange die App auf Vercel liegt, bleiben **managed** Supabase-Postgres + Upstash
  korrekt (kein Betrieb nötig). Self-hosted Postgres/Redis/**MinIO** + **Qdrant** entstehen im
  platform-backend für die schweren Pfade (RAG-Vektoren, Objektspeicher, Agenten-State). Zwei
  Datenpfade, klar getrennt: „App-Metadaten" (Supabase) vs. „Plattform-Workloads" (backend).

- **C4 — Frontend: neue React/Vite-App (§7) vs. bestehendes Next-UI (Ist).** **Lösung:** Das neue
  Premium-UI **innerhalb der bestehenden Next-App** bauen (Design-Tokens + neue Screens hinter
  einem Feature-Flag), altes UI bleibt bis zur Ablösung lauffähig (Regel §7). Kein separates
  Vite-Projekt — das würde Auth/Routing/Deploy duplizieren.

- **C5 — Vektor-RAG: neue Qdrant-Schicht vs. Memory-in-Postgres (Ist).** **Lösung:** `gedaechtnis`
  (Postgres) bleibt für einfache Fakten/kleine Tenants (optional pgvector). Qdrant kommt in Phase 3
  im backend hinzu, hinter einem `VectorStore`-Interface; die Memory-Schicht wählt Backend nach
  Tenant-Größe. Additiv, kein Bruch.

- **C6 — MCP.** *Zielbild:* MCP-Client/-Server als Kern (§B.1 A). *Ist:* MCP existiert nur
  dev-seitig (`tools/modell-rat-mcp`, `.mcp.json`), nicht im Produkt. **Lösung:** MCP-Anbindung
  als neue `integrations/mcp`-Schicht im backend (Phase 5), am bestehenden Werkzeug-/
  Integrations-Register (`lib/integrations`, `lib/connectors`) andocken — nicht daneben.

## C. Phase-1-Plan (Fundament) — Vorschlag mit Aufwandsschätzung

> Phase 1 baut **kein Feature**, sondern das Gerüst, in das Phase 2+ passt. Additiv; die Vercel-App
> bleibt unverändert lauffähig. Schätzung in Personentagen (PT), 1 erfahrener Entwickler.

| # | Arbeitspaket | Inhalt | PT |
|---|---|---|---|
| 1.1 | **Repo-/Paketstruktur** | Neues `platform-backend/` (eigenes Deploy-Ziel) + gemeinsame Typen-Pakete; Ordner `compute/ models/ knowledge/ agents/ automation/ platform/ observability/` als leere, dokumentierte Module mit Interfaces | 2 |
| 1.2 | **Config-Layer** | Einheitliche, validierte Konfiguration (Zod/eigenes Schema), `honest not-configured` als Vertrag, `.env`-Doku, Secret-Handling (SOPS+age) | 2 |
| 1.3 | **Fehler-/Logging-/Tracing-Konvention** | OpenTelemetry-Instrumentierung ab Tag 1, strukturierte Logs, Fehlertypen, „nie werfen an Schichtgrenzen" | 2 |
| 1.4 | **Test-Setup & CI** | Vitest (TS) + pytest (falls Python-backend), GitHub-Actions: `tsc` + `vitest` + Build-Gate; Baseline als Pflichtschwelle | 2 |
| 1.5 | **`docker-compose.dev.yml`** | Lokale Dienste für spätere Phasen: Postgres, Redis, Qdrant, MinIO — **nur Dev**, klar getrennt vom Prod-Managed-Stack | 1 |
| 1.6 | **`LICENSES.md` + Lizenz-Gate** | Prozess + erste Einträge (Postgres, Redis, Qdrant, LiteLLM, Temporal, Keycloak) inkl. n8n-Ausschluss (Sustainable Use) | 1 |
| 1.7 | **Backend-Laufzeit-Entscheidung dokumentiert** | Node (Fastify/Nest) vs. Python (FastAPI) fürs platform-backend — Abwägung + Festlegung, da es alles Weitere prägt | 1 |

**Summe Phase 1: ~11 PT.** Ergebnis: ein Gerüst mit CI, Konfig, Observability-Haken und
Lizenz-Gate, ohne eine einzige bestehende Datei zu verändern.

## D. Offene Entscheidungen (§3 verlangt: erst Gegenargument, dann deine Entscheidung)

Diese drei Punkte ändere ich **nicht** eigenmächtig — sie widersprechen der Regel „additiv, nie
destruktiv", wenn man §3 wörtlich nimmt:

1. **Auth:** Supabase behalten (mein Vorschlag) vs. auf Keycloak migrieren (§3). — *Empfehlung:
   behalten*, Keycloak nur bei echtem SSO-Bedarf.
2. **Modell-Router:** bestehende `providers.ts` behalten + kapseln (mein Vorschlag) vs. durch
   LiteLLM ersetzen (§B.2). — *Empfehlung: behalten + kapseln*, LiteLLM nur als zusätzlicher
   Backend-Adapter.
3. **Backend-Sprache:** Node/TypeScript (nah am bestehenden Code, ein Typ-Ökosystem) vs.
   Python (näher an vLLM/Temporal-SDK/ML-Tooling). — *Empfehlung: Python fürs platform-backend*,
   weil vLLM, Temporal-Worker, Docling, Transformers und die meisten §B-Bausteine Python-nativ
   sind; die Vercel-App bleibt TypeScript.

Bis zu deiner Entscheidung baue ich in Phase 1 nur, was von diesen Punkten **unabhängig** ist
(Struktur, Config, CI, Observability-Haken, Lizenz-Gate).
