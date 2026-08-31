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


def publication_measurement_learning_topology():
    """Publication chain, medicion y aprendizaje — mapeados, no publicados
    (mandato de continuacion §30-32). Verificado contra el codigo real de
    validate-publication-chain.py y visual/memory.py, no contra descripcion."""
    return [
        _link("production_handoff", "publication_record_schema", "PARTIAL",
              "validate-publication-chain.py define el esquema completo de PublicationRecord "
              "(metrics, available_metrics, window_days) y lo valida — pero existe UN solo "
              "registro real en publication/records/ (el ProductionHandoff de PIEZA-01); "
              "cero PublicationDecision o PublicationRecord con metricas jamas emitidos."),
        _link("publication_record_schema", "measurement", "NO_MEDIDO",
              "el esquema de metricas existe y se valida (metrics/available_metrics coherentes "
              "entre si), pero no hay ningun dato real: NO_MEDIDO, no 0 ni ausencia silenciosa."),
        _link("measurement", "content_factory_learning_loop", DISCONNECTED,
              "no existe ningun codigo que conecte metricas de publicacion con la seleccion de "
              "temas, el content factory o VisualMemory. VisualMemory (visual/memory.py) SI "
              "aprende, pero solo de generaciones aceptadas (anti-repeticion visual) — nunca de "
              "rendimiento real de publicacion, porque nunca hubo una publicacion real."),
    ]


# Vocabulario propio de las etapas del Content Factory (mandato de
# continuacion §19) — deliberadamente DISTINTO del vocabulario organismo-wide
# de arriba: aqui se pregunta "que tan hecho esta este mecanismo", no "esta
# conectado este enlace".
CF_CONNECTED = "CONNECTED"
CF_PARTIAL = "PARTIAL"
CF_DOCUMENTED_ONLY = "DOCUMENTED_ONLY"
CF_DISCONNECTED = "DISCONNECTED"
CF_MISSING = "MISSING"


def content_factory_topology():
    """Etapas reales del 'nacimiento' de una pieza (idea -> CONTENT_ID ->
    ProductionHandoff), clasificadas por lo que EXISTE hoy en el repo — no lo
    que Drive describe. Investigado (mandato de continuacion §19), no
    construido: no se crea ninguna 'fabrica' nueva, solo se lee lo real."""
    return [
        _link("idea", "claim_draft", CF_DOCUMENTED_ONLY,
              "no existe automatizacion de intake: un humano/agente redacta el claim packet "
              "a mano, sin ningun candidate_id ni estructura de captura previa."),
        _link("claim_draft", "source_discovery", CF_CONNECTED,
              "pilot/claim-packets/*.json ya declara fuentes por claim con el esquema real "
              "(tipo_fuente, url, localizador) — WORKING, es la estructura que este propio "
              "modulo (source_verification.py) lee."),
        _link("source_discovery", "source_verification", CF_CONNECTED,
              "verificacion_fuente{origen_oficial_confirmado, texto_exacto_consultado, "
              "vigencia_comprobada, metodo_o_evidencia} existe y se pobla realmente "
              "(ver pieza-02/03) — WORKING, aunque hoy BLOCKED_BY_SOURCE_ACCESS en esta sesion."),
        _link("source_verification", "territory_mapping", CF_CONNECTED,
              "jurisdicciones_cubiertas por fuente + jurisdiction_layer por claim: WORKING, "
              "ya presente en los claim packets reales."),
        _link("territory_mapping", "human_legal_review", CF_PARTIAL,
              "revision_humana{estado, revisor, fecha, contenido_hash_sha256} existe y se "
              "usa de verdad (PIEZA-01) pero no hay ningun mecanismo que declare "
              "automaticamente 'evidencia suficiente para revision' — sigue exigiendo lectura "
              "humana o de un agente explicito de las proposiciones, claim por claim."),
        _link("human_legal_review", "content_id", CF_CONNECTED,
              "resolver.py + content/*.json: WORKING, demostrado con LM-PIEZA-01-REALES."),
        _link("content_id", "production_handoff", CF_CONNECTED,
              "validate-publication-chain.py + gates.py: WORKING, demostrado con "
              "HO-PIEZA-01-REALES-001."),
    ]
