# RECHTSTEXTE

Fertig zum Einfügen als eigene Shopify-Seiten, sobald die eigene Let'sDrink-Instanz
steht. Nicht live ins geteilte Backend geschrieben, siehe STATUS-2026-07-28.md:
dort liegen schon Impressum/AGB/Datenschutz für zwei andere Geschäfte.

Rechtlicher Rahmen: Schweiz, kein EU-Recht. Kein gesetzliches Widerrufsrecht
für Onlinekäufe (siehe HANDOFF.md Regel 7). Die 14 Tage sind eine freiwillige
Zusage. Keine erfundenen Streichpreise (Preisbekanntgabeverordnung). Dies ist
eine sorgfältige Vorlage, keine Rechtsberatung — bei echten Fragen (MwSt-Pflicht
ab Umsatzschwelle, Handelsregister) einmal kurz prüfen lassen.

---

## Seite: Impressum

**Handle:** `impressum`

```
IMPRESSUM

Verantwortlich für diese Website:

[Vollständiger Name]
[Strasse und Hausnummer]
[PLZ und Ort]
Schweiz

E-Mail: [E-Mail-Adresse]
Handelsregister-Nr.: [falls vorhanden, sonst Zeile weglassen]
UID: [falls vorhanden, sonst Zeile weglassen]

Einzelunternehmen, Sitz in Rapperswil-Jona, Schweiz.

Streitschlichtung: Wir sind nicht bereit und nicht verpflichtet, an
Streitbeilegungsverfahren vor einer Verbraucherschlichtungsstelle
teilzunehmen.
```

---

## Seite: AGB

**Handle:** `agb`

```
ALLGEMEINE GESCHÄFTSBEDINGUNGEN

1. Geltungsbereich
Diese AGB gelten für alle Bestellungen über diesen Onlineshop, betrieben
von [Name], [Adresse], Schweiz.

2. Vertragsabschluss
Mit dem Absenden der Bestellung gibst du ein verbindliches Angebot ab.
Der Vertrag kommt zustande, sobald wir die Bestellung per E-Mail
bestätigen.

3. Preise
Alle Preise sind Endpreise in Schweizer Franken (CHF). Versandkosten
werden vor Abschluss der Bestellung klar ausgewiesen.

4. Zahlung
Zahlung über die im Checkout angebotenen Zahlungsarten. Die Ware bleibt
bis zur vollständigen Bezahlung unser Eigentum.

5. Lieferung
Lieferung in die Schweiz und nach Liechtenstein. Lieferzeiten stehen auf
der Seite "Versand und Rückgabe". Wir informieren aktiv, wenn sich eine
Lieferung verzögert.

6. Rückgabe
Es gilt das freiwillige Rückgaberecht auf der Seite "Versand und
Rückgabe". Ein gesetzliches Widerrufsrecht besteht in der Schweiz für
Online-Käufe nicht.

7. Mängel und Garantie
Bei einem Mangel (z.B. eine Flasche läuft aus) meldest du dich innerhalb
von 14 Tagen. Du bekommst Ersatz oder dein Geld zurück, ohne dass wir
darüber diskutieren.

8. Haftung
Wir haften im gesetzlich zulässigen Rahmen. Für leichte Fahrlässigkeit
wird die Haftung, soweit gesetzlich zulässig, ausgeschlossen.

9. Anwendbares Recht und Gerichtsstand
Es gilt Schweizer Recht. Gerichtsstand ist, soweit gesetzlich zulässig,
der Sitz des Anbieters.

10. Schlussbestimmungen
Sollte eine Bestimmung dieser AGB unwirksam sein, bleiben die übrigen
Bestimmungen davon unberührt.

Stand: [Monat, Jahr]
```

---

## Seite: Datenschutzerklärung

**Handle:** `datenschutz`

