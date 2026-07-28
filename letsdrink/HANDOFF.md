# HANDOFF: Let'sDrink — Stand 28. Juli 2026

Diese Datei ist der Übergabepunkt aus einer Claude-Chat-Sitzung nach Claude Code.
Sie enthält alles, was du brauchst, um ohne Rückfragen weiterzuarbeiten.

---

## 1. Das Vorhaben

**Marke:** Let'sDrink
**Produkt:** Tragbare Trinkflasche 550 ml mit angebautem Napf, für Hund und Katze.
Knopf drücken, Wasser läuft in den Napf, Rest läuft zurück in die Flasche.
Derselbe Napf nimmt auch Trockenfutter, daher die 2-in-1-Positionierung.

**Markt:** Schweiz und Liechtenstein, CHF, Deutsch, du-Form.
**Betreiber:** Einzelunternehmer, Rapperswil-Jona.

**Vertriebsbeschränkungen des Betreibers:** kein Telefonverkauf, kein warmes
Netzwerk, alles muss self-serve funktionieren.

---

## 2. Shopify-Zustand (live geprüft)

**Store-Handle:** `i0m1xi-h5`
**Währung:** CHF

### Produkt 1 (AKTIV) — das Verkaufsprodukt
```
GID:      gid://shopify/Product/15672665997689
Titel:    Trinkflasche mit Napf, 550 ml, für Hund und Katze
Anbieter: Let'sDrink
Typ:      Hundezubehör          <- sollte "Haustierzubehör" sein
Bestand:  44
Bilder:   7 eigene, 1600x1600, Reihenbild als Vorschau
Handle:   noch der 180-Zeichen-AliExpress-String  <- muss geändert werden
```
Varianten, alle CHF 29.90:
| Variante | SKU | Bestand |
|---|---|---|
| Rosa / 550ML-PC | FLA-550-ROSA | 7 |
| Schwarz / 550ML-PC | FLA-550-SCHWARZ | 14 |
| Grau / 550ML-PC | FLA-550-GRAU | 5 |
| Türkis / 550ML-PC | FLA-550-TUERKIS | 13 |
| Grün / 550ML-PC | FLA-550-GRUEN | 2 |
| Weiss / 550ML-PC | FLA-550-WEISS | 3 |

Die zweite Option heisst noch `550ML-PC`, sollte `550 ml` heissen.

### Produkt 2 (ENTWURF) — das Set
```
GID:    gid://shopify/Product/15672728584569
Titel:  2er-Set Trinkflasche mit Napf, 550 ml, für Hund und Katze
Preis:  CHF 49.00, sechs Farbvarianten, SKUs SET-FLA-2-*
Bilder: 4 (aus Produkt 1 referenziert)
Bestand: 0   <- nicht verkaufbar, DSers-Mapping mit MENGE 2 fehlt
Anbieter: My Store  <- muss Let'sDrink werden
```

### Produkt 3 (ENTWURF) — Backup-Lieferant
```
GID: gid://shopify/Product/15672704860537
Titel: ZZ Backup-Lieferant, nicht veröffentlichen, Trinkflasche 550 ml
```
Zweck: nur als Parkplatz für den Ersatzlieferanten. Richtig wäre: den Lieferanten
per DSers Advanced Mapping an Produkt 1 hängen und dieses Produkt löschen.
Vorher den AliExpress-Link des Lieferanten sichern.

### Kollektion
```
GID:    gid://shopify/Collection/706285109625
Titel:  Trinkflaschen für Hund und Katze
Handle: trinkflaschen-fur-hund-und-katze
Typ:    manuell, 2 Produkte, Bild gesetzt
```

---

## 3. Kalkulation

Einzelflasche CHF 29.90:
| Position | CHF |
|---|---|
| Einkauf inkl. Zulieferung | 6.95 |
| Versand an Kunden (CH) | 7.00 |
| Zahlungsgebühren | 1.17 |
| Retouren und Defekte (5%) | 1.50 |
| MwSt-Anteil | 2.24 |
| **Deckungsbeitrag** | **ca. 11.00** |

