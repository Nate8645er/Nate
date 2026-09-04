# SETTLED - Kurse.
#
# Fuer die Buchhaltung zaehlt nicht, was eine Muenze heute wert ist,
# sondern was sie am Tag des Zahlungseingangs wert war. Genau diese Zahl
# liefert dieses Modul - und sie wird gepuffert, weil ein Kurs von
# gestern sich nicht mehr aendert.
#
# Quelle: CoinGecko, freie Stufe, ohne Schluessel. Der Tageskurs ist die
# uebliche Grundlage; wer taggenau zur Sekunde bewerten muss, braucht
# eine kostenpflichtige Quelle. Das steht im Bericht, statt es zu
# verschweigen.

import datetime
import json
import os
import time
import urllib.error
import urllib.request

BASIS = "https://api.coingecko.com/api/v3"
KENNUNG = "SETTLED/0.1 (Zahlungsabgleich, nur lesend)"
PUFFER = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      "kurs-puffer.json")


class KursFehler(Exception):
    """Kurs nicht ermittelbar."""


def _laden():
    try:
        with open(PUFFER, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def _sichern(daten):
    try:
        with open(PUFFER, "w", encoding="utf-8") as f:
            json.dump(daten, f, ensure_ascii=False, indent=1, sort_keys=True)
    except OSError:
        pass


def _holen(url, versuche=3):
    for versuch in range(versuche):
        try:
            a = urllib.request.Request(url, headers={"User-Agent": KENNUNG})
            with urllib.request.urlopen(a, timeout=30) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 429:            # freie Stufe drosselt hart
                time.sleep(8 * (versuch + 1))
                continue
            if e.code == 401 and "/history?" in url:
                # Geprueft: die freie Stufe gibt historische Tageskurse
                # nur fuer die letzten rund 365 Tage heraus und
                # antwortet darueber hinaus mit 401. Das ist keine
                # Stoerung, sondern eine Grenze - und sie gehoert so in
                # den Bericht, damit niemand eine fehlende Bewertung
                # fuer einen Fehler haelt.
                raise KursFehler(
                    "Tageskurs aelter als rund ein Jahr - die freie "
                    "CoinGecko-Stufe gibt ihn nicht heraus. Fuer die "
                    "Bewertung aelterer Zahlungen braucht es eine "
                    "kostenpflichtige Kursquelle.")
            raise KursFehler("HTTP %s bei %s" % (e.code, url))
        except (urllib.error.URLError, OSError, ValueError) as e:
            time.sleep(2 * (versuch + 1))
            letzter = e
    raise KursFehler("CoinGecko nicht erreichbar: %s" % locals().get("letzter"))


def tageskurs(coingecko_id, zeit, fiat="chf"):
    """Kurs einer Muenze am Tag des Zeitstempels, in Fiat.

    zeit ist eine Unix-Sekunde. Bewertet wird UTC-Datum - das ist die
    Konvention, die auch die Kettendaten verwenden, und Mischen waere
    schlimmer als eine klar benannte Konvention.
    """
    tag = datetime.datetime.fromtimestamp(
        zeit, datetime.timezone.utc).strftime("%d-%m-%Y")
    schluessel = "%s|%s|%s" % (coingecko_id, tag, fiat.lower())

    puffer = _laden()
    if schluessel in puffer:
        return puffer[schluessel]

    daten = _holen("%s/coins/%s/history?date=%s&localization=false"
                   % (BASIS, coingecko_id, tag))
    preise = ((daten.get("market_data") or {}).get("current_price") or {})
    if fiat.lower() not in preise:
        raise KursFehler("Kein %s-Kurs fuer %s am %s"
                         % (fiat.upper(), coingecko_id, tag))
    kurs = float(preise[fiat.lower()])
    puffer[schluessel] = kurs
    _sichern(puffer)
    return kurs


def jetzt(ids, fiat="chf"):
    """Aktuelle Kurse. Nicht fuer die Buchhaltung - nur zur Anzeige."""
    daten = _holen("%s/simple/price?ids=%s&vs_currencies=%s"
                   % (BASIS, ",".join(ids), fiat.lower()))
    return {k: v.get(fiat.lower()) for k, v in daten.items()}
