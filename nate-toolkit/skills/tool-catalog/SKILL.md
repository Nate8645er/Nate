---
name: tool-catalog
description: >-
  Ehrlicher Katalog aller ~85 GitHub-Repos, die im Chat als "installieren,
  aktivieren, unter Plugins/Skills speichern" genannt wurden. Pro Repo: was es
  wirklich ist, ob es hier lauffaehig ist, und was der reale Weg waere (nicht
  "installiert als Skill", denn das ist bei den meisten technisch unmoeglich).
  AKTIVIEREN bei Fragen zu einem der gelisteten Repos, oder auf Trigger:
  "installiere die Repos", "was ist mit [Repo]", "Tool-Katalog", "Werkzeugliste".
---

# Tool-Katalog — die ~85 genannten Repos, ehrlich bewertet

**Kernpunkt zuerst:** Ein Claude-Code-Plugin ist ein Ordner mit
`.claude-plugin/plugin.json` + `skills/*/SKILL.md`. Ein GitHub-Repo wie
`huggingface/transformers` oder `microsoft/vscode` hat das nicht — das sind
Programme, Bibliotheken oder ganze Anwendungen. Man kann sie nicht "als Skill
installieren", so wie man ein Auto nicht "als App installiert". Was real
moeglich ist, haengt vom Typ ab (Details: Skill `dev-toolbelt`).

Diese Tabelle ordnet jedes genannte Repo ein:

- **nutzbar jetzt** — CLI-Werkzeug, in dieser Sandbox pruefbar/installierbar,
  echter Nutzen fuer die taegliche Arbeit an diesem Repo.
- **Kandidat** — passt inhaltlich zu Produkt A/B/C, aber noch nicht gebaut/
  integriert. Bei Bedarf gezielt angehen, nicht pauschal "installieren".
- **nur Referenz** — zu schwer fuer diese Umgebung (eigener Server/Cluster
  noetig) oder Konkurrenzprodukt. Nutzen: Architektur/Muster lesen, nicht
  betreiben.
- **nicht anwendbar** — Editor, IDE, Programmiersprache oder Laufzeit fuer
  Menschen am Rechner. Kein Skill-Konzept passt hier.

## Agenten-Frameworks & Orchestrierung (relevant fuer Produkt A)

| Repo | Status | Begruendung |
|---|---|---|
| e2b-dev/E2B | Kandidat | Sandbox-Ausfuehrung fuer Agenten-Code — falls Produkt A je Nutzer-Code ausfuehren soll |
| all-hands-ai/OpenHands | nur Referenz | eigenstaendige Agenten-IDE, eigener Server noetig |
| microsoft/semantic-kernel | nur Referenz | .NET/Python-Framework, Alternative zu unserem eigenen LiteLLM-Ansatz |
| openai/openai-agents-python | Kandidat | leichtgewichtiges Python-SDK, koennte Agenten-Orchestrierung in Produkt A ergaenzen |
| stanfordnlp/dspy | Kandidat | Prompt-Optimierung — interessant fuer bessere Council-Prompts |
| deepset-ai/haystack | nur Referenz | RAG-Framework, eigener Stack, Ueberschneidung mit unserem Ansatz |
| microsoft/PromptWizard | nur Referenz | Forschungs-Tool zur Prompt-Optimierung |
| Significant-Gravitas/AutoGPT | nur Referenz | autonomer Agent, eigene Infrastruktur |
| huggingface/smolagents | Kandidat | sehr schlankes Agenten-Framework, passt zur "einfach halten"-Linie |
| composiohq/composio | Kandidat | vorgefertigte Tool-Integrationen (genau das, was `integrations.py` bisher nur als Slack/Notion-Skelett hat) |
| langgenius/dify | nur Referenz | No-Code-Agenten-Plattform, eigener Server, Konkurrenzprodukt zu Produkt A |

## LLM-Inferenz & lokale Modelle (Infrastruktur, teils bereits genutzt)

