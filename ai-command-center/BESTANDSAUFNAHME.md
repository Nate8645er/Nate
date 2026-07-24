# Phase 0 – Bestandsaufnahme AI Command Center

Stand: Analyse durch das Team (Architektur, Security, Agenten/Integrationen, QA/Betrieb),
rein lesend, nichts verändert. Ehrliche Einordnung, Befunde mit Datei-Belegen.

## Gesamturteil
Solide gebauter **Single-Tenant-MVP** mit überdurchschnittlichem Security-Handwerk
(HMAC-Lizenzen, `timingSafeEqual`, CSP/HSTS, SSRF-Schutz im KI-Browser, ehrliche
LIVE-/„geplant"-Kennzeichnung). **Strukturell noch nicht enterprise-/multi-tenant-fähig**
und ohne Qualitätssicherung (Tests/CI/Monitoring = faktisch Null). Das sind die zwei
großen Baustellen vor „firmentauglich".

## Ist-Zustand (real)
- **Stack:** Next.js 16.2.10, React 19, Tailwind 4, TypeScript; Deploy-Ziel Vercel.
- **Datenhaltung = Browser:** Kunden-/Missionsdaten in `localStorage` (79 Fundstellen in 13 Dateien).
  Keine Datenbank, keine serverseitige Persistenz. `app/dashboard/page.tsx` trägt selbst ein
  „TODO Phase 2: serverseitig je Benutzer persistieren".
- **Lizenz/Usage:** stateless per HMAC-SHA256 (`lib/license.ts`), Token im `localStorage`,
  gehen als Header `x-acc-license`/`x-acc-usage` mit. Plan wird aus dem Token abgeleitet.
- **KI real:** Orchestrator (Commander→Worker parallel→Quality→Synthese), Modell-Rat `/api/rat`,
  KI-Browser (echte Web-Recherche mit SSRF-Schutz), Chat/E-Mail/PDF-Extract – alles echt,
  mit deterministischem Demo-Fallback pro Agent bei fehlendem Key/Fehler.
- **Shopify-Webhook:** echter externer Aufruf (HMAC-verifiziert) – nur für die eigene
  Lizenz-Auslieferung, kein Kunden-Connector.
- **Fehlerbehandlung:** try/catch in allen 8 API-Routen, `app/error.tsx`-Boundary,
  Input-Längen gekappt. a11y-Basis vorhanden (`lang`, viele `aria-label`).

## Ist-Zustand (Katalog / Vorschau / geplant)
- **Integrationen (15 Connectors):** reiner statischer Katalog (`lib/connectors.ts`), **keine**
  echte OAuth-/API-Verbindung, keine `app/api/connectors/*`-Route. Ehrlich deklariert, aber 0 % live.
- **Skills:** Prompt-Vorlagen ohne eigene Ausführungslogik.
- **Belegschaft „bis 1000" / Talentpool „1 Mrd.":** generierte Strings; real rufen nur
  MAX_DYN_AGENTS (12/24) ein LLM.

## Schwachstellen (priorisiert)

### KRITISCH
1. **Keine Datenbank / keine serverseitige Datenhoheit** – Gerätewechsel = Datenverlust,
   kein Backup, kein Audit, kein DSGVO-Nachweis. (`app/dashboard/page.tsx`, 13 localStorage-Dateien)
2. **Keine Mandantentrennung (Multi-Tenant) & kein RBAC** – kein Tenant/Org-Konzept, keine Isolation.
3. **Keine echte Authentifizierung** – Identität = Besitz eines frei kopierbaren Lizenz-Tokens.
4. **Integrationen ohne jede echte Verbindung** – Kernversprechen „KI arbeitet in Ihrem System"
   ist nicht implementiert (kein Token-Store, kein Adapter). (`lib/connectors.ts`, `app/integrationen`)
5. **Kein Human-in-the-Loop / kein Audit-Log** – heute tolerierbar (nur Text), aber Blocker,
   sobald Connectors schreibend werden.
6. **Keine Tests, kein CI** – 0 Testdateien, kein `.github/workflows`. Kritische Logik
   (HMAC, Lizenz, Limits, PDF-Extract, SSE) ungetestet.

### HOCH
7. **Tageslimit client-seitig umgehbar** – Usage-Token verwerfen → Zähler 0 (`lib/license.ts:22`).
   Kein serverseitiger Zähler → reale LLM-Kosten missbrauchbar.
8. **Admin-Passwort = Signatur-Secret** bei Default (`ADMIN_SECRET` fällt auf `LICENSE_SECRET`
   zurück, `app/api/admin/generate/route.ts`) + **kein Rate-Limiting/Bruteforce-Schutz**.
9. **Geteilte globale LLM-Keys** – keine Kosten-Zuordnung/Budget pro Tenant.
10. **Mission-Failover schwächer als Chat** – fällt ein Provider aus, springt der Agent direkt
    in Demo; Demo-Text kann unbemerkt ins Kundenergebnis (`lib/agents/orchestrator.ts:707-722`).
11. **Dev-Fallback-Secret** im Repo greift, wenn `NODE_ENV` ≠ „production" – Token fälschbar.
12. **Kein Monitoring/Observability** – nur `console.*`, keine Alerts/strukturierten Logs.

### MITTEL
13. Shopify-Webhook ohne Replay-/Idempotenzschutz (Retries → Mehrfach-Lizenz).
14. Modell-IDs teils frei erfunden (`claude-fable-5`, `gemini-3-ultra`, `grok-5`) → ohne
    `<PROVIDER>_MODEL`-Override 400 → stiller Demo-Fall.
15. a11y-Kontrast: helle Muted-Töne (`#8d8172` u.a. auf hellem Grund) ~3:1 < WCAG-AA 4.5:1.
16. Keine Input-Schema-Validierung (kein zod), manuelles Casting.
17. HTML-Injektion: `vorname` unescaped in Kunden-Mail (`app/api/shopify/webhook/route.ts`).

## Umsetzungsplan (Phasen)
**Fundament (Voraussetzung für Enterprise):**
- Postgres + Auth-Layer (z. B. Neon/Supabase + Auth.js), Modell `tenant → user → membership(role)`.
- Alles am Tenant verankern (Missionen/Ergebnisse/Usage serverseitig, jede Query mit `tenant_id`).
- Serverseitiges Quota-/Kosten-Enforcement; per-Tenant-Provider-Keys (verschlüsselt).

**Phase 1 – Kernplattform & Agenten:** echter Integrations-Hub (OAuth2-Route, verschlüsselter
Token-Store, Adapter-Interface; erst 1–2 reale Connectors statt 15 Attrappen), Workflow-Analyse
→ Agenten-Vorschläge, Human-in-the-Loop + append-only Audit-Log, Skills→Tools mit Connector-Bindung.

**Phase 2 – Design & Dashboard:** heller Look ist über ~13/14 Seiten ausgerollt (Dashboard folgt),
Widget-Dashboard, dezente animierte Büroszene (abschaltbar), a11y-Kontraste auf AA.

**Phase 3 – Shop & Video-Onboarding:** Shop-Redesign hell, pro-Abo Video-Onboarding-Bereich
mit interaktiven Checklisten/Tooltips (Videos modular/versioniert, mit Higgsfield erzeugt).

**Phase 4 – Qualität & Betrieb:** Vitest-Unit-Tests (Lizenz/HMAC/Limits zuerst), GitHub-Actions-CI
(lint + tsc + test + build), Monitoring (Sentry + strukturierte Logs), Rate-Limiting, zod-Validierung.

## Quick-Wins (klein, sicher, ohne externe Wirkung)
- `vorname` in der Webhook-Mail HTML-escapen (Befund 17).
- a11y: Muted-Text-Ton dunkler für AA (Befund 15).
- Vitest + erste Unit-Tests für `lib/license.ts` + CI-Workflow (Befund 6).
- Mission-Failover an Chat angleichen; Demo-Ergebnisse hart als solche kennzeichnen (Befund 10).
