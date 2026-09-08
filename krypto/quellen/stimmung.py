# KRYPTO - Stimmung und Aufmerksamkeit.
#
# Zwei Quellen, beide am 08.09.2026 mit HTTP 200 geprueft, beide ohne
# Schluessel:
#
#   alternative.me/fng   Fear-and-Greed-Index, 0..100
#   CoinGecko /search/trending   was gerade gesucht wird
#
# Was hier NICHT drin ist: X/Twitter, Reddit, Telegram, Discord.
#   - Reddit antwortet aus Rechenzentren mit HTTP 403 (selbst geprueft)
#   - X/Twitter verlangt einen kostenpflichtigen Zugang
#   - Telegram und Discord brauchen ein Bot-Konto in der jeweiligen Gruppe
# Deshalb gibt es hier keine "Social-Sentiment"-Zahl. Eine erfundene
# waere schlimmer als keine.
#
# Und die wichtigste Regel dieses Moduls: Aufmerksamkeit ist kein
# Kaufgrund. Ein Token steht oft genau dann in der Trendliste, wenn
# die Bewegung schon gelaufen ist.

from krypto.quellen import netz

FNG = "https://api.alternative.me/fng/?limit=%d"
TRENDS = "https://api.coingecko.com/api/v3/search/trending"


def angst_und_gier(tage=1, frische=1800):
    """Fear-and-Greed-Index. 0 = extreme Angst, 100 = extreme Gier."""
    daten, herkunft = netz.holen(FNG % int(tage), frische=frische)
    reihe = daten.get("data") or []
    if not reihe:
        raise netz.QuellFehler("Fear-and-Greed-Index leer")
    werte = []
    for e in reihe:
        try:
            werte.append({"wert": int(e["value"]),
                          "einstufung": e.get("value_classification"),
                          "zeit": int(e.get("timestamp", 0))})
        except (KeyError, TypeError, ValueError):
            continue
    if not werte:
        raise netz.QuellFehler("Fear-and-Greed-Index unbrauchbar")
    return werte, herkunft


def trends(frische=600):
    """Was auf CoinGecko gerade gesucht wird.

    Das ist Aufmerksamkeit, nicht Qualitaet - und schon gar nicht ein
    Signal. Es beantwortet die Frage "worueber reden gerade viele",
    sonst nichts.
    """
    daten, herkunft = netz.holen(TRENDS, frische=frische)
    raus = []
    for eintrag in (daten.get("coins") or []):
        i = eintrag.get("item") or {}
        raus.append({
            "id": i.get("id"),
            "symbol": (i.get("symbol") or "").upper(),
            "name": i.get("name"),
            "rang_marktkapital": i.get("market_cap_rank"),
            "rang_trend": i.get("score"),
        })
    return raus, herkunft
