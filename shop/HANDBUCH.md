# Handbuch Let'sDrink

Übergabe an Nate, den Inhaber. Stand: 5. August 2026.

Dieses Handbuch ist für dich geschrieben, nicht für Programmierer. Es sagt,
was der Shop heute kann, wo welcher Text steht, was du selbst ändern kannst
und was du besser nicht anfasst.

Zwei Begriffe, die immer wieder vorkommen:

| Begriff | Was das heisst |
|---|---|
| **Adminbereich** | Die Verwaltung deines Shops. Du meldest dich auf shopify.com an und siehst links eine Spalte mit "Bestellungen", "Produkte", "Onlineshop", "Einstellungen". Dort änderst du Dinge per Mausklick. |
| **Theme** | Das Kleid des Shops. Eine Sammlung von Dateien, die bestimmt, wie jede Seite aussieht und welcher Text darauf steht, wenn er nicht aus dem Adminbereich kommt. Ein Theme ändert man nur im Code. |

Wichtig zur Einordnung: Die Angaben in Kapitel 1 stammen aus dem Bauplan des
Projekts. Die Theme-Dateien liegen bei Shopify, nicht auf diesem Rechner. Ich
konnte sie deshalb nicht Zeile für Zeile nachlesen. Wo etwas ungeprüft ist,
steht das ausdrücklich dabei. Kapitel 7 listet alle offenen Punkte.

---

## 1. Was der Shop ist und woraus jede Seite entsteht

Let'sDrink ist ein Ein-Produkt-Shop. Verkauft wird eine Trinkflasche mit fest
angebautem Napf für Hunde und Katzen, 550 ml, in sechs Farben, zu CHF 39.90.
Gratisversand in der Schweiz, 14 Tage Rückgabe, Lieferzeit 7 bis 14 Werktage,
nur für Wasser. Höchstens 6 Flaschen pro Bestellung.

Shop-Adresse: www.katzenufos.com (technische Zweitadresse:
i0m1xi-h5.myshopify.com — dieselbe Seite, andere Tür).

### Welche Seite kommt aus welcher Datei

| Seite im Shop | Datei im Theme | Zusätzliche Gestaltungsdatei |
|---|---|---|
| Kopfzeile und Fussbereich auf **allen** Seiten | `layout/theme.liquid` | `assets/v2-core.css` |
| Startseite | `templates/index.liquid` | `assets/v2-home.css` |
| Produktseite (die Flasche) | `templates/product.liquid` | `assets/v2-product.css` |
| Alle Inhaltsseiten: Versand & Rückgabe, Impressum, AGB, Datenschutz, Über uns | `templates/page.liquid` | `assets/v2-pages.css` |
| Warenkorb | `templates/cart.liquid` | `assets/v2-cart.css` |
| Suche | `templates/search.liquid` | `assets/v2-misc.css` |
| Seite-nicht-gefunden (Fehler 404) | `templates/404.liquid` | `assets/v2-misc.css` |
| Kollektionsseite (Produktliste) | `templates/collection.liquid` | `assets/v2-misc.css` |
| Blog und einzelner Blogbeitrag | `templates/blog.liquid`, `templates/article.liquid` | `assets/v2-misc.css` |
| Geschenkkarte | `templates/gift_card.liquid` | `assets/v2-misc.css` |

### Bausteine, die keine eigene Seite sind

| Baustein | Datei | Was er macht |
|---|---|---|
| Kaufmechanik | `assets/premium.js` | Mengenwahl, Farbwahl, Kaufleiste, Preisanzeige. Das Herz des Verkaufs. |
| Drehbare Flasche | `assets/v3-bottle.js`, `assets/v3-bottle.css` | Die Flasche, die man mit der Maus drehen kann, in sechs Farben. |
| Animierte Erklärbilder | `snippets/steps-ani.liquid`, `assets/v3-steps.css` | Zeigt den Knopfdruck und wie sich der Napf füllt. |
| Bewegung und Einblendungen | `assets/v2-motion.js` | Entscheidet, wie viel Animation ein Gerät verträgt. |

**Merke:** Wenn jemand sagt "das steht in `product.liquid`", meint er die
Produktseite. Der Dateiname ist immer der Hinweis auf die Seite.

---

## 2. Text ändern: was im Adminbereich geht und was nicht

Das ist der Punkt, der dich schon einmal Stunden gekostet hat. Deshalb zuerst
die Regel, mit der du es in einer Minute selbst herausfindest:

