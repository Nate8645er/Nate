# KRYPTO - Marktdatenquelle.
#
# CoinGecko, freie Stufe, ohne Schluessel. Am 06.09.2026 geprueft:
#   GET /ping                     -> 200
#   GET /coins/markets            -> 200, Volumen und Marktkapital dabei
#   GET /coins/{id}/ohlc?days=30  -> 200, 180 Kerzen (4-Stunden-Takt)
#
# Die freie Stufe drosselt hart (HTTP 429). Deshalb: Puffer auf Platte,
# Wartezeiten zwischen den Versuchen, und im Zweifel ein ehrlicher
# Fehler statt einer erfundenen Zahl. Ein Handelssystem, das bei
# fehlenden Daten raet, ist gefaehrlicher als eines, das stehen bleibt.

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

from krypto import konfig
from krypto.betrieb import protokoll

BASIS = "https://api.coingecko.com/api/v3"
PUFFER = os.path.join(konfig.ZUSTAND, "markt-puffer.json")

# Wie lange ein gepufferter Wert als frisch gilt.
FRISCHE = {
    "markets": 300,      # Kurse und Volumen: 5 Minuten
    "ohlc": 1800,        # Kerzen: 30 Minuten
    "ping": 3600,
}


class DatenFehler(Exception):
    """Daten nicht beschaffbar. Ausdruecklich kein Ersatzwert."""


def _puffer_laden():
    try:
        with open(PUFFER, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def _puffer_sichern(daten):
    try:
        os.makedirs(konfig.ZUSTAND, exist_ok=True)
        with open(PUFFER, "w", encoding="utf-8") as f:
            json.dump(daten, f, ensure_ascii=False, default=str)
    except OSError:
        pass


def _holen(pfad, art, frisch_erzwingen=False):
    """Ein GET mit Puffer und Ruecksicht auf die Drosselung."""
    puffer = _puffer_laden()
    jetzt = time.time()
    eintrag = puffer.get(pfad)
    alter = None
    if eintrag:
        alter = jetzt - eintrag.get("zeit", 0)
        if not frisch_erzwingen and alter < FRISCHE.get(art, 300):
            return eintrag["daten"], {"quelle": "puffer", "alter_s": int(alter)}

    url = BASIS + pfad
    letzter = None
    for versuch in range(konfig.HTTP_VERSUCHE):
        try:
            a = urllib.request.Request(url, headers={
                "User-Agent": konfig.KENNUNG, "Accept": "application/json"})
            with urllib.request.urlopen(a, timeout=konfig.HTTP_TIMEOUT) as r:
                daten = json.loads(r.read().decode("utf-8"))
            puffer[pfad] = {"zeit": jetzt, "daten": daten}
            _puffer_sichern(puffer)
            protokoll.api("abruf", pfad=pfad, status=200, versuch=versuch + 1)
            return daten, {"quelle": "netz", "alter_s": 0}
        except urllib.error.HTTPError as e:
            letzter = "HTTP %s" % e.code
            protokoll.api("abruf-fehler", pfad=pfad, status=e.code,
                          versuch=versuch + 1)
            if e.code == 429:
                time.sleep(15 * (versuch + 1))
                continue
            break
        except (urllib.error.URLError, OSError, ValueError) as e:
            letzter = type(e).__name__
            protokoll.api("abruf-fehler", pfad=pfad, grund=letzter,
                          versuch=versuch + 1)
            time.sleep(3 * (versuch + 1))

    # Netz aus. Ein alter Pufferwert ist besser als nichts - aber nur,
    # wenn sein Alter mitgereicht wird. Die Datenpruefung entscheidet
    # dann, ob er noch benutzbar ist.
    if eintrag:
        protokoll.fehler("puffer-notfall", pfad=pfad, grund=letzter,
                         alter_s=int(alter or 0))
        return eintrag["daten"], {"quelle": "puffer-veraltet",
                                  "alter_s": int(alter or 0)}
    raise DatenFehler("%s nicht abrufbar (%s) und kein Puffer vorhanden."
                      % (pfad, letzter))


def erreichbar():
    """Lebenszeichen der Quelle. True/False, ohne zu raten."""
    try:
        daten, _ = _holen("/ping", "ping", frisch_erzwingen=True)
        return bool(daten.get("gecko_says"))
    except DatenFehler:
        return False


def markt(anzahl=50, waehrung=None):
    """Die groessten Werte mit Kurs, Volumen und Marktkapital."""
    waehrung = waehrung or konfig.WAEHRUNG
    pfad = ("/coins/markets?vs_currency=%s&order=market_cap_desc"
            "&per_page=%d&page=1&sparkline=false"
            "&price_change_percentage=24h,7d"
            % (urllib.parse.quote(str(waehrung), safe=""), int(anzahl)))
    daten, herkunft = _holen(pfad, "markets")
    if not isinstance(daten, list):
        raise DatenFehler("Unerwartete Antwort auf %s: %s"
                          % (pfad, str(daten)[:120]))
    protokoll.markt("marktabruf", werte=len(daten), **herkunft)
    return daten, herkunft


def kerzen(coin_id, tage=30, waehrung=None):
    """OHLC-Kerzen. Rueckgabe: Liste [zeit_ms, open, high, low, close].

    CoinGecko waehlt den Takt selbst: bis 2 Tage 30 Minuten, bis 30 Tage
    4 Stunden, darueber 4 Tage. Das steht so in der Doku und wurde am
    06.09.2026 mit days=30 -> 180 Kerzen bestaetigt.
    """
    waehrung = waehrung or konfig.WAEHRUNG
    # safe="" ist hier keine Kosmetik: mit der Vorgabe safe="/" laesst
    # quote() Schraegstriche durch, und eine Kennung wie "a/../../x"
    # wuerde den API-Pfad umbiegen. Der Host bleibt zwar fest, aber
    # eine Kennung, die irgendwann aus einer Datei statt von Hand
    # kommt, waere damit ein offenes Scheunentor.
    pfad = "/coins/%s/ohlc?vs_currency=%s&days=%d" % (
        urllib.parse.quote(str(coin_id), safe=""),
        urllib.parse.quote(str(waehrung), safe=""), int(tage))
    daten, herkunft = _holen(pfad, "ohlc")
    if not isinstance(daten, list) or not daten:
        raise DatenFehler("Keine Kerzen fuer %s." % coin_id)
    sauber = []
    for k in daten:
        if not isinstance(k, (list, tuple)) or len(k) < 5:
            continue
        try:
            sauber.append([int(k[0])] + [float(x) for x in k[1:5]])
        except (TypeError, ValueError):
            continue
    if not sauber:
        raise DatenFehler("Kerzen fuer %s unbrauchbar." % coin_id)
    protokoll.markt("kerzen", coin=coin_id, anzahl=len(sauber), **herkunft)
    return sauber, herkunft
