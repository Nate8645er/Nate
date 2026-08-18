# Zum Einfügen — fertige Texte für Shopify

Stand 18.8.2026.

Du hast mich gebeten, die **Absenderadresse** und die
**Impressum-Richtlinie** zu ändern. Beides geht von hier aus nicht.
Zwei verschiedene Gründe:

| Was | Warum es nicht geht |
|---|---|
| Absenderadresse | **Es gibt dafür keine Schnittstelle.** Ich habe nachgesehen: `shopUpdate` existiert in der Shopify-API überhaupt nicht. Shop-Name, Adresse und E-Mail sind ausschliesslich im Konto änderbar. Das ist keine fehlende Berechtigung, das ist eine Lücke bei Shopify. |
| Impressum-Richtlinie | **Fehlende Berechtigung.** `shopPolicyUpdate` antwortet: *„Required access: `write_legal_policies` access scope."* Zum zweiten Mal. Ich habe das nicht umgangen. |

Deshalb hier alles fertig zum Kopieren. **Kein Wort davon ist von mir
erfunden** — alles steht schon auf deinen eigenen Seiten
`/pages/letsdrink-impressum` und `/pages/versand-und-rueckgabe`. Ich
habe es nur an die Stelle geholt, an der die Kasse nachschaut.

---

## 1. Absenderadresse

**Weg:** Shopify-Konto → Einstellungen → Shop-Details → Kontaktdaten

Dort stehen zurzeit **beide** Felder auf:

```
Yourcatlove.info@gmail.com
```

**Eine Sache, die ich vorher falsch dargestellt habe:** Ich hatte das
als Ausrutscher in einem Feld beschrieben. Es ist keiner — dieselbe
Adresse steht auch in deinem veröffentlichten Impressum. Du benutzt
sie durchgehend. Das eigentliche Problem ist ein anderes und ein
kleineres:

> In der Shopify-Impressum-Richtlinie steht `beamswiss@gmail.com`,
> auf deiner Impressum-Seite steht `yourcatlove.info@gmail.com`.
> **Zwei verschiedene Adressen in zwei Rechtstexten desselben Ladens.**

Das gehört zusammengeführt, egal auf welche. Meine Empfehlung, aber
dein Entscheid:

- **Am saubersten:** eine eigene Adresse, etwa `hallo@letsdrink-pet.com`
  über Shopify oder deinen Anbieter. Ein Hundeflaschen-Laden, dessen
  Bestätigung von einer Katzen-Adresse kommt, wirkt seltsam — das ist
  aber Geschmack, kein Mangel.
- **Am schnellsten:** überall `yourcatlove.info@gmail.com`, weil das
  die Adresse ist, die du wirklich liest.

**Nicht vergessen:** ändern musst du beide Felder — Absenderadresse
*und* Kundenkontaktadresse.

---

## 2. Impressum-Richtlinie

**Weg:** Einstellungen → Richtlinien → Impressum → alles löschen, das
Folgende einsetzen

Das steht dort **jetzt**:

```
Handelsname: My Store
Telefonnummer:
E-Mail: beamswiss@gmail.com
Physische Adresse: Schweiz
USt-IdNr.:
Gewerbenummer:
```

Das gehört hin — wortgleich zu deiner Impressum-Seite, wie sie seit
dem 18.8.2026 aussieht:

```
Verantwortlich für diese Website und Anbieter dieses Onlineshops:

Let'sDrink
Nate
8640 Rapperswil-Jona SG
Schweiz

E-Mail: yourcatlove.info@gmail.com

Rechtsform: Einzelunternehmen mit Sitz in Rapperswil-Jona, Schweiz.

Die vollständige Postanschrift teilen wir auf Anfrage per E-Mail mit.

Streitschlichtung: Wir sind nicht bereit und nicht verpflichtet, an
Streitbeilegungsverfahren vor einer Verbraucherschlichtungsstelle
teilzunehmen.
```

**Drei Angaben fehlen absichtlich:**

- **Strasse und Nachname** — auf Nates Wunsch. Siehe Abschnitt 5, dort
  steht, was das bedeutet.
- **Telefonnummer** — ich kenne deine nicht und erfinde keine. Wenn du
  eine angeben willst, hänge sie unter die E-Mail-Zeile.
- **MWST-Nummer** — du hast keine genannt. Unter CHF 100'000 Umsatz
  besteht keine Pflicht zur Eintragung. Bist du eingetragen, gehört
  die Nummer hin; bist du es nicht, bleibt die Zeile weg. **Eine
  erfundene Nummer wäre strafbar.**

---

## 3. Rückerstattungsrichtlinie — die fehlt ganz

Nicht von dir bestellt, aber sie gehört zum selben Problem: dein Laden
verspricht auf der Produktseite **sechsmal** „14 Tage Rückgaberecht",
und an der Kasse steht dazu **nichts**. In deinem Shopify-Konto gibt
es diese Richtlinie gar nicht.

**Weg:** Einstellungen → Richtlinien → Rückerstattungsrichtlinie

Zusammengesetzt aus deiner Seite `/pages/versand-und-rueckgabe`,
Wort für Wort:

