# Nate — JARVIS Enterprise OS

> **Ein Repository, drei Bausteine: der lokale Open.Jarvis-Desktop-Assistent mit neuem
> Enterprise-Modul, das Claude-Code-Plugin ULTRA AI ENTERPRISE OS und ein
> Live-Dashboard für eine deterministisch simulierte Workforce von
> 2·10²⁴ + 10¹² virtuellen Mitarbeitern.**

---

## Überblick

Dieses Repo bündelt drei Komponenten:

1. **`jarvis/` — Open.Jarvis, erweitert um das Enterprise-Modul.**
   Der integrierte Open.Jarvis-Assistent (aus dem Original-Upload): ein Windows-first,
   local-first Desktop-Assistent mit Sprach- und Textbefehlen, Desktop-Automatisierung,
   Memory mit Privacy-Kontrollen und Cyber-Style-UI. Neu hinzugekommen ist das
   Enterprise-Modul `jarvis/open_jarvis/enterprise/` mit zentralem Fähigkeiten-Katalog,
   deterministischer Workforce-Engine und Live-Ticker — plus **128 echt installierte
   Plugins** unter `jarvis/plugins/`.

2. **`ultra-enterprise-os/` — Claude-Code-Plugin für Multi-Agent-Orchestrierung.**
   Ein bestehendes Claude-Code-Plugin, das jede Sitzung in ein virtuelles
   Technologieunternehmen verwandelt: 1 Meta-Skill (Orchestrator), 10 spawnbare
   Agenten-Team-Leads und 3 Commands (`/ultra`, `/ultra-team`, `/ultra-review`).
   Registriert im Plugin-Marketplace `.claude-plugin/marketplace.json` im Repo-Root
   (das Plugin selbst trägt sein Manifest in `ultra-enterprise-os/.claude-plugin/plugin.json`).

3. **Dashboard — `jarvis/dashboard/jarvis_live_ticker.html`.**
   Eine einzelne, komplett eigenständige HTML-Datei (kein CDN, keine externen
   Ressourcen, läuft offline im Browser) mit Kennzahlen, Live-Ticker,
   Mitarbeiter-Inspektor und Katalog-Browser.

---

## Was JARVIS jetzt kann

**Single Source of Truth** für alle Fähigkeiten ist der zentrale Katalog
[`jarvis/open_jarvis/enterprise/catalog.py`](jarvis/open_jarvis/enterprise/catalog.py):
**200 Skills**, **128 Plugins** und **192 Tools**, jeweils in **16 Kategorien**.
JARVIS selbst — und jeder einzelne virtuelle Mitarbeiter samt seinem Unternehmen und
Developer-Team — besitzt **alle** davon.

### 200 Skills

Jeder Skill ist Teil des zentralen Katalogs — JARVIS und jeder virtuelle Mitarbeiter beherrschen **alle 200**:

