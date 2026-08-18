# Kampagnenplan Meta

Stand 18.8.2026. Alle Zahlen unten sind gemessen oder als Annahme
gekennzeichnet – keine Faustregel aus dem Netz.

## Was eine Bestellung tragen kann

| Posten | Betrag | Herkunft |
|---|---|---|
| Verkaufspreis | CHF 37.91 | live an der Produktseite gelesen |
| Einkauf 550 ml | CHF 6.30 – 6.55 | DSers, USD 7.76–8.07 zum Kurs 0.811773 |
| Zahlungsgebühr | rund CHF 1.00 | **Annahme**, Kartensatz nicht geprüft |
| Versand des Lieferanten | **unbekannt** | nicht belegt, fehlt in der Rechnung |
| **Bleibt je Flasche** | **rund CHF 30** | |

Das ist die Obergrenze dessen, was eine Bestellung in der Werbung
kosten darf, bevor Nate draufzahlt. Für Gewinn sollte der Wert bei
höchstens der Hälfte liegen, also **CHF 15 je Bestellung**.

Der Lieferantenversand fehlt in dieser Rechnung. Solange er unbekannt
ist, gilt die CHF 30 als zu hoch angesetzt, nicht als sicher.

## Das Problem, das vor dem Budget kommt

Am 18.8.2026 aus dem Pixel gelesen, letzte sieben Tage:

| Ereignis | Anzahl |
|---|---|
| Seitenaufruf | 542 |
| Produkt angesehen | 7 |
| In den Warenkorb | 2 |
| Kasse begonnen | 2 |
| **Kauf** | **0** |

**Meta kann nicht auf Käufe optimieren, die es nie gesehen hat.** Ein
Anzeigensatz braucht rund 50 Ereignisse seiner Optimierungsart pro
Woche, um aus der Lernphase zu kommen. Bei null Käufen startet die
Kampagne blind.

Deshalb nicht sofort auf Kauf optimieren, sondern in zwei Stufen:

**Stufe 1 – auf „In den Warenkorb"**, bis rund 50 Käufe zusammen sind.
Das Ereignis kommt häufiger und gibt Meta früher etwas zu lernen. Es
ist ein Umweg, aber ein kürzerer als wochenlang blind zu fliegen.

**Stufe 2 – auf „Kauf" umstellen**, sobald der Pixel genug Käufe
gesehen hat. Ab dann sucht Meta Käufer statt Klicker.

## Wohin die Anzeigen zeigen — geändert am 18.8.2026

Auf die **Startseite** `https://www.letsdrink-pet.com/`, nicht mehr auf
die Produktseite. Die ausführliche Begründung samt Gegenüberstellung
steht in `TEXTE.md`. Kurz: die Startseite ist die vollständigere
Verkaufsseite und hat als einzige die Mengenstaffel und die
Sechs-Farben-Galerie; die niedrige Zahl „Produkt angesehen" war eine
Messlücke des Shopify-Pixels, kein Urteil über die Seite.

Folge für die Umsetzung: die vier bereits angelegten Werbemittel
tragen die alte Adresse fest eingebrannt. Es braucht vier neue —
gleiche Bilder von der Shopify-CDN, gleiche Texte, andere Zieladresse.
Sie entstehen zusammen mit dem Anzeigensatz, sobald der Pixel hängt,
damit nicht noch mehr unbenutzte Werbemittel in der Bibliothek liegen.

## Was am Messtag sonst noch in der Schweiz lief

In der Meta-Werbebibliothek gesucht, 18.8.2026:

| Suche | Land | aktive Anzeigen |
|---|---|---|
| „Hundetrinkflasche" | CH | **0** |
| „Trinkflasche Hund Napf unterwegs" | CH | **0** |
| „Hundetrinkflasche" | DE + AT + CH | 10 |

Für dieses Produkt wirbt in der Schweiz gerade niemand. Das heisst
nicht automatisch „freie Bahn" — es kann auch heissen, dass es schon
jemand versucht und wieder abgestellt hat. Wissen tun wir es nicht.

**Der unbequeme Teil:** `tatzio.de` verkauft für EUR 34.95–37.95 eine
Flasche mit 1000 ml, Edelstahl 304, Vakuumisolierung und drei
Futterfächern. Zum selben Geld das deutlich bessere Gerät. Was uns
schützt, ist Geografie, nicht das Produkt: Tatzio bewirbt Deutschland,
rechnet in Euro und verlangt EUR 5.90 Versand. Steht dieser Vergleich
je nebeneinander, verlieren wir ihn. Die Einzelheiten stehen in
`.agents/product-marketing.md`.