```
Rückgabe innerhalb von 14 Tagen

Du kannst die Flasche innerhalb von 14 Tagen zurückgeben, ohne
Begründung. Spül sie vorher kurz aus. Gebrauchsspuren sind in Ordnung.

So geht es: Schreib an yourcatlove.info@gmail.com mit deiner
Bestellnummer. Innerhalb eines Werktags bekommst du die
Rücksendeadresse. Die Rücksendekosten trägst du. Den Kaufpreis
erstatte ich innerhalb von fünf Werktagen nach Eingang der Rücksendung.

Wenn die Flasche ausläuft

Dann ist sie defekt. Melde dich – du bekommst Ersatz oder dein Geld
zurück, und die Rücksendung geht auf mich. Ein kurzes Video hilft bei
der Abwicklung, ist aber keine Bedingung.

Die gesetzlichen Mängelrechte nach Art. 197 ff. OR gelten unabhängig
von dieser freiwilligen Regelung.

Lieferzeit und Versand

7 bis 14 Werktage nach Zahlungseingang. Versand innerhalb der Schweiz
gratis. Bei Lieferungen ins Ausland können im Bestimmungsland Zoll und
Einfuhrsteuer anfallen; diese trägst du.
```

---

## 5. Adresse raus — was ich gemacht habe und was es kostet

Nate: *„bei den richtlinien soll nur nate und rapperswil jona stehen
und nicht meine adresse und so"*.

**Der Punkt, der zuerst kommt:** die Shopify-Richtlinie war gar nicht
das Problem. Deine Strasse stand **live auf zwei veröffentlichten
Seiten**, dein Nachname zusätzlich in der Google-Beschreibung. Nur die
Richtlinie zu ändern hätte dir gar nichts gebracht.

Geändert am 18.8.2026, alles live gegengeprüft:

| Ort | Vorher | Jetzt |
|---|---|---|
| `/pages/letsdrink-impressum` | Nate Murseli, Eichfeldstrasse 8, 8640 | Nate, 8640 Rapperswil-Jona SG |
| `/pages/letsdrink-datenschutz` Ziffer 1 | Nate Murseli, Eichfeldstrasse 8, 8640 | Let'sDrink, Nate, 8640 Rapperswil-Jona SG |
| `/pages/letsdrink-agb` Ziffer 1 | Nate Murseli | Let'sDrink, Nate |
| Google-Beschreibung Impressum | „Nate Murseli, Einzelunternehmen…" | „Nate, Einzelunternehmen…" |

Nachgemessen: `Eichfeldstrasse` **0 Treffer**, `Murseli` **0 Treffer**
auf allen fünf Rechtsseiten. Die Google-Beschreibung brauchte zwei
Minuten, bis Shopifys Zwischenspeicher nachzog.

Dazu kam eine Zeile, die vorher nicht dastand:

> Die vollständige Postanschrift teilen wir auf Anfrage per E-Mail mit.

### Und jetzt das Unangenehme

**Ich habe es gemacht, aber es ist rechtlich nicht sauber.**

Das Schweizer UWG verlangt in Art. 3 Abs. 1 lit. s von Onlineshops
„klare Angabe der Identität und der Kontaktadresse". Als
Kontaktadresse ist dabei eine **Postanschrift** gemeint, an die man
tatsächlich etwas schicken kann — eine Ortschaft allein gilt gemeinhin
nicht. Ein Ort ohne Strasse und ohne Nachname erfüllt das eher nicht.

Was daran hängt:
- Ein Wettbewerber oder eine Konsumentenorganisation könnte das
  beanstanden. Der Nachsatz mit der Postanschrift auf Anfrage
  entschärft es etwas, heilt es aber nicht.
- Ein zögernder Käufer, der wissen will, an wen er sein Geld schickt,
  findet weniger als vorher. Das ist die stille Version desselben
  Preises.

### Der Ausweg, der beides kann

**Ein Postfach in Rapperswil-Jona.** Bei der Schweizerischen Post,
Grössenordnung CHF 60 bis 90 im Jahr. Dann steht im Impressum eine
echte, zustellbare Adresse — und es ist **nicht deine Wohnung**.

Genau dafür machen es Einzelunternehmer, die nicht wollen, dass jeder
Kunde weiss, wo sie schlafen. Es ist die richtige Lösung, nicht ein
Kompromiss.

Bis dahin steht es so, wie du es wolltest. Sag Bescheid, wenn du ein
Postfach hast — dann trage ich es überall nach.

## 4. TWINT — ich kann es nicht bestätigen, und ich sage dir warum

Du schreibst, TWINT ist an. Ich finde es nicht, aber **beide meiner
Tests haben ein Loch**, deshalb behaupte ich nichts:

| Test | Ergebnis | Das Loch |
|---|---|---|
| Zahlungssymbole auf deiner Seite | Visa, Mastercard, Amex, PayPal, Apple Pay, Google Pay, Klarna — kein TWINT | Shopify legt die Seite zwischen; ich sehe vielleicht einen älteren Stand |
| Echte Kasse aufgerufen, Schweizer Sprache erzwungen | Visa, Mastercard, PayPal — kein TWINT | Die Kasse blendet einen Teil der Zahlungsarten erst nach der Adresseingabe ein. Klarna fehlte dort auch, obwohl es sicher an ist. |

**Du prüfst das in zehn Sekunden zuverlässiger als ich:** Handy,
Flasche in den Warenkorb, zur Kasse, Schweizer Adresse eintippen. Was
dann in der Zahlungsliste steht, gilt.

Wichtig für die Warenkorb-Zeile, die ich gebaut habe: sie zeigt
`shop.enabled_payment_types`. Steht TWINT dort nicht drin, obwohl es
an der Kasse funktioniert, dann **verschweigt meine Zeile es** — und
macht es damit für einen Schweizer Käufer eher schlechter als besser.

Sag mir, was du an der Kasse siehst. Zeigt sie TWINT und meine Zeile
nicht, trage ich TWINT dort von Hand nach.