| Kategorie | Anzahl | Einträge |
|---|---:|---|
| Software-Engineering | 16 | Python, TypeScript, JavaScript, Rust, Go, C++, C#, Java, Kotlin, Swift, SQL, Clean Code, Code-Review, Refactoring, API-Design, Systemarchitektur |
| KI & Machine Learning | 16 | Prompt Engineering, LLM-Orchestrierung, RAG-Pipelines, Fine-Tuning, Agenten-Systeme, Computer Vision, Sprachverarbeitung (NLP), Sprachsynthese (TTS), Spracherkennung (STT), Reinforcement Learning, Modell-Evaluierung, Feature-Engineering, MLOps, Neuronale Netze, Wissensgraphen, Multimodale Modelle |
| Data & Analytics | 12 | Datenanalyse, Statistik, Data Engineering, ETL-Pipelines, Data Warehousing, Dashboarding, Datenvisualisierung, A/B-Testing, Forecasting, Echtzeit-Streaming, Datenqualitaet, Big-Data-Verarbeitung |
| DevOps & Cloud | 14 | CI/CD-Pipelines, Docker, Kubernetes, Terraform, Infrastruktur als Code, Monitoring & Observability, Incident Response, Cloud-Architektur (AWS), Cloud-Architektur (Azure), Cloud-Architektur (GCP), Serverless, Edge Computing, Kostenoptimierung, Release-Management |
| Security | 12 | Threat Modeling, Penetration-Testing (defensiv), Secure Coding, Kryptografie, Identitaets- & Zugriffsmanagement, Security-Audits, Schwachstellen-Management, Zero-Trust-Architektur, Datenschutz (DSGVO), Secrets-Management, Netzwerksicherheit, Forensik |
| Automatisierung & Robotik | 12 | Workflow-Automatisierung, RPA (Robotic Process Automation), Desktop-Automatisierung, Sprachsteuerung, Smart-Home-Steuerung, IoT-Integration, Robotik-Steuerung, Sensorik, Prozess-Orchestrierung, Scheduling & Timer, Makro-Erstellung, Selbstheilende Systeme |
| Design & UX | 12 | UI-Design, UX-Research, Interaktionsdesign, Design-Systeme, Prototyping, Motion Design, Barrierefreiheit, Typografie, Farbtheorie, Informationsarchitektur, Usability-Testing, 3D-Design |
| Produkt & Projekt | 12 | Produktstrategie, Roadmap-Planung, Agile Methoden (Scrum), Kanban, Anforderungsanalyse, Stakeholder-Management, OKR-Planung, Risikomanagement, Priorisierung, Sprint-Planung, Retrospektiven, Produkt-Discovery |
| Business & Strategie | 12 | Geschaeftsstrategie, Businessplan-Erstellung, Marktanalyse, Wettbewerbsanalyse, Geschaeftsmodell-Design, Pricing-Strategie, Expansion & Skalierung, Partnermanagement, Fusionen & Uebernahmen, Innovationsmanagement, Unternehmensfuehrung, Change-Management |
| Finanzen | 12 | Finanzplanung, Controlling, Buchhaltung, Budgetierung, Investitionsanalyse, Cashflow-Management, Steueroptimierung, Finanzberichte, Kostenrechnung, Payroll, Foerdermittel, Treasury |
| Marketing & Vertrieb | 12 | SEO, SEA & Performance-Marketing, Content-Marketing, Social-Media-Strategie, E-Mail-Marketing, Markenaufbau (Branding), Conversion-Optimierung, Vertriebsstrategie, Lead-Generierung, CRM-Management, Kampagnenplanung, Marktforschung |
| Kommunikation & Sprachen | 16 | Deutsch, Englisch, Franzoesisch, Spanisch, Italienisch, Portugiesisch, Niederlaendisch, Polnisch, Tuerkisch, Arabisch, Chinesisch, Japanisch, Koreanisch, Russisch, Hindi, Simultan-Uebersetzung |
| Recht & Compliance | 10 | Vertragsrecht, Arbeitsrecht, Datenschutzrecht, Urheberrecht, Compliance-Management, Lizenzmanagement, Regulatorik, Richtlinien-Erstellung, Audit-Vorbereitung, Vertragspruefung |
| HR & People | 10 | Recruiting, Onboarding, Talent-Entwicklung, Performance-Management, Gehaltsbandanalyse, Mitarbeiterbindung, Teamentwicklung, Konfliktloesung, Weiterbildungsplanung, Employer Branding |
| Support & Betrieb | 10 | Kundensupport, Ticket-Management, Wissensdatenbank-Pflege, Eskalationsmanagement, SLA-Ueberwachung, Qualitaetssicherung, Beschwerdemanagement, 24/7-Betrieb, Service-Desk, Feldservice |
| Kreativ & Medien | 12 | Texterstellung, Storytelling, Videoproduktion, Audioproduktion, Podcast-Produktion, Bildbearbeitung, Musikkomposition, Drehbuch, Praesentationsdesign, Live-Streaming, Animation, Fotografie |

*Summe: **200** in **16** Kategorien.*

