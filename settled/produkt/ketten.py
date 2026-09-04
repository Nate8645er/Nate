# SETTLED - Kettenzugriff.
#
# Liest eingehende Zahlungen zu einer Empfangsadresse. Nur lesend, nur
# oeffentliche Endpunkte, kein Schluessel, kein Konto, keine Kosten.
#
# ABDECKUNG - ehrlich, weil eine falsche Vollstaendigkeitsbehauptung im
# Buchhaltungskontext teurer ist als eine fehlende Kette:
#
#   Bitcoin        vollstaendig ueber Blockstream
#   ERC-20         vollstaendig ueber eth_getLogs (USDT, USDC, jeder Token)
#   TRC-20         vollstaendig ueber TronGrid (USDT-TRC20)
#   natives ETH    NICHT abgedeckt - dafuer braeuchte es einen Indexer,
#                  und die kosten Geld. Wird als Luecke gemeldet, nie
#                  stillschweigend als "keine Zahlungen" ausgegeben.
#
# Warum niemals ein privater Schluessel: SETTLED bewegt kein Geld. Es
# liest oeffentliche Kettendaten. Ein Werkzeug, das nur lesen kann, kann
# auch bei einem Fehler nichts verlieren.

import json
import time
import urllib.error
import urllib.parse
import urllib.request

KENNUNG = "SETTLED/0.1 (Zahlungsabgleich, nur lesend)"
ZEITLIMIT = 30

BLOCKSTREAM = "https://blockstream.info/api"
# Geprueft: publicnode beantwortet eth_blockNumber, weist eth_getLogs
# aber mit HTTP 403 ab. mevblocker erlaubt getLogs und begrenzt ueber
# die Trefferzahl statt ueber die Fenstergroesse - fuer eine
# Empfaengeradresse eines Shops ist das reichlich.
ETH_RPC = "https://rpc.mevblocker.io"
ETH_RPC_ERSATZ = "https://ethereum-rpc.publicnode.com"
TRONGRID = "https://api.trongrid.io"

# Transfer(address,address,uint256) - die Signatur, unter der jeder
# ERC-20-Token eine Ueberweisung meldet.
TRANSFER_TOPIC = ("0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a1"
                  "1628f55a4df523b3ef")

# Nur was im Handel wirklich vorkommt. Wer einen anderen Token braucht,
# traegt ihn hier ein - raten waere schlimmer als fehlen.
TOKEN = {
    "USDT": {"kette": "ethereum", "dezimalen": 6,
             "vertrag": "0xdac17f958d2ee523a2206206994597c13d831ec7",
             "coingecko": "tether"},
    "USDC": {"kette": "ethereum", "dezimalen": 6,
             "vertrag": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
             "coingecko": "usd-coin"},
    "USDT-TRC20": {"kette": "tron", "dezimalen": 6,
                   "vertrag": "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t",
                   "coingecko": "tether"},
    "BTC": {"kette": "bitcoin", "dezimalen": 8, "coingecko": "bitcoin"},
}


class KettenFehler(Exception):
    """Kette nicht erreichbar oder Antwort unbrauchbar."""


class Eingang:
    """Eine eingegangene Zahlung, kettenunabhaengig."""

    def __init__(self, kette, waehrung, betrag, zeit, tx, von=None,
                 bestaetigungen=None):
        self.kette = kette
        self.waehrung = waehrung
        self.betrag = betrag              # als float, in ganzen Einheiten
        self.zeit = zeit                  # Unix-Sekunden
        self.tx = tx
        self.von = von
        self.bestaetigungen = bestaetigungen

    def als_daten(self):
        return {"kette": self.kette, "waehrung": self.waehrung,
                "betrag": self.betrag, "zeit": self.zeit, "tx": self.tx,
                "von": self.von, "bestaetigungen": self.bestaetigungen}

    def __repr__(self):
        return "<Eingang %.8f %s @%d %s>" % (
            self.betrag, self.waehrung, self.zeit, self.tx[:12])


