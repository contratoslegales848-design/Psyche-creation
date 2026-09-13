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
import {
  colores,
  cuerpoPrincipal,
  cuerpoSecundario,
  cuerpoSegundoNivel,
  zonaSegura,
} from '../brandTypography';

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

  // Cuerpos de letra derivados de la política visual, no fijados a ojo.
  const cuerpoTitulo = cuerpoPrincipal(titulo);
  const cuerpoFrase = cuerpoSegundoNivel(cuerpoTitulo);

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
    <AbsoluteFill style={{backgroundColor: colores.fondo, overflow: 'hidden'}}>
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
          // Zona segura medida del feed: fuera de ella el título y el remate
          // se publicaban recortados (el feed corta ~240 px arriba y abajo).
          paddingTop: zonaSegura.top,
          paddingBottom: zonaSegura.bottom,
          paddingLeft: zonaSegura.left,
          paddingRight: zonaSegura.right,
          justifyContent: 'space-between',
          color: colores.texto,
          textShadow: '0 4px 20px rgba(0,0,0,0.8)',
          fontFamily: textFont,
        }}
      >
        <div
          style={{
            opacity: textOpacity,
            transform: `translateY(${translateY}px)`,
            maxWidth: zonaSegura.width,
          }}
        >
          <div
            style={{
              fontSize: cuerpoTitulo,
              fontWeight: 600,
              lineHeight: 1.08,
              letterSpacing: 0.3,
            }}
          >
            {titulo}
          </div>
          <div
            style={{
              marginTop: 28,
              maxWidth: zonaSegura.width,
              fontSize: cuerpoFrase,
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
            display: 'flex',
            alignItems: 'flex-end',
            justifyContent: 'space-between',
            gap: 36,
            opacity: textOpacity,
            transform: `translateY(${-translateY * 0.55}px)`,
          }}
        >
          <div
            style={{
              maxWidth: 620,
              paddingBottom: 10,
              // Mínimo legible declarado para autor / fuente / contexto.
              fontSize: cuerpoSecundario,
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
              color: colores.secundario,
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
      </AbsoluteFill>

      {audio ? <Audio src={staticFile(assetPath(audio))} /> : null}
    </AbsoluteFill>
  );
};
