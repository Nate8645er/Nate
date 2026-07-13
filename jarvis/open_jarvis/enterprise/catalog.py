"""Zentraler Katalog aller Skills, Plugins und Tools des JARVIS Enterprise OS.

Dieser Katalog ist die einzige Datenquelle ("Single Source of Truth") fuer:

- JARVIS selbst (der Assistent besitzt ALLE Skills, Plugins und Tools),
- jeden der 1.000.000.000.000 virtuellen Mitarbeiter im Live-Ticker,
- jedes Mitarbeiter-Unternehmen samt Developer-Team,
- das HTML-Dashboard (``jarvis/dashboard/jarvis_live_ticker.html``).

Alle Funktionen sind deterministisch und benoetigen nur die Standardbibliothek.
"""

from __future__ import annotations

import json

SKILL_CATALOG: dict[str, list[str]] = {
    "Software-Engineering": [
        "Python", "TypeScript", "JavaScript", "Rust", "Go", "C++", "C#", "Java",
        "Kotlin", "Swift", "SQL", "Clean Code", "Code-Review", "Refactoring",
        "API-Design", "Systemarchitektur",
    ],
    "KI & Machine Learning": [
        "Prompt Engineering", "LLM-Orchestrierung", "RAG-Pipelines", "Fine-Tuning",
        "Agenten-Systeme", "Computer Vision", "Sprachverarbeitung (NLP)",
        "Sprachsynthese (TTS)", "Spracherkennung (STT)", "Reinforcement Learning",
        "Modell-Evaluierung", "Feature-Engineering", "MLOps", "Neuronale Netze",
        "Wissensgraphen", "Multimodale Modelle",
    ],
    "Data & Analytics": [
        "Datenanalyse", "Statistik", "Data Engineering", "ETL-Pipelines",
        "Data Warehousing", "Dashboarding", "Datenvisualisierung", "A/B-Testing",
        "Forecasting", "Echtzeit-Streaming", "Datenqualitaet", "Big-Data-Verarbeitung",
    ],
    "DevOps & Cloud": [
        "CI/CD-Pipelines", "Docker", "Kubernetes", "Terraform",
        "Infrastruktur als Code", "Monitoring & Observability", "Incident Response",
        "Cloud-Architektur (AWS)", "Cloud-Architektur (Azure)", "Cloud-Architektur (GCP)",
        "Serverless", "Edge Computing", "Kostenoptimierung", "Release-Management",
    ],
    "Security": [
        "Threat Modeling", "Penetration-Testing (defensiv)", "Secure Coding",
        "Kryptografie", "Identitaets- & Zugriffsmanagement", "Security-Audits",
        "Schwachstellen-Management", "Zero-Trust-Architektur", "Datenschutz (DSGVO)",
        "Secrets-Management", "Netzwerksicherheit", "Forensik",
    ],
    "Automatisierung & Robotik": [
        "Workflow-Automatisierung", "RPA (Robotic Process Automation)",
        "Desktop-Automatisierung", "Sprachsteuerung", "Smart-Home-Steuerung",
        "IoT-Integration", "Robotik-Steuerung", "Sensorik", "Prozess-Orchestrierung",
        "Scheduling & Timer", "Makro-Erstellung", "Selbstheilende Systeme",
    ],
    "Design & UX": [
        "UI-Design", "UX-Research", "Interaktionsdesign", "Design-Systeme",
        "Prototyping", "Motion Design", "Barrierefreiheit", "Typografie",
        "Farbtheorie", "Informationsarchitektur", "Usability-Testing", "3D-Design",
    ],
    "Produkt & Projekt": [
        "Produktstrategie", "Roadmap-Planung", "Agile Methoden (Scrum)", "Kanban",
        "Anforderungsanalyse", "Stakeholder-Management", "OKR-Planung",
        "Risikomanagement", "Priorisierung", "Sprint-Planung", "Retrospektiven",
        "Produkt-Discovery",
    ],
    "Business & Strategie": [
        "Geschaeftsstrategie", "Businessplan-Erstellung", "Marktanalyse",
        "Wettbewerbsanalyse", "Geschaeftsmodell-Design", "Pricing-Strategie",
        "Expansion & Skalierung", "Partnermanagement", "Fusionen & Uebernahmen",
        "Innovationsmanagement", "Unternehmensfuehrung", "Change-Management",
    ],
    "Finanzen": [
        "Finanzplanung", "Controlling", "Buchhaltung", "Budgetierung",
        "Investitionsanalyse", "Cashflow-Management", "Steueroptimierung",
        "Finanzberichte", "Kostenrechnung", "Payroll", "Foerdermittel", "Treasury",
    ],
    "Marketing & Vertrieb": [
        "SEO", "SEA & Performance-Marketing", "Content-Marketing",
        "Social-Media-Strategie", "E-Mail-Marketing", "Markenaufbau (Branding)",
        "Conversion-Optimierung", "Vertriebsstrategie", "Lead-Generierung",
        "CRM-Management", "Kampagnenplanung", "Marktforschung",
    ],
    "Kommunikation & Sprachen": [
        "Deutsch", "Englisch", "Franzoesisch", "Spanisch", "Italienisch",
        "Portugiesisch", "Niederlaendisch", "Polnisch", "Tuerkisch", "Arabisch",
        "Chinesisch", "Japanisch", "Koreanisch", "Russisch", "Hindi",
        "Simultan-Uebersetzung",
    ],
    "Recht & Compliance": [
        "Vertragsrecht", "Arbeitsrecht", "Datenschutzrecht", "Urheberrecht",
        "Compliance-Management", "Lizenzmanagement", "Regulatorik",
        "Richtlinien-Erstellung", "Audit-Vorbereitung", "Vertragspruefung",
    ],
    "HR & People": [
        "Recruiting", "Onboarding", "Talent-Entwicklung", "Performance-Management",
        "Gehaltsbandanalyse", "Mitarbeiterbindung", "Teamentwicklung",
        "Konfliktloesung", "Weiterbildungsplanung", "Employer Branding",
    ],
    "Support & Betrieb": [
        "Kundensupport", "Ticket-Management", "Wissensdatenbank-Pflege",
        "Eskalationsmanagement", "SLA-Ueberwachung", "Qualitaetssicherung",
        "Beschwerdemanagement", "24/7-Betrieb", "Service-Desk", "Feldservice",
    ],
    "Kreativ & Medien": [
        "Texterstellung", "Storytelling", "Videoproduktion", "Audioproduktion",
        "Podcast-Produktion", "Bildbearbeitung", "Musikkomposition", "Drehbuch",
        "Praesentationsdesign", "Live-Streaming", "Animation", "Fotografie",
    ],
}