| Repo | Status | Begruendung |
|---|---|---|
| ollama/ollama | **bereits genutzt** | steht schon in `litellm/config.yaml` als lokaler Provider |
| huggingface/transformers | nur Referenz | Modell-Bibliothek, braucht GPU-Server zum Selbstbetrieb |
| huggingface/text-generation-inference | nur Referenz | Produktions-Serving, eigener GPU-Server noetig |
| huggingface/datasets | nur Referenz | fuers Modelltraining, nicht fuer den SaaS-Betrieb relevant |
| vllm-project/vllm | nur Referenz | Hochleistungs-Inferenz, eigener GPU-Server noetig |
| sgl-project/sglang | nur Referenz | wie vllm, eigener GPU-Server noetig |
| oobabooga/text-generation-webui | nicht anwendbar | Desktop-UI fuer Menschen, kein Backend-Baustein |
| lmstudio-ai | nicht anwendbar | Desktop-App fuer Menschen |
| open-webui/open-webui | Kandidat | koennte als Alternative/Ergaenzung zum eigenen Dashboard dienen, aber eigener Server noetig |

## Observability & Evaluation (relevant fuer Produkt A, leichtgewichtig)

| Repo | Status | Begruendung |
|---|---|---|
| agentops-ai/agentops | Kandidat | Agenten-Monitoring, ergaenzt unsere bestehenden Prometheus-Metriken |
| langfuse/langfuse | Kandidat | LLM-Observability, self-hostbar, passt zu unserem Stack |
| arize-ai/phoenix | Kandidat | LLM-Eval/Tracing, Open Source |
| wandb/weave | nur Referenz | Teil von Weights & Biases, eher ML-Training-fokussiert |

## Workflow/Jobs (Kandidat fuer Automatisierung in A/B)

| Repo | Status | Begruendung |
|---|---|---|
| inngest/inngest | Kandidat | Event-getriebene Hintergrundjobs, koennte Billing/Webhooks robuster machen |
| triggerdotdev/trigger.dev | Kandidat | Alternative zu Inngest, gleicher Anwendungsfall |
| apache/airflow | nur Referenz | schwergewichtige Batch-Orchestrierung, Overkill fuer unsere Groesse |
| prefecthq/prefect | nur Referenz | wie Airflow, eigener Server noetig |

## No-Code / Business-Apps (meist Konkurrenzprodukte, nicht integrierbar)

| Repo | Status | Begruendung |
|---|---|---|
| calcom/cal.com | nur Referenz | Terminbuchung, eigenstaendiges Produkt |
| appsmithorg/appsmith | nur Referenz | interne Tools per No-Code, eigener Server |
| tooljet/tooljet | nur Referenz | wie Appsmith |
| directus/directus | nur Referenz | Headless-CMS, eigener Server, Ueberschneidung mit unserer eigenen DB |
| strapi/strapi | nur Referenz | Headless-CMS, gleiche Kategorie |
| payloadcms/payload | nur Referenz | Headless-CMS, gleiche Kategorie |
| medusajs/medusa | nur Referenz | **Shopify-Alternative** — inhaltlich naeheste Ueberschneidung mit Produkt B, aber Produkt B ist bewusst AUF Shopify aufgebaut, nicht als Ersatz dafuer |
| saleor/saleor | nur Referenz | wie Medusa, Shopify-Alternative |
| nocodb/nocodb | nur Referenz | Airtable-Alternative, kein Bezug zu A/B/C |

## MCP & Protokoll (direkt relevant, bereits im Einsatz)

| Repo | Status | Begruendung |
|---|---|---|
| supabase-community/supabase-mcp | Kandidat | falls je Supabase statt eigenem Postgres-Setup genutzt wird |
| modelcontextprotocol/python-sdk | **bereits genutzt** | Basis fuer MCP-Server, die diese Sitzung schon verwendet (Shopify, GitHub, ...) |
| modelcontextprotocol/typescript-sdk | nur Referenz | TS-Variante, unser Stack ist Python-lastig |

