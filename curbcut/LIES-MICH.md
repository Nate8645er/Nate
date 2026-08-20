# Curbcut

Prueft das ausgelieferte HTML einer Webseite auf die sechs Fehlerarten,
die zusammen rund 96 Prozent aller Barrierefreiheits-Verstoesse ausmachen -
und sagt, an welcher Stelle im Quelltext sie entstehen.

    python3 kern/pruefen.py https://beispiel.ch
    python3 betrieb/waechter.py dazu https://beispiel.ch kundenname
    python3 betrieb/waechter.py            # taeglicher Lauf
    python3 betrieb/rechnung.py            # was es kostet und traegt
    python3 betrieb/reihe.py betrieb/liste.txt   # viele Seiten messen

## Warum Quelltext und nicht Browser

Wer eine Seite beanstandet, liest das HTML, das der Server schickt. Ein
Overlay-Widget aendert nur den Baum im Browser. Darum fallen Overlays vor
Gericht durch - und ziehen Klagen an: rund ein Viertel der Klagen 2024
traf Seiten, auf denen bereits so ein Widget lief.

## Was es nicht behauptet

Nie, dass eine Seite rechtskonform ist. Das kann kein Programm feststellen.
Automatisch pruefbar ist der Teil der Kriterien, der die grosse Masse der
Fehler ausmacht. Der Rest braucht einen Menschen.

## Eigene Messung, 19.8.2026

30 Schweizer Adressen angefragt, 18 gelesen (12 sperren automatische
Zugriffe). Ergebnis:

- 17 von 18 Seiten (94 Prozent) hatten mindestens einen Fehler
- 12 von 18 (67 Prozent) hatten sperrende Fehler
- 373 Vorkommen verteilten sich auf 71 Stellen im Quelltext

Zum Vergleich: Die WebAIM-Million-Auswertung von einer Million Startseiten
kommt auf 95,9 Prozent. Rohdaten in betrieb/reihe.json.