PLUGIN_CATALOG: dict[str, list[str]] = {
    "System & Desktop": [
        "System-Monitor", "Prozess-Manager", "Datei-Explorer", "Zwischenablage-Manager",
        "Screenshot-Studio", "Fenster-Organizer", "Autostart-Manager", "Energie-Profile",
    ],
    "Produktivitaet": [
        "Kalender-Sync", "Aufgaben-Planer", "Notizen-Vault", "Pomodoro-Coach",
        "E-Mail-Assistent", "Meeting-Protokollant", "Dokumenten-Scanner", "PDF-Werkstatt",
    ],
    "KI & Assistenz": [
        "LLM-Router", "Prompt-Bibliothek", "Wissens-RAG", "Agenten-Fabrik",
        "Uebersetzer-Live", "Zusammenfasser", "Code-Copilot", "Bild-Generator",
    ],
    "Kommunikation": [
        "Chat-Hub", "Video-Konferenz", "Team-Broadcast", "SMS-Gateway",
        "Voicemail-Transkription", "Kontakt-Sync", "Kalender-Einladungen", "Status-Melder",
    ],
    "Medien & Unterhaltung": [
        "Spotify-Steuerung", "Radio-Streams", "Podcast-Player", "Video-Bibliothek",
        "Ambient-Sounds", "Musik-Erkennung", "Playlist-Kurator", "Kino-Modus",
    ],
    "Smart Home & IoT": [
        "Licht-Steuerung", "Thermostat-Regler", "Kamera-Wachdienst", "Tuer-Sensorik",
        "Energie-Messung", "Roboter-Staubsauger", "Bewaesserung", "Szenen-Automatik",
    ],
    "Entwicklung": [
        "Git-Kommandant", "CI-Wachhund", "Container-Deck", "API-Tester",
        "Datenbank-Konsole", "Log-Lupe", "Dependency-Radar", "Deploy-Pilot",
    ],
    "Business & Finanzen": [
        "Boersen-Ticker", "Portfolio-Tracker", "Rechnungs-Generator", "Ausgaben-Scanner",
        "CRM-Anbindung", "Umsatz-Dashboard", "Steuer-Helfer", "Budget-Waechter",
    ],
    "Sicherheit": [
        "Passwort-Tresor", "2FA-Verwalter", "Netzwerk-Scanner (defensiv)", "Update-Waechter",
        "Berechtigungs-Auditor", "Backup-Kommandant", "Phishing-Filter", "Datenschutz-Cockpit",
    ],
    "Wissen & Recherche": [
        "Web-Recherche", "Nachrichten-Digest", "Wikipedia-Blitz", "Wetter-Zentrale",
        "Boersen-News", "Wissenschafts-Feed", "Gesetzes-Suche", "Zitate-Archiv",
    ],
    "Reisen & Alltag": [
        "Navigations-Copilot", "Flug-Radar", "Bahn-Auskunft", "Hotel-Finder",
        "Rezept-Koch", "Einkaufslisten", "Fitness-Coach", "Schlaf-Analyse",
    ],
    "Enterprise": [
        "Enterprise-Live-Ticker", "Workforce-Monitor", "Org-Chart-Navigator", "KPI-Zentrale",
        "Schicht-Planer", "Compliance-Radar", "Flotten-Manager", "Lieferketten-Blick",
    ],
    "Daten & Berichte": [
        "Report-Fabrik", "Diagramm-Schmiede", "Tabellen-Import", "Daten-Bereiniger",
        "Export-Zentrale", "Metriken-Sammler", "Umfrage-Auswerter", "Prognose-Modul",
    ],
    "Sprache & Audio": [
        "Wake-Word-Tuner", "Stimmen-Studio", "Diktier-Modus", "Sprachbefehl-Makros",
        "Akzent-Trainer", "Vorlese-Dienst", "Audio-Mixer", "Geraeusch-Filter",
    ],
    "Bildung & Lernen": [
        "Lernkarten-Coach", "Sprachkurs-Begleiter", "Mathe-Loeser", "Code-Dojo",
        "Quiz-Meister", "Vokabel-Trainer", "Studienplaner", "Wissens-Checks",
    ],
    "Integrationen": [
        "GitHub-Bruecke", "Slack-Bruecke", "Notion-Sync", "Google-Drive-Anschluss",
        "Shopify-Cockpit", "Zapier-Verbinder", "Webhook-Zentrale", "REST-Adapter",
    ],
}

