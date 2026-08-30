# CITED - technische Auffindbarkeit fuer KI-Systeme.
#
# Dieses Modul beantwortet eine Frage: Koennte ein KI-System diese
# Website ueberhaupt lesen und daraus zitieren?
#
# Das ist der Teil des Audits, der vollstaendig maschinell pruefbar und
# jederzeit wiederholbar ist. Er wird im Bericht streng getrennt von den
# tatsaechlichen Antworten der KI-Systeme, die ein Mensch erfassen muss.
# Wer beides vermischt, verkauft Schaetzungen als Messungen.
#
# Jeder Befund traegt eine konkrete Massnahme. Ein Befund ohne Massnahme
# ist fuer den Kunden wertlos.

import html.parser
import json
import re

import netz

# Die Zugriffe, auf die es 2026 ankommt. Getrennt nach Zweck, weil die
# Entscheidung eine andere ist: Trainings-Crawler darf man guten
# Gewissens sperren, Antwort-Crawler zu sperren heisst unsichtbar sein.
CRAWLER = [
    # (Kennung, Betreiber, Zweck, wichtig)
    ("OAI-SearchBot",   "OpenAI",     "antwort",  True),
    ("ChatGPT-User",    "OpenAI",     "antwort",  True),
    ("GPTBot",          "OpenAI",     "training", False),
    ("ClaudeBot",       "Anthropic",  "training", False),
    ("Claude-User",     "Anthropic",  "antwort",  True),
    ("Claude-SearchBot", "Anthropic", "antwort",  True),
    ("PerplexityBot",   "Perplexity", "antwort",  True),
    ("Perplexity-User", "Perplexity", "antwort",  True),
    ("Google-Extended", "Google",     "antwort",  True),
    ("Applebot-Extended", "Apple",    "training", False),
    ("Bytespider",      "ByteDance",  "training", False),
    ("CCBot",           "Common Crawl", "training", False),
]

WICHTIGE_TYPEN = ["Organization", "LocalBusiness", "ProfessionalService",
                  "FAQPage", "Service", "Product", "Article", "Person",
                  "WebSite", "BreadcrumbList"]


# ------------------------------------------------------------ robots.txt

def robots_lesen(text):
    """robots.txt in {Kennung: [Regeln]} zerlegen.

    Bewusst einfach gehalten und nur fuer die Frage benutzt "ist der
    Pfad / gesperrt". Eine vollstaendige robots-Implementierung ist hier
    nicht noetig und wuerde falsche Genauigkeit vortaeuschen.
    """
    gruppen = {}
    aktuell = []
    letzte_zeile_war_agent = False
    for zeile in text.splitlines():
        zeile = zeile.split("#", 1)[0].strip()
        if not zeile or ":" not in zeile:
            continue
        feld, wert = zeile.split(":", 1)
        feld = feld.strip().lower()
        wert = wert.strip()
        if feld == "user-agent":
            if not letzte_zeile_war_agent:
                aktuell = []
            aktuell.append(wert.lower())
            for a in aktuell:
                gruppen.setdefault(a, [])
            letzte_zeile_war_agent = True
        elif feld in ("disallow", "allow"):
            letzte_zeile_war_agent = False
            for a in aktuell:
                gruppen.setdefault(a, []).append((feld, wert))
        else:
            letzte_zeile_war_agent = False
    return gruppen


def gesperrt(gruppen, kennung, pfad="/"):
    """Ist der Pfad fuer diese Kennung gesperrt?

    Reihenfolge nach Standard: die spezifischste Gruppe gewinnt, sonst
    die Sammelgruppe "*". Innerhalb einer Gruppe gewinnt die laengste
    passende Regel; bei Gleichstand gewinnt Allow.
    """
    k = kennung.lower()
    regeln = gruppen.get(k)
    if regeln is None:
        regeln = gruppen.get("*")
    if regeln is None:
        return False
    treffer = None
    for art, muster in regeln:
        if muster == "":
            # "Disallow:" ohne Wert heisst ausdruecklich: alles erlaubt.
            if art == "disallow":
                continue
            muster = "/"
        if pfad.startswith(muster.rstrip("*")):
            laenge = len(muster)
            if treffer is None or laenge > treffer[1] or (
                    laenge == treffer[1] and art == "allow"):
                treffer = (art, laenge)
    return treffer is not None and treffer[0] == "disallow"


# ----------------------------------------------------------- HTML lesen

