"""HELP_PROTOCOL_REGISTRY — HELP-001 a HELP-005.

El prompt de integracion §10 autoriza construir protocolos de ayuda NO
personalizados sin aprobacion previa. Estos protocolos orientan, preparan,
comparan y se detienen. No diagnostican, no resuelven un caso individual y no
enuncian reglas juridicas.

Por eso ningun protocolo lleva `EXACT_COPY` ni `CLAIM_ID`: en cuanto un texto
afirmara una regla concreta, dejaria de ser un protocolo de orientacion y
pasaria a exigir fuente, territorio y vigencia. Todos nacen PROPOSED: existen
como estructura, no como contenido publicable.

Cada protocolo declara su condicion de parada. La condicion de parada es la
parte importante: es donde el sistema deja de ayudar y empieza a hacer dano.
"""

from dataclasses import dataclass, field

PROPOSED = "PROPOSED"


@dataclass(frozen=True)
class HelpProtocol:
    protocol_id: str
    label: str
    human_question: str
    allowed_output: str
    stop_conditions: tuple[str, ...]
    related_objects: tuple[str, ...]
    owner: str = "fundador"
    state: str = PROPOSED
    territory: str = "PENDING"
    exact_copy: str = "NONE"
    claim_ids: tuple[str, ...] = ()
    next_action: str = "Revision humana antes de convertir en contenido"


HELP_PROTOCOLS: tuple[HelpProtocol, ...] = (
    HelpProtocol(
        protocol_id="HELP-001",
        label="Antes de comprar tierra",
        human_question="¿Que necesito entender antes de comprometerme con un terreno?",
        allowed_output="Mapa de dependencias entre inmueble, diligencia previa, "
                       "viabilidad, permisos, estructura y transmision.",
        stop_conditions=(
            "Se menciona un predio real, identificable o con documentos concretos.",
            "Se pide una promesa de viabilidad.",
            "Se pide un dictamen o una opinion sobre la operacion.",
        ),
        related_objects=("WEB-NAV-KNOWLEDGE-GRAPH",),
    ),
    HelpProtocol(
        protocol_id="HELP-002",
        label="De predio matriz a lote",
        human_question="¿Como se pasa conceptualmente de un predio grande a un lote individual?",
        allowed_output="Secuencia conceptual de autorizacion, protocolizacion, "
                       "individualizacion, registro y transmision, siempre "
                       "territorializada y sin plazos concretos.",
        stop_conditions=(
            "Se pide garantia de escrituracion.",
            "Se pide confirmar titularidad.",
            "Se pide una fecha de cierre.",
            "No hay territorio declarado: la secuencia varia por jurisdiccion.",
        ),
        related_objects=("WEB-NAV-KNOWLEDGE-GRAPH",),
    ),
    HelpProtocol(
        protocol_id="HELP-003",
        label="Quien debe intervenir",
        human_question="¿Que areas tienen que participar en esta operacion?",
        allowed_output="Mapa de roles entre juridico, urbanismo, ambiente, "
                       "ingenieria, fiscal, finanzas, comercial, talento y postventa.",
        stop_conditions=(
            "Se pide asignar la responsabilidad a una persona concreta.",
            "Se pide revisar documentos reales.",
            "Se pide una opinion sobre el desempeño de un area.",
        ),
        related_objects=("WEB-NAV-KNOWLEDGE-GRAPH",),
    ),
    HelpProtocol(
        protocol_id="HELP-004",
        label="Marketing, autorizacion y contrato",
        human_question="¿Lo que se anuncia coincide con lo autorizado y lo contratado?",
        allowed_output="Comparacion estructural entre las tres realidades y "
                       "señalamiento de inconsistencias como preguntas, no como "
                       "conclusiones.",
        stop_conditions=(
            "Se pide determinar la validez de una preventa.",
            "Se pide declarar un incumplimiento.",
            "Se pide fijar el derecho del comprador.",
        ),
        related_objects=("WEB-NAV-KNOWLEDGE-GRAPH", "WEB-HELP-BEFORE-SIGNING"),
    ),
    HelpProtocol(
        protocol_id="HELP-005",
        label="Cuando detenerse",
        human_question="¿Que hago cuando falta una fuente, un permiso o una version?",
        allowed_output="Activar HOLD, registrar la dependencia, nombrar al "
                       "responsable y declarar la siguiente accion.",
        stop_conditions=(
            "Se intenta rellenar el vacio con intuicion.",
            "Se intenta rellenar el vacio con experiencia no documentada.",
            "Se intenta continuar sin registrar el bloqueo.",
        ),
        related_objects=("PSY-EVID-SKILL-VERIF", "PSY-GOV-GATES"),
    ),
)


def by_id(protocol_id: str) -> HelpProtocol | None:
    for protocol in HELP_PROTOCOLS:
        if protocol.protocol_id == protocol_id:
            return protocol
    return None


def protocols_without_stop_condition() -> tuple[str, ...]:
    """Invariante: un protocolo de ayuda sin condicion de parada es un riesgo."""
    return tuple(p.protocol_id for p in HELP_PROTOCOLS if not p.stop_conditions)


def protocols_bearing_claims() -> tuple[str, ...]:
    """Invariante: ningun protocolo puede llevar claims ni copy exacto todavia."""
    return tuple(
        p.protocol_id for p in HELP_PROTOCOLS
        if p.claim_ids or p.exact_copy != "NONE"
    )
