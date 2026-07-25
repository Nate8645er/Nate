# Store — Produkt B (Shopify-Abo-Store)

Der Verkaufskanal für die Tarife aus Produkt A. **Getrennt** von bestehenden
Stores: eigene Domain, eigenes Theme, eigene Rechtstexte.

## Was hier liegt

```
store/
  sections/
    tariffs.liquid          Tarif-Vergleich als Theme-Sektion (Bloecke = Tarife)
  templates/
    page.impressum.liquid   Anbieterkennzeichnung
    page.agb.liquid         AGB: Preise, Abrechnung, Kuendigung, Haftung
    page.datenschutz.liquid Datenschutzerklaerung (revDSG, ggf. DSGVO)
    page.widerruf.liquid    Kuendigung + freiwillige 14-Tage-Kulanz
```

**Vor Veröffentlichung:** In jeder Rechtstext-Datei die `shop.metafields.legal.*`-
Platzhalter (Firmenname, Adresse, UID, Kontakt) über Theme-Einstellungen oder
Metafields mit den echten Angaben füllen — hier bewusst nicht erfunden.
Alle vier Seiten sind Vorlagen und ersetzen keine Rechtsberatung.

Weitere Theme-Teile (Layout, Kundenbereich) folgen additiv.

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
- [x] Impressum, AGB, Datenschutz, Widerruf/Kündigung als Seitenvorlagen —
      **Firmendaten-Platzhalter müssen vor Live-Schaltung gefüllt werden.**
