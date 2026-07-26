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

## Optional: bezahlte Hintergründe (MuAPI)

Die Pipeline kann generierte Hintergrundbilder einbinden — **nur die
Atmosphäre**, niemals Text. Empfehlung des KI-Teams (Council-Konsultation,
4/4 Modelle konvergent): generative Bilder für emotionale, nicht
datengebundene Flächen; alle Preise/Pflichtangaben bleiben deterministischer
SVG-Text, darüber gelegt. Grund: in der Schweiz muss ein Preis exakt stimmen
(Preisbekanntgabeverordnung) — das kann ein Bildmodell nicht zuverlässig,
Code schon.

```bash
python muapi_backdrop.py --list                # Motive ansehen
python muapi_backdrop.py --only pro             # Dry-Run (0 Kosten)
python muapi_backdrop.py --only pro --generate   # erzeugt wirklich, kostet Credits
python generate.py                              # bindet backdrops/*.png automatisch ein
```

Ohne `backdrops/` (Standard, nichts generiert) rendert `generate.py` wie
bisher mit reinem Farbverlauf — die Pipeline funktioniert immer, auch ohne
MuAPI-Key. Jeder Prompt enthält eine ausdrückliche Text-Verbotsklausel
(getestet in `tests/test_generate.py`), damit das Bildmodell keinen
Pseudo-Text erzeugt, der mit dem echten Preis kollidieren könnte.

**Wichtig, falls du Backdrop-Varianten committen willst:** `backdrops/` ist
per `.gitignore` bewusst nicht versioniert (wie `.models/` bei der
Video-Pipeline — kostenpflichtige Modell-Ausgaben gehören nicht ins Git).
Die aktuell committeten `out/*.svg` sind backdrop-frei und bleiben es in CI
(dort wird nichts generiert). Willst du eine Backdrop-Version fest
versionieren: `git add` sowohl die neuen `out/*.svg` **als auch** die
zugehörigen `backdrops/*.png` — sonst verweist die committete SVG auf ein
Bild, das im Repo gar nicht existiert.

## Nach PNG (optional, ohne Kosten)

SVG lässt sich verlustfrei rastern, z. B.:

```bash
rsvg-convert out/pro_1x1.svg -o out/pro_1x1.png      # librsvg
# oder: inkscape / resvg / headless Chromium
```

## Struktur

```
creative/
  tariffs.json        Tarif-Wahrheit (Preise CHF inkl. MwSt, ehrlich)
  generate.py          reine Render-Funktionen + CLI, bindet backdrops/ optional ein
  muapi_backdrop.py    Hintergrundbilder via MuAPI (bezahlt, opt-in, --dry-run per Default)
  backdrops/           generierte PNGs, NICHT versioniert (.gitignore)
  out/                 erzeugte SVGs + index.html (versioniert)
  tests/               Tests der Render-Funktionen (kein Browser)
  video/               Erklärvideo-Pipeline (Remotion + Piper-Voiceover, eigenes README)
```

## Nächste Ausbaustufen (geplant)

- Bildschirmaufnahmen der **echten** Plattform-Oberfläche für
  Anleitungsvideos (nicht generierte UI) — kann eine KI-Sitzung nicht
  produzieren, braucht einen Menschen mit der laufenden Plattform.
