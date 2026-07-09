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
| `ultra-growth` | Growth/Revenue: Funnels, Conversion, Shopify-Ops, CRM, Creatives |
| `ultra-automation` | Automation/Integration: verbundene Dienste zu Workflows koppeln |
| `ultra-docs` | Dokumentation, Legal-Hinweise, Projekt-Management |

### Echte Werkzeug-Integrationen

`skills/ultra-enterprise-os/references/integrations.md` koppelt die
**tatsaechlich verbundenen** Dienste an die Rollen: **GitHub, Gmail,
Google Drive, Shopify, Higgsfield, Web**. Standardmodell ist **Fable 5**
(`claude-fable-5`); pro Teilaufgabe wird das passende Modell gewaehlt.
Ist ein Dienst nicht verbunden, liefert das System Entwurf + Anleitung
statt eines vorgetaeuschten Live-Ergebnisses.

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

## Harmonisierung: eine Quelle, drei Wege

Dasselbe Betriebssystem laeuft ueberall — aus **einer** Quelle
(`ultra-enterprise-os/`), ohne Drift:

| Umgebung | Weg | Was laeuft |
|---|---|---|
| Claude Code (Plugin) | `/plugin install ultra-enterprise-os@nate-marketplace` | Skill + 10 Agenten + 3 Commands |
| Claude Code (dieses Repo) | `.claude/`-Spiegel laedt automatisch in jeder Session | Skill + 10 Agenten + 3 Commands |
| Claude.ai (App/Web) | `scripts/build-claude-ai-skill.sh` → ZIP unter Settings → Capabilities → Skills hochladen | Skill (Rollen werden intern simuliert — gleiches Protokoll, gleiche Gates) |

Regeln gegen Drift:

- **Quelle der Wahrheit** ist immer `ultra-enterprise-os/`. Aenderungen
  nur dort machen.
- Danach `scripts/sync-mirror.sh` ausfuehren — synchronisiert den
  `.claude/`-Spiegel.
- `scripts/sync-mirror.sh --check` prueft jederzeit auf Abweichungen
  (Exit 1 bei Drift; ideal fuer CI oder als Pre-Commit-Check).
- Nach Skill-Aenderungen das Claude.ai-Paket neu bauen und erneut
  hochladen (`scripts/build-claude-ai-skill.sh`).

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
│   └── references/
│       ├── org-chart.md            # Generativer Rollenkatalog
│       └── integrations.md         # Echte Werkzeug→Rolle-Zuordnung
├── agents/                         # 12 spawnbare Team-Leads
├── commands/                       # /ultra, /ultra-team, /ultra-review
├── promo/index.html                # Pixel-Art-Promo (Reel-Stil, standalone)
└── app/index.html                  # ULTRA Command Deck (AI-Agent-Cockpit)
```

Der AI-Agent **Blin** (`app/index.html`) ist das Cockpit deines
Unternehmens: ein lebender Partikel-Orb, **Sprachsteuerung** (Mikrofon
antippen und mit Blin reden — er antwortet mit Stimme), eine Befehlszeile,
die komplette fraktale Organisation (12 Teams, jedes mit eigenem Dev-Team +
Gates), die verbundenen Werkzeuge (GitHub, Gmail, Drive, Shopify,
Higgsfield, Web), alle Fable-5-Modelle und ein Godmode-Denken-Schalter. Ein
Befehl zeigt live, welche Teams und Werkzeuge ULTRA dafuer instanziiert.

Sprache laeuft ueber die Web-Speech-API des Browsers (Safari/Chrome, mit
Mikrofon-Freigabe). Ehrlich: Blin nutzt Mikrofon und Stimme des Handys, kann
aber das Handy-Betriebssystem nicht selbst fernsteuern — das echte Ausfuehren
passiert ueber `/ultra` in Claude Code mit den verbundenen Werkzeugen.

Das Promo (`promo/index.html`) ist eine selbststaendige HTML-Animation im
Stil eines Instagram-Reels: 7 Szenen, Story-Fortschrittsleiste, Countdown,
Autopilot-Task-Grid — einfach im Browser oeffnen (tippen = naechste Szene).

## Tests

Manuelle Verifikation nach Installation:

1. `/ultra-team Baue eine Todo-App` → liefert Plan mit Rollen, DoD,
   Abhaengigkeiten und stoppt.
2. `/ultra-review` auf einem Diff mit hartkodiertem API-Key →
   Security-Gate meldet den Befund mit Datei:Zeile.
3. „nutze ultra-orchestrator um Projekt X zu planen" → Agent wird
   gespawnt und liefert den Ausfuehrungsplan im definierten Format.
