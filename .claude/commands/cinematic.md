---
description: Erstellt professionelle Kamera-/Cinematic-Prompts (Higgsfield)
argument-hint: <szene/bildidee>
---

Erstelle professionelle Cinematic Prompts für: $ARGUMENTS

Baue jeden Prompt nach diesem Schema auf:
- **Shot-Typ**: extreme wide / wide / medium / close-up / extreme close-up / over-the-shoulder / POV
- **Objektiv & Look**: Brennweite (z.B. 24mm anamorphic, 85mm portrait), Tiefenschärfe, Filmkorn/Digital
- **Kamerabewegung**: static / slow push-in / dolly / crane / handheld / steadicam / orbit / whip pan
- **Licht**: Key/Fill/Rim, Lichtstimmung (golden hour, low-key noir, neon, overcast soft)
- **Farbwelt & Grading**: Palette, Kontrast, Referenz-Look (z.B. teal-orange, bleach bypass)
- **Stimmung & Stil**: Genre, Tempo, Atmosphäre, ggf. Regisseur-/Film-Referenz
- **Motiv & Aktion**: präzise, konkrete Beschreibung der Bewegung im Bild

Liefere 3–5 Varianten (unterschiedliche Interpretationen), jeweils als fertiger Prompt für `mcp__Higgfield__generate_video` (Video) oder `generate_image` (Still). Bei Modellunsicherheit: `models_explore(action:'recommend')`.