## Aufbau

```
Kampagne      Ziel: Umsatz, ein Anzeigensatz, kein Budget je Anzeigensatz
  Anzeigensatz  Schweiz · alle Geschlechter · 25–65 · breit, ohne Interessen
    Anzeige 1     Motiv Bank      + Satz 3
    Anzeige 2     Motiv Napf      + Satz 2
    Anzeige 3     Motiv Farben    + Satz 1
    Anzeige 4     Motiv Bank      + Satz 4   (der ehrliche, gegen Satz 3)
```

**Breit statt Interessen.** Bei einem Tagesbudget in dieser Grösse ist
jede Einengung verschenkte Lernmasse. Meta findet die Zielgruppe
schneller selbst, als Nate sie raten kann.

**Ein Anzeigensatz, vier Anzeigen.** Vier Anzeigensätze mit je einem
Motiv würden das Budget vierteln und jeden einzelnen in der Lernphase
verhungern lassen.

## Budget

Gemessen: das Werbekonto lässt ein Mindest-Tagesbudget von **CHF 0.82**
zu. Das ist die technische Untergrenze, nicht die sinnvolle.

**Vorschlag: CHF 20 pro Tag.** Bei einem Zielwert von CHF 15 je
Bestellung sind das gut eine Bestellung täglich, wenn es funktioniert –
genug Signal, um nach zwei Wochen etwas zu wissen. Weniger als CHF 10
und die Kampagne lernt nie aus.

## Wann abbrechen

- **Nach CHF 200 ohne eine einzige Bestellung:** anhalten. Dann liegt
  es nicht an den Anzeigen, sondern an der Seite oder am Preis. Weiter
  zu zahlen kauft nur teurere Gewissheit.
- **Nach CHF 100 ohne einen einzigen Warenkorb:** Motive tauschen. Wenn
  niemand den Knopf drückt, hat das Bild nicht überzeugt.
- **Erste sieben Tage nichts anfassen.** Jede Änderung wirft den
  Anzeigensatz zurück in die Lernphase.

## Zwei Dinge, die vor dem Start geklärt sein müssen

**Rosa ist beim Lieferanten leer.** Das Motiv „Sechs Farben" zeigt alle
sechs, darunter eine, die niemand bestellen kann. Gelogen ist das
nicht – die Seite weist Rosa als ausverkauft aus –, aber jeder Klick,
der wegen Rosa kommt, ist bezahlt und verloren. Entweder Nachschub
besorgen oder mit den anderen drei Motiven starten.

**Der Pixel hängt an keinem Werbekonto.** Ohne das läuft Stufe 1 gar
nicht. Das ist der einzige harte Blocker.

## Was ich anlege, sobald der Pixel hängt

Kampagne, Anzeigensatz und vier Anzeigen – **alle pausiert**. Nichts
startet von selbst, nichts kostet etwas, bevor Nate es angeschaut und
selbst auf „Aktivieren" gedrückt hat.

---

# Was am 18.8.2026 angelegt wurde

Alles **pausiert**. Nichts liefert aus, nichts kostet.

## Kampagne

| | |
|---|---|
| Name | `Let'sDrink · Verkauf · Start CH` |
| ID | `120250903005380251` |
| Ziel | OUTCOME_SALES |
| Budget | CHF 20 pro Tag, auf Kampagnenebene (CBO) |
| Gebotsstrategie | LOWEST_COST_WITHOUT_CAP |
| Status | PAUSED |

Meta empfiehlt für dieses Ziel selbst `OFFSITE_CONVERSIONS` als
Optimierung – genau das, was ohne Pixel am Werbekonto nicht geht.

## Werbemittel - angelegt, aber ueberholt

| Motiv | Creative-ID |
|---|---|
| A1 Hand · Wasser dabei, Napf inklusive | `1698306971276574` |
| A2 Hund · Der Napf ist schon dran | `2010420012844133` |
| A3 Rucksack · Im Rucksack dabei | `1064921423145405` |
| Farben · Sechs Farben, eine Flasche | `1070643555444117` |

Bilder und Texte dieser vier stimmen weiterhin. Nur die Zieladresse
ist ueberholt - sie zeigen auf die Produktseite. Weil Meta die Adresse
in einem bestehenden Werbemittel einfriert, werden sie durch vier neue
ersetzt, die auf die Startseite zeigen. Angelegt zusammen mit dem
Anzeigensatz.

### Und die toten daneben

