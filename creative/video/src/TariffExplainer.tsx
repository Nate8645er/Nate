import React from 'react';
import {
  AbsoluteFill,
  Sequence,
  useCurrentFrame,
  interpolate,
  spring,
  useVideoConfig,
} from 'remotion';
import {BRAND, TARIFFS, VAT_NOTE, Tariff} from './tariffs';
import {COLORS, FONT} from './theme';

const FPS = 30;
const TITLE_FRAMES = 90; // 3s
const TARIFF_FRAMES = 120; // 4s pro Tarif
const OUTRO_FRAMES = 90; // 3s

function fadeInOut(frame: number, durationInFrames: number, fps: number): number {
  const inOp = interpolate(frame, [0, fps * 0.4], [0, 1], {extrapolateRight: 'clamp'});
  const outOp = interpolate(
    frame,
    [durationInFrames - fps * 0.4, durationInFrames],
    [1, 0],
    {extrapolateLeft: 'clamp'}
  );
  return Math.min(inOp, outOp);
}

const Title: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const opacity = fadeInOut(frame, TITLE_FRAMES, fps);
  const scale = spring({frame, fps, config: {damping: 200}});

  return (
    <AbsoluteFill
      style={{
        backgroundColor: COLORS.bg,
        justifyContent: 'center',
        alignItems: 'center',
        opacity,
      }}
    >
      <div style={{transform: `scale(${scale})`, textAlign: 'center'}}>
        <div style={{color: COLORS.muted, fontFamily: FONT, fontSize: 28, letterSpacing: 6}}>
          {BRAND.toUpperCase()}
        </div>
        <div style={{color: COLORS.text, fontFamily: FONT, fontSize: 64, fontWeight: 700, marginTop: 16}}>
          Tarife im Überblick
        </div>
        <div style={{color: COLORS.muted, fontFamily: FONT, fontSize: 26, marginTop: 12}}>
          {VAT_NOTE}
        </div>
      </div>
    </AbsoluteFill>
  );
};

const TariffScene: React.FC<{tariff: Tariff}> = ({tariff}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const opacity = fadeInOut(frame, TARIFF_FRAMES, fps);
  const slideIn = spring({frame, fps, config: {damping: 200}});
  const translateX = interpolate(slideIn, [0, 1], [40, 0]);

  return (
    <AbsoluteFill style={{backgroundColor: COLORS.bg, opacity}}>
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 12,
          backgroundColor: COLORS.accent,
        }}
      />
      <div
        style={{
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          padding: '0 120px',
          transform: `translateX(${translateX}px)`,
        }}
      >
        <div style={{color: COLORS.muted, fontFamily: FONT, fontSize: 24, letterSpacing: 4}}>
          {tariff.audience.toUpperCase()}
        </div>
        <div style={{color: COLORS.text, fontFamily: FONT, fontSize: 84, fontWeight: 700, marginTop: 8}}>
          {tariff.name}
        </div>
        <div style={{color: COLORS.accent, fontFamily: FONT, fontSize: 40, fontWeight: 700, marginTop: 12}}>
          {tariff.priceDisplay}
        </div>
        <div style={{marginTop: 40, display: 'flex', flexDirection: 'column', gap: 18}}>
          {tariff.features.map((f, i) => (
            <FeatureRow key={f} text={f} index={i} />
          ))}
        </div>
      </div>
    </AbsoluteFill>
  );
};

const FeatureRow: React.FC<{text: string; index: number}> = ({text, index}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const delay = fps * 0.5 + index * fps * 0.25;
  const local = Math.max(0, frame - delay);
  const opacity = interpolate(local, [0, fps * 0.3], [0, 1], {extrapolateRight: 'clamp'});

  return (
    <div style={{display: 'flex', alignItems: 'center', gap: 16, opacity}}>
      <div
        style={{
          width: 14,
          height: 14,
          borderRadius: 999,
          backgroundColor: COLORS.accent,
          flexShrink: 0,
        }}
      />
      <div style={{color: COLORS.text, fontFamily: FONT, fontSize: 34}}>{text}</div>
    </div>
  );
};

const Outro: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const opacity = fadeInOut(frame, OUTRO_FRAMES, fps);

  return (
    <AbsoluteFill
      style={{
        backgroundColor: COLORS.bg,
        justifyContent: 'center',
        alignItems: 'center',
        opacity,
      }}
    >
      <div style={{textAlign: 'center'}}>
        <div style={{color: COLORS.text, fontFamily: FONT, fontSize: 48, fontWeight: 700}}>
          Tarif wählen und starten
        </div>
        <div style={{color: COLORS.muted, fontFamily: FONT, fontSize: 26, marginTop: 14}}>
          {VAT_NOTE} · jederzeit kündbar
        </div>
      </div>
    </AbsoluteFill>
  );
};

export const TariffExplainer: React.FC = () => {
  let cursor = 0;
  const titleFrom = cursor;
  cursor += TITLE_FRAMES;

  const tariffRanges = TARIFFS.map((t) => {
    const from = cursor;
    cursor += TARIFF_FRAMES;
    return {tariff: t, from};
  });

  const outroFrom = cursor;

  return (
    <AbsoluteFill style={{backgroundColor: COLORS.bg}}>
      <Sequence from={titleFrom} durationInFrames={TITLE_FRAMES}>
        <Title />
      </Sequence>
      {tariffRanges.map(({tariff, from}) => (
        <Sequence key={tariff.code} from={from} durationInFrames={TARIFF_FRAMES}>
          <TariffScene tariff={tariff} />
        </Sequence>
      ))}
      <Sequence from={outroFrom} durationInFrames={OUTRO_FRAMES}>
        <Outro />
      </Sequence>
    </AbsoluteFill>
  );
};

export const TOTAL_FRAMES = TITLE_FRAMES + TARIFFS.length * TARIFF_FRAMES + OUTRO_FRAMES;
export {FPS};
