# Deployment

- **Play URL:** https://sharp-mesa-477.higgsfield.gg/
- **game_id:** `b70a95af-dc9f-4b78-af19-ec7e5514164c` (für Updates an `deploy_game` zurückgeben — niemals weglassen, sonst entsteht ein zweites Spiel)
- **slug:** sharp-mesa-477
- Deployed: 2026-07-07, mode `rules` (logic.js Stub, Solo-Spiel)

## Update-Ablauf

1. Änderungen in `public/` machen, lokal testen (`tools/smoke.mjs`, `tools/deepsmoke.mjs`)
2. `cd public && zip -qr ../dist/game.zip logic.js index.html game.js strings.js levels.js sprites.js audio.js assets design`
3. Zip committen + pushen (raw.githubusercontent-URL dient als `source_game`)
4. `deploy_game` mit **demselben `game_id`** aufrufen

## Asset-Upgrade bei verfügbaren Higgsfield-Credits

Die Cutscene-Backdrops und Musik sind aktuell prozedural (Credits waren beim Build
aufgebraucht; 2 SFX wurden noch generiert). Upgrade-Pfad ohne Code-Änderung:

1. 10 Bilder gemäß `public/design/assets.csv` mit `nano_banana_2` generieren
   (STYLE FORMULA aus `public/design/plan.md` byte-identisch einbetten),
   2 Musik-Loops mit `sonilo_music` (40s/30s), 3 restliche SFX mit `mirelo_text_to_audio`
2. URLs in `public/assets/manifest.json` unter `images` (keys: `title`, `ch1`..`ch6`,
   `end_delete`, `end_save`, `end_merge`) bzw. `sfx` eintragen
3. Neu zippen und mit `game_id` re-deployen — das Spiel bevorzugt gelistete Assets
   automatisch und fällt sonst auf die prozedurale Version zurück
