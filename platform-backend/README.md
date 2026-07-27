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
| GET  | `/v1/checkout/{session_id}/claim` | Liefert den frisch erzeugten API-Key EINMAL (Onboarding, s.u.) | — (Session-ID als Abholschein) |
| GET  | `/checkout-success.html` | Erfolgsseite nach Stripe-Checkout — loggt automatisch ein | — |

## Onboarding ohne manuellen API-Key-Klick

Bis eben musste ein zahlender Kunde nach dem Stripe-Kauf seinen eigenen
API-Key irgendwo suchen — es gab keine Zustellung, keine Erfolgsseite. Anders
als bei ChatGPT/Claude/Kimi (Abo kaufen → direkt loslegen) hätte der Kunde
nie Zugriff auf sein eigenes Konto bekommen. Behoben, ohne neue externe
Abhängigkeit:

1. `checkout.session.completed` legt beim Neukauf wie bisher Mandant + Key
   an, hinterlegt den Klartext-Key zusätzlich unter der Stripe-Checkout-
   Session-ID (`checkout_handoffs`, Migration 010) — ein einmalig
   abrufbarer, zeitlich begrenzter (60 Min.) Abholschein.
2. Stripes `success_url` mit `?session_id={CHECKOUT_SESSION_ID}` (Stripe-
   eigene Konvention) zeigt auf `/checkout-success.html`.
3. Die Seite pollt `GET /v1/checkout/{session_id}/claim` (kurz, mit
   wachsendem Abstand — der Webhook kann etwas nach dem Redirect ankommen),
   speichert den Key automatisch im Browser (`localStorage`, wie beim
   normalen Chat-Login) und leitet zum Chat weiter — **kein Kopieren, kein
   Einfügen, kein Suchen** durch den Kunden.

Der Abholschein ist nach dem ersten Abruf sofort gelöscht (single-use) —
ein zweiter Versuch mit derselben Session-ID liefert 404, genau wie eine
unbekannte oder abgelaufene ID. Getestet gegen eine echte Postgres-DB
inkl. Beweis, dass der abgeholte Key wirklich funktioniert:
`tests/test_checkout_handoff.py`. Im Stripe-Dashboard muss die
`success_url` des Checkout-Links auf
`https://<domain>/checkout-success.html?session_id={CHECKOUT_SESSION_ID}`
gesetzt werden, damit das greift.

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
- ~~Harte Token-Limit-Durchsetzung (TOCTOU zwischen Check und Persistenz)~~
  — **behoben**: `app/completions.py` reserviert das Token-Kontingent jetzt
  ATOMAR (`_reserve_tokens`, ein einzelnes `UPDATE ... WHERE ...`) BEVOR das
  Gateway kontaktiert wird, statt nur vorab zu pruefen. Postgres serialisiert
  konkurrierende Reservierungen auf derselben `tenants`-Zeile automatisch —
  zwei gleichzeitige Anfragen koennen das Limit nicht mehr gemeinsam
  ueberschreiten. Die Reservierung wird NICHT waehrend des (langsamen)
  Gateway-Aufrufs gehalten (eigener kurzer Commit davor/danach), um den
  kleinen DB-Verbindungspool (`max_size=10`) nicht zu blockieren. Mit
  echter Nebenlaeufigkeit getestet (zwei Threads, zwei DB-Verbindungen,
  nicht nur sequenziell — der alte Bug zeigte sich nur bei echtem Race):
  `tests/test_token_reservation.py`. Bekannte Restluecke: reservierte
  Tokens bleiben "haengen", falls der Prozess mitten im Request abstuerzt
  (kein periodischer Aufraeum-Job); bei normalem Fehlerpfad (Gateway-Fehler,
  Timeout, Exception) wird immer freigegeben.
- ~~Nutzungsbasierte Abrechnung: usage_events ist die Datengrundlage, aber
  der Verbrauch wird nicht an Stripe gemeldet~~ — **umgesetzt, mit echter
  Einschraenkung**: `app/stripe_usage.py` meldet nach jedem abgeschlossenen
  Chat-Aufruf (streamend wie nicht-streamend) den Token-Verbrauch als
  Stripe-Meter-Event (`event_name="platform_tokens"`), sofern
  `STRIPE_SECRET_KEY` gesetzt UND der Mandant einen verknuepften
  `stripe_customer_id` hat (aus `link_stripe_customer`, siehe `billing.py`).
  Ohne den Key: no-op, kein Fehler — Verbrauch bleibt wie bisher nur lokal
  in `usage_events`/`GET /v1/usage` sichtbar. Meldung ist Best-Effort: ein
  Stripe-Ausfall wird geloggt, laesst aber nie einen Chat-Request scheitern.
  **Ehrliche Grenze**: in dieser Umgebung existiert kein echter Stripe-
  Account, daher ist nur die Aufrufstruktur (Endpoint, Feldnamen, Auth)
  gegen die oeffentliche Stripe-Dokumentation gebaut und mit einem
  gefaelschten HTTP-Client getestet (`tests/test_stripe_usage.py`) — nicht
  gegen die echte Stripe-API verifiziert. In Stripe muss vorher ein Billing-
  Meter mit exakt diesem `event_name` angelegt werden.
- ~~Token-Undercount, wenn das Gateway kein `usage`-Objekt liefert~~ —
  **behoben**: `app/completions.py` schaetzt Tokens (~4 Zeichen/Token) wenn
  `usage` fehlt, statt still 0 zu zaehlen — sonst haette ein Mandant ueber
  ein Modell ohne `usage`-Feld effektiv unbegrenzt und unverrechnet chatten
  koennen. Kein echter Tokenizer (ungenau), aber verhindert den
  Total-Blindspot. Getestet inkl. Beweis, dass der geschaetzte Verbrauch
  wirklich gegen `GET /v1/usage` und das Monats-Limit zaehlt:
  `tests/test_completions_token_estimate.py`.
