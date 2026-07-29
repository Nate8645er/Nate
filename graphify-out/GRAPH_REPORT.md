# Graph Report - Nate  (2026-07-29)

## Corpus Check
- 91 files · ~282,135 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 581 nodes · 670 edges · 80 communities (76 shown, 4 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 11 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `39a69ea7`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- What You Must Do When Invoked
- tools.py
- HANDOFF: Let'sDrink — Stand 28. Juli 2026
- build_scene.py
- LAUNCH-KIT: Zwei Produkte, Wandersaison 2026
- SHOP-AUFBAU KOMPLETT
- server.py
- build_fun.py
- Flow A: Nach dem Brunnenkauf (5 E-Mails)
- Status-Update, 28. Juli 2026 (Claude Code)
- HUNDE-TRINKFLASCHE, KOMPLETTPAKET
- PRODUKTENTSCHEID: Rasierer-und-Klingen für MeowUfo
- JAVIER MOBILE
- build_b.py
- build_ad.py
- build_ad3.py
- TEIL 1: META (Facebook und Instagram)
- build_ad2.py
- ULTRA AI ENTERPRISE OS
- listing-und-content.md
- ULTRA AI ENTERPRISE OS — Rollenkatalog (generativ)
- manifest.json
- build_photoad.py
- PRODUKTDATEN FINAL, KORRIGIERTE TEXTE
- WERBEVIDEO-PAKET: LET'SDRINK
- ULTRA AI ENTERPRISE OS — Rollenkatalog (generativ)
- ULTRA AI ENTERPRISE OS — Betriebsprotokoll
- graphify reference: extra exports and benchmark
- APP-EMPFEHLUNGEN
- RECHTSTEXTE
- TEXTPAKET LET'SDRINK
- ULTRA AI ENTERPRISE OS — Betriebsprotokoll
- build_product_images.py
- BRANDING LET'SDRINK
- graphify-setup
- GOOGLE ADS
- SHOP-TEXTE TRINKFLASCHE
- Nate — Arbeitsregeln fuer dieses Repo
- graphify reference: query, path, explain
- E-MAIL-FLOWS
- SEITENTEXTE
- graph-query
- graphify reference: add a URL and watch a folder
- graphify reference: commit hook and native CLAUDE.md integration
- graphify reference: incremental update and cluster-only
- graphify reference: GitHub clone and cross-repo merge
- graphify reference: transcribe video and audio
- extraction-spec.md
- skripte/README.md

## God Nodes (most connected - your core abstractions)
1. `Status-Update, 28. Juli 2026 (Claude Code)` - 16 edges
2. `JAVIER MOBILE` - 13 edges
3. `build()` - 12 edges
4. `build()` - 12 edges
5. `What You Must Do When Invoked` - 12 edges
6. `build()` - 11 edges
7. `build()` - 11 edges
8. `PRODUKTENTSCHEID: Rasierer-und-Klingen für MeowUfo` - 11 edges
9. `/graphify` - 10 edges
10. `HANDOFF: Let'sDrink — Stand 28. Juli 2026` - 10 edges

## Surprising Connections (you probably didn't know these)
- `build()` --calls--> `bubble()`  [EXTRACTED]
  letsdrink/skripte/build_colors.py → letsdrink/skripte/build_fun.py
- `build()` --calls--> `dashed_arc()`  [EXTRACTED]
  letsdrink/skripte/build_colors.py → letsdrink/skripte/build_fun.py
- `build()` --calls--> `droplet()`  [EXTRACTED]
  letsdrink/skripte/build_colors.py → letsdrink/skripte/build_fun.py
- `build()` --calls--> `F()`  [EXTRACTED]
  letsdrink/skripte/build_colors.py → letsdrink/skripte/build_fun.py
- `build()` --calls--> `fit()`  [EXTRACTED]
  letsdrink/skripte/build_colors.py → letsdrink/skripte/build_fun.py

## Import Cycles
- None detected.

## Communities (80 total, 4 thin omitted)

### Community 0 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 1 - "tools.py"
Cohesion: 0.13
Nodes (18): is_configured(), publish_post(), add_event(), _ensure_dirs(), list_contacts(), _load_contacts(), _load_custom_apps(), _load_todos() (+10 more)

### Community 2 - "HANDOFF: Let'sDrink — Stand 28. Juli 2026"
Cohesion: 0.09
Nodes (22): 1. Das Vorhaben, 2. Shopify-Zustand (live geprüft), 3. Kalkulation, 4. Verbindliche inhaltliche Regeln, 5. Offen, nach Priorität, 6. Fragen an den Lieferanten, noch offen, 7. Was in diesem Paket liegt, 8. Erster Schritt in Claude Code (+14 more)

### Community 3 - "build_scene.py"
Cohesion: 0.15
Nodes (21): build(), cat(), dog(), _ell(), F(), fit(), fitblock(), fitf() (+13 more)

### Community 4 - "LAUNCH-KIT: Zwei Produkte, Wandersaison 2026"
Cohesion: 0.10
Nodes (20): 0. Beirat-Beschluss, 1. Sourcing, 2. Kalkulation, 3. Shop aufsetzen, 4. Produktseiten (fertig zum Einsetzen), 5. Content: 30 Hooks für den ersten Drehtag, 6. Messpunkte und Kill-Kriterien, 7. Risiken, offen benannt (+12 more)

### Community 5 - "SHOP-AUFBAU KOMPLETT"
Cohesion: 0.11
Nodes (18): 0. Zwei Dinge, die du zuerst entscheiden musst, 1. Der Katalog, 2. Produktseite: Ersatzfilter, 3. Seitenstruktur des Shops, 4. Die Lieferanten-Mails, 5. Reihenfolge, 6. Was noch fehlt und wann es dran ist, 7. Der ehrliche Schlusspunkt (+10 more)

### Community 6 - "server.py"
Cohesion: 0.22
Nodes (17): BaseModel, get, chat(), ChatMessage, ChatRequest, _check_password(), elevenlabs_configured(), ensure_api_key() (+9 more)

### Community 7 - "build_fun.py"
Cohesion: 0.36
Nodes (15): build(), bubble(), build(), cutout(), dashed_arc(), droplet(), F(), fit() (+7 more)

### Community 8 - "Flow A: Nach dem Brunnenkauf (5 E-Mails)"
Cohesion: 0.11
Nodes (17): A1 — sofort nach Versandbestätigung, A2 — Tag 7, A3 — Tag 25, A4 — Tag 33, nur wenn A3 nicht gekauft wurde, A5 — Tag 45, letzte, Ausschlusskriterien, B1 — 3 Tage vor jeder Lieferung, B2 — 14 Tage nach Kündigung (+9 more)

### Community 9 - "Status-Update, 28. Juli 2026 (Claude Code)"
Cohesion: 0.12
Nodes (16): Eigenständiges Let'sDrink-Theme (ZIP, zum Hochladen), Kompletter Neubau: Comic-See-Theme nach KatzenUfos-Vorbild, Live in DSers erledigt (Abschnitt 5, "blockiert den ersten Verkauf"), Live in Shopify erledigt (Abschnitt 5, "Qualität"), Marketing- und Rechtstexte (neu), Mengenrabatt "3 für 2" (live), Motion-Layer (Animationen), Nachtrag: Interaktions-Niveau angehoben (Referenz: KatzenUfos-Theme) (+8 more)

### Community 10 - "HUNDE-TRINKFLASCHE, KOMPLETTPAKET"
Cohesion: 0.12
Nodes (16): 1. Kalkulation, 2. Vor der ersten Bestellung prüfen, 3. Die Saison, ehrlich, 4. Produktseite, 5. Content, das Wichtigste an diesem Produkt, 6. Shop-Setup, 7. Die nächsten 7 Tage, 8. Die 14-Tage-Regel (+8 more)

### Community 11 - "PRODUKTENTSCHEID: Rasierer-und-Klingen für MeowUfo"
Cohesion: 0.13
Nodes (14): Abo-Einrichtung in Shopify, Content: 12 Hooks, Der Entscheid, Hardware: Trinkbrunnen, CHF 69.00 inkl. MwSt, Gratisversand, Kalkulation (Annahmen offengelegt), Kundenwert über zwei Jahre, Nächste 7 Tage, PRODUKTENTSCHEID: Rasierer-und-Klingen für MeowUfo (+6 more)

### Community 12 - "JAVIER MOBILE"
Cohesion: 0.14
Nodes (13): Direkt-Senden per iOS-Kurzbefehl (optional, nur SMS/iMessage), Ehrliche iOS-Grenzen (damit es keine Ueberraschungen gibt), Eigene KI-Stimme (ElevenLabs, optional), Freihaendig sprechen mit AirPods (Auto-Modus), HTTPS mit mkcert (noetig fuer das Mikrofon auf iOS), In 3 Schritten aufs iPhone, Instagram Graph API Setup (optional, Kurzfassung), JAVIER MOBILE (+5 more)

### Community 13 - "build_b.py"
Cohesion: 0.30
Nodes (11): build(), F(), fit(), fitblock(), fitf(), Gespiegeltes Produkt mit weichem Ausblenden. Der Studio-Trick., reflection(), shade() (+3 more)

### Community 14 - "build_ad.py"
Cohesion: 0.23
Nodes (12): build(), fit(), font(), grain(), paper(), Feine technische Skala. Referenz auf 550 ml., Text mit manueller Laufweite., Warmer Verlauf plus feines Korn plus Raster. (+4 more)

### Community 15 - "build_ad3.py"
Cohesion: 0.51
Nodes (12): concept_a(), concept_b(), concept_c(), concept_d(), F(), fit(), fitblock(), fitf() (+4 more)

### Community 16 - "TEIL 1: META (Facebook und Instagram)"
Cohesion: 0.14
Nodes (13): ANZEIGENTEXTE UND VERÖFFENTLICHUNG, Budget und Regeln, Drei Anzeigentexte, Drei Handlungsaufforderungen, Fünf Überschriften zum Testen, Hashtags, Kennzahlen, auf die du schaust, Regeln (+5 more)

### Community 17 - "build_ad2.py"
Cohesion: 0.32
Nodes (9): background(), build(), draw_tracked(), F(), fit(), fit_font(), reg_marks(), shadow() (+1 more)

### Community 18 - "ULTRA AI ENTERPRISE OS"
Cohesion: 0.17
Nodes (11): 10 Agenten (echte, spawnbare Team-Leads), 1 Meta-Skill (der Orchestrator), 3 Commands, Beispiele, Ehrliche Grenzen (by design), Installation, Konfiguration, Struktur (+3 more)

### Community 19 - "listing-und-content.md"
Cohesion: 0.18
Nodes (10): Der Titel muss weg, Die Felder, fertig zum Einsetzen, Eine Beobachtung zur Farbe, LISTING-DATEN UND CONTENT AB HEUTE, Posting, Sobald das Muster da ist, TEIL 1: LISTING-DATEN, TEIL 2: CONTENT (+2 more)

### Community 20 - "ULTRA AI ENTERPRISE OS — Rollenkatalog (generativ)"
Cohesion: 0.20
Nodes (9): Ableitungsregel fuer neue Spezialisten, Business, C-Level (Steuerung), Data & AI, Engineering, Governance, Produkt & Design, Rollen-Template (+1 more)

### Community 21 - "manifest.json"
Cohesion: 0.20
Nodes (9): background_color, description, display, icons, name, orientation, short_name, start_url (+1 more)

### Community 22 - "build_photoad.py"
Cohesion: 0.44
Nodes (9): build(), cover(), F(), fitblock(), fitf(), Weicher Verlauf von unten, damit heller Text sicher lesbar bleibt., scrim(), trk() (+1 more)

### Community 23 - "PRODUKTDATEN FINAL, KORRIGIERTE TEXTE"
Cohesion: 0.20
Nodes (9): 1. Was jetzt bestätigt ist, 2. Was ich falsch geschrieben hatte, bitte überall ersetzen, 3. Keramik ändert die Positionierung, zum Guten, 4. Neue Kalkulation, mit echtem Einkaufspreis, 5. Korrigierte Produktseite, 6. Das Bildproblem, 7. Die eine Frage, die immer noch offen ist, 8. Was jetzt zu tun ist (+1 more)

### Community 24 - "WERBEVIDEO-PAKET: LET'SDRINK"
Cohesion: 0.20
Nodes (9): Der ehrliche Schluss, Grundregeln für alle drei, Hook-Varianten zum Testen, KONZEPT 1: Die hohle Hand, KONZEPT 2: Der Rücklauf, KONZEPT 3: Die Antwort auf den Einwand, Plattform-Unterschiede, WERBEVIDEO-PAKET: LET'SDRINK (+1 more)

### Community 25 - "ULTRA AI ENTERPRISE OS — Rollenkatalog (generativ)"
Cohesion: 0.20
Nodes (9): Ableitungsregel fuer neue Spezialisten, Business, C-Level (Steuerung), Data & AI, Engineering, Governance, Produkt & Design, Rollen-Template (+1 more)

### Community 26 - "ULTRA AI ENTERPRISE OS — Betriebsprotokoll"
Cohesion: 0.22
Nodes (8): Ehrlichkeits-Doktrin (nicht verhandelbar), Grundprinzip, Phase 1 — Intake (CEO/CTO-Ebene), Phase 2 — Organisation (dynamische Team-Komposition), Phase 3 — Ausfuehrung (Entwickler-Modus), Phase 4 — Qualitaetskontrolle (Cross-Review), Phase 5 — Delivery (konsolidiert), ULTRA AI ENTERPRISE OS — Betriebsprotokoll

### Community 27 - "graphify reference: extra exports and benchmark"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 28 - "APP-EMPFEHLUNGEN"
Cohesion: 0.22
Nodes (8): Analytics, APP-EMPFEHLUNGEN, Conversion-Optimierung, E-Mail-Marketing, Reihenfolge zum Start, Reviews, Tracking, Upsells und Bundles

### Community 29 - "RECHTSTEXTE"
Cohesion: 0.22
Nodes (8): Cookie-Banner, RECHTSTEXTE, Seite: AGB, Seite: Datenschutzerklärung, Seite: Impressum, Seite: Kontakt, Seite: Versand und Rückgabe, Seite: Über uns

### Community 30 - "TEXTPAKET LET'SDRINK"
Cohesion: 0.22
Nodes (8): 1. Titel, 2. Produktbeschreibung, 3. Preise, 4. Alt-Texte für die zwei Fotos, 5. Anzeigentexte für Meta, 6. Bildunterschriften für TikTok und Reels, 7. Was du noch klären musst, bevor du wirbst, TEXTPAKET LET'SDRINK

### Community 31 - "ULTRA AI ENTERPRISE OS — Betriebsprotokoll"
Cohesion: 0.22
Nodes (8): Ehrlichkeits-Doktrin (nicht verhandelbar), Grundprinzip, Phase 1 — Intake (CEO/CTO-Ebene), Phase 2 — Organisation (dynamische Team-Komposition), Phase 3 — Ausfuehrung (Entwickler-Modus), Phase 4 — Qualitaetskontrolle (Cross-Review), Phase 5 — Delivery (konsolidiert), ULTRA AI ENTERPRISE OS — Betriebsprotokoll

### Community 32 - "build_product_images.py"
Cohesion: 0.54
Nodes (7): fit_h(), lineup(), Sehr helles, leicht abfallendes Studiograu mit feinem Korn., reflection(), shade(), single(), studio_bg()

### Community 33 - "BRANDING LET'SDRINK"
Cohesion: 0.25
Nodes (7): Bildstil, BRANDING LET'SDRINK, Farbpalette, Icon-Stil, Logo-Idee, Markenname, Schriftarten

### Community 34 - "graphify-setup"
Cohesion: 0.29
Nodes (6): graphify-setup, Step 1 — check whether it is already installed, Step 2 — install (try in this order), Step 3 — self-test on a tiny folder, Step 4 — hand over, Troubleshooting

### Community 35 - "GOOGLE ADS"
Cohesion: 0.29
Nodes (6): Anzeigentexte (Responsive Search Ad), Conversion-Tracking, GOOGLE ADS, Kampagnenstruktur, Keywords (Exact/Phrase Match, eng gefasst), Wann skalieren, wann stoppen

### Community 36 - "SHOP-TEXTE TRINKFLASCHE"
Cohesion: 0.29
Nodes (6): SHOP-TEXTE TRINKFLASCHE, TEIL 1: Startseite, Feld für Feld, TEIL 2: Produktseite, Section "Produkt-Überzeugung", TEIL 3: Versand und Rückgabe, TEIL 4: Über uns, TEIL 5: Was am Produkt noch offen ist

### Community 37 - "Nate — Arbeitsregeln fuer dieses Repo"
Cohesion: 0.33
Nodes (5): Bekannte Redundanz (Absicht, nicht aufraeumen), Graphify-Workflow, Harte Regeln (aus HANDOFF, gelten immer), Nate — Arbeitsregeln fuer dieses Repo, Was hier drin ist

### Community 38 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 39 - "E-MAIL-FLOWS"
Cohesion: 0.33
Nodes (5): 1) Willkommen (Trigger: Newsletter-Anmeldung), 2) Warenkorbabbruch (Trigger: Checkout gestartet, nicht abgeschlossen), 3) Dankesmail / Post-Purchase (Trigger: Bestellung abgeschlossen), E-MAIL-FLOWS, Rabattcode für die Willkommensmail

