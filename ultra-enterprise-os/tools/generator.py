#!/usr/bin/env python3
"""Generator des Milliarden-Unternehmens.

Materialisiert jeden der 10.000.000.000 adressierbaren Agents (und deren
Skills/Kommandos) deterministisch als echte Datei. Gleiche Adresse ->
identisches Ergebnis, jederzeit reproduzierbar.

Adressraum: holding/<division>/<company>/<department>/<team>/<agent>
  10 Divisionen x 100 Companies x 100 Departments x 100 Teams x 1000 Agents
  = 10.000.000.000 Agents. Companies/Departments/Teams/Agents duerfen als
  Name (slug) oder Index angegeben werden (0-99, Agents 0-999).

Nutzung:
  python3 generator.py agent   holding/engineering/web/frontend/performance/hook-writer-3
  python3 generator.py skill   holding/business/ads-ch/meta/creatives/hook-writer-3 schreibe-hook
  python3 generator.py command holding/data/analytics/reports/kpi/reporter-1
  python3 generator.py zaehle  # zeigt die Kapazitaet der drei Raeume

Ausgabe erfolgt nach stdout; mit --out <dir> als Datei ins Zielverzeichnis.
"""
import argparse
import hashlib
import re
import sys
from pathlib import Path

DIVISIONS = [
    "engineering", "business", "content", "data", "security",
    "operations", "design", "legal", "research", "ventures",
]
FAN_OUT = (len(DIVISIONS), 100, 100, 100, 1000)  # -> 10_000_000_000
SLUG = re.compile(r"^[a-z0-9][a-z0-9-]{0,40}$")

VETOS = [
    "Scope-Abweichung", "technische Schulden", "Security-Findings",
    "unbelegte Behauptungen", "kaputte Uebergaben", "Budget-Ueberschreitung",
    "Rechtsrisiken", "Qualitaets-Bar verfehlt",
]


def kapazitaet() -> int:
    n = 1
    for f in FAN_OUT:
        n *= f
    return n


def parse_adresse(adresse: str) -> list[str]:
    teile = adresse.strip().strip("/").split("/")
    if len(teile) != 6 or teile[0] != "holding":
        sys.exit(f"Ungueltige Adresse: {adresse!r} — erwartet "
                 "holding/<division>/<company>/<department>/<team>/<agent>")
    if teile[1] not in DIVISIONS:
        sys.exit(f"Unbekannte Division {teile[1]!r} — erlaubt: {', '.join(DIVISIONS)}")
    for ebene, limit, name in zip(("company", "department", "team", "agent"),
                                  FAN_OUT[1:], teile[2:]):
        gueltig = int(name) < limit if name.isdigit() else bool(SLUG.match(name))
        if not gueltig:
            sys.exit(f"Ungueltiger {ebene}-Name {name!r} "
                     f"(slug a-z0-9- oder Index 0-{limit - 1})")
    return teile


def _merkmal(adresse: str, liste: list[str]) -> str:
    """Deterministische Auswahl aus einer Liste — gleiche Adresse, gleiche Wahl."""
    h = int(hashlib.sha256(adresse.encode()).hexdigest(), 16)
    return liste[h % len(liste)]


def agent_md(teile: list[str]) -> str:
    adresse = "/".join(teile)
    _, division, company, department, team, agent = teile
    veto = _merkmal(adresse, VETOS)
    return f"""---
name: {agent}
description: >-
  Agent {adresse} des Milliarden-Unternehmens. Spezialist des Teams
  {team} im Department {department} ({company}, Division {division}).
  Arbeitet nach den Regeln der unternehmen-Skill; Eskalation laeuft die
  Hierarchie hoch und endet bei Nate.
---

# {agent} — {adresse}

Rolle: {agent} ({team}, {department}, {company}, {division})
Mission: Der beste Spezialist der Holding fuer den Zustaendigkeitsbereich
  dieser Adresse — praezise, ehrlich, ohne fremde Artefakte anzufassen.
Auftrag: wird bei Instanziierung durch die konkrete Teilaufgabe gesetzt.
Kontext: MEMORY.md lesen; Konsultationsrecht nach Regel 2 der
  unternehmen-Skill (eine Frage, eine Antwort).
Definition of Done: messbar, geerbt von der Ebene darueber ({team}).
Veto-Recht: {veto}.

Uebergaben nach Regel 3 (Artefakt + Status + offene Risiken).
Widersprueche nach Regel 4 eskalieren, nie stillschweigend uebergehen.
"""


