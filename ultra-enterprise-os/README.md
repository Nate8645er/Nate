# ULTRA AI ENTERPRISE OS

Ein Claude-Code-Plugin, das jede Sitzung in ein **autonomes virtuelles
Technologieunternehmen** verwandelt: Aufgaben werden analysiert, in
Teilaufgaben zerlegt, an spezialisierte virtuelle Teams vergeben, parallel
bearbeitet, gegenseitig geprueft — und nur das konsolidierte,
produktionsreife Endergebnis wird ausgeliefert.

## Was ist drin

### 1 Meta-Skill (der Orchestrator)

| Skill | Zweck |
|---|---|
| `ultra-enterprise-os` | Betriebsprotokoll in 5 Phasen: Intake → Team-Komposition → Ausfuehrung → Cross-Review → konsolidierte Delivery. Enthaelt einen **generativen Rollenkatalog** (`references/org-chart.md`): aus einem Rollen-Template lassen sich unbegrenzt viele Spezialisierungen ableiten — instanziiert wird pro Aufgabe nur, was gebraucht wird. |

### 10 Agenten (echte, spawnbare Team-Leads)

| Agent | Deckt ab |
|---|---|
| `ultra-orchestrator` | Chief of Staff — Zerlegung, Ownership, Ausfuehrungsplan |
| `ultra-architect` | CTO — Architektur, Tech-Entscheidungen, Trade-offs |
| `ultra-fullstack` | Frontend, Backend, Mobile, APIs, Datenbanken |
| `ultra-devops` | Cloud, CI/CD, Deployment, Observability, Kosten |
| `ultra-security` | CISO — defensives Security-Review mit Veto-Recht |
| `ultra-qa` | Tests, Edge Cases, echte Verifikation |
| `ultra-data-ml` | Data Science, ML/DL, AI Research, LLM-Integration |
| `ultra-design` | UI/UX, Product Design, Zugaenglichkeit |
| `ultra-business` | Strategie, Finance, Marketing, Sales, SEO, Content, Branding |
| `ultra-docs` | Dokumentation, Legal-Hinweise, Projekt-Management |

### 3 Commands

| Command | Wirkung |
|---|---|
| `/ultra <Aufgabe>` | Volle Orchestrierung: Aufgabe Ende-zu-Ende auf hoechstem Niveau |
| `/ultra-team <Aufgabe>` | Nur Planung: optimale Organisation + Ausfuehrungsplan, dann Stopp |
| `/ultra-review [Fokus]` | Drei Qualitaets-Gates (QA, Security, Architektur) auf aktuellen Aenderungen |

## Installation

Dieses Repo ist gleichzeitig ein Plugin-Marketplace. In Claude Code:

```
/plugin marketplace add Nate8645er/Nate
/plugin install ultra-enterprise-os@nate-marketplace
```

Danach Claude Code neu starten oder die Sitzung fortsetzen — Skill,
Agenten und Commands sind dann verfuegbar (`/ultra`, `/ultra-team`,
`/ultra-review`).

## Konfiguration

Keine Pflicht-Konfiguration. Optional:

- **Agenten einzeln nutzen:** Jeder Agent laesst sich direkt ansprechen
  („nutze ultra-security auf diesem Diff").
- **Rollenkatalog erweitern:** Neue Spezialisierungen in
  `skills/ultra-enterprise-os/references/org-chart.md` nach dem
  Rollen-Template ergaenzen.
- **Eigene Commands:** Weitere `.md`-Dateien unter `commands/` anlegen.

## Beispiele

```
/ultra Baue mir eine Landingpage fuer MeowUfo mit Warteliste-Formular
/ultra-team Migriere den Shop auf ein neues Theme ohne Downtime
/ultra-review nur den Checkout-Code
```

Ohne Command wirkt die Skill automatisch bei jeder substanziellen
Aufgabe (sie ist als Auto-Trigger-Meta-Skill beschrieben).

## Ehrliche Grenzen (by design)

- **„Milliarden Agenten"** existieren nicht woertlich — der Rollenkatalog
  ist *generativ*: Er kann unbegrenzt viele Spezialisierungen definieren,
  aber pro Aufgabe werden nur die relevanten instanziiert. Das ist
  Absicht: mehr parallele Agenten = mehr Kosten und mehr
  Koordinationsfehler, nicht mehr Qualitaet.
- Echte parallele Subagenten kosten Zeit und Tokens; das Betriebsprotokoll
  simuliert Rollen standardmaessig intern und spawnt echte Agenten nur,
  wenn es die Aufgabe erfordert oder du es verlangst.
- Das Plugin haelt sich an eine Ehrlichkeits-Doktrin: keine erfundenen
  Zahlen, kein „produktionsreif" ohne echte Verifikation, Fehlschlaege
  werden berichtet statt kaschiert.

## Struktur

```
ultra-enterprise-os/
├── .claude-plugin/plugin.json      # Plugin-Manifest
├── skills/ultra-enterprise-os/
│   ├── SKILL.md                    # Betriebsprotokoll (5 Phasen)
│   └── references/org-chart.md     # Generativer Rollenkatalog
├── agents/                         # 10 spawnbare Team-Leads
└── commands/                       # /ultra, /ultra-team, /ultra-review
```

## Tests

Manuelle Verifikation nach Installation:

1. `/ultra-team Baue eine Todo-App` → liefert Plan mit Rollen, DoD,
   Abhaengigkeiten und stoppt.
2. `/ultra-review` auf einem Diff mit hartkodiertem API-Key →
   Security-Gate meldet den Befund mit Datei:Zeile.
3. „nutze ultra-orchestrator um Projekt X zu planen" → Agent wird
   gespawnt und liefert den Ausfuehrungsplan im definierten Format.
