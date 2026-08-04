import React from 'react';
import {
  AbsoluteFill,
  Composition,
  interpolate,
  random,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import guion from '../guion-actual.json';

type Tono = 'azul-oro' | 'burdeos-oro' | 'pergamino';

type Guion = {
  titulo: string;
  cita: string;
  autor: string;
  duracionSegundos: number;
  tono: Tono;
  palabrasClave: string[];
  marca: string;
};

type Paleta = {
  fondo: string;
  secundario: string;
  acento: string;
  texto: string;
};

const paletas: Record<Tono, Paleta> = {
  'azul-oro': {
    fondo: '#071426',
    secundario: '#17345D',
    acento: '#D6AD52',
    texto: '#F8F2E4',
  },
  'burdeos-oro': {
    fondo: '#260B15',
    secundario: '#641E30',
    acento: '#E0B85A',
    texto: '#FFF6E6',
  },
  pergamino: {
    fondo: '#3A2A1D',
    secundario: '#8A6845',
    acento: '#E7C77A',
    texto: '#FFF8E8',
  },
};

const escaparRegExp = (texto: string) =>
  texto.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

const TextoResaltado: React.FC<{
  texto: string;
  palabras: string[];
  color: string;
}> = ({texto, palabras, color}) => {
  const palabrasValidas = palabras.map((p) => p.trim()).filter(Boolean);

  if (palabrasValidas.length === 0) return <>{texto}</>;

  const expresion = new RegExp(
    `(${palabrasValidas.map(escaparRegExp).join('|')})`,
    'gi',
  );

  return (
    <>
      {texto.split(expresion).map((parte, index) => {
        const resaltada = palabrasValidas.some(
          (palabra) => palabra.toLocaleLowerCase('es') === parte.toLocaleLowerCase('es'),
        );

        return (
          <span
            key={`${index}-${parte}`}
            style={
              resaltada
                ? {
                    color,
                    fontWeight: 700,
                    textShadow: `0 0 20px ${color}66`,
                  }
                : undefined
            }
          >
            {parte}
          </span>
        );
      })}
    </>
  );
};

const Particulas: React.FC<{color: string}> = ({color}) => {
  const frame = useCurrentFrame();

  return (
    <>
      {Array.from({length: 28}, (_, index) => {
        const x = random(`x-${index}`) * 1080;
        const yInicial = random(`y-${index}`) * 1920;
        const tamano = 2 + random(`size-${index}`) * 5;
        const velocidad = 0.25 + random(`speed-${index}`);
        const posicion = (yInicial - frame * velocidad) % 1920;
        const y = posicion < 0 ? posicion + 1920 : posicion;

        return (
          <div
            key={index}
            style={{
              position: 'absolute',
              left: x,
              top: y,
              width: tamano,
              height: tamano,
              borderRadius: '50%',
              backgroundColor: color,
              opacity: 0.18,
              boxShadow: `0 0 12px ${color}`,
            }}
          />
        );
      })}
    </>
  );
};

const LegalMenteVideo: React.FC<Guion> = ({
  titulo,
  cita,
  autor,
  tono,
  palabrasClave,
  marca,
}) => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const colores = paletas[tono];

  const entrada = spring({
    frame,
    fps,
    config: {damping: 18, stiffness: 90, mass: 0.8},
  });
  const salida = interpolate(
    frame,
    [Math.max(0, durationInFrames - 20), durationInFrames],
    [1, 0],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'},
  );
  const desplazamiento = interpolate(entrada, [0, 1], [70, 0]);
  const escala = interpolate(entrada, [0, 1], [0.94, 1]);

  return (
    <AbsoluteFill
      style={{
        overflow: 'hidden',
        color: colores.texto,
        background: `radial-gradient(circle at 50% 35%, ${colores.secundario}, transparent 55%), linear-gradient(160deg, ${colores.fondo}, #03060C)`,
        fontFamily: 'Georgia, "Times New Roman", serif',
      }}
    >
      <Particulas color={colores.acento} />
      <AbsoluteFill
        style={{
          padding: '150px 85px 110px',
          justifyContent: 'space-between',
          textAlign: 'center',
          opacity: salida,
        }}
      >
        <header style={{opacity: entrada, transform: `translateY(${desplazamiento}px)`}}>
          <div
            style={{
              marginBottom: 28,
              color: colores.acento,
              fontSize: 30,
              fontWeight: 600,
              letterSpacing: 12,
            }}
          >
            LEGALMENTE
          </div>
          <h1
            style={{
              margin: 0,
              fontSize: 70,
              lineHeight: 1.08,
              textTransform: 'uppercase',
              textShadow: '0 8px 24px rgba(0,0,0,0.4)',
            }}
          >
            {titulo}
          </h1>
        </header>

        <main
          style={{
            padding: '60px 45px',
            borderTop: `2px solid ${colores.acento}`,
            borderBottom: `2px solid ${colores.acento}`,
            backgroundColor: 'rgba(0,0,0,0.16)',
            opacity: entrada,
            transform: `scale(${escala})`,
          }}
        >
          <div
            style={{
              fontSize: 53,
              fontStyle: 'italic',
              lineHeight: 1.38,
              textShadow: '0 5px 18px rgba(0,0,0,0.45)',
            }}
          >
            “<TextoResaltado texto={cita} palabras={palabrasClave} color={colores.acento} />”
          </div>
          <div
            style={{
              marginTop: 45,
              color: colores.acento,
              fontSize: 38,
              fontWeight: 700,
              letterSpacing: 3,
            }}
          >
            — {autor}
          </div>
        </main>

        <footer
          style={{
            color: colores.acento,
            fontSize: 32,
            fontWeight: 600,
            letterSpacing: 4,
          }}
        >
          {marca}
        </footer>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

const datos = guion as Guion;
const duracionSegundos = Number.isFinite(datos.duracionSegundos)
  ? Math.max(1, datos.duracionSegundos)
  : 10;

export const Root: React.FC = () => (
  <Composition
    id="LegalMenteQuote"
    component={LegalMenteVideo}
    width={1080}
    height={1920}
    fps={30}
    durationInFrames={Math.round(duracionSegundos * 30)}
    defaultProps={datos}
  />
);
