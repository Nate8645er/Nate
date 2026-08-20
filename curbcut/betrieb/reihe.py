#!/usr/bin/env python3
"""
reihe.py - prueft viele Seiten und zaehlt zusammen.

Das ist die Beweismaschine. Jede Zahl, die auf der Website steht, muss
hier herkommen und nachrechenbar sein. Erfundene Zahlen sind der
schnellste Weg, ein Werkzeug unglaubwuerdig zu machen, das sich gerade
darueber verkauft, dass es nicht luegt.
"""
import json
import sys
import time
sys.path.insert(0, "/home/user/Nate/curbcut/kern")

from concurrent.futures import ThreadPoolExecutor
from bauteile import buendeln
from pruefen import von_url
from seite import NichtErreichbar


def eine(url):
    try:
        b = von_url(url)
    except NichtErreichbar as e:
        return {"url": url, "fehler": str(e)[:110]}
    teile = buendeln(b.befunde)
    nach = {}
    for x in b.befunde:
        nach[x.art] = nach.get(x.art, 0) + 1
    return {
        "url": url,
        "zeilen": b.gepruefte_zeilen,
        "vorkommen": len(b.befunde),
        "stellen": len(teile),
        "sperrend": sum(1 for t in teile if t.schwere == "sperrend"),
        "arten": nach,
    }


def reihe(urls, gleichzeitig=6):
    with ThreadPoolExecutor(max_workers=gleichzeitig) as pool:
        return list(pool.map(eine, urls))


if __name__ == "__main__":
    urls = [z.strip() for z in open(sys.argv[1]) if z.strip()
            and not z.startswith("#")]
    start = time.time()
    ergebnis = reihe(urls)
    dauer = time.time() - start

    gut = [e for e in ergebnis if "fehler" not in e]
    weg = [e for e in ergebnis if "fehler" in e]
    mit = [e for e in gut if e["vorkommen"] > 0]
    sperr = [e for e in gut if e["sperrend"] > 0]

    print(f"\n{len(urls)} Adressen, {len(gut)} gelesen, {len(weg)} nicht erreichbar.")
    print(f"{dauer:.0f} Sekunden gesamt.\n")
    if gut:
        print(f"  Seiten mit mindestens einem Fehler: {len(mit)} von {len(gut)}"
              f"  ({100*len(mit)/len(gut):.0f} Prozent)")
        print(f"  Seiten mit sperrenden Fehlern:      {len(sperr)} von {len(gut)}"
              f"  ({100*len(sperr)/len(gut):.0f} Prozent)")
        v = sum(e["vorkommen"] for e in gut)
        s = sum(e["stellen"] for e in gut)
        print(f"  Vorkommen gesamt: {v}   Stellen im Quelltext: {s}")
        if s:
            print(f"  Buendelung: {v/s:.1f} Vorkommen je Stelle")
        print()
        arten = {}
        for e in gut:
            for a, n in e["arten"].items():
                arten[a] = arten.get(a, 0) + 1
        print("  Auf wie vielen Seiten kommt welcher Fehler vor:")
        for a, n in sorted(arten.items(), key=lambda x: -x[1]):
            print(f"    {a:<12} {n:>3} von {len(gut)}  ({100*n/len(gut):.0f}%)")
    json.dump(ergebnis, open("/home/user/Nate/curbcut/betrieb/reihe.json", "w"),
              ensure_ascii=False, indent=1)
    print(f"\n  Rohdaten: curbcut/betrieb/reihe.json")
