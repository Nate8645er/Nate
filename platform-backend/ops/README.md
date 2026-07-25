# Betrieb — Werkzeuge

## Das KI-Team ("Council") — echte Zweitmeinungen von 13 Anbietern

`ops/council.py` fragt über **OpenRouter** wirklich verschiedene Anbieter-Modelle
(nicht 13× dasselbe Modell) und sammelt ihre unabhängigen Antworten. Nützlich
für Architektur-Entscheidungen, bei denen eine zweite, andersartige Sicht mehr
bringt als eine weitere Runde desselben Modells.

```bash
set -a; . ./.env; set +a          # OPENROUTER_API_KEY laden
python3 ops/council.py --dry-run "Frage"          # zeigt nur, wer gefragt wuerde (0 Kosten)
python3 ops/council.py --only OpenAI,Google "Frage"
python3 ops/council.py "Frage"                     # alle 13
python3 ops/council_check.py                       # Verfuegbarkeits-Check aller 13
```

**Die 13 Mitglieder** (je das stärkste real existierende Modell pro Anbieter,
IDs aus dem Live-Katalog, per `council_check.py` verifiziert — **13/13 haben
wirklich geantwortet**):

| Anbieter | Modell-ID |
|---|---|
| OpenAI | `openai/gpt-5.6-sol-pro` |
| Anthropic | `anthropic/claude-opus-4.8` |
| Google | `google/gemini-3.1-pro-preview` |
| xAI | `x-ai/grok-4.5` |
| Moonshot | `moonshotai/kimi-k3` |
| DeepSeek | `deepseek/deepseek-v4-pro` |
| Alibaba | `qwen/qwen3.7-max` |
| Meta | `meta-llama/llama-4-maverick` |
| Mistral | `mistralai/mistral-large-2512` |
| Z-AI | `z-ai/glm-5.2` |
| Microsoft | `microsoft/phi-4` |
| Cohere | `cohere/command-a` |
| NVIDIA | `nvidia/nemotron-3-ultra-550b-a55b` |

**Wichtig zur Ehrlichkeit:** Mehrere kursierende Modellnamen existieren *nicht*
(geprüft gegen den Live-Katalog): „GPT-5.6 Sol Ultra", „Gemini 3.1 Pro Ultra",
„Grok 4.5 Heavy", „Qwen 3.8 Max", „Mistral Large 3", „Command A+",
„Nemotron Ultra". Die Tabelle oben enthält nur IDs, die wirklich antworten.

**Kosten:** Jeder Lauf verbraucht echte OpenRouter-Credits. Ein Durchlauf aller
13 mit kurzer Frage lag bei ~2.1k Token rein / ~2.9k raus. `--dry-run` zeigt die
Auswahl ohne zu senden. Reasoning-Modelle (Gemini, Kimi, DeepSeek, GLM)
verbrauchen ihr Budget zuerst intern — bei zu kleinem `--max-tokens` kommt eine
leere Antwort zurück; das ist kein Ausfall, sondern ein zu enges Limit.

---

# Backup & Wiederherstellung (Phase 7)

## Backup

```bash
DATABASE_URL_ADMIN=postgresql://postgres:...@host:5432/platform \
  ops/backup.sh ./backups
```

Nutzt `pg_dump --format=custom`, schliesst `schema_migrations` bewusst aus
(Begründung siehe Kommentar in `backup.sh`). Für einen Produktivbetrieb als
Cron/Scheduled-Job einplanen (z. B. täglich) und die Dumps versioniert extern
ablegen (nicht im selben Cluster wie die Quelle).

## Restore

```bash
DATABASE_URL_ADMIN=postgresql://postgres:...@host:5432/<ziel-db> \
  ops/restore.sh backups/platform_<stamp>.dump

# Pflicht-Folgeschritt: Rollen/Grants wiederherstellen (das Skript weist
# selbst darauf hin). schema_migrations ist nicht im Dump -> migrate()
# laeuft vollstaendig neu, sicher weil jede Migration idempotent ist:
MIGRATE_DATABASE_URL=<privilegiert> DATABASE_URL=<app_rw-Verbindung> \
  python -m app.migrate
```

**Wichtig:** Niemals ungeprüft gegen eine Produktions-Zieldatenbank
restaurieren. Für die Wiederherstellungsprobe eine frische, temporäre
Datenbank verwenden (`ops/restore.sh` erwartet keine bestehenden Daten im
Ziel — `pg_restore --clean --if-exists` räumt vorher auf).

## Wiederherstellungsprobe — durchgeführt und bestätigt

Der komplette Zyklus wurde real ausgeführt (nicht nur beschrieben):

