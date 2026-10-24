# Ghost Protocol: Neon Maze — Design Plan

## Experience formula
The player feels like a lone signal escaping a hostile machine, because the game
constantly hunts them through neon mazes while feeding them fragments of the truth.

## Profile
- Time: real-time · Space: continuous 2D top-down over a maze grid · Agency: one hero (Neo)
- Conflict: vs system (4 AI hunters, 6 bosses) · Content: authored (6 chapters, 18 maps)
- Outcome: win/lose, 3 endings (DELETE / SAVE / MERGE) · Players: solo
- Engagement: story + execution (primary), discovery (secondary)
- Delivery: desktop + mobile browsers + gamepad; languages DE (default) + EN, all strings external
- Performance: 60 fps fixed-timestep, DPR cap 1.5, static maze layer pre-rendered, pooled particles

## Verbs & teaching sequence (one pattern per chapter, exam = boss)
1. **Ch1 The Arcade** — move + dash → exam: The Guardian
2. **Ch2 The Forgotten Network** — hack (terminals, doors, turrets) → The Hacker
3. **Ch3 Neon Factory** — EMP + energy shield → The Queen
4. **Ch4 Virus Garden** — cloak + magnet → Virus Leviathan
5. **Ch5 Core Memory** — slow-time + teleport → Omega Core
6. **Ch6 The Architect** — combined exam of everything → The Architect + ending choice

## Systems
- Hunters: Blaze (aggressive chaser), Phantom (ambusher/teleporter), Widow (patroller, mines),
  Glitch (erratic feints). State machine: patrol → search → chase → flee (EMP/cloak);
  group behavior via shared last-known-position; "learning": counters the player's most-used ability.
- Economy: energy (regen; sink: abilities), XP (source: fragments/enemies; sink: skill tree),
  data keys (open doors). Fragments raise local alert level (negative feedback on hoarding).
- Story: state variables (fragments read, NPCs helped, hunters spared) gate dialogue and the
  ending epilogue lines; hero goal = player goal (escape → understand → decide).
- Saves: localStorage, 3 slots + autosave at checkpoints/chapter starts, JSON.
- Quests: main quest per chapter + optional side quests from NPCs; rewards: XP, lore, energy cells.
- Achievements: local, toast popups.
- Accessibility: remappable keys (physical codes), text scale, shake/flash toggles, CRT toggle.

## STYLE FORMULA (approved — explicit in brief)
chunky HD pixel art rendering with glowing neon bloom, sharp geometric silhouettes with thin
luminous outlines, environment in deep midnight-blue and violet circuit-board tones with charcoal
shadows, hero in radiant cyan-white that pops against the surroundings, hunters and hazards in hot
magenta and crimson glow, memory fragments and pickups in bright golden-amber light, dark synthwave
cyberpunk atmosphere with volumetric neon haze, high contrast between game elements and
backgrounds, clean readable silhouettes, consistent top-down perspective across all assets

## Reference route (smoke)
New game → intro → Ch1 maze 1 → collect fragments → checkpoint → maze 2 → Guardian →
skill point → Ch2 … → Ch6 Architect → choose ending → credits.
