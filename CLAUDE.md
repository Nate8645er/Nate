# Nate – Projekt-Konfiguration

Dieses Repo ist Nates privater Claude-Code-Marketplace (`nate-marketplace`) mit zwei Plugins,
gespiegelt nach `.claude/` für automatisches Laden in allen Sessions.

## Installierte Plugins

1. **ULTRA AI ENTERPRISE OS** (`ultra-enterprise-os/`) – virtuelles Technologieunternehmen:
   `ultra-orchestrator` zerlegt große Aufgaben, Spezialteams (`ultra-fullstack`, `ultra-business`,
   `ultra-design`, `ultra-qa`, `ultra-security`, …) arbeiten parallel. Trigger: `/ultra`, ULTRA OS.
2. **Everything Claude Code** (`everything-claude-code/`) – battle-tested Workflows von
   affaan-m/everything-claude-code (MIT): TDD, Planung, Refactoring, E2E, Memory-Persistenz.

## Arbeitsregeln (aus everything-claude-code/rules/, Kurzfassung)

- **Planung zuerst:** Bei komplexen Features `/plan` bzw. den `planner`-Agent nutzen, dann implementieren.
- **TDD:** Neue Features über `/tdd` – Tests zuerst, dann minimale Implementierung (Ziel ≥80 % Coverage).
- **Security:** Keine Secrets committen; sicherheitsrelevante Änderungen durch `security-reviewer`
  oder `ultra-security` prüfen lassen. Details: `everything-claude-code/rules/security.md`.
- **Git:** Feature-Branches, klare Commit-Messages, kein Force-Push auf main.
  Details: `everything-claude-code/rules/git-workflow.md`.
- **Coding-Style & Patterns:** `everything-claude-code/rules/coding-style.md` und `rules/patterns.md`.
- Vollständige Regeln: `everything-claude-code/rules/*.md` (agents, coding-style, git-workflow,
  hooks, patterns, performance, security, testing).

## Hooks (aktiv via .claude/settings.json)

- **SessionStart:** lädt vorherigen Session-Kontext + Package-Manager-Erkennung
- **PreCompact:** sichert Zustand vor Kontext-Kompaktierung
- **SessionEnd:** persistiert Session-Zustand und extrahiert wiederverwendbare Patterns
- **PreToolUse (Edit|Write):** schlägt strategische Kompaktierung an logischen Grenzen vor

Alle Hook-Skripte liegen in `everything-claude-code/scripts/hooks/` (Node.js, cross-platform).

## Bewusst NICHT aktiviert

- ECC `/code-review`, `/verify` und das Skill `security-review`: kollidieren mit den
  gleichnamigen eingebauten Claude-Code-Skills – die eingebauten sind zu verwenden.
- ECC-Skill `clickhouse-io`: kein ClickHouse in diesem Projekt.
- Blockierende Hooks (tmux-Zwang für Dev-Server, .md-Schreibblockade): entfernt,
  da sie mit Remote-Sessions bzw. der Doku-Struktur (`shop/*.md`) kollidieren.
- `mcp-configs/mcp-servers.json`: nur Referenz – MCP-Server werden in dieser Umgebung
  bereits über claude.ai-Connectors verwaltet.

## Shopify-Projekt

Unter `shop/` liegen Setup-Doku und Marketing-Plan für den Shopify-Store katzenufos.com (MeowUFO).
