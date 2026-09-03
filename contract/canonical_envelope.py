"""Canonical Envelope v1 — el unico contrato por el que Psyche exporta canon.

Psyche-creation es la autoridad. legalmente-web (y cualquier otro consumidor)
CONSUME, ADAPTA y PRESENTA. Nunca recalcula.

Este modulo es el lado PRODUCTOR. El consumidor no importa este codigo: importa
el esquema y las fixtures versionadas. No hay acoplamiento en tiempo de
ejecucion entre repositorios (§62).
"""

import json
import re
from dataclasses import dataclass, field, asdict

ENVELOPE_SCHEMA_VERSION = "1.0"
SUPPORTED_VERSIONS = {"1.0"}

# Estados canonicos. El consumidor los muestra; jamas los deriva ni los mejora.
CLAIM_STATES = {"APTO_PARA_NARRATIVA", "REQUIERE_INVESTIGACION", "BLOQUEADO", "PENDIENTE"}
SOURCE_STATES = {"VERIFICADA", "PENDIENTE", "INSUFICIENTE"}
LEGAL_GATE_STATES = {"ABIERTO", "CERRADO"}
# Las capas son las MISMAS que declara el validador canonico
# (.claude/skills/legalmente-legal-verification/scripts/validate-claim-packet.py,
# VALID_ALCANCE). No es una copia de cortesia: hay una prueba que compara ambos
# conjuntos y falla si divergen.
#
# 'NO_DETERMINADO' faltaba aqui, y su ausencia abria una via de blanqueo. Es el
# estado de un claim cuyo alcance todavia NO se ha establecido — exactamente el
# de las cuatro piezas que se declararon panhispanicas con fuentes de un solo
# pais. Al no caber en el sobre, la unica forma de exportarlas era reetiquetarlas
# a 'NO_APLICA', que si se aceptaba y suena inofensivo. Pero significan cosas
# opuestas: 'no sabemos que territorio cubre' frente a 'no hay territorio que
# determinar'. Convertir la primera en la segunda es perder la duda por el
# camino, que es la peor forma de perderla.
#
# Admitirla no debilita nada: 'NO_DETERMINADO' NUNCA puede viajar con el gate
# abierto ni con elegibilidad de arte, y eso se comprueba abajo.
JURISDICTION_LAYERS = {"CAPA_A_TRANSVERSAL", "CAPA_B_VARIABLE", "CAPA_C_NACIONAL",
                       "NO_DETERMINADO", "NO_APLICA"}

# Capas que, por si solas, jamas pueden acompanar a un gate abierto.
LAYERS_SIN_GATE = {"NO_DETERMINADO"}


@dataclass
class CanonicalEnvelope:
    content_id: str
    schema_version: str = ENVELOPE_SCHEMA_VERSION
    claim_state: str = "PENDIENTE"
    source_state: str = "PENDIENTE"
    legal_gate_state: str = "CERRADO"
    jurisdiction_layer: str = "NO_APLICA"
    territories: list = field(default_factory=list)
    claims: list = field(default_factory=list)      # [{claim_id, approved_claim_hash, texto_exacto}]
    provenance: dict = field(default_factory=dict)
    art_eligibility: str = "NO_ELEGIBLE"
    emitted_at: str = ""
    # --- metadatos de transporte (trazabilidad cross-repo) ---
    # Portados de la exploracion de PR #27 en legalmente-web: permiten correlacionar
    # un CONTENT_ID entre repositorios sin acoplar nada en tiempo de ejecucion.
    source_system: str = "Psyche-creation"
    source_revision: str = ""       # commit/tag del canon que emitio esto
    provenance_digest: str = ""     # sha256 sobre las referencias de procedencia

    def to_dict(self):
        return asdict(self)

    def to_json(self):
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n"


class ContractViolation(ValueError):
    """El envelope no cumple el contrato. Fail-closed: nunca se degrada a 'valido'."""


