# Betriebs-Runbook — platform-backend (Phase 8)

Härtung für den produktiven Betrieb: Backup/Restore, Update/Rollback, Lasttest,
Observability. Alles additiv; die bestehende Vercel-App bleibt unberührt.

## Observability
- **`/metrics`** (Prometheus): HTTP-Requests (Zähler + Latenz-Histogramm) und
  Compute-Gauges. Scrape via Pod-Annotation (`prometheus.io/scrape`), siehe
  `deploy/k8s/backend.yaml`.
- **`/health/live`** (Liveness): billig, nur Prozess lebt → k8s startet bei
  Fehler neu.
- **`/health/ready`** (Readiness): prüft konfigurierte Abhängigkeiten; `503`,
  wenn ein konfigurierter Dienst nicht erreichbar ist → k8s nimmt die Instanz
  aus dem Load-Balancer, **kein** Traffic auf kaputte Pods.
- **Tracing:** OTEL aktiviert sich, sobald `OTEL_EXPORTER_OTLP_ENDPOINT` gesetzt
  ist (sonst no-op).

## Backup & Restore
Code: `app/platform/backup.py` (offline getestet; Qdrant-Snapshot live bewiesen).

**Postgres** (Plattform-/Tenant-Daten, Audit-Log) — logisches Dump:
```python
from app.platform.backup import backup_postgres, restore_postgres
backup_postgres(DATABASE_URL, "/backups/pf-$(date +%F).dump")   # pg_dump -Fc
restore_postgres(DATABASE_URL, "/backups/pf-2026-07-23.dump")   # pg_restore --clean
```
- Passwort geht über `PGPASSWORD` (Env), **nie** in die Kommandozeile.
- `pg_dump`/`pg_restore` (Client 16) müssen im Backup-Job-Image vorhanden sein.
- Empfehlung: als k8s `CronJob` täglich, Dump nach MinIO/S3 (Objekt-Versionierung).

**Qdrant** (Vektoren pro Mandant) — Server-Snapshot:
```python
from qdrant_client import QdrantClient
from app.platform.backup import snapshot_qdrant, list_qdrant_snapshots
c = QdrantClient(url=QDRANT_URL)
snapshot_qdrant(c, "collection")      # Snapshot im Server-Storage
list_qdrant_snapshots(c, "collection")
```
Snapshots liegen im Qdrant-Storage-Volume → dieses Volume mitsichern.

**Restore-Test:** mindestens quartalsweise ein Restore in eine Wegwerf-Umgebung
fahren (ein ungeprüftes Backup ist kein Backup).

## Update & Rollback (k8s/k3s)
```bash
kubectl apply -k deploy/k8s                       # Rollout (RollingUpdate, maxUnavailable=0)
kubectl -n ki-plattform rollout status deploy/platform-backend
kubectl -n ki-plattform rollout undo   deploy/platform-backend   # Rollback auf vorige Revision
```
- **Zero-Downtime:** `maxUnavailable: 0` + Readiness-Gate → neue Pods bekommen
  erst Traffic, wenn `/health/ready` grün ist; alte laufen bis dahin weiter.
- `revisionHistoryLimit: 5` hält die letzten Versionen für schnellen Rollback.
- `PodDisruptionBudget` (minAvailable 1) schützt bei Node-Drains.
- Images per Digest pinnen (nicht `:latest`) — in der CI ersetzen.

## Lasttest
Code: `app/observability/loadtest.py`.
```bash
python -m app.observability.loadtest http://HOST:8000/health/live -n 500 -c 25
```
Gibt JSON mit `rps` und `latency_ms` (p50/p95/p99/max) aus; Exit-Code ≠ 0 bei
Fehlern. **Baseline (Dev, 1 uvicorn-Worker, CPU):** `/health/live` ~477 rps,
p50 41 ms / p95 128 ms, 0 Fehler bei 500 Requests; `/metrics` ~553 rps, p95 31 ms.
In Produktion mehrere Worker/Replicas → höhere Werte; k6/Locust für echte
Dauerlast.

## Deploy-Checkliste (sicherheitsrelevant)
- [ ] `DATABASE_URL`-Rolle ist **NOBYPASSRLS** und Nicht-Superuser (RLS!).
- [ ] Keycloak-`audience` (client_id) gesetzt (siehe SECURITY-REVIEW.md).
- [ ] Secrets extern injiziert (kein Klartext im Git; Manifest-Secret ist leer).
- [ ] Image per Digest gepinnt; `bandit` + `ruff` in der CI grün.
- [ ] Backups laufen + ein Restore wurde getestet.
