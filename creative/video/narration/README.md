# Voiceover + Untertitel (lokal, kostenlos)

Deutsches Voiceover für `TariffExplainer` mit [Piper](https://github.com/OHF-Voice/piper1-gpl)
— lokal, kostenlos, keine laufenden Kosten. Untertitel werden **deterministisch**
aus derselben Zeitquelle erzeugt (keine Spracherkennung nötig, da die
Szenenzeiten bereits exakt bekannt sind).

## Warum Piper statt Kokoro

Der Master-Prompt nennt Kokoro als lokale TTS-Option. **Kokoro hat aber kein
Deutsch** im Stimmen-Repertoire (nur Englisch, Japanisch, Chinesisch,
Spanisch, Französisch, Hindi, Italienisch, Portugiesisch — geprüft über
`kokoro_onnx.Kokoro.get_voices()`). Für deutschsprachigen Content wäre das
falsch ausgesprochenes Englisch-Modell-Deutsch gewesen — deshalb stattdessen
**Piper** mit der deutschen Stimme `de_DE-thorsten-medium` (echtes
deutsches Trainingsmaterial, CPU-tauglich, ~63 MB statt Kokoros ~350 MB).

## Funktionsweise (kein Rätselraten bei der Video-Länge)

1. `synthesize.py` liest `script_de.json` (ein Satz pro Szene), lässt Piper
   jede Szene **wirklich synthetisieren** und **misst die echte Sprechdauer**
   (kein geschätztes Timing).
2. Diese gemessenen Dauern (+ 0.6 s Puffer, min. 2.5 s) werden in
   `out/timing.json` geschrieben.
3. `../src/TariffExplainer.tsx` importiert `timing.json` direkt (TypeScript
   `resolveJsonModule`) und richtet die Remotion-`<Sequence>`-Längen exakt
   danach aus — die Szene ist nie kürzer als die Sprachaufnahme.
4. `generate_srt.py` erzeugt SRT/VTT aus derselben `timing.json` — Video und
   Untertitel können dadurch nie auseinanderlaufen.

## Setup (Modell nicht im Git, ~63 MB)

```bash
mkdir -p ../.models/piper-de
curl -sL -o ../.models/piper-de/de_DE-thorsten-medium.onnx \
  "https://huggingface.co/rhasspy/piper-voices/resolve/main/de/de_DE/thorsten/medium/de_DE-thorsten-medium.onnx"
curl -sL -o ../.models/piper-de/de_DE-thorsten-medium.onnx.json \
  "https://huggingface.co/rhasspy/piper-voices/resolve/main/de/de_DE/thorsten/medium/de_DE-thorsten-medium.onnx.json"
pip install piper-tts
```

## Nutzung

```bash
python3 synthesize.py        # -> out/*.wav + out/timing.json (ECHT gemessen)
cp out/*.wav ../public/audio/  # Remotion liest ueber staticFile() aus public/
python3 generate_srt.py      # -> out/subtitles_de.srt + .vtt
cd .. && npm run render      # Video MIT Voiceover
```

## Verifiziert (real, nicht nur behauptet)

- Reale Sprechdauern gemessen: Title 4.74s, Free 6.61s, Starter 7.08s,
  Pro 8.21s, Business 8.34s, Enterprise 7.50s, Outro 3.46s.
- Gerendertes Video: 50.15s, `ffprobe` bestätigt AAC-Audiospur (48kHz,
  stereo), `ffmpeg volumedetect` bestätigt echten Pegel (mean −18.5 dB,
  max −2.9 dB — keine Stille).
- Untertitel-Gesamtlänge (50.13s) stimmt mit der Videolänge überein
  (Rundungsdifferenz < 30ms durch Frame-Rundung).
- `test_generate_srt.py`: 6 Tests grün (Zeitformat, lückenlose/nicht
  überlappende Untertitel).

## Struktur

```
narration/
  script_de.json         Ein Satz pro Szene (Quelle der Wahrheit fuer den Text)
  synthesize.py           Piper-Synthese + Dauer-Messung -> out/timing.json
  generate_srt.py         Deterministische SRT/VTT-Erzeugung aus timing.json
  test_generate_srt.py    Tests der Zeitformatierung (pytest)
  out/                    Generiert, NICHT versioniert (.gitignore):
                          *.wav, timing.json, subtitles_de.srt/.vtt
```

## Bekannte Grenzen

- Nur Deutsch. Für eine englische Variante bräuchte es eine zweite
  `script_en.json` + eine englische Piper-Stimme (Kokoro wäre dafür geeignet).
- Keine Silben-genaue Wort-Hervorhebung in den Untertiteln (Satz-Ebene,
  nicht Wort-Ebene) — für Barrierefreiheit ausreichend, nicht "Karaoke-Stil".