def _holen(url, daten=None, versuche=3):
    """HTTP mit Wiederholung. Oeffentliche Endpunkte drosseln gerne."""
    kopf = {"User-Agent": KENNUNG, "Accept": "application/json"}
    leib = None
    if daten is not None:
        leib = json.dumps(daten).encode()
        kopf["Content-Type"] = "application/json"
    letzter = None
    for versuch in range(versuche):
        try:
            a = urllib.request.Request(url, data=leib, headers=kopf)
            with urllib.request.urlopen(a, timeout=ZEITLIMIT) as r:
                roh = r.read()
            text = roh.decode("utf-8", errors="replace")
            try:
                return json.loads(text)
            except ValueError:
                return text.strip()
        except urllib.error.HTTPError as e:
            letzter = "HTTP %s" % e.code
            if e.code in (429, 502, 503, 504):
                time.sleep(2 * (versuch + 1))
                continue
            break
        except (urllib.error.URLError, OSError) as e:
            letzter = str(e)
            time.sleep(1.5 * (versuch + 1))
    raise KettenFehler("%s nicht erreichbar: %s" % (url, letzter))


# ------------------------------------------------------------- Bitcoin

def bitcoin_eingaenge(adresse, seit=0):
    """Alle Zahlungseingaenge auf eine Bitcoin-Adresse."""
    try:
        txs = _holen("%s/address/%s/txs" % (BLOCKSTREAM,
                                            urllib.parse.quote(adresse)))
    except KettenFehler:
        raise
    if not isinstance(txs, list):
        raise KettenFehler("Blockstream lieferte keine Transaktionsliste")

    eingaenge = []
    for tx in txs:
        status = tx.get("status") or {}
        if not status.get("confirmed"):
            continue                       # unbestaetigt zaehlt nicht
        zeit = status.get("block_time", 0)
        if zeit < seit:
            continue
        # Summe aller Ausgaenge, die AUF diese Adresse zeigen. Eine
        # Transaktion kann mehrere haben; einzeln zaehlen wuerde eine
        # Zahlung faelschlich in Teilzahlungen zerlegen.
        satoshi = sum(v.get("value", 0) for v in tx.get("vout", [])
                      if v.get("scriptpubkey_address") == adresse)
        if satoshi <= 0:
            continue
        absender = None
        for e in tx.get("vin", []):
            vorher = e.get("prevout") or {}
            if vorher.get("scriptpubkey_address"):
                absender = vorher["scriptpubkey_address"]
                break
        eingaenge.append(Eingang(
            "bitcoin", "BTC", satoshi / 1e8, zeit, tx.get("txid", ""),
            absender))
    return eingaenge


# ------------------------------------------------------------ Ethereum

class ZuVieleTreffer(KettenFehler):
    """Das Blockfenster liefert mehr Logs, als der Knoten herausgibt."""


def _eth_rpc(methode, parameter):
    letzter = None
    for knoten in (ETH_RPC, ETH_RPC_ERSATZ):
        try:
            antwort = _holen(knoten, {"jsonrpc": "2.0", "id": 1,
                                      "method": methode,
                                      "params": parameter}, versuche=2)
        except KettenFehler as e:
            letzter = e
            continue
        if not isinstance(antwort, dict):
            letzter = KettenFehler("Unerwartete RPC-Antwort von %s" % knoten)
            continue
        if "error" in antwort:
            meldung = str(antwort["error"].get("message", antwort["error"]))
            if ("more than" in meldung or "range" in meldung.lower()
                    or "limited to" in meldung):
                raise ZuVieleTreffer(meldung)
            letzter = KettenFehler("RPC-Fehler: %s" % meldung)
            continue
        return antwort.get("result")
    raise letzter or KettenFehler("Kein Ethereum-Knoten erreichbar")


def eth_blockhoehe():
    return int(_eth_rpc("eth_blockNumber", []), 16)


def _adresse_als_topic(adresse):
    return "0x" + "0" * 24 + adresse.lower().replace("0x", "")


def erc20_eingaenge(adresse, waehrung="USDT", von_block=None, bis_block=None,
                    schritt=10000):
    """Eingehende ERC-20-Transfers an eine Adresse.

    Ueber eth_getLogs statt ueber einen Indexer: kostenlos und
    vollstaendig, dafuer nur in Blockfenstern abfragbar. Oeffentliche
    Knoten begrenzen die Fenstergroesse - deshalb wird in Schritten
    gelesen.
    """
    t = TOKEN.get(waehrung)
    if not t or t["kette"] != "ethereum":
        raise KettenFehler("Unbekannter ERC-20-Token: %s" % waehrung)

    kopf = eth_blockhoehe()
    bis = kopf if bis_block is None else bis_block
    # Vorgabe: rund 30 Tage bei ~12 Sekunden Blockzeit.
    von = bis - 216000 if von_block is None else von_block
    von = max(0, von)

    eingaenge = []
    block = von
    while block <= bis:
        ende = min(block + schritt - 1, bis)
        for l in _logs_lesen(t, adresse, block, ende):
            betrag = int(l["data"], 16) / (10 ** t["dezimalen"])
            if betrag <= 0:
                continue
            zeit = _blockzeit(int(l["blockNumber"], 16))
            absender = "0x" + l["topics"][1][-40:]
            eingaenge.append(Eingang("ethereum", waehrung, betrag, zeit,
                                     l["transactionHash"], absender))
        block = ende + 1
    return eingaenge