class _Leser(html.parser.HTMLParser):
    """Zieht aus einer Seite genau das heraus, was ein KI-System sieht."""

    UNSICHTBAR = {"script", "style", "noscript", "template", "svg"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.titel = None
        self._in_titel = False
        self.beschreibung = None
        self.sprache = None
        self.kanonisch = None
        self.h1 = []
        self.h2 = []
        self._in_ueberschrift = None
        self.jsonld_roh = []
        self._in_jsonld = False
        self.text_teile = []
        self._stapel = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self._stapel.append(tag)
        if tag == "title":
            self._in_titel = True
        elif tag == "html" and a.get("lang"):
            self.sprache = a["lang"]
        elif tag == "meta":
            name = (a.get("name") or "").lower()
            if name == "description":
                self.beschreibung = a.get("content")
        elif tag == "link" and "canonical" in (a.get("rel") or "").lower():
            self.kanonisch = a.get("href")
        elif tag in ("h1", "h2"):
            self._in_ueberschrift = tag
            getattr(self, tag).append("")
        elif tag == "script":
            art = (a.get("type") or "").lower()
            if art == "application/ld+json":
                self._in_jsonld = True
                self.jsonld_roh.append("")

    def handle_endtag(self, tag):
        if self._stapel and tag in self._stapel:
            while self._stapel and self._stapel.pop() != tag:
                pass
        if tag == "title":
            self._in_titel = False
        if tag in ("h1", "h2"):
            self._in_ueberschrift = None
        if tag == "script":
            self._in_jsonld = False

    def handle_data(self, daten):
        if self._in_titel:
            self.titel = (self.titel or "") + daten
        if self._in_jsonld and self.jsonld_roh:
            self.jsonld_roh[-1] += daten
        if self._in_ueberschrift:
            liste = getattr(self, self._in_ueberschrift)
            if liste:
                liste[-1] += daten
        if not (set(self._stapel) & self.UNSICHTBAR):
            gestrafft = daten.strip()
            if gestrafft:
                self.text_teile.append(gestrafft)

    @property
    def sichtbarer_text(self):
        return " ".join(self.text_teile)


def jsonld_typen(rohblöcke):
    """Alle @type-Werte aus den JSON-LD-Bloecken einsammeln."""
    typen = []
    kaputt = 0
    for roh in rohblöcke:
        try:
            daten = json.loads(roh)
        except (ValueError, TypeError):
            kaputt += 1
            continue
        for eintrag in _abflachen(daten):
            t = eintrag.get("@type")
            if isinstance(t, list):
                typen.extend(str(x) for x in t)
            elif t:
                typen.append(str(t))
    return sorted(set(typen)), kaputt


def _ist_organisation(typ):
    """Zaehlt der Typ als "die Firma ist maschinenlesbar beschrieben"?

    schema.org kennt Dutzende Unterarten von Organization und
    LocalBusiness - NewsMediaOrganization, Dentist, Attorney,
    AccountingService und so fort. Wer nur auf die drei Oberbegriffe
    prueft, meldet einer sauber ausgezeichneten Zahnarztpraxis einen
    Mangel, den sie nicht hat. Ein falscher Befund im Audit kostet mehr
    Vertrauen, als ein uebersehener Befund je einbringt.
    """
    t = str(typ)
    if t.endswith("Organization") or t.endswith("Business"):
        return True
    # Unterarten, deren Name den Oberbegriff nicht enthaelt.
    return t in ("ProfessionalService", "Corporation", "Dentist",
                 "Physician", "Attorney", "LegalService",
                 "AccountingService", "MedicalClinic", "RealEstateAgent",
                 "InsuranceAgency", "MovingCompany", "HousePainter",
                 "Plumber", "Electrician", "Locksmith", "DrivingSchool",
                 "Restaurant", "Hotel", "TravelAgency", "Physiotherapy")


def _abflachen(daten):
    """Verschachteltes JSON-LD in eine flache Liste von Objekten."""
    if isinstance(daten, list):
        for d in daten:
            yield from _abflachen(d)
    elif isinstance(daten, dict):
        yield daten
        for schluessel in ("@graph", "mainEntity", "itemListElement"):
            if schluessel in daten:
                yield from _abflachen(daten[schluessel])


# --------------------------------------------------------------- Befunde

class Befund:
    """Ein Prueffeld: Ergebnis, Gewicht und was der Kunde tun soll."""

    def __init__(self, feld, bestanden, aussage, massnahme=None, gewicht=1,
                 belege=None):
        self.feld = feld
        self.bestanden = bestanden        # True / False / None = ungeprueft
        self.aussage = aussage
        self.massnahme = massnahme
        self.gewicht = gewicht
        self.belege = belege or []

    def als_daten(self):
        return {"feld": self.feld, "bestanden": self.bestanden,
                "aussage": self.aussage, "massnahme": self.massnahme,
                "gewicht": self.gewicht, "belege": self.belege}


def pruefen(basis, holen=netz.holen):
    """Alle technischen Pruefungen ausfuehren.

    `holen` ist einspeisbar, damit die Tests ohne Netz laufen.
    """
    befunde = []
    startseite = holen(basis)

    # --- Erreichbarkeit -------------------------------------------------
    if startseite.fehler:
        befunde.append(Befund(
            "Erreichbarkeit", False,
            "Die Startseite war nicht abrufbar: %s" % startseite.fehler,
            "Zuerst die Erreichbarkeit klaeren. Ohne erreichbare Seite "
            "ist keine weitere Pruefung moeglich.", gewicht=5))
        return befunde, None
    if startseite.status != 200:
        befunde.append(Befund(
            "Erreichbarkeit", False,
            "Die Startseite antwortet mit Status %s." % startseite.status,
            "Server-Antwort auf 200 bringen.", gewicht=5))
        return befunde, None

    befunde.append(Befund(
        "Erreichbarkeit", True,
        "Startseite erreichbar in %.2f Sekunden." % startseite.dauer,
        None if startseite.dauer < 3 else
        "Ladezeit unter 3 Sekunden bringen - langsame Server werden von "
        "Antwort-Crawlern haeufiger abgebrochen.",
        belege=[startseite.endgueltige_url]))

    leser = _Leser()
    try:
        leser.feed(startseite.text)
    except Exception:
        pass

    # --- robots.txt -----------------------------------------------------
    r = holen(netz.unter(basis, "robots.txt"))
    if r.status == 200 and r.text.strip():
        gruppen = robots_lesen(r.text)
        blockiert = []
        for kennung, betreiber, zweck, wichtig in CRAWLER:
            if gesperrt(gruppen, kennung) and wichtig:
                blockiert.append("%s (%s)" % (kennung, betreiber))
        if blockiert:
            befunde.append(Befund(
                "Crawler-Zugang", False,
                "robots.txt sperrt %d Antwort-Crawler aus: %s."
                % (len(blockiert), ", ".join(blockiert)),
                "Diese Kennungen in robots.txt freigeben. Sie holen die "
                "Seite im Moment der Nutzerfrage - wer sie sperrt, kann "
                "in der Antwort nicht genannt werden. Trainings-Crawler "
                "duerfen gesperrt bleiben.",
                gewicht=5, belege=[r.url] + blockiert))
        else:
            befunde.append(Befund(
                "Crawler-Zugang", True,
                "robots.txt sperrt keinen der Antwort-Crawler aus.",
                None, gewicht=5, belege=[r.url]))
    elif r.status == 404:
        befunde.append(Befund(
            "Crawler-Zugang", True,
            "Keine robots.txt vorhanden - damit ist nichts gesperrt.",
            "Unkritisch. Eine robots.txt mit ausdruecklicher Freigabe "
            "waere dennoch sauberer.", gewicht=5))
    else:
        befunde.append(Befund(
            "Crawler-Zugang", None,
            "robots.txt nicht pruefbar (Status %s%s)."
            % (r.status, ", " + r.fehler if r.fehler else ""),
            "Von Hand nachsehen.", gewicht=5))

    # --- llms.txt -------------------------------------------------------
    l = holen(netz.unter(basis, "llms.txt"))
    if l.status == 200 and l.text.strip():
        befunde.append(Befund(
            "llms.txt", True,
            "llms.txt vorhanden (%d Zeichen)." % len(l.text.strip()),
            None, gewicht=1, belege=[l.url]))
    else:
        befunde.append(Befund(
            "llms.txt", False,
            "Keine llms.txt vorhanden.",
            "Eine llms.txt anlegen: eine Seite in einfachem Text, die "
            "sagt, was das Unternehmen macht, fuer wen, wo und zu "
            "welchen Konditionen. Junger Standard, noch nicht von allen "
            "Systemen ausgewertet - guenstig zu erstellen, deshalb "
            "trotzdem sinnvoll.", gewicht=1))

    # --- Strukturierte Daten -------------------------------------------
    typen, kaputt = jsonld_typen(leser.jsonld_roh)
    kern = [t for t in typen if _ist_organisation(t)]
    if kern:
        befunde.append(Befund(
            "Strukturierte Daten", True,
            "JSON-LD vorhanden, Typen: %s." % ", ".join(typen),
            None if "FAQPage" in typen else
            "Zusaetzlich FAQPage ergaenzen: Frage-Antwort-Paare sind das "
            "Format, das Antwortsysteme am haeufigsten uebernehmen.",
            gewicht=4))
    elif typen:
        befunde.append(Befund(
            "Strukturierte Daten", False,
            "JSON-LD vorhanden, aber ohne Organization oder "
            "LocalBusiness. Gefunden: %s." % ", ".join(typen),
            "Organization bzw. LocalBusiness ergaenzen, mit Name, "
            "Adresse, Telefon, Leistungen und Einzugsgebiet.", gewicht=4))
    else:
        befunde.append(Befund(
            "Strukturierte Daten", False,
            "Keine strukturierten Daten (JSON-LD) gefunden.",
            "JSON-LD mit Organization bzw. LocalBusiness einbauen. Das "
            "ist die maschinenlesbare Visitenkarte - ohne sie muss ein "
            "System aus Fliesstext raten, wer die Firma ist.", gewicht=4))
    if kaputt:
        befunde.append(Befund(
            "Strukturierte Daten", False,
            "%d JSON-LD-Block(s) sind fehlerhaft und werden ignoriert."
            % kaputt,
            "Syntaxfehler beheben - ein kaputter Block wirkt wie keiner.",
            gewicht=2))

    # --- Extrahierbarkeit ----------------------------------------------
    woerter = len(leser.sichtbarer_text.split())
    if woerter >= 300:
        befunde.append(Befund(
            "Lesbarer Inhalt", True,
            "Die Startseite liefert %d Woerter im Quelltext." % woerter,
            None, gewicht=5))
    elif woerter >= 80:
        befunde.append(Befund(
            "Lesbarer Inhalt", False,
            "Nur %d Woerter im Quelltext - wenig Substanz zum Zitieren."
            % woerter,
            "Die Startseite braucht Text, der die Leistung in Worten "
            "erklaert. Bilder und Videos sind fuer Antwortsysteme leer.",
            gewicht=5))
    else:
        befunde.append(Befund(
            "Lesbarer Inhalt", False,
            "Nur %d Woerter im Quelltext. Der Inhalt wird "
            "hoechstwahrscheinlich erst im Browser per JavaScript "
            "erzeugt." % woerter,
            "Inhalt serverseitig ausliefern. Antwort-Crawler fuehren "
            "JavaScript meist nicht aus - fuer sie ist die Seite leer. "
            "Das ist der schwerste Einzelbefund ueberhaupt.", gewicht=6))

    # --- Titel und Beschreibung ----------------------------------------
    titel = (leser.titel or "").strip()
    if titel and len(titel) >= 15:
        befunde.append(Befund(
            "Titel", True, "Titel gesetzt: „%s“" % titel,
            None, gewicht=2))
    else:
        befunde.append(Befund(
            "Titel", False,
            "Titel fehlt oder ist zu kurz: „%s“" % titel,
            "Titel setzen nach dem Muster Leistung + Ort + Firma.",
            gewicht=2))

    if (leser.beschreibung or "").strip():
        befunde.append(Befund(
            "Kurzbeschreibung", True, "Meta-Description vorhanden.",
            None, gewicht=1))
    else:
        befunde.append(Befund(
            "Kurzbeschreibung", False, "Keine Meta-Description.",
            "Einen Satz ergaenzen, der die Leistung benennt.", gewicht=1))

    # --- Fragenform -----------------------------------------------------
    fragen = [u for u in leser.h2 if "?" in u]
    if fragen:
        befunde.append(Befund(
            "Fragen auf der Seite", True,
            "%d Ueberschrift(en) in Frageform gefunden." % len(fragen),
            None, gewicht=3, belege=fragen[:5]))
    else:
        befunde.append(Befund(
            "Fragen auf der Seite", False,
            "Keine Ueberschrift ist als Frage formuliert.",
            "Die zehn haeufigsten Kundenfragen als Ueberschrift stellen "
            "und direkt darunter in zwei bis drei Saetzen beantworten. "
            "Antwortsysteme uebernehmen genau dieses Muster.", gewicht=3))

    # --- Sitemap --------------------------------------------------------
    s = holen(netz.unter(basis, "sitemap.xml"))
    if s.status == 200 and ("<urlset" in s.text or "<sitemapindex" in s.text):
        befunde.append(Befund(
            "Sitemap", True, "sitemap.xml vorhanden.", None, gewicht=1,
            belege=[s.url]))
    else:
        befunde.append(Befund(
            "Sitemap", False, "Keine sitemap.xml gefunden.",
            "Sitemap erzeugen lassen - hilft allen Crawlern beim "
            "Auffinden der Unterseiten.", gewicht=1))

    return befunde, leser


def punkte(befunde):
    """Anteil erreichter Gewichtung. Ungeprueftes zaehlt nicht mit."""
    zaehlbar = [b for b in befunde if b.bestanden is not None]
    moeglich = sum(b.gewicht for b in zaehlbar)
    if not moeglich:
        return 0, 0, 0
    erreicht = sum(b.gewicht for b in zaehlbar if b.bestanden)
    return erreicht, moeglich, round(100.0 * erreicht / moeglich)
