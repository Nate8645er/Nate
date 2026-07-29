# Phase 9 — Containerisierung & CI/CD

Schließt die Lücke aus Phase 8: die k8s-Manifeste verwiesen auf ein Image, das
es noch nicht gab. Jetzt existiert der reproduzierbare Build- und Deploy-Pfad.

## Dockerfile (gehärtet)
`platform-backend/Dockerfile` — Multi-Stage:
- **builder**: baut die Abhängigkeiten in ein venv. Optionaler BuildKit-Secret
  `proxyca` (`required=false`) für Umgebungen mit TLS-inspizierendem Proxy; in
  normaler CI ohne Proxy weggelassen → pip baut direkt.
- **runtime**: schlank (`python:3.11-slim`), **non-root uid 10001** (passt zum
  `runAsUser` im Deployment), keine Build-Toolchain, `HEALTHCHECK`,
  `uvicorn app.main:app` auf `0.0.0.0:8000`.

Real gebaut und gestartet — genau wie in Produktion (`--user 10001 --read-only
--tmpfs /tmp`): `/health/live`, `/health/ready` (ehrlich „übersprungen" ohne
Konfiguration), `/health/compute` (echte CPU), `/metrics` (Prometheus) — alle
grün; `id` im Container = uid 10001.

## docker-compose (Entwicklung)
`docker-compose.dev.yml` bekommt einen `backend`-Service, der aus dem Dockerfile
baut und an postgres/redis/qdrant/temporal/minio im selben Netz verdrahtet ist —
gehärtet (`user`, `read_only`, `no-new-privileges`, `cap_drop: ALL`).
Start: `docker compose -f docker-compose.dev.yml up -d`.

## CI (`.github/workflows/platform-backend.yml`)
Additiv, nur bei Änderungen an `platform-backend/**`:
- **test-Job**: `ruff check` (blockierend) → `bandit -r app -ll` (blockierend ab
  Severity MEDIUM) → `pytest` (Live-Tests überspringen sich ohne Dienste).
- **docker-Job**: baut das Image und führt einen Smoke-Test aus (non-root,
  read-only, `/health/live` + `/health/ready` + `/metrics`).

## Invarianten testgeprüft
`tests/test_container.py`: Multi-Stage + non-root, Dockerfile-uid == Deployment-
`runAsUser`, `.dockerignore` schließt Ballast aus, Compose-Backend gehärtet,
CI enthält Lint+SAST+Docker-Gate.

## Teststand
backend **112 grün** + 5 Live-Tests sauber übersprungen; ruff sauber;
bandit 0 High/0 Medium; Image real gebaut + Endpunkte verifiziert.
