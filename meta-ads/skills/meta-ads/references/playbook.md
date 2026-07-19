# Meta Ads — Detail-Playbook (Referenz)

Ergaenzt SKILL.md. Nur nachschlagen, was der aktuelle Auftrag braucht.

## 1. Break-even-Rechner (immer zuerst)

```
Break-even-ROAS = Verkaufspreis / Deckungsbeitrag
Deckungsbeitrag = Verkaufspreis - Produktkosten - Versand - Zahlungsgebuehren - Verpackung
Ziel-CPA        = Deckungsbeitrag (Break-even) bzw. Deckungsbeitrag - Wunschgewinn
```

Beispielrechnung (Zahlen sind Platzhalter, mit echten Werten ersetzen):
Produkt CHF 49.90, Kosten CHF 12, Versand CHF 7, Gebuehren ~CHF 2
-> Deckungsbeitrag CHF 28.90 -> Break-even-ROAS ~1.73.
Erst mit echten Zahlen aus Shopify rechnen, nie mit Schaetzwerten
skalieren.

## 2. Kampagnen-Blueprints

### 2a. Cold Start (neuer Store / neues Produkt, kleines Budget)

```
Kampagne 1: Creative-Test (CBO)
  Ziel: Purchase | Budget: klein, aber genug fuer Signal
  Ad Set je Angle (2-4), Advantage+ Audience, breit
    3-5 Creatives pro Ad Set (Hooks variieren)
Kampagne 2: ASC (Advantage+ Sales)
  startet, sobald 2-3 Creatives im Test CTR/CPA-Gewinner sind
  4-8 Gewinner-Creatives, Budget-Schwerpunkt hier
```

### 2b. Scaling-Struktur (bewiesenes Produkt)

```
ASC Haupt (70% Budget)   — Gewinner-Creatives, vertikal +20%/2-3 Tage
Creative-Lab (20%)       — permanenter Test neuer Angles/Hooks
Retargeting/DPA (10%)    — Katalog, Einwand-Copy, Frequenz-Cap beachten
```

### 2c. Retargeting-Segmente

| Segment | Fenster | Botschaft |
|---|---|---|
| ViewContent ohne ATC | 14-30 Tage | Social Proof, USP-Erinnerung |
| AddToCart/IC ohne Kauf | 7-14 Tage | Einwaende (Versand, Rueckgabe), Dringlichkeit ehrlich |
| Kaeufer | 30-180 Tage | Cross-/Upsell, Replenishment |
| IG/FB-Engager | 365 Tage | wie Cold, aber warm-Hook |

## 3. Angle-Bibliothek (Startpunkte)

1. Problem -> Loesung ("Kennst du das, wenn ...")
2. Demonstration / "So funktioniert's" (Produkt in Aktion, 5-15s)
3. UGC-Testimonial (Ich-Perspektive, Handy-Optik)
4. Social Proof / Reviews ("X Kundinnen in der Schweiz")
5. Unboxing / Was-du-bekommst
6. Vergleich (vorher/nachher SACHLICH, wir/andere fair)
7. Founder-Story (warum es MeowUfo gibt)
8. Objection-Killer (Versandzeit, Qualitaet, Rueckgabe)

Pro Angle: 2-3 Hooks schreiben, staerksten zuerst testen.

## 4. Ad-Copy-Geruest

```
Hook-Zeile (Scroll-Stopper, max 1 Satz, konkret)
2-4 Zeilen Nutzen/Beweis (keine Featureliste — Ergebnis fuer den Kunden)
Einwand-Zeile (Versand/Rueckgabe/Garantie)
CTA-Zeile (eine Handlung)
Headline: Nutzen oder Angebot in <40 Zeichen
Description: Vertrauen (z.B. "Versand aus CH/EU - einfache Rueckgabe")
```

## 5. KPI-Steuerung (Definitionen, keine erfundenen Benchmarks)

| KPI | Formel | Wofuer |
|---|---|---|
| CTR (link) | Link-Klicks / Impressionen | Creative-Hook-Qualitaet |
| CPC | Spend / Link-Klicks | Einkaufspreis Traffic |
| CVR | Purchases / Landingpage-Views | Store/Angebot (-> shopify-godmode) |
| CPA | Spend / Purchases | vs. Ziel-CPA steuern |
| ROAS | Umsatz (Ads) / Spend | vs. Break-even-ROAS |
| MER | Gesamtumsatz / Gesamt-Spend | Wahrheit auf Konto-Ebene |
| Frequenz | Impressionen / Reichweite | Fatigue-Fruehwarnung |

Diagnose-Kette bei schlechter Performance:
- CTR schlecht -> Creative/Hook-Problem
- CTR ok, CVR schlecht -> Landingpage/Angebot-Problem (shopify-godmode)
- CTR+CVR ok, ROAS schlecht -> AOV/Marge-Problem (Bundles, Upsells)
- alles ok, skaliert nicht -> Creative-Volumen und Angles erhoehen

## 6. Launch-Checkliste

- [ ] Pixel + CAPI aktiv, Purchase-Event mit Wert/Waehrung verifiziert
- [ ] Domain verifiziert, Events priorisiert
- [ ] Break-even-ROAS/CPA berechnet und notiert
- [ ] Kill- und Skalier-Regeln VOR Launch schriftlich
- [ ] Landingpage mobil geprueft (Speed, PBV-konforme Preise)
- [ ] Zahlungsarten sichtbar (TWINT fuer CH pruefen)
- [ ] Ad-Konto: 2FA, Backup-Admin, Zahlungsmittel + Backup
- [ ] Creatives in 9:16 und 1:1, Ton-aus-tauglich
- [ ] FR/IT nur mit nativ gepruefter Uebersetzung