### 128 Plugins (echt installiert unter `jarvis/plugins/`)

Alle 128 Plugins liegen als echte, ladbare Open.Jarvis-Plugins unter `jarvis/plugins/<plugin_id>/` (je `plugin.json` + `main.py`):

| Kategorie | Anzahl | Einträge |
|---|---:|---|
| System & Desktop | 8 | System-Monitor, Prozess-Manager, Datei-Explorer, Zwischenablage-Manager, Screenshot-Studio, Fenster-Organizer, Autostart-Manager, Energie-Profile |
| Produktivitaet | 8 | Kalender-Sync, Aufgaben-Planer, Notizen-Vault, Pomodoro-Coach, E-Mail-Assistent, Meeting-Protokollant, Dokumenten-Scanner, PDF-Werkstatt |
| KI & Assistenz | 8 | LLM-Router, Prompt-Bibliothek, Wissens-RAG, Agenten-Fabrik, Uebersetzer-Live, Zusammenfasser, Code-Copilot, Bild-Generator |
| Kommunikation | 8 | Chat-Hub, Video-Konferenz, Team-Broadcast, SMS-Gateway, Voicemail-Transkription, Kontakt-Sync, Kalender-Einladungen, Status-Melder |
| Medien & Unterhaltung | 8 | Spotify-Steuerung, Radio-Streams, Podcast-Player, Video-Bibliothek, Ambient-Sounds, Musik-Erkennung, Playlist-Kurator, Kino-Modus |
| Smart Home & IoT | 8 | Licht-Steuerung, Thermostat-Regler, Kamera-Wachdienst, Tuer-Sensorik, Energie-Messung, Roboter-Staubsauger, Bewaesserung, Szenen-Automatik |
| Entwicklung | 8 | Git-Kommandant, CI-Wachhund, Container-Deck, API-Tester, Datenbank-Konsole, Log-Lupe, Dependency-Radar, Deploy-Pilot |
| Business & Finanzen | 8 | Boersen-Ticker, Portfolio-Tracker, Rechnungs-Generator, Ausgaben-Scanner, CRM-Anbindung, Umsatz-Dashboard, Steuer-Helfer, Budget-Waechter |
| Sicherheit | 8 | Passwort-Tresor, 2FA-Verwalter, Netzwerk-Scanner (defensiv), Update-Waechter, Berechtigungs-Auditor, Backup-Kommandant, Phishing-Filter, Datenschutz-Cockpit |
| Wissen & Recherche | 8 | Web-Recherche, Nachrichten-Digest, Wikipedia-Blitz, Wetter-Zentrale, Boersen-News, Wissenschafts-Feed, Gesetzes-Suche, Zitate-Archiv |
| Reisen & Alltag | 8 | Navigations-Copilot, Flug-Radar, Bahn-Auskunft, Hotel-Finder, Rezept-Koch, Einkaufslisten, Fitness-Coach, Schlaf-Analyse |
| Enterprise | 8 | Enterprise-Live-Ticker, Workforce-Monitor, Org-Chart-Navigator, KPI-Zentrale, Schicht-Planer, Compliance-Radar, Flotten-Manager, Lieferketten-Blick |
| Daten & Berichte | 8 | Report-Fabrik, Diagramm-Schmiede, Tabellen-Import, Daten-Bereiniger, Export-Zentrale, Metriken-Sammler, Umfrage-Auswerter, Prognose-Modul |
| Sprache & Audio | 8 | Wake-Word-Tuner, Stimmen-Studio, Diktier-Modus, Sprachbefehl-Makros, Akzent-Trainer, Vorlese-Dienst, Audio-Mixer, Geraeusch-Filter |
| Bildung & Lernen | 8 | Lernkarten-Coach, Sprachkurs-Begleiter, Mathe-Loeser, Code-Dojo, Quiz-Meister, Vokabel-Trainer, Studienplaner, Wissens-Checks |
| Integrationen | 8 | GitHub-Bruecke, Slack-Bruecke, Notion-Sync, Google-Drive-Anschluss, Shopify-Cockpit, Zapier-Verbinder, Webhook-Zentrale, REST-Adapter |

