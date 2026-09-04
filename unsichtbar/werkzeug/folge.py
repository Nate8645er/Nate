#!/usr/bin/env python3
# UNSICHTBAR - eine Folge aus echten Messungen bauen.
#
#   python3 folge.py --branche Zahnarztpraxis --ort Winterthur \
#       --domains domains.txt --ausgabe folgen/
#
# Der Ablauf einer Folge ist immer derselbe:
#
#   1. Eine Branche und einen Ort waehlen
#   2. Zehn bis zwanzig echte Websites technisch pruefen
#   3. Aus dem ERGEBNIS das Skript bauen
#
# Schritt 3 ist der Punkt, an dem die meisten Content-Maschinen luegen:
# sie erzeugen Text und setzen Zahlen ein, die niemand gemessen hat.
# Dieses Werkzeug kann das nicht. Es setzt nur ein, was in Schritt 2
# tatsaechlich herauskam - und wenn nichts herauskam, sagt es das und
# erzeugt keine Folge.
#
# Die Pruefung selbst kommt aus business/product/sichtbarkeit (45 Tests,
# an echten Websites verifiziert). Hier wird nichts neu gemessen, nur
# zusammengefasst und erzaehlt.

import argparse
import datetime
import json
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(os.path.dirname(HIER))
PRUEFER = os.path.join(WURZEL, "business", "product", "sichtbarkeit")
sys.path.insert(0, PRUEFER)

import netz             # noqa: E402
import technik          # noqa: E402

# Ab hier gilt eine Website als technisch schwach. Nicht willkuerlich:
# unter 70 Prozent fehlt in der Regel mindestens ein schweres Feld
# (Crawler-Zugang, lesbarer Inhalt oder strukturierte Daten).
SCHWELLE = 70


def domains_lesen(pfad):
    with open(pfad, encoding="utf-8") as f:
        return [z.strip() for z in f
                if z.strip() and not z.strip().startswith("#")]


def messen(domains, laut=True):
    """Jede Domain pruefen. Fehler sind Ergebnisse, keine Abbrueche."""
    ergebnisse = []
    for i, d in enumerate(domains, 1):
        if laut:
            print("  [%d/%d] %s" % (i, len(domains), d), file=sys.stderr)
        eintrag = {"domain": d, "prozent": None, "crawler_gesperrt": False,
                   "gesperrte": [], "schwerster_mangel": None, "fehler": None}
        try:
            basis = netz.domain_normalisieren(d)
            befunde, _ = technik.pruefen(basis)
            # Eine nicht erreichbare Seite ist NICHT "0 Prozent
            # auffindbar" - sie ist ungemessen. Der Unterschied ist der
            # ganze Punkt: als 0 gezaehlt schleppt sie einen
            # dramatischen Wert in die Auswertung, den nie jemand
            # gemessen hat, und der landet dann in einem Video.
            erreichbar = next((b for b in befunde
                               if b.feld == "Erreichbarkeit"), None)
            if erreichbar is not None and erreichbar.bestanden is not True:
                eintrag["fehler"] = erreichbar.aussage
                ergebnisse.append(eintrag)
                continue
            eintrag["prozent"] = technik.punkte(befunde)[2]
            for b in befunde:
                if b.feld == "Crawler-Zugang" and b.bestanden is False:
                    eintrag["crawler_gesperrt"] = True
                    eintrag["gesperrte"] = [x for x in b.belege
                                            if "(" in str(x)]
            offen = [b for b in befunde if b.bestanden is False]
            if offen:
                schwerster = max(offen, key=lambda b: b.gewicht)
                eintrag["schwerster_mangel"] = schwerster.feld
        except Exception as e:
            eintrag["fehler"] = "%s: %s" % (type(e).__name__, e)
        ergebnisse.append(eintrag)
    return ergebnisse


