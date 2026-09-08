# KRYPTO - FOMO-Orchestrator.
#
# Die Stelle, an der aus vielen Quellen ein Bild wird. Sie ruft die
# Agenten-Rollen der Reihe nach auf, sammelt was da ist, und schreibt
# hin, was gefehlt hat.
#
# Reihenfolge (Phase 9 des Auftrags):
#   TOKEN_RESEARCHER -> LIQUIDITY_ANALYST -> ONCHAIN_ANALYST
#   -> MARKET_ANALYST -> NEWS_ANALYST -> SENTIMENT_ANALYST
#   -> SCAM_DETECTOR -> RISK_ANALYST -> REPORT_AGENT
#
# Der Bericht enthaelt nie einen Kursausblick. Er enthaelt Signale mit
# Begruendung und eine Risikostufe. Der Satz "dieser Coin wird steigen"
# kommt in diesem Modul nicht vor und ist auch nicht ableitbar.

import time

from krypto.analyse import signale, token_risiko
from krypto.betrieb import protokoll
from krypto.quellen import dexscreener, ketten, nachrichten, netz, stimmung


class Befund:
    def __init__(self, begriff):
        self.begriff = begriff
        self.zeit = time.time()
        self.paar = None
        self.alle_paare = []
        self.werte = []              # signale.Wert
        self.risiko = None
        self.quellen = {}            # Name -> Herkunft
        self.luecken = []            # was nicht abrufbar war

    def wert(self, name):
        for w in self.werte:
            if w.name == name:
                return w
        return None

    def bericht(self):
        z = ["=" * 68,
             "TOKEN-BEFUND: %s" % str(self.begriff).upper(),
             "=" * 68]
        if self.paar is None:
            z.append("KEIN HANDELSPAAR GEFUNDEN.")
            z += ["Luecken:"] + ["  - %s" % l for l in self.luecken]
            return "\n".join(z)

        p = self.paar
        z.append("Paar        %s / %s auf %s (%s)"
                 % (p.symbol, (p.name or "?"), p.kette, p.dex))
        z.append("Adresse     %s" % p.token)
        for name, wert, form in (
                ("Kurs", p.kurs, "%.8f USD"),
                ("Liquiditaet", p.liquiditaet, "%.0f USD"),
                ("Volumen 24h", p.volumen_24h, "%.0f USD"),
                ("Marktkapital", p.marktkapital, "%.0f USD"),
                ("FDV", p.fdv, "%.0f USD"),
                ("24h", p.aend_24h, "%+.2f %%")):
            z.append("%-11s %s" % (name, (form % wert) if wert is not None
                                   else "NICHT VERFUEGBAR"))
        z.append("%-11s %s" % ("Alter", ("%.1f Tage" % p.alter_tage)
                               if p.alter_tage is not None
                               else "NICHT VERFUEGBAR"))
        if len(self.alle_paare) > 1:
            z.append("%-11s %d Paare gefunden, das meistgehandelte mit "
                     "genug Tiefe genommen" % ("Auswahl",
                                               len(self.alle_paare)))

        z += ["", "SIGNALE (0-100)", "-" * 68]
        z += ["  " + w.zeile() for w in self.werte]
        zus = signale.zusammenstellen(self.werte)
        z.append("  %-18s %d von %d gemessen (%.0f %%)"
                 % ("VOLLSTAENDIGKEIT", zus["gemessen"], zus["gesamt"],
                    zus["vollstaendigkeit"] * 100))

        if self.risiko:
            z += ["", "RISIKO", "-" * 68]
            z += ["  " + l for l in self.risiko.bericht().split("\n")]

        z += ["", "QUELLEN", "-" * 68]
        for name, h in self.quellen.items():
            z.append("  %-14s %s, Alter %ds"
                     % (name, h.get("quelle"), h.get("alter_s", 0)))
        if self.luecken:
            z += ["", "NICHT ABRUFBAR", "-" * 68]
            z += ["  - %s" % l for l in self.luecken]

        z += ["", "-" * 68,
              "Das ist kein Kursausblick. Ein hoher FOMO-Wert misst",
              "Aufmerksamkeit - und Aufmerksamkeit kommt oft, wenn die",
              "Bewegung schon gelaufen ist."]
        return "\n".join(z)