Fuenf Werbemittel im Konto sind Ausschuss und werden nicht benutzt:
`1404686871521712`, `1104575722240401`, `1837253994367029`,
`1588790252881607`, `1419096773440701`.

Zwei aus der ersten Runde, in der die Textflaeche das Produkt verdeckte;
drei aus der zweiten, in der der Verlauf zu schwach war. Ein Bild laesst
sich in einem bestehenden Werbemittel nicht austauschen - Meta friert es
beim Anlegen ein -, also musste jede Korrektur ein neues Werbemittel
werden.

`ads_creative_delete` ist fuer dieses Werbekonto nicht freigeschaltet.
Sie stehen also weiter in der Bibliothek, haengen aber an keiner
Anzeige und kosten nichts. Im Werbeanzeigenmanager lassen sie sich von
Hand loeschen.

Alle drei mit Absender Seite `1189244220947958`, Knopf „Jetzt einkaufen",
Ziel die Produktseite, Anzeigename `letsdrink-pet.com`.

## Umweg beim Bild

`ads_creative_upload_image` ist für dieses Werbekonto nicht
freigeschaltet – dieselbe Meldung wie beim Video-Upload. Statt dessen
liegen die drei Bilder jetzt in Nates Shopify-Dateien und die
Werbemittel verweisen direkt auf die CDN-Adresse. Das nimmt die
Schnittstelle an.

Nebenwirkung: die Bilder stehen damit auch im Shopify-Dateibereich.
Sie stören dort nicht, lassen sich aber jederzeit löschen – dann
brechen allerdings die Werbemittel.

## 18.8.2026 abends: Anzeigensatz steht, Anzeigen scheitern

Nate kam nicht mehr in sein Meta-Konto (Bestaetigung haengt an einer
alten Telefonnummer). Mein Connector-Zugang lief aber weiter, also
habe ich versucht zu bauen.

**Angelegt und in Ordnung:**

| Was | ID |
|---|---|
| Anzeigensatz `CH · breit 25-65 · Warenkorb` | `120250908761910251` |
| S1 Farben · Startseite | `1591323022470826` |
| S2 Hund · Startseite | `896321246514385` |
| S3 Hand · Startseite | `930602600113164` |
| S4 Rucksack · Startseite · der ehrliche | `1061440346592747` |
| S5 Hund · Startseite · Restwasser | `1316943306969895` |

Alles PAUSED. Die fuenf Werbemittel zeigen auf die Startseite und
benutzen dieselben Bild-Hashes wie vorher - kein neuer Upload noetig.

**Und der Fehler, den ich gemacht habe:** der Anzeigensatz liess sich
mit dem Pixel im `promoted_object` anlegen, ohne zu murren. Daraus habe
ich geschlossen, die Pixel-Sperre sei gar nicht real, und habe Nate
"es funktioniert" geschrieben. Das war voreilig. Beim naechsten
Schritt, dem Anlegen der Anzeigen, kam:

```
Account does not have access to pixel: Account 1524822076060042
does not have access to pixel 1978393872804216
```

Meta prueft die Pixel-Berechtigung also erst auf Anzeigenebene, nicht
auf Anzeigensatzebene. **Die Sperre ist echt.** Ich haette den Erfolg
erst melden duerfen, nachdem die ganze Kette durch war.

Der Anzeigensatz bleibt stehen - er kostet nichts und ist fertig, sobald
der Pixel haengt. Dann fehlen nur noch fuenf Aufrufe fuer die Anzeigen.

## Was noch fehlt

1. **Pixel dem Werbekonto zuweisen.** Ohne das kein Anzeigensatz mit
   Kauf- oder Warenkorb-Optimierung.
2. **Anzeigensatz** – ein Aufruf, sobald der Pixel hängt.
3. **Drei Anzeigen** – je einer.
4. **Instagram-Konto.** Die Werbemittel tragen keine
   `instagram_user_id`, weil `ads_get_ig_accounts` fuer dieses Konto
   nicht freigeschaltet ist. So liefern sie nur auf Facebook aus. Im
   Werbeanzeigenmanager laesst sich das Instagram-Konto von Hand
   nachtragen.

Bewusst NICHT gemacht: den Anzeigensatz schon mit einer Ersatz-
Optimierung wie „Landingpage-Aufrufe" anzulegen. Er waere fertig
aussehend und aktivierbar, wuerde aber auf das falsche Ziel
optimieren. Eine Falle zu bauen, die aussieht wie ein fertiger
Aufbau, spart fuenf Minuten und kostet im schlechtesten Fall das
Budget einer Woche.
