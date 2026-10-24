# Numeric thresholds (fixed before build)

- Frame budget: 16.6 ms (60 fps) on a mid phone; DPR cap 1.5.
- Simulation: fixed timestep 1000/60 ms, seeded RNG (mulberry32), logic/visual RNG split.
- Entities per scene: ≤ 300 active; particles pooled, cap 400, zero per-frame allocations in loop.
- Static maze layer: pre-rendered once per level to offscreen canvas (1 draw per frame).
- Input tolerance: dash buffer 120 ms, checkpoint invulnerability 1200 ms,
  player hitbox 60% of sprite, laser telegraph ≥ 600 ms before damage.
- Asset bounds: zip ≤ 25 MiB per asset; images 1k; music 40s/30s loops; 5 SFX.
- Audio mix targets: SFX −10 dBFS, music −18 dBFS, true-peak ≤ −3 dBFS (gain-staged in WebAudio).
