# COMMANDS

Claude-Code-Slash-Commands sind Markdown-Dateien mit YAML-Frontmatter (`description`, `argument-hint`) und einem Prompt-Body, in den `$ARGUMENTS` eingesetzt wird. Der **Body ist portabel**; der `/name`-Aufrufmechanismus ist Claude-Code-spezifisch (in OpenCode als Custom-Command/Prompt-Template nachbauen).

## Eigene Commands (3, KOPIERT nach `capabilities/commands/`)

| Command | Zweck | Benoetigt | OpenCode |
|---|---|---|---|
| `/ultra <Aufgabe>` | Aktiviert ULTRA AI ENTERPRISE OS: Intake → Team-Komposition → Ausfuehrung → Cross-Review (QA+Security+Architektur) → konsolidierte Delivery in einem Durchgang | Skill `ultra-enterprise-os` | ADAPTABLE |
| `/ultra-team <Aufgabe>` | Stellt nur die optimale virtuelle Organisation zusammen (Plan, keine Ausfuehrung); nutzt `references/org-chart.md`, optional Agent `ultra-orchestrator` | Skill `ultra-enterprise-os`, Agent `ultra-orchestrator` | ADAPTABLE |
| `/ultra-review <...>` | Cross-Review-Durchlauf (Qualitaets-Gates) | Skill + Agents `ultra-qa`, `ultra-security` | ADAPTABLE |

Alle drei liegen doppelt vor (Quelle `../ultra-enterprise-os/commands/` und aktiv unter `.claude/commands/`) — kopiert wurde die Plugin-Quelle.

## Fremd-Commands (referenziert, nicht kopiert)
- **wshobson-agents:** 105 Commands unter `../wshobson-agents/plugins/*/commands/*.md` (Katalog).
- **design-skillstack:** Commands unter `../design-skillstack/commands/`.

## Aktivierungs-/Portierungsweg
- **Claude Code:** Datei in `.claude/commands/` (Projekt) oder `~/.claude/commands/` (global) → als `/dateiname` aufrufbar. `$ARGUMENTS` = alles nach dem Command.
- **OpenCode:** Body als Command-Template/Prompt hinterlegen; `$ARGUMENTS` durch OpenCodes Argument-Platzhalter ersetzen; referenzierte Skills/Agents mitliefern.

## NOT FOUND
- Home-`~/.claude/commands/` existiert, ist aber leer.
