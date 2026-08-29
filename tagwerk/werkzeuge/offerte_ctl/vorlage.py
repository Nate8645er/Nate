# offerte_ctl - Datenschicht: ODT-Vorlagen lesen und fuellen.
#
# Nach der cli-anything-Methodik, Phase 1: Das Datenmodell zuerst.
#
# Eine ODT-Datei ist ein ZIP-Archiv mit XML darin. Der sichtbare Text steht
# in content.xml. Platzhalter der Form {{feld}} werden dort ersetzt, und
# das Archiv wird unveraendert neu geschrieben - ohne LibreOffice, ohne
# Java, ohne laufende Anwendung.
#
# Warum nicht die UNO-API: Sie braucht einen laufenden soffice-Prozess und
# funktionierendes Java. Fuer reines Textersetzen ist das unnoetig
# schwergewichtig und unnoetig fehleranfaellig. LibreOffice kommt erst bei
# der PDF-Erzeugung ins Spiel.

import re
import shutil
import xml.sax.saxutils as saxutils
import zipfile

PLATZHALTER = re.compile(r"\{\{\s*([a-zA-Z0-9_äöüÄÖÜß.-]+)\s*\}\}")

# Die drei Dateien, die eine ODT mindestens braucht.
MIMETYPE = "application/vnd.oasis.opendocument.text"

MANIFEST = """<?xml version="1.0" encoding="UTF-8"?>
<manifest:manifest xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:\
manifest:1.0" manifest:version="1.2">
 <manifest:file-entry manifest:full-path="/" manifest:media-type="%s"/>
 <manifest:file-entry manifest:full-path="content.xml" \
manifest:media-type="text/xml"/>
</manifest:manifest>
""" % MIMETYPE

CONTENT_RAHMEN = """<?xml version="1.0" encoding="UTF-8"?>
<office:document-content
 xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
 xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0"
 xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0"
 xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0"
 office:version="1.2">
 <office:automatic-styles>
  <style:style style:name="Titel" style:family="paragraph">
   <style:text-properties fo:font-size="16pt" fo:font-weight="bold"/>
  </style:style>
  <style:style style:name="Fett" style:family="paragraph">
   <style:text-properties fo:font-weight="bold"/>
  </style:style>
 </office:automatic-styles>
 <office:body><office:text>%s</office:text></office:body>
</office:document-content>
"""


class VorlagenFehler(Exception):
    """Vorlage fehlerhaft oder nicht lesbar."""


def _absatz(text, stil=None):
    sicher = saxutils.escape(text)
    if stil:
        return '<text:p text:style-name="%s">%s</text:p>' % (stil, sicher)
    return "<text:p>%s</text:p>" % sicher


def vorlage_erzeugen(ziel, zeilen):
    """Eine ODT-Vorlage aus Textzeilen bauen.

    Jede Zeile ist entweder ein String oder ein Paar (text, stil).
    Platzhalter bleiben als {{feld}} stehen - sie werden hier NICHT
    ersetzt, das ist Aufgabe von fuellen().

    Der mimetype-Eintrag muss der erste im Archiv und unkomprimiert sein,
    sonst erkennen manche Programme die Datei nicht als ODT.
    """
    absaetze = []
    for zeile in zeilen:
        if isinstance(zeile, (tuple, list)):
            absaetze.append(_absatz(zeile[0], zeile[1]))
        else:
            absaetze.append(_absatz(zeile))
    inhalt = CONTENT_RAHMEN % "".join(absaetze)

    with zipfile.ZipFile(ziel, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(zipfile.ZipInfo("mimetype"), MIMETYPE,
                   compress_type=zipfile.ZIP_STORED)
        z.writestr("META-INF/manifest.xml", MANIFEST)
        z.writestr("content.xml", inhalt)
    return ziel


def _content_lesen(pfad):
    try:
        with zipfile.ZipFile(pfad) as z:
            return z.read("content.xml").decode("utf-8")
    except (zipfile.BadZipFile, KeyError, OSError) as e:
        raise VorlagenFehler("%s ist keine lesbare ODT-Datei: %s" % (pfad, e))


def felder_finden(pfad):
    """Alle Platzhalter einer Vorlage auflisten.

    Das ist das Probe-Kommando der Methodik: erst hinschauen, dann
    veraendern. Wer die Felder nicht kennt, fuellt blind.
    """
    inhalt = _content_lesen(pfad)
    return sorted(set(PLATZHALTER.findall(inhalt)))


def fuellen(vorlage, ziel, werte, streng=True):
    """Vorlage mit Werten fuellen und als neue ODT speichern.

    streng=True: Ein Platzhalter ohne passenden Wert ist ein Fehler.
    Bewusst so - eine Offerte mit {{betrag}} im Text geht an einen Kunden
    und blamiert den Betrieb. Lieber hier abbrechen.

    Werte werden XML-escaped: Ein Kundenname wie "Meier & Co" wuerde die
    Datei sonst zerstoeren.
    """
    inhalt = _content_lesen(vorlage)
    vorhanden = set(PLATZHALTER.findall(inhalt))
    fehlend = sorted(vorhanden - set(werte))
    if fehlend and streng:
        raise VorlagenFehler(
            "Werte fehlen fuer: %s" % ", ".join(fehlend))

    def ersetze(treffer):
        name = treffer.group(1)
        if name not in werte:
            return treffer.group(0)
        return saxutils.escape(str(werte[name]))

    neu = PLATZHALTER.sub(ersetze, inhalt)

    # Archiv kopieren und nur content.xml austauschen, damit Stile,
    # Bilder und Schriften der Vorlage erhalten bleiben.
    shutil.copyfile(vorlage, ziel)
    _content_ersetzen(ziel, neu)
    return {"ziel": ziel, "ersetzt": sorted(vorhanden & set(werte)),
            "offen": fehlend}


def _content_ersetzen(pfad, neuer_inhalt):
    """content.xml in einer bestehenden ODT austauschen.

    Python kann Eintraege in einem ZIP nicht ersetzen, nur anhaengen -
    also wird das Archiv neu geschrieben. Der mimetype bleibt dabei
    erster und unkomprimierter Eintrag.
    """
    with zipfile.ZipFile(pfad) as alt:
        eintraege = [(i, alt.read(i.filename)) for i in alt.infolist()]

    with zipfile.ZipFile(pfad, "w", zipfile.ZIP_DEFLATED) as neu:
        for info, daten in eintraege:
            if info.filename == "mimetype":
                neu.writestr(zipfile.ZipInfo("mimetype"), daten,
                             compress_type=zipfile.ZIP_STORED)
        for info, daten in eintraege:
            if info.filename == "mimetype":
                continue
            if info.filename == "content.xml":
                neu.writestr("content.xml", neuer_inhalt)
            else:
                neu.writestr(info, daten)
