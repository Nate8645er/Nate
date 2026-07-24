# Platform Backend — Produkt A (Fundament)

Mandantengetrenntes KI-Plattform-Backend. Phase-2-Ziel des Master-Prompts:
**ein Modell, ein Mandant, ein Chat — lauffähig**, mit Mandantentrennung auf
Datenbankebene (Row Level Security), Tarif-Durchsetzung und Verbrauchsmessung.

## Architektur (kurz)

```
Client ──Bearer API-Key──▶ FastAPI (dieses Backend)
                              │  Auth: api_keys → Mandant + Tarif
                              │  RLS:  SET LOCAL app.current_tenant
                              ▼
                          Postgres (RLS erzwingt Mandantentrennung)
                              ▲
        Chat ──▶ LiteLLM-Gateway ──▶ Anthropic / OpenAI / Ollama (lokal)
```

- **Mandantentrennung (real erzwungen)**: `migrations/001_init.sql` aktiviert
  `ENABLE`+`FORCE ROW LEVEL SECURITY` auf allen mandantengebundenen Tabellen.
  Entscheidend ist die **Rollentrennung**: die App verbindet sich zur Laufzeit
  als `app_rw` (NOSUPERUSER, NOBYPASSRLS, **nicht** Tabellen-Owner) — nur für
  eine solche Rolle greift RLS. Superuser/Owner umgehen RLS (auch mit FORCE),
  deshalb laufen **Migrationen über eine separate, privilegierte Verbindung**
  (`MIGRATE_DATABASE_URL`), die Laufzeit über `DATABASE_URL` (app_rw). Die App
  setzt pro Transaktion `app.current_tenant`; die DB filtert automatisch. Ein
  App-Bug kann keine fremden Zeilen liefern — bewiesen durch
  `tests/test_rls_integration.py` gegen eine echte DB.
- **`api_keys`** ist bewusst nicht RLS-gebunden: der Login-Lookup erfolgt über
  den global-eindeutigen, geheimen `key_hash`; ohne diese Ausnahme entstünde
  ein Henne-Ei-Problem (der Mandant wird erst durch den Lookup bestimmt).
- **Tarife**: `migrations/002_seed_plans.sql` (Free … Enterprise, Master-Prompt
  3.3). Modelle sind pro Tarif freigeschaltet, nicht pro Nutzer hart kodiert.
- **Gateway**: LiteLLM (`litellm/config.yaml`) — ein Zugang für alle Anbieter
  inkl. mindestens einem lokalen Modell (Ollama).
- **Verbrauch**: jede Chat-Antwort schreibt ein `usage_events`-Ereignis →
  Grundlage für Limit-Durchsetzung und spätere Abrechnung (Phase 4).

## Lokal starten

```bash
cp .env.example .env      # Pflichtwerte setzen: POSTGRES_PASSWORD, APP_DB_PASSWORD,
                          # LITELLM_MASTER_KEY, ADMIN_TOKEN (fehlt eines -> Start
                          # schlägt bewusst fehl, keine Default-Secrets)
docker compose up --build
```

Compose legt beim ersten Start via `db-init/01-app-role.sh` die eingeschränkte
Rolle `app_rw` an; die Migrationen (Owner-Rolle) erstellen Schema, Policies und
Grants. `migrate()` führt jede SQL-Datei genau einmal aus (Tracking-Tabelle
`schema_migrations`) — Neustarts gegen ein bestehendes Volume sind unkritisch.

Dann:

```bash
# 1) Mandant provisionieren (liefert einmalig den API-Key)
curl -sX POST localhost:8080/admin/provision \
  -H "X-Admin-Token: $ADMIN_TOKEN" -H 'Content-Type: application/json' \
  -d '{"tenant_name":"Acme","owner_email":"chef@acme.ch","plan_code":"pro"}'

# 2) Chat (mit dem zurückgegebenen api_key)
curl -sX POST localhost:8080/v1/chat \
  -H "Authorization: Bearer pk_..." -H 'Content-Type: application/json' \
  -d '{"model":"ollama/llama3.2","messages":[{"role":"user","content":"Hallo"}]}'

# 3) Verbrauch ansehen
curl -s localhost:8080/v1/usage -H "Authorization: Bearer pk_..."
```

