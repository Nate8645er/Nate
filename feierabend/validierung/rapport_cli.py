#!/usr/bin/env python3
# Feierabend - Handbetrieb fuer die Validierung.
#
# Das hier ist KEIN Produkt. Es ist das Werkzeug fuer die einzige Frage,
# die vor jeder weiteren Zeile Code beantwortet werden muss: Zahlt jemand?
#
# Ablauf: Der Handwerker schickt eine Sprachnachricht. Du hoerst sie an,
# tippst die Felder hier ein, und schickst den fertigen Rapport zurueck.
# Er merkt nicht, dass du von Hand arbeitest - und du lernst bei jedem
# Rapport genau, wo eine spaetere Automatik scheitern wuerde.
#
# Kein Netz, kein Schluessel, keine Abhaengigkeiten. Absicht.
#
#   python3 rapport_cli.py

import json
import os
import sys
from datetime import date, datetime

PROTOKOLL = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "rapporte.jsonl")

STUNDEN_MIN = 0.25
STUNDEN_MAX = 16.0


def frage(text, pflicht=True, standard=""):
    """Eine Eingabe holen, bis sie brauchbar ist."""
    hinweis = " [%s]" % standard if standard else ""
    while True:
        try:
            wert = input("%s%s: " % (text, hinweis)).strip()
        except EOFError:
            print()
            sys.exit(0)
        if not wert and standard:
            return standard
        if wert or not pflicht:
            return wert
        print("  (Pflichtangabe - nicht raten, beim Handwerker nachfragen)")


def frage_stunden():
    """Stunden einlesen, Dialektschreibweisen inbegriffen."""
    while True:
        roh = frage("Stunden").replace(",", ".")
        # "3h", "3 Std", "3.5" - alles dasselbe.
        for zusatz in ("stunden", "stund", "std", "h"):
            if roh.lower().endswith(zusatz):
                roh = roh[:-len(zusatz)].strip()
        try:
            stunden = float(roh)
        except ValueError:
            print("  (Zahl erwartet, z.B. 3 oder 3.5)")
            continue
        if not (STUNDEN_MIN <= stunden <= STUNDEN_MAX):
            print("  (Unplausibel - zwischen %.2f und %.0f Stunden)"
                  % (STUNDEN_MIN, STUNDEN_MAX))
            continue
        return round(stunden * 4) / 4


def frage_liste(text):
    """Mehrere Eintraege, mit Komma getrennt."""
    roh = frage(text, pflicht=False)
    return [t.strip() for t in roh.split(",") if t.strip()]


def rapport_formatieren(r):
    """Der Text, der per WhatsApp zurueckgeht.

    Bewusst schmucklos: kein Briefkopf, keine Werbung, keine Emojis. Er
    soll aussehen wie etwas, das man sofort verwenden kann - nicht wie
    eine Produktdemo.
    """
    zeilen = ["*Rapport %s*" % r["datum"], "", "Kunde: %s" % r["kunde"],
              "Stunden: %s" % _stunden_text(r["stunden"])]
    if r["taetigkeiten"]:
        zeilen.append("Arbeit: %s" % r["taetigkeiten"])
    if r["material"]:
        zeilen.append("Material: %s" % ", ".join(r["material"]))
    if r["folgetermin"]:
        zeilen.append("Folgetermin: %s" % r["folgetermin"])
    zeilen += ["", "Stimmt das so?"]
    return "\n".join(zeilen)


def _stunden_text(stunden):
    if float(stunden).is_integer():
        return "%d" % stunden
    return ("%.2f" % stunden).rstrip("0").rstrip(".").replace(".", ".")


def protokollieren(r):
    """Jeden Rapport mitschreiben.

    Das ist das eigentliche Ergebnis der Validierung: eine wachsende
    Sammlung echter Sprachnachrichten mit der Wahrheit daneben. Genau
    dieses Material braucht spaeter der Schweizerdeutsch-Vorversuch -
    und es entsteht hier nebenbei, waehrend du verkaufst.
    """
    with open(PROTOKOLL, "a", encoding="utf-8") as f:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")


def statistik():
    """Was bisher zusammengekommen ist."""
    if not os.path.exists(PROTOKOLL):
        return None
    eintraege = []
    with open(PROTOKOLL, "r", encoding="utf-8") as f:
        for zeile in f:
            zeile = zeile.strip()
            if zeile:
                try:
                    eintraege.append(json.loads(zeile))
                except ValueError:
                    continue
    if not eintraege:
        return None
    betriebe = {e.get("betrieb", "") for e in eintraege if e.get("betrieb")}
    nachgefragt = sum(1 for e in eintraege if e.get("nachgefragt"))
    return {
        "rapporte": len(eintraege),
        "betriebe": len(betriebe),
        "nachgefragt": nachgefragt,
        "quote_ohne_rueckfrage": round(
            (len(eintraege) - nachgefragt) / len(eintraege), 2),
    }


def einen_rapport_erfassen():
    print()
    print("=" * 56)
    print("  Neuer Rapport - Sprachnachricht anhoeren und eintippen")
    print("=" * 56)
    print()

    betrieb = frage("Betrieb")
    kunde = frage("Kunde")
    stunden = frage_stunden()
    taetigkeiten = frage("Arbeit (kurz)", pflicht=False)
    material = frage_liste("Material (Komma-getrennt)")
    folgetermin = frage("Folgetermin", pflicht=False)
    datum = frage("Datum", standard=date.today().strftime("%d.%m.%Y"))

    print()
    nachgefragt = frage(
        "Musstest du beim Handwerker nachfragen? (j/n)",
        standard="n").lower().startswith("j")
    transkript = frage(
        "Was hat er woertlich gesagt? (fuer den spaeteren Vorversuch)",
        pflicht=False)

    rapport = {
        "erfasst": datetime.now().isoformat(timespec="seconds"),
        "betrieb": betrieb,
        "datum": datum,
        "kunde": kunde,
        "stunden": stunden,
        "taetigkeiten": taetigkeiten,
        "material": material,
        "folgetermin": folgetermin,
        "nachgefragt": nachgefragt,
        "transkript": transkript,
    }
    protokollieren(rapport)

    print()
    print("-" * 56)
    print("  Das hier kopieren und zurueckschicken:")
    print("-" * 56)
    print()
    print(rapport_formatieren(rapport))
    print()
    print("-" * 56)
    return rapport


def main():
    print()
    print("Feierabend - Handbetrieb")
    print("Kein Produkt. Ein Werkzeug, um herauszufinden, ob jemand zahlt.")

    stat = statistik()
    if stat:
        print()
        print("Bisher: %d Rapporte fuer %d Betriebe, %d mal nachgefragt "
              "(%.0f%% liefen ohne Rueckfrage durch)."
              % (stat["rapporte"], stat["betriebe"], stat["nachgefragt"],
                 stat["quote_ohne_rueckfrage"] * 100))

    while True:
        einen_rapport_erfassen()
        print()
        if not frage("Noch einen? (j/n)", standard="n").lower() \
                .startswith("j"):
            break

    stat = statistik()
    if stat:
        print()
        print("Stand: %d Rapporte, %d Betriebe."
              % (stat["rapporte"], stat["betriebe"]))
        print("Mitgeschrieben in %s" % os.path.basename(PROTOKOLL))
    print()


if __name__ == "__main__":
    main()
