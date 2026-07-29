# Zusatz-Plugins fuer das ULTRA / AI Command Center Setup

Zwei externe Tools, harmonisiert mit den bestehenden Werkzeugen.

## 1. Anthropic Cybersecurity Skills (Plugin, 817 Skills)
- Quelle: github.com/mukul975/Anthropic-Cybersecurity-Skills
- Zweck: Web-Security, Pentesting, DFIR, Threat-Intel, Cloud-Security, Malware-Analyse.
- Rolle im System: liefert die Substanz fuer das "AI Security Center" der Plattform
  und fuer den `ultra-security`-Agenten (defensive Reviews vor Auslieferung).
- Installation (Claude Code): Ordner nach `~/.claude/plugins/anthropic-cybersecurity-skills`
  kopieren (Windows: `%USERPROFILE%\.claude\plugins\`). Aktiv ab naechster Session.

## 2. Agent Reach (Python, Web-Reichweite)
- Quelle: github.com/Panniantong/agent-reach
- Zweck: gibt Agenten Internet-Zugriff: Web-Reader (Jina), YouTube/Bilibili-Transkripte,
  Twitter/Reddit/RSS, GitHub, semantische Suche (Exa).
- Rolle im System: Recherche-Backend fuer den ANALYST-Agenten des AI Command Center
  und fuer die ZEHNTAGE-Akquise (Firmen-Recherche).
- Installation: `uv venv agent-reach-venv && uv pip install -e ./agent-reach`
  danach `agent-reach doctor` (Kanaele pruefen) und `agent-reach setup` (Kanaele freischalten).

## Harmonie mit bestehenden Werkzeugen
| Aufgabe | Primaeres Tool | Ergaenzung |
|---|---|---|
| Security-Review vor Deploy | ultra-security | cybersecurity-skills |
| Tiefen-Recherche fuer Analyst-Agent | WebSearch/browser-use | Agent Reach |
| Web-Inhalte sauber einlesen | WebFetch | Agent Reach (Jina Reader) |
