# PLUGINS

## Marktplatz
**`nate-marketplace`** — Quelle: GitHub `Nate8645er/Nate` (das ist dieses Repo selbst). Konfiguriert in `.claude/settings.json` → `extraKnownMarketplaces` und `.claude-plugin/marketplace.json`.

## Installierte + aktive Plugins (6, alle im Repo)

| Plugin | Version | Autor | Inhalt | Ort | OpenCode |
|---|---|---|---|---|---|
| **ultra-enterprise-os** | 1.0.0 | Nate (eigen) | 12 Agents, 3 Commands, 1 Skill | `../ultra-enterprise-os` | ADAPTABLE |
| **design-skillstack** | 1.0.0 | Claude Design Skillstack | 22 Skills, 27 Agents, Commands | `../design-skillstack` | ADAPTABLE |
| **threejs-skills** | 1.0.0 | pinkforest | 10 Skills | `../threejs-skills` | ADAPTABLE |
| **security-guidance** | 2.0.0 | David Dworken (Anthropic) | Hooks (Edit/Write/Stop/Commit-Review) | `../security-guidance` | CLAUDE_ONLY |
| **marketing-skillstack** | 1.0.0 | coreyhaines31 | 49 Skills, tools/ | `../marketing-skillstack` | ADAPTABLE |
| **awesome-skillstack** | 1.0.0 | Composio | 25 Skills | `../awesome-skillstack` | ADAPTABLE |

Aktivierung (`.claude/settings.json` → `enabledPlugins`): alle 6 auf `true`.

## Zusaetzlicher Plugin-Baum im Repo (nicht in nate-marketplace registriert)
**`wshobson-agents`** — eigenstaendiger Claude-Code-Marktplatz (`wshobson-agents/.claude-plugin/`), im Repo unter `../wshobson-agents`.
- 91 Sub-Plugins, 202 Agents, 181 Skills, 105 Commands (1002 Dateien).
- Installationsnachweis: `wshobson-agents/INSTALLIERT.md`.
- 17 Agenten davon sind in dieser Umgebung aktiviert (siehe SUBAGENTS.md), der Rest liegt als Katalog bereit.

## Status-Klassifizierung
- **installiert + aktiv:** alle 6 nate-marketplace-Plugins.
- **lokal vorhanden, teils aktiviert:** wshobson-agents (17 von 202 Agenten aktiv).
- **Claude-only:** security-guidance (Hook-Runtime), Anthropic-First-Party-Doc-Skills.
- **OpenCode-kompatibel (adaptierbar):** ultra-enterprise-os, design-skillstack, threejs-skills, marketing-skillstack, awesome-skillstack, wshobson-agents — als Instruction-Dateien.
- **benoetigt Auth:** keiner der Plugins selbst; einzelne Skills rufen externe APIs (eigene Keys).
- **nicht uebertragbar:** die Hook-Mechanik von security-guidance (PreToolUse/Stop), nicht der Inhalt.

## Installations-/Referenzweg
- **Claude Code:** `.claude/settings.json` verweist auf `nate-marketplace` (GitHub `Nate8645er/Nate`); `enabledPlugins` schaltet frei.
- **Neuinstallation woanders:** Repo klonen → `/plugin marketplace add Nate8645er/Nate` → `/plugin install <name>@nate-marketplace`.
- **OpenCode:** Plugins als Ordner mit `agents/`, `skills/`, `commands/` behandeln; Inhalte einzeln in OpenCodes Konfiguration uebernehmen (Frontmatter mappen).

## Upstream-Quellen
Siehe REPOSITORIES.md. Jeder Skillstack traegt `README.md`/`LICENSE`/`PACKAGING-NOTES.md` mit der genauen Herkunft.

## NOT FOUND
- Keine weiteren registrierten Marktplaetze ausser `nate-marketplace`.
- Kein Plugin, das ausserhalb des Repos installiert waere.