## Sprachen & Laufzeiten (kein Skill-Konzept)

| Repo | Status | Begruendung |
|---|---|---|
| microsoft/typescript | nicht anwendbar | Programmiersprache, nutzen wir bereits (Remotion-Video-Pipeline) |
| python/cpython | nicht anwendbar | Programmiersprache, nutzen wir bereits |

## Dev-CLI-Werkzeuge (real pruefbar — siehe Skill `dev-toolbelt`)

| Repo | Status | Begruendung |
|---|---|---|
| astral-sh/uv | **bereits verfuegbar** | siehe `dev-toolbelt` |
| astral-sh/ruff | **bereits verfuegbar** | siehe `dev-toolbelt` |
| pre-commit/pre-commit | **bereits verfuegbar** | siehe `dev-toolbelt` |
| tree-sitter/tree-sitter | Kandidat | fuer eigenes Tooling (z. B. Codeanalyse), aktuell kein Bedarf |
| sharkdp/bat | **bereits verfuegbar** | siehe `dev-toolbelt` (als `batcat`) |
| sharkdp/fd | **bereits verfuegbar** | siehe `dev-toolbelt` (als `fdfind`) |
| BurntSushi/ripgrep | **bereits verfuegbar** | siehe `dev-toolbelt`, nutzt das Grep-Tool intern |
| jesseduffield/lazygit | Kandidat | Terminal-UI fuer Git, kein Mehrwert in einer nicht-interaktiven Sitzung |
| starship/starship | nicht anwendbar | Shell-Prompt-Deko, kein funktionaler Nutzen hier |
| neovim/neovim | nicht anwendbar | interaktiver Editor fuer Menschen |
| tmux/tmux | **bereits verfuegbar** | siehe `dev-toolbelt` |

## Editoren/IDEs (nicht anwendbar in einer Agenten-Sitzung)

| Repo | Status | Begruendung |
|---|---|---|
| zed-industries/zed | nicht anwendbar | Editor fuer Menschen |
| microsoft/vscode | nicht anwendbar | Editor fuer Menschen |
| getcursor/cursor | nicht anwendbar | Editor fuer Menschen |
| TabbyML/tabby | nur Referenz | selbst gehosteter Code-Vervollstaendiger, eigener GPU-Server |

## Security-Scanner (bereits bewertet, siehe `security-scan`)

| Repo | Status | Begruendung |
|---|---|---|
| StacklokLabs/repoaudit | nur Referenz | nicht getestet, Ueberschneidung mit unserem `security_scan.py` |
| trufflesecurity/trufflehog | **blockiert** | Release-Binary hinter Proxy nicht erreichbar (verifiziert) |
| anchore/syft | **blockiert** | dito |
| anchore/grype | **blockiert** | dito |
| aquasecurity/trivy | **blockiert** | dito, in `dev-toolbelt` dokumentiert |
| gitleaks/gitleaks | **blockiert** | dito, in `dev-toolbelt` dokumentiert |
| hashicorp/vault | Kandidat | fuer echtes Secret-Management, sobald ueber `.env` hinausgewachsen wird |

## Observability-Infrastruktur (schwergewichtig, eigener Server noetig)

| Repo | Status | Begruendung |
|---|---|---|
| open-telemetry/opentelemetry-collector | Kandidat | Standard-Weg, unsere Prometheus-Metriken zentral zu sammeln |
| getsentry/sentry | Kandidat | Error-Tracking, sinnvoll sobald echte Nutzer da sind |
| grafana/loki | nur Referenz | Log-Aggregation, eigener Server |
| elastic/elasticsearch | nur Referenz | Overkill fuer unsere Datenmengen |
| opensearch-project/OpenSearch | nur Referenz | dito |
| meilisearch/meilisearch | Kandidat | leichtgewichtige Suche, falls Produkt A/B Volltextsuche braucht |
| typesense/typesense | Kandidat | Alternative zu Meilisearch, gleicher Anwendungsfall |
| milvus-io/milvus | nur Referenz | Vektor-DB fuer Grossmengen, aktuell kein Bedarf |
| weaviate/weaviate | nur Referenz | dito |

