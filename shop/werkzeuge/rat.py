#!/usr/bin/env python3
"""Der Beraterrat. Acht Modelle aus acht Haeusern sehen sich denselben
Shop an und geben unabhaengig voneinander eine Note von 1 bis 100.

Absichtlich KEIN Anthropic-Modell im Rat: die Bauleitung ist selbst
eines. Ein Rat, in dem der Baumeister mitstimmt, ist kein Rat. Die
Anthropic-Stimme kommt getrennt und ist als solche gekennzeichnet.

Jedes Modell bekommt exakt dieselbe Unterlage: den ausgelesenen Text
beider Hauptseiten, die gemessenen Zahlen und die offenen Punkte -
einschliesslich der unangenehmen. Wer nur das Schoene vorlegt, bekommt
eine Note fuer das Schoene.
"""
import concurrent.futures as futures
import json
import os
import re
import urllib.request

HIER = os.path.dirname(os.path.abspath(__file__))
KEY = open('/root/.claude/uploads/2d96a9a6-93ca-5da3-99c5-55dbdd35f6e9/'
           '7d5931bf-Text_3.txt').read().splitlines()[2].strip()

RAT = [
    "openai/gpt-5.6-terra-pro",
    "google/gemini-3.1-pro-preview",
    "x-ai/grok-4.5",
    "deepseek/deepseek-v4-pro",
    "qwen/qwen3.8-max",
    "moonshotai/kimi-k3",
    "z-ai/glm-5.2",
    "minimax/minimax-m3",
]

AUFTRAG = """Du bist Mitglied eines Beraterrats. Antworte auf Deutsch.

Ein Einzelunternehmer in Rapperswil-Jona (Schweiz) verkauft EIN Produkt
ueber einen eigenen Shopify-Shop: eine Trinkflasche mit fest angebautem
Napf fuer Hund und Katze, 550 ml, sechs Farben, CHF 39.90. Er betreibt
den Shop allein, ohne Lager, per Dropshipping. Sein Ziel ist CHF 1000
Umsatz pro Tag.

Unten steht, was auf den beiden Hauptseiten tatsaechlich steht
(ausgelesen aus dem gelieferten HTML), was gemessen wurde, und was noch
offen ist. Es ist absichtlich auch das Unangenehme dabei.

DEINE AUFGABE
1. Gib eine NOTE VON 1 BIS 100 fuer den Shop, so wie er jetzt ist.
   1 = das Schlechteste, 100 = das Beste. Sei streng und ehrlich; eine
   geschenkte Note hilft niemandem. Begruende die Zahl in zwei Saetzen.
2. Nenne die DREI STAERKSTEN Punkte. Konkret, mit Bezug auf das, was
   unten steht - keine allgemeinen Lobsprueche.
3. Nenne die DREI SCHWAECHSTEN Punkte, nach Schaden geordnet.
4. Nenne die EINE Aenderung, die den Umsatz am staerksten heben wuerde,
   und schaetze, warum gerade diese.
5. Sag, ob du an diesem Shop selbst kaufen wuerdest, und warum nicht.

WICHTIG: Der Betreiber hat sich bewusst gegen einige uebliche
Verkaufsmittel entschieden. Es gibt KEINE Bewertungen, KEINE Sterne,
KEINE Verkaufszahlen, KEINE Dringlichkeit, KEINEN Countdown, KEINE
Verknappung - weil er nichts behaupten will, was er nicht belegen kann.
Er nennt ausserdem offen, was er ueber das Produkt NICHT weiss.
Du darfst das kritisieren, wenn du es fuer falsch haeltst. Aber
schlag nicht einfach "fuege Bewertungen hinzu" vor, ohne dazuzusagen,
woher echte Bewertungen bei null Bestellungen kommen sollen.

Antworte in genau dieser Gliederung, ohne Vorrede:
NOTE: <Zahl>
BEGRUENDUNG: <zwei Saetze>
STARK: <drei Punkte>
SCHWACH: <drei Punkte, nach Schaden geordnet>
GROESSTER HEBEL: <einer>
WUERDE ICH KAUFEN: <ja/nein und warum>
"""


def unterlage():
    t = []
    t.append("=== TEXT DER STARTSEITE ===\n")
    t.append(open(HIER + "/text-start.txt", encoding="utf-8").read())
    t.append("\n\n=== TEXT DER PRODUKTSEITE ===\n")
    t.append(open(HIER + "/text-produkt.txt", encoding="utf-8").read())
    t.append("\n\n" + open(HIER + "/fakten.md", encoding="utf-8").read())
    return "".join(t)


def frage(modell, text):
    daten = json.dumps({
        "model": modell,
        "messages": [{"role": "user", "content": AUFTRAG + "\n\n" + text}],
        "max_tokens": 5000,
        "temperature": 0.4,
        "usage": {"include": True},
    }).encode()
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions", data=daten,
        headers={"Authorization": "Bearer " + KEY,
                 "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            a = json.load(r)
        w = a["choices"][0]
        inhalt = (w["message"].get("content") or "").strip()
        kosten = a.get("usage", {}).get("cost", 0)
        if not inhalt:
            # Manche Modelle verbrauchen das Token-Budget im Nachdenken
            # und liefern einen leeren Inhalt. Das ist kein Absturzgrund,
            # sondern ein Ratsmitglied, das nichts gesagt hat.
            return modell, None, kosten, f"leere Antwort (finish={w.get('finish_reason')})"
        return modell, inhalt, kosten, None
    except Exception as e:
        leib = ""
        if hasattr(e, "read"):
            try:
                leib = e.read().decode()[:300]
            except Exception:
                pass
        return modell, None, 0, f"{type(e).__name__}: {e} {leib}"


def main():
    text = unterlage()
    print(f"Unterlage: {len(text)} Zeichen, rund {len(text)//4} Token\n")
    ergebnisse = []
    with futures.ThreadPoolExecutor(max_workers=8) as ex:
        for m, inhalt, kosten, fehler in ex.map(
                lambda mm: frage(mm, text), RAT):
            ergebnisse.append((m, inhalt, kosten, fehler))

    gesamt = 0
    noten = []
    for m, inhalt, kosten, fehler in ergebnisse:
        print("=" * 72)
        print(m, f"({kosten:.4f} USD)" if kosten else "")
        print("=" * 72)
        gesamt += kosten
        if fehler:
            print("  FEHLER:", fehler)
            continue
        n = re.search(r"NOTE:\s*(\d{1,3})", inhalt)
        if n:
            noten.append((m, int(n.group(1))))
        print(inhalt.strip())
        print()

    print("=" * 72)
    print("NOTEN")
    for m, n in sorted(noten, key=lambda x: -x[1]):
        print(f"  {n:3d}   {m}")
    if noten:
        z = [n for _, n in noten]
        z.sort()
        mitte = z[len(z) // 2] if len(z) % 2 else (z[len(z)//2 - 1] + z[len(z)//2]) / 2
        print(f"\n  Mittelwert {sum(z)/len(z):.1f}   Median {mitte}   "
              f"Spanne {min(z)} bis {max(z)}")
    print(f"  Kosten gesamt: {gesamt:.4f} USD")

    json.dump([{"modell": m, "antwort": i, "kosten": k, "fehler": f}
               for m, i, k, f in ergebnisse],
              open(HIER + "/rat-antworten.json", "w"), ensure_ascii=False,
              indent=1)


main()
