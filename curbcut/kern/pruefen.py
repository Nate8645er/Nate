#!/usr/bin/env python3
"""
pruefen.py - eine Seite pruefen und den Befund ausgeben.

    python3 pruefen.py https://beispiel.ch
    python3 pruefen.py datei.html

Der Bericht zaehlt Handgriffe, nicht Fehler. Siehe bauteile.py.
"""

import os
import sys

import regeln
from bauteile import buendeln
from befund import DIE_SECHS, Bericht
from seite import NichtErreichbar, Seite, holen


def pruefen(quelle, url=""):
    s = Seite(quelle, url)
    b = Bericht(shop=url or "datei")
    b.gepruefte_dateien = 1
    b.gepruefte_zeilen = quelle.count("\n") + 1
    for regel in regeln.ALLE:
        regel(s, b)
    return b


def von_url(url):
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    text, endgueltig = holen(url)
    return pruefen(text, endgueltig)


def umbrechen(text, breite=72):
    zeilen, jetzt = [], ""
    for w in text.split():
        if len(jetzt) + len(w) + 1 > breite:
            zeilen.append(jetzt)
            jetzt = w
        else:
            jetzt = (jetzt + " " + w).strip()
    if jetzt:
        zeilen.append(jetzt)
    return zeilen


def ausgeben(b, alle=False):
    teile = buendeln(b.befunde)
    print(f"\n  {b.shop}")

    if not b.befunde:
        print("\n  Kein Fehler der sechs haeufigsten Arten gefunden.\n")
        print("  Das heisst NICHT, dass die Seite barrierefrei ist. Ein Teil")
        print("  der Kriterien laesst sich nur von Hand pruefen - Tastatur-")
        print("  bedienung, Reihenfolge, Verstaendlichkeit. Ein Programm kann")
        print("  das nicht beurteilen, und wer etwas anderes verspricht,")
        print("  verspricht zu viel.\n")
        return

    sperrend = sum(1 for t in teile if t.schwere == "sperrend")
    print(f"\n  {len(teile)} Stellen im Quelltext, "
          f"{len(b.befunde)} Vorkommen auf der Seite.")
    if sperrend:
        print(f"  {sperrend} davon sperren die Bedienung.")
    print()

    zeigen = teile if alle else teile[:8]
    for i, t in enumerate(zeigen, 1):
        titel, anteil, krit = DIE_SECHS[t.art]
        marke = {"sperrend": "SPERREND", "ernst": "ernst",
                 "hinweis": "Hinweis"}[t.schwere]
        print(f"  {i}. {titel}   [{marke}]   WCAG {krit}")
        print(f"     {t.beschreiben()}.")
        print(f"     {t.erster.stelle[:96]}")
        for z in umbrechen(t.erster.vorschlag, 70):
            print(f"       {z}")
        print()

    if len(teile) > len(zeigen):
        rest = len(teile) - len(zeigen)
        print(f"  ... und {rest} weitere Stellen. Mit --alle vollstaendig.\n")

    print("  Diese Pruefung deckt die sechs Fehlerarten ab, die zusammen rund")
    print("  96 Prozent aller gemessenen Verstoesse ausmachen. Sie ersetzt")
    print("  keine Pruefung von Hand und ist keine Rechtsauskunft.\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    ziel = sys.argv[1]
    alle = "--alle" in sys.argv
    if os.path.exists(ziel):
        with open(ziel, encoding="utf-8", errors="replace") as f:
            b = pruefen(f.read(), ziel)
    else:
        try:
            b = von_url(ziel)
        except NichtErreichbar as e:
            print(f"\n  {ziel}\n  {e}\n")
            sys.exit(2)
    ausgeben(b, alle)