*Summe: **128** in **16** Kategorien.*

### 192 Tools

Der Werkzeugkasten — JARVIS und jeder virtuelle Mitarbeiter nutzen **alle 192**:

| Kategorie | Anzahl | Einträge |
|---|---:|---|
| Code & Build | 12 | Code-Editor, Debugger, Profiler, Linter, Formatter, Compiler-Suite, Paket-Manager, Build-Runner, Test-Runner, Coverage-Analyzer, Benchmark-Suite, Code-Suche |
| Versionierung & Zusammenarbeit | 12 | Git-Client, Diff-Viewer, Merge-Assistent, Branch-Visualisierer, PR-Reviewer, Issue-Tracker, Wiki-Editor, Pair-Programming-Board, Release-Notizen-Generator, Changelog-Builder, Code-Owners-Manager, Monorepo-Navigator |
| Infrastruktur | 12 | Container-Runtime, Cluster-Dashboard, Load-Balancer-Konsole, DNS-Verwalter, Zertifikats-Manager, VPN-Steuerung, Firewall-Konsole, Objekt-Speicher-Browser, Queue-Inspektor, Cache-Kontrolle, Serverless-Deployer, Infra-Drift-Detektor |
| Daten & Datenbanken | 12 | SQL-Konsole, NoSQL-Browser, Schema-Designer, Migrations-Runner, Query-Optimierer, Daten-Generator, Backup-Restore-Tool, Replikations-Monitor, Vektor-Datenbank-Studio, Zeitreihen-Explorer, Graph-Datenbank-Navigator, Daten-Anonymisierer |
| KI-Werkzeuge | 12 | Prompt-Playground, Modell-Vergleicher, Token-Zaehler, Embedding-Inspektor, Agenten-Debugger, Eval-Harness, Datensatz-Kurator, Halluzinations-Pruefer, Kontext-Fenster-Optimierer, Feinabstimmungs-Studio, Inferenz-Profiler, Guardrail-Tester |
| Monitoring & Betrieb | 12 | Metriken-Dashboard, Log-Aggregator, Trace-Explorer, Alarm-Manager, Statusseiten-Publisher, Fehler-Tracker, Uptime-Prober, Kapazitaets-Planer, Kosten-Analyzer, SLO-Rechner, Incident-Timeline, Runbook-Bibliothek |
| Sicherheit & Compliance | 12 | Secrets-Scanner, Abhaengigkeits-Pruefer, SBOM-Generator, Policy-Engine, Zugriffs-Auditor, Verschluesselungs-Toolkit, Sicherheits-Header-Pruefer, DSGVO-Checkliste, Signatur-Verifizierer, Schwachstellen-Datenbank, Hardening-Assistent, Audit-Log-Viewer |
| Design & Frontend | 12 | Design-Canvas, Komponenten-Galerie, Farbpaletten-Generator, Icon-Bibliothek, Font-Manager, Responsive-Tester, Kontrast-Pruefer, Animations-Editor, SVG-Werkstatt, Screenshot-Vergleicher, Style-Guide-Builder, Mockup-Renderer |
| Dokumente & Office | 12 | Text-Editor, Tabellen-Kalkulation, Praesentations-Builder, PDF-Editor, Vorlagen-Bibliothek, Serienbrief-Tool, OCR-Erkennung, E-Signatur, Dokumenten-Vergleich, Formular-Designer, Archiv-Suche, Versions-Historie |
| Kommunikation & Planung | 12 | Kalender, Aufgaben-Board, Zeiterfassung, Umfrage-Tool, Abstimmungs-Planer, Videoanruf-Studio, Bildschirm-Recorder, Team-Chat, Ankuendigungs-Kanal, Erinnerungs-Dienst, Kontaktbuch, Besprechungs-Timer |
| Analyse & Berichte | 12 | Diagramm-Builder, Pivot-Analyzer, KPI-Karten, Berichts-Planer, Daten-Story-Editor, Kohorten-Analyse, Funnel-Visualisierer, Heatmap-Renderer, Geo-Karten, Export-Manager, Prognose-Rechner, Anomalie-Detektor |
| Automatisierung | 12 | Workflow-Designer, Regel-Engine, Cron-Planer, Makro-Recorder, Datei-Watcher, Web-Scraper (regelkonform), Formular-Ausfueller, Batch-Prozessor, Trigger-Verwalter, Pipeline-Visualisierer, Roboter-Simulator, Skript-Bibliothek |
| Audio & Video | 12 | Audio-Editor, Video-Schnitt, Untertitel-Generator, Transkriptions-Studio, Rausch-Entferner, Stimmen-Kloner (autorisiert), Streaming-Encoder, Thumbnail-Designer, Kapitel-Marker, Ton-Mischpult, Frame-Extraktor, Wellenform-Viewer |
| Wissen & Recherche | 12 | Websuche, Quellen-Verwalter, Zitations-Generator, Faktencheck-Assistent, Archiv-Crawler, Themen-Radar, Trend-Scanner, Patent-Suche, Literatur-Datenbank, Lesezeichen-Vault, Notiz-Verknuepfer, Zusammenfassungs-Tool |
| Finanz-Tools | 12 | Rechnungs-Editor, Angebots-Generator, Wechselkurs-Rechner, Steuer-Rechner, Portfolio-Analyzer, Budget-Planer, Zahlungs-Abgleich, Mahnwesen-Assistent, Kassenbuch, Spesen-Erfassung, Finanzkalender, Abschreibungs-Rechner |
| Alltag & Sonstiges | 12 | Wetter-Radar, Routenplaner, Uebersetzer, Einheiten-Umrechner, Zeitzone-Konverter, QR-Code-Studio, Passwort-Generator, Countdown-Timer, Notfall-Kontakte, Paket-Verfolgung, Rezept-Datenbank, Geschenk-Planer |

