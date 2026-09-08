# CITED - Fragensatz und Erfassung der Antworten.
#
# Der zweite Teil des Audits: Was antworten die KI-Systeme tatsaechlich,
# wenn ein Kunde fragt?
#
# GRENZE DES WERKZEUGS - hier steht sie ausdruecklich, weil sie den
# Unterschied zwischen Messung und Erfindung ausmacht:
#
#   Dieses Werkzeug ruft KEINE KI-Systeme auf. Es hat keine Zugaenge und
#   gibt kein Geld aus. Es erzeugt den Fragensatz und nimmt die Antworten
#   entgegen, die ein Mensch im Wortlaut erfasst.
#
# Damit ist jede Zahl im Bericht auf eine echte, nachlesbare Antwort
# zurueckfuehrbar. Eine geschaetzte Nennung waere eine erfundene Zahl,
# und eine erfundene Zahl macht den ganzen Bericht wertlos.

import datetime
import json
import os
import re

# Die Fragen sind so gebaut, wie Menschen wirklich fragen: nach einer
# Empfehlung, nach einem Preis, nach einem Vergleich, nach einem
# Sonderfall. Nicht nach Schlagworten.
MUSTER = [
    "Wer bietet {leistung} in {ort} an?",
    "Welche {branche} in {ort} kannst du empfehlen?",
    "Ich brauche {leistung} in der Region {region}. Wen soll ich fragen?",
    "Was kostet {leistung} in der Schweiz ungefaehr?",
    "Worauf muss ich achten, wenn ich {leistung} beauftrage?",
    "Welche {branche} in {ort} hat gute Bewertungen?",
    "Gibt es in {ort} eine {branche}, die auch {zusatz} macht?",
    "{branche} {ort} - wer ist da seriös?",
    "Ich vergleiche Anbieter fuer {leistung}. Wen sollte ich anfragen?",
    "Wer macht {leistung} kurzfristig in {ort}?",
    "Lohnt sich {leistung} ueberhaupt, oder mache ich das selbst?",
    "Welche Firma in {ort} ist auf {leistung} spezialisiert?",
]

SYSTEME = ["ChatGPT", "Perplexity", "Google AI Overview", "Claude",
           "Gemini", "Microsoft Copilot"]


def fragen_bauen(branche, ort, leistungen, region=None, zusatz=None,
                 anzahl=None):
    """Fragensatz erzeugen. Ohne Zufall - derselbe Betrieb, derselbe Satz.

    Wiederholbarkeit ist hier keine Feinheit: Stufe 3 vergleicht die
    Messung von heute mit der von naechstem Monat. Verschiebt sich der
    Fragensatz, misst man nichts.
    """
    region = region or ort
    zusatz = zusatz or "Notfaelle"
    liste = []
    for i, muster in enumerate(MUSTER):
        leistung = leistungen[i % len(leistungen)]
        liste.append(muster.format(
            leistung=leistung, branche=branche, ort=ort,
            region=region, zusatz=zusatz))
    # Doppelte entfernen, Reihenfolge behalten.
    gesehen, sauber = set(), []
    for f in liste:
        if f not in gesehen:
            gesehen.add(f)
            sauber.append(f)
    return sauber[:anzahl] if anzahl else sauber


# ------------------------------------------------------------- Erfassung

class Erhebung:
    """Die erfassten Antworten eines Audits. Liegt als JSON auf der Platte."""

    def __init__(self, pfad):
        self.pfad = pfad
        self.daten = {"firma": "", "domain": "", "erstellt": "",
                      "fragen": [], "antworten": []}
        if os.path.exists(pfad):
            with open(pfad, encoding="utf-8") as f:
                self.daten = json.load(f)

    def sichern(self):
        ordner = os.path.dirname(os.path.abspath(self.pfad))
        if ordner:
            os.makedirs(ordner, exist_ok=True)
        with open(self.pfad, "w", encoding="utf-8") as f:
            json.dump(self.daten, f, ensure_ascii=False, indent=2)

    def anlegen(self, firma, domain, fragen):
        self.daten["firma"] = firma
        self.daten["domain"] = domain
        self.daten["erstellt"] = datetime.date.today().isoformat()
        self.daten["fragen"] = fragen
        self.daten.setdefault("antworten", [])
        return self

    def erfassen(self, system, frage, wortlaut, quellen=None):
        """Eine Antwort im Wortlaut ablegen.

        Ob die Firma genannt wurde, wird NICHT vom Menschen behauptet,
        sondern aus dem Wortlaut ermittelt. So kann sich niemand - auch
        wir nicht - ein besseres Ergebnis wuenschen.
        """
        eintrag = {
            "system": system,
            "frage": frage,
            "wortlaut": wortlaut,
            "quellen": quellen or [],
            "erfasst": datetime.datetime.now().isoformat(timespec="seconds"),
        }
        self.daten["antworten"].append(eintrag)
        return eintrag


def genannt(wortlaut, firma, domain=""):
    """Kommt die Firma im Antworttext vor?

    Vergleicht auf Wortgrenzen und ohne Rechtsform, weil ein System
    „Meier Treuhand“ schreibt, wo die Firma „Meier Treuhand AG“ heisst.
    """
    if not wortlaut:
        return False
    text = wortlaut.lower()
    for name in _namensformen(firma, domain):
        if re.search(r"\b" + re.escape(name) + r"\b", text):
            return True
    return False


RECHTSFORMEN = (" ag", " gmbh", " sa", " sarl", " kg", " ohg", " ug",
                " e.k.", " & co", " holding", " group", " gruppe")


def _namensformen(firma, domain=""):
    formen = set()
    name = (firma or "").strip().lower()
    if name:
        formen.add(name)
        for form in RECHTSFORMEN:
            if name.endswith(form):
                formen.add(name[: -len(form)].strip())
    if domain:
        kern = re.sub(r"^https?://", "", domain).split("/")[0]
        kern = kern.replace("www.", "")
        formen.add(kern)
        if "." in kern:
            formen.add(kern.split(".")[0])
    return {f for f in formen if len(f) >= 3}


def auswerten(erhebung):
    """Nennungsquote je System und insgesamt."""
    firma = erhebung.daten.get("firma", "")
    domain = erhebung.daten.get("domain", "")
    je_system = {}
    for a in erhebung.daten.get("antworten", []):
        eintrag = je_system.setdefault(
            a["system"], {"gefragt": 0, "genannt": 0, "fragen_genannt": []})
        eintrag["gefragt"] += 1
        if genannt(a.get("wortlaut", ""), firma, domain):
            eintrag["genannt"] += 1
            eintrag["fragen_genannt"].append(a["frage"])
    gefragt = sum(e["gefragt"] for e in je_system.values())
    treffer = sum(e["genannt"] for e in je_system.values())
    return {
        "je_system": je_system,
        "gefragt": gefragt,
        "genannt": treffer,
        "quote": round(100.0 * treffer / gefragt) if gefragt else None,
    }