def analysieren(begriff, kette=None):
    """Vollstaendige Token-Analyse ueber alle erreichbaren Quellen."""
    b = Befund(begriff)

    # --- TOKEN_RESEARCHER + LIQUIDITY_ANALYST ---
    try:
        paare, h = dexscreener.suchen(begriff)
        b.quellen["dexscreener"] = h
        if kette:
            paare = [p for p in paare if p.kette == str(kette).lower()]
        b.alle_paare = paare
        b.paar = dexscreener.bestes_paar(paare)
    except netz.QuellFehler as e:
        b.luecken.append("DexScreener: %s" % e)

    p = b.paar
    if p is None:
        b.luecken.append("ohne Handelspaar sind alle weiteren Werte "
                         "nicht berechenbar")
        protokoll.signal("fomo-befund", begriff=str(begriff),
                         ergebnis="kein Paar")
        return b

    # --- ONCHAIN_ANALYST: ist die Kette ueberhaupt erreichbar? ---
    kette_ok = None
    try:
        hoehe, hk = ketten.hoehe(p.kette)
        kette_ok = True
        b.quellen["kette:%s" % p.kette] = hk
    except (netz.QuellFehler, ValueError, TypeError):
        kette_ok = False
        b.luecken.append("Kette %s nicht direkt erreichbar - "
                         "On-chain-Wert stuetzt sich nur auf DexScreener"
                         % p.kette)

    # --- NEWS_ANALYST ---
    news_wert = signale.nachrichten_momentum()
    try:
        eintraege, hn, fehlend = nachrichten.alle()
        b.quellen.update({"news:%s" % k: v for k, v in hn.items()})
        b.luecken.extend(fehlend)
        if eintraege:
            z = nachrichten.erwaehnungen(eintraege, [p.symbol, p.name])
            treffer = sum(v["anzahl"] for v in z.values())
            news_wert = signale.nachrichten_momentum(treffer, len(eintraege))
    except netz.QuellFehler as e:
        b.luecken.append("Nachrichten: %s" % e)

    # --- SENTIMENT_ANALYST ---
    fg = None
    im_trend = None
    try:
        werte, hf = stimmung.angst_und_gier()
        fg = werte[0]["wert"]
        b.quellen["fear-greed"] = hf
    except netz.QuellFehler as e:
        b.luecken.append("Fear-and-Greed: %s" % e)
    try:
        t, ht = stimmung.trends()
        b.quellen["trending"] = ht
        im_trend = any(
            (e["symbol"] == p.symbol) or
            (p.name and e["name"] and e["name"].lower() == p.name.lower())
            for e in t)
    except netz.QuellFehler as e:
        b.luecken.append("Trendliste: %s" % e)

    # --- MARKET_ANALYST ---
    markt = signale.marktmomentum(p.aend_1h, p.aend_24h, None)
    liq = signale.liquiditaet(p.liquiditaet, p.volumen_24h, p.marktkapital)
    onchain = signale.onchain_staerke(kette_ok, p.kaeufe_24h,
                                      p.verkaeufe_24h, p.alter_tage)
    sozial = signale.soziale_stimmung()      # ohne Quelle: DATA_INCOMPLETE
    fomo = signale.fomo_signal(markt, news_wert, im_trend, fg)

    # --- SCAM_DETECTOR + RISK_ANALYST ---
    b.risiko = token_risiko.bewerten(paar=p)
    risiko_wert = signale.Wert("RISK", float(b.risiko.punkte),
                               [(t, g) for g, t in b.risiko.funde])
    scam_wert = signale.Wert(
        "SCAM_RISK", None,
        fehlend=["Vertragspruefung braucht einen Etherscan-Schluessel",
                 "Honeypot-Test wuerde echtes Geld riskieren",
                 "Halterverteilung braucht Nansen/Arkham"])

    b.werte = [fomo, markt, onchain, liq, sozial, news_wert,
               risiko_wert, scam_wert]

    protokoll.signal("fomo-befund", begriff=str(begriff), symbol=p.symbol,
                     kette=p.kette, risiko=b.risiko.stufe,
                     fomo=fomo.anzeige(), liquiditaet=liq.anzeige())
    return b


def lage():
    """'Was ist gerade interessant?' - kombiniert Trend, Stimmung, News."""
    ergebnis = {"trends": [], "angst_gier": None, "schlagzeilen": [],
                "ketten": {}, "luecken": [], "quellen": {}}
    try:
        t, h = stimmung.trends()
        ergebnis["trends"] = t
        ergebnis["quellen"]["trending"] = h
    except netz.QuellFehler as e:
        ergebnis["luecken"].append("Trendliste: %s" % e)
    try:
        w, h = stimmung.angst_und_gier()
        ergebnis["angst_gier"] = w[0]
        ergebnis["quellen"]["fear-greed"] = h
    except netz.QuellFehler as e:
        ergebnis["luecken"].append("Fear-and-Greed: %s" % e)
    try:
        e, h, fehlend = nachrichten.alle(grenze=12)
        ergebnis["schlagzeilen"] = e[:12]
        ergebnis["luecken"].extend(fehlend)
        ergebnis["quellen"].update({"news:%s" % k: v for k, v in h.items()})
    except netz.QuellFehler as e:
        ergebnis["luecken"].append("Nachrichten: %s" % e)
    return ergebnis
