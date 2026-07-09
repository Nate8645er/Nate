# ULTRA AI ENTERPRISE OS — Integrations-Schicht (echt)

Diese Datei koppelt die **tatsaechlich verbundenen** Werkzeuge an die
ULTRA-Rollen. Nur was hier steht, kann das System real ausfuehren. Alles
andere ist Entwurf/Code, keine laufende Funktion.

Ehrlichkeits-Regel: Ein Werkzeug gilt erst als „verfuegbar", wenn es in
der aktuellen Sitzung wirklich aufrufbar ist. Ist ein Dienst nicht
verbunden, sagt das System das offen, statt ein Ergebnis vorzutaeuschen.

## Modell-Basis

- **Fable 5** (`claude-fable-5`) ist das Standardmodell dieses Systems:
  das faehigste allgemein verfuegbare Claude-Modell, mit zusaetzlichen
  Sicherheitsmassnahmen fuer Dual-Use-Faehigkeiten.
- Weitere ansteuerbare Modelle (je nach Umgebung/Abo): Opus 4.8, Sonnet 5,
  Haiku 4.5. Modellwahl nach Aufgabe: Haiku fuer schnelle/guenstige
  Mechanik, Fable/Opus fuer die schwersten Analyse-, Design- und
  Review-Schritte.
- „Alle Versionen" bedeutet praktisch: das System nutzt pro Teilaufgabe
  das passende Modell — nicht wahllos das teuerste.

## Werkzeug → Rolle (Mapping)

| Dienst (verbunden) | ULTRA-Rolle(n) | Wofuer |
|---|---|---|
| **GitHub** | DevOps, Full-Stack, Docs | Code, PRs, Reviews, CI, Releases |
| **Gmail** | Sales/Support, Business, Ops | Threads lesen/entwerfen, Labels, Outreach-Entwuerfe |
| **Google Drive** | Docs, Data, Business | Dateien lesen/erstellen, Recherche-Ablage, Reports |
| **Shopify** | Business, Full-Stack, Data | Produkte, Collections, Orders, Inventar, ShopifyQL-Analytics |
| **Higgsfield** | Design, Marketing/Content | Bild/Video/Audio/3D, Werbeclips, Voice, Virality-Check |
| **Web (Search/Fetch)** | AI Research, Business, alle | Fakten pruefen, Markt/Wettbewerb, Quellen |

## Nutzungsprinzipien (damit es nicht schadet)

1. **Lesen vor Schreiben.** Erst Zustand pruefen, dann aendern. Nie ein
   Werkzeug „blind" mutieren lassen.
2. **Bestaetigung bei Aussenwirkung.** E-Mails senden, Produkte
   veroeffentlichen, Rabatte anlegen, deployen — solche Aktionen mit
   Aussenwirkung nur nach expliziter Freigabe, nicht automatisch.
3. **Keine erfundenen Ergebnisse.** Liefert ein Werkzeug einen Fehler,
   wird der Fehler berichtet — nicht ein Erfolg behauptet.
4. **Secrets bleiben draussen.** Keine Tokens/Passwoerter in Repos,
   Commits, PRs oder generierten Dateien.

## Was „Milliarden-Agentur" ehrlich bedeutet

Das System kann sich pro Aufgabe in **beliebig viele** virtuelle Rollen
aufteilen (der Rollenkatalog ist generativ). Das ist die reale Grundlage
hinter dem Bild „grosses Unternehmen mit vielen Mitarbeitern": nicht
Milliarden dauerhaft laufende Agenten (das gaebe es real weder technisch
noch wirtschaftlich), sondern genau die Spezialisten, die eine konkrete
Aufgabe braucht — koordiniert, gegengeprueft, konsolidiert.

Was das System **nicht** tut und nicht verspricht:
- Es laeuft **nicht**, wenn du offline bist. Es reagiert nur auf deine
  Eingaben, waehrend du Claude aktiv nutzt.
- Es **generiert nicht von allein Geld/Umsatz**. Es baut, analysiert und
  automatisiert — Ergebnis haengt an echter Arbeit und echten Kanaelen.
- Es enthaelt **keine Angriffs-/Hacking-Faehigkeiten**. Security-Arbeit
  ist rein defensiv (Haerten, Finden eigener Schwachstellen, Fixen).
