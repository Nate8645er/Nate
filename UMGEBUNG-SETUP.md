# Claude-Code-Umgebung: Einrichtung und Aenderungen (2026-07-29)

Vollstaendige Bestandsaufnahme und Optimierung der Umgebung. Alles hier
Beschriebene ist committet und damit in jeder neuen Session vorhanden.

## Bestandsaufnahme (vorher)

| Bereich | Zustand |
|---|---|
| Marketplace | Repo ist `nate-marketplace` mit 1 Plugin (ultra-enterprise-os) |
| Projekt `.claude/` | 10 ultra-Agenten, 3 Commands, 1 Skill, settings.json |
| Globale Skills | 29 Skills (ueber claude.ai synchronisiert) |
| Hooks | nur System-Hooks der Remote-Umgebung (nicht anfassen) |
| `.mcp.json` | nicht vorhanden |
| CLAUDE.md | fehlte |
| graphify | CLI nicht installiert, kein Plugin |

## Vorgenommene Aenderungen

1. **Graphify als Plugin im Marketplace** (`graphify-plugin/`):
   3 Skills (graphify, graphify-setup, graph-query), 3 Agenten
   (graph-builder, graph-analyst, graph-extractor), LICENSE.
   Registriert in `.claude-plugin/marketplace.json` (v1.1.0),
   aktiviert in `.claude/settings.json` unter `enabledPlugins`.
2. **SessionStart-Hook** in `.claude/settings.json`: installiert die
   graphify-CLI automatisch, falls sie fehlt
   (`command -v graphify || pip install -q graphifyy`), asynchron mit
   300 s Timeout — blockiert den Sessionstart nicht.
   Pipe-Test bestanden (Exit 0, CLI danach verfuegbar).
3. **CLAUDE.md** neu angelegt: Projektstruktur, harte Shop-Regeln
   (UWG, Live-Theme-Verbot, shared Backend), Graphify-Workflow.
4. **Wissensgraph des Repos gebaut** (`graphify-out/`):
   581 Knoten, 670 Kanten, 80 Communities. Funktionstest bestanden
   (`graphify explain "syncDeal"` liefert Quelldatei + Zeile).
   `graphify-out/cache/` ist gitignored (808 KB Cache bleibt lokal).
5. **Validierung aller Bausteine**: 31 Dateien (Skills, Agenten,
   Commands beider Plugins + Projekt) auf YAML-Frontmatter, Namen und
   Vollstaendigkeit geprueft — alle valide. settings.json und
   marketplace.json per jq syntaxgeprueft.

## Bewusst NICHT gemacht (mit Begruendung)

- **`.mcp.json` nicht angelegt**: Die installierte graphify-Version hat
  keinen MCP-Server-Befehl; alle MCP-Server dieser Umgebung kommen als
  claude.ai-Connectoren (Shopify, DSers, Gmail, ...). Ein Eintrag mit
  nicht existierendem Kommando waere ein Fehler, kein Feature.
- **Duplikate `.claude/agents|commands|skills` nicht geloescht**: Sie
  spiegeln das ultra-Plugin 1:1, sind aber in Remote-Containern die
  tatsaechlich ladende Quelle (installed_plugins ist dort leer).
  Loeschen wuerde die funktionierende Konfiguration zerstoeren.
  Dokumentiert in CLAUDE.md.
- **System-Hooks in `~/.claude/` nicht angefasst**: gehoeren der
  Remote-Infrastruktur (Git-Identity, Reply-Gate).

## Wichtig zu wissen

- Der Marketplace laedt von GitHub (Default-Branch). Das
  graphify-Plugin wird also erst nach dem Merge von PR #46 fuer
  `/plugin`-Installationen sichtbar. In dieser Session funktioniert
  graphify bereits direkt (CLI installiert, Graph gebaut).
- Aufgefrischt wird der Repo-Graph mit `graphify update .`
