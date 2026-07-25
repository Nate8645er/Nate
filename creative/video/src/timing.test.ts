import {describe, expect, it} from 'vitest';
import {TARIFFS} from './tariffs';
import {TOTAL_FRAMES, FPS} from './TariffExplainer';
import timing from '../narration/out/timing.json';

describe('Tarifdaten', () => {
  it('deckt alle 5 Tarife ab', () => {
    expect(TARIFFS).toHaveLength(5);
    expect(TARIFFS.map((t) => t.code)).toEqual([
      'free',
      'starter',
      'pro',
      'business',
      'enterprise',
    ]);
  });

  it('jeder Tarif hat Pflichtfelder', () => {
    for (const t of TARIFFS) {
      expect(t.name).toBeTruthy();
      expect(t.priceDisplay).toBeTruthy();
      expect(t.audience).toBeTruthy();
      expect(t.features.length).toBeGreaterThan(0);
    }
  });
});

describe('Timing (aus echt gemessenen Sprechdauern, narration/out/timing.json)', () => {
  it('hat fuer jede Szene (Titel + 5 Tarife + Outro) einen Timing-Eintrag', () => {
    const ids = timing.scenes.map((s) => s.id);
    expect(ids).toEqual(['title', 'free', 'starter', 'pro', 'business', 'enterprise', 'outro']);
  });

  it('Gesamtlaenge = Summe aller gemessenen Szenendauern (keine Magic Number)', () => {
    const expectedFrames = timing.scenes.reduce(
      (sum, s) => sum + Math.round(s.scene_duration_s * timing.fps),
      0
    );
    expect(TOTAL_FRAMES).toBe(expectedFrames);
    expect(FPS).toBe(timing.fps);
  });

  it('jede Szene ist mindestens so lang wie die gemessene Sprechdauer', () => {
    for (const s of timing.scenes) {
      expect(s.scene_duration_s).toBeGreaterThanOrEqual(s.speech_duration_s);
    }
  });
});
