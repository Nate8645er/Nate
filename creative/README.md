# Creative-Pipeline — Produkt C (selbst gebaut)

Programmatische Ad-Creative-Erzeugung **ohne Fremd-Credits und ohne Browser**:
aus `tariffs.json` werden Tarif-Creatives als **SVG** (Code, deterministisch)
in drei Werbe-Formaten erzeugt — 1:1, 4:5, 9:16 (Meta/TikTok/Google).

## Warum selbst gebaut (statt generativem Dienst)

- **Deterministisch & versionierbar**: Gleiche Eingabe → gleiche Ausgabe, im Git
  nachvollziehbar. Kein Zufall, keine „Fantasie-UI".
- **Keine laufenden Kosten**: reine Text-/Vektor-Erzeugung, keine Credits.
- **Eine Wahrheit**: `tariffs.json` spiegelt die Tarife aus
  `platform-backend/migrations/002_seed_plans.sql`. Ändern sich Preise oder
  Funktionen, hier anpassen und neu rendern → alle Assets sind aktuell (DoD C).

## Nutzung

```bash
python generate.py          # rendert alle Tarife × alle Formate nach out/
```

Ergebnis: `out/<tarif>_<format>.svg` + `out/index.html` (Galerie zum Sichten).

## Nach PNG (optional, ohne Kosten)

SVG lässt sich verlustfrei rastern, z. B.:

```bash
rsvg-convert out/pro_1x1.svg -o out/pro_1x1.png      # librsvg
# oder: inkscape / resvg / headless Chromium
```

## Struktur

```
creative/
  tariffs.json     Tarif-Wahrheit (Preise CHF inkl. MwSt, ehrlich)
  generate.py      reine Render-Funktionen + CLI
  out/             erzeugte SVGs + index.html (versioniert)
  tests/           Tests der Render-Funktionen (kein Browser)
```

## Nächste Ausbaustufen (geplant)

- Erklärvideos pro Tarif als **Remotion** (Video als Code) — gleiche
  Datenquelle, ein Render-Befehl.
- Bildschirmaufnahmen der **echten** Plattform-Oberfläche für
  Anleitungsvideos (nicht generierte UI).
- Lokales TTS (Kokoro) für Voiceover — ohne laufende Kosten.
