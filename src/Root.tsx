import React from 'react';
import {Composition} from 'remotion';
import {LegalMenteQuote} from './compositions/LegalMenteQuote';
import {pieces} from './content';

const FPS = 30;

export const Root: React.FC = () => (
  <>
    {pieces.map((piece) => (
      <Composition
        key={piece.id}
        id={piece.id}
        component={LegalMenteQuote}
        width={1080}
        height={1920}
        fps={FPS}
        durationInFrames={Math.round(piece.duracionSegundos * FPS)}
        defaultProps={piece}
      />
    ))}
  </>
);
