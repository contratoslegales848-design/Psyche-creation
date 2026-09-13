/**
 * Parámetros tipográficos y de paleta del render de video.
 *
 * No se declara aquí ni un solo número de marca: todos se leen de
 * `visual/policy/legalmente-visual-policy-v1.json`, que es la política visual
 * ejecutable y que a su vez transcribe la skill `legalmente-visual-system`
 * (§3 núcleo de marca, §6 tipografía). Antes el render de video llevaba su
 * propia paleta (`#F4EBD8`, `#E6C879`, `#100d0b`), sus propios cuerpos de letra
 * (62 / 44 / 25 px) y su propio margen (130 px arriba, 90 abajo), y ninguno
 * coincidía con lo aprobado: el título caía dentro de la franja que el feed
 * recorta y el remate quedaba por debajo del mínimo legible.
 *
 * Si la política cambia, esto cambia con ella sin tocar código.
 */
import policy from '../visual/policy/legalmente-visual-policy-v1.json';

const LIENZO = {width: 1080, height: 1920};

type Escalon = {max_caracteres: number; px_min: number; px_max: number};

const tipografia = policy.tipografia;
const paleta = policy.paleta.requerida;
const escalones: Escalon[] = tipografia.escalones_principal;

/** Zona segura medida del feed (la skill mide el recorte solo en 9:16). */
export const zonaSegura = (() => {
  const z = tipografia.zona_segura_declarada.VERTICAL_9_16;
  return {
    top: z.y,
    left: z.x,
    right: LIENZO.width - z.x2,
    bottom: LIENZO.height - z.y2,
    width: z.x2 - z.x,
    height: z.y2 - z.y,
  };
})();

export const colores = {
  /** Cuerpo principal: marfil editorial. */
  texto: paleta.marfil_editorial[0],
  /** Autor, fuente, contexto y marca: latón viejo. */
  secundario: paleta.laton_oro_viejo[0],
  /** Fondo bajo la imagen: nogal profundo, el tono más oscuro. */
  fondo: paleta.nogal_profundo[1],
};

/**
 * Cuerpo del bloque principal (el que se reconoce en menos de dos segundos)
 * según su longitud, dentro del escalón aprobado. Fuera de tabla se aplica el
 * mínimo aprobado más bajo y la pieza queda marcada por
 * `visual/cli.py audit-art`: el render no decide por su cuenta encoger el texto
 * hasta hacerlo ilegible.
 */
export const cuerpoPrincipal = (texto: string): number => {
  const n = texto.length;
  let previo = 0;
  for (const e of escalones) {
    if (n <= e.max_caracteres) {
      const t = (n - previo) / Math.max(1, e.max_caracteres - previo);
      return Math.round(e.px_max - t * (e.px_max - e.px_min));
    }
    previo = e.max_caracteres;
  }
  return escalones[escalones.length - 1].px_min;
};

/**
 * Segundo nivel: la skill exige que no compita con el principal pero no le
 * asigna tabla propia. Se conserva la proporción del diseño ya en uso (0,71)
 * y se pone como suelo el máximo del nivel secundario, para que nunca caiga a
 * tamaño de pie de foto.
 */
export const cuerpoSegundoNivel = (principal: number): number =>
  Math.max(tipografia.secundario.px_max, Math.round(principal * 0.71));

/** Autor, fuente y contexto: mínimo declarado, nunca menos. */
export const cuerpoSecundario = tipografia.secundario.px_min;

export const maxLineas = tipografia.max_lineas;