def _logs_lesen(t, adresse, von, bis, tiefe=0):
    """Logs eines Fensters holen, bei Ueberlauf das Fenster halbieren.

    Knoten begrenzen unterschiedlich - der eine ueber die Blockzahl, der
    andere ueber die Trefferzahl. Statt eine Grenze zu raten, wird auf
    die Fehlermeldung reagiert und geteilt.
    """
    try:
        return _eth_rpc("eth_getLogs", [{
            "fromBlock": hex(von), "toBlock": hex(bis),
            "address": t["vertrag"],
            "topics": [TRANSFER_TOPIC, None, _adresse_als_topic(adresse)],
        }]) or []
    except ZuVieleTreffer:
        if von >= bis or tiefe > 20:
            raise KettenFehler(
                "Block %d liefert allein zu viele Treffer - Adresse zu "
                "aktiv fuer oeffentliche Knoten." % von)
        mitte = (von + bis) // 2
        return (_logs_lesen(t, adresse, von, mitte, tiefe + 1)
                + _logs_lesen(t, adresse, mitte + 1, bis, tiefe + 1))


_BLOCKZEIT = {}


def _blockzeit(nummer):
    """Zeitstempel eines Blocks, gepuffert.

    Ohne Puffer wird jeder Log einzeln aufgeloest und der oeffentliche
    Knoten drosselt nach wenigen Sekunden.
    """
    if nummer in _BLOCKZEIT:
        return _BLOCKZEIT[nummer]
    block = _eth_rpc("eth_getBlockByNumber", [hex(nummer), False])
    zeit = int(block["timestamp"], 16) if block else 0
    _BLOCKZEIT[nummer] = zeit
    return zeit


# ---------------------------------------------------------------- Tron

def trc20_eingaenge(adresse, waehrung="USDT-TRC20", seit=0, grenze=200):
    """Eingehende TRC-20-Transfers. Die haeufigste Schiene im Handel."""
    t = TOKEN.get(waehrung)
    if not t or t["kette"] != "tron":
        raise KettenFehler("Unbekannter TRC-20-Token: %s" % waehrung)

    url = ("%s/v1/accounts/%s/transactions/trc20?only_to=true&limit=%d"
           % (TRONGRID, urllib.parse.quote(adresse), grenze))
    if seit:
        url += "&min_timestamp=%d" % (seit * 1000)
    antwort = _holen(url)
    if not isinstance(antwort, dict) or not antwort.get("success", True):
        raise KettenFehler("TronGrid lieferte keine brauchbare Antwort")

    eingaenge = []
    for e in antwort.get("data", []):
        info = e.get("token_info") or {}
        if info.get("address") != t["vertrag"]:
            continue                       # fremder Token, nicht zaehlen
        dezimalen = info.get("decimals", t["dezimalen"])
        try:
            betrag = int(e.get("value", "0")) / (10 ** dezimalen)
        except (TypeError, ValueError):
            continue
        if betrag <= 0:
            continue
        eingaenge.append(Eingang(
            "tron", waehrung, betrag,
            int(e.get("block_timestamp", 0)) // 1000,
            e.get("transaction_id", ""), e.get("from")))
    return eingaenge


# ------------------------------------------------------------- Fassade

def eingaenge_lesen(adresse, waehrung, seit=0):
    """Einheitlicher Einstieg. Kette folgt aus der Waehrung."""
    t = TOKEN.get(waehrung)
    if not t:
        raise KettenFehler(
            "Waehrung %s ist nicht hinterlegt. Bekannt: %s"
            % (waehrung, ", ".join(sorted(TOKEN))))
    if t["kette"] == "bitcoin":
        return bitcoin_eingaenge(adresse, seit)
    if t["kette"] == "ethereum":
        return erc20_eingaenge(adresse, waehrung)
    if t["kette"] == "tron":
        return trc20_eingaenge(adresse, waehrung, seit)
    raise KettenFehler("Kette %s nicht unterstuetzt" % t["kette"])
