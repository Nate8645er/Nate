# E-MAIL-FLOWS

Für Klaviyo oder eine vergleichbare E-Mail-App. Schweizer du-Form, CHF,
keine Geviertstriche, kurze Sätze. Platzhalter in `{ }` ersetzen.

Rechtlich: Abmeldelink in jeder Mail, Double-Opt-in fürs Newsletter. Der
Rabattcode **LETSDRINK10** muss real in Shopify existieren (siehe unten,
ist bereits angelegt).

---

## 1) Willkommen (Trigger: Newsletter-Anmeldung)

**Mail 1, sofort**
Betreff: Willkommen, hier ist dein Rabatt
Text:
> Schön, dass du da bist.
> Dein Code: **LETSDRINK10**, 10 Prozent auf deine erste Bestellung.
> [Jetzt einlösen]
> Die Trinkflasche mit Napf ist für Hunde und Katzen gemacht, die
> unterwegs trinken müssen. Knopf drücken, Wasser läuft in den Napf,
> der Rest läuft zurück in die Flasche.

**Mail 2, nach 2 Tagen**
Betreff: Das 2er-Set spart dir eine Bestellung
Text:
> Falls du noch überlegst: das 2er-Set kostet CHF 49.00 statt CHF 59.80
> einzeln, weil wir nur einmal versenden müssen. Einer bleibt im Auto,
> einer im Rucksack.
> [2er-Set ansehen]
> Dein Code LETSDRINK10 gilt noch.

**Mail 3, nach 4 Tagen**
Betreff: Wieso es diesen Shop gibt
Text:
> Kurz zu uns: Wir betreiben diesen Shop allein, aus der Schweiz. Wenn du
> schreibst, antwortet ein Mensch, kein Callcenter.
> Versand aus der Schweiz. 14 Tage Rückgabe, ohne Begründung.
> [Sortiment ansehen]

---

## 2) Warenkorbabbruch (Trigger: Checkout gestartet, nicht abgeschlossen)

**Mail 1, nach 1 Std.**
Betreff: Deine Flasche wartet noch
Text:
> Hey,
> dein Warenkorb wartet noch auf dich.
> [Bestellung abschliessen]
> Fragen? Antworte einfach auf diese Mail.

**Mail 2, nach 24 Std.**
Betreff: Kurz gefragt, was hält dich noch ab?
Text:
> Falls du gezögert hast: Versand aus der Schweiz, 14 Tage Rückgabe ohne
> Begründung. Läuft sie aus, bekommst du Ersatz oder dein Geld zurück,
> ohne Diskussion.
> [Jetzt sichern]

**Mail 3, nach 48 Std.**
Betreff: Letzte Erinnerung, mit kleinem Extra
Text:
> Dein Warenkorb läuft bald ab. Zwei kaufen, eine gratis: die Aktion gilt
> automatisch an der Kasse, sobald du zwei oder mehr in den Warenkorb
> legst.
> [Bestellung abschliessen]

---

## 3) Dankesmail / Post-Purchase (Trigger: Bestellung abgeschlossen)

**Mail 1, sofort**
Betreff: Bestellung bestätigt, danke
Text:
> Danke für deine Bestellung. Sobald sie das Lager verlässt, bekommst du
> die Sendungsverfolgung. Versand aus der Schweiz.

**Mail 2, nach 5 Tagen**
Betreff: So kommt sie am besten an
Text:
> Deine Flasche sollte angekommen sein. Kurz zur Bedienung: Knopf
> drücken, Wasser läuft in den Napf, aufrichten und der Rest läuft
> zurück. Der Napf nimmt auch eine Portion Trockenfutter.

**Mail 3, nach 10 Tagen**
Betreff: Wie war sie unterwegs?
Text:
> Eine kurze Rückmeldung hilft uns und anderen, die noch überlegen.
> [Erfahrung teilen]
> P.S. Falls ihr zwei Tiere seid oder zwei Autos: das 2er-Set kostet
> CHF 49.00 statt CHF 59.80 einzeln.

---

## Rabattcode für die Willkommensmail

**LETSDRINK10**, 10 Prozent auf die erste Bestellung, live angelegt in
Shopify (siehe STATUS-2026-07-28.md). Ohne Ablaufdatum, manuell
deaktivierbar, sobald die Marge das nicht mehr trägt.
