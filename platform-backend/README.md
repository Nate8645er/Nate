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
| GET  | `/metrics` | Prometheus-Metriken (Requests, Latenz, Chat-Verbrauch) | — |
| POST | `/admin/provision` | Mandant + API-Key anlegen | `X-Admin-Token` |
| POST | `/v1/chat` | Chat via Gateway, mit Tarif-/Limit-Prüfung | Bearer API-Key |
| GET  | `/v1/models` | Im Tarif freigeschaltete Modelle (fürs UI-Dropdown) | Bearer API-Key |
| GET  | `/v1/usage` | Monatsverbrauch des Mandanten | Bearer API-Key |
| GET  | `/v1/conversations` | Liste der Unterhaltungen | Bearer API-Key |
| GET  | `/v1/conversations/{id}` | Eine Unterhaltung mit Nachrichten | Bearer API-Key |
| GET/POST | `/v1/agents…` | Agenten verwalten + ausführen (Tarif-Limit) | Bearer API-Key |
| GET  | `/v1/billing` | Tarif, Abo-Zustand, Verbrauch, Historie | Bearer API-Key |
| GET/POST/DELETE | `/v1/integrations…` | Integrationen-Gerüst (Tarif-Limit) — s.u. | Bearer API-Key |
| POST | `/webhooks/shopify/orders-paid` | Kauf → Mandant freischalten | HMAC (Shopify) |
| POST | `/webhooks/stripe` | Abo-Ereignisse (Kauf/Wechsel/Zahlung/Kündigung) | HMAC (Stripe) |
| GET  | `/dashboard.html` | Widget-Dashboard (Agenten/Verbrauch/Historie, Drag-and-Drop) | — (Key im Browser) |

## Abrechnung (Phase 4)

Der Stripe-Webhook hält Tarif und Zugang synchron mit dem Abo:

| Ereignis | Wirkung |
|---|---|
| `checkout.session.completed` | Mandant freischalten (oder verknüpfen), Tarif setzen |
| `customer.subscription.updated` | Tarifwechsel (Up-/Downgrade) übernehmen |
| `invoice.payment_failed` | Mandant auf `suspended` → Zugang gesperrt (401/403) |
| `invoice.paid` | Mandant wieder `active` |
| `customer.subscription.deleted` | Kündigung → gesperrt |

- **Signatur**: HMAC-SHA256 über `{timestamp}.{body}` inkl. 300-s-Zeitfenster
  (Replay-Schutz), konstant-Zeit verglichen. Ohne Stripe-SDK (Stdlib).
- **Idempotenz**: `processed_webhooks` (Provider + Event-ID). **Jedes** Ereignis
  — nicht nur Neuanlagen — belegt seine Kennung und ändert Zustand in **einer**
  Transaktion; bricht ein Schritt ab, greift die Wiederzustellung korrekt statt
  den Zustand dauerhaft falsch stehen zu lassen. Ein `400` (ungültiger Auftrag)
  verbraucht die Kennung nicht; eine **fehlende** Kennung wird fail-closed mit
  `400` abgelehnt (nie fail-open verarbeitet).
- **Tarif-Zuordnung**: `metadata.plan_code` am Stripe-Objekt, sonst
  `STRIPE_PRICE_MAP` (Preis-ID → Tarif).
- **`metadata.tenant_id`-Härtung**: wird nur akzeptiert, wenn es eine gültige
  UUID ist **und** die zahlende E-Mail nachweislich zu einem Nutzer genau
  dieses Mandanten gehört (RLS-geprüft) — verhindert die Übernahme eines
  fremden Mandanten über frei wählbare Checkout-Metadaten. Zweite
  Verteidigungslinie: `stripe_customer_id` wird nie überschrieben, wenn
  bereits ein *anderer* Kunde verknüpft ist.
- **Admin- vs. billing-Sperre**: `tenants.suspended_reason` unterscheidet
  `'admin'` (manuell durch den Betreiber) von `'billing'` (Abo inaktiv). Ein
  reguläres `invoice.paid` hebt eine administrative Sperre **nicht** auf.
