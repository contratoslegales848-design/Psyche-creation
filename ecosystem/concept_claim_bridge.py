"""CONCEPT → CLAIM_ID — contrato de relación entre navegación y evidencia.

Es el hueco de integración prioritario: los conceptos y mundos viven en
`legalmente-web`, los claim packets en `psyche-creation`, y hasta ahora ningún
objeto los ligaba. Sin ese puente no se puede recorrer

    pregunta humana → concepto → claim → fuente → territorio → límite →
    ayuda permitida → estado → owner → siguiente acción

sin saltar de repositorio a mano.

Lo que este módulo NO es: no es un knowledge graph nuevo, no redefine
`content_id`, `claim_id`, la taxonomía ni el Canonical Envelope. Sólo declara
relaciones entre identificadores que ya existen, y las valida contra los claim
packets reales del disco.

Fail-closed: una relación sin evidencia suficiente nunca queda `VERIFIED_BINDING`.
Los estados de ausencia son `PENDING_BINDING`, `REVIEW_REQUIRED` y `ACCESS_GAP`,
nunca una aprobación. Reversible: basta borrar este archivo.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PACKETS_DIR = REPO / ".claude" / "skills" / "legalmente-legal-verification" / "pilot" / "claim-packets"

# --- Estados del vínculo ---------------------------------------------------
PENDING_BINDING = "PENDING_BINDING"
REVIEW_REQUIRED = "REVIEW_REQUIRED"
ACCESS_GAP = "ACCESS_GAP"
VERIFIED_BINDING = "VERIFIED_BINDING"
REJECTED = "REJECTED"

BINDING_STATES = frozenset({
    PENDING_BINDING, REVIEW_REQUIRED, ACCESS_GAP, VERIFIED_BINDING, REJECTED,
})

# --- Capas jurisdiccionales, tomadas del esquema real de los packets -------
CAPA_A = "CAPA_A_TRANSVERSAL"
CAPA_B = "CAPA_B_VARIABLE"
CAPA_C = "CAPA_C_NACIONAL"

# Relaciones de identidad, para que dos objetos que representan el mismo
# contenido no puedan coexistir como canónicos independientes.
ALIAS_OF = "ALIAS_OF"
DERIVED_FROM = "DERIVED_FROM"


@dataclass(frozen=True)
class ConceptClaimBinding:
    """Una relación declarada entre un concepto de navegación y un claim.

    Cada campo separa deliberadamente una dimensión distinta: confundirlas es
    lo que produce que un claim nacional viaje como si fuera panhispánico.
    """

    binding_id: str
    # Navegación (vive en legalmente-web)
    concept_id: str
    concept_label: str
    human_question: str
    # Evidencia (vive en psyche-creation)
    claim_id: str
    packet_file: str
    # Alcance jurídico — declarado por el vínculo, contrastado con el packet
    declared_layer: str
    territories: tuple[str, ...]
    source_ids: tuple[str, ...]
    limits: tuple[str, ...]
    # Gobernanza
    owner: str
    next_action: str
    blocker: str = "NONE"
    # Identidad: si este objeto representa contenido ya existente en otro sitio
    identity_relation: str = "NONE"   # ALIAS_OF | DERIVED_FROM | NONE
    identity_target: str = "NONE"
    # Publicación: nunca se deriva, siempre se declara
    publication_state: str = "NOT_PUBLISHED"


@dataclass
class BindingDecision:
    binding_id: str
    state: str
    reasons: list[str] = field(default_factory=list)
    packet_layer: str | None = None
    packet_claim_state: str | None = None
    publication_state: str = "NOT_PUBLISHED"


def _load_packet(packet_file: str) -> dict | None:
    path = PACKETS_DIR / packet_file
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def available_claim_ids() -> dict[str, dict]:
    """Todos los claims realmente presentes en el disco, por claim_id.

    Se lee el canon, no se replica: si un packet cambia, esto cambia con él.
    """
    catalogo: dict[str, dict] = {}
    if not PACKETS_DIR.is_dir():
        return catalogo
    for path in sorted(PACKETS_DIR.glob("*.json")):
        try:
            packet = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        for claim in packet.get("claims", []):
            claim_id = claim.get("claim_id")
            if claim_id:
                catalogo[claim_id] = {"claim": claim, "packet_file": path.name}
    return catalogo


def evaluate_binding(binding: ConceptClaimBinding,
                     catalogo: dict[str, dict] | None = None) -> BindingDecision:
    """Evalúa una relación contra el canon real. Fail-closed.

    Nunca devuelve VERIFIED_BINDING por plausibilidad: exige que el claim
    exista, que su alcance coincida, que tenga fuentes y límites, y que una
    persona lo haya aprobado.
    """
    catalogo = catalogo if catalogo is not None else available_claim_ids()
    decision = BindingDecision(binding_id=binding.binding_id, state=PENDING_BINDING)

    # --- Identidad: nada canónico duplicado sin declararlo -----------------
    if binding.identity_relation not in ("NONE", ALIAS_OF, DERIVED_FROM):
        decision.state = REJECTED
        decision.reasons.append(
            f"Relación de identidad desconocida: {binding.identity_relation}.")
        return decision
    if binding.identity_relation != "NONE" and binding.identity_target == "NONE":
        decision.state = REJECTED
        decision.reasons.append(
            f"{binding.identity_relation} exige nombrar el objeto de origen.")
        return decision

    # --- Campos de gobernanza obligatorios ---------------------------------
    if not binding.concept_id.strip():
        decision.state = REJECTED
        decision.reasons.append("CONCEPT_ID ausente.")
    if not binding.claim_id.strip():
        decision.state = REJECTED
        decision.reasons.append("CLAIM_ID ausente.")
    if not binding.owner.strip():
        decision.state = REJECTED
        decision.reasons.append("Owner ausente: ninguna relación queda sin responsable.")
    if not binding.next_action.strip():
        decision.state = REJECTED
        decision.reasons.append("Siguiente acción ausente.")
    if binding.publication_state != "NOT_PUBLISHED":
        decision.state = REJECTED
        decision.reasons.append(
            f"Estado de publicación '{binding.publication_state}': una relación "
            "jamás abre publicación.")
    if decision.state == REJECTED:
        return decision

    # --- El claim tiene que existir de verdad ------------------------------
    entrada = catalogo.get(binding.claim_id)
    if entrada is None:
        decision.state = PENDING_BINDING
        decision.reasons.append(
            f"El claim '{binding.claim_id}' no existe en el canon local "
            f"({PACKETS_DIR.name}/). El vínculo queda pendiente, no aprobado.")
        return decision

    claim = entrada["claim"]
    if entrada["packet_file"] != binding.packet_file:
        decision.state = REVIEW_REQUIRED
        decision.reasons.append(
            f"El claim vive en '{entrada['packet_file']}' y el vínculo declara "
            f"'{binding.packet_file}'.")

    decision.packet_layer = claim.get("alcance")
    decision.packet_claim_state = claim.get("estado")

    # --- Falsa universalización: el error jurídico más caro ----------------
    if binding.declared_layer != decision.packet_layer:
        decision.state = REJECTED
        decision.reasons.append(
            f"El vínculo declara alcance {binding.declared_layer} y el claim "
            f"real es {decision.packet_layer}. Presentar un claim nacional como "
            "transversal es falsa universalización.")
        return decision

    # --- Un claim nacional exige territorio explícito ----------------------
    if binding.declared_layer == CAPA_C and not binding.territories:
        decision.state = REJECTED
        decision.reasons.append(
            "Un claim de Capa C es necesariamente nacional y exige territorio.")
        return decision

    # --- Fuentes y límites --------------------------------------------------
    fuentes_packet = {f.get("id") for f in claim.get("fuentes", [])}
    if not binding.source_ids:
        decision.state = REVIEW_REQUIRED
        decision.reasons.append("El vínculo no declara ninguna fuente.")
    else:
        huerfanas = [s for s in binding.source_ids if s not in fuentes_packet]
        if huerfanas:
            decision.state = REJECTED
            decision.reasons.append(
                f"Fuentes ausentes del claim real: {', '.join(huerfanas)}.")
            return decision

    if not binding.limits:
        decision.state = REVIEW_REQUIRED
        decision.reasons.append("Sin límites explícitos declarados.")

    # --- Estado de verificación del claim ----------------------------------
    estado = claim.get("estado")
    revision = claim.get("revision_humana", {}) or {}
    aprobado_por_humano = revision.get("estado") == "APROBADO"

    if estado == "REQUIERE_INVESTIGACION":
        decision.state = ACCESS_GAP
        decision.reasons.append(
            "El claim sigue en REQUIERE_INVESTIGACION: falta evidencia de fuente, "
            "no una decisión.")
        return decision

    if estado == "APTO_CON_MATICES":
        decision.state = REVIEW_REQUIRED
        decision.reasons.append(
            "APTO_CON_MATICES no basta para un vínculo verificado: una persona "
            "debe decidir si lo investigado alcanza.")
        return decision

    if estado == "APTO_PARA_NARRATIVA" and aprobado_por_humano:
        if decision.state == PENDING_BINDING:
            decision.state = VERIFIED_BINDING
            decision.reasons.append(
                "Claim apto y aprobado por una persona; fuentes y límites presentes.")
        return decision

    decision.state = REVIEW_REQUIRED
    decision.reasons.append(
        f"Estado '{estado}' sin aprobación humana registrada: no se verifica el vínculo.")
    return decision


# --- Relaciones declaradas hoy ---------------------------------------------
# Ninguna se inventa: los concept_id son los de las rutas reales de
# legalmente-web (src/lib/knowledge-graph/model.ts) y los claim_id los de los
# packets reales. Todas nacen sin verificar, porque ninguna cumple todavía las
# condiciones para estarlo — que es exactamente el estado del proyecto.

DECLARED_BINDINGS: tuple[ConceptClaimBinding, ...] = (
    ConceptClaimBinding(
        binding_id="BND-001",
        concept_id="enterprise-commerce",
        concept_label="Empresa y comercio",
        human_question="¿Cuándo existe una relación de trabajo aunque no haya contrato escrito?",
        claim_id="pieza-04-claim-1",
        packet_file="pieza-04-laboral-basico.json",
        declared_layer=CAPA_A,
        territories=("México", "Argentina", "Colombia", "España"),
        source_ids=("SRC-P04-MX-LFT-20", "SRC-P04-AR-LCT-21-22",
                    "SRC-P04-CO-CST-22-23", "SRC-P04-ES-ET-01"),
        limits=("No se declara universal panhispánico completo: sólo 4 países revisados.",),
        owner="fundador",
        next_action="Rebasar esta rama sobre main para que el packet sea legible",
        blocker="ECO-BLK-STALE-BRANCH",
    ),
    ConceptClaimBinding(
        binding_id="BND-002",
        concept_id="everyday-life",
        concept_label="Vida cotidiana",
        human_question="¿Qué distingue propiedad, posesión y tenencia?",
        claim_id="pieza-01-claim-1",
        packet_file="pieza-01-reales.json",
        declared_layer=CAPA_B,
        territories=("México", "España", "Argentina"),
        source_ids=("SRC-P01-MX-FED-02", "SRC-P01-ES-CC-01", "SRC-P01-AR-CCYC-02"),
        limits=("Capa B: misma lógica, pero el detalle varía por país; no se "
                "presenta como regla común sin nombrar la jurisdicción.",),
        owner="fundador",
        next_action="NONE — vínculo verificado; siguiente paso es asignar ayuda permitida",
    ),
    ConceptClaimBinding(
        binding_id="BND-003",
        concept_id="enterprise-commerce",
        concept_label="Empresa y comercio",
        human_question="¿Qué diferencia hay entre despido y renuncia?",
        claim_id="pieza-02-claim-1",
        packet_file="pieza-02-laboral.json",
        declared_layer=CAPA_C,
        territories=("México",),
        source_ids=(),
        limits=("Varía por país; no se presenta como regla común.",),
        owner="fundador",
        next_action="Obtener los PDFs oficiales en HOLD",
        blocker="ECO-BLK-SOURCES-HOLD",
    ),
)


def evaluate_all() -> list[BindingDecision]:
    catalogo = available_claim_ids()
    return [evaluate_binding(b, catalogo) for b in DECLARED_BINDINGS]


def verified_bindings() -> list[BindingDecision]:
    return [d for d in evaluate_all() if d.state == VERIFIED_BINDING]


def traversable_route(binding_id: str) -> dict | None:
    """La ruta completa que el criterio de finalización exige poder recorrer.

    Devuelve cada eslabón con su estado real; nunca oculta un eslabón vacío.
    """
    binding = next((b for b in DECLARED_BINDINGS if b.binding_id == binding_id), None)
    if binding is None:
        return None
    decision = evaluate_binding(binding)
    return {
        "pregunta_humana": binding.human_question,
        "concepto": f"{binding.concept_id} ({binding.concept_label})",
        "claim": binding.claim_id,
        "fuentes": list(binding.source_ids) or ["PENDING_BINDING"],
        "territorio": list(binding.territories) or ["NO_DECLARADO"],
        "limites": list(binding.limits) or ["PENDING_BINDING"],
        "ayuda_permitida": "HELP-005 (cuándo detenerse)" if decision.state != VERIFIED_BINDING
                           else "pendiente de asignar",
        "estado": decision.state,
        "owner": binding.owner,
        "siguiente_accion": binding.next_action,
        "publicacion": decision.publication_state,
    }