> **Die Ein-Minuten-Probe**
> Ändere den Text im Adminbereich und speichere. Lade danach die Seite im Shop
> neu (Strg + F5). Steht der neue Text da, war es die richtige Stelle.
> Steht der alte Text da, steckt dieser Text fest im Theme und ist im
> Adminbereich nicht auffindbar. Dann brauchst du Hilfe am Code.

### Was du im Adminbereich selbst änderst

| Was | Wo im Adminbereich |
|---|---|
| Produktname, Produktbeschreibung, Produktfotos | Produkte → die Flasche anklicken |
| Preis, auch pro Farbe | Produkte → die Flasche → Abschnitt "Preisgestaltung" bzw. "Varianten" |
| Lagerbestand | Produkte → die Flasche → "Bestand" |
| Rabatte (Mengenrabatt, Gutscheincodes) | Rabatte |
| Inhalt der Seiten Versand & Rückgabe, Impressum, AGB, Datenschutz | Onlineshop → Seiten |
| Menüpunkte oben und unten | Onlineshop → Menüs |
| Versandkosten und Versandzonen | Einstellungen → Versand und Zustellung |
| Zahlungsarten (TWINT, Karten, PayPal) | Einstellungen → Zahlungen |
| Texte der Bestellbestätigungs-Mails | Einstellungen → Benachrichtigungen |
| Shop-Name (siehe Kapitel 6) | Einstellungen → Allgemein |

### Was nur im Theme-Code steht

Diese Texte findest du im Adminbereich **nicht**, egal wie lange du suchst.
Sie sind beim Bau direkt in die Theme-Dateien geschrieben worden.

| Text | Steckt in | Anmerkung |
|---|---|---|
| Alle Fragen und Antworten der FAQ | Theme-Code der Produktseite (`templates/product.liquid`) | Genau das hat dich Zeit gekostet. Die FAQ ist keine Seite im Adminbereich. |
| Überschriften und Fliesstext der Startseite | `templates/index.liquid` | Zum Beispiel "So funktioniert's", die Vergleichspunkte, Nates Notiz. |
| Sätze im Fussbereich, etwa "Versand aus der Schweiz" | `layout/theme.liquid` | Ungeprüft: laut Bauplan gehört der Fussbereich zu dieser Datei. |
| Die Mengen- und Rabattdarstellung auf der Produktseite | `templates/product.liquid` und `assets/premium.js` | Die Beträge selbst kommen aus dem Produktpreis, siehe Kapitel 4. |

### Wenn du einen Theme-Text wirklich selbst ändern willst

1. Adminbereich → Onlineshop → Themes.
2. Beim gewünschten Theme rechts auf die drei Punkte (…) → **Code bearbeiten**.
3. Links die Datei aus der Tabelle oben anklicken.
4. Mit Strg + F den Text suchen, den du ändern willst.
5. Nur den Text zwischen den Wörtern ändern. Nichts mit spitzen Klammern
   `< >`, keine geschweiften Klammern `{{ }}`, keine Anführungszeichen löschen.
6. Speichern.

**Vier Warnungen dazu:**

- Änderst du das **veröffentlichte** Theme, ist die Änderung sofort für jeden
  Besucher sichtbar. Es gibt kein "Vorschau" und kein "später".
- Ein fehlendes Zeichen kann eine ganze Seite weiss machen.
- Sicherer Weg: Theme vorher duplizieren (drei Punkte → Duplizieren), im
  Duplikat ändern, ansehen, dann veröffentlichen.
- Solange die sechs Bau-Trupps am neuen Theme arbeiten, fasse dort nichts an.
  Sonst geht deine Änderung beim nächsten Hochladen verloren.

---

## 3. Die roten Linien

Drei Regeln, die niemand im Projekt überschreitet, auch du nicht. Jeweils mit
dem Grund, denn Regeln ohne Grund vergisst man.

### Nie das Wort "auslaufsicher" — und auch kein Bild, das es behauptet

Dein Lieferant hat dir nirgends schriftlich bestätigt, dass die Flasche unter
allen Umständen dicht bleibt. Wer eine Eigenschaft bewirbt, die er nicht
belegen kann, macht ein Versprechen, für das er geradesteht: jede undichte
Flasche wird dann zu deiner Rechnung, plus Rücksendung, plus verärgerter
Kunde.

Das gilt auch ohne Worte. Ein Bild einer kopfstehenden Flasche, aus der nichts
läuft, ist dieselbe Behauptung — deshalb wird die Flasche nirgends im Shop auf
dem Kopf gezeigt.

Erlaubt und gewollt ist stattdessen dieser abgestimmte Satz:

