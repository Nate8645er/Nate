# SKILLS

Skills sind Instructions-Pakete (`SKILL.md` + optionale Hilfsdateien), die Claude bei passenden Aufgaben laedt. Sie sind fast immer **portable Textanleitungen** — der Inhalt ist auch fuer OpenCode wertvoll, nur der Auto-Lade-Mechanismus ist Claude-Code-spezifisch.

## Herkunft der 120 aktivierten Skills (`~/.claude/skills`)

`~/.claude/skills` ist die aktivierte Obermenge. Sie speist sich aus:

| Quelle | Anzahl | Ort im Repo | Portierbar |
|---|---:|---|---|
| **Anthropic First-Party** | ~25 | nicht im Repo (Home) | CLAUDE_ONLY — haengen an Artifacts/Sandbox/pdf-libs |
| **marketing-skillstack** (coreyhaines31) | 49 | `../marketing-skillstack/skills` | ADAPTABLE |
| **awesome-skillstack** (Composio) | 25 | `../awesome-skillstack/skills` | ADAPTABLE |
| **design-skillstack** | 22 | `../design-skillstack/skills` | ADAPTABLE |
| **threejs-skills** (pinkforest) | 10 | `../threejs-skills/skills` | ADAPTABLE |
| **ultra-enterprise-os** (eigen) | 1 | `../ultra-enterprise-os/skills` → **kopiert** | ADAPTABLE |
| **wshobson-agents** (181 Skills, eigener Marktplatz) | 181 | `../wshobson-agents/plugins/*/skills` | ADAPTABLE |

> Home zeigt 120, weil nicht alle Repo-Skills gleichzeitig aktiviert sind und First-Party-Skills dazukommen.

## Anthropic First-Party (CLAUDE_ONLY)
Dokument-/Medien-Skills, die an Claude-Runtime haengen: `pdf`, `docx`, `pptx`, `xlsx`, `canvas-design`, `artifacts-builder` / `web-artifacts-builder`, `artifact-design`, `artifact-diagramming`, `artifact-capabilities`, `dataviz`, `design`, `design-taste`, `skill-creator`, `mcp-builder`, `code-review`, `security-review`, `webapp-testing`, `slack-gif-creator`, `update-config`, `keybindings-help`, `plugin-doctor`, `claude-api`, `loop`, `run`, `init`.
→ **Nutzen fuer OpenCode:** Als Referenz/Checkliste lesbar; die automatische Ausfuehrung (PDF-Rendern, Artifact-Publish) fehlt in OpenCode.

## marketing-skillstack (49, ADAPTABLE) — der Business-Kern
Positionierung & Strategie: `product-marketing`, `marketing-plan`, `positioning` (in copywriting), `competitors`, `competitor-profiling`, `customer-research`, `content-strategy`, `marketing-council`, `marketing-ideas`, `marketing-psychology`, `marketing-loops`.
Copy & Content: `copywriting`, `copy-editing`, `content-research-writer`, `emails`, `cold-email`, `ad-creative`, `social`, `video`, `image`.
Konversion & Wachstum: `cro`, `ab-testing`, `signup`, `onboarding`, `paywalls`, `popups`, `pricing`, `offers`, `lead-magnets`, `referrals`, `churn-prevention`, `free-tools`.
SEO/AEO: `seo-audit`, `ai-seo`, `aso`, `programmatic-seo`, `site-architecture`, `schema`, `analytics`, `attribution`, `revops`.
Vertrieb & PR: `prospecting`, `sales-enablement`, `public-relations`, `influencer-marketing`, `community-marketing`, `co-marketing`, `directory-submissions`, `launch`, `sms`.
→ **Fuer Let'sDrink direkt relevant:** `product-marketing`, `pricing`, `cro`, `copywriting`, `seo-audit`, `ad-creative`, `emails`.

## awesome-skillstack (25, ADAPTABLE)
`artifacts-builder`, `brand-guidelines`, `changelog-generator`, `competitive-ads-extractor`, `connect`, `connect-apps`, `content-research-writer`, `developer-growth-analysis`, `domain-name-brainstormer`, `file-organizer`, `image-enhancer`, `internal-comms`, `invoice-organizer`, `langsmith-fetch`, `lead-research-assistant`, `mcp-builder`, `meeting-insights-analyzer`, `raffle-winner-picker`, `skill-share`, `slack-gif-creator`, `tailored-resume-generator`, `template-skill`, `twitter-algorithm-optimizer`, `video-downloader`, `webapp-testing`.

## design-skillstack (22) & threejs-skills (10) (ADAPTABLE)
3D/Animation/Web-Design: `gsap-scrolltrigger`, `motion-framer`, `react-three-fiber`, `threejs-webgl`, `babylonjs-engine`, `pixijs-2d`, `playcanvas-engine`, `aframe-webxr`, `lottie-animations`, `rive-interactive`, `spline-interactive`, `locomotive-scroll`, `scroll-reveal-libraries`, `animated-component-libraries`, `barba-js`, `blender-web-pipeline`, `substance-3d-texturing`, `lightweight-3d-effects`, `modern-web-design`, `web3d-integration-patterns`, plus die 10 threejs-Fundamentals (fundamentals, geometry, materials, textures, lighting, animation, shaders, loaders, interaction, postprocessing). Dazu Projekt-Skills: `apple-design`, `emil-design-eng`, `animate`, `animation-vocabulary`, `find-animation-opportunities`, `improve-animations`, `review-animations`, `prototype`, `pick-ui-library`, `fish-speech`, `n8n-templates`.

## ultra-enterprise-os (1, eigen — KOPIERT)
`capabilities/skills/ultra-enterprise-os/SKILL.md` + `references/org-chart.md`. Der Orchestrator-Skill, der fuer eine Aufgabe die passende virtuelle Organisation aus ULTRA-Teams zusammenstellt. **Direkt als Prompt-Vorlage fuer OpenCode adaptierbar.**

## Aktivierungsweg
- **Claude Code:** Skills werden aus `~/.claude/skills` bzw. Plugin-`skills/` automatisch nach Beschreibung geladen, oder per `/<skill-name>`.
- **OpenCode:** `SKILL.md`-Inhalt als System-/Task-Prompt einspeisen oder als eigene OpenCode-Regel/Command hinterlegen. Hilfsdateien (`references/`, `scripts/`) mitkopieren.

## NOT FOUND
- Keine Skills ausserhalb der genannten Quellen.
