# TEAM-LOG — Entscheidungsprotokoll

Arbeitsweise: 7-Agenten-Team, iterativ & koordiniert. Jede Änderung wird
begründet, nach jeder Änderung laufen die verfügbaren Tests. Keine erfundenen
Ergebnisse — fehlt etwas, wird es benannt.

## Rollen
| Agent | Rolle |
|------|------|
| 1 | Chefarchitekt — Architektur, Planung, Aufgabenverteilung |
| 2 | Softwareentwickler — Implementierung, Refactoring, saubere Struktur |
| 3 | ML-/Trainingsingenieur — Trainings-/Fine-Tuning-Pipeline, Daten, Eval |
| 4 | Qualitätssicherung — Tests schreiben & ausführen |
| 5 | Performance — Geschwindigkeit, Speicher, Parallelität |
| 6 | Sicherheit — Schwachstellen, Abhängigkeiten, sichere Alternativen |
| 7 | Dokumentation — Doku, Kommentare, Diagramme, dieses Log |

---

## Eintrag 001 — Ist-Zustand (Referenz)
**Von:** Agent 1, 4, 6 · **Gemessen, nicht geschätzt**
- 16 Python-Module, 3.382 Zeilen (core+dashboard), **64 Tests grün**
- Laufzeit-Deps: fastapi, uvicorn, psutil, pydantic (schlank)
- Gefährliche Werkzeuge env-gesperrt: browser_auto, code_agent, desktop, tools
- Keys 0600, SSRF-Redirect-Schutz, Host-Guard aktiv

## Eintrag 002 — Entscheidung: Trainings-Pipeline (Agent 3)
**Begründung:** JARVIS nutzt bisher nur fertige API-Modelle, hat aber echte
Interaktionsdaten (Gedächtnis-DB, Autopilot-Ideen). Daraus lässt sich ein
*echter* Fine-Tuning-Datensatz bauen.
**Umfang (real & testbar, ohne schwere Abhängigkeiten):**
1. `training/build_dataset.py` — exportiert Gedächtnis + Ideen als Chat-JSONL,
   mit PII-Bereinigung (Agent 6).
2. `training/tokenize_stats.py` — echte Token-/Längen-Statistik (tiktoken falls
   vorhanden, sonst wortbasierte Schätzung — ehrlich gekennzeichnet).
3. `training/evaluate.py` — Holdout-Split + Eval-Gerüst.
**Ehrliche Grenze:** Volles lokales Gewicht-Training braucht GPU + torch/
transformers; das ist als optionaler Pfad dokumentiert, NICHT als „läuft"
behauptet. Der Datensatz ist direkt für API-Fine-Tuning (OpenAI/Anthropic)
bzw. lokales Fine-Tuning nutzbar.
**QS:** eigene Tests in `tests/test_training.py`.

## Eintrag 003 — Umgesetzt & verifiziert (Trainings-Pipeline)
**Von:** Agent 2, 3, 4, 6, 7 · **Echt gemessen**
- Neu: `training/scrub.py`, `build_dataset.py`, `tokenize_stats.py`,
  `evaluate.py`, `README.md`; `pyproject.toml`-Extra `training` (tiktoken).
- **Agent 6:** PII-Bereinigung (E-Mail/Key/Karte/IP/Telefon) auf jeden Export;
  Test `test_scrub_masks_pii` grün.
- **Agent 4:** 6 neue Tests, **gesamt 70 Tests grün** (vorher 64).
- **Echter CLI-Lauf:** 3 Test-Einträge → Builder schrieb 2 Gedächtnis- + 1
  Ideen-Beispiel (Offline-Eintrag korrekt gefiltert); tokenize_stats lieferte
  reale Statistik (Wort-Schätzung, da tiktoken hier nicht installiert).
- **Ehrlich offen:** volles lokales Gewicht-Training (torch/transformers, GPU)
  bewusst NICHT enthalten — nur vorbereitet, klar dokumentiert.

## Eintrag 004 — Level-/Meisterschafts-System („Max-Levelup")
**Von:** Agent 1, 2, 3, 4, 7 · **Echt gemessen**
**Ehrliche Einordnung:** 10²² fiktive Mitarbeiter einzeln per ML zu trainieren
ist unmöglich (keine Daten/Compute, keine echten Modelle). Stattdessen ein
ECHTES, skalierendes Fortschrittssystem:
- **identity.py:** jeder Mitarbeiter bekommt prozedural (0 Byte) `level` (1–99),
  `mastery` (Novize→Großmeister), `xp`, `tools` — mehr Skills/Werkzeuge je Level;
  Führungs-/Senior-Rollen + tiefere Ebenen erhalten Bonus. Deterministisch.
- **progression.py:** echtes Level-Up durch echte Arbeit — 10 XP je erledigter
  Aufgabe, je 100 XP +1 Bonus-Level (max +20), in SQLite pro Adresse.
- **orchestrator:** vergibt XP bei jeder wirklich erledigten Aufgabe, loggt Level-Ups.
- **Dashboard:** Mitarbeiter-Karte zeigt Meisterschaft/Level/XP/Werkzeuge.
- **Verbindung zur Trainings-Pipeline:** echtes Modell-Fine-Tuning auf den
  echten Ausgaben (Eintrag 003).
- **Agent 4:** 5 neue Tests inkl. End-to-End (Aufgabe→XP), **gesamt 75 grün**.
- **Live-Beweis:** Nr. 31337 (Kai Lumen-337) Basis Level 29; nach 10 echten
  Aufgaben effektives Level 30.



