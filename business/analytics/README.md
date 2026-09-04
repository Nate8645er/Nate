# Auswertung

Hier liegen die Messungen, aus denen später ein Verlauf wird.

## verlauf/

Eine Datei je Kunde und Monat, erzeugt aus derselben Prüfung:

```bash
python3 ../product/sichtbarkeit/cited.py pruefen <domain> --json \
  > verlauf/<kunde>-$(date +%Y-%m).json
```

**Warum das der Kern von Stufe 3 ist:** Die monatliche Gebühr ist nur
begründbar, wenn eine Veränderung nachweisbar ist. Zwei Messungen
derselben Prüfung sind der Nachweis. Ohne diesen Ordner ist die
Beobachtung ein Abo ohne Gegenwert.

**Warum die Prüfung reproduzierbar sein muss:** Teil 1 des Audits
liefert bei gleicher Website dasselbe Ergebnis. Nur deshalb ist eine
Differenz zwischen zwei Monaten eine Aussage über die Website und nicht
über das Werkzeug.

## Was hier NICHT liegt

Keine geschätzten Zahlen, keine Hochrechnungen, keine
Vorher-Nachher-Vergleiche ohne zwei echte Messungen. Eine erfundene
Verbesserung wäre der schnellste Weg, den einzigen Vorteil dieses
Angebots zu verlieren.

## Stand

**Leer.** Es gibt noch keinen Kunden und damit keine Messreihe.
