import type {LegalMentePiece} from './types';

const jsonContext = require.context('../content', false, /\.json$/);

const isNonEmptyString = (value: unknown): value is string =>
  typeof value === 'string' && value.trim().length > 0;

const validatePiece = (value: unknown, source: string): LegalMentePiece => {
  if (!value || typeof value !== 'object') {
    throw new Error(`${source}: el JSON debe contener un objeto.`);
  }

  const piece = value as Record<string, unknown>;
  const requiredText = ['id', 'titulo', 'frase', 'remate', 'marca', 'imagen'] as const;

  for (const field of requiredText) {
    if (!isNonEmptyString(piece[field])) {
      throw new Error(`${source}: el campo "${field}" es obligatorio.`);
    }
  }

  if (
    typeof piece.duracionSegundos !== 'number' ||
    !Number.isFinite(piece.duracionSegundos) ||
    piece.duracionSegundos < 8 ||
    piece.duracionSegundos > 15
  ) {
    throw new Error(`${source}: "duracionSegundos" debe estar entre 8 y 15.`);
  }

  if (piece.audio !== null && piece.audio !== undefined && !isNonEmptyString(piece.audio)) {
    throw new Error(`${source}: "audio" debe ser una ruta válida, null u omitirse.`);
  }

  // Regla de redacción del manual de marca (docs/legalmente-marca-y-estilo.md, §1.3):
  // por encima de 18 palabras la tipografía se comprime y la pieza pierde jerarquía.
  const fraseWordCount = (piece.frase as string).trim().split(/\s+/).length;
  if (fraseWordCount > 18) {
    throw new Error(
      `${source}: "frase" tiene ${fraseWordCount} palabras; el máximo de marca es 18.`,
    );
  }

  return piece as LegalMentePiece;
};

export const pieces = jsonContext
  .keys()
  .sort()
  .map((key) => {
    const imported = jsonContext(key) as {default?: unknown} | unknown;
    const value =
      imported && typeof imported === 'object' && 'default' in imported
        ? imported.default
        : imported;
    return validatePiece(value, key);
  });

const ids = pieces.map(({id}) => id);
const duplicateIds = ids.filter((id, index) => ids.indexOf(id) !== index);

if (duplicateIds.length > 0) {
  throw new Error(`IDs de composición duplicados: ${[...new Set(duplicateIds)].join(', ')}`);
}