> Wir haben keine schriftliche Zusicherung des Lieferanten, dass sie unter
> allen Umständen dicht ist – deshalb behaupten wir es auch nicht.
> Transportiere sie am besten aufrecht. Läuft deine Flasche trotzdem aus,
> ist das ein Reklamationsfall: Du bekommst Ersatz oder dein Geld zurück.

Aus demselben Grund stehen im Shop **keine** Materialangaben, keine Masse
ausser 550 ml, kein "BPA-frei" und kein "spülmaschinenfest". Was der Lieferant
nicht bestätigt hat, schreiben wir nicht hin.

### Keine erfundenen Bewertungen, keine künstliche Eile

Sterne, Kundenstimmen oder Verkaufszahlen, die es nicht gibt, sind in der
Schweiz unlauterer Wettbewerb (UWG) und können dir eine Anzeige einbringen.
Dazu kommt das Praktische: Dein einziges Kapital ist, dass man dir glaubt —
eine einzige erfundene Stimme entwertet jeden ehrlichen Satz daneben.

Dasselbe gilt für "nur noch 3 auf Lager" und Countdown-Uhren. Dein Shop ist
neu, das ist kein Makel, und Druck ersetzt kein Vertrauen.

### Der beworbene Preis muss dem Preis an der Kasse entsprechen

Die Schweizer Preisbekanntgabeverordnung verlangt, dass der Betrag, den du
irgendwo anschreibst, genau der Betrag ist, den der Kunde an der Kasse zahlt.
Steht auf der Seite CHF 79.80 und die Kasse verlangt CHF 119.70, ist das ein
Rechtsverstoss — und der Kunde bricht ohnehin ab.

Deshalb werden im Shop keine Preise ausgerechnet, sondern nur die tatsächlich
im Warenkorb gemessenen Beträge angezeigt. Siehe das nächste Kapitel.

---

## 4. Die gemessenen Preise

Diese Tabelle wurde am 3. August 2026 in einem echten Warenkorb gemessen, mit
echtem Klicken bis zur Kasse. Sie ist nicht ausgerechnet.

| Menge | Du zahlst für | Gratis | Total CHF |
|---|---|---|---|
| 1 | 1 | 0 | 39.90 |
| 2 | 2 | 0 | 79.80 |
| 3 | 2 | 1 | 79.80 |
| 4 | 3 | 1 | 119.70 |
| 5 | 3 | 2 | 119.70 |
| 6 | 4 | 2 | 159.60 |

Höchstens 6 Flaschen pro Bestellung.

Daraus folgt: 2 Flaschen kosten gleich viel wie 3, und 4 kosten gleich viel
wie 5. Wer 2 oder 4 bestellt, verschenkt eine Flasche. Deshalb lohnen sich
für den Kunden die Mengen 1, 3, 5 und 6.

### Die Warnung dazu — bitte ernst nehmen

Bei dir laufen **zwei automatische Rabatte gleichzeitig**. Shopify wendet pro
Bestellung den jeweils besseren an. Welcher das ist, lässt sich nicht sicher
vorhersagen, sondern nur messen.

**Sobald du an einem Rabatt etwas änderst, ihn löschst, verlängerst oder einen
dritten hinzufügst, ist diese Tabelle ungültig.** Dann musst du sie neu
messen, bevor die Zahlen irgendwo im Shop stehen bleiben dürfen. So geht das:

1. Im Shop 1 Flasche in den Warenkorb legen, Total notieren.
2. Menge auf 2 erhöhen, Total notieren. Dann 3, 4, 5, 6 — jedes Mal notieren.
3. Die sechs Beträge mit der Tabelle oben vergleichen.
4. Weicht ein Betrag ab, darf die alte Tabelle nirgends mehr im Shop stehen.
   Die Zahlen stehen auf der Startseite, auf der Produktseite und in der FAQ —
   also im Theme-Code. Melde die neuen Werte, bevor du irgendwo verkaufst.

---

## 5. Ein Theme veröffentlichen und wieder zurücknehmen

### Die Ausgangslage

| Theme | Zustand | Was es ist |
|---|---|---|
| `ki-shop-theme-8` | **live** | Was deine Besucher heute sehen. |
| **Let'sDrink NEU** (Nummer 197118132601) | Entwurf | Das neue Theme, an dem gebaut wird. |
| Let'sDrink Premium (Nummer 196902617465) | Entwurf | Ältere Ausbaustufe. Nicht veröffentlichen. Ungeprüft, ob sie noch in deiner Liste steht. |

