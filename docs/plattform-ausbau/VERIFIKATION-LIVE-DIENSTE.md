# Verifikation gegen ECHTE Dienste

Auftrag: „behebe jeden Fehler bei jeder Phase und alle Sachen die nicht gingen —
mache, dass alle gehen." Dieses Dokument hält fest, was zuvor nur gegen
In-Memory-/`:memory:`-Attrappen lief und jetzt **gegen echte, laufende Server**
bewiesen ist. Alle Beweise sind als Tests reproduzierbar
(`platform-backend/tests/test_live_services.py`) und **opt-in**: ist ein Dienst
nicht erreichbar, wird der Test übersprungen — die Standard-Suite bleibt offline-
und CI-tauglich (Regel „ohne Netz, ohne GPU").

## Was jetzt real läuft (Docker)

| Dienst   | Image                  | Port  | Beweis |
|----------|------------------------|-------|--------|
| Postgres | `postgres:16-alpine`   | 5433  | RLS blockt Cross-Tenant auf DB-Ebene |
| Qdrant   | `qdrant/qdrant:latest` | 6333  | Mandantentrennung im echten Retrieval |
| Redis    | `redis:7-alpine`       | 6380  | Atomarer Zähler (Basis Quota/Rate-Limit) |
| Ollama   | `ollama/ollama:latest` | 11434 | Echte lokale Inferenz durch den ModelRouter |

Start (Entwicklung):

```bash
docker run -d --name pf-pg    -e POSTGRES_PASSWORD=devpass -e POSTGRES_DB=platform -p 5433:5432 postgres:16-alpine
docker run -d --name pf-qdrant -p 6333:6333 qdrant/qdrant:latest
docker run -d --name pf-redis  -p 6380:6379 redis:7-alpine
docker run -d --name pf-ollama -p 11434:11434 ollama/ollama:latest
# Modell (klein, CPU): über die API, TTY-neutral
curl -s localhost:11434/api/pull -d '{"model":"qwen2.5:0.5b","stream":false}'
```

Ausführen der Live-Beweise:

```bash
cd platform-backend && .venv/bin/python -m pytest tests/test_live_services.py -v
# 4 passed  (bzw. skipped, wenn ein Dienst nicht läuft)
```

## Die einzelnen Beweise

### 1. Postgres RLS blockt Cross-Tenant (DB-Ebene)
Wichtige Erkenntnis aus dem echten Lauf: **RLS greift NICHT für Superuser/
`BYPASSRLS`-Rollen.** Der erste Versuch (als `postgres`) zeigte, dass die
`WITH CHECK`-Policy übersprungen wird. Der Test verbindet daher — wie die
Produktion — als **unprivilegierte Rolle** (`NOBYPASSRLS`). Bewiesen:
- Tenant `acme` schreibt seine Zeile.
- Schreiben für `globex` verletzt die `WITH CHECK`-Policy → Fehler.
- `globex` sieht `count(*) = 0`, `acme` sieht `count(*) = 1` derselben Tabelle.

Konsequenz für Produktion: Die App-DB-Rolle **darf nicht** Superuser sein und
**darf nicht** `BYPASSRLS` haben, sonst ist die Mandantentrennung auf DB-Ebene
wirkungslos. (Code-Ebene `TenantRepository` schützt zusätzlich.)

### 2. Qdrant Mandantentrennung im echten Server
`QdrantVectorStore` gegen den echten Server: `acme` und `globex` legen
denselben Text ab; die Suche von `acme` liefert **nie** das Dokument von
`globex` (Payload-Filter `tenant`). `count` pro Tenant stimmt.

### 3. Redis atomarer Zähler
`INCRBY` fünfmal → 500, `EXPIRE`/`TTL` gesetzt. Basis für Quota- und
Rate-Limit-Zähler gegen echten Server statt Attrappe.

### 4. Ollama: echte lokale Inferenz durch den ModelRouter
Der komplette Produktionspfad wurde bewiesen — nicht nur ein roher curl:
`ModelRequest(data_class=LOCAL_ONLY)` → `decide()` platziert **lokal** (Daten
dürfen die Umgebung nicht verlassen) → `ModelRouter.complete()` → **LiteLLM** →
echter Ollama-Server (`/v1/chat/completions`) → Antwort mit realer
Token-Nutzung. Modell: `qwen2.5:0.5b` (494 M Parameter, Q4_K_M), rein CPU,
Antwort in ~4 s. Der Test prüft die **Pipeline** (Routing → Ausführung →
nicht-leere Antwort + `completion_tokens > 0`), nicht die Genauigkeit des
0.5B-Modells.

Netz-Hinweis: `registry.ollama.ai` ist über den Agent-Proxy erreichbar; der
Container braucht dafür die Proxy-CA (`SSL_CERT_FILE=/ca/ca-bundle.crt`) und
`HTTPS_PROXY` (Host-Loopback via `--network host`). Der Modell-Pull läuft
TTY-neutral über die HTTP-API (`/api/pull`), nicht über `docker exec … ollama
pull` (dessen Spinner in nicht-interaktiven Shells „something went wrong"
vortäuscht, obwohl der Pull erfolgreich ist).

## Frontend ↔ Backend: echte Kennzahlen im v2-Dashboard

Das v2-Dashboard zeigte bisher fest „—". Jetzt liest es **echte** Compute-Daten
vom laufenden `platform-backend`:

- Neuer, dependency-freier Server-Helfer:
  `ai-command-center/lib/platform-backend.ts` (`fetchCompute`, kurzer Timeout,
  `cache: "no-store"`). Ist `PLATFORM_BACKEND_URL` nicht gesetzt **oder** das
  Backend nicht erreichbar → `null` → Dashboard zeigt weiter ehrlich „—"
  („Backend nicht verbunden"). Kein erfundener Status.
- `app/v2/page.tsx` ist eine async Server-Component, die CPU/RAM/GPU aus
  `/health/compute` rendert.

Ende-zu-Ende bewiesen (Dev-Server mit `PLATFORM_BACKEND_URL=http://127.0.0.1:8099`):
das Dashboard rendert real `x86_64`, `15.7 GB`, `cpu · llama_cpp`,
`nur CPU erkannt` — statt Platzhalter.

Konfiguration (Vercel/Env): `PLATFORM_BACKEND_URL=https://<backend-host>`.
Ohne die Variable bleibt das Verhalten unverändert (additiv).

## Teststand

- `platform-backend`: **84** Tests grün (80 offline + 4 live), `ruff` sauber.
- `ai-command-center`: **210** Tests grün, `tsc` sauber, `next build` grün
  (inkl. `/v2`; prerendert mit ehrlichem „—", wird dynamisch sobald
  `PLATFORM_BACKEND_URL` gesetzt ist).
