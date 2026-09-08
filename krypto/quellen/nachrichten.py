# KRYPTO - Nachrichten.
#
# RSS. Kein Schluessel, keine Kosten, kein Konto. Am 08.09.2026
# geprueft: Cointelegraph und Decrypt antworten mit HTTP 200.
#
# Was dieses Modul tut: Schlagzeilen holen und zaehlen, wie oft ein
# Begriff vorkommt. Was es NICHT tut: den Inhalt bewerten. Eine
# Schlagzeile mit dem Wort "Hack" ist nicht dasselbe wie eine mit
# "Rally", aber ein Wortzaehler kann das nicht unterscheiden - und
# ein Sprachmodell, das Schlagzeilen benotet, liefert eine Meinung
# mit Zahlenanstrich. Deshalb: Zaehlung und Titel, mehr nicht.

import html
import re

from krypto.quellen import netz

FEEDS = {
    "cointelegraph": "https://cointelegraph.com/rss",
    "decrypt": "https://decrypt.co/feed",
}

_EINTRAG = re.compile(r"<item\b.*?</item>", re.S | re.I)
_TITEL = re.compile(r"<title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>",
                    re.S | re.I)
_LINK = re.compile(r"<link>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</link>", re.S | re.I)
_DATUM = re.compile(r"<pubDate>(.*?)</pubDate>", re.S | re.I)


def _sauber(t):
    return html.unescape(re.sub(r"<[^>]+>", "", t or "")).strip()


def feed(name, frische=900, grenze=40):
    """Schlagzeilen einer Quelle."""
    url = FEEDS.get(name)
    if url is None:
        raise netz.QuellFehler("unbekannter Feed: %s" % name)
    text, herkunft = netz.holen(url, frische=frische, roh=True)
    raus = []
    for stueck in _EINTRAG.findall(text)[:grenze]:
        t = _TITEL.search(stueck)
        if not t:
            continue
        raus.append({
            "quelle": name,
            "titel": _sauber(t.group(1)),
            "link": _sauber((_LINK.search(stueck) or [None, ""]).group(1)
                            if _LINK.search(stueck) else ""),
            "datum": _sauber((_DATUM.search(stueck) or [None, ""]).group(1)
                             if _DATUM.search(stueck) else ""),
        })
    return raus, herkunft


def alle(frische=900, grenze=40):
    """Alle erreichbaren Feeds. Fehlende werden gemeldet, nicht ersetzt."""
    eintraege, herkunft, fehlend = [], {}, []
    for name in FEEDS:
        try:
            e, h = feed(name, frische=frische, grenze=grenze)
            eintraege.extend(e)
            herkunft[name] = h
        except netz.QuellFehler as f:
            fehlend.append("%s: %s" % (name, f))
    return eintraege, herkunft, fehlend


def erwaehnungen(eintraege, begriffe):
    """Wie oft kommt ein Begriff in den Schlagzeilen vor?

    Wortgrenzen, damit 'SOL' nicht in 'SOLD' oder 'Solution' trifft.
    Das ist der haeufigste Fehler bei solchen Zaehlungen.
    """
    zaehlung = {}
    for b in begriffe:
        if not b:
            continue
        muster = re.compile(r"\b%s\b" % re.escape(str(b)), re.I)
        treffer = [e for e in eintraege if muster.search(e["titel"])]
        zaehlung[str(b).upper()] = {"anzahl": len(treffer),
                                    "titel": [t["titel"] for t in treffer[:3]]}
    return zaehlung
