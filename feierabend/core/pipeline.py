# Feierabend - der Weg von der Sprachnachricht zum Rapport.
#
# Haelt die Reihenfolge ein, auf der die Datenschutzarchitektur beruht:
#
#   Audio  ->  Transkript  ->  pseudonymisiert  ->  Modell  ->  Rapport
#                   |               |
#                   |               +-- Sicherheitsnetz: steht noch ein
#                   |                   Klarname drin? Dann geht nichts raus.
#                   +-- Audio ist ab hier verworfen, nie gespeichert.
#
# Transkription und Modell werden hereingereicht. Diese Datei kennt keinen
# Anbieter und keinen Schluessel - dadurch ist der ganze Ablauf ohne Netz
# pruefbar, und der Anbieter laesst sich tauschen, ohne die Logik
# anzufassen.

from dataclasses import dataclass, field

from extract import ExtraktionFehler, extrahieren
from pseudonym import Pseudonymisierer


class PipelineFehler(Exception):
    """Der Durchlauf konnte nicht abgeschlossen werden."""


class KlarnameEntwichen(PipelineFehler):
    """Nach der Pseudonymisierung stand noch ein Kundenname im Text.

    Harter Abbruch, kein Weiterlaufen: Lieber eine Rueckfrage an den
    Handwerker als Namen und Adressen Dritter an ein fremdes Modell.
    """


@dataclass
class Ergebnis:
    """Was am Ende eines Durchlaufs herauskommt."""

    mandant_id: str
    kunde: str = ""
    stunden: float | None = None
    taetigkeiten: str = ""
    material: list = field(default_factory=list)
    folgetermin: str = ""
    unsicher: list = field(default_factory=list)
    unbekannte_namen: list = field(default_factory=list)

    def fehlende_pflichtfelder(self):
        fehlend = []
        if not self.kunde.strip():
            fehlend.append("kunde")
        if self.stunden is None:
            fehlend.append("stunden")
        return fehlend

    @property
    def vollstaendig(self):
        return not self.fehlende_pflichtfelder()

    def rueckfrage(self):
        """Die Frage, die dem Handwerker zurueckgeschickt wird.

        Nie raten: Ein still falsch gespeicherter Rapport zerstoert das
        Vertrauen in alle anderen.
        """
        fehlend = self.fehlende_pflichtfelder()
        if not fehlend:
            return ""
        if self.unbekannte_namen:
            return ("Den Namen %s kenne ich noch nicht. Zu welchem Kunden "
                    "gehoert der Rapport?" % self.unbekannte_namen[0])
        if fehlend == ["stunden"]:
            ziel = self.kunde or "dem Kunden"
            return "Wie lange warst du bei %s?" % ziel
        if fehlend == ["kunde"]:
            return "Bei welchem Kunden war das?"
        return "Bei welchem Kunden warst du, und wie lange?"


def verarbeiten(eingang, audio, kunden, transkribieren, modell,
                uebliche_materialien=()):
    """Eine Sprachnachricht zu einem Rapport verarbeiten.

    "transkribieren" ist eine Funktion (audio) -> Text.
    "modell" ist eine Funktion (anweisung, text) -> Antworttext.

    Das Audio wird nach der Transkription nicht zurueckgegeben und
    nirgends abgelegt - der Aufrufer haelt es im Arbeitsspeicher und
    verwirft es mit dem Ende des Aufrufs.
    """
    transkript = transkribieren(audio)
    if not transkript or not transkript.strip():
        raise PipelineFehler("Transkription lieferte keinen Text")

    pseudo = Pseudonymisierer(kunden)
    zuordnung = pseudo.pseudonymisieren(transkript)

    # Sicherheitsnetz vor dem Modellaufruf. Schlaegt es an, verlaesst
    # nichts das Haus.
    if pseudo.enthaelt_klarnamen(zuordnung.text):
        raise KlarnameEntwichen(
            "Pseudonymisierung unvollstaendig - Abbruch vor Modellaufruf")

    try:
        roh = extrahieren(zuordnung.text, modell,
                          bekannte_token=sorted(zuordnung.treffer),
                          uebliche_materialien=uebliche_materialien)
    except ExtraktionFehler as e:
        raise PipelineFehler("Extraktion fehlgeschlagen: %s" % e)

    kunde = ""
    if roh["kunde_token"]:
        eintrag = pseudo.kunde_zu_token(roh["kunde_token"])
        if eintrag:
            kunde = eintrag.name

    return Ergebnis(
        mandant_id=eingang.mandant_id,
        kunde=kunde,
        stunden=roh["stunden"],
        taetigkeiten=pseudo.aufloesen(roh["taetigkeiten"]),
        material=roh["material"],
        folgetermin=roh["folgetermin"],
        unsicher=roh["unsicher"],
        unbekannte_namen=zuordnung.unbekannt,
    )
