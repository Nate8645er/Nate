# EXPORT-MANIFEST — Claude-Code-Capabilities fuer ai-business

**Erstellt:** 2026-08-25
**Quelle:** Claude-Code-Umgebung von Nate (Konto `Nate8645er`, Repo `Nate8645er/Nate`)
**Zweck:** Portable Sammlung aller technisch uebertragbaren Faehigkeiten, damit OpenCode sie spaeter nutzen oder adaptieren kann.
**Regel:** Nichts erfunden. Was nicht gefunden wurde, steht als `NOT FOUND`. Keine Secrets im Repo.

> **Wichtiger Hinweis zur Ablage:** Ein eigenstaendiges GitHub-Repo `ai-business` konnte aus dieser Sitzung **nicht** angelegt werden — die GitHub-App-Integration hat kein Recht, neue Repos zu erstellen (`403 Resource not accessible by integration`). Deshalb liegt der Export als Ordner `ai-business/` **im bestehenden Repo `Nate8645er/Nate`**. Vorteil: alle Marktplaetze liegen als Geschwister-Ordner direkt daneben — wer `Nate8645er/Nate` klont, hat den ganzen Werkzeugkasten. Wenn du ein separates Repo willst: leg auf GitHub ein leeres `ai-business` an, dann kann der Ordner dorthin verschoben werden.

---

## Zahlen auf einen Blick

| Kategorie | Gefunden (gesamt) | In diesem Export | Bemerkung |
|---|---:|---:|---|
| Skills (aktiviert, Home `~/.claude/skills`) | 120 | dokumentiert + Kerncopy | Obermenge aus allen Plugins + Anthropic-First-Party |
| Skills (Repo-Plugins, Quelle) | 287 | referenziert (Geschwister) | design 22, threejs 10, marketing 49, awesome 25, ultra 1, wshobson 181 (`-1` doppelt gezaehlt siehe unten) |
| Plugins (nate-marketplace) | 6 | referenziert + ultra kopiert | ultra-enterprise-os, design-skillstack, threejs-skills, security-guidance, marketing-skillstack, awesome-skillstack |
| Plugins (wshobson-Marktplatz, im Repo) | 91 | referenziert | eigener Marktplatz-Baum |
| Commands | 3 (ultra) + 105 (wshobson) | 3 kopiert, 105 referenziert | design-skillstack-Commands zusaetzlich |
| Agents (ULTRA, eigen) | 12 | **kopiert** | inkl. omni-team, ultra-prime |
| Agents (wshobson, Quelle) | 202 | referenziert | 17 aktiviert -> kopiert als Subagents |
| Agents (design-skillstack) | 27 | referenziert | Geschwister |
| Agents (installiert, Home) | 280 | dokumentiert | Obermenge |
| Subagents (aktiviert, kopiert) | 17 | **kopiert** | wshobson-* Business/SEO/Content-Set |
| MCP-Server (Sitzung beobachtet) | 10 | dokumentiert (ohne Secrets) | siehe MCP.md |
| Tools / Scripts (eigen) | rat.py, omniroute, curbcut(13) | 2 **kopiert**, curbcut referenziert | + n8n 328 Workflows, marketing-skillstack/tools |
| Repositories / Marktplaetze | 8 | dokumentiert | siehe REPOSITORIES.md |
| Hooks | 6 | dokumentiert | 4 Home (Claude-only) + security-guidance + SessionStart |

> Die Skill-Gesamtzahl der Repo-Plugins (287) und die Home-Zahl (120) ueberschneiden sich: `~/.claude/skills` ist die **aktivierte Auswahl**, die Repo-Plugins sind die **vollstaendige Quelle**. Es sind keine 407 verschiedenen Skills.

---

## Master-Tabelle (portierbare Kern-Ressourcen)

Legende Portierbarkeit: **DIRECT** = Datei direkt nutzbar · **ADAPTABLE** = fuer OpenCode anzupassen · **CLAUDE_ONLY** = nicht direkt uebertragbar · **AUTH_REQUIRED** = erst nach Login/Key · **NOT_TESTED** = noch nicht in OpenCode getestet.

