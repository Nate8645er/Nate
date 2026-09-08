# CITED - der Bericht, den der Kunde bekommt.
#
# Zwei Teile, sichtbar getrennt:
#   1. Maschinell geprueft - jederzeit wiederholbar, ohne Ermessen.
#   2. Im Wortlaut erfasste Antworten der KI-Systeme.
#
# Was nicht geprueft werden konnte, steht als "nicht geprueft" drin.
# Eine Luecke offen auszuweisen ist der einzige Weg, wie der Rest
# glaubwuerdig bleibt.

import datetime
import html


def _s(wert):
    """Alles, was in die Seite geht, wird escaped. Auch fremder Text."""
    return html.escape(str(wert), quote=True)


# Achtung: im Kopf steht CSS voller Prozentzeichen. Deshalb wird hier
# NICHT mit %-Formatierung gearbeitet, sondern ein eindeutiges Zeichen
# ersetzt - sonst verschluckt sich Python am ersten "width:100%".
KOPF = """<!doctype html>
<html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>KI-Sichtbarkeit — @@FIRMA@@</title>
<style>
:root{--papier:#FCFCFA;--tinte:#15191B;--matt:#5B6569;--linie:#E2E4E0;
 --gut:#2F6B4F;--gut-f:#E6F0E9;--schlecht:#9A3F2C;--schlecht-f:#F7E8E3;
 --offen:#7A6A3C;--offen-f:#F4EFE0;--akzent:#123A44}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--papier);color:var(--tinte);
 font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
 padding:0 22px 80px}
.bahn{max-width:760px;margin:0 auto}
header{padding:44px 0 28px;border-bottom:3px solid var(--tinte)}
.marke{font-size:12px;font-weight:700;letter-spacing:.22em;
 text-transform:uppercase;color:var(--akzent)}
h1{font-size:31px;letter-spacing:-.02em;margin-top:10px;line-height:1.15}
.unter{color:var(--matt);margin-top:10px;font-size:15px}
h2{font-size:13px;font-weight:700;letter-spacing:.13em;text-transform:uppercase;
 color:var(--matt);margin:44px 0 14px;padding-bottom:7px;
 border-bottom:1px solid var(--linie)}
h3{font-size:18px;margin:26px 0 8px}
p{margin-bottom:12px}
.kennzahlen{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:26px}
.kennzahl{border:1px solid var(--linie);border-radius:10px;padding:16px 18px}
.kennzahl .wert{font-size:34px;font-weight:700;line-height:1;
 font-variant-numeric:tabular-nums}
.kennzahl .was{font-size:12px;font-weight:700;letter-spacing:.1em;
 text-transform:uppercase;color:var(--matt);margin-top:8px}
.befund{border:1px solid var(--linie);border-left-width:5px;border-radius:9px;
 padding:14px 16px;margin-bottom:11px}
.befund.ja{border-left-color:var(--gut)}
.befund.nein{border-left-color:var(--schlecht)}
.befund.offen{border-left-color:var(--offen)}
.befund .zeile{display:flex;justify-content:space-between;gap:14px;
 align-items:baseline;flex-wrap:wrap}
.befund .feld{font-weight:700}
.marke-ja,.marke-nein,.marke-offen{font-size:11px;font-weight:700;
 letter-spacing:.09em;text-transform:uppercase;padding:3px 9px;border-radius:4px}
.marke-ja{background:var(--gut-f);color:var(--gut)}
.marke-nein{background:var(--schlecht-f);color:var(--schlecht)}
.marke-offen{background:var(--offen-f);color:var(--offen)}
.befund p{margin:8px 0 0;font-size:15px}
.tat{margin-top:9px;padding-top:9px;border-top:1px dashed var(--linie);
 font-size:15px}
.tat b{color:var(--akzent)}
.belege{font-size:13px;color:var(--matt);margin-top:7px;word-break:break-word}
table{width:100%;border-collapse:collapse;margin-top:14px;font-size:15px}
th,td{text-align:left;padding:9px 10px;border-bottom:1px solid var(--linie)}
th{font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--matt)}
td.zahl{text-align:right;font-variant-numeric:tabular-nums}
.antwort{border:1px solid var(--linie);border-radius:9px;padding:14px 16px;
 margin-bottom:12px}
.antwort .oben{font-size:13px;color:var(--matt);margin-bottom:7px}
.antwort .frage{font-weight:700;margin-bottom:9px}
.antwort blockquote{border-left:3px solid var(--linie);padding-left:14px;
 white-space:pre-wrap;font-size:15px;color:#33393B}
.hinweis{background:#F1F3F0;border-radius:10px;padding:16px 18px;
 font-size:14px;color:var(--matt);margin-top:16px}
.hinweis b{color:var(--tinte)}
footer{margin-top:52px;padding-top:18px;border-top:1px solid var(--linie);
 font-size:13px;color:var(--matt)}
@media print{body{padding:0}header{padding-top:0}}
</style></head><body><div class="bahn">
"""