## Wissens-/Memory-Graphen (Kandidat fuer Agenten-Gedaechtnis)

| Repo | Status | Begruendung |
|---|---|---|
| getzep/graphiti | Kandidat | Wissensgraph fuer Agenten-Gedaechtnis, passt zur Frage "wie merkt sich das System etwas" |
| getzep/zep | Kandidat | Memory-Layer fuer LLM-Apps, gleicher Anwendungsfall |

## BI/Analytics (Kandidat, spaeter)

| Repo | Status | Begruendung |
|---|---|---|
| apache/superset | nur Referenz | schwergewichtiges BI-Tool, eigener Server |
| metabase/metabase | Kandidat | leichter einzurichten als Superset, fuer spaetere Business-Dashboards |

## Web-/Site-Frameworks (falls Marketing-Sites entstehen)

| Repo | Status | Begruendung |
|---|---|---|
| gohugoio/hugo | Kandidat | statische Marketing-Seiten (aehnlich der bestehenden GitHub-Pages-Site) |
| nuxt/nuxt | nur Referenz | Vue-Framework, unser Stack ist nicht Vue-basiert |
| sveltejs/kit | nur Referenz | eigenes Framework, kein aktueller Bezug |
| remix-run/remix | nur Referenz | React-Framework, aktuell kein Bedarf (Dashboard ist bewusst simples HTML/JS) |

## Mobile (Kandidat fuer spaetere App, aktuell kein Web-Aequivalent)

| Repo | Status | Begruendung |
|---|---|---|
| ionic-team/ionic-framework | Kandidat | Web-basierte Mobile-App, falls Produkt A/B eine App braucht |
| expo/expo | Kandidat | React-Native-Tooling, gleicher Anwendungsfall |
| flutter/flutter | nur Referenz | eigenes Sprach-Oekosystem (Dart), groesserer Umstieg |
| facebook/react-native | Kandidat | naheliegendste Wahl, falls eine native App noetig wird |

## Runde 2 — ~300 weitere genannte Repos (26.07., kompakt bewertet)

Gleiche Bewertungslogik wie oben, nur dichter: bei dieser Menge wuerde eine
Einzelbegruendung pro Repo (wie in Runde 1) die Datei auf ein Vielfaches
aufblaehen — und genau das widerspricht der eigenen Regel aus `CLAUDE.md`
("nicht mit Kleinkram vollstopfen"). Deshalb hier pro Themenblock **eine
gemeinsame Einordnung**, mit Einzelnennung nur, wo der Status vom Block
abweicht.

