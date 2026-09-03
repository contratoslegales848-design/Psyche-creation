"""RELATIONSHIP_MAP del ecosistema.

No construye un grafo paralelo. `visual/topology.py` ya modela los enlaces
internos del organismo (canon -> resolver -> pipeline -> proveedor), las etapas
del content factory y la cadena publicacion/medicion/aprendizaje. Este modulo
lo CONSUME y anade unicamente la capa que ese grafo no cubre: los enlaces
entre repositorios, entre capas del modelo unificado y hacia los paquetes que
el prompt de integracion nombra pero que no tienen artefacto.

Vocabulario reutilizado de topology.py, deliberadamente: si un enlace esta
DISCONNECTED alli, aqui no puede aparecer como CONNECTED.
"""

import sys
from pathlib import Path

from . import registry

REPO = Path(__file__).resolve().parent.parent
_VISUAL = REPO / "visual"

CONNECTED = "CONNECTED"
READY_TO_CONNECT = "READY_TO_CONNECT"
BLOCKED = "BLOCKED"
DISCONNECTED = "DISCONNECTED"
MISSING = "MISSING"

RELATION_STATES = frozenset({CONNECTED, READY_TO_CONNECT, BLOCKED, DISCONNECTED, MISSING})


def _link(source: str, target: str, state: str, reason: str) -> dict:
    return {"source": source, "target": target, "state": state, "reason": reason}


def inherited_topology() -> list[dict]:
    """Enlaces que ya modela visual/topology.py, leidos en vivo.

    Si el modulo no se puede importar, se declara explicitamente en lugar de
    devolver una lista vacia que pareceria "sin problemas".
    """
    if str(_VISUAL) not in sys.path:
        sys.path.insert(0, str(_VISUAL))
    try:
        import topology  # noqa: PLC0415  (import tardio deliberado)
    except ImportError as exc:  # pragma: no cover - defensivo
        return [_link("ecosystem_relations", "visual_topology", BLOCKED,
                      f"no se pudo importar visual/topology.py: {exc}")]

    links: list[dict] = []
    links.extend(topology.build_topology())
    links.extend(topology.publication_measurement_learning_topology())
    links.extend(topology.content_factory_topology())
    return links


def ecosystem_links() -> list[dict]:
    """Enlaces de nivel ecosistema. Cada estado se deriva del registro real."""
    def state_of(object_id: str) -> str:
        obj = registry.by_id(object_id)
        return obj.resolve_state() if obj else registry.MISSING_ARTIFACT

    links: list[dict] = []

    # --- Hueco 2: entrada humana (web) <-> evidencia (psyche) --------------
    grafo = state_of("WEB-NAV-KNOWLEDGE-GRAPH")
    links.append(_link(
        "WEB-NAV-KNOWLEDGE-GRAPH", "PSY-EVID-SKILL-VERIF", DISCONNECTED,
        "El grafo de mundos y conceptos vive en legalmente-web; los claim "
        "packets viven en psyche-creation. No existe ningun objeto que ligue "
        f"un CONCEPT con un CLAIM_ID. Estado del grafo: {grafo}. "
        "Es el hueco de integracion mas importante del ecosistema."))

    # --- Contrato cross-repo ------------------------------------------------
    links.append(_link(
        "PSY-PROD-CONTRACT", "WEB-PROD-CONSUMER", READY_TO_CONNECT,
        "Canonical Envelope v1 implementado y probado en ambos lados; el "
        "consumidor se entrego como serie de patches en handoff/legalmente-web/. "
        "Falta una sesion con permiso de escritura sobre legallmente-alt."))

    links.append(_link(
        "PSY-PROD-CONTRACT", "WEB-KNOW-COMPOSITION", DISCONNECTED,
        "El contrato de composicion se construyo contra el grafo de web, no "
        "contra el Canonical Envelope. Unirlos exige que antes exista una "
        "composicion que alcance READY_FOR_REVIEW con copy exacto real."))

    # --- Gates: nunca encadenados -------------------------------------------
    links.append(_link(
        "PSY-EVID-SKILL-VERIF", "PSY-GOV-GATES", CONNECTED,
        "El gate de arte se calcula desde el claim packet validado y queda "
        "ligado por hash al contenido aprobado."))

    links.append(_link(
        "PSY-GOV-GATES", "publication_decision", DISCONNECTED,
        "Deliberado y verificado en topology.py: ningun handoff de produccion "
        "abre ni implica una decision de publicacion."))

    # --- Ayuda: solo un protocolo real --------------------------------------
    links.append(_link(
        "WEB-NAV-KNOWLEDGE-GRAPH", "WEB-HELP-BEFORE-SIGNING", CONNECTED,
        "Unica ruta de ayuda implementada y con prueba de privacidad propia."))

    links.append(_link(
        "WEB-NAV-KNOWLEDGE-GRAPH", "HELP-001..005", MISSING,
        "Los cinco protocolos de ayuda que el prompt de integracion describe "
        "no existen en ningun repositorio. Registrados en help_protocols.py "
        "como PROPOSED, sin copy normativo."))

    # --- Paquetes nombrados sin artefacto -----------------------------------
    for obj in registry.ALL_OBJECTS:
        if obj.declared_state != registry.MISSING_ARTIFACT:
            continue
        links.append(_link(
            "ecosystem", obj.object_id, MISSING,
            f"{obj.label}: {obj.notes}"))

    # --- Distribucion --------------------------------------------------------
    links.append(_link(
        "MIS-LINKEDIN-BANK", "distribution_linkedin", MISSING,
        "Sin banco editorial no hay puente que construir: el registro de "
        "temas propuestos queda vacio a proposito, no relleno con inferencias."))

    return links


def full_map() -> list[dict]:
    return inherited_topology() + ecosystem_links()


def integration_gaps() -> list[dict]:
    """Los enlaces que hoy impiden que el ecosistema se lea como uno solo."""
    return [link for link in full_map() if link["state"] in (DISCONNECTED, MISSING, BLOCKED)]
