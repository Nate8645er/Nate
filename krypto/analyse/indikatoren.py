# KRYPTO - Indikatoren.
#
# Reines Python, keine Abhaengigkeiten. Jede Funktion gibt eine Reihe
# zurueck, die genau so lang ist wie die Eingabe, mit None dort, wo noch
# nicht genug Daten fuer eine Aussage vorhanden sind.
#
# Das None ist Absicht und der wichtigste Teil der Datei: Wer die
# Aufwaermphase abschneidet und die Reihen dann aneinanderlegt,
# verschiebt sie gegeneinander und rechnet mit der Zukunft. Gleich lange
# Reihen mit Luecken machen diesen Fehler unmoeglich.
#
# Index i einer Reihe verwendet ausschliesslich Werte bis
# einschliesslich i. Nie einen spaeteren. Das ist die einzige Regel,
# die zwischen einem Backtest und einer Illusion steht.


def _pruefe(reihe, laenge):
    if laenge < 1:
        raise ValueError("Periode muss mindestens 1 sein")
    return list(reihe)


def sma(werte, laenge):
    """Einfacher gleitender Durchschnitt."""
    w = _pruefe(werte, laenge)
    raus, summe = [], 0.0
    for i, x in enumerate(w):
        summe += x
        if i >= laenge:
            summe -= w[i - laenge]
        raus.append(summe / laenge if i >= laenge - 1 else None)
    return raus


def ema(werte, laenge):
    """Exponentiell geglaettet. Startwert ist der SMA der ersten Periode -
    so beginnt die Reihe nicht mit einem willkuerlichen Ausreisser."""
    w = _pruefe(werte, laenge)
    raus = [None] * len(w)
    if len(w) < laenge:
        return raus
    faktor = 2.0 / (laenge + 1)
    stand = sum(w[:laenge]) / laenge
    raus[laenge - 1] = stand
    for i in range(laenge, len(w)):
        stand = (w[i] - stand) * faktor + stand
        raus[i] = stand
    return raus


def rsi(schluss, laenge=14):
    """RSI nach Wilder. 0..100."""
    w = _pruefe(schluss, laenge)
    raus = [None] * len(w)
    if len(w) < laenge + 1:
        return raus
    gewinne = losse = 0.0
    for i in range(1, laenge + 1):
        d = w[i] - w[i - 1]
        gewinne += max(d, 0.0)
        losse += max(-d, 0.0)
    schnitt_g, schnitt_v = gewinne / laenge, losse / laenge
    raus[laenge] = 100.0 if schnitt_v == 0 else \
        100.0 - 100.0 / (1.0 + schnitt_g / schnitt_v)
    for i in range(laenge + 1, len(w)):
        d = w[i] - w[i - 1]
        schnitt_g = (schnitt_g * (laenge - 1) + max(d, 0.0)) / laenge
        schnitt_v = (schnitt_v * (laenge - 1) + max(-d, 0.0)) / laenge
        raus[i] = 100.0 if schnitt_v == 0 else \
            100.0 - 100.0 / (1.0 + schnitt_g / schnitt_v)
    return raus


def macd(schluss, kurz=12, lang=26, signal=9):
    """Gibt (macd, signal, histogramm) zurueck, alle gleich lang."""
    e_kurz, e_lang = ema(schluss, kurz), ema(schluss, lang)
    linie = [None if a is None or b is None else a - b
             for a, b in zip(e_kurz, e_lang)]

    # Die Signallinie ist ein EMA der MACD-Linie. Sie darf erst starten,
    # wenn die MACD-Linie selbst existiert.
    start = next((i for i, x in enumerate(linie) if x is not None), None)
    sig = [None] * len(linie)
    if start is not None:
        teil = ema(linie[start:], signal)
        sig[start:] = teil
    hist = [None if a is None or b is None else a - b
            for a, b in zip(linie, sig)]
    return linie, sig, hist


