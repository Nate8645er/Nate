#!/usr/bin/env python3
"""
seite.py - liest eine Webseite so, wie ein Pruefer sie liest.

WARUM DAS AUSGELIEFERTE HTML UND NICHT DER BROWSER-BAUM

Wer eine Seite beanstandet - eine Aufsichtsbehoerde, ein Verband, ein
Klaeger mit einem automatischen Scanner - liest das HTML, das der Server
schickt. Nicht den Baum, den Javascript daraus im Browser macht.

Das ist der ganze Grund, warum Overlay-Widgets vor Gericht durchfallen.
Ein Overlay laedt nach und biegt den fertigen Baum zurecht. Auf dem
Bildschirm sieht es dann besser aus. In der Antwort des Servers steht
unveraendert derselbe Fehler. Die US-Handelsbehoerde hat einen grossen
Anbieter im April 2025 zu einer Million Dollar verurteilt, weil er das
Gegenteil versprochen hatte, und rund ein Viertel der Klagen 2024 traf
Seiten, auf denen so ein Widget bereits lief. Es schuetzt nicht, es
markiert.

Also liest dieses Werkzeug genau das, was der Server ausliefert.

WAS ES BEWUSST NICHT TUT

Es behauptet nie, eine Seite sei rechtskonform. Das kann kein Programm
feststellen. Automatisch pruefbar ist ein Teil der Kriterien - der Teil,
der die grosse Masse der Fehler ausmacht. Der Rest braucht einen Menschen.
Wer etwas anderes verspricht, verkauft dieselbe Luege wie die Overlays.
"""

import gzip
import io
import re
import urllib.request
import urllib.error
from urllib.parse import urljoin, urlparse

import farbe
from befund import Befund, Bericht

KOPFZEILEN = {
    # Ehrlich sagen, wer da anklopft. Ein Werkzeug, das sich als Browser
    # tarnt, um an Inhalte zu kommen, faengt sein Geschaeft mit einer
    # Taeuschung an - und wird zu Recht gesperrt.
    "User-Agent": "Curbcut/0.1 (Barrierefreiheits-Pruefung; +https://curbcut.com/bot)",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Encoding": "gzip",
}

GRENZE = 5_000_000     # 5 MB reichen fuer jede ehrliche Seite


class NichtErreichbar(Exception):
    """Die Seite konnte nicht gelesen werden - mit einem Grund im Klartext.

    Wichtig fuer den kostenlosen Scan: Wer eine Adresse eingibt und einen
    Programmabsturz sieht, kommt nicht wieder. Wer liest "die Seite hat
    unsere Anfrage abgewiesen", versteht, dass es nicht an ihm lag.
    """


def holen(url, zeit=25):
    """Holt eine Seite. Gibt (text, endgueltige_url)."""
    anfrage = urllib.request.Request(url, headers=KOPFZEILEN)
    try:
        with urllib.request.urlopen(anfrage, timeout=zeit) as antwort:
            roh = antwort.read(GRENZE)
            if antwort.headers.get("Content-Encoding") == "gzip":
                try:
                    roh = gzip.GzipFile(fileobj=io.BytesIO(roh)).read()
                except OSError:
                    pass          # war doch nicht gepackt
            art = antwort.headers.get_content_charset() or "utf-8"
            return roh.decode(art, "replace"), antwort.geturl()
    except urllib.error.HTTPError as e:
        if e.code in (401, 403):
            raise NichtErreichbar(
                f"Der Server hat die Anfrage abgewiesen (Code {e.code}). "
                f"Viele grosse Seiten sperren automatische Zugriffe. Das "
                f"sagt nichts ueber die Barrierefreiheit aus."
            ) from e
        if e.code == 404:
            raise NichtErreichbar("Unter dieser Adresse liegt keine Seite (404).") from e
        raise NichtErreichbar(f"Der Server antwortete mit Code {e.code}.") from e
    except urllib.error.URLError as e:
        grund = getattr(e, "reason", e)
        raise NichtErreichbar(
            f"Keine Verbindung zu {urlparse(url).netloc or url}: {grund}"
        ) from e
    except TimeoutError:
        raise NichtErreichbar(
            f"Die Seite hat nach {zeit} Sekunden nicht geantwortet."
        ) from None
    except Exception as e:
        raise NichtErreichbar(f"Unerwarteter Fehler beim Abruf: {e}") from e


# ------------------------------------------------------------------ HTML

KOMMENTAR = re.compile(r"<!--.*?-->", re.DOTALL)
SKRIPT = re.compile(r"<script\b[^>]*>.*?</script>", re.DOTALL | re.IGNORECASE)
STILBLOCK = re.compile(r"<style\b[^>]*>(.*?)</style>", re.DOTALL | re.IGNORECASE)


def _zeilentreu(text, muster):
    """Loescht Treffer, behaelt jede Zeilenumbruchposition.

    Ein Befund auf der falschen Zeile ist schlimmer als gar keiner: Er
    kostet den Betreiber Zeit und das Werkzeug sein Vertrauen.
    """
    return muster.sub(lambda m: "".join("\n" if z == "\n" else " "
                                        for z in m.group(0)), text)


VERKNUEPFUNG = re.compile(
    r"""<link\b[^>]*\brel\s*=\s*["']?stylesheet["']?[^>]*>""", re.IGNORECASE)
ADRESSE = re.compile(r"""\bhref\s*=\s*["']([^"']+)["']""", re.IGNORECASE)

CSS_GRENZE = 2_000_000
CSS_HOECHSTENS = 6      # mehr Dateien bringen kaum neue Farben, kosten aber Zeit


