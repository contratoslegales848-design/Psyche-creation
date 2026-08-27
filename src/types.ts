export type ProvenanceMode = 'GOBERNADO' | 'NO_APLICA' | 'EJEMPLO_TECNICO';

export type JurisdictionLayer =
  | 'CAPA_A_TRANSVERSAL'
  | 'CAPA_B_VARIABLE'
  | 'CAPA_C_NACIONAL'
  | 'NO_APLICA';

/**
 * Claim aprobado que respalda una pieza gobernada. El hash liga la pieza al
 * contenido exacto que un humano aprobó; la verificación real del hash contra
 * el claim packet la hace scripts/validate-content-provenance.py, que sí tiene
 * acceso al sistema de archivos.
 */
export type ProvenanceClaim = {
  claim_id: string;
  approved_claim_hash: string;
};

/**
 * De dónde viene una pieza. No hay modo por defecto: un artefacto sin
 * procedencia no se renderiza.
 */
export type Provenance = {
  modo: ProvenanceMode;
  content_id: string;
  publicable: boolean;
  jurisdiction_layer: JurisdictionLayer;
  /** Solo en modo GOBERNADO. */
  handoff_id?: string;
  piece_id?: string;
  claims?: ProvenanceClaim[];
  production_status?: string;
  /** Solo en modo NO_APLICA. */
  motivo_no_aplica?: string;
  justificacion_no_aplica?: string;
  autorizado_por?: string;
  fecha_autorizacion?: string;
  nota?: string;
};

/** Taxonomía editorial. Obligatoria en contenido publicable. */
export type Taxonomia = {
  materia: string;
  submateria: string;
  concepto: string;
  situacion_humana: string;
  content_type: string;
};

export type LegalMentePiece = {
  id: string;
  titulo: string;
  frase: string;
  remate: string;
  marca: string;
  imagen: string;
  audio?: string | null;
  duracionSegundos: number;
  procedencia: Provenance;
  taxonomia?: Taxonomia;
};
