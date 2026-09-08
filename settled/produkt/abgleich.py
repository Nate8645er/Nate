# SETTLED - der Abgleich.
#
# Das Herzstueck: Welche Bestellung wurde von welcher Kettenzahlung
# beglichen, und was fehlt?
#
# Zwei Regeln, die den Unterschied zwischen brauchbar und gefaehrlich
# ausmachen:
#
#   1. Eine Zahlung wird hoechstens einer Bestellung zugeordnet und
#      umgekehrt. Ohne diese Regel wuerde eine Zahlung zwei Bestellungen
#      "begleichen" und der Haendler liefert zweimal.
#   2. Was nicht sicher zugeordnet werden kann, bleibt OFFEN. Eine
#      unsichere Zuordnung ist schlimmer als keine, weil sie
#      unbemerkt bleibt.

import csv
import datetime

# Stablecoins schwanken nicht; dort ist eine enge Toleranz richtig.
# Bei BTC deckt die weitere Toleranz Netzgebuehren des Absenders ab.
TOLERANZ = {"USDT": 0.01, "USDC": 0.01, "USDT-TRC20": 0.01, "BTC": 0.02}
TOLERANZ_VORGABE = 0.01

FENSTER_VOR = 2 * 3600          # Zahlung darf 2 h vor der Bestellung sein
FENSTER_NACH = 14 * 86400       # und bis 14 Tage danach

BEZAHLT = "bezahlt"
UNTERBEZAHLT = "unterbezahlt"
UEBERBEZAHLT = "ueberbezahlt"
OFFEN = "offen"
UNERWARTET = "unerwartet"


class Bestellung:
    def __init__(self, nummer, betrag, waehrung, zeit, adresse=None,
                 kunde=None):
        self.nummer = str(nummer)
        self.betrag = float(betrag)
        self.waehrung = waehrung.strip().upper()
        self.zeit = int(zeit)
        self.adresse = (adresse or "").strip() or None
        self.kunde = (kunde or "").strip() or None

    def __repr__(self):
        return "<Bestellung %s %.6f %s>" % (self.nummer, self.betrag,
                                            self.waehrung)


def zeit_lesen(wert):
    """Datum aus einer CSV in Unix-Sekunden. UTC, wie die Kettendaten."""
    wert = str(wert).strip()
    if wert.isdigit():
        return int(wert)
    for muster in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S",
                   "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M", "%Y-%m-%d",
                   "%d.%m.%Y %H:%M", "%d.%m.%Y"):
        try:
            d = datetime.datetime.strptime(wert, muster)
            return int(d.replace(tzinfo=datetime.timezone.utc).timestamp())
        except ValueError:
            continue
    raise ValueError("Datum nicht lesbar: %s" % wert)


def bestellungen_lesen(pfad):
    """CSV einlesen. Semikolon oder Komma, Kopfzeile Pflicht."""
    with open(pfad, encoding="utf-8-sig", newline="") as f:
        probe = f.read(4096)
        f.seek(0)
        trenner = ";" if probe.count(";") >= probe.count(",") else ","
        liste = []
        for zeile in csv.DictReader(f, delimiter=trenner):
            sauber = {(k or "").strip().lower(): (v or "").strip()
                      for k, v in zeile.items()}
            if not sauber.get("betrag"):
                continue
            liste.append(Bestellung(
                sauber.get("bestellnummer") or sauber.get("nummer") or "?",
                sauber["betrag"].replace("'", "").replace(",", "."),
                sauber.get("waehrung", "USDT"),
                zeit_lesen(sauber.get("datum") or sauber.get("zeit") or "0"),
                sauber.get("adresse"), sauber.get("kunde")))
    return liste


def _toleranz(waehrung, betrag):
    anteil = TOLERANZ.get(waehrung, TOLERANZ_VORGABE)
    return max(betrag * anteil, 1e-8)


def zuordnen(bestellungen, eingaenge):
    """Bestellungen und Kettenzahlungen einander zuordnen.

    Vorgehen: alle plausiblen Paare bilden, nach Guete sortieren, dann
    gierig vergeben. Bestes Paar zuerst - so bekommt die Zahlung, die
    eindeutig zu einer Bestellung passt, diese auch, statt von einer
    schlechteren Uebereinstimmung weggenommen zu werden.
    """
    paare = []
    for bi, b in enumerate(bestellungen):
        for ei, e in enumerate(eingaenge):
            if e.waehrung != b.waehrung:
                continue
            versatz = e.zeit - b.zeit
            if versatz < -FENSTER_VOR or versatz > FENSTER_NACH:
                continue
            abweichung = abs(e.betrag - b.betrag)
            # Guete: Betragsabweichung wiegt schwerer als Zeitabstand.
            guete = (abweichung / max(b.betrag, 1e-9)) * 1000 + versatz / 86400.0
            paare.append((guete, bi, ei))
    paare.sort()

    zu_b, zu_e = {}, {}
    for _, bi, ei in paare:
        if bi in zu_b or ei in zu_e:
            continue
        zu_b[bi] = ei
        zu_e[ei] = bi

    zeilen = []
    for bi, b in enumerate(bestellungen):
        if bi not in zu_b:
            zeilen.append({"status": OFFEN, "bestellung": b, "eingang": None,
                           "differenz": -b.betrag})
            continue
        e = eingaenge[zu_b[bi]]
        differenz = e.betrag - b.betrag
        t = _toleranz(b.waehrung, b.betrag)
        status = (BEZAHLT if abs(differenz) <= t
                  else UNTERBEZAHLT if differenz < 0 else UEBERBEZAHLT)
        zeilen.append({"status": status, "bestellung": b, "eingang": e,
                       "differenz": differenz})

    for ei, e in enumerate(eingaenge):
        if ei not in zu_e:
            zeilen.append({"status": UNERWARTET, "bestellung": None,
                           "eingang": e, "differenz": e.betrag})
    return zeilen


def bewerten(zeilen, kurs_funktion, fiat="chf"):
    """Jeder zugeordneten Zahlung den Fiatwert am Eingangstag geben.

    Fehler beim Kurs sind kein Grund abzubrechen: die Zeile bekommt
    'kurs_fehler' und der Bericht weist sie als unbewertet aus. Eine
    geschaetzte Bewertung waere in der Buchhaltung wertlos.
    """
    for z in zeilen:
        e = z.get("eingang")
        if not e:
            continue
        try:
            kurs = kurs_funktion(e.waehrung, e.zeit, fiat)
            z["kurs"] = kurs
            z["fiat"] = round(e.betrag * kurs, 2)
        except Exception as fehler:
            z["kurs"] = None
            z["fiat"] = None
            z["kurs_fehler"] = str(fehler)
    return zeilen


def zusammenfassen(zeilen, fiat="chf"):
    z = {"gesamt": len(zeilen), "fiat": fiat.upper()}
    for status in (BEZAHLT, UNTERBEZAHLT, UEBERBEZAHLT, OFFEN, UNERWARTET):
        z[status] = sum(1 for x in zeilen if x["status"] == status)
    z["fiat_summe"] = round(sum(x.get("fiat") or 0 for x in zeilen
                                if x["status"] in (BEZAHLT, UNTERBEZAHLT,
                                                   UEBERBEZAHLT)), 2)
    z["unbewertet"] = sum(1 for x in zeilen
                          if x.get("eingang") and x.get("fiat") is None)
    z["fehlbetrag"] = round(sum(x["differenz"] for x in zeilen
                                if x["status"] in (OFFEN, UNTERBEZAHLT)), 8)
    return z