TOOL_CATALOG: dict[str, list[str]] = {
    "Code & Build": [
        "Code-Editor", "Debugger", "Profiler", "Linter", "Formatter", "Compiler-Suite",
        "Paket-Manager", "Build-Runner", "Test-Runner", "Coverage-Analyzer",
        "Benchmark-Suite", "Code-Suche",
    ],
    "Versionierung & Zusammenarbeit": [
        "Git-Client", "Diff-Viewer", "Merge-Assistent", "Branch-Visualisierer",
        "PR-Reviewer", "Issue-Tracker", "Wiki-Editor", "Pair-Programming-Board",
        "Release-Notizen-Generator", "Changelog-Builder", "Code-Owners-Manager",
        "Monorepo-Navigator",
    ],
    "Infrastruktur": [
        "Container-Runtime", "Cluster-Dashboard", "Load-Balancer-Konsole",
        "DNS-Verwalter", "Zertifikats-Manager", "VPN-Steuerung", "Firewall-Konsole",
        "Objekt-Speicher-Browser", "Queue-Inspektor", "Cache-Kontrolle",
        "Serverless-Deployer", "Infra-Drift-Detektor",
    ],
    "Daten & Datenbanken": [
        "SQL-Konsole", "NoSQL-Browser", "Schema-Designer", "Migrations-Runner",
        "Query-Optimierer", "Daten-Generator", "Backup-Restore-Tool", "Replikations-Monitor",
        "Vektor-Datenbank-Studio", "Zeitreihen-Explorer", "Graph-Datenbank-Navigator",
        "Daten-Anonymisierer",
    ],
    "KI-Werkzeuge": [
        "Prompt-Playground", "Modell-Vergleicher", "Token-Zaehler", "Embedding-Inspektor",
        "Agenten-Debugger", "Eval-Harness", "Datensatz-Kurator", "Halluzinations-Pruefer",
        "Kontext-Fenster-Optimierer", "Feinabstimmungs-Studio", "Inferenz-Profiler",
        "Guardrail-Tester",
    ],
    "Monitoring & Betrieb": [
        "Metriken-Dashboard", "Log-Aggregator", "Trace-Explorer", "Alarm-Manager",
        "Statusseiten-Publisher", "Fehler-Tracker", "Uptime-Prober", "Kapazitaets-Planer",
        "Kosten-Analyzer", "SLO-Rechner", "Incident-Timeline", "Runbook-Bibliothek",
    ],
    "Sicherheit & Compliance": [
        "Secrets-Scanner", "Abhaengigkeits-Pruefer", "SBOM-Generator", "Policy-Engine",
        "Zugriffs-Auditor", "Verschluesselungs-Toolkit", "Sicherheits-Header-Pruefer",
        "DSGVO-Checkliste", "Signatur-Verifizierer", "Schwachstellen-Datenbank",
        "Hardening-Assistent", "Audit-Log-Viewer",
    ],
    "Design & Frontend": [
        "Design-Canvas", "Komponenten-Galerie", "Farbpaletten-Generator", "Icon-Bibliothek",
        "Font-Manager", "Responsive-Tester", "Kontrast-Pruefer", "Animations-Editor",
        "SVG-Werkstatt", "Screenshot-Vergleicher", "Style-Guide-Builder", "Mockup-Renderer",
    ],
    "Dokumente & Office": [
        "Text-Editor", "Tabellen-Kalkulation", "Praesentations-Builder", "PDF-Editor",
        "Vorlagen-Bibliothek", "Serienbrief-Tool", "OCR-Erkennung", "E-Signatur",
        "Dokumenten-Vergleich", "Formular-Designer", "Archiv-Suche", "Versions-Historie",
    ],
    "Kommunikation & Planung": [
        "Kalender", "Aufgaben-Board", "Zeiterfassung", "Umfrage-Tool", "Abstimmungs-Planer",
        "Videoanruf-Studio", "Bildschirm-Recorder", "Team-Chat", "Ankuendigungs-Kanal",
        "Erinnerungs-Dienst", "Kontaktbuch", "Besprechungs-Timer",
    ],
    "Analyse & Berichte": [
        "Diagramm-Builder", "Pivot-Analyzer", "KPI-Karten", "Berichts-Planer",
        "Daten-Story-Editor", "Kohorten-Analyse", "Funnel-Visualisierer", "Heatmap-Renderer",
        "Geo-Karten", "Export-Manager", "Prognose-Rechner", "Anomalie-Detektor",
    ],
    "Automatisierung": [
        "Workflow-Designer", "Regel-Engine", "Cron-Planer", "Makro-Recorder",
        "Datei-Watcher", "Web-Scraper (regelkonform)", "Formular-Ausfueller",
        "Batch-Prozessor", "Trigger-Verwalter", "Pipeline-Visualisierer",
        "Roboter-Simulator", "Skript-Bibliothek",
    ],
    "Audio & Video": [
        "Audio-Editor", "Video-Schnitt", "Untertitel-Generator", "Transkriptions-Studio",
        "Rausch-Entferner", "Stimmen-Kloner (autorisiert)", "Streaming-Encoder",
        "Thumbnail-Designer", "Kapitel-Marker", "Ton-Mischpult", "Frame-Extraktor",
        "Wellenform-Viewer",
    ],
    "Wissen & Recherche": [
        "Websuche", "Quellen-Verwalter", "Zitations-Generator", "Faktencheck-Assistent",
        "Archiv-Crawler", "Themen-Radar", "Trend-Scanner", "Patent-Suche",
        "Literatur-Datenbank", "Lesezeichen-Vault", "Notiz-Verknuepfer", "Zusammenfassungs-Tool",
    ],
    "Finanz-Tools": [
        "Rechnungs-Editor", "Angebots-Generator", "Wechselkurs-Rechner", "Steuer-Rechner",
        "Portfolio-Analyzer", "Budget-Planer", "Zahlungs-Abgleich", "Mahnwesen-Assistent",
        "Kassenbuch", "Spesen-Erfassung", "Finanzkalender", "Abschreibungs-Rechner",
    ],
    "Alltag & Sonstiges": [
        "Wetter-Radar", "Routenplaner", "Uebersetzer", "Einheiten-Umrechner",
        "Zeitzone-Konverter", "QR-Code-Studio", "Passwort-Generator", "Countdown-Timer",
        "Notfall-Kontakte", "Paket-Verfolgung", "Rezept-Datenbank", "Geschenk-Planer",
    ],
}


