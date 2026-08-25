# OPENCODE-INTEGRATION

Wie OpenCode auf deinem PC die hier exportierten Capabilities nutzt. **Ehrlichkeitsregel:** Nichts hier ist als "funktioniert" markiert, bevor du es in OpenCode getestet hast — deshalb steht ueberall `NOT_TESTED`, wo noch kein Test lief.

## Klassifizierung

- **DIRECT** — Datei direkt nutzbar (Skript, Prompt-Text, Workflow-JSON).
- **ADAPTABLE** — Inhalt portabel, aber Format/Frontmatter/Tool-Namen fuer OpenCode anpassen.
- **CLAUDE_ONLY** — haengt an Claude-Code-Runtime (Artifacts, Hooks, Doc-Sandbox); nicht direkt uebertragbar.
- **AUTH_REQUIRED** — braucht Login/API-Key/laufenden Dienst.
- **NOT_TESTED** — in OpenCode noch nicht verifiziert.

## Schritt 1 — Repo holen
```
git clone https://github.com/Nate8645er/Nate.git
cd Nate/ai-business
```
Alles hier plus die Geschwister-Ordner (`../wshobson-agents`, `../marketing-skillstack`, …) stehen dann lokal bereit.

## Schritt 2 — Was wie einbinden

### Agenten (ADAPTABLE, NOT_TESTED)
`capabilities/agents/` (12 ULTRA) und `capabilities/subagents/` (17 wshobson).
1. Rollen-Body (unter dem `---`-Frontmatter) = System-Prompt eines OpenCode-Agenten.
2. `tools:`-Zeile auf OpenCodes Tool-Set mappen (`All tools` → OpenCodes Standard).
3. `name`/`description` uebernehmen.

### Skills (ADAPTABLE, NOT_TESTED)
`SKILL.md`-Inhalt als Task-/System-Prompt oder OpenCode-Command hinterlegen. Hilfsdateien (`references/`, `scripts/`) mitnehmen. Grosse Packs (marketing/design/threejs/awesome) aus den Geschwister-Ordnern ziehen.

### Commands (ADAPTABLE, NOT_TESTED)
`capabilities/commands/` — Body als OpenCode-Command-Template; `$ARGUMENTS` durch OpenCodes Argument-Platzhalter ersetzen. `/ultra` braucht zusaetzlich den `ultra-enterprise-os`-Skilltext.

### Tools (DIRECT/ADAPTABLE)
- `tools/rat.py` — DIRECT, aber AUTH_REQUIRED (OmniRoute + `OPENROUTER_API_KEY`).
- `tools/omniroute-autostart.sh` — ADAPTABLE (Pfade anpassen).
- `../curbcut/*.py` — DIRECT.
- `../n8n-templates/*.json` — DIRECT in n8n.

### MCP-Server (AUTH_REQUIRED, NOT_TESTED)
OpenCode kann MCP-Server einbinden. Nimm aus `MCP.md` den **Servertyp**, richte ihn in OpenCode ein und **authentifiziere neu** (eigener OAuth/Key). Keine Anmeldung aus diesem Repo uebernehmbar — es sind keine drin.

### Hooks (groesstenteils CLAUDE_ONLY)
`capabilities/prompts/hooks-uebersicht.md` erklaert, welche Hooks es gibt. Die Claude-Code-Hook-Mechanik (PreToolUse/Stop/SessionStart) existiert in OpenCode so nicht — der **Zweck** ist adaptierbar (z.B. Security-Review als eigener OpenCode-Schritt), der Mechanismus nicht.

## Schritt 3 — Empfohlene Reihenfolge fuer Let'sDrink-Business
1. `ultra-orchestrator` + `/ultra-team` als Planer.
2. wshobson-SEO-Team (10) + `marketing-skillstack` (`product-marketing`, `pricing`, `cro`, `copywriting`).
3. `rat.py` fuer echte Zweitmeinungen bei Entscheidungen.
4. MCP (Shopify, Meta) erst nach Neu-Login in OpenCode.

## Was sicher NICHT ohne Weiteres laeuft
- Anthropic-Doc-Skills (pdf/docx/pptx/xlsx/canvas/artifacts) — CLAUDE_ONLY.
- security-guidance-Hooks als Live-Gate — CLAUDE_ONLY (Inhalt als Checkliste nutzbar).
- Claude-eingebaute Tools 1:1 — CLAUDE_ONLY.

## Teststatus
Alles: **NOT_TESTED** in OpenCode. Bitte nach dem ersten erfolgreichen Lauf hier den Status pro Block auf DIRECT/ADAPTABLE mit Datum hochsetzen.
