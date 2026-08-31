"""VisualInputAdapter — vista del canon, no segundo canon.

Psyche conserva la autoridad. Este adapter LEE las estructuras canonicas ya
existentes (procedencia de content/*.json + ProductionHandoff de la cadena
post-aprobacion), NORMALIZA su forma para el pipeline visual y PRESERVA la
autoridad tal cual.

Nunca: recalcula canon, eleva autoridad, altera hashes, infiere procedencia
ausente como valida.

No se crea ningun ContentUnit paralelo: docs/contrato-motor-masivo.md §1-§2 ya
repartio esos campos entre estructuras existentes.
"""

from dataclasses import dataclass, field

import gates
from errors import VisualInputInvalidError

SUPPORTED_PROVENANCE_MODES = {gates.MODO_GOBERNADO, gates.MODO_NO_APLICA, gates.MODO_EJEMPLO_TECNICO}
SUPPORTED_CONTENT_SCHEMA = {"1.0", None}   # None: artefactos previos al campo


@dataclass(frozen=True)
class VisualInput:
    """Forma normalizada que consume el pipeline visual. Solo referencias al canon."""

    content_id: str
    provenance_mode: str
    jurisdiction_layer: str
    publicable: bool
    handoff_ref: str = ""
    piece_id: str = ""
    claim_refs: tuple = ()          # ((claim_id, approved_claim_hash), ...)
    content_type: str = ""
    series: str = ""
    exact_copy: str = ""
    author: str = ""
    territory: str = ""
    art_gate_state: str = "DESCONOCIDO"     # leido, jamas derivado aqui
    raw_provenance: dict = field(default_factory=dict)

    @property
    def content_hash(self):
        """Hash canonico del primer claim aprobado. No se recalcula: se transporta."""
        return self.claim_refs[0][1] if self.claim_refs else ""


def build_visual_input(artefacto, handoff=None):
    """Construye un VisualInput desde un artefacto de content/ ya validado.

    Fail-closed en todos los casos del mandato §3. Lanza VisualInputInvalidError.
    """
    if not isinstance(artefacto, dict):
        raise VisualInputInvalidError("artefacto de contenido ausente o con forma invalida.")

    proc = artefacto.get("procedencia")
    if not isinstance(proc, dict):
        raise VisualInputInvalidError("falta 'procedencia': no se infiere procedencia ausente como valida.")

    esquema = artefacto.get("schema_version")
    if esquema not in SUPPORTED_CONTENT_SCHEMA:
        raise VisualInputInvalidError(
            f"schema_version de contenido no soportada: {esquema!r}. Version desconocida -> se rechaza."
        )

    content_id = str(proc.get("content_id") or "").strip()
    if not content_id:
        raise VisualInputInvalidError("falta content_id.")

    modo = proc.get("modo")
    if modo not in SUPPORTED_PROVENANCE_MODES:
        raise VisualInputInvalidError(f"modo de procedencia desconocido: {modo!r}.")

    claim_refs = []
    for c in (proc.get("claims") or []):
        if not isinstance(c, dict):
            raise VisualInputInvalidError("claim con forma invalida en procedencia.")
        cid, h = str(c.get("claim_id") or "").strip(), str(c.get("approved_claim_hash") or "").strip()
        if not cid or not h:
            raise VisualInputInvalidError("claim sin 'claim_id' o sin 'approved_claim_hash'.")
        claim_refs.append((cid, h))

    if modo == gates.MODO_GOBERNADO:
        if not claim_refs:
            raise VisualInputInvalidError("modo GOBERNADO sin claims: procedencia requerida ausente.")
        if handoff is not None:
            if handoff.get("content_id") != content_id:
                raise VisualInputInvalidError(
                    f"el handoff pertenece a otro CONTENT_ID ({handoff.get('content_id')!r} != {content_id!r})."
                )
            hh = handoff.get("content_hash")
            if hh and claim_refs and hh != claim_refs[0][1]:
                raise VisualInputInvalidError("content hash mismatch entre handoff y claim aprobado.")

    # El estado del gate se LEE del handoff. Sin handoff, permanece DESCONOCIDO
    # (y el gate lo tratara como cerrado). Nunca se deriva aqui.
    art_gate = "DESCONOCIDO"
    if isinstance(handoff, dict) and handoff.get("status"):
        art_gate = str(handoff["status"])

    tax = artefacto.get("taxonomia") or {}
    return VisualInput(
        content_id=content_id,
        provenance_mode=modo,
        jurisdiction_layer=str(proc.get("jurisdiction_layer") or "NO_APLICA"),
        publicable=bool(proc.get("publicable")),
        handoff_ref=str(proc.get("handoff_id") or ""),
        piece_id=str(proc.get("piece_id") or ""),
        claim_refs=tuple(claim_refs),
        content_type=str(tax.get("content_type") or ""),
        series=str(tax.get("materia") or ""),
        exact_copy=str(artefacto.get("frase") or ""),
        author=str(artefacto.get("remate") or ""),
        territory=str(proc.get("jurisdiction_layer") or ""),
        art_gate_state=art_gate,
        raw_provenance=proc,
    )
