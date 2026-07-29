# SHOP-AUFBAU KOMPLETT

Store ist leer. Das ist die beste Ausgangslage, die du seit Monaten hattest: du baust einmal richtig auf, statt an etwas herumzuflicken.

---

## 0. Zwei Dinge, die du zuerst entscheiden musst

### Das Domain-Problem

**katzenufos.com passt nicht mehr.** Die Domain ist nach einem einzelnen Produkt benannt, das es im Shop nicht mehr gibt. Ein Trinkbrunnen auf "Katzenufos" verkaufen ist wie Kaffee bei "Toasterwelt.ch" kaufen. Kunden stolpern darüber, und du kannst die Marke nie erweitern.

Was du brauchst: einen Namen auf **Kategorieebene**, nicht auf Produktebene. Etwas, unter dem Brunnen, Filter und alles Spätere Platz haben.

Vorgehen: neue .ch-Domain registrieren (rund CHF 15 im Jahr), in Shopify als Hauptdomain setzen, katzenufos.com als Weiterleitung behalten. Shopify unterstützt mehrere Domains, du verlierst nichts.

Namensrichtung: kurz, aussprechbar am Telefon, keine Umlaute in der Domain, kein Produktwort drin. Sag mir, wenn ich Vorschläge machen soll, dann prüfe ich auch gleich die Verfügbarkeit.

### Zwei Altlasten, die jetzt weg müssen

Aus deinem bisherigen Store stehen zwei Punkte offen, die im Neuaufbau nicht mitwandern dürfen:

1. **Der Shop heisst intern noch "My Store".** Das erscheint in E-Mail-Absendern, Rechnungen und Browser-Tabs. Nur manuell änderbar unter Einstellungen, Shop-Details.
2. **Die Hauptnavigation ist noch auf Englisch.** Bei einem Schweizer Shop ist das ein sofortiger Vertrauensverlust.

Beides zusammen zehn Minuten. Beides erledigen, bevor der erste Besucher kommt.

---

## 1. Der Katalog

Vier Einträge, mehr nicht. Ein voller Katalog wirkt professionell, ein fokussierter verkauft.

| # | Produkt | Preis | Zweck |
|---|---|---|---|
| 1 | Trinkbrunnen 2.5 L | CHF 69.00 | Einstieg, holt den Kunden |
| 2 | Ersatzfilter 3er-Pack | CHF 14.90 | der Gewinn |
| 3 | Ersatzfilter 6er-Pack | CHF 26.90 | höherer Warenkorb, weniger Versand |
| 4 | Set: Brunnen + 6 Filter | CHF 89.00 | bestes Angebot, Standardempfehlung |

Rechnung zum Set: Einzeln wären es CHF 95.90. Du gibst CHF 6.90 Rabatt und bindest den Kunden für ein halbes Jahr an deine Filterbauform. Das ist der billigste Kundenbindungskauf, den du machen kannst.

**Das Set wird der Standard-Kaufbutton auf der Brunnenseite.** Der Einzelbrunnen bleibt als kleinere Option daneben stehen.

### Varianten-Struktur

Leg Filter als **eigenes Produkt** an, nicht als Variante des Brunnens. Grund: nur ein eigenständiges Produkt kann abonniert werden, taucht in der Nachbestell-Mail als Direktlink auf und lässt sich separat bewerben.

SKU-Schema, damit du später nicht suchst:
```
BRN-25       Brunnen 2.5 L
FIL-03       Filter 3er
FIL-06       Filter 6er
SET-BRN-06   Set Brunnen + 6 Filter
```

---

## 2. Produktseite: Ersatzfilter

Diese Seite muss nicht überzeugen, sie muss **den Nachkauf reibungslos machen**. Wer hier landet, ist schon Kunde. Jede Zeile zu viel ist eine Bremse.

**Titel:** Ersatzfilter für den Trinkbrunnen, 3er-Pack

**Untertitel:** Reicht drei Monate. Kommt als Brief in den Briefkasten.

**Beschreibung:**

```
Wechsle den Filter alle vier Wochen. Länger geht, wird aber
unappetitlich: was hängen bleibt, ist Fell, Futterrest und Kalk.

Ein 3er-Pack deckt ein Vierteljahr ab. Der Versand erfolgt als
Brief, du musst nicht zu Hause sein.

Passt auf: Trinkbrunnen 2.5 L (BRN-25)
Passt nicht auf: Modelle anderer Hersteller
```

