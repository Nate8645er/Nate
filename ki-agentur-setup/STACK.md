# KI SaaS Factory - Stack-Registry

Welche Bausteine wie eingebunden werden (Git/Paketmanager, keine ZIPs).

## Bereits aktiv (installiert und in Nutzung)
| Baustein | Rolle | Status |
|---|---|---|
| CrewAI | Multi-Agent-Teams (GPT+Kimi Worker) | CLI installiert, Demo-Crew gelaufen |
| n8n | Automatisierung (Lead-Webhook live) | installiert, Workflow exportiert |
| Playwright | Browser-Tests, QA, Videos | in browser-use-venv |
| Next.js/React/TypeScript/Tailwind | Frontend | im AI Command Center produktiv |
| ComfyUI | Bild-Pipeline | installiert |
| Metabase | Analytics-Dashboards | installiert |
| Agent Reach | Web-Recherche fuer Agenten | installiert, Skill aktiv |
| Cybersecurity-Skills (817) | Security-Reviews | Plugin abgelegt |

## Neu installiert (rag-venv)
| Baustein | Rolle |
|---|---|
| LangGraph | Produktions-Agenten-Workflows mit Zustand |
| LlamaIndex | RAG / Firmenwissen / Dokumenten-KI |
| Chroma | Vektordatenbank fuer RAG |
| Shopify CLI | Shop-/App-Entwicklung |

## Pro Projekt einbinden (Bibliotheken, kein Vorab-Klonen)
Auth.js (Login/OAuth), Prisma (DB-Schema), shadcn/ui + Polaris (UI),
Vercel AI SDK, Stripe SDK, FastAPI/NestJS (je nach Service-Sprache),
Redis-Client, PDF/Excel/CSV-Parser.

## Infrastruktur (als Dienst nutzen, nicht als Quellcode)
PostgreSQL (Neon/Supabase), Redis (Upstash), Docker, Vercel (Deploy),
Supabase (Auth+DB+Storage), PostHog (Analytics), Grafana/Prometheus
(Monitoring), Vault (Secrets), Temporal (Background-Jobs).

## Referenz (bei Bedarf klonen)
AutoGen, Semantic Kernel, Haystack, Qdrant, OWASP CheatSheets,
Shopify App Template (Remix), MCP-Spezifikation.

## Fabrik-Prinzip
Neues Produkt = ai-command-center als Vorlage kopieren:
Agenten-Registry (lib/agents/team.ts) austauschen, Branchen-Presets
setzen, Lizenz-Secret neu, Landing anpassen, auf Vercel deployen,
Produkt im Shopify-Store anlegen. RAG-Produkte ergaenzen rag-venv
(LlamaIndex+Chroma) als Wissensbasis-Schicht.
