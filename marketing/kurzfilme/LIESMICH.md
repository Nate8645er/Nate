# Drei Anfänge, ein Film

Drei Fassungen des Napf-Films für TikTok und Reels. Die Quelle ist in
allen dreien dieselbe – `shop/theme-nova/assets/a-film-napf.mp4`.
Verschieden ist nur, **womit sie anfangen**.

Das ist Absicht. Auf TikTok entscheidet die erste Sekunde über Bleiben
oder Weiterwischen, und der Anfang ist die einzige Stellschraube, die
sich sauber gegeneinander messen lässt: gleicher Film, gleicher Text,
gleiche Länge – nur ein anderer erster Blick. Was gewinnt, weiss man
danach.

| Datei | Anfang | Wofür der Anfang gedacht ist |
|---|---|---|
| `kurz-1-hund.mp4` | Der Hund trinkt, ganz nah | Das wärmste Bild steht in Sekunde null. Wer einen Hund hat, bleibt hängen, bevor er weiss, was das Produkt ist. |
| `kurz-2-knopf.mp4` | Die Hand am Knopf | Die Mechanik zuerst. Für alle, die nicht wissen, dass es so etwas gibt – der Aha-Moment kommt sofort statt nach vier Sekunden. |
| `kurz-3-frage.mp4` | Eine Frage über der Bank | Zwingt zum Mitdenken, bevor irgendetwas verkauft wird. Schliesst nebenbei aus, wer keinen Hund hat. |

Länge 10,6 bis 11,6 Sekunden, 720 × 1280, ohne Ton. Eine stumme
Tonspur ist trotzdem drin, weil manche Hochlade-Wege ohne Tonspur
zicken.

## Warum der Text im Bild steht

Auf TikTok läuft der Ton bei vielen aus. Der Text sitzt im oberen
Drittel: unten liegt die Bedienleiste der App, rechts die Knopfspalte
– beides verdeckt Text zuverlässig.

## Was in keinem der Texte steht

Keine Bewertungen, keine Verkaufszahlen, keine Dringlichkeit. Keine
Produktangabe ausser 550 ml und sechs Farben. Nichts zur Dichtigkeit.
Und die Flasche steht in keiner Einstellung auf dem Kopf.

Eine Zeile ist beim Bauen korrigiert worden: über der Rucksack-
Einstellung stand zuerst „Aufrichten – der Rest läuft zurück". Das
Aufrichten kommt im Film aber gar nicht vor, der Text hätte etwas
behauptet, was das Bild nicht zeigt. Jetzt steht dort, was man
wirklich sieht: die Öse für Band oder Karabiner.

## Neu bauen

`bauen.py` erzeugt alle drei aus der Quelldatei. Schnittmarken und
Texte stehen oben in der Datei, sonst muss nichts angefasst werden.

Zwei Dinge, die beim Bauen aufgefallen sind und im Skript dokumentiert
sind: das mitgelieferte ffmpeg hat **kein** `drawtext` (ohne freetype
gebaut), deshalb entstehen die Textkarten als PNG mit PIL und werden
überblendet. Und die Schnittmarken stammen aus einem Kontaktbogen mit
einem Bild pro Sekunde, nicht aus dem Gefühl.
