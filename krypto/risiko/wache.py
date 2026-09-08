# KRYPTO - Risikowache.
#
# Die letzte Instanz vor jeder Order. Sie kennt nur ein Wort: NEIN,
# wenn irgendeine Grenze verletzt ist. Sie kann keine Order ausloesen,
# nur verhindern - das ist Absicht.
#
# Zusaetzlich fuehrt sie die Notbremse (Kill Switch). Einmal ausgeloest,
# steht sie auf der Platte und bleibt gezogen, bis ein Mensch sie
# ausdruecklich loest. Ein Neustart loescht sie nicht. Ein Kill Switch,
# den ein Neustart aufhebt, ist keiner.

import datetime
import json
import os

from krypto import konfig
from krypto.betrieb import protokoll

NOTBREMSE = os.path.join(konfig.ZUSTAND, "notbremse.json")

GRUENDE = {
    "api": "API-Fehler haeufen sich",
    "daten": "Marktdaten veraltet oder unbrauchbar",
    "doppelt": "doppelte Order erkannt",
    "drosselung": "Datenquelle drosselt dauerhaft",
    "tagesverlust": "Tagesverlustgrenze erreicht",
    "drawdown": "maximaler Drawdown erreicht",
    "hand": "von Hand gezogen",
}


# --- Notbremse --------------------------------------------------------

def notbremse_stand():
    try:
        with open(NOTBREMSE, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def notbremse_ziehen(grund, einzelheit=""):
    stand = {
        "grund": grund,
        "text": GRUENDE.get(grund, grund),
        "einzelheit": str(einzelheit)[:400],
        "zeit": datetime.datetime.now(datetime.timezone.utc)
                .isoformat(timespec="seconds"),
    }
    os.makedirs(konfig.ZUSTAND, exist_ok=True)
    with open(NOTBREMSE, "w", encoding="utf-8") as f:
        json.dump(stand, f, ensure_ascii=False, indent=1)
    protokoll.risiko("notbremse-gezogen", **stand)
    return stand


def notbremse_loesen(wer="mensch"):
    stand = notbremse_stand()
    if stand is None:
        return False
    os.remove(NOTBREMSE)
    protokoll.risiko("notbremse-geloest", vorher=stand.get("grund"), durch=wer)
    return True


# --- Fehlerzaehler ----------------------------------------------------
#
# Einzelne API-Fehler sind normal. Eine Serie ist ein Systemzustand.

_ZAEHLER = os.path.join(konfig.ZUSTAND, "fehlerzaehler.json")
API_FEHLER_GRENZE = 5


def fehler_melden(art):
    try:
        with open(_ZAEHLER, encoding="utf-8") as f:
            z = json.load(f)
    except (OSError, ValueError):
        z = {}
    z[art] = int(z.get(art, 0)) + 1
    os.makedirs(konfig.ZUSTAND, exist_ok=True)
    with open(_ZAEHLER, "w", encoding="utf-8") as f:
        json.dump(z, f)
    if z[art] >= API_FEHLER_GRENZE:
        notbremse_ziehen("api" if art != "drosselung" else "drosselung",
                         "%d Fehler der Art %s in Folge" % (z[art], art))
    return z[art]


def fehler_zuruecksetzen(art=None):
    try:
        with open(_ZAEHLER, encoding="utf-8") as f:
            z = json.load(f)
    except (OSError, ValueError):
        return
    if art is None:
        z = {}
    else:
        z.pop(art, None)
    with open(_ZAEHLER, "w", encoding="utf-8") as f:
        json.dump(z, f)


# --- Der Torwaechter --------------------------------------------------

class Pruefergebnis:
    def __init__(self, erlaubt, gruende):
        self.erlaubt = erlaubt
        self.gruende = gruende

    def __bool__(self):
        return self.erlaubt

    def __repr__(self):
        return "<Pruefung %s: %s>" % (
            "erlaubt" if self.erlaubt else "abgelehnt", "; ".join(self.gruende))


def order_pruefen(depot, symbol, einstieg, stop, menge, zeit=None):
    """Darf diese Order gestellt werden? Alle Gruende, nicht nur der erste.

    'depot' ist das Papierdepot (oder ein Objekt mit gleicher
    Schnittstelle): kapital, freies_geld, positionen, hoechststand,
    tagesergebnis(), trades_heute().
    """
    gruende = []

    bremse = notbremse_stand()
    if bremse:
        gruende.append("Notbremse gezogen: %s (%s)"
                       % (bremse.get("text"), bremse.get("zeit")))

    if konfig.STOP_PFLICHT and (stop is None or stop >= einstieg):
        gruende.append("kein gueltiger Stop-Loss - Pflicht")

    if menge is None or menge <= 0:
        gruende.append("Menge nicht positiv")

    wert = (menge or 0) * (einstieg or 0)
    if wert > depot.freies_geld:
        gruende.append("Ordervolumen %.2f ueber freiem Geld %.2f"
                       % (wert, depot.freies_geld))

    if symbol in depot.positionen:
        gruende.append("Position in %s besteht bereits - keine Verdopplung"
                       % symbol)

    if len(depot.positionen) >= konfig.POSITIONEN_MAX:
        gruende.append("Positionsgrenze %d erreicht" % konfig.POSITIONEN_MAX)

    gesamtwert = depot.gesamtwert()
    investiert = sum(p.wert(p.letzter_kurs) for p in depot.positionen.values())
    if gesamtwert > 0 and (investiert + wert) / gesamtwert > konfig.EXPOSURE_MAX:
        gruende.append("Exposure ueber %.0f %% des Depots"
                       % (konfig.EXPOSURE_MAX * 100))

    if gesamtwert > 0 and wert / gesamtwert > konfig.POSITION_MAX_ANTEIL:
        gruende.append("Einzelposition ueber %.0f %% des Depots"
                       % (konfig.POSITION_MAX_ANTEIL * 100))

    tag = depot.tagesergebnis(zeit)
    if depot.kapital_tagesbeginn > 0 and \
            tag / depot.kapital_tagesbeginn <= -konfig.VERLUST_TAG_MAX:
        gruende.append("Tagesverlustgrenze %.0f %% erreicht"
                       % (konfig.VERLUST_TAG_MAX * 100))
        notbremse_ziehen("tagesverlust", "Tagesergebnis %.2f" % tag)

    if depot.hoechststand > 0:
        dd = (depot.hoechststand - gesamtwert) / depot.hoechststand
        if dd >= konfig.DRAWDOWN_MAX:
            gruende.append("Drawdown %.1f %% ueber Grenze %.0f %%"
                           % (dd * 100, konfig.DRAWDOWN_MAX * 100))
            notbremse_ziehen("drawdown", "Drawdown %.3f" % dd)

    if depot.trades_heute(zeit) >= konfig.TRADES_TAG_MAX:
        gruende.append("Tageslimit von %d Trades erreicht"
                       % konfig.TRADES_TAG_MAX)

    if gruende:
        protokoll.risiko("order-abgelehnt", symbol=symbol, gruende=gruende)
    return Pruefergebnis(not gruende, gruende)
