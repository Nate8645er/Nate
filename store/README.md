# Store — Produkt B (Shopify-Abo-Store)

Der Verkaufskanal für die Tarife aus Produkt A. **Getrennt** von bestehenden
Stores: eigene Domain, eigenes Theme, eigene Rechtstexte.

## Was hier liegt

```
store/
  layout/
    theme.liquid            Grundgeruest (Header/Footer/Meta), bindet base.css ein
  assets/
    base.css                Globale Palette (dunkel/Premium), gemeinsam fuer alle Sektionen
  sections/
    header.liquid           Logo + Navigation (Bloecke) + Warenkorb-Link
    footer.liquid           Copyright + Links zu den Rechtstexten (blendet fehlende aus)
    hero.liquid             Startseiten-Aufmacher (Ueberschrift/Unterzeile editierbar)
    features.liquid         Funktionen-Grid (Bloecke) -- was die Plattform WIRKLICH kann
    tariffs.liquid          Tarif-Vergleich (Bloecke = Tarife)
    faq.liquid              Haeufige Fragen (Bloecke, <details>-Akkordeon, kein JS)
    main-product.liquid     Produktseite pro Abo-SKU (Preis kommt von Shopify, nicht hart kodiert)
  templates/
    index.liquid            Startseite: Hero + Funktionen + Tarife + FAQ
    product.liquid          Bindet main-product.liquid ein (fuer die 5 Abo-Produkte)
    page.impressum.liquid   Anbieterkennzeichnung
    page.agb.liquid         AGB: Preise, Abrechnung, Kuendigung, Haftung
    page.datenschutz.liquid Datenschutzerklaerung (revDSG, ggf. DSGVO)
    page.widerruf.liquid    Kuendigung + freiwillige 14-Tage-Kulanz
  config/
    settings_schema.json    Theme-Einstellungen, u.a. Firmendaten fuer die Rechtstexte
```

Alle Liquid-Dateien sind auf Tag-Balance und die `{% schema %}`-JSONs auf
Gültigkeit geprüft (kein Shopify-CLI in dieser Umgebung verfügbar, daher
strukturelle statt Live-Validierung).

## Vor Veröffentlichung: zwei operative Schritte

1. **Firmendaten eintragen**: Theme-Editor → Einstellungen → „Firmendaten
   (Rechtstexte)" — füllt `settings.legal_*`, das die vier Rechtstext-Seiten
   referenzieren. Hier bewusst **keine** Firmendaten erfunden (Master-Prompt:
   keine erfundenen Fakten); ungefüllt zeigen die Seiten `[Platzhalter]`.
2. **Seiten anlegen**: Im Shopify-Admin unter „Onlineshop → Seiten" vier
   Seiten mit **genau diesen Handles** anlegen und der passenden Vorlage
   zuweisen, damit Footer-Links und `page.<handle>.liquid` greifen:
   `impressum` → `page.impressum`, `agb` → `page.agb`,
   `datenschutz` → `page.datenschutz`, `widerruf` → `page.widerruf`.
   Der Footer blendet einen Link automatisch aus, solange die zugehörige
   Seite noch nicht existiert (bricht also nichts, wenn das noch aussteht).

Alle vier Rechtstexte sind Vorlagen und ersetzen keine Rechtsberatung.

## Automatische Freischaltung (Store → Plattform)

Der Kauf löst die Kontoerstellung in Produkt A aus:

1. Shopify-Webhook **`orders/paid`** → `POST /webhooks/shopify/orders-paid`
   (im `platform-backend`, HMAC-verifiziert gegen `SHOPIFY_WEBHOOK_SECRET`).
2. Der Webhook liest den Tarif aus der Artikel-**SKU** nach der Konvention
   `plan-<code>` (z. B. `plan-pro`) und die Kunden-E-Mail.
3. Er legt Mandant + API-Key an (`provision_tenant`). Die Zustellung der
   Zugangsdaten an den Kunden ist ein separater Schritt (E-Mail-Flow).

**Wichtig:** Lege die Abo-Produkte im Store mit genau diesen SKUs an
(`plan-free`, `plan-starter`, `plan-pro`, `plan-business`, `plan-enterprise`).

## Deploy-Regel (nicht verhandelbar)

Theme **immer als Draft/Development** hochladen, **nie** direkt ins Live-Theme.
Veröffentlichung macht der Betreiber manuell.

```bash
# Beispiel mit Shopify CLI — als unveroeffentlichtes Theme:
shopify theme push --unpublished --path store
# oder Entwicklungs-Theme:
shopify theme dev --path store
```

## Schweizer Recht (UWG/PBV) — Checkliste

- [x] Preise in **CHF inkl. MwSt**, klar ausgewiesen (Sektion zeigt „inkl. MwSt").
- [x] Keine Fake-Verknappung, keine Countdown-Balken.
- [x] Keine erfundenen Bewertungen/Testimonials.
- [x] Keine falschen Streichpreise.
- [x] Impressum, AGB, Datenschutz, Widerruf/Kündigung als Seitenvorlagen,
      im Footer verlinkt — **Firmendaten vor Live-Schaltung im Theme-Editor
      eintragen (siehe oben).**

## Design

Dieselben Design-Tokens wie `platform-backend/static/{index,dashboard}.html`
(siehe `assets/base.css`): tieferes Off-Black, Space-Grotesk-Ueberschriften,
derselbe Akzentfarbverlauf. Ein Look ueber Produkt A und Produkt B hinweg,
nicht zwei getrennte Marken-Identitaeten.

## Bewusst offen

- Kein Kundenbereich mit Onboarding-Videos — wartet auf die
  Erklärvideos aus `../creative/video/` (Produkt C).
- Lighthouse-Performance-Check (DoD ≥ 90 mobil) — braucht einen echten
  Shopify-Store-Deploy, hier nicht durchführbar.
- `features.liquid`/`faq.liquid` sind neue Standard-Inhalte (Runde 2) —
  Texte im Theme-Editor anpassbar, aber die Standardwerte beschreiben nur,
  was in `platform-backend/` tatsächlich existiert und getestet ist (13er-
  Council, echte Composio-Integrationen, Streaming, automatisches
  Onboarding). Ändert sich eine dieser Fähigkeiten, hier nachziehen.