| Themenblock | Repos (Auswahl) | Status |
|---|---|---|
| Multi-Agent-Frameworks | crewAI, AutoGen, LangGraph, LangChain, MetaGPT, CAMEL, agent-zero, AG2, Mastra, pydantic-ai, Agno, ChatDev, AutoGPT, SuperAGI, taskade/agentic | nur Referenz — Alternativen zu unserem eigenen schlanken FastAPI+LiteLLM-Agentenmodell, keine Ersetzung geplant |
| KI-Chat-Oberflaechen | LibreChat, anything-llm, lobe-chat, FlowiseAI, FastChat | nur Referenz — Konkurrenz zum eigenen Dashboard |
| Multi-Provider-Gateway | BerriAI/litellm | **bereits genutzt** (`litellm/config.yaml`) |
| " | songquanpeng/one-api | nur Referenz — litellm deckt den Bedarf bereits ab |
| KI-Coding-Agenten | aider, cline, Roo-Code, continue, sourcegraph/amp, devika, bolt.new, CodeFuse | nur Referenz — wir arbeiten bereits mit Claude Code selbst |
| Bild-/Video-Generierung | ComfyUI, Stability generative-models, AnimateDiff, FramePack, stable-diffusion-webui, InvokeAI, Fooocus, FLUX | Kandidat fuer Produkt C, aber GPU-Server noetig — hier nicht lauffaehig; aktuell deckt MuAPI (Cloud-API, kein eigener Server) denselben Bedarf |
| TTS/STT | coqui TTS, OpenVoice, chatterbox, whisper, faster-whisper, bark, audiocraft, stable-audio-tools | Kandidat falls Sprache-zu-Text gebraucht wird |
| " | rhasspy/piper | **bereits genutzt** (Produkt C Voiceover) |
| Talking-Head/Avatar | LivePortrait, SadTalker | Kandidat, aktuell kein Avatar-Feature geplant |
| Browser-/Computer-Steuerung | open-interpreter, browser-use, Selenium, crawl4ai, firecrawl, jina-reader, Stagehand, Browserbase, Puppeteer | Kandidat je nach Automatisierungsbedarf |
| " | microsoft/playwright | **bereits verfuegbar** (Chromium vorinstalliert, siehe `dev-toolbelt`) |
| RAG/Vektor-Suche/Wissensgraph | llama_index, Haystack, Chroma, Qdrant, Weaviate, Milvus, Neo4j, Memgraph, mem0, Zep | Kandidat fuer Agenten-Gedaechtnis in Produkt A, noch nicht gebaut |
| Automatisierung/Workflow | n8n, Activepieces, Windmill, Trigger.dev, Temporal, Airflow, Inngest | Kandidat — ueberschneidet sich mit unseren eigenen Webhook-Handlern (`routes/webhooks.py`) |
| Notebooks/Datenanalyse | JupyterLab, pandas-ai | Kandidat fuer eigene Datenanalyse, nicht produktkritisch |
| Self-hosted Backend-Plattformen | Supabase, Appwrite, PocketBase | nur Referenz — eigenes Postgres+FastAPI+RLS bereits gebaut |
| Deploy/PaaS | Coolify, Dokploy, CapRover | Kandidat fuer eigenes Hosting, aktuell laeuft Deploy ueber `render.yaml` (Render.com) |
| LLM-Inferenz/Serving (GPU) | vLLM, SGLang, transformers, TGI, mlc-llm, exo, llama.cpp, LMDeploy, ExLlamaV2, PEFT, Accelerate, TensorRT-LLM | nur Referenz — brauchen eigenen GPU-Server, den diese Sandbox nicht hat |
| Frontend-Frameworks | React Native, Flutter, Expo, Next.js, Nuxt, Astro, Remix, Gatsby, Eleventy | Kandidat nur falls eigene Web-/Mobile-App noetig wird (Dashboard ist bewusst simples HTML/JS) |
| Social/Marketing-Planung | Postiz | Kandidat fuer Produkt B Social-Media-Planung |
| Business-Analytics | maybe-finance, Plausible, PostHog, Grafana | Kandidat fuer spaetere Business-Dashboards |
| Persoenliche Produktivitaet | Firefly III, Actual, AppFlowy, Outline, Immich, Paperless-ngx, Logseq, Joplin, Standard Notes | nicht anwendbar — privates Tooling ohne Bezug zu Produkt A/B/C |
| Hardware/Robotik/CAD/3D-Druck/Drohnen/Game-Engines | ROS2, ArduPilot, PX4, Home Assistant, Godot, Bevy, Unity ML-Agents, ESPHome, Zigbee2MQTT, OctoPrint, PrusaSlicer, FreeCAD, OpenSCAD | **nicht anwendbar** — komplett ausserhalb der drei Produkte, keine Hardware in dieser Sandbox |
| Offensive Security/Pentesting | sqlmap, Metasploit Framework | **bewusst nicht aktiviert** — Angriffswerkzeuge, die ohne konkreten autorisierten Pentest-/CTF-Auftrag nicht eingesetzt werden (gilt generell fuer diese Sitzung, nicht nur hier) |
| " | OWASP ZAP, Nuclei, httpx (ProjectDiscovery), Ghidra, Rizin, SonarQube | Kandidat als *defensiver* Scanner der eigenen Plattform, falls explizit beauftragt — aktuell kein solcher Auftrag |
| Backend-Frameworks | Express, NestJS, gRPC | nur Referenz — unser Stack ist FastAPI |
| " | fastapi/fastapi | **bereits Kernstueck** von Produkt A |
| Test-Tools | Cypress, Jest | Kandidat falls Frontend-E2E-Tests noetig werden |
| UI-Kits/Design-Systeme | shadcn/ui, Tailwind CSS, Radix, Chakra UI, MUI | Kandidat falls Dashboard auf ein echtes Frontend-Framework umgestellt wird |
| Streaming/Media-Server/3D | OBS Studio, Owncast, MediaMTX, Instant-NGP, Nerfstudio, Blender | nicht anwendbar — kein Video-Streaming- oder 3D-Produkt |
| Container/Infra/IaC | docker compose, Buildx, Moby, Kubernetes, Helm, k3s, Terraform, Pulumi, Crossplane | nur Referenz — Docker-Daemon in dieser Sandbox nicht verfuegbar (siehe `dev-toolbelt`), Deploy laeuft ueber Render |
| Chat-/Community-Plattformen | Mattermost, Element, Rocket.Chat, Discourse, NodeBB | nicht anwendbar — kein internes Chat-Produkt geplant |
| Videokonferenz/Sprachassistent | Jitsi, LiveKit, LiveKit Agents, Pipecat, Vocode, Rhasspy | Kandidat NUR falls ein Sprachassistent-Feature (wie das separate JAVIER-Projekt) auf diese Plattform kommt |
| CRM/ERP | Twenty, Evolution API, ERPNext, Frappe CRM, Odoo, Monica | nur Referenz — Konkurrenzprodukte, keine Integration geplant |
| Kalender/Termine | Nextcloud Calendar, Easy!Appointments | Kandidat fuer Produkt B Kundentermine (Cal.com bereits in Runde 1 gelistet) |
| E-Mail-Infrastruktur | Postal, Mailcow, Listmonk, Mailtrain | Kandidat falls eigener Mailversand noetig wird — aktuell kein SMTP-Feature gebaut |
| Suche | SearXNG | Kandidat (Meilisearch/Typesense bereits in Runde 1) |
| Monitoring/Observability | Loki, Jaeger, Helicone, OpenLIT, DeepEval | Kandidat (Prometheus **bereits genutzt** in `metrics.py`; Sentry/Langfuse/Phoenix bereits Runde 1) |
| Dateiverwaltung/Storage | Filebrowser, Nextcloud Server, MinIO, Ceph, Seafile | Kandidat falls eigener Objektspeicher noetig wird |
| Security-Scan | Falco | nur Referenz — Trivy/Grype bereits in Runde 1 als "blockiert" dokumentiert |
| Karten | OpenStreetMap, MapLibre | nicht anwendbar |
| Datenbanken | Redis, Dragonfly, MySQL, MongoDB | Kandidat fuer Caching (aktuell eigene Sliding-Window-Rate-Limiter-Implementierung) |
| " | postgres/postgres | **bereits Kern unseres Stacks** |
| ML-Frameworks | scikit-learn, PyTorch, TensorFlow, PyTorch Lightning | nur Referenz — kein eigenes Modelltraining geplant |
| Desktop-Frameworks | Tauri, Electron | nur Referenz |
| OCR/PDF/Uebersetzung | OCRmyPDF, Stirling-PDF, Tesseract, PaddleOCR, LibreTranslate, Argos Translate | Kandidat falls ein Rechnungs-/Dokumenten-Feature gebaut wird |
| Passwort-Manager | Bitwarden, KeePassXC | nicht anwendbar — eigenes Secret-Management via `.env`, Vault als Kandidat bereits in Runde 1 |
| Support/Formulare/Doku | Chatwoot, Formbricks, Typebot, Documenso, InvoiceNinja, Akaunting, FreeScout, SurveyJS | Kandidat fuer Kundenservice-Ausbau von Produkt A/B |
| Shopify-eigene Werkzeuge | Shopify/cli, Shopify/dawn, Shopify/hydrogen, Shopify/polaris | **Kandidat, direkt relevant** — das sind Shopifys eigene Theme-/Storefront-Werkzeuge fuer Produkt B, kein Fremdprodukt |
| E-Commerce-Alternativen | Vendure, Spree, Sylius, WooCommerce, Bagisto, ReactionCommerce, Sharetribe, Magento, Shopware | nur Referenz — Konkurrenzprodukte zu Shopify, Produkt B baut bewusst AUF Shopify auf |
| Website-Builder/No-Code | Plasmic, GrapesJS, Webstudio, Builder.io, Budibase, NocoBase | nur Referenz |
| CMS | KeystoneJS, Ghost | nur Referenz (Strapi/Directus/Payload bereits Runde 1) |
| Auth | NextAuth, Clerk, Supabase Auth | Kandidat falls Login ueber eigene API-Keys hinauswaechst |
| SaaS-Starter-Kits | BoxyHQ, Nextacular, Makerkit, Wasp/open-saas | nur Referenz — Produkt A ist bereits weiter als ein Starter-Kit |
| MCP | modelcontextprotocol/servers | Kandidat — Registry mit Hunderten MCP-Servern, ergaenzt die bereits genutzten SDKs |
| " | Gmail-MCP-Server | nur Referenz — diese Sitzung nutzt bereits einen offiziellen Gmail-MCP-Server |
| Affiliate/Links | Dub, Kutt | Kandidat |
| Marketing/SEO-Themes | Hugo-Modules, Starlight | Kandidat (Hugo selbst bereits Runde 1) |
| Bildungsplattform | LibreEdu, OpenCourseLab | nicht anwendbar |
| Payment-Beispiele | adyen-examples | nur Referenz — wir nutzen Stripe direkt per HMAC, kein SDK |

