# SUBAGENTS

Als "Subagents" bezeichnen wir hier die aus dem **wshobson-Katalog aktivierten** Fachagenten, die im Projekt (`.claude/agents/wshobson-*.md`) freigeschaltet sind und **nach `capabilities/subagents/` kopiert** wurden. Es sind Markdown-Instruktionen ohne Secrets — voll portabel als Rollen-Prompts.

## Aktivierte wshobson-Subagents (17 — KOPIERT)

| Datei | Rolle | Business-Nutzen |
|---|---|---|
| `wshobson-startup-analyst.md` | Startup-Analyst | Marktgroesse (TAM/SAM/SOM), Unit Economics, Finanzprojektionen |
| `wshobson-business-analyst.md` | Business-Analyst | KPI-Frameworks, Dashboards, strategische Auswertung |
| `wshobson-content-marketer.md` | Content-Marketer | Content-Strategie, Omnichannel, SEO-Content |
| `wshobson-sales-automator.md` | Sales-Automator | Cold-Mails, Follow-ups, Angebots-Templates, Verkaufsskripte |
| `wshobson-customer-support.md` | Customer-Support | Support-Automatisierung, Ticketing, Sentiment |
| `wshobson-search-specialist.md` | Research/Search-Spezialist | Tiefenrecherche, Wettbewerbsanalyse, Fact-Checking |
| `wshobson-context-manager.md` | Context-Manager | Kontext ueber lange/mehrstufige Aufgaben verwalten |
| `wshobson-seo-authority-builder.md` | SEO — E-E-A-T | Autoritaets-/Trust-Signale, YMYL |
| `wshobson-seo-content-writer.md` | SEO — Content-Writer | SEO-Texte nach Keyword-Brief |
| `wshobson-seo-content-planner.md` | SEO — Content-Planner | Themencluster, Redaktionsplan |
| `wshobson-seo-content-auditor.md` | SEO — Content-Auditor | Qualitaets-/E-E-A-T-Scoring |
| `wshobson-seo-content-refresher.md` | SEO — Content-Refresher | Veraltete Inhalte aktualisieren |
| `wshobson-seo-keyword-strategist.md` | SEO — Keyword-Stratege | Keyword-Dichte, LSI, Over-Optimization vermeiden |
| `wshobson-seo-meta-optimizer.md` | SEO — Meta-Optimizer | Titel/Descriptions/URLs im Zeichenlimit |
| `wshobson-seo-snippet-hunter.md` | SEO — Snippet-Hunter | Featured-Snippet-/SERP-Formatierung |
| `wshobson-seo-structure-architect.md` | SEO — Structure-Architect | Header-Hierarchie, Schema, interne Verlinkung |
| `wshobson-seo-cannibalization-detector.md` | SEO — Kannibalisierung | Keyword-Ueberschneidungen aufspueren |

**Schwerpunkt:** ein vollstaendiges SEO-Team (10) + Business/Sales/Content/Support/Research (7). Genau der Stack fuer einen Ein-Produkt-Shop wie Let'sDrink.

## Der ganze Katalog (nicht aktiviert, referenziert)
Weitere 185 wshobson-Agenten liegen unter `../wshobson-agents/plugins/*/agents/` bereit (Engineering, Finance, Security, GIS, Testing, PM, u.v.m.). Aktivierung: Datei nach `.claude/agents/` kopieren.

## Portierungsweg (OpenCode)
Jede Datei ist ein Rollen-Prompt: Body als System-Prompt eines OpenCode-Agenten uebernehmen, Frontmatter-Tools mappen. Kein Auth noetig, keine Secrets.

## Portierbarkeit
Alle 17: **ADAPTABLE**, **NOT_TESTED** in OpenCode.
