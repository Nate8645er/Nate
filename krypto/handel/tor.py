# KRYPTO - Freigabetor.
#
# Die einzige Stelle im System, an der eine Order das Papier verlassen
# koennte. Es gibt keine zweite. Alles, was handeln will, muss hier
# durch - und hier steht die Tuer zu.
#
# Stand 06.09.2026: ES GIBT KEINE LIVE-AUSFUEHRUNG. Kein Modul dieses
# Systems ist an einen Broker angebunden. freigeben() prueft die
# Bedingungen und wirft danach trotzdem - weil hinter der Tuer nichts
# gebaut ist. Das ist kein Versehen, sondern der verlangte Zustand:
# "Aktiviere Live Trading NICHT automatisch."
#
# Vier Bedingungen muessen zusammenkommen, bevor hier ueberhaupt
# weitergedacht wird:
#   1. LIVE_TRADING_ENABLED=true              (Umgebung, Vorgabe false)
#   2. LIVE_TRADING_CONFIRM=ICH-HANDLE-MIT-ECHTEM-GELD   (zweiter Riegel)
#   3. keine gezogene Notbremse
#   4. eine ausdrueckliche Freigabe je einzelner Order durch einen
#      Menschen - keine Sammelfreigabe, keine Freigabe auf Vorrat

from krypto import konfig
from krypto.betrieb import protokoll
from krypto.risiko import wache


class LiveGesperrt(Exception):
    """Live-Handel ist gesperrt. Beabsichtigt."""


def live_zustand():
    """Was fehlt, damit Live-Handel ueberhaupt denkbar waere."""
    fehlt = []
    if not konfig.LIVE_TRADING_ENABLED:
        fehlt.append("LIVE_TRADING_ENABLED ist nicht 'true'")
    if konfig.LIVE_TRADING_CONFIRM != konfig.LIVE_FREIGABE_WORT:
        fehlt.append("LIVE_TRADING_CONFIRM traegt nicht das Freigabewort")
    bremse = wache.notbremse_stand()
    if bremse:
        fehlt.append("Notbremse gezogen: %s" % bremse.get("text"))
    fehlt.append("keine Broker-Anbindung implementiert "
                 "(ausdrueckliche Vorgabe: keine echten Orders)")
    return {"aktiv": False, "fehlt": fehlt}


def freigeben(order, bestaetigung_mensch=None):
    """Der Versuch, eine Order live zu stellen. Endet immer mit einer
    Ausnahme - dokumentiert, protokolliert, ohne Nebenwirkung."""
    zustand = live_zustand()
    protokoll.risiko("live-versuch-abgewiesen",
                     symbol=getattr(order, "symbol", order),
                     fehlt=zustand["fehlt"],
                     mensch_bestaetigt=bool(bestaetigung_mensch))
    raise LiveGesperrt(
        "Live-Handel gesperrt. Offen: " + "; ".join(zustand["fehlt"]))


def papier_erlaubt():
    """Papierhandel braucht keine Freigabe - er bewegt kein Geld."""
    return True
