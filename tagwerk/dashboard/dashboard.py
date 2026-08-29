#!/usr/bin/env python3
# Tagwerk - Dashboard.
#
# Liest status.json und zeigt den Stand. Zwei Ausgaben: kurz im Terminal,
# ausfuehrlich als HTML-Datei.
#
# Es rechnet nichts schoen und schaetzt nichts. Was in status.json steht,
# steht im Dashboard - nicht mehr. Eine einzige erfundene Zahl macht das
# ganze Ding wertlos, weil man dann keiner mehr trauen kann.
#
#   python3 dashboard.py          Terminal
#   python3 dashboard.py --html   erzeugt dashboard.html

import json
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
STATUS = os.path.join(HIER, "status.json")
ZIEL_HTML = os.path.join(HIER, "dashboard.html")

TRICHTER = [
    ("leads_recherchiert", "Leads recherchiert"),
    ("nummern_geprueft", "Nummern geprüft"),
    ("angerufen", "angerufen"),
    ("erreicht", "erreicht"),
    ("vorgespraech_vereinbart", "Vorgespräch vereinbart"),
    ("vorgespraech_gefuehrt", "Vorgespräch geführt"),
    ("angebot_gemacht", "Angebot gemacht"),
    ("kunden", "KUNDEN"),
]


def laden():
    with open(STATUS, encoding="utf-8") as f:
        return json.load(f)


def naechster_engpass(t):
    """Die erste Stufe, an der der Trichter stockt.

    Das ist die einzige Zahl, die zaehlt: Wo bleibt es stehen? Alles
    davor ist erledigt, alles danach ist noch nicht dran.
    """
    for i, (schluessel, name) in enumerate(TRICHTER[:-1]):
        naechster = TRICHTER[i + 1]
        if t.get(schluessel, 0) > 0 and t.get(naechster[0], 0) == 0:
            return "%s → %s" % (name, naechster[1])
    if t.get("kunden", 0) > 0:
        return "Erster Kunde gewonnen — jetzt liefern"
    return "Noch nichts begonnen"


def terminal(d):
    t = d["trichter"]
    g = d["geld"]
    z = d["zeit"]

    print()
    print("  TAGWERK — Stand %s" % d["stand"])
    print("  " + "─" * 46)
    print()
    print("  TRICHTER")
    breite = max(t.get(k, 0) for k, _ in TRICHTER) or 1
    for schluessel, name in TRICHTER:
        wert = t.get(schluessel, 0)
        balken = "█" * int(18 * wert / breite) if wert else ""
        print("    %-24s %4d  %s" % (name, wert, balken))
    print("    %-24s %4d" % ("Absagen", t.get("absagen", 0)))
    print()
    print("  GELD")
    print("    Umsatz    CHF %8.2f" % g["umsatz_chf"])
    print("    Kosten    CHF %8.2f" % g["kosten_chf"])
    print("    Gewinn    CHF %8.2f" % g["gewinn_chf"])
    print()
    print("  ZEIT DIESE WOCHE")
    print("    Verkauf   %4.1f h" % z["verkaufsstunden_diese_woche"])
    print("    Bauen     %4.1f h" % z["baustunden_diese_woche"])
    if z["baustunden_diese_woche"] > 0 and \
            z["verkaufsstunden_diese_woche"] < z["baustunden_diese_woche"] / 3:
        print("    ⚠  Verkauf unter einem Drittel der Bauzeit.")
    print()
    print("  ENGPASS")
    print("    %s" % naechster_engpass(t))
    print()
    print("  NÄCHSTE AKTIONEN")
    for a in d["naechste_aktionen"]:
        print("    · %s" % a)
    if d.get("blockiert"):
        print()
        print("  BLOCKIERT")
        for b in d["blockiert"]:
            print("    · %s" % b)
    print()


def html(d):
    t, g, z = d["trichter"], d["geld"], d["zeit"]
    hoechst = max(t.get(k, 0) for k, _ in TRICHTER) or 1

    def zeilen():
        aus = []
        for schluessel, name in TRICHTER:
            wert = t.get(schluessel, 0)
            breite = 100 * wert / hoechst if wert else 0
            klasse = " ziel" if schluessel == "kunden" else ""
            aus.append(
                '<div class="stufe%s"><div class="n">%s</div>'
                '<div class="bar"><i style="width:%.1f%%"></i></div>'
                '<div class="w">%d</div></div>' % (klasse, name, breite, wert))
        return "".join(aus)

    def liste(eintraege, leer):
        if not eintraege:
            return '<li class="leer">%s</li>' % leer
        return "".join("<li>%s</li>" % e for e in eintraege)

    seite = HTML_VORLAGE % {
        "stand": d["stand"],
        "stufen": zeilen(),
        "absagen": t.get("absagen", 0),
        "umsatz": g["umsatz_chf"],
        "kosten": g["kosten_chf"],
        "gewinn": g["gewinn_chf"],
        "verkauf": z["verkaufsstunden_diese_woche"],
        "bauen": z["baustunden_diese_woche"],
        "engpass": naechster_engpass(t),
        "aktionen": liste(d["naechste_aktionen"], "keine"),
        "blockiert": liste(d.get("blockiert", []), "nichts"),
        "web": "erreichbar" if d["website"]["erreichbar"] else "NICHT erreichbar",
        "zahlung": "eingerichtet" if d["zahlung"]["eingerichtet"]
                   else "offen — " + d["zahlung"]["offener_schritt"],
        "plaetze": "%d von %d vergeben" % (
            d["angebot"]["gruendungsplaetze_vergeben"],
            d["angebot"]["gruendungsplaetze_total"]),
    }
    with open(ZIEL_HTML, "w", encoding="utf-8") as f:
        f.write(seite)
    return ZIEL_HTML


