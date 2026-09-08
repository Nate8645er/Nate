# KRYPTO - Positionsgroesse.
#
# Nicht "wie viel will ich kaufen", sondern "wie viel darf ich
# verlieren". Die Groesse folgt aus dem Stop-Abstand, nicht umgekehrt.
#
#   Menge = (Kapital * Risikoanteil) / (Einstieg - Stop)
#
# Danach greifen zwei Deckel: der maximale Anteil eines einzelnen Werts
# am Kapital, und das freie Geld. Der kleinere gewinnt.

from krypto import konfig


class Groessenbefund:
    def __init__(self, menge, wert, risiko_geld, gruende, begrenzt_durch=None):
        self.menge = menge
        self.wert = wert
        self.risiko_geld = risiko_geld
        self.gruende = gruende
        self.begrenzt_durch = begrenzt_durch

    def __bool__(self):
        return self.menge > 0

    def __repr__(self):
        return "<Groesse %.6f Wert %.2f Risiko %.2f>" % (
            self.menge, self.wert, self.risiko_geld)


def berechnen(kapital, freies_geld, einstieg, stop,
              risiko_anteil=None, max_anteil=None):
    """Positionsgroesse. Gibt bei jeder Unklarheit 0 zurueck."""
    risiko_anteil = (konfig.RISIKO_JE_TRADE if risiko_anteil is None
                     else risiko_anteil)
    max_anteil = (konfig.POSITION_MAX_ANTEIL if max_anteil is None
                  else max_anteil)
    gruende = []

    if einstieg is None or einstieg <= 0:
        return Groessenbefund(0, 0, 0, ["kein gueltiger Einstiegskurs"])
    if stop is None:
        return Groessenbefund(0, 0, 0, ["kein Stop-Loss - Pflicht"])
    if stop >= einstieg:
        return Groessenbefund(0, 0, 0, ["Stop liegt nicht unter dem Einstieg"])
    if kapital <= 0 or freies_geld <= 0:
        return Groessenbefund(0, 0, 0, ["kein Kapital verfuegbar"])

    abstand = einstieg - stop
    risiko_geld = kapital * risiko_anteil
    menge = risiko_geld / abstand
    gruende.append("Risikobudget %.2f bei Stop-Abstand %.4f"
                   % (risiko_geld, abstand))

    grenze = None
    deckel_wert = kapital * max_anteil
    if menge * einstieg > deckel_wert:
        menge = deckel_wert / einstieg
        grenze = "Positionsdeckel %.0f %% des Kapitals" % (max_anteil * 100)
        gruende.append(grenze)

    # Gebuehr muss aus dem freien Geld mitbezahlt werden koennen.
    machbar = freies_geld / (einstieg * (1 + konfig.GEBUEHR + konfig.SLIPPAGE))
    if menge > machbar:
        menge = machbar
        grenze = "freies Geld"
        gruende.append("durch freies Geld begrenzt")

    if menge <= 0:
        return Groessenbefund(0, 0, 0, gruende + ["Ergebnis nicht positiv"])

    wert = menge * einstieg
    return Groessenbefund(menge, wert, menge * abstand, gruende, grenze)
