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

## Zusammenfassung

- **Bereits genutzt/verfuegbar:** ollama, MCP Python-SDK, uv, ruff, pre-commit,
  bat, fd, ripgrep, tmux, TypeScript, Python.
- **Echte Kandidaten fuer Produkt A/B/C**, wenn konkret gebraucht: E2B,
  openai-agents-python, dspy, smolagents, composio, agentops, langfuse,
  phoenix, inngest/trigger.dev, supabase-mcp, vault, opentelemetry-collector,
  sentry, meilisearch/typesense, graphiti/zep, metabase, hugo,
  ionic/expo/react-native.
- **Nur Referenz oder nicht anwendbar:** der Rest — meist weil es Editoren,
  Konkurrenzprodukte oder Infrastruktur ist, die einen eigenen Server/GPU
  braucht, den diese Sandbox nicht hat.

Wird ein Kandidat konkret gebraucht, wird er **gezielt integriert** (Code,
Tests, Doku) — nicht pauschal "installiert". Das ist der ehrliche Unterschied
zwischen "in der Liste erwaehnt" und "im Produkt wirksam".
