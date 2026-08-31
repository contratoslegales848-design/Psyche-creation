"""Puertas de entrada a la generacion visual.

Regla central (mandato §10, §16 y CLAUDE.md §3): este modulo **lee** el estado
canonico que produjo la verificacion juridica. No lo recalcula, no lo mejora y
no lo abre. Si el estado no se puede leer con certeza, cierra.

La autoridad juridica vive en
`.claude/skills/legalmente-legal-verification/` (claim packet, gate_arte,
ProductionHandoff). Aqui solo se decide si una pieza ya autorizada puede entrar
al pipeline visual.
"""

from dataclasses import dataclass, field

# Unico estado de handoff que habilita produccion visual.
HANDOFF_STATUS_PRODUCIBLE = "APROBADO_QA"

# Modos de procedencia de content/*.json (src/types.ts).
MODO_GOBERNADO = "GOBERNADO"
MODO_NO_APLICA = "NO_APLICA"
MODO_EJEMPLO_TECNICO = "EJEMPLO_TECNICO"


@dataclass
class GateDecision:
    """Resultado de una puerta. `permitido` nunca es True por omision."""

    permitido: bool = False
    motivos: list = field(default_factory=list)

    def __bool__(self):
        return self.permitido


def _cerrar(*motivos):
    return GateDecision(permitido=False, motivos=list(motivos))


def can_enter_visual_generation(procedencia, handoff=None):
    """¿Puede esta pieza entrar a generacion visual?

    `procedencia` es el bloque `procedencia` de un artefacto de content/.
    `handoff` es el ProductionHandoff ya validado por
    validate-publication-chain.py, o None si no se aporto.

    Falla cerrado ante: procedencia ausente, modo desconocido, campo canonico
    ausente, handoff ausente o handoff en un estado que no autoriza producir.
    """
    if not isinstance(procedencia, dict):
        return _cerrar("Sin bloque 'procedencia': un artefacto sin origen no entra al pipeline visual.")

    modo = procedencia.get("modo")

    if modo == MODO_EJEMPLO_TECNICO:
        return _cerrar(
            "modo EJEMPLO_TECNICO: material de prueba del pipeline, nunca material generable como pieza."
        )

    if modo == MODO_NO_APLICA:
        # NO_APLICA exige autorizacion humana explicita registrada en el artefacto.
        faltantes = [
            c for c in ("motivo_no_aplica", "autorizado_por", "fecha_autorizacion")
            if not str(procedencia.get(c) or "").strip()
        ]
        if faltantes:
            return _cerrar(
                "modo NO_APLICA sin autorizacion humana completa; faltan: " + ", ".join(faltantes)
            )
        return GateDecision(True, ["modo NO_APLICA con autorizacion humana registrada."])

    if modo != MODO_GOBERNADO:
        return _cerrar(f"modo de procedencia desconocido o ausente: {modo!r}. Estado canonico no legible -> cierra.")

    # --- modo GOBERNADO ---
    handoff_id = str(procedencia.get("handoff_id") or "").strip()
    if not handoff_id:
        return _cerrar("modo GOBERNADO sin 'handoff_id': no hay produccion autorizada que consumir.")

    claims = procedencia.get("claims")
    if not isinstance(claims, list) or not claims:
        return _cerrar("modo GOBERNADO sin claims ligados: sin hash aprobado no hay procedencia verificable.")
    for i, c in enumerate(claims):
        if not isinstance(c, dict) or not str(c.get("claim_id") or "").strip() \
                or not str(c.get("approved_claim_hash") or "").strip():
            return _cerrar(f"claim #{i} incompleto: exige 'claim_id' y 'approved_claim_hash'.")

    if handoff is None:
        return _cerrar(
            f"handoff {handoff_id!r} no aportado. El pipeline visual no infiere el estado de produccion: "
            "sin el registro no se abre."
        )
    if not isinstance(handoff, dict):
        return _cerrar("handoff con forma invalida.")

    if handoff.get("handoff_id") != handoff_id:
        return _cerrar(
            f"el handoff aportado ({handoff.get('handoff_id')!r}) no es el declarado por la pieza ({handoff_id!r})."
        )
    if handoff.get("content_id") != procedencia.get("content_id"):
        return _cerrar("content_id de la pieza y del handoff no coinciden.")

    status = handoff.get("status")
    if status != HANDOFF_STATUS_PRODUCIBLE:
        return _cerrar(
            f"handoff en status {status!r}; solo {HANDOFF_STATUS_PRODUCIBLE!r} autoriza produccion visual."
        )

    # El handoff solo existe si el validador canonico vio gate_arte ABIERTO
    # (validate-publication-chain.py §validate_handoff). No se re-deriva aqui.
    return GateDecision(True, [f"handoff {handoff_id!r} en {status}."])


def requires_human_visual_review(qa_report):
    """La revision humana visual es obligatoria SIEMPRE.

    El QA automatico puede anadir motivos, nunca puede retirarlos. No existe
    ninguna ruta por la que un asset llegue a produccion sin firma humana
    (CLAUDE.md §4, mandato §4).
    """
    motivos = ["La aprobacion visual final es siempre humana; el QA automatico no la sustituye."]
    if qa_report is not None and not qa_report.passed:
        motivos.extend(f"QA estructural fallido: {p}" for p in qa_report.problemas)
    return motivos


def can_enter_production(gate, qa_report, human_visual_approval):
    """Ultimo cierre: nada entra a produccion sin gate + QA + firma humana."""
    if not gate or not gate.permitido:
        return _cerrar("gate de entrada visual cerrado.")
    if qa_report is None or not qa_report.passed:
        return _cerrar("QA estructural no superado.")
    if human_visual_approval is not True:
        return _cerrar("falta aprobacion visual humana explicita.")
    return GateDecision(True, ["gate abierto, QA superado y aprobacion humana registrada."])
