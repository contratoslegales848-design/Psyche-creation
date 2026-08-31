"""Contrato versionado del Command Center. Psyche es el productor/authority
owner; legalmente-web (u otro consumidor) es SIEMPRE consumidor estricto —
nunca recalcula autoridad, nunca infiere lo que no venga en el payload.

Fail-closed: un consumidor que reciba una `contract_version` que no reconoce
debe rechazar el payload entero, no intentar leerlo parcialmente. Del mismo
modo, ningun campo usa cadenas libres que puedan crearse autoridad por
accidente ("APPROVED", "LIVE"): el vocabulario es cerrado y se declara aqui.
"""

CONTRACT_VERSION = "1.0"

# Vocabulario cerrado para el campo `data_freshness` de cada fila y del
# payload. Un consumidor jamas debe tratar SNAPSHOT o SIMULATED como LIVE.
FRESHNESS_LIVE = "LIVE"
FRESHNESS_DERIVED = "DERIVED"
FRESHNESS_SNAPSHOT = "SNAPSHOT"
FRESHNESS_SIMULATED = "SIMULATED"
FRESHNESS_UNKNOWN = "UNKNOWN"

KNOWN_VERSIONS = {CONTRACT_VERSION}


def build_envelope():
    """El sobre versionado que envuelve inventory.command_center_payload().

    No sustituye a inventory.py (que sigue siendo la fuente real): solo lo
    empaqueta con version y metadatos de sistema para un consumidor externo.
    """
    import datetime
    import inventory

    filas = inventory.command_center_payload()
    inbox = [i.to_dict() for i in inventory.build_inbox()]
    ejecutable = [r.to_dict() for r in inventory.executable_now()]
    cola_sistema = [r.to_dict() for r in inventory.system_executable_queue()]

    for f in filas:
        f["data_freshness"] = FRESHNESS_SIMULATED if f.get("provider_is_simulated") else FRESHNESS_DERIVED

    return {
        "contract_version": CONTRACT_VERSION,
        "producer": "psyche-creation/visual",
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "data_freshness": FRESHNESS_SNAPSHOT,
        "content": filas,
        "human_decision_inbox": inbox,
        "automatic_executable_now": ejecutable,
        "system_executable_queue": cola_sistema,
        "authority_note": (
            "Este payload NUNCA recalcula autoridad juridica ni visual. "
            "publicable=true no es PublicationDecision. ProductionHandoff no es "
            "PublicationDecision. human_legal_approval no es human_art_review."
        ),
    }


def validate_envelope(payload):
    """Validacion fail-closed minima para un consumidor. Devuelve lista de
    errores; lista vacia = payload aceptable de leer. No corrige nada."""
    errores = []
    if not isinstance(payload, dict):
        return ["payload no es un objeto."]
    v = payload.get("contract_version")
    if v not in KNOWN_VERSIONS:
        errores.append(f"contract_version desconocida: {v!r}. Version(es) conocida(s): {sorted(KNOWN_VERSIONS)}.")
        return errores  # fail-closed: version desconocida invalida todo lo demas.
    if not isinstance(payload.get("content"), list):
        errores.append("'content' ausente o no es una lista.")
    if not isinstance(payload.get("human_decision_inbox"), list):
        errores.append("'human_decision_inbox' ausente o no es una lista.")
    for fila in payload.get("content") or []:
        if fila.get("human_art_review") not in (
                "PENDIENTE", "SIN_GENERACION", "APPROVE_VISUAL", "REJECT_VISUAL",
                "NOT_ACTIONABLE_UNTIL_REAL_PROVIDER", "NOT_AVAILABLE", "DESCONOCIDO"):
            errores.append(f"content_id {fila.get('content_id')!r}: human_art_review con valor "
                            f"fuera del vocabulario cerrado: {fila.get('human_art_review')!r}.")
        if fila.get("human_art_review") == "APPROVE_VISUAL" and fila.get("publication_state") not in (
                "NO_PUBLICADO",):
            errores.append(f"content_id {fila.get('content_id')!r}: intento de escalada de autoridad — "
                            "visual aprobado no puede implicar publication_state distinto de NO_PUBLICADO "
                            "sin una PublicationDecision explicita.")
    return errores
