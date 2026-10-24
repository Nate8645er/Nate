# Ghost Protocol: Neon Maze

Ein vollständiges Story-Adventure im Browser: Top-Down-Neon-Maze-Action mit
RPG-Systemen, gebaut mit der Higgsfield-Game-Pipeline (HTML5 Canvas, 60 FPS,
Keyboard + Gamepad + Touch, Deutsch/Englisch).

## Story

Ein verlassener Arcade-Automat zieht dich ins **Neon Grid** — eine sterbende
Simulation aus den Erinnerungen aller, die je gespielt haben. Sammle
Erinnerungsfragmente, entkomme den vier KI-Jägern, besiege sechs Bosse und
entscheide am Ende: **Löschen, Retten oder Verschmelzen** (3 Enden).

## Features

- 6 Kapitel (Arcade → Forgotten Network → Neon Factory → Virus Garden → Core Memory → The Architect), 12 Labyrinthe + 6 Boss-Arenen
- 4 Jäger-KIs mit eigener Persönlichkeit (Blaze, Phantom, Widow, Glitch): Patrouille/Suche/Jagd-Statemachine, Gruppenverhalten (geteilte letzte Position), lernende Gegner (kontern deine meistgenutzte Fähigkeit)
- 8 Fähigkeiten: Dash, Hack (Minigame), EMP, Unsichtbarkeit, Zeitlupe, Teleport, Energieschild, Magnet
- 6 Bosse mit Phasen: The Guardian, The Hacker, The Queen, Virus Leviathan, Omega Core, The Architect
- RPG: XP, Level, Skilltree (3 Zweige × 4 Skills), Inventar, Nebenquests mit NPCs (ECHO, BYTE, PIXEL, ROOT, IRIS), Questlog
- Dialogsystem mit Portraits & Typewriter, 36 Lore-Fragmente, Cutscenes je Kapitel, Intro & 3 Ending-Cinematics, Credits
- Level-Mechanik: verschlossene Türen + Datenschlüssel, hackbare Türen, Laser (getimt + geschaltet), Schalter, Portale, Geheimräume, Checkpoints
- Save-System: Autosave + 3 Slots (localStorage, JSON), Achievements (12), Speedrun-Erfolg
- Sound: prozeduraler Synthwave-Soundtrack (WebAudio-Sequencer, dynamische Intensität, Boss-Themes), Higgsfield-SFX + Synth-SFX, Stereo-Panning
- Grafik: prozedurale Neon-Pixel-Sprites nach fester Stilformel, gebakter Bloom, CRT-Filter, Vignette, Screenshake, Partikel-Pool
- Optionen: Sprache (DE/EN), Lautstärken, CRT/Shake/Flash-Toggles, Textgröße, Tasten-Remapping (physische Keycodes)
- Barrierefrei: alle Strings extern (`strings.js`), Touch-UI, Gamepad-API

## Steuerung

| Aktion | Taste | Gamepad |
|---|---|---|
| Bewegen | WASD / Pfeile | Stick / D-Pad |
| Puls-Schuss | Leertaste | A |
| Dash | Shift | B |
| Interagieren/Hacken | E | X |
| EMP | Q | Y |
| Tarnung | C | LB |
| Schild | R | RB |
| Teleport | T | LT |
| Zeitlupe | F | RT |
| Magnet | G | — |
| Skilltree / Questlog / Inventar | K / J / I | Select |
| Pause | Esc | Start |

## Projektstruktur

```
public/
├── index.html      Boot + Fixed-Timestep-Loop (60 Hz), DPR-Cap, Pause-on-Blur
├── logic.js        Plattform-Stub (Solo-Spiel)
├── game.js         Engine: Statemachine, KI, Bosse, UI, Saves, Quests
├── strings.js      Alle Spielertexte DE/EN
├── levels.js       Generierte Karten (deterministische Seeds)
├── sprites.js      Prozedurale Sprite-Factory (Stilformel eingebettet)
├── audio.js        WebAudio: Synthwave-Sequencer + SFX
├── assets/         Generierte SFX (Higgsfield)
└── design/         assets.csv (Manifest), plan.md, thresholds.md

tools/
├── genmaps.mjs        Karten-Generator (Backtracker + Loops + Räume, selbstvalidierend)
└── validate-maps.mjs  Unabhängiger Karten-Validator
```

## Lokal starten

```
cd public && python3 -m http.server 8000
# http://localhost:8000  (Dev-Overlay: http://localhost:8000/?dev=1)
```

## Karten neu generieren

```
node tools/genmaps.mjs && node tools/validate-maps.mjs
```
