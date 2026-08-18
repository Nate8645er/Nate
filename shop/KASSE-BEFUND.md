# Die Kasse, nachgemessen

Stand 18.8.2026. Alles hier ist im Shopify-Konto abgefragt oder an der
ausgelieferten Seite gelesen. Keine Vermutung ohne Kennzeichnung.

---

## NACHTRAG vom selben Tag: das meiste unten steht auf zu duennem Eis

Nach einem neuen Meta-Zugang konnte ich den Pixel zum ersten Mal
stundenweise auslesen. Zwei Befunde entwerten die Grundlage dieses
Dokuments zum grossen Teil:

**Erstens: der Pixel gehoert zwei Laeden.** `1978393872804216` feuert
sowohl auf `letsdrink-pet.com` als auch auf `katzenufos.com`. Die
542 Seitenaufrufe, mit denen ich hier rechne, sind eine Mischung aus
beiden Shops. Die Zahl gilt nicht fuer Let'sDrink allein.

**Zweitens: die zwei Warenkoerbe und die zwei Kassengaenge liegen in
derselben einzigen Stunde** — 16.8.2026, 18 Uhr. Davor nichts, danach
nichts. Das sind mit grosser Wahrscheinlichkeit **nicht zwei Kunden,
sondern eine Sitzung**, moeglicherweise ein eigener Test.

Dasselbe Muster bei den sieben Produktansichten: alle sieben in einer
einzigen Stunde am 15.8.

**Was das bedeutet:** meine Aussage „der Abbruch liegt an der Kasse"
ist damit nicht mehr belegt. Wahrscheinlicher ist etwas Nuechterneres
— **es hat nie ein echter Kaeufer die Kasse erreicht.** Der Trichter
ist nicht kaputt; er ist leer.

**Was trotzdem stehen bleibt:** die Maengel 1 bis 5 unten sind alle
einzeln nachgemessen und real. Sie gehoeren behoben, weil sie falsch
sind — nicht, weil sie nachweislich Umsatz kosten. Diesen Nachweis
gibt es nicht. Insbesondere verliert die TWINT-Vermutung ihren
Hauptbeleg: sie stuetzte sich auf zwei Abbrueche, die vermutlich gar
keine Kundenabbrueche waren.

---

## Warum überhaupt hier suchen

| Ereignis | Anzahl |
|---|---|
| Seitenaufruf | 542 |
| In den Warenkorb | 2 |
| Kasse begonnen | 2 |
| **Kauf** | **0** |

Jeder, der den Warenkorb erreicht hat, ist auch zur Kasse gegangen.
Keiner hat gekauft. Das ist der einzige Ort im Laden, an dem
nachweislich etwas verloren geht.

**Wichtige Einschränkung vorweg:** das sind zwei Fälle. Zwei. Alles
unten ist eine Erklärung, die zu zwei Beobachtungen passt, keine
Statistik. Ich schreibe es trotzdem auf, weil die gefundenen Mängel
auch ohne diese zwei Fälle behoben gehören.

## Der Hinweis, der die Suche eingegrenzt hat

Shopify speichert **null** abgebrochene Warenkörbe. Der Pixel meldet
zwei begonnene Kassengänge.

Das ist kein Widerspruch, sondern eine Auskunft: Shopify legt einen
Abbruch erst an, wenn jemand seine Kontaktdaten eingetippt hat. Beide
sind also **in den ersten Sekunden** wieder raus — bevor sie
überhaupt etwas geschrieben haben.

Damit fallen die üblichen Verdächtigen weg. Es lag nicht an einem zu
langen Formular, nicht an Pflichtfeldern, nicht an Versandkosten, die
erst spät auftauchen. Es lag an dem, was man **sieht, bevor man
tippt.**

---

## Befund 1 — TWINT fehlt

An der ausgelieferten Seite gelesen, das sind die freigeschalteten
Zahlungsarten:

Visa · Mastercard · American Express · PayPal · Apple Pay ·
Google Pay · Klarna

**Kein TWINT. Kein PostFinance.**

Das sind die beiden Zahlungsarten, die in der Schweiz jeder hat. Ein
Schweizer Käufer, der bei einem Laden ohne eine einzige Bewertung zum
ersten Mal ist, tippt seine Kartennummer nicht ein — er sucht TWINT.
Findet er es nicht, geht er.

Das passt genau auf das Muster oben: rein, hingeschaut, raus, ohne zu
tippen.

**Das ist der wahrscheinlichste einzelne Grund.** Bewiesen ist es
nicht — zwei Fälle beweisen nichts —, aber es ist der Mangel mit dem
grössten Hebel und der einfachsten Behebung.

→ Nur Nate: Shopify-Konto → Einstellungen → Zahlungen.