def stile_nachladen(html, basis, zeit=10):
    """Holt die verknuepften Stylesheets.

    Ohne das findet die Kontrastpruefung fast nichts. Ein Test ueber 18
    Schweizer Seiten fand Kontrastfehler nur auf 22 Prozent - waehrend die
    WebAIM-Million-Auswertung 83,9 Prozent misst. Der Unterschied war
    nicht die Realitaet, sondern die eigene Blindheit: Farben stehen fast
    nie im HTML, sie stehen in der verknuepften CSS-Datei.

    Ein Werkzeug, das den haeufigsten Fehler uebersieht und trotzdem
    "geprueft" meldet, ist schlimmer als keines.
    """
    aus = []
    for m in list(VERKNUEPFUNG.finditer(html))[:CSS_HOECHSTENS]:
        a = ADRESSE.search(m.group(0))
        if not a:
            continue
        ziel = urljoin(basis, a.group(1))
        if not ziel.startswith(("http://", "https://")):
            continue
        try:
            anfrage = urllib.request.Request(ziel, headers={
                **KOPFZEILEN, "Accept": "text/css,*/*;q=0.1"})
            with urllib.request.urlopen(anfrage, timeout=zeit) as antwort:
                roh = antwort.read(CSS_GRENZE)
                if antwort.headers.get("Content-Encoding") == "gzip":
                    try:
                        roh = gzip.GzipFile(fileobj=io.BytesIO(roh)).read()
                    except OSError:
                        pass
                aus.append(roh.decode("utf-8", "replace"))
        except Exception:
            continue      # eine fehlende Stildatei darf die Pruefung nicht kippen
    return aus


class Seite:
    """Original und Arbeitsfassung zeichengenau nebeneinander."""

    def __init__(self, quelle, url="", extern=True):
        self.original = quelle
        self.url = url
        t = _zeilentreu(quelle, KOMMENTAR)
        self.arbeit = _zeilentreu(t, SKRIPT)
        self.stile = [m.group(1) for m in STILBLOCK.finditer(quelle)]
        self.externe_stile = 0
        if extern and url:
            geholt = stile_nachladen(quelle, url)
            self.externe_stile = len(geholt)
            self.stile.extend(geholt)

    def zeile(self, pos):
        return self.arbeit.count("\n", 0, pos) + 1

    def zitat(self, start, ende, laenge=140):
        roh = self.original[start:min(ende, start + laenge * 3)]
        roh = re.sub(r"\s+", " ", roh).strip()
        return roh[:laenge] + ("..." if len(roh) > laenge else "")


def attribute(roh):
    d = {}
    for m in re.finditer(
        r"""([a-zA-Z_:][-a-zA-Z0-9_:.]*)\s*(?:=\s*("([^"]*)"|'([^']*)'|([^\s"'>]+)))?""",
        roh,
    ):
        wert = next((g for g in (m.group(3), m.group(4), m.group(5))
                     if g is not None), "")
        d[m.group(1).lower()] = wert
    return d


def hat_text(inhalt):
    ohne = re.sub(r"<[^>]*>", "", inhalt)
    return bool(ohne.replace("&nbsp;", " ").strip())


def paare(t, tag):
    """<tag ...>inhalt</tag>, verschachtelungsfest."""
    for m in re.finditer(rf"<{tag}\b([^>]*)>", t, re.IGNORECASE):
        tiefe = 1
        ende = None
        for n in re.finditer(rf"<(/?){tag}\b[^>]*>", t[m.end():], re.IGNORECASE):
            tiefe += -1 if n.group(1) else 1
            if tiefe == 0:
                ende = m.end() + n.start()
                break
        if ende is not None:
            yield m, t[m.end():ende]


# ------------------------------------------------------------------ CSS

REGEL = re.compile(r"([^{}]+)\{([^{}]*)\}")


def stilregeln(css):
    """Sehr flache CSS-Auswertung: Selektor -> {eigenschaft: wert}.

    Bewusst flach. Eine vollstaendige Kaskade braeuchte einen Browser -
    Vererbung, Spezifitaet, Medienabfragen, benutzerdefinierte
    Eigenschaften. Was hier nicht sicher zugeordnet werden kann, wird
    NICHT gemeldet. Lieber ein Fehler weniger gefunden als einer
    behauptet, den es nicht gibt.
    """
    aus = {}
    css = re.sub(r"/\*.*?\*/", " ", css, flags=re.DOTALL)
    css = re.sub(r"@media[^{]*\{", " ", css)      # Medienabfragen flach oeffnen
    for m in REGEL.finditer(css):
        eigen = {}
        for stueck in m.group(2).split(";"):
            if ":" not in stueck:
                continue
            k, _, v = stueck.partition(":")
            eigen[k.strip().lower()] = v.strip().rstrip("!important").strip()
        if not eigen:
            continue
        for sel in m.group(1).split(","):
            sel = sel.strip().lower()
            if sel:
                aus.setdefault(sel, {}).update(eigen)
    return aus


def _groesse(wert):
    """CSS-Laenge in Pixel. Nur was sicher umrechenbar ist."""
    if not wert:
        return None
    w = wert.strip().lower()
    m = re.match(r"^([\d.]+)(px|pt|rem|em)?$", w)
    if not m:
        return None
    try:
        z = float(m.group(1))
    except ValueError:
        return None
    art = m.group(2) or "px"
    return {"px": z, "pt": z * 4 / 3, "rem": z * 16, "em": z * 16}[art]
