# CITED - Netzschicht.
#
# Alles, was das Werkzeug ueber eine fremde Website weiss, kommt durch
# dieses Modul. Getrennt gehalten, damit die Pruefungen ohne Netz
# testbar sind: die Tests fuettern technik.py mit Antworten, statt
# fremde Server anzurufen.
#
# Grundsaetze:
#   - Wir identifizieren uns ehrlich im User-Agent. Kein Tarnen.
#   - Jede Anfrage hat ein Zeitlimit. Eine haengende Website darf ein
#     Audit nicht blockieren.
#   - Ein Fehler ist ein Ergebnis, kein Absturz: Antwort.fehler wird
#     gesetzt und der Bericht sagt spaeter, was nicht geprueft werden
#     konnte.

import gzip
import socket
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request

KENNUNG = ("Mozilla/5.0 (compatible; CITED-Audit/1.0; "
           "+Sichtbarkeitspruefung im Auftrag des Seitenbetreibers)")
ZEITLIMIT = 20
MAX_BYTES = 3 * 1024 * 1024


class Antwort:
    """Was von einer HTTP-Anfrage uebrig bleibt."""

    def __init__(self, url, status=None, text="", kopf=None, dauer=0.0,
                 endgueltige_url=None, fehler=None):
        self.url = url
        self.status = status
        self.text = text
        self.kopf = kopf or {}
        self.dauer = dauer
        self.endgueltige_url = endgueltige_url or url
        self.fehler = fehler

    @property
    def da(self):
        return self.fehler is None and self.status == 200

    def __repr__(self):
        return "<Antwort %s %s%s>" % (
            self.url, self.status,
            " FEHLER: %s" % self.fehler if self.fehler else "")


def _entpacken(rohdaten, kodierung):
    if kodierung and "gzip" in kodierung.lower():
        try:
            return gzip.decompress(rohdaten)
        except OSError:
            return rohdaten
    return rohdaten


def holen(url, zeitlimit=ZEITLIMIT):
    """Eine Seite holen. Gibt immer eine Antwort zurueck, nie eine Ausnahme."""
    anfrage = urllib.request.Request(url, headers={
        "User-Agent": KENNUNG,
        "Accept": "text/html,application/xhtml+xml,text/plain,*/*",
        "Accept-Encoding": "gzip",
        "Accept-Language": "de-CH,de;q=0.9,en;q=0.6",
    })
    start = time.time()
    try:
        with urllib.request.urlopen(anfrage, timeout=zeitlimit) as a:
            roh = a.read(MAX_BYTES)
            roh = _entpacken(roh, a.headers.get("Content-Encoding"))
            zeichensatz = a.headers.get_content_charset() or "utf-8"
            return Antwort(
                url, a.status, roh.decode(zeichensatz, errors="replace"),
                dict(a.headers), time.time() - start, a.geturl())
    except urllib.error.HTTPError as e:
        # 404 auf /llms.txt ist ein Befund, kein Unfall - deshalb mit
        # Statuscode zurueck statt als Fehler.
        try:
            text = e.read(MAX_BYTES).decode("utf-8", errors="replace")
        except Exception:
            text = ""
        return Antwort(url, e.code, text, dict(e.headers or {}),
                       time.time() - start, url)
    except urllib.error.URLError as e:
        return Antwort(url, fehler=_klartext(e.reason),
                       dauer=time.time() - start)
    except (socket.timeout, TimeoutError):
        return Antwort(url, fehler="Zeitlimit von %ds ueberschritten"
                       % zeitlimit, dauer=time.time() - start)
    except (ssl.SSLError, ValueError, OSError) as e:
        return Antwort(url, fehler=_klartext(e), dauer=time.time() - start)


def _klartext(grund):
    text = str(grund)
    if "Name or service not known" in text or "nodename" in text:
        return "Domain nicht auffindbar (DNS)"
    if "certificate" in text.lower():
        return "TLS-Zertifikat nicht gueltig: %s" % text
    if "Connection refused" in text:
        return "Server verweigert die Verbindung"
    return text


def domain_normalisieren(eingabe):
    """"cited.works", "https://cited.works/preise" -> "https://cited.works"."""
    eingabe = (eingabe or "").strip()
    if not eingabe:
        raise ValueError("Keine Domain angegeben")
    if "://" not in eingabe:
        eingabe = "https://" + eingabe
    teile = urllib.parse.urlsplit(eingabe)
    if not teile.netloc:
        raise ValueError("Domain nicht lesbar: %s" % eingabe)
    return urllib.parse.urlunsplit((teile.scheme, teile.netloc, "", "", ""))


def unter(basis, pfad):
    return basis.rstrip("/") + "/" + pfad.lstrip("/")
