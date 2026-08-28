# Feierabend - Pseudonymisierung von Kundennamen.
#
# Der wichtigste Datenschutzbaustein des Systems: Bevor ein Transkript an
# ein Sprachmodell geht, werden bekannte Kundennamen durch Token ersetzt.
# Das Modell sieht "KUNDE_7", nicht "Familie Meier in Jona".
#
# Damit verlassen Namen und Adressen der Endkunden - Menschen, die nie
# eingewilligt haben und vom System nichts wissen - die eigene
# Infrastruktur nie.
#
# Ehrlich zur Grenze: Pseudonymisierte Daten bleiben Personendaten, weil
# wir sie zurueckaufloesen koennen. Die Uebermittlungsfrage verschwindet
# nicht, das Risiko sinkt aber erheblich.

import difflib
import re
import unicodedata
from dataclasses import dataclass, field

TOKEN_MUSTER = re.compile(r"KUNDE_(\d+)")

# Ab welcher Aehnlichkeit ein gesprochener Name einem Kunden aus dem Stamm
# zugeordnet wird. Bewusst hoch: Eine falsche Zuordnung belastet den
# Rapport dem falschen Auftrag - der gefaehrlichste Fehler im ganzen
# System, weil er unsichtbar bleibt.
AEHNLICHKEIT_SCHWELLE = 0.82

# Anreden, die vor einem Namen stehen koennen und nichts unterscheiden.
ANREDEN = ("familie", "fam", "herr", "hr", "frau", "fr")

# Woerter, die im Dialekt vor Ortsangaben stehen ("Meier z Jona").
ORTSMARKER = ("in", "z", "zu", "an", "bei", "uf", "auf")


def _entaccent(text):
    """Umlaute und Akzente vereinheitlichen.

    Transkriptionsmodelle schreiben denselben Namen mal "Mueller", mal
    "Müller", mal "Muller". Ohne Vereinheitlichung findet der Abgleich
    denselben Kunden dreimal nicht.
    """
    text = text.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue")
    text = text.replace("Ä", "Ae").replace("Ö", "Oe").replace("Ü", "Ue")
    text = text.replace("ß", "ss")
    zerlegt = unicodedata.normalize("NFKD", text)
    return "".join(c for c in zerlegt if not unicodedata.combining(c))


def normalisieren(text):
    """Kleinschreibung, Akzente weg, Anreden weg, Leerraum vereinheitlicht."""
    if not text:
        return ""
    text = _entaccent(text.lower())
    text = re.sub(r"[^\w\s-]", " ", text)
    woerter = text.split()
    while woerter and woerter[0].strip(".") in ANREDEN:
        woerter.pop(0)
    return " ".join(woerter)


@dataclass
class Kunde:
    """Ein Kunde aus dem Stamm eines Betriebs."""

    id: int
    name: str
    aliase: list = field(default_factory=list)

    @property
    def token(self):
        return "KUNDE_%d" % self.id

    def suchbegriffe(self):
        """Alle Schreibweisen, unter denen dieser Kunde erkannt wird."""
        begriffe = {normalisieren(self.name)}
        for alias in self.aliase:
            norm = normalisieren(alias)
            if norm:
                begriffe.add(norm)
        # Der Nachname allein ist im Handwerk die haeufigste Anrede.
        teile = normalisieren(self.name).split()
        if len(teile) > 1:
            begriffe.add(teile[-1])
        return {b for b in begriffe if b}


@dataclass
class Zuordnung:
    """Was bei der Pseudonymisierung tatsaechlich ersetzt wurde."""

    text: str
    treffer: dict = field(default_factory=dict)   # token -> Originalwortlaut
    unbekannt: list = field(default_factory=list)  # nicht zuordenbare Namen

    @property
    def eindeutig(self):
        """Genau ein Kunde erkannt - dann ist die Zuordnung sicher."""
        return len(self.treffer) == 1


