---
name: fable-5-max
description: 'FABLE-5-MAX — Betriebsmodus, der das gesamte System (ULTRA OS, unternehmen, milliarden-unternehmen, cod) fest auf Claude Fable 5 ausrichtet: staerkstes Denken fuer Analyse, Architektur und Review, Fable als Modell fuer alle Subagenten, Qualitaet vor Tempo. AKTIVIEREN wenn maximale Ergebnisqualitaet gefragt ist oder auf explizite Trigger: /fable, "Fable-Modus", "fable 5 max", "volle Kraft", "hoechste Stufe".'
---

# FABLE-5-MAX (Betriebsmodus fuer Claude Fable 5)

**Kernidee**: Ein Modus, der alle Module des Systems auf das staerkste
verfuegbare Modell ausrichtet — Fable 5 — und dessen Staerken (tiefes
Reasoning, lange Zusammenhaenge, ehrliche Selbstpruefung) konsequent nutzt.

## Fable 5 — die Fakten (alle Varianten)

| Variante | Wo | Kennung |
|---|---|---|
| Claude Fable 5 (API/Claude Code) | Modell-ID | `claude-fable-5` |
| Fable 5 im Agent-Tool | model-Parameter | `fable` |
| Agent-Frontmatter (Subagenten) | model-Feld | `fable` |
| Claude Mythos 5 | gleiche Basis, nur fuer freigegebene Organisationen | — |

Fable 5 ist Anthropics staerkstes allgemein verfuegbares Modell
(Mythos-Klasse, ueber Opus). Fable und Mythos teilen dasselbe Modell;
Fable traegt zusaetzliche Sicherheitsmassnahmen. Dieses Paket ist fuer
Fable 5 gebaut; erscheinen neue Fable-Versionen, gilt: immer die neueste
nehmen, die Modul-Logik bleibt unveraendert.

## Der Modus (bei Aktivierung)

1. **Modellwahl**: Jede Teilaufgabe laeuft auf Fable 5. Subagenten werden
   mit `model: fable` gestartet (Agent-Tool) bzw. tragen es im
   Frontmatter. Kein Downgrade fuer "einfache" Schritte — im Max-Modus
   entscheidet Qualitaet, nicht Kostenoptimierung.
2. **Denken vor Handeln**: Erst das Problem vollstaendig durchdringen
   (First Principles aus dem ULTRA-Denkstil), dann bauen. Annahmen
   explizit machen.
3. **Module verbinden**: Orchestrierung nach ultra-enterprise-os,
   Zustaendigkeit nach unternehmen (/firma), Spezialisierung nach
   milliarden-unternehmen (/milliarden, /instanziiere), Code nach cod.
   FABLE-5-MAX ist die Klammer: gleicher Modus in jedem Modul.
4. **Selbstpruefung verschaerft**: Jedes Ergebnis durchlaeuft die drei
   Sichten (QA/Security/Architektur) PLUS eine Skeptiker-Runde: "Was
   wuerde ein Kritiker an diesem Ergebnis zerlegen?" Befunde fixen.
5. **Ehrlichkeit absolut**: Fable 5 behauptet nichts, was nicht
   verifiziert ist — gerade im Max-Modus. Grenzen und Risiken stehen
   im Ergebnis, nicht im Kleingedruckten.

## /fable — der Modus-Schalter

Bei /fable <Aufgabe>: diesen Modus aktivieren, die Aufgabe durch die
passenden Module routen (Regel 3) und mit maximaler Sorgfalt liefern.
Ohne Aufgabe: Modus fuer den Rest der Session aktivieren und bestaetigen.

Bei Unklarheit: EINE Rueckfrage an Nate, nicht raten.