Solange du nicht ausdrücklich Ja sagst, bleibt das neue Theme ein Entwurf.
Kein Team im Projekt schaltet etwas live.

### Vorher ansehen, ohne dass es jemand sieht

1. Adminbereich → Onlineshop → Themes.
2. Beim Theme unter "Theme-Bibliothek" auf die drei Punkte (…) → **Vorschau**.

Alternativ direkt im Browser:
`www.katzenufos.com/?preview_theme_id=197118132601`

Nimm den Weg über www.katzenufos.com, nicht über die myshopify-Adresse — dort
geht die Vorschau nach dem ersten Klick verloren.

### Veröffentlichen

1. Adminbereich → Onlineshop → Themes.
2. Unter "Theme-Bibliothek" das Theme **Let'sDrink NEU** suchen.
3. Rechts auf die drei Punkte (…) → **Veröffentlichen** → bestätigen.
4. Sofort danach www.katzenufos.com in einem privaten Browserfenster öffnen
   und prüfen: Startseite, Produktseite, eine Flasche in den Warenkorb,
   Total mit der Tabelle in Kapitel 4 vergleichen.

Das dauert Sekunden und ist ab dem Klick für alle sichtbar.

### Zurücknehmen

Genau derselbe Weg, nur mit dem alten Theme:

1. Adminbereich → Onlineshop → Themes.
2. `ki-shop-theme-8` in der Theme-Bibliothek suchen.
3. Drei Punkte (…) → **Veröffentlichen** → bestätigen.

Nach wenigen Sekunden ist wieder alles wie vorher.

### Was ein Theme-Wechsel **nicht** anrührt

Deine Bestellungen, Kunden, Produkte, Preise, Rabatte, Seiteninhalte,
Versandeinstellungen und Zahlungsarten bleiben unverändert. Ein Theme ist nur
das Kleid. Veröffentlichen löscht auch das alte Theme nicht — es rutscht nur
zurück in die Bibliothek.

---

## 6. Was nur du selbst tun kannst: den Shop-Namen ändern

Dein Shop heisst intern noch **"My Store"**. Dieser Name erscheint im
Browser-Reiter, in jeder Bestellbestätigung, in jeder E-Mail an Kunden und auf
Belegen. Er muss auf **Let'sDrink** geändert werden.

Das geht über die technische Schnittstelle nicht — Shopify lässt Shop-Daten
nur den angemeldeten Inhaber ändern. Niemand kann dir das abnehmen.

So geht es:

1. Im Adminbereich anmelden.
2. Ganz unten links auf **Einstellungen**.
3. Reiter **Allgemein**, Abschnitt **Shop-Details**.
4. Feld **Shop-Name**: `My Store` löschen, `Let'sDrink` eintragen.
5. Oben rechts **Speichern**.

Prüfe danach den Reiter im Browser und schicke dir selbst eine Testbestellung,
damit du siehst, was in der Bestätigungsmail steht.

Ungeprüft: Ob im selben Abschnitt noch eine Kontaktadresse oder ein
Absendername auf "My Store" steht, konnte ich nicht nachsehen. Schau beim
Ändern kurz die ganze Seite durch.

---

## 7. Grenzen dieses Handbuchs

Was ich **nicht** selbst prüfen konnte, weil die Theme-Dateien bei Shopify
liegen und nicht auf diesem Rechner:

- Ob jede Datei aus der Tabelle in Kapitel 1 heute wirklich existiert und
  genau diese Seite erzeugt. Die Tabelle stammt aus dem Bauplan vom 5.8.2026.
- Welche Texte im Detail im Theme stehen und welche aus dem Adminbereich
  kommen. Deshalb die Ein-Minuten-Probe in Kapitel 2 — sie ersetzt das Raten.
- Die genauen Beschriftungen im Shopify-Adminbereich. Shopify ändert sie
  gelegentlich. Die Reihenfolge der Schritte bleibt aber dieselbe.
- Wer den Rückversand bei einer Rückgabe zahlt. Das steht nirgends im Shop und
  wurde bewusst nicht erfunden. Du musst es festlegen.

Was bewusst **nicht** in diesem Handbuch steht:

- Anleitungen zum Programmieren. Die brauchst du nicht, und halbes Wissen am
  Code des laufenden Shops ist gefährlicher als kein Wissen.
- Die technischen Bauregeln der Teams. Die stehen im Bauplan des Projekts.
- Alles, was noch offen ist und deine Entscheidung braucht. Das steht in
  `ENTSCHEIDUNGEN.md` neben dieser Datei.
