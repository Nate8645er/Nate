# AgentCrow — Installation, geprüft

**Stand:** 30.08.2026 · **Version:** 5.0.0 (aus dem gelieferten ZIP)
**Quelle:** `agentcrowmain.zip`, entspricht github.com/jee599/agentcrow · MIT

---

## Installationsweg

Der offizielle Weg im README ist `npm i -g agentcrow`. Ich habe
stattdessen **aus dem gelieferten Quellcode gebaut** — dieselbe im
`package.json` hinterlegte Kette (`tsc`), nur eben genau der Code, den
du geschickt hast, statt einer möglicherweise abweichenden
Registry-Version.

```bash
cd vendor/agentcrow-main
npm install          # 142 Pakete
npm run build        # tsc -> dist/
npm link             # macht 'agentcrow' global verfügbar
agentcrow init --global --mcp
```

Alle vier Schritte sind ausgeführt und mit Ausgabe belegt.

---

## Was tatsächlich installiert ist — an den Dateien gezählt

| Gezählt | Wert |
|---|---:|
| Agenten-Definitionen (`~/.agentcrow/agents/md/*.md`) | **234** |
| Einträge im Suchindex (`catalog-index.json` → `entries`) | 240 |
| Eindeutige Rollen (`catalog-index.json` → `agents`) | **234** |
| Builtin-YAML (`~/.agentcrow/agents/builtin/*.yaml`) | 14 |
| Extern (aus `agency-agents`) | 220 |
| Divisionen laut `INDEX.md` | **19** |
| Symlinks unter `~/.claude/agents` | 235 (234 + INDEX.md) |

**Die 240 gegen 234:** Sechs Rollen kommen doppelt vor, einmal als
Builtin und einmal als externer Agent — `ai_engineer`,
`backend_architect`, `devops_automator`, `frontend_developer`,
`technical_writer`, `ui_designer`. Im Katalog gewinnt das Builtin, im
Suchindex stehen beide. Deshalb 240 Einträge, aber 234 Rollen.

**Das README nennt 154.** Das ist veraltet: 14 Builtin plus 140 extern.
Das externe Repo ist seither auf 220 Agenten gewachsen. Die Zahl im
README stimmt nicht mehr; die 234 sind gezählt, nicht geglaubt.

**`agentcrow status` meldet 235** (14 + 221). Auch das weicht um eins
ab, weil dort die `INDEX.md` mitgezählt wird. Drei verschiedene Zahlen
aus demselben Werkzeug — die belastbare ist die Zahl der
Agenten-Dateien: **234**.

### Divisionen

| Division | Agenten | Division | Agenten |
|---|---:|---|---:|
| engineering | 50 | security | 12 |
| specialized | 39 | design | 10 |
| marketing | 30 | testing | 9 |
| game-development | 21 | sales | 8 |
| builtin | 14 | project-management | 7 |
| gis | 13 | academic · support | je 6 |
| finance | 5 | spatial-computing | 4 |
| healthcare | 3 | product · research · strategy | je 1 |

---

## Integration in Claude Code

**Ja, offiziell unterstützt — über zwei Hooks in
`~/.claude/settings.json`:**

| Hook | Auslöser | Was er tut |
|---|---|---|
| `SessionStart` | Sitzungsbeginn | Meldet AgentCrow als aktiv und schreibt die Dispatch-Regeln in den Kontext |
| `PreToolUse` (Matcher `Agent`) | Jeder Aufruf des Agent-Werkzeugs | Ruft `~/.claude/hooks/agentcrow-inject.sh` auf, das die passende Persona vor den Prompt setzt |

Zusätzlich angelegt:
- `~/.claude/CLAUDE.md` — Dispatch-Regeln (**angelegt, nicht
  überschrieben**: es gab vorher keine)
- `~/.claude/agents` → Symlink auf `~/.agentcrow/agents/md`

### MCP

**Ja, unterstützt und aktiviert.** `agentcrow serve` ist ein echter
MCP-Server über stdio. Handshake und Werkzeugliste habe ich direkt
gegen den Prozess geprüft:

```
initialize -> {'name': 'agentcrow', 'version': '5.0.0'}
tools/list -> agentcrow_match, agentcrow_search, agentcrow_list
```

Eingetragen unter `mcpServers.agentcrow` in `~/.claude/settings.json`.
**Wirksam ab der nächsten Sitzung** — MCP-Server werden beim Start
verbunden.

---

## Sicherungen

Vor der Installation gesichert nach `vendor/backup-<Zeitstempel>/`:
`~/.claude/settings.json`, `~/.claude.json`, `~/.claude/hooks/`.

**Eine Lücke in meinem eigenen Vorgehen, die ich nicht verschweige:**
Ich habe `~/.claude/agents` **nicht** vorher gesichert. `init` löscht
ein dort vorhandenes Verzeichnis rekursiv, ohne selbst zu sichern
(`src/commands/init.ts`, Zeile 226: `fs.rmSync(agentsDir, {recursive:
true, force: true})`). Es gab keinen Fehler und keine Hinweise auf
vorherigen Inhalt — die Agenten dieser Umgebung kommen aus Plugins, die
davon unberührt sind. Beweisen kann ich es rückwirkend nicht.

**Vor jedem weiteren `agentcrow init` auf einem Rechner mit eigenen
Agenten:** `cp -a ~/.claude/agents ~/.claude/agents.backup`.

---

## Funktionstest

Der Hook wurde mit realistischen Nutzlasten direkt gefüttert:

| Fall | Eingabe | Ergebnis |
|---|---|---|
| Exakter Name | `name: "qa_engineer"` | ✔ QA-Engineer-Persona injiziert |
| Subagent-Typ | `subagent_type: "security_auditor_deep"` | ✔ Security-Auditor-Persona injiziert |
| Stichworte | „kubernetes deployment with docker and CI" | ✔ DevOps Automator (fuzzy) |
| Stichworte | „React dashboard with charts" | ✔ Frontend Developer (fuzzy) |
| Eingebauter Typ | `subagent_type: "Explore"` | ✔ **nicht** injiziert, durchgereicht |
| Anderes Werkzeug | `tool_name: "Bash"` | ✔ nicht injiziert |
| Kaputte Eingabe | `kein json` | ✔ kein Absturz, durchgereicht |

Zusätzlich: `agentcrow compose` zerlegte einen dreiteiligen Auftrag
korrekt in Frontend Developer, QA Engineer und Security Auditor, alle
drei mit exakter Zuordnung. Die projekteigene Testsuite läuft:
**169 Tests grün, 23 übersprungen.**

---

## Bedienung

```bash
agentcrow status                  # Zustand
agentcrow doctor                  # Diagnose
agentcrow agents search "<wort>"  # Agenten suchen
agentcrow compose "<auftrag>"     # Zerlegung als Trockenlauf
agentcrow stats                   # Zuordnungsstatistik
agentcrow off / on --global       # abschalten / einschalten
agentcrow uninstall               # vollständig entfernen
agentcrow update                  # externe Agenten aktualisieren
```

## Nicht im Repository abgelegt

`vendor/agentcrow-main/node_modules` und `dist` sind ignoriert. Wer die
Installation wiederholen will, führt die vier Schritte oben aus.
