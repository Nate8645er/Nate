#!/usr/bin/env python3
"""
waechter.py - der Teil, fuer den bezahlt wird.

WARUM EIN ABO UND NICHT EIN EINMALIGER BERICHT

Barrierefreiheit ist kein Zustand, den man einmal herstellt. Sie bricht
bei jeder Aenderung: Jemand tauscht ein Bild aus und vergisst den
Alternativtext. Der Baukasten bekommt eine neue Fassung und aendert eine
Farbe. Ein Praktikant baut ein Formular ein. Die Seite war am Montag in
Ordnung und ist am Freitag wieder angreifbar.

Ein einmaliger Bericht ist darum ein Foto von einem Fluss. Er sagt, wie
es an einem Tag aussah. Bezahlt wird fuer das, was danach passiert:
dass jemand hinschaut, jeden Tag, und sich meldet, BEVOR es jemand
anderes tut.

WAS DER WAECHTER NICHT TUT

Er verschickt keine Meldung, wenn sich nichts geaendert hat. Ein Dienst,
der taeglich schreibt "alles unveraendert", wird nach zwei Wochen in den
Spam-Ordner verschoben, und dann kommt auch die Meldung nicht mehr an,
die zaehlt. Er meldet sich, wenn etwas NEU ist - und sonst schweigt er.
"""

import json
import os
import sys
from dataclasses import dataclass, field, asdict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "kern"))

from bauteile import buendeln, signatur
from pruefen import von_url
from seite import NichtErreichbar

LAGER = os.path.join(os.path.dirname(__file__), "stand.json")


@dataclass
class Wache:
    url: str
    kunde: str
    bekannt: dict = field(default_factory=dict)   # signatur -> anzahl
    stumm: list = field(default_factory=list)     # bewusst akzeptierte
    letzter_lauf: str = ""
    fehlversuche: int = 0


def laden():
    if not os.path.exists(LAGER):
        return {}
    with open(LAGER, encoding="utf-8") as f:
        roh = json.load(f)
    return {k: Wache(**v) for k, v in roh.items()}


def sichern(wachen):
    with open(LAGER, "w", encoding="utf-8") as f:
        json.dump({k: asdict(v) for k, v in wachen.items()},
                  f, ensure_ascii=False, indent=1)


def einmal_pruefen(w, heute=""):
    """Prueft eine Wache. Gibt (neu, verschwunden, gewachsen, bericht) zurueck.

    Drei Arten von Veraenderung, und nur die erste ist ein Alarm:

      neu           eine Fehlerart, die es gestern nicht gab. Das ist
                    fast immer eine frische Aenderung an der Seite und
                    der einzige Grund, jemanden zu stoeren.
      verschwunden  war da, ist weg. Gute Nachricht, aber kein Anruf wert -
                    sie steht im Monatsbericht.
      gewachsen     dieselbe Stelle, aber deutlich haeufiger eingebunden.
                    Ein Hinweis, dass ein fehlerhaftes Bauteil sich
                    gerade ueber die Seite ausbreitet.
    """
    try:
        b = von_url(w.url)
    except NichtErreichbar as e:
        w.fehlversuche += 1
        return [], [], [], f"nicht erreichbar: {e}"

    w.fehlversuche = 0
    teile = buendeln(b.befunde)
    jetzt = {t.signatur: t.anzahl for t in teile}
    nach_sig = {t.signatur: t for t in teile}

    neu, gewachsen = [], []
    for sig, anzahl in jetzt.items():
        if sig in w.stumm:
            continue
        if sig not in w.bekannt:
            neu.append(nach_sig[sig])
        elif anzahl >= w.bekannt[sig] * 2 and anzahl - w.bekannt[sig] >= 5:
            gewachsen.append((nach_sig[sig], w.bekannt[sig], anzahl))

    verschwunden = [s for s in w.bekannt if s not in jetzt]

    w.bekannt = jetzt
    w.letzter_lauf = heute
    return neu, verschwunden, gewachsen, ""


def meldung(w, neu, gewachsen):
    """Der Text, der beim Kunden ankommt. Kurz, oder er wird nicht gelesen."""
    if not neu and not gewachsen:
        return None

    zeilen = [f"Auf {w.url} ist etwas dazugekommen.", ""]

    for t in neu[:5]:
        from befund import DIE_SECHS
        titel = DIE_SECHS[t.art][0]
        wo = (f"{t.anzahl} Mal" if t.anzahl > 1 else "einmal")
        zeilen.append(f"  NEU: {titel} ({wo}, Zeile {t.erster.zeile})")
        zeilen.append(f"       {t.erster.stelle[:90]}")
        zeilen.append(f"       {t.erster.vorschlag[:150]}")
        zeilen.append("")

    if len(neu) > 5:
        zeilen.append(f"  ... und {len(neu)-5} weitere neue Stellen.")
        zeilen.append("")

    for t, alt, jetzt in gewachsen[:3]:
        from befund import DIE_SECHS
        zeilen.append(f"  MEHR: {DIE_SECHS[t.art][0]} war {alt} Mal "
                      f"eingebunden, jetzt {jetzt} Mal.")
        zeilen.append("")

    zeilen.append("Wenn eine dieser Stellen so bleiben soll, kannst du sie")
    zeilen.append("stummschalten - dann meldet sich der Waechter dazu nicht mehr.")
    return "\n".join(zeilen)


def runde(heute=""):
    """Ein Durchlauf ueber alle Wachen. Das ist der taegliche Auftrag."""
    wachen = laden()
    ergebnis = []
    for schluessel, w in wachen.items():
        neu, weg, mehr, fehler = einmal_pruefen(w, heute)
        text = meldung(w, neu, mehr) if not fehler else None
        ergebnis.append({
            "wache": schluessel, "url": w.url, "kunde": w.kunde,
            "neu": len(neu), "verschwunden": len(weg), "gewachsen": len(mehr),
            "fehler": fehler, "meldung": text,
        })
    sichern(wachen)
    return ergebnis


def dazu(url, kunde):
    wachen = laden()
    schluessel = f"{kunde}:{url}"
    if schluessel in wachen:
        return False
    w = Wache(url=url, kunde=kunde)
    einmal_pruefen(w)          # erster Lauf setzt den Ausgangsstand
    wachen[schluessel] = w
    sichern(wachen)
    return True


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "dazu":
        url = sys.argv[2]
        kunde = sys.argv[3] if len(sys.argv) > 3 else "probe"
        if dazu(url, kunde):
            w = laden()[f"{kunde}:{url}"]
            print(f"  {url} wird ueberwacht.")
            print(f"  Ausgangsstand: {len(w.bekannt)} Stellen im Quelltext.")
        else:
            print("  wird schon ueberwacht")
    else:
        for e in runde():
            if e["fehler"]:
                print(f"  {e['url']}: {e['fehler']}")
            elif e["meldung"]:
                print(f"\n{'='*64}\n{e['meldung']}")
            else:
                print(f"  {e['url']}: nichts Neues"
                      + (f", {e['verschwunden']} behoben"
                         if e["verschwunden"] else ""))
