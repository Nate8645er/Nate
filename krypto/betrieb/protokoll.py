# KRYPTO - Protokoll.
#
# Sieben getrennte Spuren, damit man nachher nicht in einer einzigen
# Datei sucht: system, markt, signale, trades, risiko, api, fehler.
# Jede Zeile ist eine JSON-Zeile - lesbar fuer Menschen, auswertbar
# ohne Parser-Basteln.
#
# Die Schwaerzung ist kein Extra. Ein Handelssystem, das versehentlich
# einen Schluessel protokolliert, hat den Schluessel verloren - Logs
# werden kopiert, gemailt, in Tickets geklebt. Deshalb geht jeder
# Eintrag durch _schwaerzen(), bevor er die Platte sieht.

import datetime
import json
import os
import re

from krypto import konfig

SPUREN = ("system", "markt", "signale", "trades", "risiko", "api", "fehler")

# Namen, deren Werte nie im Klartext auf die Platte gehoeren.
_HEIKEL = re.compile(
    r"(api[_-]?key|apikey|secret|passwor[dt]|passwd|token|identifier|"
    r"credential|authorization|cst|x-security-token|private[_-]?key|"
    r"seed|mnemonic|session)", re.I)

# Muster, die auch ohne Feldnamen nach Geheimnis aussehen.
_MUSTER = (
    (re.compile(r"\b[A-Za-z0-9_-]{32,}\b"), "<GESCHWAERZT:lang>"),
    (re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.]+\b"), "<GESCHWAERZT:mail>"),
)


def _schwaerzen(wert, schluessel=None):
    if schluessel is not None and _HEIKEL.search(str(schluessel)):
        return "<GESCHWAERZT>"
    if isinstance(wert, dict):
        return {k: _schwaerzen(v, k) for k, v in wert.items()}
    if isinstance(wert, (list, tuple)):
        return [_schwaerzen(v) for v in wert]
    if isinstance(wert, str):
        t = wert
        for muster, ersatz in _MUSTER:
            t = muster.sub(ersatz, t)
        return t
    return wert


def _pfad(spur):
    os.makedirs(konfig.LOGS, exist_ok=True)
    tag = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    return os.path.join(konfig.LOGS, "%s-%s.jsonl" % (spur, tag))


def schreiben(spur, ereignis, **felder):
    """Eine Zeile in eine Spur. Gibt den geschriebenen Eintrag zurueck."""
    if spur not in SPUREN:
        raise ValueError("unbekannte Spur: %s" % spur)
    eintrag = {
        "zeit": datetime.datetime.now(datetime.timezone.utc)
                .isoformat(timespec="seconds"),
        "spur": spur,
        "ereignis": ereignis,
    }
    eintrag.update(_schwaerzen(felder))
    try:
        with open(_pfad(spur), "a", encoding="utf-8") as f:
            f.write(json.dumps(eintrag, ensure_ascii=False, default=str) + "\n")
    except OSError:
        # Ein volles Dateisystem darf den Handel nicht zum Absturz
        # bringen - aber es darf auch nicht stumm bleiben.
        print("PROTOKOLL NICHT SCHREIBBAR: %s" % _pfad(spur))
    return eintrag


def system(ereignis, **f):
    return schreiben("system", ereignis, **f)


def markt(ereignis, **f):
    return schreiben("markt", ereignis, **f)


def signal(ereignis, **f):
    return schreiben("signale", ereignis, **f)


def trade(ereignis, **f):
    return schreiben("trades", ereignis, **f)


def risiko(ereignis, **f):
    return schreiben("risiko", ereignis, **f)


def api(ereignis, **f):
    return schreiben("api", ereignis, **f)


def fehler(ereignis, **f):
    return schreiben("fehler", ereignis, **f)


def lesen(spur, tage=1, grenze=200):
    """Die letzten Eintraege einer Spur, neueste zuletzt."""
    heute = datetime.datetime.now(datetime.timezone.utc).date()
    zeilen = []
    for i in range(tage):
        tag = heute - datetime.timedelta(days=i)
        p = os.path.join(konfig.LOGS, "%s-%s.jsonl" % (spur, tag.isoformat()))
        try:
            with open(p, encoding="utf-8") as f:
                for z in f:
                    z = z.strip()
                    if not z:
                        continue
                    try:
                        zeilen.append(json.loads(z))
                    except ValueError:
                        continue
        except OSError:
            continue
    zeilen.sort(key=lambda e: e.get("zeit", ""))
    return zeilen[-grenze:]
