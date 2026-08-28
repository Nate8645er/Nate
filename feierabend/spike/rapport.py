# Feierabend - Schritt 0: Rapport-Schema und Bewertung.
#
# Der Vorversuch beantwortet EINE Frage: Wie viele Rapporte haben korrekte
# Felder, wenn ein Handwerker auf Schweizerdeutsch diktiert?
#
# Gemessen wird bewusst NICHT die Wortgenauigkeit der Transkription. Ein
# Transkript darf "zwoi Liter Grundierig" enthalten - solange am Ende
# {material: "Grundierung", menge: 2, einheit: "Liter"} herauskommt, ist der
# Rapport brauchbar. Das ist die niedrigere und die richtige Messlatte.

from dataclasses import dataclass, field

# Felder, ohne die ein Rapport wertlos ist. Fehlt eines, muss das System
# nachfragen statt zu raten - ein still falsch gespeicherter Rapport ist
# schlimmer als gar keiner.
PFLICHTFELDER = ("kunde", "stunden")

# Felder, die den Rapport besser machen, aber ihn nicht tragen.
KUERFELDER = ("taetigkeiten", "material", "folgetermin")

# Wie stark ein Feld in die Gesamtnote eingeht.
GEWICHTE = {
    "kunde": 3.0,
    "stunden": 3.0,
    "taetigkeiten": 1.0,
    "material": 1.5,
    "folgetermin": 0.5,
}

# Stunden gelten als richtig, wenn sie hoechstens um diesen Wert abweichen.
# Eine Viertelstunde Toleranz entspricht der Genauigkeit, mit der Handwerker
# ohnehin rapportieren ("so drei Stunden").
STUNDEN_TOLERANZ = 0.25


@dataclass
class Rapport:
    """Ein extrahierter Arbeitsrapport."""

    kunde: str = ""
    stunden: float | None = None
    taetigkeiten: str = ""
    material: list = field(default_factory=list)
    folgetermin: str = ""

    def fehlende_pflichtfelder(self):
        fehlend = []
        for name in PFLICHTFELDER:
            wert = getattr(self, name)
            if wert is None or (isinstance(wert, str) and not wert.strip()):
                fehlend.append(name)
        return fehlend

    def braucht_rueckfrage(self):
        return bool(self.fehlende_pflichtfelder())


def _normalisieren(text):
    """Grosskleinschreibung, Umlaute und Zierrat entfernen.

    Der Handwerker sagt "Familie Meier", das System schreibt "Meier",
    beides meint denselben Kunden. Ohne Normalisierung zaehlt jede solche
    Variante als Fehler und die Messung wird unbrauchbar.
    """
    if not text:
        return ""
    text = text.lower().strip()
    for alt, neu in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")):
        text = text.replace(alt, neu)
    # Anreden und Fuellwoerter, die nichts unterscheiden.
    for wort in ("familie ", "herr ", "frau ", "hr. ", "fr. "):
        if text.startswith(wort):
            text = text[len(wort):]
    return " ".join(text.split())


def kunde_stimmt(erwartet, tatsaechlich):
    """Kundenname gilt als richtig, wenn der erwartete Name enthalten ist.

    "Meier" in "Familie Meier in Jona" ist ein Treffer - der Ortszusatz
    macht die Zuordnung nicht falsch, nur ausfuehrlicher.
    """
    e, t = _normalisieren(erwartet), _normalisieren(tatsaechlich)
    if not e:
        return not t
    if not t:
        return False
    return e in t or t in e


def stunden_stimmen(erwartet, tatsaechlich):
    if erwartet is None:
        return tatsaechlich is None
    if tatsaechlich is None:
        return False
    return abs(float(erwartet) - float(tatsaechlich)) <= STUNDEN_TOLERANZ