**Kaufoptionen (Reihenfolge zwingend so):**

```
◉ Automatisch nachliefern, alle 3 Monate     CHF 13.41   10% gespart
  Pausieren oder kündigen mit einem Klick. Keine Mindestlaufzeit.

○ Einmalig kaufen                            CHF 14.90
```

**Das Abo steht oben und ist vorausgewählt.** Das ist der einzige wichtigste Klick im ganzen Shop. Wer hier zum Abo greift, ist dreimal so viel wert wie ein Einmalkäufer.

**Direkt unter den Kaufoptionen, klein:**
```
Keine Mindestlaufzeit. Pausieren, verschieben oder kündigen
jederzeit im Kundenkonto, ohne uns zu schreiben.
```

Diese Zeile ist keine Höflichkeit. Ohne sie kreuzt kaum jemand das Abo an, weil alle Angst vor der Kündigungsfalle haben.

**Drei FAQ, mehr nicht:**

- *Wie oft muss ich wechseln?* Alle vier Wochen. Bei mehreren Katzen eher drei.
- *Was, wenn ich zu viele habe?* Lieferung überspringen mit einem Klick, oder Intervall auf vier Monate stellen.
- *Passt der auf meinen Brunnen?* Nur auf unseren 2.5 L Brunnen. Bei anderen Modellen ist die Bauform anders, dann geht es nicht.

**6er-Pack:** identische Seite, Preis CHF 26.90, Abo CHF 24.21, Zusatzzeile "Deckt ein halbes Jahr. Ein Versand statt zwei."

---

## 3. Seitenstruktur des Shops

```
Startseite
├─ Trinkbrunnen (Produktseite, mit Section "Produkt-Überzeugung")
├─ Ersatzfilter
│  ├─ 3er-Pack
│  └─ 6er-Pack
├─ Set: Brunnen + 6 Filter
├─ Häufige Fragen
├─ Über uns
└─ Rechtliches
   ├─ Impressum
   ├─ AGB
   ├─ Datenschutz
   └─ Versand und Rückgabe
```

**Hauptnavigation, genau vier Punkte:**
```
Trinkbrunnen  ·  Ersatzfilter  ·  Häufige Fragen  ·  Kontakt
```

Nicht mehr. Jeder zusätzliche Menüpunkt kostet Conversion.

**Collections:** genau zwei, `brunnen` und `filter`. Mehr braucht ein Vier-Produkt-Shop nicht.

### Startseite, von oben nach unten

1. Hero: Video der trinkenden Katze, darüber ein Satz, darunter der Kaufbutton fürs Set
2. Das Problem in drei Zeilen (voller Napf, Wasserhahn, Giesskanne)
3. Das Set als Hauptangebot
4. Der Filter-Block, warum es weitergeht
5. Kundenstimmen, sobald du welche hast. Vorher **weglassen**, nicht erfinden.
6. Versand, Rückgabe, Kontakt

**Was nicht auf die Startseite kommt:** Countdown, "nur noch 3 auf Lager", erfundene Bewertungen, durchgestrichene Fantasiepreise. Das ist in der Schweiz nicht nur unschön, es ist UWG-relevant.

### Über uns

Ein Absatz, ehrlich: Einzelunternehmer, Schweiz, du beantwortest die Mails selbst. Das ist gegenüber anonymen Dropshipping-Shops dein grösster Vorteil. Nutz ihn, statt "Wir sind ein junges dynamisches Team" zu schreiben.

---

## 4. Die Lieferanten-Mails

Drei Typen, drei verschiedene Anfragen. Schick alle drei raus, nicht nur eine.

### Mail A: Hersteller auf Alibaba

**Betreff:** Cat water fountain + filter supply, Swiss retailer

```
Hello,

I am a Swiss online retailer building a subscription offer
around a cat water fountain. The fountain is the entry product,
the replacement filters are the recurring business. That means
I care more about long-term filter supply than about the
lowest unit price.

Before I order a sample:

1. EU Declaration of Conformity for this exact model, as PDF.
2. Test reports: EMC, Low Voltage or SELV, RoHS.
3. Does the model number on the DoC match the product you ship?
4. Is it USB powered with no mains adapter in the box?
5. Replacement filter price per piece at 50 / 200 / 500 units.
6. Have you changed the filter housing design in the last
   24 months, and do you plan to?
7. Do you ship from an EU warehouse, or China only?
8. Defect rate on this model?
9. Measured noise level in dB and the measuring method.
10. Can you send one sample this week at my cost?

If you cannot supply filters separately and reliably, this is
not a fit for me and we can both save the time.

Best regards
[Name], [Firma], Switzerland
```

