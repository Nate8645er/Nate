# KRYPTO - DefiLlama.
#
# Am 08.09.2026 geprueft: HTTP 200 ohne Schluessel.
# Liefert TVL je Protokoll und Kette sowie einen zweiten, unabhaengigen
# Kurs. Der zweite Kurs ist der eigentliche Wert dieser Quelle: wenn
# CoinGecko und DefiLlama weit auseinanderliegen, stimmt etwas nicht -
# und dann wird nicht gehandelt.

from krypto.quellen import netz

PROTOKOLLE = "https://api.llama.fi/protocols"
KETTEN_TVL = "https://api.llama.fi/v2/chains"
KURSE = "https://coins.llama.fi/prices/current/%s"


def kurs(coingecko_id, frische=120):
    """Zweitkurs zu einer CoinGecko-Kennung."""
    schluessel = "coingecko:%s" % str(coingecko_id)
    daten, herkunft = netz.holen(
        KURSE % netz.urllib.parse.quote(schluessel, safe=":"),
        frische=frische)
    eintrag = (daten.get("coins") or {}).get(schluessel)
    if not eintrag or eintrag.get("price") is None:
        raise netz.QuellFehler("kein DefiLlama-Kurs fuer %s" % coingecko_id)
    return float(eintrag["price"]), herkunft


def kurs_abgleich(coingecko_id, kurs_a, toleranz=0.02):
    """Vergleicht einen Kurs mit dem von DefiLlama.

    Rueckgabe (einig, abweichung, text). Bei einem Fehler der zweiten
    Quelle ist 'einig' None - nicht True. Ein nicht durchgefuehrter
    Abgleich ist kein bestandener Abgleich.
    """
    try:
        kurs_b, _ = kurs(coingecko_id)
    except netz.QuellFehler as e:
        return None, None, "Zweitquelle nicht erreichbar: %s" % e
    if not kurs_a:
        return None, None, "kein erster Kurs zum Vergleichen"
    abw = abs(kurs_a - kurs_b) / kurs_a
    if abw <= toleranz:
        return True, abw, "Kurse stimmen ueberein (%.2f %% Abweichung)" % (
            abw * 100)
    return False, abw, ("Kurse weichen um %.2f %% ab (CoinGecko %.6f, "
                        "DefiLlama %.6f)" % (abw * 100, kurs_a, kurs_b))


def ketten_tvl(frische=1800):
    """TVL je Kette - grobes Mass dafuer, wo ueberhaupt Geld liegt."""
    daten, herkunft = netz.holen(KETTEN_TVL, frische=frische)
    raus = []
    for e in (daten if isinstance(daten, list) else []):
        raus.append({"name": e.get("name"), "tvl": e.get("tvl"),
                     "symbol": e.get("tokenSymbol")})
    raus.sort(key=lambda x: x["tvl"] or 0, reverse=True)
    return raus, herkunft
