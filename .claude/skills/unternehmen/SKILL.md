---
name: unternehmen
description: 'Das Organigramm und die Kooperationsregeln fuer Nates gesamtes Agenten-Unternehmen (~24 Agents aus nate-os, Beirat, Council und Factory): wer ruft wen, wie Uebergaben laufen, wie Agents sich gegenseitig helfen (Konsultationsrecht, gemeinsames Gedaechtnis, Eskalationspfade) und wodurch sie sich NICHT im Weg stehen (klare Zustaendigkeit, ein Artefakt pro Sache, parallel nur wo lesend). AKTIVIEREN bei jeder Aufgabe, die mehrere Module/Agents beruehrt, bei Zustaendigkeits-Unklarheit oder Widerspruechen zwischen Agents. Explizite Trigger: /firma, /org, "wer ist zustaendig", "lass die Firma ran".'
---

# DAS UNTERNEHMEN (nate-os Modul 9)

**Kernidee**: Ein grosses Unternehmen entsteht nicht durch mehr Leute, sondern durch
klare Zustaendigkeiten + geregelte Hilfe. Jeder Agent hat EINEN Job (steht er niemandem
im Weg) und ein KONSULTATIONSRECHT (hilft er den anderen). Das Gedaechtnis ist die
Kaffeekueche: dort teilt jeder, was alle wissen muessen.

## Organigramm

```
                        NATE (Inhaber — letztes Wort, immer)
                          |
        +-----------------+------------------+
        |                                    |
   DER RAT (nate-council)              BEIRAT (Strategie-Consulting)
   grosse/strittige Entscheidungen     Mentor, Operator, Vertriebler,
   beruft Stimmberechtigte ein         Finanzchef, Skeptiker
        |
   CEO (Wert, Go/No-Go)
        |
   +----+--------------------+---------------------+
   |                         |                     |
ENTWICKLUNG (nate-os 1-7) CONTENT (Factory, M8)  QUERSCHNITT (helfen allen)
product-manager           spec-architekt         security-auditor
engineering-manager       batch-drafter          qa-lead
blueprint-architekt       fliessband             ui-kritiker
blueprint-builder         qa-inspektor           memory-kurator
staff-engineer                                   5 Review-Agents (parallel)
```

## Regel 1 — Zustaendigkeit (niemand steht im Weg)

- Jede Aufgabe hat genau EINEN verantwortlichen Agent (siehe Router in nate-os / factory).
- Jedes Artefakt hat genau EINEN Besitzer: Blueprints -> blueprint-architekt,
  INDEX.md -> engineering-manager, Specs -> spec-architekt, MEMORY.md -> memory-kurator.
  Niemand schreibt in fremde Artefakte — er meldet dem Besitzer.
- PARALLEL arbeiten duerfen nur Agents, die LESEN (die 5 Review-Agents, Beirat-Meinungen).
  Wer SCHREIBT, arbeitet sequenziell. Das ist die ganze Kollisionsvermeidung.

## Regel 2 — Konsultationsrecht (so helfen sie sich)

Jeder Agent DARF vor seiner Arbeit genau die Kollegen konsultieren, deren Wissen
sein Ergebnis besser macht — als kurze Frage, nicht als Uebergabe:

| Wer arbeitet | darf konsultieren | wofuer |
|---|---|---|
| spec-architekt (Ad-/Sales-Batches) | Vertriebler, Finanzchef | Hook-Winkel, Budget-Rahmen in die Quality Bar |
| spec-architekt (jeder MeowUfo-Batch) | Skeptiker | UWG/PBV-Fallen in die Bar |
| blueprint-architekt | security-auditor | Sicherheits-Stolperfallen in den Blueprint |
| blueprint-architekt | ui-kritiker | Design-Entscheidungen VOR dem Bauen fixieren |
| qa-inspektor / qa-lead | product-manager | strittige Akzeptanzkriterien auslegen |
| ceo | Finanzchef, Mentor | Opportunitaetskosten, Fokus |
| jeder | memory-kurator (via MEMORY.md lesen) | verifizierte Fakten, gelernte Fallen |

Konsultation ist EINE Frage + EINE Antwort. Wird daraus eine Debatte -> Regel 4.

## Regel 3 — Uebergabeprotokoll (saubere Schnittstellen)

Jede Uebergabe zwischen Stationen/Modulen enthaelt genau drei Dinge:
1. **Artefakt** (Blueprint / Spec / Batch / Befundliste — fertig, nicht halb)
2. **Status** (bereit / blockiert mit Grund)
3. **Offene Risiken** (ehrlich, auch wenn unangenehm)
Wer etwas Unfertiges weitergibt, hat nicht geholfen — er hat Arbeit verschoben.

## Regel 4 — Eskalationspfad (Widersprueche)

1. Zwei Agents widersprechen sich -> der ARTEFAKT-BESITZER entscheidet.
2. Betrifft es Strategie/Geld -> Beirat-Kurzmeinung (Finanzchef + Skeptiker reichen oft).
3. Immer noch strittig oder gross -> /council (Rat tagt, stimmt ab).
4. Der Rat ist sich uneins oder es ist irreversibel -> NATE entscheidet. Immer.
Kein Agent ueberstimmt Nate, keiner macht "trotzdem" weiter.

## Regel 5 — Die Kaffeekueche (gemeinsames Gedaechtnis)

MEMORY.md ist der Ort, an dem sich die Firma gegenseitig hilft, ohne sich zu treffen:
- Jeder Agent LIEST sie vor der Arbeit (laedt der SessionStart-Hook).
- Neue Stolperfalle entdeckt -> an memory-kurator melden, der traegt sie ein UND
  in betroffene bereite Blueprints/Specs nach. So lernt die ganze Firma aus dem
  Fehler EINES Agents.
- Kuratieren statt protokollieren: unter ~150 Zeilen, sonst hilft es niemandem.

## Regel 6 — Wachstum

Die Firma waechst durch bessere Regeln und Specs, nicht durch mehr Agents.
Ein neuer Agent wird nur eingestellt, wenn eine Aufgabe regelmaessig anfaellt,
die KEIN bestehender Agent besitzt — und dann ersetzt oder entlastet er explizit
jemanden. Einstellung ist eine /council-Entscheidung, keine Laune.

## /firma — der Dispatcher

Bei /firma <Aufgabe>: Aufgabe lesen, anhand der Organigramm-Aeste routen
(Entwicklung -> nate-os Router, Content-Batch -> factory Router, Strategie ->
Beirat/Council), die Kette benennen ("das laeuft so durch die Firma: ...") und
dann ausfuehren. Bei Unklarheit: EINE Rueckfrage, nicht raten.
