---
description: Erstellt Produktwerbung/Produktvideo (Higgsfield)
argument-hint: <produkt> [plattform]
---

Erstelle eine Produktwerbung für: $ARGUMENTS

Vorgehen (Werbeagentur + Social Media Creator Workflow kombiniert):
1. **Produkt-Analyse**: USP, Zielgruppe, Plattform (Standard: Social 9:16 + 16:9 Master).
2. **Konzept**: Hook (erste 2 Sekunden!), Produkt-Demo/Benefit, Social Proof, CTA.
3. **Shot-List mit Prompts**:
   - Produkt-Stills: higgsfield-product-photoshoot Skill (Modi: product_shot, lifestyle_scene, hero_banner, ad_creative_pack).
   - Video-Shots: `mcp__Higgfield__generate_video` (Seedance 2.0) bzw. Marketing Studio für UGC-/Avatar-Ads (Produkt per URL importierbar: `media_import_url`).
   - Marketplace-Listings: higgsfield-marketplace-cards Skill.
4. **Varianten** für A/B-Tests (unterschiedliche Hooks).
5. Optional: `virality_predictor` auf fertige Videos anwenden.

Rendern nur nach Bestätigung (Credits).
