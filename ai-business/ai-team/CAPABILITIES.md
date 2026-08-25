# CAPABILITIES — Gesamtueberblick

Ein Register aller Faehigkeiten dieser Claude-Code-Umgebung, gruppiert nach Wirkung. Details je Kategorie in den Nachbardateien.

## 1. Orchestrierung (eigen)
- **ULTRA AI ENTERPRISE OS** — Skill + 12 Agenten + 3 Commands. Stellt fuer eine Aufgabe die passende virtuelle Organisation zusammen, fuehrt aus, reviewt (QA/Security/Architektur), liefert konsolidiert. → AGENTS.md, COMMANDS.md.
- **omni-team / rat.py** — externe Modell-Flotte (7 fremde Modelle) fuer echte Zweitmeinungen ueber OmniRoute. → TOOLS.md.

## 2. Business & Marketing
- **marketing-skillstack** (49 Skills): Positionierung, Copywriting, CRO, Pricing, SEO/AEO, Ads, E-Mail, Onboarding, Retention, Analytics.
- **wshobson-Subagents** (17 aktiv): komplettes SEO-Team + Business/Sales/Content/Support/Research.
- **marketing/** (eigen): Ad-Assets, Kurzfilme.
→ SKILLS.md, SUBAGENTS.md.

## 3. Web, Design, 3D
- **design-skillstack** (22 Skills, 27 Agents) + **threejs-skills** (10): GSAP, R3F, Three.js, Babylon, Pixi, Framer Motion, Lottie, Rive, Spline, Blender-Pipeline.
- Projekt-Design-Skills: `apple-design`, `emil-design-eng`, `animate`, `dataviz`, `design`, `design-taste`.
→ SKILLS.md, AGENTS.md.

## 4. Engineering & Sicherheit
- **wshobson-Katalog** (202 Agents): engineering-*, security-*, testing-*, data, devops, PM u.v.m.
- **security-guidance** (Hooks): Injection/XSS/SSRF/Secrets/IDOR/Auth-Checks bei Edit/Write/Commit.
→ AGENTS.md, PLUGINS.md.

## 5. Automatisierung & Daten
- **n8n-templates** (328 Workflows).
- **MCP-Server** (10): Shopify, Meta Ads, DSers, Gmail, Drive, Higgsfield, ChatPlace, GitHub, Economic Index, Claude-Code-Remote.
- **curbcut** (eigenes A11y-Produkt, 13 .py + Cron-Waechter).
→ TOOLS.md, MCP.md.

## 6. Dokumente & Medien (Claude-only)
- Anthropic-First-Party: pdf, docx, pptx, xlsx, canvas-design, artifacts-*, dataviz. → CLAUDE_ONLY, siehe SKILLS.md.

## Portierbarkeit-Kurzbilanz
| Klasse | Beispiele | OpenCode |
|---|---|---|
| DIRECT | rat.py, curbcut, n8n-Workflows | sofort |
| ADAPTABLE | ULTRA/wshobson/design-Agenten, alle Instruktions-Skills, Commands | Format mappen |
| AUTH_REQUIRED | alle MCP, omni-team, Higgsfield | Neu-Login/Key |
| CLAUDE_ONLY | Doc-/Medien-Skills, Hook-Mechanik, Claude-Tools | nicht 1:1 |

## Sicherheit
Keine Secrets exportiert. Kopierte Tools beziehen Keys aus Umgebungsvariablen. Secret-Scan vor Commit durchgefuehrt. → EXPORT-MANIFEST.md.
