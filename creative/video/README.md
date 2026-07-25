# Erklärvideo-Pipeline — Produkt C (Remotion, selbst gebaut)

Video als React-Code (Remotion) — **kein Fremd-Dienst, keine Credits**.
Ein Befehl rendert das Erklärvideo neu, wenn sich Tarife/Preise ändern
(Master-Prompt-DoD: „Ein Befehl rendert alle Tarif-Videos neu").

Ergänzt `../generate.py` (Ad-Creatives als SVG) um bewegte Bilder — gleiche
Datenquelle, gleiches dunkles Premium-Design (`src/theme.ts` spiegelt die
Palette aus `../generate.py` und `platform-backend/static/index.html`).

## Was entsteht

Ein ~50-sekündiges 1920×1080-Video (30 fps, H.264 + AAC-Stereo): Titelkarte
→ je eine Szene pro Tarif (Name, Preis CHF inkl. MwSt, Kernfunktionen) →
Outro, **mit deutschem Voiceover** (lokales TTS, siehe `narration/README.md`).
Die Szenenlänge richtet sich nach der **echt gemessenen** Sprechdauer der
jeweiligen Szene — kein geschätztes Timing. Wirklich gerendert und verifiziert
(Dauer/Auflösung/Codec/Audiopegel via `ffprobe`+`ffmpeg volumedetect`,
Bildinhalt per Screenshot geprüft).

## Nutzung

```bash
# 1) Voiceover synthetisieren (einmalig Modell laden, siehe narration/README.md)
cd narration && python3 synthesize.py && cp out/*.wav ../public/audio/ && python3 generate_srt.py && cd ..

# 2) Video rendern
npm install
npm run render     # -> out/explainer.mp4 (mit Voiceover)
npm run still      # -> out/preview.png (Einzelbild zur Vorschau)
npm test           # Timing-/Daten-Tests (vitest)
```

Chromium wird beim ersten Render automatisch von Remotion selbst verwaltet
(`npx remotion browser ensure`) — unabhängig vom in dieser Umgebung
vorinstallierten Playwright-Chromium, da Remotion eine eigene
Headless-Shell-Variante braucht.

## Voiceover + Untertitel

Siehe `narration/README.md` für die volle Doku. Kurzfassung: **Piper**
(lokal, kostenlos) statt Kokoro, weil Kokoro kein Deutsch spricht — ehrlich
dokumentierte Korrektur einer impliziten Master-Prompt-Annahme. Die
Szenenlänge im Video richtet sich nach der echt gemessenen Sprechdauer
(`narration/synthesize.py`), Untertitel werden deterministisch aus derselben
Zeitquelle erzeugt (`narration/generate_srt.py`) — Video und Untertitel
können nicht auseinanderlaufen.

## Sicherheit

`npm audit` wurde ausgeführt und die gefundenen Probleme behoben, nicht nur
zur Kenntnis genommen: die ursprünglich gewählte Remotion-Version enthielt
eine **kritische RCE-Schwachstelle** (GHSA-2jqp-f4gr-44fr) und eine
Schwachstelle für beliebiges Datei-Schreiben (GHSA-g6pc-6676-c23j). Fix:
`remotion`/`@remotion/cli` auf `4.0.499` gehoben, `vitest` auf `4.1.10`
(behebt zusätzlich eine esbuild-Dev-Server-Schwachstelle). Danach:
`npm audit` → **0 Schwachstellen**. `package-lock.json` ist committed für
reproduzierbare, geprüfte Builds.

## Struktur

```
video/
  src/
    tariffs.ts            Tarif-Daten (manuell synchron mit ../tariffs.json
                           und platform-backend/migrations/002_seed_plans.sql)
    theme.ts               Farbpalette (identisch zu SVG-Pipeline + UI)
    TariffExplainer.tsx    Die Komposition: Titel, Tarif-Szenen, Outro,
                           Timing + <Audio> aus narration/out/timing.json
    index.tsx               Remotion-Root (Composition-Registrierung)
    timing.test.ts         Tests: Tarif-Vollständigkeit, Timing-Konsistenz
  narration/               Voiceover + Untertitel-Pipeline (siehe eigenes README)
  public/audio/            Voiceover-WAVs fürs Rendering (generiert, .gitignore)
  remotion.config.ts
  out/                     Generiert, nicht versioniert (.gitignore)
```

## Bekannte Grenzen (ehrlich, Master-Prompt-konform)

- **Keine Anleitungsvideos**: Die Master-Prompt-Regel verlangt für
  Klick-für-Klick-Anleitungen echte Bildschirmaufnahmen der tatsächlichen
  Oberfläche — die kann eine KI-Sitzung nicht produzieren. Dieses Video ist
  ein **Tarif-Erklärvideo** (Produktvorstellung), keine Anleitung.
- `src/tariffs.ts` ist eine manuell gepflegte Kopie der Tarif-Wahrheit (kein
  automatischer JSON-Import in dieser einfachen Pipeline) — bei Preisänderung
  hier UND in `../tariffs.json` UND in der Backend-Migration UND in
  `narration/script_de.json` nachziehen.
- Nur deutsches Voiceover (siehe `narration/README.md` für Details/Grenzen).
