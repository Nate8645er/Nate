# Session-Übergabe (Stand 2026-07-29)

Für die nächste Session: Alles hier ist committet auf Branch
`claude/handoff-md-uebergabe-ozku9b` (PR #46). CLAUDE.md verweist hierher.

## Wo wir stehen

**Let'sDrink-Shop (Shopify, Store `i0m1xi-h5`, shared Backend mit MeowUfo):**
- Produkt live: "Trinkflasche mit Napf, 550 ml" —
  `gid://shopify/Product/15672665997689`, CHF 29.90, 6 Farbvarianten,
  SEO gesetzt. Duplikat-Produkt wurde geloescht.
- Rabatte live: Automatik "2 kaufen 1 gratis" (wirkt auch 4+2/6+9,
  `gid://shopify/DiscountAutomaticNode/2391964811641`) + Code LETSDRINK10
  (`gid://shopify/DiscountCodeNode/2391982342521`).
- Theme "animations-theme" (`gid://shopify/OnlineStoreTheme/196787667321`,
  UNPUBLISHED): komplettes Comic-See-Design mit Animationen (laufende
  Hunde/Katzen, Flaschen-Regen, Parade, Deal-Picker 1/3/6/9,
  Newsletter-Popup mit LETSDRINK10, Mobile-Overflow-Fix). Alle 36 Dateien
  per API eingespielt, MD5-verifiziert gegen
  `letsdrink/shopify-theme-letsdrink/` (Repo = Quelle der Wahrheit).
- 6 Rechts-/Infoseiten angelegt (Impressum, Datenschutz, AGB, Versand,
  FAQ, Ueber uns) — Platzhalter [Name]/[Adresse]/[E-Mail]/[Lieferzeit]
  muss Nate selbst fuellen.
- Details/Verlauf: `letsdrink/STATUS-2026-07-28.md`.

**Arbeitsregeln (immer):**
- Theme-Aenderungen DIREKT per Shopify-API in Theme 196787667321
  (themeFilesUpsert; kleine Dateien BASE64, grosse via stagedUploadsCreate
  → curl-POST → body.type URL). KEINE ZIPs schicken. Nie aufs Live/MAIN-
  Theme schreiben. Andere Marken im Backend nicht anfassen.
- UWG/HANDOFF: keine Fake-Bewertungen/-Countdowns, keine unbelegten
  Material-Claims, 14 Tage Rueckgabe freiwillig, Du-Form, "ss" statt "ß".

**Umgebung (eingerichtet 2026-07-29, siehe UMGEBUNG-SETUP.md):**
- Repo = Plugin-Marketplace `nate-marketplace` mit ultra-enterprise-os
  UND graphify-plugin (3 Skills, 3 Agenten). Beide in
  `.claude/settings.json` aktiviert.
- SessionStart-Hook installiert graphify-CLI automatisch
  (`pip install graphifyy`, Kommando: `graphify`).
- Repo-Wissensgraph in `graphify-out/` (581 Knoten). Auffrischen:
  `graphify update .` Abfragen: `graphify explain "X"` /
  `graphify path "A" "B"`.
- graphify ist auch als claude.ai-Plugin hochgeladen und aktiviert
  (insgesamt 83 Plugins am Konto aktiv; Empfehlung: ungenutzte
  deaktivieren, damit Trigger treffsicher bleiben).

## Offene Punkte

Nur Nate kann:
1. PR #46 mergen → aktiviert Marketplace-Plugins + Hook fuer alle
   kuenftigen Sessions.
2. Theme veroeffentlichen (Admin → Themes → animations-theme → Vorschau
   → Veroeffentlichen).
3. Platzhalter auf den 6 Rechtsseiten fuellen.
4. DSers: Mapping der Trinkflasche pruefen (Duplikat wurde geloescht!)
   — KEIN Advanced Mapping noetig, Mengen-Deal laeuft ueber Stueckzahl.
5. Testbestellung (Menge 3 → Kasse zieht 1 Flasche ab).

Naechste sinnvolle Claude-Aufgaben (wenn Nate will):
- Screenshot-Feedback zur Theme-Vorschau einarbeiten (direkt per API)
- E-Mail-Flows aus `letsdrink/texte/email-flows.md` in Shopify Email
- Google-Ads-Setup nach `letsdrink/texte/google-ads.md`

## Start-Prompt fuer neue Session

"Lies CLAUDE.md und SESSION-HANDOFF.md und mach beim Let'sDrink-Shop
weiter, ohne mich zu fragen. Theme-Aenderungen direkt per Shopify-API,
keine ZIPs."
