import type {
  JurisdictionLayer,
  LegalMentePiece,
  Provenance,
  ProvenanceMode,
  Taxonomia,
} from './types';

const jsonContext = require.context('../content', false, /\.json$/);

const isNonEmptyString = (value: unknown): value is string =>
  typeof value === 'string' && value.trim().length > 0;

const PROVENANCE_MODES: ProvenanceMode[] = ['GOBERNADO', 'NO_APLICA', 'EJEMPLO_TECNICO'];

const JURISDICTION_LAYERS: JurisdictionLayer[] = [
  'CAPA_A_TRANSVERSAL',
  'CAPA_B_VARIABLE',
  'CAPA_C_NACIONAL',
  'NO_APLICA',
];

const CONTENT_ID = /^[A-Z0-9][A-Z0-9-]{2,63}$/;
const SHA256_HEX = /^[0-9a-fA-F]{64}$/;

const TAXONOMIA_FIELDS: (keyof Taxonomia)[] = [
  'materia',
  'submateria',
  'concepto',
  'situacion_humana',
  'content_type',
];

/**
 * Comprueba la FORMA de la procedencia. La verificación de FONDO —que el
 * handoff exista, que la cadena valide y que los hashes correspondan al claim
 * aprobado— la hace scripts/validate-content-provenance.py en CI, que sí puede
 * leer los claim packets. Aquí se cierra la puerta a lo que ni siquiera declara
 * de dónde viene.
 *
 * Fail-closed: no hay modo por defecto. Un artefacto sin procedencia no se
 * renderiza.
 */
const validateProvenance = (value: unknown, source: string): Provenance => {
  if (!value || typeof value !== 'object') {
    throw new Error(
      `${source}: falta el objeto "procedencia". Ningún contenido se renderiza sin declarar de dónde viene.`,
    );
  }

  const p = value as Record<string, unknown>;
  const modo = p.modo as ProvenanceMode;

  if (!PROVENANCE_MODES.includes(modo)) {
    throw new Error(
      `${source}: "procedencia.modo" inválido (${String(p.modo)}); debe ser uno de ${PROVENANCE_MODES.join(', ')}.`,
    );
  }

  if (!isNonEmptyString(p.content_id) || !CONTENT_ID.test(p.content_id)) {
    throw new Error(
      `${source}: "procedencia.content_id" es obligatorio (mayúsculas, dígitos y guiones, 3-64).`,
    );
  }

  if (typeof p.publicable !== 'boolean') {
    throw new Error(`${source}: "procedencia.publicable" debe ser booleano explícito.`);
  }

  if (!JURISDICTION_LAYERS.includes(p.jurisdiction_layer as JurisdictionLayer)) {
    throw new Error(
      `${source}: "procedencia.jurisdiction_layer" inválida (${String(p.jurisdiction_layer)}).`,
    );
  }

  if (modo === 'EJEMPLO_TECNICO' && p.publicable !== false) {
    throw new Error(
      `${source}: el modo EJEMPLO_TECNICO exige "publicable": false — el material de prueba no entra en la cadena gobernada.`,
    );
  }

  if (modo !== 'EJEMPLO_TECNICO' && p.publicable !== true) {
    throw new Error(
      `${source}: el modo ${modo} describe contenido publicable; "publicable" debe ser true, o el modo correcto es EJEMPLO_TECNICO.`,
    );
  }

  if (modo === 'GOBERNADO') {
    if (!isNonEmptyString(p.handoff_id)) {
      throw new Error(`${source}: el modo GOBERNADO exige "procedencia.handoff_id".`);
    }
    if (!isNonEmptyString(p.piece_id)) {
      throw new Error(`${source}: el modo GOBERNADO exige "procedencia.piece_id".`);
    }
    if (!Array.isArray(p.claims) || p.claims.length === 0) {
      throw new Error(`${source}: el modo GOBERNADO exige "procedencia.claims" como lista no vacía.`);
    }
    p.claims.forEach((claim, index) => {
      const c = claim as Record<string, unknown>;
      if (!c || typeof c !== 'object' || !isNonEmptyString(c.claim_id)) {
        throw new Error(`${source}: "procedencia.claims[${index}].claim_id" es obligatorio.`);
      }
      if (!isNonEmptyString(c.approved_claim_hash) || !SHA256_HEX.test(c.approved_claim_hash)) {
        throw new Error(
          `${source}: "procedencia.claims[${index}].approved_claim_hash" debe ser 64 hexadecimales — liga la pieza al contenido aprobado.`,
        );
      }
    });
    if (p.jurisdiction_layer === 'NO_APLICA') {
      throw new Error(
        `${source}: una pieza GOBERNADA no puede declarar "jurisdiction_layer": "NO_APLICA"; debe declarar la capa del claim que la respalda.`,
      );
    }
  }

  if (modo === 'NO_APLICA') {
    if (!isNonEmptyString(p.motivo_no_aplica)) {
      throw new Error(
        `${source}: el modo NO_APLICA exige "procedencia.motivo_no_aplica" tipificado.`,
      );
    }
    if (!isNonEmptyString(p.justificacion_no_aplica)) {
      throw new Error(
        `${source}: el modo NO_APLICA exige "procedencia.justificacion_no_aplica".`,
      );
    }
    if (!isNonEmptyString(p.autorizado_por)) {
      throw new Error(
        `${source}: el modo NO_APLICA exige "procedencia.autorizado_por" — decidir que una pieza no lleva claim jurídico es una decisión humana con responsable.`,
      );
    }
    if (p.jurisdiction_layer !== 'NO_APLICA') {
      throw new Error(
        `${source}: el modo NO_APLICA exige "jurisdiction_layer": "NO_APLICA".`,
      );
    }
  }

  return value as Provenance;
};

const validateTaxonomia = (value: unknown, source: string): Taxonomia => {
  if (!value || typeof value !== 'object') {
    throw new Error(
      `${source}: el contenido publicable exige "taxonomia" (${TAXONOMIA_FIELDS.join(', ')}).`,
    );
  }
  const t = value as Record<string, unknown>;
  for (const field of TAXONOMIA_FIELDS) {
    if (!isNonEmptyString(t[field])) {
      throw new Error(`${source}: "taxonomia.${field}" es obligatorio.`);
    }
  }
  return value as Taxonomia;
};

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

  const procedencia = validateProvenance(piece.procedencia, source);
  if (procedencia.publicable) {
    validateTaxonomia(piece.taxonomia, source);
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

const contentIds = pieces.map(({procedencia}) => procedencia.content_id);
const duplicateContentIds = contentIds.filter((id, index) => contentIds.indexOf(id) !== index);

if (duplicateContentIds.length > 0) {
  throw new Error(
    `Content IDs duplicados: ${[...new Set(duplicateContentIds)].join(', ')} — un Content ID identifica una pieza y solo una.`,
  );
}
