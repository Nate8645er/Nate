# Feierabend - Anbindung an das Sprachmodell.
#
# Wichtig fuer das Verstaendnis der Architektur: Die Transkription passiert
# NICHT hier, sondern im Browser des Handwerkers (Web Speech API). Damit
# verlaesst die Audioaufnahme das Geraet nie.
#
# Das loest drei Probleme auf einmal:
#   - Datenschutz: Kein Audio auf unseren Servern, kein Transkriptions-
#     dienstleister als Auftragsbearbeiter, keine Grenzueberschreitung.
#   - Kosten: Keine Minutenabrechnung fuer Spracherkennung.
#   - Recht: Die heikelste Datenklasse (Stimme, Nebengeraeusche, Stimmen
#     Dritter im Raum) entsteht bei uns gar nicht erst.
#
# Was hier ankommt, ist bereits Text - und bevor er an das Modell geht,
# sind die Kundennamen durch Token ersetzt.

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "core"))

from extract import ExtraktionFehler, extrahieren  # noqa: E402

MODELL = os.environ.get("FEIERABEND_MODELL", "claude-sonnet-4-6")
MAX_TOKEN = 700


class ModellNichtVerfuegbar(Exception):
    """Kein Schluessel gesetzt oder Aufruf fehlgeschlagen."""


def _client():
    schluessel = os.environ.get("ANTHROPIC_API_KEY")
    if not schluessel:
        raise ModellNichtVerfuegbar(
            "ANTHROPIC_API_KEY ist nicht gesetzt.")
    try:
        import anthropic
    except ImportError:
        raise ModellNichtVerfuegbar(
            "Paket 'anthropic' fehlt - pip install -r requirements.txt")
    return anthropic.Anthropic(api_key=schluessel)


def _aufrufen(anweisung, text):
    """Ein Modellaufruf, bewusst ohne Werkzeuge.

    Der Text stammt aus einer Spracherkennung und ist damit nicht
    vertrauenswuerdig. Ein Modell ohne Werkzeuge kann durch eingeschleuste
    Anweisungen hoechstens schlechte Daten liefern - niemals Aktionen
    ausloesen.
    """
    antwort = _client().messages.create(
        model=MODELL,
        max_tokens=MAX_TOKEN,
        system=anweisung,
        messages=[{"role": "user", "content": text}],
    )
    return "".join(b.text for b in antwort.content if b.type == "text")


def rapport_aus_text(pseudonymisierter_text, bekannte_token=(),
                     uebliche_materialien=()):
    """Pseudonymisierten Text in einen validierten Rapport verwandeln."""
    try:
        return extrahieren(pseudonymisierter_text, _aufrufen,
                           bekannte_token=bekannte_token,
                           uebliche_materialien=uebliche_materialien)
    except ExtraktionFehler:
        raise
    except ModellNichtVerfuegbar:
        raise
    except Exception as e:
        raise ModellNichtVerfuegbar("Modellaufruf fehlgeschlagen: %s" % e)


def verfuegbar():
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def materialien_aus_rapporten(rapporte, hoechstens=25):
    """Die ueblichen Materialien eines Betriebs aus der Historie ziehen.

    Das ist der Kontext, der die Dialekterkennung traegt: Ein Modell, das
    weiss, dass dieser Betrieb mit Grundierung und Abdeckband arbeitet,
    erkennt 'Grundierig' auch dann, wenn die Spracherkennung es
    verstuemmelt hat.
    """
    zaehler = {}
    for r in rapporte:
        for teil in (r.get("material") or "").split(","):
            teil = teil.strip()
            if teil:
                zaehler[teil] = zaehler.get(teil, 0) + 1
    haeufig = sorted(zaehler.items(), key=lambda p: -p[1])
    return [name for name, _ in haeufig[:hoechstens]]


def als_json(wert):
    return json.dumps(wert, ensure_ascii=False)