# ---------------------------------------------------------------------------
# Neu installierte Faehigkeiten dieser Ausbaustufe. JARVIS UND jeder der
# 10**12 Mitarbeiter (samt Unternehmen + Developer-Team) besitzen sie ebenfalls:
# der Fable-5-Knopf (alle KI-Modelle), die Agent-Werkzeuge und die volle
# Shopify-Anbindung.
# Spiegeln: open_jarvis.agent.models (MODEL_REGISTRY) und
# open_jarvis.agent.shopify_client (CAPABILITY_MAP) — Konsistenz per Test geprueft.
# ---------------------------------------------------------------------------

#: Auswaehlbare KI-Motoren ("Fable-5-Knopf"). Reihenfolge = Anzeige-Reihenfolge.
AI_MODELS: list[str] = [
    "Fable 5",
    "Claude Opus 4.8",
    "Claude Sonnet 5",
    "Claude Haiku 4.5",
    "Groq (Llama)",
    "Lokal (keyless)",
]

#: Werkzeuge des JARVIS-Agenten (Befehle ausfuehren wie Claude Code).
AGENT_TOOLS: list[str] = [
    "Shop bauen",
    "Shop veroeffentlichen (Shopify live)",
    "Shop-Info",
    "Produkte suchen",
    "Bestellungen abrufen",
    "Rabattcode anlegen",
    "Websuche",
    "Webseite oeffnen",
    "App starten",
    "Datei schreiben",
    "Datei lesen",
    "Notiz",
    "Plugins auflisten",
    "Sprachsteuerung (Command Center)",
    "Agent-Bruecke (HUD -> Ausfuehrung)",
]