1. Mandant + Agent über die laufende Anwendung angelegt (Quelle: temporärer
   Postgres-Cluster, DB `platform`).
2. `ops/backup.sh` → Dump geschrieben (Custom-Format, ohne `schema_migrations`).
3. Frische, leere Ziel-DB (`restore_target`) angelegt.
4. `ops/restore.sh` → Daten + Schema + RLS-Policies wiederhergestellt.
5. `python -m app.migrate` gegen die Ziel-DB → Rolle `app_rw` + alle Grants
   erneut gesetzt (bewusst getestet: **ohne** diesen Schritt schlägt der
   Zugriff mit `permission denied` fehl — deshalb ist er im Skript-Output
   als Pflichtschritt vermerkt, nicht optional).
6. Verbindung als `app_rw` gegen die Ziel-DB: derselbe Mandant (gleiche
   UUID), derselbe Agent sind vorhanden. Ohne gesetzten Mandantenkontext
   liefert `agents` **0 Zeilen** — RLS ist nach dem Restore weiterhin wirksam,
   nicht nur die Rohdaten sind da.

Ergebnis: **Backup → Restore → Rechte → RLS** funktioniert durchgängig und
ist nicht nur behauptet, sondern einmal vollständig durchgespielt.

## Lasttest — durchgeführt

```bash
DATABASE_URL=postgresql://app_rw:...@host/db \
MIGRATE_DATABASE_URL=postgresql://postgres:...@host/db \
ADMIN_TOKEN=... \
  python ops/loadtest.py --concurrency 20 --requests 1000 --path /v1/models
```

Treibt echte Requests gegen die echte FastAPI-App (ASGI in-process via
`httpx.ASGITransport`) — durchläuft Auth, RLS-gebundene DB-Zugriffe und
JSON-Serialisierung wie im echten Betrieb. Bewusst **nicht** durch einen
echten uvicorn-Prozess/Netzwerk-Stack getunnelt (kein Reverse-Proxy hier zu
testen); `/v1/chat` bewusst ausgeklammert, da es ein laufendes LiteLLM-Gateway
braucht, das hier nicht verfügbar ist.

**Real gemessen** (gegen den temporären Postgres-Cluster dieser Session):

| Pfad | Nebenläufigkeit | Requests | Fehler | Durchsatz | p50 | p95 | p99 |
|---|---|---|---|---|---|---|---|
| `/v1/models` | 20 | 1000 | 0 | 337.7 req/s | 2.9 ms | 3.6 ms | 4.5 ms |
| `/v1/usage`  | 20 | 1000 | 0 | 280.6 req/s | 3.5 ms | 4.4 ms | 5.5 ms |
| `/v1/models` | 50 | 2000 | 0 | 349.7 req/s | 2.8 ms | 3.4 ms | 3.8 ms |

Bei Nebenläufigkeit 50 — über der DB-Connection-Pool-Größe von 10
(`app/db.py`) — bleiben alle Requests fehlerfrei; `psycopg_pool` queued
wartende Anfragen, statt sie abzulehnen. Durchsatz bleibt stabil.

**Ehrliche Grenzen dieses Tests:** Single-Prozess, in-process (kein
Netzwerk/Reverse-Proxy, keine mehreren uvicorn-Worker), gegen eine lokale
Test-DB. Für eine Kapazitätsaussage zur echten Produktionsumgebung (Hosting,
Worker-Anzahl, Netzwerklatenz zu Postgres/LiteLLM) reicht das nicht — dafür
bräuchte es einen Test gegen die tatsächliche Zielinfrastruktur.

## Monitoring

`/health` liefert Liveness + DB-Erreichbarkeit. `/metrics` liefert
Prometheus-Metriken (`app/metrics.py`), ohne Auth (keine mandantenspezifischen
Daten, nur globale Zähler/Histogramme):

- `http_requests_total{method,route,status}` — Requests, mit **Routen-Vorlage**
  statt rohem Pfad (`/v1/agents/{agent_id}`, nicht die echte UUID) — verhindert
  Kardinalitäts-Explosion in Grafana/Prometheus, real getestet (zwei
  verschiedene IDs landen im selben Label).
- `http_request_duration_seconds{method,route}` — Latenz-Histogramm.
- `chat_completions_total{model}` / `chat_tokens_total{model,direction}` —
  fachliche Zahlen aus `app/completions.py`.

Anbindung an ein Grafana-Dashboard (Master-Prompt Kap. 3.2) ist der nächste
Schritt, sobald eine echte Prometheus-Instanz läuft — der Scrape-Endpunkt
selbst ist fertig und getestet.