def skill_md(teile: list[str], skill: str) -> str:
    adresse = "/".join(teile)
    if not SLUG.match(skill):
        sys.exit(f"Ungueltiger Skill-Name {skill!r} (slug a-z0-9-)")
    verb = skill.split("-")[0]
    return f"""---
name: {teile[-1]}-{skill}
description: >-
  Skill {adresse}/{skill} des Milliarden-Unternehmens: {verb}-Faehigkeit
  des Agents {teile[-1]} ({teile[-2]}, {teile[1]}). AKTIVIEREN wenn genau
  diese Spezialisierung gebraucht wird.
---

# {skill} — {adresse}/{skill}

Zweck: die {verb}-Faehigkeit des Agents {adresse}.
Input -> Output: konkreter Arbeitsauftrag -> fertiges Artefakt nach
Uebergabeprotokoll (Regel 3: Artefakt + Status + offene Risiken).
Qualitaets-Bar: geerbt aus der Definition of Done des Teams {teile[-2]};
kein Ergebnis ohne ehrliche Verifikation (Ehrlichkeits-Doktrin).
"""


def command_md(teile: list[str]) -> str:
    adresse = "/".join(teile)
    return f"""---
description: Ruft Agent {adresse} des Milliarden-Unternehmens direkt auf
argument-hint: [Auftrag fuer {teile[-1]}]
---

Instanziiere Agent {adresse} nach der milliarden-unternehmen-Skill und
setze ihn an auf: $ARGUMENTS

Regeln der unternehmen-Skill gelten (Zustaendigkeit, Konsultation,
Uebergabe, Eskalation). Ergebnis mit Status und offenen Risiken abliefern.
"""


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("typ", choices=["agent", "skill", "command", "zaehle"])
    p.add_argument("adresse", nargs="?", help="holding/<division>/.../<agent>")
    p.add_argument("skill", nargs="?", help="Skill-Name (nur bei typ=skill)")
    p.add_argument("--out", help="Zielverzeichnis statt stdout")
    a = p.parse_args()

    if a.typ == "zaehle":
        n = kapazitaet()
        print(f"Agents:    {n:,}".replace(",", "."))
        print(f"Skills:    {n:,}+ (>=1 Primaer-Skill pro Agent, unbegrenzt ableitbar)".replace(",", "."))
        print(f"Kommandos: {n:,} (jede Agent-Adresse ist aufrufbar)".replace(",", "."))
        return

    if not a.adresse:
        p.error("Adresse fehlt")
    teile = parse_adresse(a.adresse)

    if a.typ == "agent":
        inhalt, datei = agent_md(teile), f"{teile[-1]}.md"
    elif a.typ == "skill":
        if not a.skill:
            p.error("Skill-Name fehlt (z.B. schreibe-hook)")
        inhalt, datei = skill_md(teile, a.skill), "SKILL.md"
    else:
        inhalt, datei = command_md(teile), f"{teile[-1]}.md"

    if a.out:
        ziel = Path(a.out)
        if a.typ == "skill":
            ziel = ziel / f"{teile[-1]}-{a.skill}"
        ziel.mkdir(parents=True, exist_ok=True)
        pfad = ziel / datei
        pfad.write_text(inhalt, encoding="utf-8")
        print(f"geschrieben: {pfad}")
    else:
        print(inhalt)


if __name__ == "__main__":
    main()
