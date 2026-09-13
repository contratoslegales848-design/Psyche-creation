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
  comillas,
  cuerpoPrincipal,
  cuerpoSecundario,
  cuerpoSegundoNivel,
  filete,
  tracking,
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
          // Sin sombra de texto: se midió sobre el fotograma real y no aportaba
          // nada al contraste (variantes B y C idénticas hasta el tercer
          // decimal). Una muleta que no sostiene nada solo ensucia el trazo.
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
              letterSpacing: `${tracking.display}em`,
            }}
          >
            {titulo}
          </div>
          {filete.visible && frase ? (
            <div
              style={{
                marginTop: Math.round(cuerpoTitulo * filete.aireEm * 0.5),
                width: filete.ancho,
                height: filete.grosorPx,
                backgroundColor: colores.secundario,
                opacity: 0.92,
              }}
            />
          ) : null}

          <div
            style={{
              position: 'relative',
              marginTop: Math.round(cuerpoTitulo * filete.aireEm * 0.5),
              maxWidth: zonaSegura.width,
              fontSize: cuerpoFrase,
              fontWeight: 400,
              fontStyle: 'italic',
              lineHeight: 1.18,
            }}
          >
            {comillas.usar ? (
              <span
                style={{
                  // Cuelga en el margen óptico: el texto conserva toda su medida
                  // y la primera línea arranca alineada con las demás.
                  position: 'absolute',
                  left: -Math.round(cuerpoFrase * comillas.escala * 0.62),
                  top: 0,
                  fontSize: Math.round(cuerpoFrase * comillas.escala),
                  fontStyle: 'normal',
                  color: colores.secundario,
                  opacity: comillas.opacidad,
                }}
              >
                {comillas.apertura}
              </span>
            ) : null}
            {frase}
            {comillas.usar ? (
              <span
                style={{
                  fontSize: Math.round(cuerpoFrase * comillas.escala),
                  fontStyle: 'normal',
                  color: colores.secundario,
                  opacity: comillas.opacidad,
                }}
              >
                {'\u2009'}
                {comillas.cierre}
              </span>
            ) : null}
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
              letterSpacing: `${tracking.versalitas}em`,
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
