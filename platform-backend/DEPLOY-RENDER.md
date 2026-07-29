# platform-backend auf Render deployen (Container-Host)

Der komplette Deploy ist im Repo definiert (`render.yaml`). Render **baut das
gehärtete Image selbst** aus `platform-backend/Dockerfile` — kein GHCR-Zugang
nötig. Push auf den verbundenen Branch → automatischer Redeploy.

## Was ich (der Code) schon erledigt habe
- `render.yaml`: Service `platform-backend` (Docker, non-root, `/health/ready`
  als Health-Check, `$PORT`-fähig, EU-Region), `autoDeploy: true`.
- Alle Env-Variablen sind deklariert; die geheimen als `sync: false`
  (werden NICHT im Git gespeichert).

## Was NUR du tun kannst (deine Zugänge — nicht in den Chat!)
1. **Render-Account**: auf [render.com](https://render.com) registrieren.
2. **Blueprint verbinden**: „New +“ → „Blueprint“ → dieses GitHub-Repo wählen.
   Render liest `render.yaml` und legt den Service an.
3. **Diese Werte im Render-Dashboard eintragen** (Service → Environment):

   | Variable | Woher du sie bekommst | Pflicht? |
   |---|---|---|
   | `DATABASE_URL` | Supabase-Dashboard → Connection String. **Eigene Rolle mit `NOBYPASSRLS`, kein Superuser** (sonst greift die Mandantentrennung nicht). | ja |
   | `REDIS_URL` | Upstash-Dashboard → Redis-URL. | empfohlen |
   | `QDRANT_URL` | Qdrant Cloud (kostenloser Tier) → Cluster-URL. Leer lassen = Wissens-API meldet ehrlich 503. | optional |
   | `KEYCLOAK_ISSUER` / `KEYCLOAK_AUDIENCE` | Nur wenn du auf Keycloak-Login umstellst. Leer = dein bestehendes Supabase-Login bleibt aktiv. | optional |
   | `OTEL_EXPORTER_OTLP_ENDPOINT` | Nur für Tracing (Grafana/Langfuse). | optional |

4. **Deploy auslösen**: Render deployt nach dem Speichern automatisch. Fertig,
   sobald `/health/ready` grün ist.

## Danach prüfen (öffentlich erreichbar)
```
curl https://<dein-service>.onrender.com/health/ready      # ready: true
curl https://<dein-service>.onrender.com/health/compute    # Hardware
```

## Frontend-Anbindung
In der Vercel-App `PLATFORM_BACKEND_URL=https://<dein-service>.onrender.com`
setzen → das v2-Dashboard zeigt echte Live-Kennzahlen (Cutover-Runbook Stufe 1).

## Datenbank-Rolle mit NOBYPASSRLS (einmalig, in Supabase SQL-Editor)
```sql
CREATE ROLE app_user LOGIN PASSWORD '<sicher>' NOBYPASSRLS;
GRANT USAGE ON SCHEMA public TO app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;
-- RLS-Policies siehe platform-backend/app/platform/sql/tenancy_rls.sql
```
Dann `DATABASE_URL` mit dieser Rolle (nicht dem Supabase-Default) verwenden.