### Community 40 - "SEITENTEXTE"
Cohesion: 0.33
Nodes (5): Häufige Fragen, Reihenfolge beim Einsetzen, SEITENTEXTE, Versand und Rückgabe, Über uns

### Community 41 - "graph-query"
Cohesion: 0.40
Nodes (4): Answering rules, graph-query, Locate the graph, Three query shapes

### Community 43 - "graphify reference: add a URL and watch a folder"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 44 - "graphify reference: commit hook and native CLAUDE.md integration"
Cohesion: 0.50
Nodes (3): For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### Community 45 - "graphify reference: incremental update and cluster-only"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

## Knowledge Gaps
- **293 isolated node(s):** `name`, `short_name`, `description`, `start_url`, `display` (+288 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What connects `name`, `short_name`, `description` to the rest of the system?**
  _293 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `What You Must Do When Invoked` be split into smaller, more focused modules?**
  _Cohesion score 0.08 - nodes in this community are weakly interconnected._
- **Should `tools.py` be split into smaller, more focused modules?**
  _Cohesion score 0.12666666666666668 - nodes in this community are weakly interconnected._
- **Should `HANDOFF: Let'sDrink — Stand 28. Juli 2026` be split into smaller, more focused modules?**
  _Cohesion score 0.08695652173913043 - nodes in this community are weakly interconnected._
- **Should `build_scene.py` be split into smaller, more focused modules?**
  _Cohesion score 0.14624505928853754 - nodes in this community are weakly interconnected._
- **Should `LAUNCH-KIT: Zwei Produkte, Wandersaison 2026` be split into smaller, more focused modules?**
  _Cohesion score 0.09523809523809523 - nodes in this community are weakly interconnected._
- **Should `SHOP-AUFBAU KOMPLETT` be split into smaller, more focused modules?**
  _Cohesion score 0.10526315789473684 - nodes in this community are weakly interconnected._