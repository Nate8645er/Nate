# LICENSES.md — Lizenz-Gate (blockierend)

Regel (Auftrag §4): **Kein Einbau ohne Eintrag hier.** Alles, was Kunden nutzen, muss unter einer
freien Lizenz stehen (MIT/Apache-2.0/BSD/MPL-2.0/ISC). (A)GPL nur als **separater Netzwerkdienst**
nach Einzelprüfung. Gesperrt: SSPL, BSL, „fair-code"/Sustainable Use für Kundenpfade.

Einsatzart: **lib** = Bibliothek im Prozess · **service** = eigener Dienst/Container · **dev** = nur
Entwicklung. Spalte „geprüft": `pip`-Metadaten bzw. Projekt-Repo zum Analysezeitpunkt.

## In Phase 1 tatsächlich installiert (Backend-Bibliotheken)

| Paket | Version (gepinnt) | Lizenz | Einsatzart | Entscheidung |
|---|---|---|---|---|
| fastapi | s. `requirements.txt` | MIT | lib | ✅ erlaubt |
| uvicorn | " | BSD-3-Clause | lib | ✅ |
| pydantic / pydantic-settings | " | MIT | lib | ✅ |
| httpx | " | BSD-3-Clause | lib | ✅ |
| tenacity | " | Apache-2.0 | lib | ✅ |
| litellm | " | MIT | lib | ✅ (Modell-Router-Adapter) |
| instructor | " | MIT | lib | ✅ (strukturierte Ausgaben) |
| qdrant-client | " | Apache-2.0 | lib | ✅ (Vektor-DB-Client) |
| sqlalchemy | " | MIT | lib | ✅ |
| opentelemetry-api / -sdk | " | Apache-2.0 | lib | ✅ (Observability ab Tag 1) |
| PyJWT | " | MIT | lib | ✅ (Keycloak/OIDC-Token-Verify) |
| cryptography | " | Apache-2.0 / BSD-3 (dual) | lib | ✅ (RS256-Signaturprüfung) |
| prometheus-client | " | Apache-2.0 | lib | ✅ (Compute-Metriken-Exporter) |
| temporalio (Python-SDK) | " | MIT | lib | ✅ (Workflow-Adapter; Server als Dienst) |
| pytest | " | MIT | dev | ✅ |

## Dienste (als Container geplant, NICHT als Prozess-Bibliothek eingebaut)

| Dienst | Lizenz (zum Prüfzeitpunkt) | Einsatzart | Entscheidung |
|---|---|---|---|
| PostgreSQL | PostgreSQL License (BSD-artig) | service | ✅ |
| Redis | ⚠ Lizenzwechsel-Historie (RSALv2/SSPL bzw. AGPLv3 ab 8.0) — **vor Prod erneut prüfen**; Alternative: Valkey (BSD) | service | ⏸ als Dev-Cache ok, Prod-Entscheidung offen |
| Qdrant (Server) | Apache-2.0 | service | ✅ |
| MinIO | ⚠ AGPL-3.0 — nur als **separater Netzwerkdienst** zulässig, nicht einbetten | service | ✅ (nur als Dienst) |
| Temporal | MIT | service | ✅ |
| Keycloak | Apache-2.0 | service | ✅ (nur falls Auth-Migration beschlossen) |
| Grafana | AGPL-3.0 | service | ✅ (separater Dienst) |
| Prometheus | Apache-2.0 | service | ✅ |

## Bewusst NICHT installiert (mit Grund) — Auszug

| Komponente | Grund |
|---|---|
| vLLM, transformers+torch, TGI, ExLlamaV2 | GPU/CUDA nötig — in dieser Umgebung nicht lauffähig/testbar; kommen ins GPU-Backend (Phase 2/8) |
| n8n | ⚠ Sustainable Use License — Hosten für zahlende Kunden nicht abgedeckt → Workflow-Engine = Temporal |
| Kubernetes/k3s, Istio, Envoy, Kafka, Spark | erst Phase 8 (Auftrag §9) |
| Elasticsearch, Milvus, Weaviate, Chroma | Redundanz zu Qdrant / Betriebsaufwand (§B) |
| Supabase-Gesamtstack, Dify, ragflow | Lock-in / Konkurrenzprodukt (§B) |

> Aktualisierung bei jedem weiteren Einbau. Lizenzen mit ⚠ werden vor Produktion an der
> Originalquelle erneut geprüft, nicht aus dem Gedächtnis.