## Zusammenfassung

- **Bereits genutzt/verfuegbar:** ollama, Piper, litellm, FastAPI, PostgreSQL,
  Prometheus, Playwright/Chromium, MCP Python-SDK, uv, ruff, pre-commit, bat,
  fd, ripgrep, tmux, TypeScript, Python.
- **Echte Kandidaten fuer Produkt A/B/C**, wenn konkret gebraucht: E2B,
  openai-agents-python, dspy, smolagents, composio, agentops, langfuse,
  phoenix, inngest/trigger.dev, supabase-mcp, vault, opentelemetry-collector,
  sentry, meilisearch/typesense, graphiti/zep/mem0, metabase, hugo,
  ionic/expo/react-native, Shopify/dawn+hydrogen+polaris (Produkt B),
  n8n/windmill (Automatisierung), Redis/Dragonfly (Caching), Chatwoot/
  Formbricks (Kundenservice).
- **Bewusst nicht aktiviert:** sqlmap, Metasploit Framework — Angriffs-
  werkzeuge ohne aktuellen autorisierten Pentest-/CTF-Auftrag.
- **Nur Referenz oder nicht anwendbar:** der grosse Rest — meist weil es
  Editoren, Konkurrenzprodukte, Hardware/Robotik/Game-Engines oder
  Infrastruktur ist, die einen eigenen Server/GPU/Cluster braucht, den diese
  Sandbox nicht hat.

Wird ein Kandidat konkret gebraucht, wird er **gezielt integriert** (Code,
Tests, Doku) — nicht pauschal "installiert". Das ist der ehrliche Unterschied
zwischen "in der Liste erwaehnt" und "im Produkt wirksam". Diese Datei selbst
ist der reale Mechanismus, der das ueberlebt: sie ist committet und wird bei
jedem "was ist mit Repo X"/"installiere Y" zuerst konsultiert (siehe
`CLAUDE.md` und der Trigger-Beschreibung oben).