- **Body-Limit**: Webhook-Bodies werden gestreamt und ab 1 MiB mit `413`
  abgebrochen (`app/http_limits.py`) — schützt auch gegen fehlenden/falschen
  `Content-Length`-Header (Chunked Transfer-Encoding).

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
- **Rate-Limiting** pro Mandant auf `/v1/chat` und `/v1/agents/{id}/chat`
  (30 Aufrufe/60s, Sliding Window). In-Process per Default (ein Prozess
  genuegt fuer lokale Entwicklung); `REDIS_URL` setzen fuer horizontale
  Skalierung (mehrere Prozesse/Pods teilen sich dann EIN Kontingent statt
  je eines) — atomar per Lua-Script, siehe `app/ratelimit.py` und
  `tests/test_ratelimit_redis.py` (Test gegen echten lokalen redis-server).

## Status / bewusst offen (Phase 3+)

Aus den Reviews dokumentiert, nicht vergessen:
- **Harte Token-Limit-Durchsetzung** (aktuell TOCTOU zwischen Check und
  Persistenz möglich) → LiteLLM Virtual Keys/Budgets pro Mandant.
- **Nutzungsbasierte Abrechnung**: `usage_events` ist die Datengrundlage, aber
  der Verbrauch wird noch **nicht** an Stripe/Lago gemeldet (aktuell reine
  Tarif-Pauschale + Limit). Meldung an ein Usage-Billing folgt.
- **Token-Undercount**, wenn das Gateway kein `usage`-Objekt liefert (z.B.
  Ollama) → Tokenizer-Schätzung (Phase 3).
- **Verbrauchsverlust**, falls die Persistenz nach erfolgreichem Call scheitert
  → Retry/Outbox (Phase 3/4).
- **Streaming** (`stream`-Param) noch nicht unterstützt (Phase 3).
- ~~Enterprise-`"*"` laesst jedes Modell zu; unbekannte enden als 502 statt
  403~~ — **stimmt nicht (mehr)**: `is_registered()` in `models_catalog.py`
  prueft unabhaengig vom Tarif-Wildcard gegen die registrierte Gateway-Liste,
  bevor ueberhaupt an das Gateway weitergeleitet wird. Empirisch bestaetigt
  (26.07., echte Postgres-DB) und als Regressionstest festgehalten:
  `tests/test_model_validation_integration.py`.
- Modellwechsel-UI + Agenten-Ebene (Phase 3); Store-Webhook `orders/paid` →
  `/admin/provision` (Phase 5).
- **`/v1/integrations`** hat jetzt einen echten OAuth-Weg über Composio
  (`app/composio_client.py`), statt selbst Client-IDs/Secrets pro Provider zu
  verwalten: `COMPOSIO_API_KEY` gesetzt → `POST /v1/integrations` initiiert
  eine echte Verbindung und liefert eine echte Login-URL (`connect_url`)
  zurück; `POST /v1/integrations/{id}/refresh` fragt den echten
  Verbindungsstatus ab und setzt `status` auf `connected`, sobald Composio
  das bestätigt. Mandantentrennung (RLS) und Tarif-Limit
  (`plans.max_integrations`) bleiben unabhängig davon durchgesetzt und
  getestet. **Ohne** `COMPOSIO_API_KEY` (kein Composio-Account in dieser
  Umgebung) bleibt exakt das bisherige Gerüst-Verhalten: `status` bleibt
  beim Anlegen immer `disconnected`, keine externe Anfrage, kein Fehler.
  Noch offen: verschlüsselte Token-Speicherung, falls Composio in `config`
  mehr als die Connected-Account-ID zurückgibt.
- **`dashboard.html`** ist noch nicht mit `index.html` verlinkt (nur ein
  „← Chat"-Link zurück) — beide UIs bewusst als getrennte, unabhängig
  ladbare Seiten gehalten.
