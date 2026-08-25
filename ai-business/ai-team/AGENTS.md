# AGENTS

Agenten sind Markdown-Dateien mit YAML-Frontmatter (`name`, `description`, `tools`) und einem Rollen-/Instruktions-Body. Der **Body und die Rollendefinition sind portabel**; das Frontmatter muss auf OpenCodes Agenten-Schema gemappt werden (Tool-Namen, Modellwahl).

## Zahlen
- **Home installiert (`~/.claude/agents`):** 280 (Obermenge).
- **Projekt aktiv (`.claude/agents`):** 56 = 12 ULTRA + 27 design-skillstack + 17 wshobson-Subagents.
- **Quelle wshobson:** 202 Agents im Katalog (`../wshobson-agents`).
- **Quelle design-skillstack:** 27 Agents (`../design-skillstack/agents`).

## ULTRA-Team (12, eigen — KOPIERT nach `capabilities/agents/`)

| Agent | Rolle | Tools (Frontmatter) |
|---|---|---|
| `ultra-orchestrator` | Chief of Staff — zerlegt Vorhaben, definiert Ownership + DoD, liefert Ausfuehrungsplan | Read, Glob, Grep, Bash |
| `ultra-architect` | CTO/Lead-Architect — Systemarchitektur, Tech-Entscheidungen, Trade-offs | Read, Glob, Grep, Bash, WebSearch, WebFetch |
| `ultra-fullstack` | Full-Stack-Engineering (Frontend, Backend, Mobile, APIs, DB) | All tools |
| `ultra-business` | Strategie, Finance, Marketing, Sales, Branding, SEO, Content | Read, Glob, Grep, WebSearch, WebFetch |
| `ultra-design` | UI/UX & Product-Design | All tools |
| `ultra-data-ml` | Data-Science, ML, AI-Research | All tools |
| `ultra-devops` | CI/CD, Deployment, IaC, Monitoring, Kostenkontrolle | All tools |
| `ultra-qa` | QA — Tests schreiben/ausfuehren, Edge Cases | All tools |
| `ultra-security` | CISO (rein defensiv) — Injection, Auth, Secrets, Datenlecks | Read, Glob, Grep, Bash |
| `ultra-docs` | Dokumentation & Projektmanagement | Read, Glob, Grep, Write, Edit |
| `ultra-prime` | Elite-Generalist (Full-Stack + Business + CH-Recht + Design + Security-Grundpruefung in einer Rolle) | All tools |
| `omni-team` | Dispatcher zur externen Modell-Flotte via OmniRoute (Zweitmeinungen, Cross-Model-Checks) — braucht OPENROUTER_API_KEY + laufenden Server | All tools |

**Rollen-Abdeckung (vom Auftrag gefordert):** CEO/Chief of Staff → `ultra-orchestrator`/`ultra-prime`; CTO/Architect → `ultra-architect`; Developer/Frontend/Backend/DevOps → `ultra-fullstack`/`ultra-devops`; Security → `ultra-security`; QA → `ultra-qa`; Data → `ultra-data-ml`; Design → `ultra-design`; Marketing/Sales → `ultra-business` (+ wshobson-Subagents); Product → `ultra-orchestrator`/`ultra-business`; Research → `omni-team`/`wshobson-search-specialist`.

## wshobson-Subagents (17 aktiviert — KOPIERT nach `capabilities/subagents/`)
Siehe SUBAGENTS.md.

## design-skillstack-Agents (27, referenziert `../design-skillstack/agents`)
3D-/Animations-Spezialisten: `threejs-webgl-architect`, `react-three-fiber-architect`, `babylonjs-engine-architect`, `gsap-scrolltrigger-choreographer`, `motion-framer-choreographer`, `pixijs-2d-architect`, `playcanvas-engine-architect`, `aframe-webxr-architect`, `lottie-animations-choreographer`, `rive-interactive-choreographer`, `spline-interactive-pipeline`, `locomotive-scroll-specialist`, `scroll-reveal-libraries-specialist`, `animejs-choreographer`, `barba-js-specialist`, `react-spring-physics-choreographer`, `blender-web-pipeline-pipeline`, `substance-3d-texturing-pipeline`, `lightweight-3d-effects-architect`, `modern-web-design-specialist`, `web3d-integration-patterns-specialist`, `animated-component-libraries-specialist`, + 5 Integrations-Rollen.

## wshobson-Katalog (202, referenziert `../wshobson-agents`)
Grosse Domaenen-Sammlung: `engineering-*` (~60: backend/frontend/mobile/devops/data/security/…), `marketing-*` (~40), `sales-*` (~12), `finance-*`, `security-*` (~12), `gis-*`, `design-*`, `testing-*`, `project-management-*`, `academic-*`, `specialized-*`, u.a. Vollstaendige Liste: `../wshobson-agents/AGENTS.md`.

## Portierungsweg
- **Claude Code:** `.md` in `.claude/agents/` legen → Agent-Typ verfuegbar; via Task/Agent-Tool aufrufbar.
- **OpenCode:** Rollen-Body als System-Prompt eines OpenCode-Agenten; `tools:`-Frontmatter auf OpenCodes Tool-Set mappen; `All tools` → OpenCodes Standard-Toolset.

## Portierbarkeit
- ULTRA + wshobson + design-skillstack: **ADAPTABLE** (reine Instruktionen).
- `omni-team`: **AUTH_REQUIRED** (OmniRoute + OpenRouter-Key).

## NOT FOUND
- Keine Agents ausserhalb der genannten Quellen.
