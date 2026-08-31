"""Topologia del organismo: que esta unido, y con que estado, sin graph DB.

Vocabulario cerrado (mandato de continuacion §13). Cada entrada es una
afirmacion sobre un enlace real del sistema, verificada en el momento de
construir la lista — no una promesa estatica escrita a mano y olvidada.
"""

import os

CONNECTED = "CONNECTED"
READY_TO_CONNECT = "READY_TO_CONNECT"
BLOCKED = "BLOCKED"
DISCONNECTED = "DISCONNECTED"
EXPERIMENTAL = "EXPERIMENTAL"
SUPERSEDED = "SUPERSEDED"


def _link(source, target, state, reason):
    return {"source": source, "target": target, "state": state, "reason": reason}


def build_topology():
    import provider_preflight
    import resolver

    links = []

    # Psyche canon -> visual resolver: siempre CONNECTED, es lectura directa.
    ids = resolver.list_content_ids()
    links.append(_link(
        "psyche_canon", "visual_resolver", CONNECTED,
        f"resolver.list_content_ids() lee {len(ids)} content_id(s) reales del canon."))

    # CONTENT_ID -> ProductionHandoff -> visual pipeline: CONNECTED solo si
    # al menos una pieza real llega a production_ready; si no, DISCONNECTED
    # (existe el codigo, pero nada real lo atraviesa todavia).
    alguna_lista = any(resolver.resolve(cid).production_ready for cid, _, m in ids if m == "GOBERNADO")
    links.append(_link(
        "content_id", "visual_pipeline",
        CONNECTED if alguna_lista else DISCONNECTED,
        "al menos un content_id GOBERNADO resuelve production_ready=True."
        if alguna_lista else "ningun content_id real llega hoy a production_ready."))

    # visual pipeline -> proveedor real de imagen: siempre depende del preflight real.
    pf = provider_preflight.preflight()
    estado_proveedor = CONNECTED if pf.status == provider_preflight.READY else BLOCKED
    links.append(_link(
        "visual_pipeline", "real_image_provider", estado_proveedor,
        f"provider_preflight.preflight() -> {pf.status}: {pf.blocking_reason or 'listo.'}"))

    # FakeImageProvider: nunca productivo, siempre EXPERIMENTAL/SIMULATION.
    links.append(_link(
        "visual_pipeline", "fake_image_provider", EXPERIMENTAL,
        "FakeImageProvider es para pruebas mecanicas de CI; nunca se presenta como arte final."))

    # Psyche -> legalmente-web consumidor estricto.
    handoff_dir_existe = os.path.isdir(str(resolver.REPO / "handoff" / "legalmente-web"))
    links.append(_link(
        "psyche_command_center_contract", "legalmente_web_consumer", READY_TO_CONNECT,
        "contrato preparado en handoff/legalmente-web/ (ver NEXT_SESSION_PROMPT.md); "
        "sin sesion con permiso de escritura sobre ese repo en este momento."
        if handoff_dir_existe else "no existe todavia paquete de handoff."))

    # Human legal approval -> human visual approval: nunca el mismo gate.
    links.append(_link(
        "human_legal_approval", "human_visual_review", DISCONNECTED,
        "deliberado: una aprobacion juridica nunca implica ni sustituye una revision visual humana."))

    # ProductionHandoff -> PublicationDecision: nunca automatico.
    links.append(_link(
        "production_handoff", "publication_decision", DISCONNECTED,
        "deliberado: ningun ProductionHandoff abre ni implica una PublicationDecision."))

    return links
