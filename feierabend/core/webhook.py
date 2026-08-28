# Feierabend - Eingangspruefung fuer WhatsApp-Webhooks.
#
# Ohne diese Schicht kann jeder, der die URL kennt, Rapporte in beliebige
# Mandanten schreiben, Verarbeitung ausloesen und das Transkriptions- und
# Modellbudget abbrennen. Sie ist die duenne Wand zwischen dem offenen
# Internet und allem dahinter.
#
# Drei Pruefungen, in dieser Reihenfolge:
#   1. Signatur - stammt die Anfrage wirklich von Meta?
#   2. Wiedereinspielung - habe ich diese Nachricht schon verarbeitet?
#   3. Absender - ist diese Nummer bei einem Mandanten eingetragen?
#
# Die Absendernummer ist ausdruecklich KEIN Berechtigungsnachweis. Sie
# laesst sich faelschen (SIM-Swap), deshalb wird sie nur gegen eine
# ausdrueckliche Freigabeliste geprueft und nie implizit einem Mandanten
# zugeordnet.

import hashlib
import hmac
import time
from dataclasses import dataclass

SIGNATUR_KOPFZEILE = "X-Hub-Signature-256"
SIGNATUR_PRAEFIX = "sha256="

# Wie lange eine Nachrichten-ID gegen Wiedereinspielung gemerkt wird.
WIEDERHOLUNGSFENSTER_SEKUNDEN = 24 * 60 * 60


class EingangFehler(Exception):
    """Anfrage abgewiesen. Die Meldung ist fuer das Protokoll, nicht fuer
    den Absender - nach aussen geht nur ein nackter Statuscode."""


def signatur_pruefen(rohkoerper, kopfzeile, app_secret):
    """HMAC-SHA256 ueber den ROHEN Anfragekoerper pruefen.

    Der haeufigste Fehler an dieser Stelle: Das Web-Rahmenwerk parst JSON,
    und die Pruefung laeuft dann gegen das neu serialisierte Ergebnis. Ein
    einziges Leerzeichen Unterschied, und jede echte Anfrage wird
    abgelehnt - oder schlimmer, die Pruefung wird entnervt entfernt.
    Deshalb: immer die unveraenderten Bytes.
    """
    if not app_secret:
        # Fehlendes Geheimnis ist ein Startfehler, keine Freigabe. Genau
        # hier ist der Prototyp javier-mobile falsch herum gebaut.
        raise EingangFehler("App-Secret nicht gesetzt")
    if not isinstance(rohkoerper, (bytes, bytearray)):
        raise EingangFehler("Rohkoerper muss aus Bytes bestehen")
    if not kopfzeile or not kopfzeile.startswith(SIGNATUR_PRAEFIX):
        raise EingangFehler("Signatur fehlt oder hat falsches Format")

    erwartet = hmac.new(
        app_secret.encode("utf-8"), rohkoerper, hashlib.sha256).hexdigest()
    geliefert = kopfzeile[len(SIGNATUR_PRAEFIX):]

    # Konstante Laufzeit: sonst laesst sich die gueltige Signatur Zeichen
    # fuer Zeichen erraten.
    if not hmac.compare_digest(erwartet, geliefert):
        raise EingangFehler("Signatur stimmt nicht")
    return True


def signatur_erzeugen(rohkoerper, app_secret):
    """Gegenstueck fuer Tests und fuer die lokale Entwicklung."""
    unterschrift = hmac.new(
        app_secret.encode("utf-8"), rohkoerper, hashlib.sha256).hexdigest()
    return SIGNATUR_PRAEFIX + unterschrift


class Wiedereinspielsperre:
    """Merkt sich verarbeitete Nachrichten-IDs.

    Meta stellt Webhooks bei Fehlern erneut zu. Ohne Sperre entstehen
    doppelte Rapporte - und ein Angreifer koennte eine abgefangene, gueltig
    signierte Anfrage beliebig oft wiederholen.

    Im Betrieb gehoert das in eine gemeinsame Ablage (Redis, Datenbank);
    diese Fassung reicht fuer einen einzelnen Prozess und fuer Tests.
    """

    def __init__(self, fenster_sekunden=WIEDERHOLUNGSFENSTER_SEKUNDEN,
                 jetzt=time.time):
        self._gesehen = {}
        self._fenster = fenster_sekunden
        self._jetzt = jetzt

    def schon_gesehen(self, nachricht_id):
        if not nachricht_id:
            raise EingangFehler("Nachricht ohne ID")
        self._aufraeumen()
        return nachricht_id in self._gesehen

    def vermerken(self, nachricht_id):
        if not nachricht_id:
            raise EingangFehler("Nachricht ohne ID")
        self._gesehen[nachricht_id] = self._jetzt()

    def _aufraeumen(self):
        grenze = self._jetzt() - self._fenster
        veraltet = [k for k, t in self._gesehen.items() if t < grenze]
        for k in veraltet:
            del self._gesehen[k]

    def __len__(self):
        self._aufraeumen()
        return len(self._gesehen)


@dataclass
class Eingang:
    """Eine gepruefte, einem Mandanten zugeordnete Sprachnachricht."""

    mandant_id: str
    absender: str
    nachricht_id: str
    medien_id: str


def nummer_normalisieren(nummer):
    """Auf reine Ziffern mit fuehrendem Plus bringen.

    "+41 79 123 45 67", "0041791234567" und "41791234567" sind dieselbe
    Nummer. Ohne Vereinheitlichung schlaegt die Freigabeliste sporadisch
    fehl - und das sieht dann aus wie ein Zufallsfehler.
    """
    if not nummer:
        return ""
    ziffern = "".join(c for c in str(nummer) if c.isdigit())
    if not ziffern:
        return ""
    if ziffern.startswith("00"):
        ziffern = ziffern[2:]
    return "+" + ziffern


def mandant_zuordnen(absender, nummernverzeichnis):
    """Absendernummer einem Mandanten zuordnen - oder abweisen.

    Kein Anlegen unterwegs: Eine unbekannte Nummer bekommt eine
    freundliche Absage, keinen Zugang. Nummern werden ausschliesslich
    beim ausdruecklichen Onboarding eingetragen.
    """
    normalisiert = nummer_normalisieren(absender)
    if not normalisiert:
        raise EingangFehler("Absendernummer fehlt")
    mandant = nummernverzeichnis.get(normalisiert)
    if not mandant:
        raise EingangFehler("Nummer keinem Mandanten zugeordnet")
    return mandant


def eingang_pruefen(rohkoerper, kopfzeile, app_secret, nutzlast,
                    nummernverzeichnis, sperre):
    """Die vollstaendige Eingangspruefung, in sicherer Reihenfolge.

    Die Signatur wird zuerst geprueft - vor jedem Zugriff auf den Inhalt.
    Alles danach verarbeitet bereits als echt erwiesene Daten.
    """
    signatur_pruefen(rohkoerper, kopfzeile, app_secret)

    nachricht_id = nutzlast.get("nachricht_id")
    if sperre.schon_gesehen(nachricht_id):
        raise EingangFehler("Nachricht bereits verarbeitet")

    mandant = mandant_zuordnen(nutzlast.get("absender"), nummernverzeichnis)

    medien_id = nutzlast.get("medien_id")
    if not medien_id:
        raise EingangFehler("Keine Sprachnachricht enthalten")

    sperre.vermerken(nachricht_id)
    return Eingang(mandant_id=mandant,
                   absender=nummer_normalisieren(nutzlast.get("absender")),
                   nachricht_id=nachricht_id,
                   medien_id=medien_id)
