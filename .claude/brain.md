# 🧠 Brain — Projektgedächtnis (Nate8645er/Nate)

Persistentes Gedächtnis dieses Projekts. Claude Code liest diese Datei zu Beginn
substanzieller Aufgaben und ergänzt nach relevanten Arbeiten einen kurzen Eintrag
(Datum + was/warum). Ältestes zuerst.

---

## Projekt-Historie (seit der ersten Claude-Nutzung)

### Session 1 — Repo-Start & ULTRA AI ENTERPRISE OS
*(Commits: `d348d16`, `372b63b`, `e8d8317`)*

- **Initial commit**: Repository `Nate8645er/Nate` angelegt.
- **ULTRA AI ENTERPRISE OS Plugin** gebaut (`ultra-enterprise-os/`):
  - Meta-Orchestrator-Skill, der Sessions in ein virtuelles Technologieunternehmen verwandelt (Aufgabe zerlegen → Teams zusammenstellen → parallel arbeiten → Qualitäts-Gates → konsolidiertes Ergebnis).
  - Agenten: ultra-architect, ultra-orchestrator, ultra-fullstack, ultra-design, ultra-devops, ultra-data-ml, ultra-qa, ultra-security, ultra-business, ultra-docs.
  - Commands: `/ultra`, `/ultra-review`, `/ultra-team`.
  - Skills: ultra-enterprise-os, ultra, ultra-review, ultra-team.
- **Marketplace-Manifest** (`.claude-plugin/marketplace.json`) erstellt, damit das Repo als Plugin-Marketplace `nate-marketplace` dient; Plugin in `.claude/` gespiegelt, damit es in allen Sessions automatisch lädt (`.claude/settings.json`: enabledPlugins).

### Session 2 — 2026-07-12 — Graphify-Installation & Integration
*(Branch: `claude/graphify-claude-code-setup-qnj1v4`)*

- **Umgebung geprüft**: Python 3.11.15 ✓, uv 0.8.17 ✓, Node 22.22.2 ✓, Git 2.43 ✓, Claude Code CLI 2.1.207 ✓.
- **Graphify 0.9.13 installiert** (`uv tool install`, PyPI-Name `graphifyy`, Quelle: github.com/safishamsi/graphify). Installiert aus der vom User hochgeladenen ZIP-Quelle, nachdem der Code auf verdächtiges Verhalten geprüft wurde (sauber: nur erwartete LLM-API-Endpunkte, keine Exfiltration).
- **Claude-Code-Integration registriert**:
  - `graphify install --project` → Skill nach `.claude/skills/graphify/`, Registrierung in `.claude/CLAUDE.md`.
  - `graphify claude install` → Graphify-Regeln in `CLAUDE.md`, PreToolUse-Hooks (Bash-Suche + Read/Glob werden zum Graph umgeleitet) in `.claude/settings.json`.
  - Hooks robust gemacht (kein harter Pfad; No-Op wenn Graphify fehlt) und **SessionStart-Hook** ergänzt: installiert `graphifyy==0.9.13` automatisch in frischen Cloud-Containern und prüft Graph-Aktualität.
- **Knowledge Graph gebaut** (`graphify . --backend claude-cli`, kein API-Key nötig):
  - 45 Dateien gescannt (3 Code, 42 Docs), 42 Knoten, 53 Kanten, 12 Communities.
  - Ausgabe: `graphify-out/graph.json`, `GRAPH_REPORT.md`, `graph.html`.
- **Token-Optimierungsregeln** in `CLAUDE.md` ergänzt (Graph zuerst, keine Repo-Scans, Kontext klein halten).
- **Neue Commands** angelegt: `/project-map`, `/find-impact <datei>`, `/explain-module <name>`, `/optimize-context`.
- **Brain angelegt**: diese Datei (`.claude/brain.md`), referenziert aus `CLAUDE.md`.

### Session 3 — 2026-07-12 — Higgsfield AI Creative System
*(gleicher Branch: `claude/graphify-claude-code-setup-qnj1v4`, PR #15)*

- **5 Higgsfield Skills** projekt-lokal installiert (`.claude/skills/`, aus dem offiziellen Repo `higgsfield-ai/skills` v0.12.0, vom User als ZIP hochgeladen): higgsfield-generate, higgsfield-soul-id, higgsfield-product-photoshoot, higgsfield-marketplace-cards, higgsfield-websites.
- **Higgsfield CLI v1.1.13** global installiert (`npm install -g @higgsfield/cli`). Achtung: CLI braucht `higgsfield auth login`; im ephemeren Container muss sie ggf. neu installiert werden — der **Higgsfield MCP-Server** ist der zuverlässige Weg (bereits verbunden, ~70 Tools).
- **CLAUDE.md**: Abschnitt „Higgsfield Creative Agent Mode" mit Arbeitsweise (Ziel → Produktionsplan → Funktion → Prompts → Konsistenz) und 3 Produktionsmodi (Hollywood / Werbeagentur / Social Media Creator).
- **6 neue Commands**: `/movie`, `/ad`, `/trailer`, `/storyboard`, `/product-video`, `/cinematic`.
- **Kontostand bei Setup**: 0,2 Credits (Starter-Plan) → echte Bild-/Video-Generierung erst nach Credit-Aufladung; Konzepte/Prompts sind gratis. Kosten-Regel in CLAUDE.md verankert (vor Render-Batches bestätigen).
- Wichtige Modelle (via `models_explore`): Seedance 2.0 & Cinema Studio Video 3.0 (Video), GPT Image 2 / Nano Banana 2/Pro / Seedream 5.0 / FLUX.2 (Bild), Soul 2.0 / Soul Cinema (Charaktere), Marketing Studio (Ads/UGC), Seed Audio 1.0 (Audio), Meshy/SAM-3 (3D).

## Entscheidungen & Konventionen

- **Graph zuerst**: Codebase-Fragen laufen über `graphify query/explain/path/affected`, nicht über grep/find/volles Lesen. Erzwungen per PreToolUse-Hooks.
- **LLM-Backend**: `claude-cli` (nutzt die lokale Claude-Code-Installation, kein API-Key erforderlich). Für AST-only-Updates: `graphify update .` (kostenlos).
- **Persistenz**: Der Cloud-Container ist ephemer — alles Dauerhafte muss committet werden. Deshalb sind Skill, Hooks, Commands, Graph-Output und dieses Brain im Repo versioniert; der SessionStart-Hook stellt das Graphify-Binary in neuen Sessions wieder her.
- **Graphify-Version gepinnt** auf 0.9.13 (geprüfter Stand); Upgrade bewusst und nach Review durchführen.

## Offene Punkte

- (leer)

---

*Neue Einträge unten anfügen: `### Session N — YYYY-MM-DD — Titel` + Stichpunkte.*