HTML_VORLAGE = """<!doctype html>
<html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Tagwerk — Dashboard</title>
<style>
:root{--g:#FBFAF7;--f:#F1EFE9;--t:#1C1F21;--m:#616669;--l:#E4E2DC;
  --a:#1F5A62;--rot:#B4402F}
@media(prefers-color-scheme:dark){:root{--g:#131614;--f:#1C201E;--t:#EFEEE9;
  --m:#9AA09D;--l:#2A2F2C;--a:#5FA9AF;--rot:#D9705C}}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--g);color:var(--t);font:16px/1.55 system-ui,sans-serif;
  padding:36px 20px 70px}
.bahn{max-width:660px;margin:0 auto}
h1{font-size:26px;letter-spacing:-.02em}
.stand{color:var(--m);font-size:14px;margin-top:5px}
h2{font-size:12px;letter-spacing:.16em;text-transform:uppercase;
  color:var(--m);margin:36px 0 14px;font-weight:600}
.karte{background:var(--f);border-radius:12px;padding:20px 22px}
.stufe{display:grid;grid-template-columns:170px 1fr 48px;gap:12px;
  align-items:center;padding:6px 0}
.stufe .n{font-size:14px;color:var(--m)}
.stufe.ziel .n{color:var(--t);font-weight:700}
.bar{background:var(--l);height:8px;border-radius:4px;overflow:hidden}
.bar i{display:block;height:100%%;background:var(--a);border-radius:4px}
.stufe.ziel .bar i{background:var(--rot)}
.w{text-align:right;font-variant-numeric:tabular-nums;font-weight:600}
.paar{display:flex;gap:34px;flex-wrap:wrap}
.paar div span{display:block;font-size:12px;color:var(--m);
  letter-spacing:.1em;text-transform:uppercase}
.paar div b{font-size:26px;font-variant-numeric:tabular-nums;
  font-weight:700}
.engpass{border-left:4px solid var(--a);padding-left:16px;font-size:19px;
  font-weight:600}
ul{list-style:none;display:grid;gap:9px}
li{padding-left:20px;position:relative;color:var(--m)}
li::before{content:"·";position:absolute;left:6px;color:var(--a);
  font-weight:700}
li.leer{font-style:italic;opacity:.65}
li.leer::before{content:""}
.fuss{margin-top:40px;font-size:13px;color:var(--m);text-align:center}
</style></head><body><div class="bahn">

<h1>Tagwerk</h1>
<p class="stand">Stand %(stand)s · Website %(web)s · Zahlung %(zahlung)s ·
  Gründungsplätze %(plaetze)s</p>

<h2>Engpass</h2>
<p class="engpass">%(engpass)s</p>

<h2>Trichter</h2>
<div class="karte">%(stufen)s
  <div class="stufe"><div class="n">Absagen</div><div class="bar"></div>
    <div class="w">%(absagen)d</div></div></div>

<h2>Geld</h2>
<div class="karte"><div class="paar">
  <div><span>Umsatz</span><b>%(umsatz).0f</b></div>
  <div><span>Kosten</span><b>%(kosten).0f</b></div>
  <div><span>Gewinn</span><b>%(gewinn).0f</b></div>
</div></div>

<h2>Zeit diese Woche</h2>
<div class="karte"><div class="paar">
  <div><span>Verkauf</span><b>%(verkauf).1f</b></div>
  <div><span>Bauen</span><b>%(bauen).1f</b></div>
</div></div>

<h2>Nächste Aktionen</h2>
<div class="karte"><ul>%(aktionen)s</ul></div>

<h2>Blockiert</h2>
<div class="karte"><ul>%(blockiert)s</ul></div>

<p class="fuss">Alle Zahlen aus status.json. Nichts geschätzt, nichts
  gerundet.</p>
</div></body></html>
"""


def main(argumente):
    if not os.path.exists(STATUS):
        print("status.json fehlt.")
        return 1
    d = laden()
    if "--html" in argumente:
        print("Geschrieben: %s" % html(d))
    else:
        terminal(d)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