2er-Set CHF 49.00: Deckungsbeitrag rund CHF 24, weil nur einmal Versand.

**Die wichtigste Konsequenz:** Bei CHF 11 Deckungsbeitrag liegt die Schmerzgrenze
für bezahlte Werbung bei CHF 11 pro Verkauf. Das schafft Meta auf kaltem Publikum
bei einem CHF 30 Produkt praktisch nie. **Organischer Content ist der einzige
tragfähige Kanal.** Jede Planung, die auf Ads setzt, ist rechnerisch falsch.

Noch zu verifizieren, bevor Preise final sind: echte CH-Versandkosten, Gewicht,
Lieferzeit.

---

## 4. Verbindliche inhaltliche Regeln

Diese Entscheidungen wurden getroffen und sollen nicht stillschweigend gekippt
werden:

1. **Keine erfundenen Streichpreise.** UWG-relevant in der Schweiz. Der Vergleich
   "einzeln CHF 59.80" ist zulässig, weil es der echte Doppelpreis ist.
2. **Kein Wort über BPA**, solange der Lieferant es nicht schriftlich bestätigt.
3. **Kein "eigenes Futterfach"** behaupten. Die Flasche hat einen Wassertank und
   einen Napf. Formulierung: "Der Napf nimmt beides."
4. **Keine Spülmaschinen-Aussage**, nicht bestätigt.
5. **Keine erfundenen Bewertungen, keine Countdowns, keine Verknappung.**
6. **KI-generierte Fotos nur für Werbeanzeigen**, nie als Produktbild auf der
   Detailseite. Auf TikTok und Meta muss KI-Inhalt gekennzeichnet werden.
7. **In der Schweiz gibt es kein gesetzliches Widerrufsrecht für Onlinekäufe.**
   Die 14 Tage sind eine freiwillige Zusage und deshalb ein Verkaufsargument.
8. **Schreibstil:** keine Geviertstriche, keine Marketing-Floskeln, kurze Sätze,
   du-Form, Schweizer Schreibweise (ss statt ß).

---

## 5. Offen, nach Priorität

### Blockiert den ersten Verkauf
1. DSers: Auto-Update für Preis und Produktdaten AUS, Lagerbestand AN (war beim
   Import die Ursache dafür, dass Preise dreimal auf Einkaufspreis zurückfielen)
2. DSers: Mapping für das 2er-Set mit **Menge 2**
3. Testbestellung mit echter Karte, einmal komplett durch
4. Rechtstexte und Versandseite live
5. Lieferzeit vom Lieferanten schriftlich, dann auf die Versandseite

### Qualität
6. Alt-Texte an den 7 Produktbildern
7. URL-Handle auf `trinkflasche-napf-hund-katze`
8. Produkttyp auf `Haustierzubehör`
9. Tag `hunde-trinkflasche` löschen, Apostroph-Tags korrigieren
10. Zweite Option `550ML-PC` auf `550 ml`
11. Anbieter beim Set auf `Let'sDrink`
12. ZZ Backup löschen, vorher Lieferanten-Link sichern

### Shop-Aufbau
13. Seiten anlegen: Versand und Rückgabe, Häufige Fragen, Über uns
14. Shop-Name prüfen (stand auf "My Store")
15. Hauptnavigation auf Deutsch, vier Punkte
16. Neue Domain, Kategorieebene, nicht produktspezifisch
17. Theme-Sections einbauen (liegen als .liquid bereit)

### Was über Erfolg entscheidet
18. Videos. Drei Clips pro Tag, TikTok und Reels. Ohne das kommt niemand.

---

## 6. Fragen an den Lieferanten, noch offen

```
1. Is the bowl food-safe for dry pet food, or water only?
2. What is the exact material, and is it BPA-free? Documentation please.
3. Is it dishwasher safe?
4. Shipping cost and delivery time to Switzerland?
5. Product weight?
6. Do you ship from an EU warehouse?
```