| Name | Typ | Quelle | Lokal | Exportiert | OpenCode | Claude-only | Auth | Status |
|---|---|---|---|---|---|---|---|---|
| ultra-enterprise-os (Skill) | Skill | eigen (nate-marketplace) | ja | ja (kopiert) | ADAPTABLE | nein | nein | NOT_TESTED |
| ultra-orchestrator … ultra-prime (12) | Agents | eigen | ja | ja (kopiert) | ADAPTABLE | teils¹ | nein | NOT_TESTED |
| omni-team | Agent | eigen | ja | ja (kopiert) | ADAPTABLE | nein | AUTH_REQUIRED² | NOT_TESTED |
| wshobson-* (17 aktiviert) | Subagents | wshobson/agents | ja | ja (kopiert) | ADAPTABLE | nein | nein | NOT_TESTED |
| ultra / ultra-team / ultra-review | Commands | eigen | ja | ja (kopiert) | ADAPTABLE | ja³ | nein | NOT_TESTED |
| rat.py | Tool | eigen | ja | ja (kopiert) | DIRECT | nein | AUTH_REQUIRED² | NOT_TESTED |
| omniroute-autostart.sh | Tool/Hook | eigen | ja | ja (kopiert) | ADAPTABLE | nein | AUTH_REQUIRED² | NOT_TESTED |
| curbcut (13 .py) | Tools | eigen | ja | referenziert `../curbcut` | DIRECT | nein | nein | NOT_TESTED |
| design-skillstack (22 Skills, 27 Agents) | Plugin | Claude Design Skillstack | ja | referenziert `../design-skillstack` | ADAPTABLE | nein | nein | NOT_TESTED |
| threejs-skills (10) | Plugin | pinkforest | ja | referenziert `../threejs-skills` | ADAPTABLE | nein | nein | NOT_TESTED |
| marketing-skillstack (49) | Plugin | coreyhaines31 | ja | referenziert `../marketing-skillstack` | ADAPTABLE | nein | nein | NOT_TESTED |
| awesome-skillstack (25) | Plugin | Composio | ja | referenziert `../awesome-skillstack` | ADAPTABLE | nein | teils⁴ | NOT_TESTED |
| security-guidance | Plugin/Hooks | David Dworken (Anthropic) | ja | referenziert `../security-guidance` | CLAUDE_ONLY⁵ | ja | nein | NOT_TESTED |
| wshobson-agents (91 Plugins) | Marktplatz | wshobson/agents | ja | referenziert `../wshobson-agents` | ADAPTABLE | nein | nein | NOT_TESTED |
| n8n-templates (328) | Workflows | Zie619/n8n-workflows | ja | referenziert `../n8n-templates` | DIRECT | nein | teils⁴ | NOT_TESTED |
| Anthropic-First-Party-Skills (pdf, docx, pptx, xlsx, canvas-design, artifacts …) | Skills | Anthropic | ja (Home) | referenziert | CLAUDE_ONLY⁵ | ja | nein | NOT_TESTED |
| MCP-Server (10) | MCP | claude.ai/Umgebung | Konfig extern | dokumentiert | AUTH_REQUIRED | teils | ja | NOT_TESTED |

**Fussnoten**
1. Die ULTRA-Agenten sind Markdown-Instructions mit YAML-Frontmatter (`name`, `description`, `tools`). Der Rollentext ist portierbar; das Frontmatter-Format muss auf OpenCodes Agenten-Schema gemappt werden.
2. Braucht `OPENROUTER_API_KEY` als Umgebungsvariable und einen laufenden OmniRoute-Server (localhost:20128). Kein Key im Repo.
3. Claude-Code-Slash-Command-Format. Inhalt ist portierbar, der `/ultra`-Aufrufmechanismus ist Claude-Code-spezifisch.
4. Einzelne Skills/Workflows rufen externe Dienste (APIs) auf, die eigene Keys brauchen.
5. Haengt an Claude-Code-Hook-/Runtime-Mechanik (PreToolUse/Stop, Artifacts, Dateisandbox), die es in OpenCode so nicht gibt.

---

## Was bewusst NICHT kopiert wurde (und warum)

- **Grosse Fremd-Marktplaetze** (wshobson 1002 Dateien, marketing 410, design 274, n8n 333) — liegen bereits als Geschwister-Ordner im selben Repo. Kopieren wuerde nur duplizieren (Regel 12). Stattdessen referenziert.
- **Secrets jeglicher Art** — keine `.credentials.json`, keine API-Keys, keine Tokens, keine Session-Dateien. Vor dem Commit Secret-Scan durchgefuehrt (siehe unten).
- **`~/.claude/` Laufzeit-/Sitzungsdateien** (`.credentials.json`, `sessions/`, `projects/`, `shell-snapshots/`) — enthalten private Daten und/oder sind Claude-Code-Laufzeit, nicht portierbar.

## Secret-Scan
Vor Commit wurde `ai-business/` auf Key-Muster (`API_KEY`, `sk-`, `token`, `password`, `Bearer`, `PRIVATE KEY`) geprueft. Ergebnis: siehe Commit-Log. Die kopierten Tools (`rat.py`, `omniroute-autostart.sh`) beziehen ihren Key ausschliesslich aus Umgebungsvariablen.

## NOT FOUND
- Eigenstaendiges `ai-business`-GitHub-Repo — nicht anlegbar (App-Recht fehlt).
- Projekt-`.mcp.json` — existiert nicht; MCP wird auf der claude.ai-Umgebungsebene verwaltet.
- Home-`commands/` — Ordner existiert, ist aber leer.
