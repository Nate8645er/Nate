import {registerRoot, Composition} from 'remotion';
import React from 'react';
import {TariffExplainer, TOTAL_FRAMES, FPS} from './TariffExplainer';

const Root: React.FC = () => {
  return (
    <Composition
      id="TariffExplainer"
      component={TariffExplainer}
      durationInFrames={TOTAL_FRAMES}
      fps={FPS}
      width={1920}
      height={1080}
    />
  );
};

registerRoot(Root);
