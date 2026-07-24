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

- **Mandantentrennung**: `migrations/001_init.sql` aktiviert `FORCE ROW LEVEL
  SECURITY` auf allen mandantengebundenen Tabellen. Die App setzt pro
  Transaktion `app.current_tenant`; die DB filtert automatisch. Ein App-Bug
  kann keine fremden Zeilen liefern.
- **Tarife**: `migrations/002_seed_plans.sql` (Free … Enterprise, Master-Prompt
  3.3). Modelle sind pro Tarif freigeschaltet, nicht pro Nutzer hart kodiert.
- **Gateway**: LiteLLM (`litellm/config.yaml`) — ein Zugang für alle Anbieter
  inkl. mindestens einem lokalen Modell (Ollama).
- **Verbrauch**: jede Chat-Antwort schreibt ein `usage_events`-Ereignis →
  Grundlage für Limit-Durchsetzung und spätere Abrechnung (Phase 4).

## Lokal starten

```bash
cp .env.example .env      # Werte eintragen (ANTHROPIC_API_KEY, ADMIN_TOKEN, ...)
docker compose up --build
```

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
| GET  | `/health` | Liveness + DB-Check | — |
| POST | `/admin/provision` | Mandant + API-Key anlegen | `X-Admin-Token` |
| POST | `/v1/chat` | Chat via Gateway, mit Tarif-/Limit-Prüfung | Bearer API-Key |
| GET  | `/v1/usage` | Monatsverbrauch des Mandanten | Bearer API-Key |

## Tests

```bash
pip install -r requirements.txt pytest
pytest -q
```

Die Tests decken die Tarif-Logik, die API-Key-Erzeugung/Hashing und die
Struktur-Garantie (RLS + FORCE auf allen Mandantentabellen) ab — ohne
laufende DB.

## Sicherheit

- Keine Secrets im Code — alles aus `.env` (in `.gitignore`).
- API-Keys werden nur als SHA-256-Hash gespeichert, Klartext genau einmal
  ausgegeben.
- `/admin/provision` per konstant-Zeit-Vergleich gegen `ADMIN_TOKEN`.
- Docker-Image läuft als Nicht-root, mit Healthcheck.

## Status / offen (Phase 3+)

- Modellwechsel-UI + Agenten-Ebene (Phase 3)
- Kosten-/Budget-Tracking pro virtuellem LiteLLM-Key (Phase 4)
- Store-Webhook `orders/paid` → ruft `/admin/provision` (Phase 5)