---

## 7. Was in diesem Paket liegt

### Texte
| Datei | Inhalt |
|---|---|
| `textpaket-letsdrink.md` | Titel, SEO, Produktbeschreibung, Preise, Alt-Texte, Meta-Anzeigentexte, TikTok-Captions |
| `shop-texte-trinkflasche.md` | Startseiten-Felder, Produktseiten-Felder, Versand und Rückgabe, FAQ, Über uns |
| `anzeigentexte.md` | Meta-Kampagnenstruktur, Budgetregeln, Kennzahlen mit Zielwerten |
| `hunde-trinkflasche-paket.md` | Kalkulation, Lieferantenprüfung, 12 Content-Hooks, Tagesplan |
| `shop-aufbau-komplett.md` | Katalogstruktur, Navigation, Seitenstruktur, Lieferanten-Mails |
| `listing-und-content.md` | Listing-Felder, Content-Plan |
| `werbevideo-paket.md` | Drei Ad-Konzepte mit Sekundenplan |

### Theme
| Datei | Zweck |
|---|---|
| `startseite-brunnen.liquid` | Startseiten-Section, settings-gesteuert |
| `produkt-ueberzeugung.liquid` | Produktseiten-Section unter dem Kaufbutton |

Beide sind für ein Katzenprodukt getextet, die Felder sind aber im Theme-Editor
frei änderbar. Die passenden Werte für die Trinkflasche stehen in
`shop-texte-trinkflasche.md`.

### Bilder
- `produktbilder/` — 7 eigene Produktbilder, 1600x1600, bereits in Shopify hoch
- `ad-FOTO-1-farben.png`, `ad-FOTO-2-wasser-futter.png` — Werbebilder auf
  KI-generierten Fotos, 4:5, mit Headline, Beschreibung, Preis, Knopf
- `ad-H1/H2/H3-*.png` — illustrierte Werbebilder, alle sechs Farben, Hunde und
  Katzen gezeichnet, Wasser und Futter laufen aus den liegenden Flaschen
- `ad-B1..B5`, `ad-C1..C3`, `ad-G1..G3` — weitere Ad-Serien

### Skripte (Python, PIL)
| Datei | Zweck |
|---|---|
| `build_scene.py` | illustrierte Serie H, enthält `recolor()` und `BOTTLES` |
| `build_product_images.py` | die 7 Produktbilder |
| `build_photoad.py` | Werbeebene über die generierten Fotos |
| `build_b.py`, `build_colors.py`, `build_fun.py`, `build_ad*.py` | frühere Serien |

**Wichtigster Baustein:** `recolor()` in `build_scene.py`. Es färbt nur die
gesättigte Fläche der grossen Produktaufnahme um und erzeugt daraus alle sechs
Farben in voller Auflösung. Ohne das wären die Farbvarianten nur 81 Pixel breit.

Fonts liegen im Paket, damit die Skripte ohne Netz laufen.

---

## 8. Erster Schritt in Claude Code

```
Lies HANDOFF.md, dann /areas/meowufo.md und /areas/neues-digitalprodukt.md
aus dem Memory. Danach sag mir in drei Sätzen, wo wir stehen, und schlag
den nächsten Schritt vor, ohne mich vorher zu fragen.
```

Empfehlung für den ersten echten Arbeitsschritt: das Theme. Der Shop hat noch
kein eigenes Design, und ein ZIP-fähiges Shopify-Theme lässt sich in Claude Code
mit Dateizugriff deutlich sauberer bauen als hier im Chat.

## Hinweis zu den Bildern

Die Werbebilder liegen als JPEG (Qualitaet 86) statt PNG, damit das Paket
klein bleibt. Fuer den Upload zu Meta oder TikTok reicht das vollstaendig.
Wer PNG braucht: die Skripte in skripte/ erzeugen sie neu.
