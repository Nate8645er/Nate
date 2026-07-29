# platform-backend

Additive Enterprise-Schicht des KI-Systems (`ai-command-center`). **Neuer, separater Dienst** —
erweitert das bestehende System, ersetzt nichts. Siehe `../docs/plattform-ausbau/` für Kontext
(Inventar, Ist-Architektur, Phasenplan).

## Status: Phase 1 (Fundament)

Vorhanden und getestet (ohne GPU, ohne Netz):

- **Config-Layer** (`app/config.py`) — honest not-configured für alle Dienste.
- **Compute-HAL** (`app/compute/hal.py`) — Geräteerkennung CPU/NVIDIA, `dedicated` vs.
  `unified` memory (DGX Spark), injizierbarer Runner → ohne GPU testbar.
- **Modell-Router** (`app/models/router.py`) — reine Routing-Policy (lokal ↔ Cloud,
  `local_only` bindend) + LiteLLM-Ausführungsadapter (lazy).
- **Observability** (`app/observability/`) — OpenTelemetry-Haken (no-op bis Collector da).
- **FastAPI** (`app/main.py`) — `/health`, `/health/compute`.
- Leere, dokumentierte Pakete für spätere Phasen: `knowledge/ agents/ automation/ platform/`.

## Entwicklung

```bash
cd platform-backend
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
python -m pytest                    # 19 Tests, grün, ohne GPU/Netz
uvicorn app.main:app --reload       # dann GET /health, /health/compute
```

Dienste für spätere Phasen (nur Dev, startet nichts automatisch):

```bash
docker compose -f docker-compose.dev.yml up -d   # postgres, redis, qdrant, minio, temporal
```

## Grenzen (ehrlich)

- Läuft vollständig **ohne GPU**; GPU-Backends (vLLM) sind Erkennung + Interface, aber hier nicht
  ausführbar (keine CUDA-Hardware). Ausführung gehört ins GPU-Backend (Phase 2/8).
- Kein Dienst wird in Produktion betrieben — das ist laufender Betriebsaufwand, kein Code-Feature.
- Fachliche Endpunkte (RAG, Agenten, Workflows) folgen ab Phase 2 gemäß `docs/plattform-ausbau`.
