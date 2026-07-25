# Erklärvideo-Pipeline — Produkt C (Remotion, selbst gebaut)

Video als React-Code (Remotion) — **kein Fremd-Dienst, keine Credits**.
Ein Befehl rendert das Erklärvideo neu, wenn sich Tarife/Preise ändern
(Master-Prompt-DoD: „Ein Befehl rendert alle Tarif-Videos neu").

Ergänzt `../generate.py` (Ad-Creatives als SVG) um bewegte Bilder — gleiche
Datenquelle, gleiches dunkles Premium-Design (`src/theme.ts` spiegelt die
Palette aus `../generate.py` und `platform-backend/static/index.html`).

## Was entsteht

Ein 26-sekündiges 1920×1080-Video (30 fps, H.264): Titelkarte → je eine
Szene pro Tarif (Name, Preis CHF inkl. MwSt, Kernfunktionen) → Outro. Wirklich
gerendert und verifiziert (Dauer/Auflösung/Codec via `ffprobe`, Bildinhalt
per Screenshot geprüft).

## Nutzung

```bash
npm install
npm run render     # -> out/explainer.mp4
npm run still      # -> out/preview.png (Einzelbild zur Vorschau)
npm test           # Timing-/Daten-Tests (vitest)
```

Chromium wird beim ersten Render automatisch von Remotion selbst verwaltet
(`npx remotion browser ensure`) — unabhängig vom in dieser Umgebung
vorinstallierten Playwright-Chromium, da Remotion eine eigene
Headless-Shell-Variante braucht.

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
    TariffExplainer.tsx    Die Komposition: Titel, Tarif-Szenen, Outro
    index.tsx               Remotion-Root (Composition-Registrierung)
    timing.test.ts         Tests: Tarif-Vollständigkeit, Gesamtlänge
  remotion.config.ts
  out/                     Generiert, nicht versioniert (.gitignore)
```

## Bekannte Grenzen (ehrlich, Master-Prompt-konform)

- **Kein Voiceover, keine Untertitel** in dieser Scheibe — geplant: lokales
  TTS (Kokoro) für Voiceover, `faster-whisper`/`whisperX` für Untertitel-
  Zeitstempel, wie im Master-Prompt (Kap. 5.4) vorgesehen.
- **Keine Anleitungsvideos**: Die Master-Prompt-Regel verlangt für
  Klick-für-Klick-Anleitungen echte Bildschirmaufnahmen der tatsächlichen
  Oberfläche — die kann eine KI-Sitzung nicht produzieren. Dieses Video ist
  ein **Tarif-Erklärvideo** (Produktvorstellung), keine Anleitung.
- `src/tariffs.ts` ist eine manuell gepflegte Kopie der Tarif-Wahrheit (kein
  automatischer JSON-Import in dieser einfachen Pipeline) — bei Preisänderung
  hier UND in `../tariffs.json` UND in der Backend-Migration nachziehen.
