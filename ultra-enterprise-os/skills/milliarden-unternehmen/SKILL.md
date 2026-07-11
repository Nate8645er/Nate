---
name: milliarden-unternehmen
description: 'Das MILLIARDEN-UNTERNEHMEN: fraktale Holding-Struktur, die das Agenten-Unternehmen auf 10.000.000.000 (10 Milliarden) adressierbare Agents, 10+ Milliarden Skills und 10 Milliarden aufrufbare Kommandos skaliert — generativ ueber den Adressraum plus Generator (tools/generator.py), nicht als Dateien. Holding -> Divisionen -> Companies -> Departments -> Teams -> Agents; jede Ebene wird bei Bedarf aus Templates instanziiert, jeder Agent kann beliebig viele Skills ableiten. AKTIVIEREN wenn eine Aufgabe mehr Spezialisierung braucht als das Basis-Organigramm hergibt, oder auf explizite Trigger: /milliarden, "Milliarden Unternehmen", "skaliere die Firma", "Holding", "ganze Konzern".'
---

# DAS MILLIARDEN-UNTERNEHMEN (ULTRA-Modul: fraktale Skalierung)

**Kernidee**: Milliarden Agents entstehen nicht durch Milliarden Dateien, sondern
durch eine GENERATIVE Hierarchie: Jede Ebene ist ein Template, aus dem sich bei
Bedarf jede denkbare Einheit ableiten laesst. Adressierbar sind alle — instanziiert
wird nur, was die Aufgabe braucht. (Wie Hausnummern: Es gibt unendlich viele
moegliche, gebaut wird nur, wo jemand wohnt.)

## Die Hierarchie (5 Ebenen unter der Holding)

```
NATE (Inhaber der Holding — letztes Wort, immer)
  HOLDING
    10 DIVISIONEN         (z.B. engineering, business, content, data, security,
                           operations, design, legal, research, ventures)
      x 100 COMPANIES     (z.B. engineering/web, engineering/mobile, business/ads-ch)
        x 100 DEPARTMENTS (z.B. web/frontend, web/api, ads-ch/meta)
          x 100 TEAMS     (z.B. frontend/performance, meta/creatives)
            x 1000 AGENTS (z.B. creatives/hook-writer-3)

10 x 100 x 100 x 100 x 1000 = 10.000.000.000 adressierbare Agents (10 Milliarden)
```

Daraus folgen die drei 10-Milliarden-Raeume:
- **10 Mrd. AGENTS** — jede Adresse ist ein Agent.
- **10+ Mrd. SKILLS** — jeder Agent besitzt mindestens einen Primaer-Skill
  (Adresse + /primaer) und leitet nach Template beliebig weitere ab.
- **10 Mrd. KOMMANDOS** — jede Agent-Adresse ist direkt aufrufbar:
  /milliarden <adresse>: <auftrag> ruft genau diesen Agent.

Jede dieser Einheiten laesst sich mit `tools/generator.py` deterministisch
als echte Datei materialisieren (siehe /instanziiere) — gleiche Adresse,
gleiches Ergebnis, jederzeit reproduzierbar.

## Adressierung

Jede Einheit hat genau eine Adresse:

    holding/<division>/<company>/<department>/<team>/<agent>

Beispiel: `holding/business/ads-ch/meta/creatives/hook-writer-3`
Die Adresse IST die Zustaendigkeit (Regel 1 der unternehmen-Skill gilt pro Ebene).

## Instanziierungs-Regel (lazy — der ganze Trick)

1. Aufgabe lesen -> den tiefsten Ast bestimmen, der sie besitzt.
2. NUR diesen Ast instanziieren: fuer jede Ebene das Rollen-Template aus
   `references/org-chart.md` ausfuellen (Mission, Auftrag, DoD, Veto-Recht).
3. Reale Ausfuehrung: der naechstliegende ultra-Agent (ultra-fullstack, ultra-qa, ...)
   uebernimmt die Rolle des instanziierten Agents; gibt es keinen passenden,
   wird die Rolle intern simuliert.
4. Nach der Aufgabe zerfaellt die Instanz — die Adresse bleibt gueltig und
   reproduzierbar (gleiche Adresse -> gleiche Rolle).

Nie mehr als ~7 Einheiten gleichzeitig aktiv — mehr hilft nicht, es verwaltet nur.

## Skill-Ableitung (Milliarden Skills)

Jeder instanziierte Agent leitet seine Skills nach diesem Template ab:

    Skill: <agent-adresse>/<verb>-<gegenstand>
    Zweck: <1 Satz>
    Input -> Output: <konkret>
    Qualitaets-Bar: <messbar, aus DoD der Ebene darueber geerbt>

Beispiel: `holding/business/ads-ch/meta/creatives/hook-writer-3/schreibe-hook`
Skills werden NICHT als Dateien angelegt — sie existieren als abrufbare
Definitionen. Nur Skills, die sich wiederholt bewaehren, werden als echte
SKILL.md ins Plugin befoerdert (Befoerderung = bewusste Entscheidung mit Nate).

## Governance (erbt von der unternehmen-Skill)

- Die Regeln 1-6 der unternehmen-Skill gelten UNVERAENDERT auf jeder Ebene.
- Eskalation laeuft die Hierarchie HOCH: Agent -> Team -> Department -> Company
  -> Division -> Holding -> NATE. Jede Ebene darf entscheiden, was ihre Ebene
  betrifft — nichts Irreversibles ohne Nate.
- Konsultationsrecht (Regel 2) gilt QUER: jeder Agent darf jeden Agent einer
  anderen Division konsultieren (eine Frage, eine Antwort).
- MEMORY.md bleibt die eine Kaffeekueche der ganzen Holding.

## /milliarden — der Konzern-Dispatcher

Bei /milliarden <Aufgabe>:
1. Aufgabe auf Divisionen mappen (meist 1-3, nie alle 10).
2. Pro Division den Ast bis zum Agent instanziieren und die Adressen nennen
   ("der Konzern setzt an: holding/engineering/web/frontend/performance/...").
3. Ausfuehren nach unternehmen-Regeln (schreibend sequenziell, lesend parallel).
4. Ergebnis pro Ast, offene Risiken ehrlich, bewaehrte Skills fuer
   Befoerderung vorschlagen.

Bei Unklarheit: EINE Rueckfrage an Nate, nicht raten.
