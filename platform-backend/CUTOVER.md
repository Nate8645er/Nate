# Cutover-Runbook — schrittweise Umschaltung auf das platform-backend

Additiv und umkehrbar. Jeder Schritt ist ein Feature-Flag; Standard = AUS =
bestehendes Verhalten (lokaler Orchestrator, Supabase-Login). Reihenfolge so
gewählt, dass jederzeit zurückgeschaltet werden kann.

## Stufen

### 0 — Backend bereitstellen (kein Kundeneffekt)
`docker compose -f docker-compose.dev.yml up -d` (Dev) bzw. `kubectl apply -k
deploy/k8s` (Prod). Prüfen: `/health/ready` grün, `/metrics` scrape-bar.
Noch kein App-Flag gesetzt → die verkaufte App ist unverändert.

### 1 — Live-Kennzahlen im v2-Dashboard
`PLATFORM_BACKEND_URL=https://<backend>` in der App setzen. Das v2-Dashboard
zeigt echte CPU/RAM/GPU statt „—". Kein Auth nötig (nur /health/compute).
**Rollback:** Variable entfernen → wieder „—".

### 2 — Keycloak-Login (Alternative zu Supabase)
Voraussetzung: Keycloak mit Realm (Beispiel: `deploy/keycloak/realm-ki.json`).
App-Env: `NEXT_PUBLIC_KEYCLOAK_AUTH=1`, `NEXT_PUBLIC_KEYCLOAK_ISSUER`,
`NEXT_PUBLIC_KEYCLOAK_CLIENT_ID`, `NEXT_PUBLIC_KEYCLOAK_REDIRECT_URI`.
Login-Einstieg: `GET /api/auth/keycloak/start` → Redirect → Callback setzt ein
HttpOnly-`kc_access`-Cookie. Supabase bleibt parallel nutzbar.
**Rollback:** `NEXT_PUBLIC_KEYCLOAK_AUTH` entfernen → Route liefert 404, nur
Supabase.

### 3 — Missionen ans Backend delegieren
Backend-Env: `KEYCLOAK_ISSUER` (+ in Prod `KEYCLOAK_AUDIENCE` via Audience-
Mapper), `LOCAL_LLM_URL` (Ollama/vLLM) oder Cloud-Router.
App-Env: `NEXT_PUBLIC_USE_PLATFORM_BACKEND=1`. Die Mission-Route delegiert an
`POST /api/v1/missions`, WENN ein Backend-Token (Header `x-acc-backend-token`,
aus dem `kc_access`-Cookie) mitkommt. Schlägt das fehl (401/403/503/nicht
erreichbar), läuft der bestehende lokale Orchestrator weiter — kein Ausfall.
**Rollback:** `NEXT_PUBLIC_USE_PLATFORM_BACKEND` entfernen.

### 4 — Wissen (RAG) über das Backend
`POST /api/v1/knowledge/ingest` + `/search` (RBAC `knowledge:write`/`:read`,
mandantengetrennt). VectorStore = Qdrant (`QDRANT_URL`).

## Sicherheits-Pflichten vor Prod (aus SECURITY-REVIEW.md)
- DB-Rolle in `DATABASE_URL`: **NOBYPASSRLS**, kein Superuser (sonst RLS wirkungslos).
- Keycloak-**Audience-Mapper** setzen und `KEYCLOAK_AUDIENCE` erzwingen.
- Secrets extern injizieren (kein Klartext im Git/Manifest).

## Live verifiziert (diese Umgebung)
- Auth-Kette end-to-end: echtes Keycloak-Token (Realm `ki`, User `demo`) →
  echtes JWKS → Signaturprüfung → `GET /api/v1/me` liefert den Principal
  (`roles:["member"]`, `email:demo@example.com`). Manipuliertes/fehlendes Token → 401.
- RBAC: `member` besitzt `agent:run` → `/api/v1/missions` passiert die Prüfung
  und antwortet ehrlich 503 ohne verbundenes LLM.
- Routing-Policy: `local_only → local`, `vision → cloud+fallback`.
- Compute: v2-Dashboard rendert echte Hardware, wenn `PLATFORM_BACKEND_URL` gesetzt ist.
