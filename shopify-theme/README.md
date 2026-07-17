# Aurum Premium – Shopify Theme

Ein vollständiges, produktionsreifes Shopify-Theme (Online Store 2.0) mit
Premium-Design, Conversion-Fokus und deutschen Inhalten. Nach Upload, Zuweisung
der Seiten-Templates und Anpassung der rechtlichen Platzhalter ist der Shop
startklar.

## Projektstruktur

```
shopify-theme/
├── assets/          base.css (ein CSS-File), theme.js (ein JS-File, defer)
├── config/          settings_schema.json (Theme-Settings), settings_data.json
├── layout/          theme.liquid (Grundgerüst, SEO, Fonts, CSS-Variablen)
├── locales/         de.default.json (deutsche Sprachdatei)
├── sections/        Alle Sections inkl. header-group/footer-group (JSON-Gruppen)
├── snippets/        icon, meta-tags, structured-data, price, product-card, free-shipping-bar
├── templates/       JSON-Templates für alle Seiten + gift_card.liquid
├── BRANDING.md      Markenname, Logo, Farben, Schriften, Story, Slogan
└── README.md        Diese Anleitung
```

## Installation

### Variante A: Upload als ZIP (ohne Tools)

1. Den Ordner-Inhalt von `shopify-theme/` als ZIP packen (die Ordner `assets/`,
   `config/`, `layout/` usw. müssen auf oberster Ebene der ZIP liegen):
   `cd shopify-theme && zip -r ../aurum-premium.zip . -x '*.md'`
2. Shopify Admin → **Onlineshop → Themes → Theme hinzufügen → ZIP-Datei hochladen**.
3. Erst als **Entwurf** testen (Vorschau), dann **Veröffentlichen**.

### Variante B: Shopify CLI (empfohlen für Entwicklung)

```bash
npm install -g @shopify/cli
cd shopify-theme
shopify theme dev --store DEIN-STORE.myshopify.com   # Live-Vorschau
shopify theme push --unpublished                      # Als Entwurf hochladen
```

## Einrichtung nach dem Upload (Checkliste)

### 1. Seiten anlegen (Admin → Onlineshop → Seiten)