def material_stimmt(erwartet, tatsaechlich):
    """Materialliste als Menge vergleichen, Reihenfolge egal.

    Teiltreffer zaehlen anteilig: Wer zwei von drei Positionen erkennt,
    bekommt zwei Drittel. Alles-oder-nichts waere hier zu hart, weil eine
    vergessene Rolle Abdeckband den Rapport nicht wertlos macht.
    """
    e = {_normalisieren(x) for x in (erwartet or []) if _normalisieren(x)}
    t = {_normalisieren(x) for x in (tatsaechlich or []) if _normalisieren(x)}
    if not e:
        return 1.0 if not t else 0.0
    treffer = 0
    for erwartetes in e:
        if any(erwartetes in kandidat or kandidat in erwartetes
               for kandidat in t):
            treffer += 1
    return treffer / len(e)


def text_stimmt(erwartet, tatsaechlich):
    """Freitext: Es genuegt, dass die erwarteten Stichworte vorkommen."""
    e, t = _normalisieren(erwartet), _normalisieren(tatsaechlich)
    if not e:
        return 1.0
    if not t:
        return 0.0
    stichworte = [w for w in e.split() if len(w) > 3]
    if not stichworte:
        return 1.0 if e in t else 0.0
    return sum(1 for w in stichworte if w in t) / len(stichworte)


def bewerte(erwartet, tatsaechlich):
    """Einen extrahierten Rapport gegen die Wahrheit bewerten.

    Gibt Einzelnoten je Feld (0.0 bis 1.0), die gewichtete Gesamtnote und
    das Urteil zurueck, ob dieser Rapport brauchbar ist.
    """
    noten = {
        "kunde": 1.0 if kunde_stimmt(erwartet.kunde,
                                     tatsaechlich.kunde) else 0.0,
        "stunden": 1.0 if stunden_stimmen(erwartet.stunden,
                                          tatsaechlich.stunden) else 0.0,
        "taetigkeiten": text_stimmt(erwartet.taetigkeiten,
                                    tatsaechlich.taetigkeiten),
        "material": material_stimmt(erwartet.material, tatsaechlich.material),
        "folgetermin": text_stimmt(erwartet.folgetermin,
                                   tatsaechlich.folgetermin),
    }
    gewicht_summe = sum(GEWICHTE.values())
    gesamt = sum(noten[f] * GEWICHTE[f] for f in noten) / gewicht_summe

    # Ein Rapport ist brauchbar, wenn beide Pflichtfelder sitzen. Ohne
    # Kunde und Stunden laesst sich nichts verrechnen - dann helfen auch
    # perfekt erkannte Materialien nicht.
    brauchbar = noten["kunde"] == 1.0 and noten["stunden"] == 1.0

    return {
        "noten": noten,
        "gesamt": round(gesamt, 3),
        "brauchbar": brauchbar,
    }


# Das Abbruchkriterium aus der Spec.
SCHWELLE_BRAUCHBAR = 0.70


def auswerten(ergebnisse):
    """Ueber alle Testfaelle zusammenfassen und das Urteil faellen."""
    if not ergebnisse:
        return {"anzahl": 0, "quote": 0.0, "bestanden": False,
                "urteil": "Keine Testfaelle - nichts entschieden."}
    brauchbar = sum(1 for e in ergebnisse if e["brauchbar"])
    quote = brauchbar / len(ergebnisse)
    bestanden = quote >= SCHWELLE_BRAUCHBAR
    if bestanden:
        urteil = ("Bestanden: %d von %d Rapporten brauchbar (%.0f%%). "
                  "Der Ansatz traegt." % (brauchbar, len(ergebnisse),
                                          quote * 100))
    else:
        urteil = ("Durchgefallen: nur %d von %d Rapporten brauchbar "
                  "(%.0f%%, noetig sind %.0f%%). Der Kanal muss ueberdacht "
                  "werden." % (brauchbar, len(ergebnisse), quote * 100,
                               SCHWELLE_BRAUCHBAR * 100))
    return {
        "anzahl": len(ergebnisse),
        "brauchbar": brauchbar,
        "quote": round(quote, 3),
        "durchschnittsnote": round(
            sum(e["gesamt"] for e in ergebnisse) / len(ergebnisse), 3),
        "bestanden": bestanden,
        "urteil": urteil,
    }