def validate_envelope(data):
    """Valida un envelope del lado CONSUMIDOR. Devuelve lista de errores.

    Esta es exactamente la funcion que legalmente-web debe reimplementar (o
    portar) en su adapter estricto. Cada regla de aqui es un test que el
    consumidor debe pasar.
    """
    e = []
    if not isinstance(data, dict):
        return ["envelope ausente o con forma invalida."]

    v = data.get("schema_version")
    if v not in SUPPORTED_VERSIONS:
        # Regla central: version desconocida NUNCA se interpreta con optimismo.
        return [f"schema_version desconocida: {v!r}. Fail-closed: no se consume."]

    if not str(data.get("content_id") or "").strip():
        e.append("falta content_id.")

    for campo, validos in (("claim_state", CLAIM_STATES), ("source_state", SOURCE_STATES),
                           ("legal_gate_state", LEGAL_GATE_STATES),
                           ("jurisdiction_layer", JURISDICTION_LAYERS)):
        if data.get(campo) not in validos:
            e.append(f"{campo} desconocido: {data.get(campo)!r} (validos: {sorted(validos)}).")

    # Un alcance sin determinar no puede llegar con el gate abierto ni con arte
    # elegible: si pudiera, admitir la capa habria sido una puerta, no un
    # registro honesto de la duda.
    if data.get("jurisdiction_layer") in LAYERS_SIN_GATE:
        if data.get("legal_gate_state") == "ABIERTO":
            e.append("jurisdiction_layer 'NO_DETERMINADO' con legal_gate_state ABIERTO: "
                     "no se puede abrir el gate de un claim cuyo territorio no se conoce.")
        if data.get("art_eligibility") not in (None, "", "NO_ELEGIBLE"):
            e.append("jurisdiction_layer 'NO_DETERMINADO' con art_eligibility "
                     f"{data.get('art_eligibility')!r}: solo cabe NO_ELEGIBLE.")

    prov = data.get("provenance")
    if not isinstance(prov, dict) or not prov.get("sources"):
        e.append("provenance ausente o sin fuentes: no se infiere procedencia valida.")

    # Transporte: si se declara un digest, debe tener forma de sha256. Un digest
    # con forma invalida es peor que ausente, porque aparenta trazabilidad.
    dig = data.get("provenance_digest")
    if dig and not re.fullmatch(r"[0-9a-fA-F]{64}", str(dig)):
        e.append(f"provenance_digest con forma invalida: se espera sha256 hex de 64 caracteres.")
    if data.get("source_system") and data["source_system"] != "Psyche-creation":
        e.append(f"source_system inesperado: {data['source_system']!r}. "
                 "El unico emisor autorizado del canon es Psyche-creation.")

    claims = data.get("claims")
    if not isinstance(claims, list) or not claims:
        e.append("envelope sin claims.")
    else:
        for i, c in enumerate(claims):
            if not isinstance(c, dict) or not c.get("claim_id") or not c.get("approved_claim_hash"):
                e.append(f"claim #{i} sin claim_id o sin approved_claim_hash.")

    # Coherencias que impiden elevar autoridad.
    if data.get("legal_gate_state") == "ABIERTO" and data.get("claim_state") != "APTO_PARA_NARRATIVA":
        e.append("incoherencia: gate ABIERTO con claim que no es APTO_PARA_NARRATIVA.")
    if data.get("art_eligibility") == "ELEGIBLE" and data.get("legal_gate_state") != "ABIERTO":
        e.append("incoherencia: elegible para arte con el gate juridico cerrado.")
    if data.get("claim_state") == "BLOQUEADO" and data.get("art_eligibility") == "ELEGIBLE":
        e.append("un claim BLOQUEADO no puede ser elegible para arte.")

    return e


def consume(data):
    """Consumo estricto: devuelve el envelope o lanza. Nunca devuelve algo a medias."""
    errores = validate_envelope(data)
    if errores:
        raise ContractViolation("; ".join(errores))
    return data


# --- lo que el consumidor NO puede hacer, en forma ejecutable ---

WEB_MAY = ("display", "adapt_presentation", "filter_safely", "prepare_ux")
WEB_MUST_NOT = (
    "approve_claim", "recompute_sources", "upgrade_jurisdiction",
    "open_legal_gate", "change_canonical_hash", "infer_missing_provenance_as_valid",
)