```
DATENSCHUTZERKLÄRUNG

Diese Erklärung informiert dich, welche Daten wir bearbeiten, wenn du
diesen Shop besuchst oder bei uns bestellst. Grundlage ist das
revidierte Schweizer Datenschutzgesetz (revDSG).

1. Verantwortliche Stelle
[Name], [Adresse], Schweiz. E-Mail: [E-Mail-Adresse]

2. Welche Daten wir bearbeiten
- Bestelldaten: Name, Adresse, E-Mail, Zahlungsinformationen (verarbeitet
  über den Zahlungsanbieter, nicht bei uns gespeichert)
- Technische Daten: IP-Adresse, Browsertyp, besuchte Seiten (über
  Shopify und ggf. Analyse-Tools)
- Newsletter-Daten: E-Mail-Adresse, nur bei aktiver Anmeldung

3. Zweck der Bearbeitung
Bestellabwicklung, Versand, Kundenservice, mit deiner Einwilligung:
Newsletter und Marketing.

4. Cookies und Tracking
Wir setzen technisch notwendige Cookies für den Betrieb des Shops ein.
[Falls Meta-Pixel/Google Analytics aktiv: Zusätzlich verwenden wir
{Tool-Namen} zur Reichweitenmessung und Anzeigenoptimierung. Diese
Cookies werden erst nach deiner Zustimmung im Cookie-Banner gesetzt.]

5. Weitergabe an Dritte
Wir geben Daten nur weiter, soweit für die Bestellabwicklung nötig
(Versanddienstleister, Zahlungsanbieter) oder gesetzlich vorgeschrieben.

6. Speicherdauer
Bestelldaten werden so lange gespeichert, wie gesetzlich vorgeschrieben
(insbesondere Aufbewahrungspflichten im Rechnungswesen).

7. Deine Rechte
Du hast das Recht auf Auskunft, Berichtigung, Löschung und
Einschränkung der Bearbeitung deiner Daten. Schreib uns dazu an
[E-Mail-Adresse].

8. Änderungen
Wir passen diese Erklärung an, wenn sich Bearbeitung oder Rechtslage
ändern.

Stand: [Monat, Jahr]
```

---

## Cookie-Banner

Nur technisch notwendige Cookies sind ohne Einwilligung erlaubt. Sobald
Meta-Pixel oder Google Analytics eingebunden werden, braucht es eine
echte Zustimmung, nicht nur einen Hinweis. Zwei Bausteine, je nachdem
was aktiv ist:

**Nur technisch notwendig (aktueller Stand, kein Tracking aktiv):**
```
Wir verwenden nur technisch notwendige Cookies für den Betrieb dieses
Shops. Mehr dazu in unserer Datenschutzerklärung.
[Verstanden]
```
Das ist bereits im Theme eingebaut (`consent-bar` in `layout/theme.liquid`).

**Sobald Tracking (Meta/Google) dazukommt:**
```
Wir verwenden Cookies, um den Shop zu betreiben und, mit deiner
Zustimmung, um Anzeigen zu messen und zu verbessern.
[Nur Notwendige]   [Alle akzeptieren]
```
Dann braucht es echtes Consent-Management (z.B. via Shopify Customer
Privacy API oder eine Consent-App), nicht nur einen Hinweis-Banner ohne
Wirkung. Bis dahin bewusst nichts vortäuschen.

---

## Seite: Versand und Rückgabe

**Handle:** `versand-und-rueckgabe`

Bereits fertig getextet in `shop-texte-trinkflasche.md`, Teil 3. Zwei
Lücken bleiben, bis der Lieferant antwortet: die genaue Lieferzeit
(Platzhalter `[X bis Y Werktage]`) und die E-Mail-Adresse fürs
Retourenverfahren.

---

## Seite: Über uns

**Handle:** `ueber-uns`

Bereits fertig getextet in `shop-texte-trinkflasche.md`, Teil 4.
Platzhalter `[Name]` und `[E-Mail]` ausfüllen.

---

## Seite: Kontakt

**Handle:** `kontakt`

```
KONTAKT

Fragen zur Bestellung, zur Flasche oder zur Lieferzeit? Schreib direkt,
es antwortet ein Mensch, kein Callcenter.

E-Mail: [E-Mail-Adresse]
Antwortzeit: innerhalb eines Werktags

Für Retouren und Reklamationen: gib deine Bestellnummer gleich mit an,
dann geht es schneller.
```

Formular auf dieser Seite: Name, E-Mail, Bestellnummer (optional),
Nachricht. Shopify stellt das Kontaktformular über `{% form 'contact' %}`
nativ bereit, keine App nötig.
