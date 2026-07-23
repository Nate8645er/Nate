# BASELINE.md — Referenzstand vor dem Ausbau (Phase 0)

Zweck: ein reproduzierbarer „grüner" Ausgangspunkt. Jede spätere Phase muss diese Baseline
mindestens halten (keine Regression).

## 1. Umgebung

- Verzeichnis: `ai-command-center/`
- Node: v22 (Container), Paketmanager laut `vercel.json`: **pnpm**; hier ausgeführt via `npx`.
- `node_modules` vorhanden (kein Neu-Install nötig für den Testlauf).

## 2. Testlauf (Vitest)

Befehl:

```bash
cd ai-command-center
npx vitest run
```

Ergebnis (Phase-0-Messung):

```
Test Files  20 passed (20)
Tests      195 passed (195)
Duration   ~6.1 s
```

Abgedeckte Bereiche: `features, license, shopify-license, preise, roi, mail, kunden, memory,
integrations, ratelimit, vision, vorlagen, freigabe, aufnahme, blitz, demo-org, dokumente, daten,
zahlung-login, zuverlaessigkeit`.

## 3. Typprüfung

```bash
npx tsc --noEmit      # Exit 0 — keine Fehler
```

## 4. Build

Nicht Teil der Phase-0-Messung (Netz/Turbopack). In den Vorsessions lief `next build` grün
(50/50 statische Seiten). Für die Baseline zählt der Vertrag: **`vitest run` grün + `tsc`
sauber**. Ein Build-Gate gehört in die CI aus Phase 1.

## 5. Umfang (Referenzgröße)

- `lib/` + `app/`: **~21.300 Zeilen** TypeScript/TSX.
- 14 API-Routen, 28 UI-Seiten, ~32 `lib/`-Module, 20 Test-Dateien.

## 6. Reproduktion / Regressions-Gate

Eine Änderung gilt erst als „grün", wenn nach ihr gilt:

```bash
cd ai-command-center
npx tsc --noEmit          # Exit 0
npx vitest run            # 20 files / ≥195 tests passed
```

Neue Module bringen **eigene** Tests mit (Auftrag §0.4), sodass diese Zahl mit dem Ausbau steigt,
nie fällt.

## 7. Bekannte, bewusst offene Punkte (kein Fehler, sondern Ist-Stand)

- Rate-Limit ohne Upstash = nur In-Memory (pro Instanz) — dokumentiert in `lib/ratelimit.ts`.
- Missionen ohne LLM-Key laufen im **Demo-Modus** (echte Struktur, klar markiert).
- Kein E2E-/Last-Test in der Baseline (gehört in Phase 8 bzw. CI).