*Summe: **192** in **16** Kategorien.*

---

## Live-Ticker

Das Herzstück des Enterprise-Moduls ist eine **deterministisch simulierte
Workforce**:

| Kennzahl | Wert |
|---|---|
| Mitarbeiter direkt im JARVIS Live-Ticker | **1.000.000.000.000** (10¹², „1000 Milliarden") |
| Unternehmen (eines je Mitarbeiter) | 1.000.000.000.000 |
| Mitarbeiter je Unternehmen | 1.000.000.000.000 (10¹²) |
| Developer-Team je Unternehmen | 1.000.000.000.000 (10¹²) |
| Entwickler gesamt (alle Unternehmen) | 10²⁴ = 1.000.000.000.000.000.000.000.000 |
| **Gesamt-Workforce** | **2·10²⁴ + 10¹² = 2.000.000.000.001.000.000.000.000** |
| Skills / Plugins / Tools im Katalog | 200 / 128 / 192 (je 16 Kategorien) |

Jeder der 10¹² direkten Mitarbeiter führt ein **eigenes Unternehmen** mit
1.000.000.000.000 Mitarbeitern **und** einem zusätzlichen
1.000.000.000.000-köpfigen Developer-Team. Name, Rolle, Abteilung,
Spezialisierung und Firmenname jedes Mitarbeiters werden **deterministisch**
aus seiner ID abgeleitet (SplitMix64-Hash) — **jede Mitarbeiter-ID von 1 bis
10¹² ist jederzeit inspizierbar** und liefert in Python und im
JavaScript-Dashboard exakt denselben Datensatz.

> **Ehrlicher Hinweis:** Es handelt sich um eine **Simulation** — eine virtuelle
> Organisation, deren Mitarbeiter on-the-fly deterministisch **berechnet statt
> gespeichert** werden. Es laufen keine 10¹² Prozesse und es existiert keine
> Datenbank mit 2·10²⁴ Einträgen; genau deshalb funktionieren diese Größen
> verlustfrei und exakt. Details: [`jarvis/docs/ENTERPRISE_LIVE_TICKER.md`](jarvis/docs/ENTERPRISE_LIVE_TICKER.md).

---

## Schnellstart

### Dashboard (empfohlen)

Die Datei [`jarvis/dashboard/jarvis_live_ticker.html`](jarvis/dashboard/jarvis_live_ticker.html)
einfach im Browser öffnen — keine Installation, kein Server, kein Internet nötig:

```bash
# Linux
xdg-open jarvis/dashboard/jarvis_live_ticker.html
# macOS
open jarvis/dashboard/jarvis_live_ticker.html
# Windows
start jarvis\dashboard\jarvis_live_ticker.html
```

### Terminal-Live-Ticker

```bash
cd jarvis
python3 -m open_jarvis.enterprise --ticks 20
```

Ohne `--ticks` (bzw. mit `--ticks 0`) läuft der Ticker endlos bis `Strg+C`.
Weitere Optionen: `--interval` (Sekunden zwischen Events), `--seed`
(reproduzierbare Event-Sequenz).

### Kennzahlen als JSON

```bash
cd jarvis
python3 -m open_jarvis.enterprise --summary
```

### Desktop-App (Open.Jarvis-Assistent)

```bash
cd jarvis
pip install -r requirements.txt
python jarvis.py
```

> **Hinweis:** Open.Jarvis ist **Windows-first** (Windows 10/11). Sprachein-/-ausgabe
> und die Desktop-UI benötigen die Abhängigkeiten aus `requirements.txt`; ohne
> API-Keys läuft die App im lokalen „keyless degraded mode". Details:
> [`jarvis/README.md`](jarvis/README.md).

### JARVIS-Agent — Befehle wirklich ausführen (wie Claude Code)

JARVIS kann Befehle entgegennehmen und **ausführen** — Aufgabe planen, Werkzeuge
benutzen, Ergebnis liefern. Mit **Modell-Auswahl inkl. Fable 5** (Standard).

```bash
cd jarvis
python3 -m open_jarvis.agent --list-models                 # KI-Motoren (Fable 5, Opus, …)
python3 -m open_jarvis.agent "baue mir einen Shop für Kaffee namens Bergbohne"
python3 -m open_jarvis.agent --execute "baue einen Shop für Sneaker"   # echt schreiben
python3 -m open_jarvis.agent --model fable-5 "suche nach günstigen Flügen"
```

Werkzeuge u. a.: `shop_bauen` (kompletter, verkaufsfertiger Shop-Bauplan mit
Produkten & CHF-Preisen), `web_suche`, `webseite`, `app_starten`, `datei_schreiben`,
`notiz`, `plugins`. Ohne `--execute` läuft eine gefahrlose Vorschau.

> **Ehrlich:** Für Planung mit **Fable 5 / Claude** brauchst du einen Anthropic-Schlüssel
> in `ANTHROPIC_API_KEY`. Ohne Schlüssel plant der **lokale, kostenlose** Motor —
> JARVIS bleibt immer bedienbar. `shop_bauen` erzeugt einen **Bauplan** (kein live
> erstellter Shopify-Shop). Details: [`jarvis/docs/JARVIS_AGENT.md`](jarvis/docs/JARVIS_AGENT.md).

### Tests

```bash
cd jarvis
python3 -m pytest tests/test_enterprise_*.py tests/test_agent_*.py
```

Deckt Workforce-Engine, Live-Ticker, alle 128 Plugins und den JARVIS-Agenten ab.

---

## Struktur des Repos

```text
Nate/
├── README.md                        ← diese Datei
├── .claude-plugin/
│   └── marketplace.json             ← Plugin-Marketplace (registriert ultra-enterprise-os)
├── jarvis/                          ← Open.Jarvis-Assistent + Enterprise-Modul
│   ├── jarvis.py                    ← Einstiegspunkt der Desktop-App
│   ├── requirements.txt
│   ├── open_jarvis/
│   │   ├── enterprise/              ← NEU: Enterprise-Modul
│   │   │   ├── catalog.py           ← Single Source of Truth (200 Skills / 128 Plugins / 192 Tools)
│   │   │   ├── workforce.py         ← deterministische Mitarbeiter-Ableitung (SplitMix64)
│   │   │   ├── live_ticker.py       ← Event-Engine (10 Event-Typen)
│   │   │   └── __main__.py          ← Terminal-Ticker: python3 -m open_jarvis.enterprise
│   │   ├── agent/                   ← NEU: JARVIS-Agent (Befehle ausführen, wie Claude Code)
│   │   │   ├── models.py            ← Modell-Registry (Fable 5, Opus, Sonnet, Haiku, Groq, lokal)
│   │   │   ├── claude_provider.py   ← Anthropic-API-Client (Fable 5 / Claude)
│   │   │   ├── planner.py           ← lokaler + Claude-Planer (mit Fallback)
│   │   │   ├── tools.py             ← sichere Werkzeug-Registry
│   │   │   ├── shop_builder.py      ← Shop-Bauplan-Generator
│   │   │   └── __main__.py          ← CLI: python3 -m open_jarvis.agent "<befehl>"
│   │   └── …                        ← bestehender Assistent (app, audio, memory, plugins, …)
│   ├── plugins/                     ← 128 Katalog-Plugins + JARVIS-Agent-Plugin
│   │   └── <plugin_id>/
│   │       ├── plugin.json          ← Manifest
│   │       └── main.py              ← Entrypoint (nur Standardbibliothek)
│   ├── dashboard/
│   │   └── jarvis_live_ticker.html  ← Live-Dashboard (eigenständig, offline)
│   ├── docs/
│   │   ├── ENTERPRISE_LIVE_TICKER.md ← ausführliche Anleitung zum Enterprise-Modul
│   │   ├── JARVIS_AGENT.md          ← Anleitung zum JARVIS-Agenten (Fable 5, Werkzeuge)
│   │   └── …                        ← bestehende Open.Jarvis-Doku
│   └── tests/
│       ├── test_enterprise_workforce.py
│       ├── test_enterprise_live_ticker.py
│       ├── test_enterprise_plugins.py
│       └── test_agent_*.py
└── ultra-enterprise-os/             ← Claude-Code-Plugin (Multi-Agent-Orchestrierung)
    ├── .claude-plugin/plugin.json   ← Plugin-Manifest
    ├── skills/ultra-enterprise-os/  ← Meta-Skill (Orchestrator)
    ├── agents/                      ← 10 spezialisierte Team-Lead-Agenten
    ├── commands/                    ← /ultra, /ultra-team, /ultra-review
    └── README.md
```

---

## Weiterführende Dokumentation

- **Enterprise Live-Ticker im Detail:** [`jarvis/docs/ENTERPRISE_LIVE_TICKER.md`](jarvis/docs/ENTERPRISE_LIVE_TICKER.md)
  — Architektur, deterministisches Prinzip, CLI-Referenz, Dashboard-Funktionen,
  Event-Typen, Plugin-Katalog, FAQ.
- **JARVIS-Agent (Befehle ausführen, Fable 5):** [`jarvis/docs/JARVIS_AGENT.md`](jarvis/docs/JARVIS_AGENT.md)
  — Modell-Auswahl inkl. Fable 5, Werkzeuge, Shop-Bauplan, Sicherheit, Python-API.
- **Open.Jarvis-Assistent:** [`jarvis/README.md`](jarvis/README.md) und [`jarvis/docs/`](jarvis/docs/)
- **Plugin-Verzeichnis:** [`jarvis/plugins/README.md`](jarvis/plugins/README.md)
- **ULTRA AI ENTERPRISE OS:** [`ultra-enterprise-os/README.md`](ultra-enterprise-os/README.md)