def auswerten(ergebnisse):
    """Nur zaehlen, was gemessen wurde. Fehlversuche zaehlen nicht mit."""
    gemessen = [e for e in ergebnisse if e["prozent"] is not None]
    if not gemessen:
        return None
    gesperrt = [e for e in gemessen if e["crawler_gesperrt"]]
    schwach = [e for e in gemessen if e["prozent"] < SCHWELLE]
    maengel = {}
    for e in gemessen:
        if e["schwerster_mangel"]:
            maengel[e["schwerster_mangel"]] = \
                maengel.get(e["schwerster_mangel"], 0) + 1
    haeufigster = max(maengel.items(), key=lambda x: x[1])[0] if maengel \
        else None
    werte = sorted(e["prozent"] for e in gemessen)
    return {
        "geprueft": len(gemessen),
        "nicht_erreichbar": len(ergebnisse) - len(gemessen),
        "gesperrt": len(gesperrt),
        "schwach": len(schwach),
        "median": werte[len(werte) // 2],
        "bester": werte[-1],
        "schlechtester": werte[0],
        "haeufigster_mangel": haeufigster,
        "maengel": maengel,
    }


# --------------------------------------------------------------- Texte

def kurzvideo(branche, ort, a):
    """Skript fuer TikTok, Reels und Shorts. 35-45 Sekunden."""
    return """FOLGE: {branche} in {ort}
LAENGE: 35-45 Sekunden
BILD: Bildschirmaufnahme des Terminals, waehrend die Pruefung laeuft.
      Kein Gesicht, keine Musik, keine Schnitteffekte.

[0:00] HOOK - waehrend die erste Pruefung durchlaeuft
"Ich habe {geprueft} {branche}-Websites in {ort} geprueft.
{gesperrt} davon sperren die KI-Systeme aktiv aus."

[0:06] WAS DAS HEISST
"Das heisst: Wenn jemand ChatGPT oder Google fragt, wer in {ort}
{branche_klein} empfiehlt, koennen diese Betriebe gar nicht genannt
werden. Nicht weil sie schlecht sind. Weil eine Textdatei auf ihrem
Server Nein sagt."

[0:16] DER BEWEIS - Ergebnisliste einblenden
"Hier ist die Auswertung. Median {median} Prozent technisch auffindbar.
Bester {bester}. Schlechtester {schlechtester}.
{schwach} von {geprueft} liegen unter {schwelle} Prozent."

[0:26] DER HAEUFIGSTE FEHLER
"Und das hier war der haeufigste Mangel: {mangel}."

[0:32] CTA
"Willst du wissen, wie deine Seite abschneidet? Domain in die
Kommentare. Ich pruefe zehn pro Woche, kostenlos."

---
REGELN FUER DIESE FOLGE
- Keine Firmennamen nennen. Branche und Ort genuegen.
- Die Zahlen oben sind gemessen. Nicht runden, nicht aufhuebschen.
- Wenn die Zahlen langweilig sind, ist die Folge langweilig. Dann eine
  andere Branche nehmen - nicht die Zahlen anpassen.
""".format(branche=branche, branche_klein=branche.lower(), ort=ort,
           geprueft=a["geprueft"], gesperrt=a["gesperrt"],
           median=a["median"], bester=a["bester"],
           schlechtester=a["schlechtester"], schwach=a["schwach"],
           schwelle=SCHWELLE,
           mangel=a["haeufigster_mangel"] or "keiner eindeutig")


def linkedin(branche, ort, a, datum):
    return """{branche} in {ort}: {gesperrt} von {geprueft} sind fuer
KI-Antworten unsichtbar.

Ich habe heute {geprueft} Websites geprueft. Nicht nach Design, nicht
nach Google-Ranking - nach einer einzigen Frage: Koennte ein KI-System
diese Seite ueberhaupt lesen und daraus zitieren?

Das Ergebnis:

- {gesperrt} sperren Antwort-Crawler in der robots.txt aus
- {schwach} liegen unter {schwelle} % technischer Auffindbarkeit
- Median {median} %, bester {bester} %, schlechtester {schlechtester} %
- Haeufigster Mangel: {mangel}

Der Unterschied, den fast niemand kennt: Es gibt zwei Sorten Crawler.
Die einen sammeln Text fuers Training - die darf man guten Gewissens
sperren. Die anderen holen die Seite in dem Moment, in dem ein Kunde
fragt. Wer die sperrt, sperrt den Kunden aus.

Die meisten haben beide gesperrt, weil sie den Unterschied nicht kannten.

Pruefen Sie es selbst: Ihre Domain plus /robots.txt. Steht dort GPTBot,
PerplexityBot oder Google-Extended unter Disallow, wissen Sie genug.

Ich pruefe zehn Firmen pro Woche kostenlos. Domain in die Kommentare
oder per Nachricht.

(Gemessen am {datum}. Branchen aggregiert, keine Firma wird genannt.)
""".format(branche=branche, ort=ort, geprueft=a["geprueft"],
           gesperrt=a["gesperrt"], schwach=a["schwach"], schwelle=SCHWELLE,
           median=a["median"], bester=a["bester"],
           schlechtester=a["schlechtester"],
           mangel=a["haeufigster_mangel"] or "kein eindeutiger",
           datum=datum)


def karussell(branche, ort, a):
    return """KARUSSELL - 7 Bilder, Instagram und LinkedIn

1  {gesperrt} von {geprueft} {branche} in {ort}
   sind fuer KI-Antworten unsichtbar.
   (grosse Zahl, sonst fast nichts auf dem Bild)

2  Ihre Kunden googeln nicht mehr. Sie fragen.
   Und die Antwort nennt drei Firmen.

3  Es gibt keine Fehlermeldung, wenn KI Sie uebergeht.
   Nur allmaehlich weniger Anfragen.

4  Zwei Sorten Crawler:
   TRAINING - darf man sperren
   ANTWORT  - wer die sperrt, ist unsichtbar
   Die meisten sperren beide.

5  Das Ergebnis der Messung:
   Median {median} % · bester {bester} % · schlechtester {schlechtester} %
   Haeufigster Mangel: {mangel}

6  In zehn Minuten selbst pruefbar:
   deinedomain.ch/robots.txt
   Steht dort GPTBot unter Disallow?

7  Ich pruefe zehn Firmen pro Woche kostenlos.
   Domain in die Kommentare.
""".format(branche=branche, ort=ort, geprueft=a["geprueft"],
           gesperrt=a["gesperrt"], median=a["median"], bester=a["bester"],
           schlechtester=a["schlechtester"],
           mangel=a["haeufigster_mangel"] or "kein eindeutiger")


def schreiben(ordner, name, text):
    os.makedirs(ordner, exist_ok=True)
    pfad = os.path.join(ordner, name)
    with open(pfad, "w", encoding="utf-8") as f:
        f.write(text)
    return pfad


def main(argumente):
    p = argparse.ArgumentParser(
        prog="folge",
        description="Eine UNSICHTBAR-Folge aus echten Messungen bauen.")
    p.add_argument("--branche", required=True)
    p.add_argument("--ort", required=True)
    p.add_argument("--domains", required=True,
                   help="Textdatei, eine Domain je Zeile")
    p.add_argument("--ausgabe", default="folgen")
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argumente)

    try:
        domains = domains_lesen(args.domains)
    except OSError as e:
        print("Fehler: %s" % e, file=sys.stderr)
        return 1
    if not domains:
        print("Fehler: keine Domains in %s" % args.domains, file=sys.stderr)
        return 1

    print("Messe %d Domains ..." % len(domains), file=sys.stderr)
    ergebnisse = messen(domains, laut=not args.json)
    a = auswerten(ergebnisse)

    if a is None:
        # Der wichtigste Zweig im ganzen Programm.
        print("KEINE FOLGE. Keine einzige Domain war messbar.",
              file=sys.stderr)
        print("Ohne Messung gibt es keine Zahlen, und ohne Zahlen keinen "
              "Inhalt. Erfundene Zahlen waeren das Ende der "
              "Glaubwuerdigkeit.", file=sys.stderr)
        return 1

    if a["gesperrt"] == 0 and a["schwach"] == 0:
        print("SCHWACHE FOLGE: alle geprueften Seiten sind in Ordnung.",
              file=sys.stderr)
        print("Das ist eine gute Nachricht fuer die Branche und eine "
              "langweilige Folge. Andere Branche waehlen - nicht die "
              "Zahlen anpassen.", file=sys.stderr)

    datum = datetime.date.today().strftime("%d.%m.%Y")
    kennung = "%s-%s" % (args.branche.lower().replace(" ", "-"),
                         args.ort.lower().replace(" ", "-"))
    ordner = os.path.join(args.ausgabe, kennung)

    dateien = [
        schreiben(ordner, "kurzvideo.txt", kurzvideo(args.branche, args.ort, a)),
        schreiben(ordner, "linkedin.txt",
                  linkedin(args.branche, args.ort, a, datum)),
        schreiben(ordner, "karussell.txt",
                  karussell(args.branche, args.ort, a)),
        schreiben(ordner, "messung.json",
                  json.dumps({"branche": args.branche, "ort": args.ort,
                              "datum": datum, "auswertung": a,
                              "ergebnisse": ergebnisse},
                             ensure_ascii=False, indent=2)),
    ]

    bericht = {"folge": kennung, "auswertung": a, "dateien": dateien}
    if args.json:
        print(json.dumps(bericht, ensure_ascii=False, indent=2))
    else:
        print()
        print("Folge: %s" % kennung)
        print("  geprueft %d · nicht erreichbar %d · Crawler gesperrt %d "
              "· schwach %d" % (a["geprueft"], a["nicht_erreichbar"],
                                a["gesperrt"], a["schwach"]))
        print("  Median %d%% · bester %d%% · schlechtester %d%%"
              % (a["median"], a["bester"], a["schlechtester"]))
        print("  haeufigster Mangel: %s" % (a["haeufigster_mangel"] or "-"))
        print()
        for d in dateien:
            print("  %s" % d)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