def bauen(firma, domain, befunde, technik_punkte, erhebung=None,
          auswertung=None, ausgabe_datum=None):
    datum = ausgabe_datum or datetime.date.today().strftime("%d.%m.%Y")
    erreicht, moeglich, prozent = technik_punkte
    t = [KOPF.replace("@@FIRMA@@", _s(firma))]

    t.append('<header><div class="marke">CITED · KI-Sichtbarkeit</div>')
    t.append("<h1>Werden Sie in KI-Antworten genannt?</h1>")
    t.append('<div class="unter">%s · %s · Stand %s</div></header>'
             % (_s(firma), _s(domain), _s(datum)))

    # ---- Kennzahlen
    t.append('<div class="kennzahlen">')
    t.append('<div class="kennzahl"><div class="wert">%d%%</div>'
             '<div class="was">technisch auffindbar</div></div>' % prozent)
    if auswertung and auswertung.get("quote") is not None:
        t.append('<div class="kennzahl"><div class="wert">%d%%</div>'
                 '<div class="was">Nennungen (%d von %d Fragen)</div></div>'
                 % (auswertung["quote"], auswertung["genannt"],
                    auswertung["gefragt"]))
    else:
        t.append('<div class="kennzahl"><div class="wert">—</div>'
                 '<div class="was">Nennungen noch nicht erhoben</div></div>')
    t.append("</div>")

    # ---- Teil 1
    t.append("<h2>Teil 1 — Maschinell geprüft</h2>")
    t.append("<p>Diese Prüfungen laufen automatisch und lassen sich "
             "jederzeit wiederholen. Sie beantworten eine Frage: "
             "<b>Könnte ein KI-System diese Website überhaupt lesen und "
             "daraus zitieren?</b></p>")
    for b in befunde:
        klasse = "ja" if b.bestanden else ("nein" if b.bestanden is False
                                           else "offen")
        marke = {"ja": "erfüllt", "nein": "nicht erfüllt",
                 "offen": "nicht geprüft"}[klasse]
        t.append('<div class="befund %s"><div class="zeile">'
                 '<span class="feld">%s</span>'
                 '<span class="marke-%s">%s</span></div>'
                 % (klasse, _s(b.feld), klasse, marke))
        t.append("<p>%s</p>" % _s(b.aussage))
        if b.massnahme:
            t.append('<div class="tat"><b>Zu tun:</b> %s</div>'
                     % _s(b.massnahme))
        if b.belege:
            t.append('<div class="belege">%s</div>'
                     % _s(" · ".join(str(x) for x in b.belege[:6])))
        t.append("</div>")
    t.append('<div class="hinweis">Gewichtete Punkte: <b>%d von %d</b>. '
             'Nicht geprüfte Felder zählen nicht mit.</div>'
             % (erreicht, moeglich))

    # ---- Teil 2
    t.append("<h2>Teil 2 — Was die KI-Systeme tatsächlich antworten</h2>")
    if not erhebung or not erhebung.daten.get("antworten"):
        t.append('<div class="hinweis"><b>Noch nicht erhoben.</b> Dieser '
                 'Teil enthält ausschliesslich im Wortlaut erfasste '
                 'Antworten. Es wird nichts geschätzt und nichts '
                 'simuliert — solange nichts erfasst ist, steht hier '
                 'nichts.</div>')
    else:
        t.append("<table><tr><th>System</th><th>Fragen</th>"
                 "<th>genannt</th><th>Quote</th></tr>")
        for system, e in sorted(auswertung["je_system"].items()):
            quote = round(100.0 * e["genannt"] / e["gefragt"]) \
                if e["gefragt"] else 0
            t.append("<tr><td>%s</td><td class=\"zahl\">%d</td>"
                     "<td class=\"zahl\">%d</td>"
                     "<td class=\"zahl\">%d%%</td></tr>"
                     % (_s(system), e["gefragt"], e["genannt"], quote))
        t.append("</table>")
        t.append("<h3>Die Antworten im Wortlaut</h3>")
        for a in erhebung.daten["antworten"]:
            t.append('<div class="antwort">')
            t.append('<div class="oben">%s · erfasst %s</div>'
                     % (_s(a["system"]), _s(a.get("erfasst", ""))))
            t.append('<div class="frage">%s</div>' % _s(a["frage"]))
            t.append("<blockquote>%s</blockquote>" % _s(a["wortlaut"]))
            if a.get("quellen"):
                t.append('<div class="belege">Genannte Quellen: %s</div>'
                         % _s(" · ".join(a["quellen"])))
            t.append("</div>")

    # ---- Was jetzt
    offen = [b for b in befunde if b.bestanden is False and b.massnahme]
    offen.sort(key=lambda b: -b.gewicht)
    t.append("<h2>Was zuerst zu tun ist</h2>")
    if offen:
        t.append("<p>Nach Wirkung sortiert. Oben steht, was am meisten "
                 "bringt.</p><table><tr><th>#</th><th>Feld</th>"
                 "<th>Massnahme</th></tr>")
        for i, b in enumerate(offen[:6], 1):
            t.append("<tr><td class=\"zahl\">%d</td><td>%s</td><td>%s</td></tr>"
                     % (i, _s(b.feld), _s(b.massnahme)))
        t.append("</table>")
    else:
        t.append("<p>Technisch ist alles Geprüfte erfüllt. Der Hebel "
                 "liegt dann bei den Inhalten, nicht bei der Technik.</p>")

    t.append('<div class="hinweis"><b>Was dieser Bericht nicht behauptet.</b> '
             'Er sagt nicht voraus, wie viele Anfragen eine Massnahme '
             'bringt. Er zeigt, was heute messbar ist, und was sich daran '
             'ändern lässt. Ob aus besserer Auffindbarkeit mehr Nennungen '
             'werden, zeigt die nächste Messung — nicht dieser Text.</div>')

    t.append('<footer>CITED · Rapperswil-Jona · Erstellt am %s. '
             'Teil 1 ist reproduzierbar: dieselbe Prüfung, dieselbe '
             'Website, dasselbe Ergebnis.</footer>' % _s(datum))
    t.append("</div></body></html>")
    return "\n".join(t)