class Pseudonymisierer:
    """Ersetzt Kundennamen im Transkript durch Token und wieder zurueck.

    Arbeitet ausschliesslich lokal. Der Kundenstamm verlaesst den Prozess
    nicht.
    """

    def __init__(self, kunden):
        self.kunden = list(kunden)
        self._nach_token = {k.token: k for k in self.kunden}
        # Laengste Begriffe zuerst, damit "Meier-Schmid" nicht von "Meier"
        # zerschnitten wird.
        self._begriffe = []
        for kunde in self.kunden:
            for begriff in kunde.suchbegriffe():
                self._begriffe.append((begriff, kunde))
        self._begriffe.sort(key=lambda p: len(p[0]), reverse=True)

    # ------------------------------------------------------------ hinweg

    def pseudonymisieren(self, transkript):
        """Transkript -> Text mit Token statt Kundennamen."""
        if not transkript:
            return Zuordnung(text="")
        text = transkript
        treffer = {}

        for begriff, kunde in self._begriffe:
            if kunde.token in treffer:
                continue
            gefunden = self._finde(text, begriff)
            if gefunden is None:
                continue
            start, ende = gefunden
            treffer[kunde.token] = text[start:ende]
            text = text[:start] + kunde.token + text[ende:]

        return Zuordnung(text=text, treffer=treffer,
                         unbekannt=self._unbekannte_namen(text))

    def _finde(self, text, begriff):
        """Position eines Begriffs im Text, tolerant gegen Schreibweisen.

        Erst exakt (normalisiert), dann aehnlich. Gibt Zeichenpositionen
        im ORIGINALTEXT zurueck, damit die Ersetzung den Wortlaut trifft.
        """
        wortanzahl = len(begriff.split())
        woerter = list(re.finditer(r"\S+", text))
        if not woerter:
            return None

        for i in range(len(woerter) - wortanzahl + 1):
            fenster = woerter[i:i + wortanzahl]
            start, ende = fenster[0].start(), fenster[-1].end()
            kandidat = normalisieren(text[start:ende])
            if not kandidat:
                continue
            if kandidat == begriff:
                return (start, ende)
            if self._aehnlich(kandidat, begriff):
                return (start, ende)
        return None

    @staticmethod
    def _aehnlich(a, b):
        # Sehr kurze Namen nicht fuzzy vergleichen - "Ott" und "Ost"
        # waeren sonst derselbe Kunde.
        if min(len(a), len(b)) < 5:
            return False
        return difflib.SequenceMatcher(None, a, b).ratio() >= \
            AEHNLICHKEIT_SCHWELLE

    def _unbekannte_namen(self, text):
        """Grossgeschriebene Woerter nach einer Anrede, die kein Token sind.

        Das ist keine Namenserkennung, sondern ein Signal fuer die
        Rueckfrage: "Familie Zimmermann" ohne passenden Stamm-Eintrag
        heisst, dass nachgefragt werden muss statt geraten.
        """
        unbekannt = []
        woerter = text.split()
        for i, wort in enumerate(woerter[:-1]):
            if wort.lower().strip(".,") not in ANREDEN:
                continue
            naechstes = woerter[i + 1].strip(".,")
            if naechstes.startswith("KUNDE_"):
                continue
            if naechstes[:1].isupper():
                unbekannt.append(naechstes)
        return unbekannt

    # ------------------------------------------------------------ zurueck

    def aufloesen(self, text):
        """Token im Modellergebnis wieder durch Klarnamen ersetzen."""
        if not text:
            return ""

        def ersetze(treffer):
            kunde = self._nach_token.get(treffer.group(0))
            return kunde.name if kunde else treffer.group(0)

        return TOKEN_MUSTER.sub(ersetze, text)

    def kunde_zu_token(self, token):
        return self._nach_token.get(token)

    def enthaelt_klarnamen(self, text):
        """Sicherheitsnetz: Steht noch ein bekannter Kundenname im Text?

        Wird vor jedem Modellaufruf geprueft. Schlaegt sie an, geht der
        Text nicht raus - lieber eine Rueckfrage als ein Datenabfluss.
        """
        norm = normalisieren(text)
        for begriff, _ in self._begriffe:
            if len(begriff) < 4:
                continue
            if re.search(r"\b%s\b" % re.escape(begriff), norm):
                return True
        return False
