# KRYPTO - DexScreener.
#
# Am 08.09.2026 geprueft: HTTP 200 ohne Schluessel, ohne Konto.
# Das ist die Quelle, die dem am naechsten kommt, was Fomo anzeigt -
# neue Paare, Liquiditaet, Volumen, Kursbewegung, und zwar auf der
# Kette, nicht auf einer Boerse.
#
# Was diese Quelle NICHT kann: sie sagt nichts darueber, ob ein Token
# ein Betrug ist. Sie zeigt Zahlen. Die Deutung macht risiko_token.py,
# und auch die kann nur Auffaelligkeiten benennen, keine Garantie geben.

from krypto.quellen import netz

BASIS = "https://api.dexscreener.com"

# Ketten, die dieses System kennt. Die Namen sind die von DexScreener.
KETTEN = ("ethereum", "solana", "base", "arbitrum", "optimism",
          "polygon", "bsc", "avalanche")


class Paar:
    """Ein Handelspaar auf einer dezentralen Boerse."""

    def __init__(self, roh):
        self.roh = roh
        self.kette = roh.get("chainId")
        self.dex = roh.get("dexId")
        self.adresse = roh.get("pairAddress")
        basis = roh.get("baseToken") or {}
        self.symbol = (basis.get("symbol") or "").upper()
        self.name = basis.get("name")
        self.token = basis.get("address")
        self.url = roh.get("url")
        self.kurs = self._zahl(roh.get("priceUsd"))
        self.liquiditaet = self._zahl((roh.get("liquidity") or {}).get("usd"))
        self.volumen_24h = self._zahl((roh.get("volume") or {}).get("h24"))
        self.aend_24h = self._zahl((roh.get("priceChange") or {}).get("h24"))
        self.aend_1h = self._zahl((roh.get("priceChange") or {}).get("h1"))
        self.marktkapital = self._zahl(roh.get("marketCap"))
        self.fdv = self._zahl(roh.get("fdv"))
        self.erstellt_ms = roh.get("pairCreatedAt")
        kaeufe = (roh.get("txns") or {}).get("h24") or {}
        self.kaeufe_24h = kaeufe.get("buys")
        self.verkaeufe_24h = kaeufe.get("sells")

    @staticmethod
    def _zahl(x):
        try:
            return float(x)
        except (TypeError, ValueError):
            return None

    @property
    def alter_tage(self):
        if not self.erstellt_ms:
            return None
        import time
        return (time.time() - self.erstellt_ms / 1000.0) / 86400.0

    @property
    def umschlag(self):
        """Volumen im Verhaeltnis zur Liquiditaet.

        Ein sehr hoher Wert heisst: es wird viel gehandelt bei wenig
        Tiefe. Das ist entweder echtes Interesse oder Wash-Trading -
        die Zahl allein unterscheidet das nicht.
        """
        if not self.liquiditaet:
            return None
        return (self.volumen_24h or 0) / self.liquiditaet

    def __repr__(self):
        return "<Paar %s auf %s, Liq %s>" % (self.symbol, self.kette,
                                             self.liquiditaet)


def suchen(begriff, frische=120):
    """Paare zu einem Suchbegriff (Symbol, Name oder Tokenadresse)."""
    url = "%s/latest/dex/search?q=%s" % (BASIS, netz.urllib.parse.quote(
        str(begriff), safe=""))
    daten, herkunft = netz.holen(url, frische=frische)
    paare = [Paar(p) for p in (daten.get("pairs") or [])]
    return paare, herkunft


def token(kette, adresse, frische=120):
    """Alle Paare eines Tokens auf einer Kette."""
    url = "%s/tokens/v1/%s/%s" % (
        BASIS, netz.urllib.parse.quote(str(kette), safe=""),
        netz.urllib.parse.quote(str(adresse), safe=""))
    daten, herkunft = netz.holen(url, frische=frische)
    liste = daten if isinstance(daten, list) else (daten.get("pairs") or [])
    return [Paar(p) for p in liste], herkunft


def bestes_paar(paare, min_liquiditaet=25_000):
    """Das Paar, das den Token tatsaechlich abbildet.

    Nicht das mit der hoechsten Liquiditaet. Beim ersten Lauf gegen
    echte Daten (PENGU, 08.09.2026) hatte das tiefste Paar 44 Mio USD
    Liquiditaet - und ZWEI Trades in 24 Stunden. Ein toter Pool. Kurs,
    Volumen und 24h-Veraenderung waren dort leer, und der ganze Befund
    stand voller "NICHT VERFUEGBAR", obwohl der Token rege gehandelt
    wurde.

    Richtig ist: dort schauen, wo gehandelt wird. Also das hoechste
    Volumen - aber nur unter Paaren mit genug Tiefe, damit nicht ein
    Miniatur-Pool mit einem einzigen grossen Trade gewinnt.
    """
    if not paare:
        return None
    tief_genug = [p for p in paare
                  if (p.liquiditaet or 0) >= min_liquiditaet]
    mit_volumen = [p for p in tief_genug if p.volumen_24h]
    if mit_volumen:
        return max(mit_volumen, key=lambda p: p.volumen_24h)
    # Kein Paar handelt. Dann ist die Tiefe das einzige Kriterium, das
    # bleibt - und der leere Handel faellt in der Risikopruefung auf.
    mit_liq = [p for p in paare if p.liquiditaet]
    if mit_liq:
        return max(mit_liq, key=lambda p: p.liquiditaet)
    return paare[0]