def wahre_spanne(hoch, tief, schluss):
    """True Range je Kerze. Erste Kerze: nur Hoch minus Tief."""
    raus = [hoch[0] - tief[0]] if hoch else []
    for i in range(1, len(hoch)):
        raus.append(max(hoch[i] - tief[i],
                        abs(hoch[i] - schluss[i - 1]),
                        abs(tief[i] - schluss[i - 1])))
    return raus


def atr(hoch, tief, schluss, laenge=14):
    """Average True Range nach Wilder - das Mass fuer Stop-Abstaende."""
    tr = wahre_spanne(hoch, tief, schluss)
    raus = [None] * len(tr)
    if len(tr) < laenge:
        return raus
    stand = sum(tr[:laenge]) / laenge
    raus[laenge - 1] = stand
    for i in range(laenge, len(tr)):
        stand = (stand * (laenge - 1) + tr[i]) / laenge
        raus[i] = stand
    return raus


def bollinger(schluss, laenge=20, faktor=2.0):
    """(mitte, oben, unten). Standardabweichung der Grundgesamtheit."""
    m = sma(schluss, laenge)
    oben, unten = [None] * len(m), [None] * len(m)
    for i in range(len(m)):
        if m[i] is None:
            continue
        fenster = schluss[i - laenge + 1:i + 1]
        varianz = sum((x - m[i]) ** 2 for x in fenster) / laenge
        s = varianz ** 0.5
        oben[i], unten[i] = m[i] + faktor * s, m[i] - faktor * s
    return m, oben, unten


def volatilitaet(schluss, laenge=20):
    """Standardabweichung der Renditen je Kerze, als Anteil."""
    raus = [None] * len(schluss)
    renditen = [None]
    for i in range(1, len(schluss)):
        renditen.append((schluss[i] - schluss[i - 1]) / schluss[i - 1]
                        if schluss[i - 1] else None)
    for i in range(len(schluss)):
        fenster = [r for r in renditen[max(0, i - laenge + 1):i + 1]
                   if r is not None]
        if len(fenster) < laenge:
            continue
        mittel = sum(fenster) / len(fenster)
        raus[i] = (sum((r - mittel) ** 2 for r in fenster)
                   / len(fenster)) ** 0.5
    return raus


def regime(vola_reihe, index=-1, ruhig=0.01, wild=0.03):
    """Volatilitaetsregime als Wort. Ohne Wert: 'unbekannt'."""
    try:
        v = vola_reihe[index]
    except IndexError:
        return "unbekannt"
    if v is None:
        return "unbekannt"
    if v < ruhig:
        return "ruhig"
    if v < wild:
        return "normal"
    return "wild"


def marken(hoch, tief, fenster=5, anzahl=3, bis=None):
    """Unterstuetzung und Widerstand aus lokalen Extrema.

    Ein Punkt zaehlt nur, wenn er auf beiden Seiten 'fenster' Kerzen
    ueberragt. Die letzten 'fenster' Kerzen liefern daher keine Marke -
    das ist korrekt, denn ob dort ein Extrem liegt, weiss man erst
    spaeter. Genau hier schleicht sich sonst die Zukunft ein.
    """
    n = len(hoch) if bis is None else min(bis, len(hoch))
    hochs, tiefs = [], []
    for i in range(fenster, n - fenster):
        umgebung_h = hoch[i - fenster:i + fenster + 1]
        umgebung_t = tief[i - fenster:i + fenster + 1]
        if hoch[i] == max(umgebung_h) and umgebung_h.count(hoch[i]) == 1:
            hochs.append(hoch[i])
        if tief[i] == min(umgebung_t) and umgebung_t.count(tief[i]) == 1:
            tiefs.append(tief[i])
    return {"widerstand": sorted(hochs, reverse=True)[:anzahl],
            "unterstuetzung": sorted(tiefs, reverse=True)[:anzahl]}


def zerlegen(kerzen):
    """OHLC-Kerzen in vier Reihen."""
    return ([k[1] for k in kerzen], [k[2] for k in kerzen],
            [k[3] for k in kerzen], [k[4] for k in kerzen])