Für jede Seite das passende Template zuweisen (rechts unter „Theme-Template"):

| Seite (Titel) | Handle (empfohlen) | Template |
| --- | --- | --- |
| FAQ | `faq` | `page.faq` |
| Über uns | `ueber-uns` | `page.about` |
| Kontakt | `kontakt` | `page.contact` |
| Impressum | `impressum` | `page.impressum` |
| Datenschutz | `datenschutz` | `page.datenschutz` |
| Widerruf & Rückgabe | `widerruf` | `page.widerruf` |
| Versand | `versand` | `page.versand` |
| Sendungsverfolgung | `tracking` | `page.tracking` |

Wichtig: Die Handles `kontakt` und `tracking` werden im Theme intern verlinkt
(mobile Navigation, FAQ-Hinweise) – genau so benennen.

### 2. Navigation (Admin → Onlineshop → Navigation)

- **Hauptmenü** (`main-menu`): Kategorien als Menüpunkte. Für das **Mega-Menü**
  einem Menüpunkt Unterpunkte geben, die selbst Unterpunkte haben (3 Ebenen) –
  das Theme rendert dann automatisch ein mehrspaltiges Mega-Menü; 2 Ebenen
  ergeben ein normales Dropdown.
- **Fußzeilenmenü** (`footer`): Hilfe-Links (FAQ, Versand, Tracking, Kontakt) und
  Rechtliches (Impressum, Datenschutz, Widerruf, AGB). Im Theme-Editor können der
  Footer-Section drei getrennte Menü-Spalten zugewiesen werden.

### 3. Theme-Editor (Admin → Onlineshop → Themes → Anpassen)

- **Logo + Favicon** hochladen (Theme-Settings → Marke & Logo).
- **Startseite:** Hero-Bild setzen, Bestseller-Section eine Collection zuweisen,
  CTA-Links prüfen.
- **Warenkorb:** Upsell-Collection zuweisen (Template Warenkorb → Section-Settings).
- **Gratisversand-Schwelle** (Theme-Settings → Versand & Vertrauen) mit den
  echten Versandregeln (Einstellungen → Versand) synchron halten.
- **Tracking-URL** setzen (Theme-Settings → Sendungsverfolgung), z. B.
  `https://www.17track.net/de`.
- **Social-Media-Links** eintragen.
- **Countdown-Section** nur bei echten, terminierten Aktionen einfügen
  (Startseite → Section hinzufügen → Countdown).

### 4. Produkte & Collections

- Produkte mit Beschreibung (Nutzen vor Features), mehreren Bildern und
  **Alt-Texten** anlegen; `Vergleichspreis` nur nutzen, wenn der Preis vorher
  tatsächlich verlangt wurde (Schweiz: Preisbekanntgabeverordnung).
- Eine Collection „Bestseller" pflegen und der Startseiten-Section zuweisen.
- Produkt-Metafelder `reviews.rating` und `reviews.rating_count` werden
  automatisch für Sterne + SEO-Rich-Snippets genutzt (füllt z. B. Judge.me).

### 5. Rechtliches – PFLICHT vor Livegang ⚠️

Die Templates `page.impressum`, `page.datenschutz` und `page.widerruf` enthalten
**gekennzeichnete Platzhalter**. Diese müssen vor Veröffentlichung an das
Zielland angepasst werden (Schweiz: DSG/PBV, kein gesetzliches Widerrufsrecht –
freiwillige Garantie klar beschreiben; DE/AT: DSGVO, 14-Tage-Widerruf inkl.
Musterformular). Zusätzlich unter **Einstellungen → Richtlinien** hinterlegen,
damit sie im Checkout verlinkt werden. Im Zweifel rechtlich prüfen lassen.

### 6. Zahlungen, Versand, Märkte

- Zahlungsarten aktivieren (Einstellungen → Zahlungen): Karten, TWINT, PayPal,
  Apple/Google Pay. Die Footer-/Warenkorb-Icons erscheinen automatisch.
- Versandzonen und -preise konfigurieren; Gratisversand-Schwelle identisch zur
  Theme-Einstellung anlegen.
- Checkout (Einstellungen → Checkout): Kundenkonten optional, Trinkgeld aus,
  Adress-Autovervollständigung an.
- Newsletter-Versprechen decken: Rabattcode **WILLKOMMEN10** (10%) anlegen
  (Admin → Rabatte) und per Willkommens-E-Mail ausliefern (Shopify Email).

## Conversion-Features (eingebaut, ohne Apps)

- Sticky Add-to-Cart-Leiste auf Produktseiten (mobil + Desktop)
- Gratisversand-Fortschrittsbalken im Warenkorb
- Cross-Selling über native Shopify-Produktempfehlungen (Section-Rendering-API)
- Upsell-Grid im Warenkorb (Collection-basiert, blendet bereits gekaufte aus)
- Trust-Badges, Garantie-Accordion, Kaufargumente, Zahlungsarten-Icons
- Bewertungen (kuratierte Testimonials + Metafield-Sterne), Social Proof
- FAQ-Accordions auf Produktseiten + eigene FAQ-Seite mit FAQ-Schema
- Countdown-Banner für echte Aktionen (blendet sich nach Ablauf aus)
- Ankündigungsleiste mit rotierenden Botschaften

## SEO (eingebaut)

- Saubere Meta-Titel/-Descriptions mit Fallbacks (`snippets/meta-tags.liquid`)
- Strukturierte Daten: Organization, WebSite/SearchAction, BreadcrumbList,
  Product (Preis, Verfügbarkeit, Bewertungen), FAQPage, Article
- Alt-Texte überall durchgereicht, kanonische URLs, Open Graph + Twitter Cards
- Interne Verlinkung: Breadcrumbs, Mega-Menü, Footer, Kontakt-/Tracking-Hinweise

## Performance

- Ein CSS- und ein JS-File, JS mit `defer`, keine Frameworks, keine jQuery
- Bilder: responsive `srcset`/`sizes`, Lazy-Loading unterhalb des Folds,
  Hero/LCP-Bild mit `fetchpriority="high"` und `loading="eager"`
- Fonts über Shopify-CDN mit `font-display: swap` (kein Google-Fonts-Request)
- Animationen nur mit `transform`/`opacity`, `prefers-reduced-motion` respektiert

## Apps: native Funktionen zuerst, sonst kostenlos

| Bedarf | Empfehlung (kostenlos) |
| --- | --- |
| Produktbewertungen sammeln | **Judge.me** (Free-Plan) – füllt die `reviews.*`-Metafelder |
| Filter & bessere Suche | **Shopify Search & Discovery** (Shopify, gratis) |
| E-Mail-Marketing / Willkommensserie | **Shopify Email** (gratis Kontingent) |
| Chat/Support | **Shopify Inbox** (gratis) |
| Automatisierungen | **Shopify Flow** (gratis) |
| Übersetzungen (falls mehrsprachig) | **Translate & Adapt** (Shopify, gratis) |

## Launch-Checkliste

- [ ] Rechtstexte (Impressum/Datenschutz/Widerruf) ersetzt und geprüft
- [ ] Zahlungsarten + Versandzonen konfiguriert, Testbestellung durchgeführt
- [ ] Seiten angelegt und Templates zugewiesen (Tabelle oben)
- [ ] Menüs gepflegt (Hauptmenü + Footer)
- [ ] Logo, Favicon, Hero-Bild, Produktbilder mit Alt-Texten
- [ ] Gutschein WILLKOMMEN10 angelegt (deckt das Newsletter-Versprechen)
- [ ] Mobil getestet: Navigation, Produktseite, Sticky-ATC, Checkout
- [ ] Google Search Console verbunden, Sitemap eingereicht (`/sitemap.xml`)
