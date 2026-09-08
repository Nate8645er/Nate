# KRYPTO - Blockchains, nur lesend.
#
# Am 08.09.2026 einzeln geprueft. Was geantwortet hat und was nicht,
# steht in der Tabelle unten - unveraendert, auch wenn es Luecken zeigt.
#
#   Ethereum    rpc.mevblocker.io          200
#   Base        mainnet.base.org           200
#   Arbitrum    arb1.arbitrum.io/rpc       200
#   Optimism    mainnet.optimism.io        200
#   BNB         bsc-dataseed.binance.org   200
#   Avalanche   api.avax.network           200
#   Polygon     polygon-bor-rpc.publicnode 200  (polygon-rpc.com: 401)
#   Solana      api.mainnet-beta.solana    200
#   Bitcoin     blockstream.info/api       200  (kein RPC, REST)
#
# Diese Datei kann nicht schreiben. netz.rpc() hat eine Positivliste
# lesender Methoden; alles andere wird abgelehnt, bevor ein Byte das
# Geraet verlaesst.

from krypto.quellen import netz

EVM = {
    "ethereum": "https://rpc.mevblocker.io",
    "base": "https://mainnet.base.org",
    "arbitrum": "https://arb1.arbitrum.io/rpc",
    "optimism": "https://mainnet.optimism.io",
    "bsc": "https://bsc-dataseed.binance.org",
    "avalanche": "https://api.avax.network/ext/bc/C/rpc",
    "polygon": "https://polygon-bor-rpc.publicnode.com",
}
SOLANA = "https://api.mainnet-beta.solana.com"
BITCOIN = "https://blockstream.info/api"

# ERC-20 Transfer(address,address,uint256)
TRANSFER = ("0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef")


def hoehe(kette, frische=30):
    """Aktuelle Blockhoehe. Der einfachste Beweis, dass eine Kette
    ueberhaupt erreichbar ist."""
    k = str(kette).lower()
    if k == "bitcoin":
        text, h = netz.holen("%s/blocks/tip/height" % BITCOIN,
                             frische=frische, roh=True)
        return int(text.strip()), h
    if k == "solana":
        wert, h = netz.rpc(SOLANA, "getSlot", frische=frische)
        return int(wert), h
    if k not in EVM:
        raise netz.QuellFehler("unbekannte Kette: %s" % kette)
    wert, h = netz.rpc(EVM[k], "eth_blockNumber", frische=frische)
    return int(wert, 16), h


def guthaben(kette, adresse, frische=60):
    """Nativguthaben einer Adresse, in der kleinsten Einheit.

    Rueckgabe (menge, einheit, herkunft). Umgerechnet wird bewusst
    nicht - wer Wei mit Ether verwechselt, soll es an der Einheit
    sehen und nicht an einer stillschweigend geteilten Zahl.
    """
    k = str(kette).lower()
    if k == "bitcoin":
        d, h = netz.holen("%s/address/%s" % (BITCOIN, netz.urllib.parse.quote(
            str(adresse), safe="")), frische=frische)
        kette_stat = d.get("chain_stats") or {}
        saldo = (kette_stat.get("funded_txo_sum", 0)
                 - kette_stat.get("spent_txo_sum", 0))
        return saldo, "sat", h
    if k == "solana":
        wert, h = netz.rpc(SOLANA, "getBalance", [str(adresse)],
                           frische=frische)
        menge = wert.get("value") if isinstance(wert, dict) else wert
        return menge, "lamport", h
    if k not in EVM:
        raise netz.QuellFehler("unbekannte Kette: %s" % kette)
    wert, h = netz.rpc(EVM[k], "eth_getBalance", [str(adresse), "latest"],
                       frische=frische)
    return int(wert, 16), "wei", h


def erreichbarkeit():
    """Prueft jede Kette einzeln. Gibt zurueck, was wirklich antwortet.

    Kein Sammelurteil: eine Kette, die nicht antwortet, wird namentlich
    genannt. "On-chain funktioniert" waere sonst eine Behauptung ueber
    neun Systeme, von denen vielleicht sechs laufen.
    """
    stand = {}
    for name in list(EVM) + ["solana", "bitcoin"]:
        try:
            h, herkunft = hoehe(name, frische=0)
            stand[name] = {"ok": True, "hoehe": h,
                           "quelle": herkunft.get("quelle")}
        except (netz.QuellFehler, ValueError, TypeError, KeyError) as e:
            stand[name] = {"ok": False, "grund": str(e)[:110]}
    return stand
