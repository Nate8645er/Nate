# INSTALL-LOG.md — was tatsächlich installiert wurde (Phase 1)

Ehrliche Bilanz. „Installiert" heißt: in einem venv real per `pip` aufgelöst, importiert und in
Tests/Boot verwendet. „Vertagt" heißt: bewusst nicht installiert, mit Grund.

## Umgebung
- Python 3.11.15 · pip 24 · **x86_64** (nicht die aarch64-Zielhardware) · Docker 29 · ~21 GB frei.
- Keine NVIDIA-GPU / kein CUDA in dieser Umgebung.

## Installiert & verifiziert (venv `platform-backend/.venv`)
Import-Check grün für: fastapi 0.139.2 · uvicorn 0.51.0 · pydantic-settings 2.14.2 · httpx 0.28.1
· tenacity 9.1.4 · **litellm 1.93.0** · instructor 1.15.4 · qdrant-client 1.18.0 · SQLAlchemy 2.0.51
· opentelemetry-api/sdk 1.44.0 · pytest 9.1.1. Gepinnt in `requirements.txt`.

**Verifikation:** `python -m pytest` → **19 passed**. App-Boot `/health` + `/health/compute` →
liefert ehrlich `gpu_available: false`, alle Dienste `not-configured`.

## Als Container-Dienst konfiguriert (NICHT als Bibliothek installiert)
`docker-compose.dev.yml` (validiert mit `docker compose config`): **postgres 16 · redis 7 ·
qdrant · minio · temporal**. Starten diese Dienste nur auf Wunsch (`up -d`), nicht automatisch —
in einem ephemeren Container kein Dauerbetrieb.

## Bewusst VERTAGT (mit Grund) — nicht installiert
| Komponente | Grund |
|---|---|
| **vLLM** | Benötigt CUDA-GPU; in dieser Umgebung nicht installier-/lauffähig. Interface + Erkennung sind da; Ausführung = GPU-Backend (Phase 2/8). |
| **transformers + torch** | ~mehrere GB, GPU-orientiert; für das Fundament nicht nötig. Kommt in Phase 3 (Embeddings/Reranker) im Backend. |
| **temporalio (Python-SDK)** | Erst mit Phase 5 (Workflows) sinnvoll; der Temporal-**Server** ist im Compose vorbereitet. |
| **Ollama / llama.cpp** | Sind Server/Binaries, keine pip-Bibliothek; werden per HTTP (OpenAI-kompatibel) über den Router angesprochen (`LOCAL_LLM_URL`). |
| **docling / unstructured / opencv** | Schwer; gehören zu Phase 3/5 (Dokument-/Vision-Pipeline), nicht ins Fundament. |
| **playwright** | Browser bereits separat in der Umgebung vorhanden; Einbau in Phase 5. |
| **keycloak / postgres / redis / qdrant / minio (Server)** | Dienste, keine Prozess-Bibliotheken → Compose statt pip. |
| **kubernetes / k3s / istio / kafka / spark** | Erst Phase 8 (Auftrag §9). |
| **51 E-Tier-Repos** (§B) | Bewusst nicht eingebaut (Redundanz/Lizenz/kein Bezug) — u. a. n8n (Sustainable Use), Milvus/Weaviate/Chroma (Redundanz zu Qdrant), AutoGPT/SuperAGI, Selenium. |

## Nächster echter Schritt
Phase 2: `models/`-Ausführung gegen ein **lokales** Modell testen (Ollama-Container, OpenAI-
kompatibel) + Prometheus-Exporter für Compute-Metriken. Erfordert einen laufenden Dienst.