*Der letzte Absatz ist Absicht. Er filtert in einem Satz alle aus, die nur Geräte verkaufen wollen.*

---

### Mail B: EU-Grosshändler oder Dropship-Anbieter mit Lager

**Betreff:** Dropship partnership, cat fountain, Switzerland

```
Hello,

I run a Swiss pet ecommerce store and am looking for a
dropship partner for cat water fountains with reliable
replacement filter supply.

My requirements:

- Shipping from an EU warehouse to Switzerland, with the
  delivery time you can actually hold
- Neutral packaging, no invoices or your branding inside
- Replacement filters available as a separate SKU, long term
- CE Declaration of Conformity and test reports available
- Direct contact for warranty replacements

Please send your price list, delivery times to Switzerland,
and the compliance documents. If you have a minimum order
value, tell me now rather than later.

Best regards
[Name], [Firma], Switzerland
```

---

### Mail C: Sourcing-Agent

**Betreff:** Sourcing request, cat fountain with filter subscription model

```
Hello,

I need a sourcing partner for one product line, not a catalogue.

Product: cat water fountain, around 2.5 litres, USB powered,
quiet, with replaceable filters.

The important part: I sell the filters as a subscription. I
need a supplier whose filter form factor will not change and
who can supply filters separately in small, frequent quantities.

Please come back with two or three factory options including:
unit price, filter price, EU warehouse availability, and
whether they hold a valid CE Declaration of Conformity.

Best regards
[Name], [Firma], Switzerland
```

---

### Auswertung der Antworten

| Antwort | Bedeutung |
|---|---|
| Papiere kommen innert 24 h als PDF | ernstzunehmen, weiterverfolgen |
| "CE, no problem" ohne Anhang | raus |
| Weicht bei Frage 6 aus (Bauform) | raus, das killt dein Modell |
| Nur China-Direktversand | Notlösung, parallel weitersuchen |
| Antwortet nach 3 Tagen nicht | raus, so wird auch der Support laufen |

---

## 5. Reihenfolge

| Wann | Was |
|---|---|
| Heute | 3 Lieferanten-Mails raus. Shop-Name und Navigation korrigieren. Zwei Katzenvideos drehen. |
| Tag 2 | Domain entscheiden und registrieren |
| Tag 3 | Vier Produkte anlegen (ohne Bilder, kommt später), SKUs setzen |
| Tag 4 | Abo-App installieren, Testabo mit eigener Karte durchspielen, wieder kündigen |
| Tag 5 | Section einbauen, Filterseiten befüllen, Navigation setzen |
| Tag 6 | E-Mail-Flows anlegen, Rechtstexte gegenlesen |
| Tag 7 | Muster bestellen, sobald ein Lieferant die Papiere geliefert hat |

Alles ausser dem letzten Punkt hängt von niemandem ab. Das ist der Grund, warum ich es in diese Reihenfolge gelegt habe.

---

## 6. Was noch fehlt und wann es dran ist

- **Produktbilder.** Erst wenn das Muster da ist. Lieferantenbilder sind der grösste sichtbare Unterschied zwischen einem Dropshipping-Shop und einer Marke.
- **Kundenstimmen.** Erst wenn echte da sind. Nicht vorher, unter keinen Umständen.
- **Meta Ads.** Erst wenn ein Video organisch funktioniert. Bezahlte Reichweite auf schwaches Material ist verbranntes Geld.
- **Zweite Filterquelle.** Vor dem ersten Verkauf, nicht danach.

---

## 7. Der ehrliche Schlusspunkt

Du hast jetzt einen leeren Shop, einen klaren Katalog, fertige Seitentexte, eine fertige Section, sieben E-Mails und drei Lieferantenanfragen. Der Aufbau ist nicht mehr der Engpass.

Der Engpass ist ab hier nur noch, ob du die drei Mails heute rausschickst und ob du anfängst zu filmen. Das kann ich dir nicht abnehmen, und kein weiteres Dokument ändert daran etwas.