## Endpunkte

| Methode | Pfad | Zweck | Schutz |
|---------|------|-------|--------|
| GET  | `/` | Statisches Chat-UI (Modellwechsel + Verbrauch) | — |
| GET  | `/health` | Liveness + DB-Check | — |
| POST | `/admin/provision` | Mandant + API-Key anlegen | `X-Admin-Token` |
| POST | `/v1/chat` | Chat via Gateway, mit Tarif-/Limit-Prüfung | Bearer API-Key |
| GET  | `/v1/models` | Im Tarif freigeschaltete Modelle (fürs UI-Dropdown) | Bearer API-Key |
| GET  | `/v1/usage` | Monatsverbrauch des Mandanten | Bearer API-Key |
| GET  | `/v1/conversations` | Liste der Unterhaltungen | Bearer API-Key |
| GET  | `/v1/conversations/{id}` | Eine Unterhaltung mit Nachrichten | Bearer API-Key |

## Tests

```bash
pip install -r requirements.txt pytest
pytest -q                                  # Unit-Tests (ohne DB)

# Zusätzlich der echte RLS-Laufzeitbeweis gegen eine Postgres-Testdatenbank:
PLATFORM_TEST_DATABASE_URL=postgresql://postgres:...@localhost:5432/platform pytest -q
```

Abgedeckt: Tarif-Logik, API-Key-Erzeugung/Hashing, Schema-Struktur (RLS/FORCE,
Idempotenz, api_keys-Ausnahme) sowie — mit gesetzter Test-DB — der
Laufzeit-Nachweis, dass `app_rw` nur die Zeilen des gesetzten Mandanten sieht
und ohne Kontext gar keine. Die CI (`platform-backend-ci.yml`) fährt dafür
einen Postgres-Service hoch.

## Sicherheit

- **RLS real erzwungen** über die eingeschränkte Rolle `app_rw` (nicht Owner,
  kein BYPASSRLS); Migrationen laufen getrennt über eine privilegierte Rolle.
- Keine Secrets im Code — alles aus `.env` (in `.gitignore`); Compose ist
  fail-closed (`${VAR:?}`), keine bekannten Default-Passwörter.
- API-Keys werden nur als SHA-256-Hash gespeichert, Klartext genau einmal
  ausgegeben. `pk_` + 256-Bit-Zufall.
- `/admin/provision` per konstant-Zeit-Vergleich gegen `ADMIN_TOKEN`.
- Chat: Payload-Grenzen (Länge/Anzahl Messages), Konversations-Eigentumsprüfung,
  generische Upstream-Fehler (kein Info-Leak). Docker-Image als Nicht-root
  mit Healthcheck.

## Status / bewusst offen (Phase 3+)

Aus den Reviews dokumentiert, nicht vergessen:
- **Harte Token-Limit-Durchsetzung** (aktuell TOCTOU zwischen Check und
  Persistenz möglich) → LiteLLM Virtual Keys/Budgets pro Mandant (Phase 4).
- **Token-Undercount**, wenn das Gateway kein `usage`-Objekt liefert (z.B.
  Ollama) → Tokenizer-Schätzung (Phase 3).
- **Verbrauchsverlust**, falls die Persistenz nach erfolgreichem Call scheitert
  → Retry/Outbox (Phase 3/4).
- **Enterprise-`"*"`** lässt jedes Modell zu; unbekannte enden als 502 statt 403
  → gegen die registrierte Gateway-Liste validieren (Phase 3).
- **Streaming** (`stream`-Param) noch nicht unterstützt (Phase 3).
- Modellwechsel-UI + Agenten-Ebene (Phase 3); Store-Webhook `orders/paid` →
  `/admin/provision` (Phase 5).
