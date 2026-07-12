# JARVIS

Ein Claude-Code-Plugin, das Claude Code + Fable 5 in einen persoenlichen
**AI Chief of Staff** verwandelt: eine Mission-Control-Zentrale, die eine
virtuelle Organisation aus Agenten dirigiert, statt selbst jede Aufgabe
mechanisch abzuarbeiten.

## Was ist JARVIS

JARVIS behaelt Absicht, Entscheidungen, Qualitaets-Gates und die finale
Antwort — und delegiert alles Mechanische: Recherche an `scout`,
Umsetzung an `executor`, komplexe/riskante Faelle an `architect`,
Pruefungen an `verifier` (Tier 1, ueber `fable-baton`), bei Bedarf ganze
Abteilungen ueber die `ultra-*`-Agenten (Tier 2, ueber
`ultra-enterprise-os`) und — nur mit ausdruecklicher Zustimmung
("ultracode" oder explizite Bitte um einen Workflow) — massiven Fan-out
ueber das Workflow-Tool (Tier 3).

Jede Mission wird in einem Live-Ticker protokolliert und mit einem
kurzen, ehrlichen Abschlussbericht (Ergebnis, beteiligte Agenten,
Verifikation, Risiken) beendet.

## Voraussetzungen (empfohlen)

- Plugin **fable-baton** (fuer Tier-1-Agenten: scout, executor,
  architect, verifier)
- Plugin **ultra-enterprise-os** (fuer Tier-2-Abteilungsteams)

Fehlt eines der beiden, funktioniert JARVIS trotzdem — die jeweilige
Ebene faellt einfach weg, und JARVIS weist ehrlich darauf hin statt
Agenten zu simulieren.

## Nutzung

```
/jarvis <Auftrag>
```

Beispiele:

```
/jarvis Finde heraus, warum der Checkout auf Mobile haengt, und behebe es
/jarvis status
/jarvis ultracode: baue eine komplette Landingpage inkl. Tests und Deploy
```

Auf "status", "ueberblick" oder "dashboard" liefert JARVIS eine
Zusammenfassung der laufenden bzw. abgeschlossenen Mission.

## Live-Ticker

JARVIS schreibt fuer jede Mission JSON-Lines-Events nach
`.jarvis/ticker.jsonl` im Projekt-Root (Missionsstart, jeder
Agenten-Dispatch/-Abschluss, Missionsende). Das Protokoll ist
best-effort: Ticker-Fehler duerfen eine Mission nie zum Scheitern
bringen.

Ein visuelles Dashboard dazu liegt (separat gepflegt) unter
`jarvis/dashboard/mission-control.html`.

## Installation

Dieses Repo ist gleichzeitig ein Plugin-Marketplace. In Claude Code:

```
/plugin marketplace add Nate8645er/Nate
/plugin install jarvis@nate-marketplace
```

Fuer die volle Erfahrung zusaetzlich:

```
/plugin install fable-baton@fable-baton
/plugin install ultra-enterprise-os@nate-marketplace
```

Danach Claude Code neu starten oder die Sitzung fortsetzen — der Command
`/jarvis` ist dann verfuegbar.

## Struktur

```
jarvis/
├── .claude-plugin/plugin.json           # Plugin-Manifest
├── agents/oi-hands.md                   # Agent fuer lokale PC-Aufgaben
├── commands/jarvis.md                   # /jarvis Command
├── dashboard/mission-control.html       # Mission-Control-Dashboard (separat)
├── skills/open-interpreter/SKILL.md     # Skill: Open Interpreter installieren/nutzen
└── README.md
```

## Lokale PC-Aufgaben: Open Interpreter (optional)

Fuer Auftraege, die eine eigenstaendige Aktion auf dem lokalen Rechner
brauchen — also ausserhalb des aktuellen Projekts/Repos, z. B. den PC
selbst steuern oder lokale Programme starten — bringt JARVIS zwei
zusaetzliche Bausteine mit:

- **Skill `open-interpreter`**: greift, sobald Open Interpreter
  installiert/konfiguriert werden soll oder der Nutzer "Interpreter" /
  "Open Interpreter" erwaehnt. Erklaert Verfuegbarkeitspruefung,
  Installation, API-Key-Voraussetzung, Nutzung und die Sicherheitsregeln.
- **Agent `oi-hands`**: uebernimmt die eigentliche Ausfuehrung, wenn Open
  Interpreter bereits installiert ist und eine klar umrissene lokale
  Aufgabe delegiert wird. Prueft vorher Verfuegbarkeit und API-Key,
  fuehrt nur eindeutig harmlose Auftraege selbststaendig aus (`-y`) und
  gibt destruktive/risikoreiche Auftraege mit Begruendung an den
  Orchestrator zurueck statt sie auszufuehren.

Innerhalb eines Projekts bleiben die normalen Werkzeuge und
`fable-baton`-Agenten die erste Wahl — Open Interpreter kommt nur zum
Einsatz, wenn der Nutzer es ausdruecklich will oder die Aufgabe wirklich
lokale Automatisierung ausserhalb der Session ist.
