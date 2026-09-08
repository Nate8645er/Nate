# KRYPTO - Handelsuniversum.
#
# Was ueberhaupt in Frage kommt. Kein Bauchgefuehl, sondern zwei harte
# Filter: genug Handelsvolumen und genug Marktkapital. Beides kommt aus
# echten Daten, beides ist in konfig.py einstellbar.
#
# Stablecoins fliegen raus. Nicht weil sie schlecht sind, sondern weil
# ein Trendsystem auf einem Wert ohne Trend nur Gebuehren produziert.

from krypto import konfig
from krypto.betrieb import protokoll
from krypto.daten import pruefung, quelle

STABLECOINS = {
    "usdt", "usdc", "dai", "busd", "tusd", "usdd", "fdusd", "pyusd",
    "usde", "usds", "frax", "lusd", "gusd", "usd1", "rlusd",
}

# Verpackte oder gestakte Abbilder eines anderen Werts. Sie laufen
# praktisch deckungsgleich mit dem Original - zwei davon im Depot sind
# eine Position, die sich als zwei tarnt.
ABBILDER = {
    "wbtc", "cbbtc", "lbtc", "tbtc", "solvbtc", "wbeth", "weth", "steth",
    "wsteth", "reth", "cbeth", "wbnb", "bsc-usd", "meth", "ezeth", "weeth",
    "rseth", "jitosol", "msol", "bnsol", "jupsol", "beth", "clbtc",
}


class Kandidat:
    def __init__(self, roh, befund):
        self.id = roh.get("id")
        self.symbol = (roh.get("symbol") or "").lower()
        self.name = roh.get("name")
        self.kurs = roh.get("current_price")
        self.volumen = roh.get("total_volume")
        self.marktkapital = roh.get("market_cap")
        self.aend_24h = roh.get("price_change_percentage_24h_in_currency")
        self.aend_7d = roh.get("price_change_percentage_7d_in_currency")
        self.befund = befund

    @property
    def umschlag(self):
        """Volumen im Verhaeltnis zum Marktkapital - grobes Mass fuer
        Liquiditaet relativ zur Groesse."""
        if not self.marktkapital:
            return None
        return self.volumen / self.marktkapital

    def __repr__(self):
        return "<Kandidat %s %s>" % (self.symbol.upper(),
                                     "ok" if self.befund else "abgelehnt")


def aufbauen(anzahl=50, min_volumen=None, min_mcap=None):
    """Liefert (zugelassen, abgelehnt, herkunft).

    Abgelehnte werden mitgeliefert, samt Grund. Ein Filter, der seine
    Ablehnungen verschweigt, laesst sich nicht pruefen.
    """
    min_volumen = konfig.MIN_VOLUMEN_24H if min_volumen is None else min_volumen
    min_mcap = konfig.MIN_MARKTKAPITAL if min_mcap is None else min_mcap

    roh, herkunft = quelle.markt(anzahl=anzahl)
    zugelassen, abgelehnt = [], []

    for eintrag in roh:
        symbol = (eintrag.get("symbol") or "").lower()
        befund = pruefung.markteintrag_pruefen(eintrag, min_volumen, min_mcap)
        k = Kandidat(eintrag, befund)

        if symbol in STABLECOINS:
            befund.tauglich = False
            befund.gruende.insert(0, "Stablecoin - kein Trend zu handeln")
        elif symbol in ABBILDER:
            befund.tauglich = False
            befund.gruende.insert(0, "Abbild eines anderen Werts "
                                     "(wrapped/gestaked) - doppelte Position")

        (zugelassen if befund.tauglich else abgelehnt).append(k)

    protokoll.markt("universum", geprueft=len(roh),
                    zugelassen=len(zugelassen), abgelehnt=len(abgelehnt),
                    **herkunft)
    return zugelassen, abgelehnt, herkunft
