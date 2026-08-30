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

import ipaddress
import socket
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
import zlib

KENNUNG = ("Mozilla/5.0 (compatible; CITED-Audit/1.0; "
           "+Sichtbarkeitspruefung im Auftrag des Seitenbetreibers)")
ZEITLIMIT = 20
MAX_BYTES = 3 * 1024 * 1024
# Obergrenze fuer die ENTPACKTEN Daten. MAX_BYTES begrenzt nur, was vom
# Netz kommt; drei Megabyte gzip lassen sich zu mehreren Gigabyte
# aufblasen und wuerden den Prozess umbringen.
MAX_ENTPACKT = 24 * 1024 * 1024

SCHEMATA = ("http", "https")


class ZielFehler(ValueError):
    """Das Ziel darf nicht abgerufen werden."""


def _adresse_erlaubt(url):
    """Zeigt die URL auf eine oeffentliche Adresse?

    Ohne diese Pruefung kann jemand als "Domain" 169.254.169.254
    eintragen und sich ueber den Bericht die Zugangsdaten des
    Cloud-Metadatendienstes ausliefern lassen. Das Werkzeug ruft
    fremdbestimmte Adressen ab - damit ist das kein theoretischer Fall,
    sondern der Normalfall.
    """
    host = urllib.parse.urlsplit(url).hostname
    if not host:
        return False, "Kein Hostname in %s" % url
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror as e:
        return False, "Domain nicht auflösbar: %s" % e
    for eintrag in infos:
        adresse = eintrag[4][0]
        try:
            ip = ipaddress.ip_address(adresse)
        except ValueError:
            return False, "Adresse nicht lesbar: %s" % adresse
        if (ip.is_private or ip.is_loopback or ip.is_link_local
                or ip.is_reserved or ip.is_multicast or ip.is_unspecified):
            return False, ("%s zeigt auf die interne Adresse %s - "
                           "solche Ziele werden nicht abgerufen"
                           % (host, adresse))
    return True, None


class _SichereWeiterleitung(urllib.request.HTTPRedirectHandler):
    """Prueft jeden Weiterleitungsschritt erneut.

    Sonst genuegt eine oeffentliche Domain, die auf 169.254.169.254
    weiterleitet, um die Pruefung beim ersten Aufruf zu umgehen.
    """

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if urllib.parse.urlsplit(newurl).scheme not in SCHEMATA:
            raise urllib.error.URLError(
                "Weiterleitung auf ein nicht erlaubtes Schema: %s" % newurl)
        erlaubt, grund = _adresse_erlaubt(newurl)
        if not erlaubt:
            raise urllib.error.URLError("Weiterleitung abgelehnt: %s" % grund)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


_OEFFNER = urllib.request.build_opener(_SichereWeiterleitung())


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


def _entpacken(rohdaten, kodierung, grenze=MAX_ENTPACKT):
    """gzip auspacken, aber nur bis zur Grenze.

    gzip.decompress() kennt keine Obergrenze. Ein Server, der drei
    Megabyte stark redundanter Daten schickt, erzeugt daraus mehrere
    Gigabyte im Speicher und beendet den Prozess - und mit ihm jedes
    parallel laufende Audit.
    """
    if not (kodierung and "gzip" in kodierung.lower()):
        return rohdaten
    try:
        entpacker = zlib.decompressobj(16 + zlib.MAX_WBITS)
        heraus = bytearray()
        for anfang in range(0, len(rohdaten), 65536):
            heraus += entpacker.decompress(
                rohdaten[anfang:anfang + 65536], grenze - len(heraus))
            if len(heraus) >= grenze:
                break
        return bytes(heraus)
    except (OSError, zlib.error):
        return rohdaten


def holen(url, zeitlimit=ZEITLIMIT):
    """Eine Seite holen. Gibt immer eine Antwort zurueck, nie eine Ausnahme."""
    if urllib.parse.urlsplit(url).scheme not in SCHEMATA:
        return Antwort(url, fehler="Nur http und https werden abgerufen")
    erlaubt, grund = _adresse_erlaubt(url)
    if not erlaubt:
        return Antwort(url, fehler=grund)

    anfrage = urllib.request.Request(url, headers={
        "User-Agent": KENNUNG,
        "Accept": "text/html,application/xhtml+xml,text/plain,*/*",
        "Accept-Encoding": "gzip",
        "Accept-Language": "de-CH,de;q=0.9,en;q=0.6",
    })
    start = time.time()
    try:
        with _OEFFNER.open(anfrage, timeout=zeitlimit) as a:
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
    # Ohne diese Pruefung kaeme "file://localhost/etc" durch, und der
    # naechste Aufruf laese eine Datei vom eigenen Server statt einer
    # fremden Website.
    if teile.scheme not in SCHEMATA:
        raise ValueError("Nur http und https werden unterstuetzt: %s"
                         % eingabe)
    if not teile.netloc:
        raise ValueError("Domain nicht lesbar: %s" % eingabe)
    return urllib.parse.urlunsplit((teile.scheme, teile.netloc, "", "", ""))


def unter(basis, pfad):
    return basis.rstrip("/") + "/" + pfad.lstrip("/")
