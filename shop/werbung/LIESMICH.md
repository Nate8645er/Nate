# Werbebilder Let'sDrink

Erzeugt am 10.8.2026 aus den echten Studio-Freistellern des Produkts.
Nichts hineinretuschiert, nichts hinzuerfunden - nur skaliert,
beschnitten und auf eine Studioflaeche gesetzt.

## Formate je Entwurf
- `_1080x1080` Feed (Instagram, Meta)
- `_1080x1920` Story, Reel, TikTok
- `_1200x628`  Meta-Linkanzeige

## Die fuenf Entwuerfe
| Datei | Aussage | Einsatz |
|---|---|---|
| `C-napf_*` | "Der Napf ist fest angebaut." | **Startmotiv fuer kalte Zielgruppen.** Grosser Anschnitt, traegt auch im Daumenbild. Aussage und Beleg im selben Bild. |
| `B-farben_*` | "Sechs Farben." | Zweitmotiv. Beantwortet "welche nehme ich". Im Feed werden die einzelnen Flaschen klein - besser als Story und Querformat. |
| `E-fakten_*` | "Auf einen Blick." | Retargeting. Das 1200x628 ist die beste Linkanzeige der Reihe, fuer kaltes Publikum zu textlastig. |
| `A-hand_*` | "Eine Hand reicht." | Zweite Welle. Der Satz behauptet Einhandbedienung, das Bild kann sie nicht zeigen - eine Hand daneben waere ein Groessenvergleich, den wir nicht belegen koennen. |
| `D-volumen_*` | "550 ml" | NICHT als Anzeige schalten. Handwerklich das sauberste Plakat, inhaltlich das schwaechste: 550 ml ist kein Kaufgrund. Taugt als Banner im Shop. |

`kontaktbogen-*.png` zeigt alle fuenf Entwuerfe je Format nebeneinander.

## Was bewusst NICHT drin ist
Keine Bewertung, kein Stern, keine Kundenzahl - der Shop hat null
Bestellungen. Keine Dringlichkeit, kein Countdown, kein Streichpreis.
Als Produktangabe nur "550 ml" und "Sechs Farben" plus die Namen der
sechs echten Farben. Kein Gegenstand, keine Hand und kein Tier neben
der Flasche: das waere ein Groessenvergleich, und die Masse des
Produkts liegen uns nicht vor. Die Flasche steht ueberall aufrecht.

## Neu bauen
`python3 c_napf.py` und so weiter; `lib_studio.py` ist der gemeinsame
Renderer (Zyklorama, zwei gestapelte Schatten, Laufweite von Hand).
Die Freisteller kommen aus dem Ordner mit den Produktbildern.

## Naechster Schritt
Fuer Reels und TikTok fehlt jedes Bewegtformat. Naheliegend waere eine
Sequenz von C (Anschnitt) nach B (Farbreihe).