## Befund 2 — die Absenderadresse des Ladens ist `Yourcatlove.info@gmail.com`

Neu gefunden. Im Konto stehen unter Absender- und Kontaktadresse beide
Male:

```
Yourcatlove.info@gmail.com
```

Von dieser Adresse kommt die Bestellbestätigung. Wer eine
Hundetrinkflasche in der Schweiz kauft und eine Bestätigung von einer
Katzen-Gmail bekommt, zweifelt zu Recht.

Am Kassenvorgang selbst ändert das nichts — man sieht die Adresse erst
danach. Für Vertrauen und Rückfragen ist es trotzdem falsch.

→ Nur Nate: Einstellungen → Shop-Details → Absenderadresse.

## Befund 3 — im Kassen-Impressum steht „My Store"

Wortwörtlich das, was Shopify an der Kasse ausliefert:

```
Handelsname: My Store
Telefonnummer:
E-Mail: beamswiss@gmail.com
Physische Adresse: Schweiz
USt-IdNr.:
Gewerbenummer:
```

Der Laden hat ein richtiges Impressum unter
`/pages/letsdrink-impressum`. **Die Kasse zeigt das nicht.** Sie zeigt
die Shopify-Richtlinie, und die sagt, der Händler heisse „My Store"
und wohne in „Schweiz".

Wer an der Kasse zögert und nachschaut, wer da eigentlich verkauft,
liest genau das.

→ Nur Nate, weil mir die Berechtigung `write_legal_policies` fehlt.
Ich habe das nicht umgangen.

## Befund 4 — es gibt gar keine Rückerstattungsrichtlinie

Im Konto liegen nur zwei Richtlinien: Impressum und
Datenschutzerklärung. **Keine Rückerstattungsrichtlinie, keine AGB,
keine Versandrichtlinie.**

Die Produktseite verspricht **sechsmal** „14 Tage Rückgaberecht". An
der Kasse steht dazu nichts. Das ist die Stelle, an der ein
misstrauischer Käufer nachsieht — und nichts findet.

→ Nur Nate, gleiche Sperre wie Befund 3.

## Befund 5 — CHF 1.50 Versand in rund 200 Länder

Kein Kassenproblem. Ein Loch.

| Zone | Länder | Preis |
|---|---|---|
| Schweiz | CH | gratis |
| Europa | 51 | CHF 1.50 |
| International | ~150 | CHF 1.50 |

Der Laden verschickt eine Flasche nach Australien, Brasilien, Japan
oder in die USA für **CHF 1.50**. Der Einkauf kostet CHF 6.55, der
Versand des Lieferanten ist bis heute unbekannt und in keiner Rechnung
enthalten.

Solange null Bestellungen da sind, ist nichts passiert. Sobald Werbung
läuft, kann eine einzige Bestellung aus Übersee mehr kosten als der
Gewinn aus zehn Schweizer Bestellungen.

**Das ist eine Geschäftsentscheidung, keine Einstellung:** Will der
Laden überhaupt ins Ausland verkaufen? Wenn ja, muss der Preis
stimmen. Wenn nein, gehören die beiden Zonen weg — dann verschwinden
auch 200 Länder aus der Auswahlliste an der Kasse, was den Vorgang
nebenbei kürzer macht.

Ich habe daran **nichts geändert**, weil das Nates Entscheid ist.

---

## Was ich selbst geändert habe

Eine Sache, und nur die: **die Zahlungsarten stehen jetzt im
Warenkorb**, direkt unter „Zur Kasse".

Begründung ist der Hinweis ganz oben — wer in den ersten Sekunden
abspringt, sucht die Antwort auf „kann ich hier überhaupt zahlen".
Bisher stand die Antwort nur im Seitenfuss.

Gebaut aus `shop.enabled_payment_types`, nicht von Hand getippt.
Damit kann die Zeile nicht falsch werden: schaltet Nate TWINT frei,
erscheint es dort von selbst.

**Das behebt Befund 1 nicht.** Es zeigt die Wahrheit früher an. Wenn
die Wahrheit „kein TWINT" lautet, hilft es wenig — dann sieht der
Käufer nur früher, dass er hier nicht so zahlen kann, wie er möchte.
Der eigentliche Hebel bleibt TWINT.

## Reihenfolge, wenn Nate am Rechner sitzt

1. **TWINT** freischalten. Grösster Hebel, kleinste Mühe.
2. **Absenderadresse** auf eine Let'sDrink-Adresse ändern.
3. **Impressum-Richtlinie** füllen: Handelsname Let'sDrink, echte
   Adresse in Rapperswil-Jona, Telefonnummer.
4. **Rückerstattungsrichtlinie** anlegen — 14 Tage, passend zur Seite.
5. **Auslandversand** entscheiden: richtiger Preis oder gar nicht.