#: Shopify-Faehigkeiten (aus dem Shopify-MCP gespiegelt).
SHOPIFY_CAPABILITIES: list[str] = [
    "Shop-Infos",
    "Produkte suchen",
    "Produkt abrufen",
    "Produkt anlegen",
    "Produkt aendern",
    "Produktstatus in Masse",
    "Kollektionen suchen",
    "Kollektion abrufen",
    "Kollektion anlegen",
    "Kollektion aendern",
    "Produkt zu Kollektion",
    "Bestellungen auflisten",
    "Bestellung abrufen",
    "Kunden auflisten",
    "Lagerbestaende abrufen",
    "Lagerbestand setzen",
    "Rabattcode anlegen",
    "Analytics (ShopifyQL)",
    "GraphQL-Abfrage",
    "GraphQL-Mutation",
]


def all_models() -> list[str]:
    """Alle auswaehlbaren KI-Modelle (inkl. Fable 5)."""

    return list(AI_MODELS)


def all_agent_tools() -> list[str]:
    """Alle Agent-Werkzeuge."""

    return list(AGENT_TOOLS)


def all_shopify_capabilities() -> list[str]:
    """Alle Shopify-Faehigkeiten."""

    return list(SHOPIFY_CAPABILITIES)


def all_skills() -> list[str]:
    """Alle Skills als flache, deterministisch sortierte Liste."""

    return [skill for category in SKILL_CATALOG for skill in SKILL_CATALOG[category]]


def all_plugins() -> list[str]:
    """Alle Plugins als flache, deterministisch sortierte Liste."""

    return [plugin for category in PLUGIN_CATALOG for plugin in PLUGIN_CATALOG[category]]


def all_tools() -> list[str]:
    """Alle Tools als flache, deterministisch sortierte Liste."""

    return [tool for category in TOOL_CATALOG for tool in TOOL_CATALOG[category]]


def catalog_summary() -> dict[str, int]:
    """Anzahl der Skills, Plugins und Tools im Katalog."""

    return {
        "skills": len(all_skills()),
        "plugins": len(all_plugins()),
        "tools": len(all_tools()),
        "skill_categories": len(SKILL_CATALOG),
        "plugin_categories": len(PLUGIN_CATALOG),
        "tool_categories": len(TOOL_CATALOG),
    }


def capability_summary() -> dict[str, int]:
    """Erweiterte Zaehler inkl. der neu installierten Faehigkeiten.

    (Getrennt von ``catalog_summary()``, damit dessen stabile 6-Schluessel-Form
    erhalten bleibt.)
    """

    base = catalog_summary()
    base.update(
        {
            "models": len(AI_MODELS),
            "agent_tools": len(AGENT_TOOLS),
            "shopify_capabilities": len(SHOPIFY_CAPABILITIES),
        }
    )
    return base


def export_catalog() -> dict[str, object]:
    """Kompletter Katalog als JSON-faehiges Objekt (fuer Dashboard und Plugins)."""

    return {
        "summary": capability_summary(),
        "skills": SKILL_CATALOG,
        "plugins": PLUGIN_CATALOG,
        "tools": TOOL_CATALOG,
        "models": AI_MODELS,
        "agent_tools": AGENT_TOOLS,
        "shopify": SHOPIFY_CAPABILITIES,
    }


def export_catalog_json(indent: int | None = None) -> str:
    """Kompletter Katalog als JSON-String."""

    return json.dumps(export_catalog(), ensure_ascii=False, indent=indent)
