import {describe, expect, it} from 'vitest';
import {TARIFFS} from './tariffs';
import {TOTAL_FRAMES, FPS} from './TariffExplainer';

describe('Timing', () => {
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

  it('Gesamtlaenge ist Titel + 5 Tarife + Outro', () => {
    // 90 (Titel) + 5*120 (Tarife) + 90 (Outro) = 780 Frames = 26s bei 30fps.
    expect(TOTAL_FRAMES).toBe(780);
    expect(FPS).toBe(30);
    expect(TOTAL_FRAMES / FPS).toBe(26);
  });
});
