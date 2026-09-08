# KRYPTO - Datenpruefung.
#
# Zwischen "Daten da" und "Daten brauchbar" liegt der Unterschied
# zwischen einem Signal und einem teuren Irrtum. Dieses Modul sagt nur
# eines: darf auf dieser Reihe gerechnet werden, ja oder nein - und
# wenn nein, warum.
#
# Es rechnet nichts glatt. Es fuellt keine Luecken. Es interpoliert
# nicht. Kaputte Daten bleiben kaputt und werden gemeldet.

import time


class Befund:
    def __init__(self, tauglich, gruende=None, hinweise=None):
        self.tauglich = bool(tauglich)
        self.gruende = list(gruende or [])     # blockierend
        self.hinweise = list(hinweise or [])   # auffaellig, nicht blockierend

    def __bool__(self):
        return self.tauglich

    def __repr__(self):
        return "Befund(%s, %s)" % (self.tauglich, self.gruende)

    def bericht(self):
        if self.tauglich and not self.hinweise:
            return "Daten tauglich."
        teile = []
        if not self.tauglich:
            teile.append("NICHT TAUGLICH: " + "; ".join(self.gruende))
        if self.hinweise:
            teile.append("Hinweis: " + "; ".join(self.hinweise))
        return " | ".join(teile)


def kerzen_pruefen(kerzen, min_kerzen, max_alter_s, jetzt=None):
    """Prueft eine OHLC-Reihe auf das, was wirklich schiefgehen kann."""
    gruende, hinweise = [], []
    jetzt = time.time() if jetzt is None else jetzt

    if not kerzen:
        return Befund(False, ["keine Kerzen"])

    if len(kerzen) < min_kerzen:
        gruende.append("nur %d Kerzen, mindestens %d noetig"
                       % (len(kerzen), min_kerzen))

    zeiten = [k[0] for k in kerzen]
    if any(zeiten[i] >= zeiten[i + 1] for i in range(len(zeiten) - 1)):
        gruende.append("Zeitstempel nicht streng aufsteigend")

    # Die Altersgrenze muss zum Takt der Reihe passen. Eine Quelle mit
    # 4-Stunden-Kerzen kann gar keine Kerze liefern, die juenger als vier
    # Stunden ist - eine feste Stundengrenze wuerde jede solche Reihe
    # verwerfen, obwohl nichts fehlt. Also: die konfigurierte Grenze ist
    # der Boden, der doppelte Kerzentakt der eigentliche Massstab.
    takt = None
    if len(zeiten) >= 3:
        abstaende = sorted(zeiten[i + 1] - zeiten[i]
                           for i in range(len(zeiten) - 1))
        takt = abstaende[len(abstaende) // 2] / 1000.0
    grenze = max(max_alter_s, 2 * takt) if takt else max_alter_s

    alter = jetzt - zeiten[-1] / 1000.0
    if alter > grenze:
        gruende.append("letzte Kerze %d Minuten alt (Grenze %d, Kerzentakt %s)"
                       % (alter / 60, grenze / 60,
                          ("%d Min" % (takt / 60)) if takt else "unbekannt"))
    if alter < -300:
        gruende.append("letzte Kerze liegt in der Zukunft")

    for i, k in enumerate(kerzen):
        o, h, l, c = k[1], k[2], k[3], k[4]
        if min(o, h, l, c) <= 0:
            gruende.append("Kerze %d hat einen Kurs <= 0" % i)
            break
        if h < max(o, c) or l > min(o, c) or h < l:
            gruende.append("Kerze %d ist in sich widerspruechlich "
                           "(High/Low passen nicht zu Open/Close)" % i)
            break

    # Luecken: wenn ein Abstand deutlich aus dem Rahmen faellt, fehlen
    # Kerzen. Das verzerrt jeden Indikator, der Perioden zaehlt.
    if len(zeiten) >= 3:
        abstaende = sorted(zeiten[i + 1] - zeiten[i]
                           for i in range(len(zeiten) - 1))
        median = abstaende[len(abstaende) // 2]
        if median > 0:
            gross = [a for a in abstaende if a > median * 2.5]
            if gross:
                hinweise.append("%d Luecke(n) in der Zeitreihe" % len(gross))

    # Ausreisser: ein einzelner Sprung um mehr als 50 % zwischen zwei
    # Kerzen ist bei Krypto moeglich, aber selten genug, um ihn zu
    # nennen statt stillschweigend zu verrechnen.
    for i in range(1, len(kerzen)):
        vor, jetzt_k = kerzen[i - 1][4], kerzen[i][4]
        if vor > 0 and abs(jetzt_k - vor) / vor > 0.5:
            hinweise.append("Kurssprung >50 %% bei Kerze %d" % i)
            break

    return Befund(not gruende, gruende, hinweise)


def markteintrag_pruefen(eintrag, min_volumen, min_mcap):
    """Prueft einen Eintrag aus /coins/markets auf Handelbarkeit."""
    gruende, hinweise = [], []
    kurs = eintrag.get("current_price")
    vol = eintrag.get("total_volume")
    mcap = eintrag.get("market_cap")

    if not isinstance(kurs, (int, float)) or kurs <= 0:
        gruende.append("kein gueltiger Kurs")
    if not isinstance(vol, (int, float)):
        gruende.append("kein Volumen gemeldet")
    elif vol < min_volumen:
        gruende.append("24h-Volumen %.0f unter Grenze %.0f" % (vol, min_volumen))
    if not isinstance(mcap, (int, float)):
        gruende.append("keine Marktkapitalisierung gemeldet")
    elif mcap < min_mcap:
        gruende.append("Marktkapital %.0f unter Grenze %.0f" % (mcap, min_mcap))

    if isinstance(vol, (int, float)) and isinstance(mcap, (int, float)) \
            and mcap > 0 and vol / mcap > 3:
        hinweise.append("Volumen groesser als 3x Marktkapital - "
                        "auffaellig, moegliches Wash-Trading")

    return Befund(not gruende, gruende, hinweise)