- **Verbrauchsverlust bei Persistenz-Fehlern: teilweise behoben.**
  `_persist_and_release_with_retry` in `app/completions.py` wiederholt die
  Persistenz-Transaktion bis zu 3× (kurzer Backoff dazwischen), wenn sie
  nach einem bereits erfolgreichen (kostenpflichtigen) Gateway-Aufruf
  fehlschlägt — deckt den häufigeren Fall ab: einen kurzen transienten
  DB-Fehler (Verbindungsabbruch, Pool-Spitze) innerhalb derselben Anfrage.
  **Nicht behoben:** ein voller Outbox mit Wiederaufnahme über
  Prozessneustarts hinweg bleibt Phase 4 (braucht eine Queue) — stirbt der
  Prozess mitten in allen 3 Versuchen, ist die Antwort trotzdem weg, nur
  vollständig geloggt statt still verschwunden. Getestet (Retry-Logik
  isoliert, nicht die DB-Schicht selbst): `tests/test_persist_retry.py`.
- ~~Streaming (`stream`-Param) noch nicht unterstützt~~ — **umgesetzt**:
  `POST /v1/chat` und `POST /v1/agents/{id}/chat` mit `"stream": true`
  liefern Server-Sent-Events (OpenAI-kompatibles Chunk-Format), direkt vom
  LiteLLM-Gateway durchgereicht. Modellvalidierung, Konversationspruefung
  und Token-Reservierung laufen VOR dem ersten gesendeten Byte (danach ist
  der HTTP-Statuscode fest auf 200). Bittet das Gateway per
  `stream_options.include_usage` um echte Nutzungsdaten im letzten Chunk;
  fehlen sie, greift dieselbe Schaetzung wie im nicht-streamenden Pfad.
  Reservierung wird nach Streamende (Erfolg wie Fehler) zuverlaessig
  freigegeben. Getestet mit einem gefaelschten SSE-Gateway gegen eine echte
  Postgres-DB: `tests/test_chat_streaming.py`.
- ~~Enterprise-`"*"` laesst jedes Modell zu; unbekannte enden als 502 statt
  403~~ — **stimmt nicht (mehr)**: `is_registered()` in `models_catalog.py`
  prueft unabhaengig vom Tarif-Wildcard gegen die registrierte Gateway-Liste,
  bevor ueberhaupt an das Gateway weitergeleitet wird. Empirisch bestaetigt
  (26.07., echte Postgres-DB) und als Regressionstest festgehalten:
  `tests/test_model_validation_integration.py`.
- ~~Modellwechsel-UI + Agenten-Ebene (Phase 3); Store-Webhook `orders/paid` →
  `/admin/provision` (Phase 5)~~ — **umgesetzt**: Modellauswahl in
  `static/index.html` (`#model`-Select, befüllt aus `GET /v1/models`),
  Agenten-Endpunkte in `app/routes/agents.py` (`GET/POST /v1/agents`,
  `POST /v1/agents/{id}/chat`), Store-Webhook in `app/routes/webhooks.py`
  (`POST /webhooks/shopify/orders-paid`, HMAC-verifiziert, idempotent über
  `claim_event`, ruft `provision_tenant` in derselben Transaktion auf).
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
- ~~Konversations-Fortsetzung faktisch kaputt: der Stream-Pfad gab die
  `conversation_id` nirgends an den Client zurück, jede Nachricht legte
  serverseitig eine neue Konversation an~~ — **behoben** (gefunden von
  `ultra-architect` beim Weiterentwicklungs-Audit, 27.07.): `stream_chat`
  löst die `conversation_id` jetzt VOR dem Gateway-Aufruf auf
  (`_resolve_conversation_id`) und `_stream_events` sendet sie als ersten
  SSE-Chunk. `static/index.html` liest sie aus dem Stream, speichert sie
  pro API-Key in `localStorage` und hängt Folgenachrichten wirklich an
  dieselbe Konversation an; ein „+ Neu"-Button startet bewusst eine neue.
  Eine veraltete gespeicherte ID (404 vom Server) wird clientseitig einmalig
  automatisch verworfen und als neue Konversation fortgesetzt statt den Chat
  tot enden zu lassen. Echter Regressionstest gegen eine echte Postgres-DB
  (zwei Nachrichten landen nachweislich in derselben Konversation, nicht in
  zwei getrennten): `tests/test_chat_streaming.py::test_stream_returns_conversation_id_for_continuation`.
  Zusätzlich: mobiler mit Zeilenumbruch (`header{flex-wrap}` +
  `@media (max-width:640px)`) in `index.html` und `dashboard.html`, da der
  Header vorher auf schmalen Bildschirmen überlaufen konnte (keine
  Breakpoints trotz Viewport-Meta-Tag).

### Vom Weiterentwicklungs-Audit noch offen (nicht in dieser Runde umgesetzt)

- **Agenten-Chat im UI**: `POST /v1/agents/{id}/chat` ist voll funktionsfähig
  (inkl. Streaming), aber `dashboard.html` kann Agenten nur anlegen/löschen,
  nicht mit ihnen chatten — nur per eigenem curl-Aufruf nutzbar.
- **`/v1/integrations` ohne UI**: Composio-OAuth-Fluss ist serverseitig
  fertig und getestet, aber im Dashboard nicht bedienbar (kein Widget in der
  `WIDGETS`-Registry).
