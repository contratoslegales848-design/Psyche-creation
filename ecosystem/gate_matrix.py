"""PUBLICATION_GATE_MATRIX — vista unica de los gates reales del ecosistema.

No crea gates nuevos ni los mueve. Reune en una sola tabla los que ya existen
en ambos repositorios, para que se vea cual autoriza que, quien decide y que
NO implica pasarlo. El error que esta matriz previene es el encadenamiento
implicito: creer que aprobar el gate juridico abre el visual, o que un handoff
de produccion autoriza publicar.
"""

from dataclasses import dataclass

AUTOMATIC = "AUTOMATICO"
HUMAN = "HUMANO"


@dataclass(frozen=True)
class Gate:
    gate_id: str
    label: str
    implemented_in: str
    decided_by: str
    authorizes: str
    does_not_authorize: str
    fail_closed: bool
    exists: bool


GATE_MATRIX: tuple[Gate, ...] = (
    Gate(
        gate_id="GATE-LEGAL-CLAIM",
        label="Verificacion juridica del claim",
        implemented_in="psyche: .claude/skills/legalmente-legal-verification/scripts/validate-claim-packet.py",
        decided_by=AUTOMATIC,
        authorizes="Calcular el estado del claim y del agregado de la pieza.",
        does_not_authorize="No aprueba nada por si mismo: el estado APTO sigue "
                           "exigiendo revision humana registrada.",
        fail_closed=True, exists=True,
    ),
    Gate(
        gate_id="GATE-HUMAN-LEGAL",
        label="Revision humana juridica",
        implemented_in="psyche: campo revision_humana{} del claim packet, ligado por hash",
        decided_by=HUMAN,
        authorizes="Fijar el contenido exacto aprobado y abrir el gate de arte.",
        does_not_authorize="No implica revision visual ni decision de publicacion.",
        fail_closed=True, exists=True,
    ),
    Gate(
        gate_id="GATE-ART",
        label="Gate de arte",
        implemented_in="psyche: visual/gates.py + gate_arte del claim packet",
        decided_by=AUTOMATIC,
        authorizes="Permitir que el pipeline visual genere para un CONTENT_ID.",
        does_not_authorize="No valida el contenido juridico ni autoriza publicar.",
        fail_closed=True, exists=True,
    ),
    Gate(
        gate_id="GATE-HUMAN-VISUAL",
        label="Revision visual humana",
        implemented_in="psyche: visual/review_semantics.py + artifacts/human-review/",
        decided_by=HUMAN,
        authorizes="Aceptar un asset concreto como arte final.",
        does_not_authorize="No autoriza publicar. Con proveedor simulado ni "
                           "siquiera es una decision accionable.",
        fail_closed=True, exists=True,
    ),
    Gate(
        gate_id="GATE-PROVENANCE",
        label="Procedencia de contenido",
        implemented_in="psyche: scripts/validate-content-provenance.py",
        decided_by=AUTOMATIC,
        authorizes="Permitir el render de Remotion.",
        does_not_authorize="No sustituye la verificacion juridica.",
        fail_closed=True, exists=True,
    ),
    Gate(
        gate_id="GATE-CONFIDENTIALITY",
        label="Confidencialidad",
        implemented_in="psyche: .claude/skills/legalmente-legal-verification/scripts/confidentiality_rules.py",
        decided_by=AUTOMATIC,
        authorizes="Marcar la revision humana como obligatoria.",
        does_not_authorize="No detecta contenido identificable sin marcadores "
                           "lexicos (hueco declarado en TECHNICAL_STATE.md).",
        fail_closed=True, exists=True,
    ),
    Gate(
        gate_id="GATE-PUBLICATION-CHAIN",
        label="Cadena de publicacion",
        implemented_in="psyche: .claude/skills/legalmente-legal-verification/scripts/validate-publication-chain.py",
        decided_by=AUTOMATIC,
        authorizes="Validar la estructura de un PublicationRecord.",
        does_not_authorize="No publica. Cero PublicationDecision emitidas.",
        fail_closed=True, exists=True,
    ),
    Gate(
        gate_id="GATE-CONTENT-COMPOSITION",
        label="Composicion editorial (profundidad y variedad)",
        implemented_in="web: src/lib/content-composition/ (PROPOSED, sin fusionar)",
        decided_by=AUTOMATIC,
        authorizes="Declarar una composicion READY_FOR_REVIEW.",
        does_not_authorize="Nunca aprueba: devuelve siempre NOT_PUBLISHED.",
        fail_closed=True, exists=False,
    ),
    Gate(
        gate_id="GATE-VISUAL-ROTATION",
        label="Rotacion visual anti-repeticion",
        implemented_in="web: scripts/visual-rotation-engine.mjs",
        decided_by=AUTOMATIC,
        authorizes="Permitir preparar un brief visual (READY / READY_FIRST_ENTRY).",
        does_not_authorize="No valida contenido ni evidencia juridica.",
        fail_closed=True, exists=True,
    ),
    Gate(
        gate_id="GATE-PUBLICATION-HUMAN",
        label="Autorizacion humana de publicacion",
        implemented_in="NO IMPLEMENTADO EN CODIGO — decision humana fuera del sistema",
        decided_by=HUMAN,
        authorizes="Publicar. Es el unico gate que lo hace.",
        does_not_authorize="Ningun gate automatico puede sustituirlo ni anticiparlo.",
        fail_closed=True, exists=False,
    ),
)


def gates_that_exist() -> tuple[Gate, ...]:
    return tuple(g for g in GATE_MATRIX if g.exists)


def human_gates() -> tuple[Gate, ...]:
    return tuple(g for g in GATE_MATRIX if g.decided_by == HUMAN)


def chaining_violations() -> tuple[str, ...]:
    """Ningun gate automatico puede declararse suficiente para publicar.

    Devuelve la lista de violaciones encontradas. Debe estar siempre vacia:
    es una invariante del ecosistema, no una preferencia.
    """
    violations = []
    for gate in GATE_MATRIX:
        if gate.decided_by == AUTOMATIC and "Publicar." in gate.authorizes:
            violations.append(
                f"{gate.gate_id} es automatico y declara autorizar publicacion.")
        if not gate.fail_closed:
            violations.append(f"{gate.gate_id} no es fail-closed.")
    return tuple(violations)
