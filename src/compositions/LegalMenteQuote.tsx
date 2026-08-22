import React from 'react';
import '@fontsource/eb-garamond/400.css';
import '@fontsource/eb-garamond/400-italic.css';
import '@fontsource/eb-garamond/600.css';
import '@fontsource/unifrakturcook/700.css';
import {
  AbsoluteFill,
  Audio,
  Img,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import type {LegalMentePiece} from '../types';

const textFont = 'EB Garamond';

// Las fuentes están autoalojadas en el bundle para evitar dependencias de red.
// UnifrakturCook aporta el carácter gótico; Georgia queda como fallback seguro.
const wordmarkFont = 'UnifrakturCook';

const assetPath = (path: string) => path.replace(/^\/?assets\//, '');

export const LegalMenteQuote: React.FC<LegalMentePiece> = ({
  titulo,
  frase,
  remate,
  marca,
  imagen,
  audio,
}) => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();

  const entrance = interpolate(frame, [0.5 * fps, 1.5 * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const exit = interpolate(
    frame,
    [durationInFrames - 0.6 * fps, durationInFrames],
    [1, 0],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'},
  );
  const textOpacity = entrance * exit;
  const translateY = interpolate(entrance, [0, 1], [34, 0]);
  const imageScale = interpolate(frame, [0, durationInFrames], [1.02, 1.075], {
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{backgroundColor: '#100d0b', overflow: 'hidden'}}>
      <Img
        src={staticFile(assetPath(imagen))}
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          transform: `scale(${imageScale})`,
        }}
      />

      <AbsoluteFill
        style={{
          background:
            'linear-gradient(180deg, rgba(5,8,14,0.34) 0%, rgba(5,8,14,0.04) 38%, rgba(5,8,14,0.08) 63%, rgba(5,8,14,0.56) 100%)',
        }}
      />

      <AbsoluteFill
        style={{
          padding: '130px 78px 90px',
          justifyContent: 'space-between',
          color: '#F4EBD8',
          fontFamily: textFont,
          textShadow: '0 4px 20px rgba(0,0,0,0.8)',
        }}
      >
        <div
          style={{
            opacity: textOpacity,
            transform: `translateY(${translateY}px)`,
            maxWidth: 900,
          }}
        >
          <div
            style={{
              fontSize: 62,
              fontWeight: 600,
              lineHeight: 1.08,
              letterSpacing: 0.8,
              fontVariant: 'small-caps',
            }}
          >
            {titulo}
          </div>
          <div
            style={{
              marginTop: 28,
              maxWidth: 820,
              fontSize: 44,
              fontWeight: 400,
              fontStyle: 'italic',
              lineHeight: 1.18,
            }}
          >
            {frase}
          </div>
        </div>

        <div
          style={{
            opacity: textOpacity,
            transform: `translateY(${-translateY * 0.55}px)`,
          }}
        >
          {/* Regla epigráfica: remite a la línea tallada de una inscripción romana. */}
          <div
            style={{
              height: 1,
              marginBottom: 22,
              background:
                'linear-gradient(90deg, rgba(230,200,121,0) 0%, rgba(230,200,121,0.55) 50%, rgba(230,200,121,0) 100%)',
            }}
          />
          <div
            style={{
              display: 'flex',
              alignItems: 'flex-end',
              justifyContent: 'space-between',
              gap: 36,
            }}
          >
            <div
              style={{
                maxWidth: 620,
                paddingBottom: 10,
                fontSize: 25,
                fontWeight: 600,
                letterSpacing: 5.5,
                lineHeight: 1.3,
                textTransform: 'uppercase',
              }}
            >
              {remate}
            </div>
            <div
              style={{
                color: '#E6C879',
                fontFamily: `${wordmarkFont}, Georgia, serif`,
                fontSize: 50,
                fontWeight: 700,
                lineHeight: 1,
                whiteSpace: 'nowrap',
              }}
            >
              {marca}
            </div>
          </div>
        </div>
      </AbsoluteFill>

      {audio ? <Audio src={staticFile(assetPath(audio))} /> : null}
    </AbsoluteFill>
  );
};
