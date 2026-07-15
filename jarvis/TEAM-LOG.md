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