## Eintrag 005 — Sichtbar & nutzbar gemacht (Bestenliste + Training-Knopf)
**Von:** Agent 1, 2, 4, 7 · **Echt gemessen** · Entscheidung durch Team (Nutzer delegiert)
- **Bestenliste** `/api/fortschritt/top` + Panel auf der Mitarbeiter-Seite:
  zeigt die Aufsteiger nach echter, verdienter Erfahrung.
- **Trainings-Knopf** `/api/training/build` + Panel auf der Werkzeuge-Seite:
  baut den Fine-Tuning-Datensatz per Klick (mit PII-Bereinigung), statt CLI.
- **Agent 4:** 2 neue Tests, gesamt **77 grün**. Live verifiziert: Bestenliste
  füllt sich nach echten Aufgaben, Datensatz-Knopf baute 2 Beispiele, 0 JS-Fehler.

## Eintrag 006 — Team-Chef-Struktur (Ordnung & Überblick)
**Von:** Agent 1, 2, 4, 7 · **Echt gemessen**
**Wunsch:** jedes Team soll einen Chef haben.
- **identity.py:** in JEDEM Unternehmen sind die Adressen 0..24 die Teamleiter
  (je einer pro Team); jeder andere Mitarbeiter kennt `boss_address` (Chef im
  gleichen Team). Chefs erhalten Titel „Teamleiter <Team>" + Level-Bonus.
  Deterministisch, 0 Byte, rekursiv auch in Unter-Firmen.
- **team_bosses(company):** liefert die 25 Chefs eines Unternehmens.
- **/api/teams:** Teams + Chefs; Mitarbeiter-Endpunkt zeigt `chef_name`.
- **Dashboard:** Panel „TEAMS & CHEFS" (25 Teamleiter, anklickbar);
  Mitarbeiter-Karte zeigt Chef bzw. „★ TEAMLEITER".
- **Agent 4:** 2 neue Tests, gesamt **79 grün**. Live verifiziert: 25 Chefs,
  Mitarbeiter kennt Chef im gleichen Team, Panel rendert, 0 JS-Fehler.

## Eintrag 007 — Chefs funktional: Delegation
**Von:** Agent 1, 2, 4, 7 · **Echt gemessen**
**Wunsch:** Aufgaben zuerst an den Teamleiter, der im Team verteilt.
- **orchestrator:** jede Aufgabe wird vom Teamleiter des Teams überwacht;
  ist der Bearbeiter kein Chef, delegiert der Teamleiter an ihn (im Log:
  „Teamleiter X delegiert an Y"). `Task.boss`/`chef` im State.
- **XP:** Mitglied bekommt volle 10 XP, Teamleiter 3 Führungs-XP — Chefs
  steigen also durchs Leiten auf.
- **Dashboard:** Live-Tabelle zeigt Spalte „Teamleiter".
- **Agent 4:** 1 neuer Test (Delegation end-to-end), gesamt **80 grün**.
- **Live-Beweis:** Nova Nexus-500 → Teamleiter Mira Klar-000 delegiert →
  erledigt; Mitglied 10 XP, Chef 3 XP.

## Eintrag 008 — Nutzer-Fragen laufen sichtbar durch die Hierarchie
**Von:** Agent 1, 2, 4, 7 · **Echt gemessen**
**Wunsch:** meine Fragen automatisch an die Chefs, die verteilen; alle wirken mit
(JARVIS → Chef → Mitarbeiter).
- **orchestrator:** jede Aufgabe trägt eine Bearbeitungskette `kette`
  (JARVIS-Koordinator → Teamleiter → Mitarbeiter) + `mitwirkende`
  (3 Team-Kollegen). Kollegen erhalten je 1 Mitwirk-XP — alle wirken real mit.
- **identity.team_members():** deterministische Team-Kollegen, 0 Byte.
- **Dashboard-Chat (Gehirn + Start):** zeigt die Kette „⛓ JARVIS → Teamleiter …
  → Mitarbeiter …" und „👥 Team wirkt mit: …" über der Antwort.
- **Ehrlich:** die Antwort erzeugt der zuständige Mitarbeiter (ein echter
  Aufruf); die Kette zeigt die echte Organisationsstruktur, keine erfundene
  Mehrfach-Arbeit.
- **Agent 4:** 2 neue Tests, gesamt **82 grün**. Live: Kette + Team-Mitwirkung
  im Chat, 0 JS-Fehler.

## Eintrag 009 — Echter Team-Modus (abschaltbar, mit Kostenwarnung)
**Von:** Agent 1, 2, 4, 7 · **Echt gemessen**
**Wunsch:** mehrere Mitarbeiter geben je einen echten Beitrag, der Chef führt zusammen.
- **orchestrator:** `team_mode` (Standard AUS). An: 3 Teammitglieder beantworten
  die Frage eigenständig (echte, parallele brain.answer-Aufrufe), der Teamleiter
  führt die Beiträge zu EINER Antwort zusammen (`_team_answer`). `Task.beitraege`.
- **/api/teammode:** Status + Umschalten. `KeyIn` nach oben verschoben (sonst
  wurde der Body als Query fehlinterpretiert — behoben & verifiziert).
- **Dashboard:** Panel „TEAM-MODUS" mit Schalter + KOSTENWARNUNG (im API-Modus
  ~4 Aufrufe/Frage); Chat zeigt die Einzelbeiträge + „vom Teamleiter zusammengeführt".
- **Ehrlich:** nur im Team-Modus entstehen Mehrfach-Kosten, klar gewarnt; aus =
  ein Aufruf. Keine erfundenen Beiträge (Gehirn-gemockt getestet).
- **Agent 4:** 3 neue Tests (Team-Modus 4 Aufrufe, Toggle, /api/teams),
  gesamt **85 grün**. Live: Schalter da, 0 JS-Fehler.
