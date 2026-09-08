# KRYPTO - gemeinsame Netzschicht fuer alle Quellen.
#
# Eine Stelle fuer alles, was mit fremden Servern zu tun hat: Puffer,
# Drosselung, Zeitlimit, Herkunftsangabe. Jede Antwort traegt mit, WOHER
# sie kommt und WIE ALT sie ist - ohne diese zwei Angaben ist eine Zahl
# in diesem System wertlos.
#
# Nur GET. Es gibt in diesem Modul keine Moeglichkeit, etwas zu senden,
# das eine Zustandsaenderung ausloest. Einzige Ausnahme ist der
# JSON-RPC-Aufruf an eine Blockchain-Node - der ist technisch ein POST,
# ruft aber ausschliesslich lesende Methoden auf (siehe ketten.py).

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

from krypto import konfig
from krypto.betrieb import protokoll

PUFFER = os.path.join(konfig.ZUSTAND, "quellen-puffer.json")
KENNUNG = konfig.KENNUNG


class QuellFehler(Exception):
    """Quelle nicht erreichbar oder Antwort unbrauchbar.

    Es gibt bewusst keinen Ersatzwert. Wer diesen Fehler faengt, muss
    DATA_INCOMPLETE melden, nicht schaetzen.
    """


def _puffer_laden():
    try:
        with open(PUFFER, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def _puffer_sichern(d):
    try:
        os.makedirs(konfig.ZUSTAND, exist_ok=True)
        vor = PUFFER + ".neu"
        with open(vor, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, default=str)
        os.replace(vor, PUFFER)
    except OSError:
        pass


def holen(url, frische=300, kopf=None, roh=False, versuche=3):
    """GET mit Puffer. Gibt (daten, herkunft) zurueck.

    herkunft = {"quelle": <netz|puffer|puffer-veraltet>, "alter_s": int,
                "url": <url>, "zeit": <unix>}
    """
    puffer = _puffer_laden()
    jetzt = time.time()
    schluessel = url
    alt = puffer.get(schluessel)
    if alt and (jetzt - alt.get("zeit", 0)) < frische:
        return alt["daten"], {"quelle": "puffer",
                              "alter_s": int(jetzt - alt["zeit"]),
                              "url": url, "zeit": alt["zeit"]}

    kopfzeilen = {"User-Agent": KENNUNG,
                  "Accept": "*/*" if roh else "application/json"}
    kopfzeilen.update(kopf or {})
    letzter = None
    for i in range(versuche):
        try:
            a = urllib.request.Request(url, headers=kopfzeilen)
            with urllib.request.urlopen(a, timeout=konfig.HTTP_TIMEOUT) as r:
                text = r.read().decode("utf-8", errors="replace")
            daten = text if roh else json.loads(text)
            puffer[schluessel] = {"zeit": jetzt, "daten": daten}
            _puffer_sichern(puffer)
            protokoll.api("quelle-ok", url=url, status=200, versuch=i + 1)
            return daten, {"quelle": "netz", "alter_s": 0, "url": url,
                           "zeit": jetzt}
        except urllib.error.HTTPError as e:
            letzter = "HTTP %s" % e.code
            protokoll.api("quelle-fehler", url=url, status=e.code,
                          versuch=i + 1)
            if e.code == 429:
                time.sleep(10 * (i + 1))
                continue
            break            # 401/403/404 werden durch Warten nicht besser
        except (urllib.error.URLError, OSError, ValueError) as e:
            letzter = type(e).__name__
            protokoll.api("quelle-fehler", url=url, grund=letzter,
                          versuch=i + 1)
            time.sleep(2 * (i + 1))

    if alt:
        return alt["daten"], {"quelle": "puffer-veraltet",
                              "alter_s": int(jetzt - alt["zeit"]),
                              "url": url, "zeit": alt["zeit"]}
    raise QuellFehler("%s: %s" % (url, letzter))


def rpc(url, methode, parameter=None, frische=30):
    """Lesender JSON-RPC-Aufruf an eine Blockchain-Node.

    Die Methodenliste ist eine Positivliste. Alles, was eine
    Transaktion senden oder ein Konto entsperren koennte, ist hier
    nicht aufgefuehrt und wird abgelehnt - nicht weil ein Angreifer
    das ausnutzen wuerde, sondern damit ein Tippfehler in diesem
    Projekt niemals eine Kette beschreiben kann.
    """
    ERLAUBT = {
        "eth_blockNumber", "eth_getBalance", "eth_getCode", "eth_call",
        "eth_getLogs", "eth_getTransactionByHash", "eth_getBlockByNumber",
        "eth_getTransactionReceipt", "eth_chainId", "eth_gasPrice",
        "eth_getTransactionCount", "net_version",
        "getSlot", "getBalance", "getAccountInfo", "getSignaturesForAddress",
        "getTokenSupply", "getTokenAccountsByOwner", "getTransaction",
    }
    if methode not in ERLAUBT:
        raise QuellFehler(
            "RPC-Methode %r ist nicht auf der Leseliste. Dieses System "
            "schreibt nicht auf eine Blockchain." % methode)

    koerper = json.dumps({"jsonrpc": "2.0", "id": 1, "method": methode,
                          "params": parameter or []}).encode("utf-8")
    schluessel = "%s#%s#%s" % (url, methode, parameter)
    puffer = _puffer_laden()
    jetzt = time.time()
    alt = puffer.get(schluessel)
    if alt and (jetzt - alt.get("zeit", 0)) < frische:
        return alt["daten"], {"quelle": "puffer",
                              "alter_s": int(jetzt - alt["zeit"]), "url": url}

    try:
        a = urllib.request.Request(url, data=koerper, headers={
            "Content-Type": "application/json", "User-Agent": KENNUNG})
        with urllib.request.urlopen(a, timeout=konfig.HTTP_TIMEOUT) as r:
            antwort = json.loads(r.read().decode("utf-8"))
    except (urllib.error.HTTPError, urllib.error.URLError,
            OSError, ValueError) as e:
        protokoll.api("rpc-fehler", url=url, methode=methode,
                      grund=type(e).__name__)
        raise QuellFehler("RPC %s an %s: %s" % (methode, url,
                                                type(e).__name__))
    if "error" in antwort:
        raise QuellFehler("RPC %s: %s" % (methode,
                                          str(antwort["error"])[:120]))
    puffer[schluessel] = {"zeit": jetzt, "daten": antwort.get("result")}
    _puffer_sichern(puffer)
    protokoll.api("rpc-ok", url=url, methode=methode)
    return antwort.get("result"), {"quelle": "netz", "alter_s": 0, "url": url}
