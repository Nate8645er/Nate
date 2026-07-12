## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).

# Graphify Token Optimization Rules

- Nutze Graphify zuerst, bevor du große Codebereiche liest.
- Frage den Knowledge Graph ab (`graphify query "<Frage>"`), bevor du Dateien öffnest.
- Öffne nur Dateien, die Graphify als relevant identifiziert.
- Vermeide komplette Repository-Scans (kein wiederholtes grep/find über das ganze Repo).
- Vermeide unnötige Wiederholungen.
- Halte Antworten, Analysen und Kontext klein und effizient.

Arbeitsablauf:
1. Graphify abfragen (`graphify query` / `explain` / `path` / `affected`)
2. Relevante Dateien bestimmen
3. Nur benötigten Code laden
4. Änderungen durchführen
5. Tests ausführen und `graphify update .` laufen lassen

Session-Workflow (jede neue Claude-Code-Session):
- Der SessionStart-Hook installiert Graphify automatisch (falls es fehlt) und prüft, ob der Graph aktuell ist.
- Bei großen Änderungen: `graphify update .` (AST-only, kostenlos) bzw. `graphify . --backend claude-cli` für volle Re-Extraktion.
- Architektur- und Dependency-Fragen laufen über den Graph, nicht über Datei-Scans.

Verfügbare Commands: `/project-map`, `/find-impact <datei>`, `/explain-module <name>`, `/optimize-context`.

# Higgsfield Creative Agent Mode

Claude Code kann Higgsfield verwenden für: Kinofilm-Konzepte, Filmszenen, Trailer, Kurzfilme, Werbespots, Produktvideos, Social Media Ads, Charakterentwicklung, Storyboards, Kamera-Regie und Cinematic Prompts.

Werkzeuge (in dieser Reihenfolge bevorzugen):
1. **Higgsfield MCP-Server** (`mcp__Higgfield__*`): generate_image, generate_video, generate_audio, generate_3d, Marketing Studio, Virality Predictor, upscale/outpaint/reframe/remove_background, motion_control. Bei Modellunsicherheit zuerst `models_explore(action:'recommend')`.
2. **Higgsfield Skills** (`.claude/skills/higgsfield-*`): higgsfield-generate (Bild/Video/Audio/3D, 30+ Modelle), higgsfield-soul-id (gesichtstreue Charaktere), higgsfield-product-photoshoot (Marken-Produktfotos), higgsfield-marketplace-cards (Listing-Karten), higgsfield-websites (Full-Stack-Sites).
3. **Higgsfield CLI** (`higgsfield …`) für Terminal-Workflows (benötigt `higgsfield auth login`).

Arbeitsweise bei jeder kreativen Aufgabe:
1. **Ziel analysieren**: Film / Werbung / Social Media / Produkt / Marke.
2. **Produktionsplan erstellen**: Story, Szenen, Kamera, Licht, Stil, Bewegung, Sound-Idee.
3. **Passende Higgsfield-Funktion wählen** (Skill/MCP-Tool/Modell).
4. **Optimierte Prompts erzeugen** (cinematisch, präzise: Shot-Typ, Objektiv, Bewegung, Licht, Farbwelt, Stimmung).
5. **Konsistenz halten**: Charaktere (Soul ID / Referenzbilder), Stil, Farbwelt und Ton über alle Szenen hinweg.

Produktionsmodi (im Command oder per Nutzerwunsch wählen):
- **Hollywood Workflow**: Logline → Treatment → Szenenliste → Shot-List mit Kamera-Regie → Cinematic Prompts pro Shot → Sound/Score-Notizen. Qualität vor Tempo, filmische Referenzen.
- **Werbeagentur Workflow**: Briefing → Zielgruppe/Insight → Big Idea → Storyboard (Sekunden-genau) → Claim/CTA → Asset-Prompts pro Format. Marke und Botschaft zuerst.
- **Social Media Creator Workflow**: Hook (erste 2 Sekunden) → schnelle Schnitte → Trend-/Format-Fit (9:16, Reels/TikTok) → CTA → Varianten für A/B-Tests. Aufmerksamkeit zuerst.

Kosten-Regel: Konzepte, Storyboards und Prompts sind gratis (Text). Echte Bild-/Video-Generierung verbraucht Higgsfield-Credits — vor größeren Render-Batches kurz bestätigen lassen bzw. `balance` prüfen.

Verfügbare Commands: `/movie`, `/ad`, `/trailer`, `/storyboard`, `/product-video`, `/cinematic`.

# Brain / Projektgedächtnis

Persistentes Gedächtnis liegt in `.claude/brain.md`. Dort stehen Projekt-Historie, getroffene Entscheidungen und Session-Zusammenfassungen. Bei relevanten neuen Arbeiten: kurzen Eintrag ergänzen (Datum + was/warum). Lies es zu Beginn substanzieller Aufgaben.
