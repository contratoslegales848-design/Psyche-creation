"""Inventario de estado real y bandeja de decisiones humanas.

No es un canon paralelo (docs/contrato-motor-masivo.md §1-§2): todo campo se
LEE de estructuras que ya existen (resolver.py sobre content/*.json,
pilot/claim-packets/*.json, publication/records/*.json) o del unico rastro
PERSISTENTE de revision visual que el repo conserva:
artifacts/human-review/<CONTENT_ID>/review-packet.json.

Deliberadamente NO lee el AssetRegistry (visual/registry.py): ese registro
vive hoy en directorios efimeros (ver docs/real-generation-readiness.md,
hueco conocido) y no sobrevive entre sesiones. Un inventario que dependiera
de el mentiria en cuanto ese directorio desapareciera. review-packet.json,
en cambio, se comitea: es el unico puntero al estado visual que persiste.
Si en el futuro el registro se mueve a una raiz persistente, este modulo
puede empezar a leerlo tambien — hoy no existe esa raiz, asi que no se finge.

Ausencia de dato != cero ni PASS: se representa como NOT_AVAILABLE / UNKNOWN,
nunca como una aprobacion o un exito implicitos.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path

import resolver
import review_semantics
import source_verification

HUMAN_REVIEW_DIR = resolver.REPO / "artifacts" / "human-review"

UNKNOWN = "UNKNOWN"
NOT_AVAILABLE = "NOT_AVAILABLE"

# Vocabulario cerrado de tipos de decision humana pendiente. No se inventan
# categorias nuevas aqui: cada una corresponde a un gate real ya modelado en
# gates.py / resolver.py / el esquema de ProductionHandoff.
DECISION_LEGAL_REVIEW = "LEGAL_REVIEW"
DECISION_PRODUCTION_HANDOFF = "PRODUCTION_HANDOFF"
DECISION_VISUAL_REVIEW = "VISUAL_REVIEW"
DECISION_PUBLICATION_AUTHORIZATION = "PUBLICATION_AUTHORIZATION"
DECISION_BUSINESS_COST = "BUSINESS_COST"

# Vocabulario cerrado de NEXT_EXECUTABLE_ACTION. Este motor OBSERVA y DERIVA
# — jamas abre un gate, jamas eleva autoridad.
ACTION_VERIFY_SOURCES = "VERIFY_SOURCES"
ACTION_BLOCKED_BY_SOURCE_ACCESS = "BLOCKED_BY_SOURCE_ACCESS"
ACTION_HUMAN_LEGAL_REVIEW = "HUMAN_LEGAL_REVIEW"
ACTION_EMIT_PRODUCTION_HANDOFF = "EMIT_PRODUCTION_HANDOFF"
ACTION_GENERATE_VISUAL = "GENERATE_VISUAL"
ACTION_WAIT_REAL_PROVIDER = "WAIT_REAL_PROVIDER"
ACTION_AUTOMATED_VISUAL_QA = "AUTOMATED_VISUAL_QA"
ACTION_HUMAN_VISUAL_REVIEW = "HUMAN_VISUAL_REVIEW"
ACTION_PUBLICATION_DECISION = "PUBLICATION_DECISION"
ACTION_MEASURE = "MEASURE"
ACTION_NO_ACTION = "NO_ACTION"
ACTION_BLOCKED = "BLOCKED"

OWNER_SYSTEM = "SYSTEM"
OWNER_HUMAN = "HUMAN"

# machine work != human authority (mandato de continuacion §1). VERIFY_SOURCES
# y BLOCKED_BY_SOURCE_ACCESS son trabajo/estado de SISTEMA: mientras exista
# una via legitima de ejecutarlo, la persona NO es el owner. Solo se convierte
# en HUMAN cuando la preparacion ya esta hecha (o topo con un gate real).
ACTION_OWNER = {
    ACTION_VERIFY_SOURCES: OWNER_SYSTEM,
    ACTION_BLOCKED_BY_SOURCE_ACCESS: OWNER_SYSTEM,
    ACTION_HUMAN_LEGAL_REVIEW: OWNER_HUMAN,
    ACTION_EMIT_PRODUCTION_HANDOFF: OWNER_HUMAN,
    ACTION_GENERATE_VISUAL: OWNER_SYSTEM,
    ACTION_WAIT_REAL_PROVIDER: OWNER_SYSTEM,
    ACTION_AUTOMATED_VISUAL_QA: OWNER_SYSTEM,
    ACTION_HUMAN_VISUAL_REVIEW: OWNER_HUMAN,
    ACTION_PUBLICATION_DECISION: OWNER_HUMAN,
    ACTION_MEASURE: OWNER_SYSTEM,
    ACTION_NO_ACTION: OWNER_SYSTEM,
    ACTION_BLOCKED: OWNER_SYSTEM,
}

# Acciones que el sistema puede completar SIN intervencion humana (mecanicas).
# BLOCKED_BY_SOURCE_ACCESS NO esta aqui a proposito: es SYSTEM-owned pero no
# ejecutable ahora mismo (el propio nombre lo dice) — executable_now() exige
# ademas que la accion sea realizable, no solo que no sea humana.
AUTOMATIC_ACTIONS = {ACTION_GENERATE_VISUAL, ACTION_AUTOMATED_VISUAL_QA, ACTION_MEASURE, ACTION_VERIFY_SOURCES}


def _load(p):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception:
        return None


@dataclass
class ContentReadinessRecord:
    """Estado real de una pieza, derivado — nunca inventado ni recalculado."""

    piece_id: str
    canonical_state: str = UNKNOWN
    art_gate: str = UNKNOWN
    territory: str = NOT_AVAILABLE
    content_ids: list = field(default_factory=list)
    handoff_state: str = "SIN_HANDOFF"
    latest_generation_id: str = ""
    provider_mode: str = ""
    provider_is_simulated: bool = True
    mechanical_qa: str = NOT_AVAILABLE
    copy_qa: str = NOT_AVAILABLE
    brand_composition_qa: str = NOT_AVAILABLE
    real_art_semantic_qa: str = NOT_AVAILABLE
    human_art_review: str = NOT_AVAILABLE
    publication_decision: str = "NO_EXISTE"
    publication_state: str = "NO_PUBLICADO"
    measurement_state: str = "NO_MEDIDO"
    blockers: list = field(default_factory=list)
    next_action: str = ""
    next_executable_action: str = ACTION_BLOCKED
    source_summary: object = None  # source_verification.PieceSourceSummary o None

    @property
    def owner(self):
        return ACTION_OWNER.get(self.next_executable_action, OWNER_HUMAN)

    def to_dict(self):
        return {
            "piece_id": self.piece_id,
            "owner": self.owner,
            "canonical_state": self.canonical_state,
            "art_gate": self.art_gate,
            "territory": self.territory,
            "content_ids": list(self.content_ids),
            "handoff_state": self.handoff_state,
            "latest_generation_id": self.latest_generation_id,
            "provider_mode": self.provider_mode,
            "provider_is_simulated": self.provider_is_simulated,
            "mechanical_qa": self.mechanical_qa,
            "copy_qa": self.copy_qa,
            "brand_composition_qa": self.brand_composition_qa,
            "real_art_semantic_qa": self.real_art_semantic_qa,
            "human_art_review": self.human_art_review,
            "publication_decision": self.publication_decision,
            "publication_state": self.publication_state,
            "measurement_state": self.measurement_state,
            "blockers": list(self.blockers),
            "next_action": self.next_action,
            "next_executable_action": self.next_executable_action,
        }


def _review_packet_para(content_id):
    """El puntero PERSISTENTE mas reciente para este content_id, o None.

    review-packet.json es, por convencion de materializacion humana (no
    impuesta por codigo todavia), el puntero vigente; review-packet-<gen>.json
    es el historial inmutable. Si algun dia el puntero vuelve a quedar
    desactualizado, este modulo no lo detecta por si solo — lee lo que hay.
    """
    d = HUMAN_REVIEW_DIR / content_id
    return _load(d / "review-packet.json") if d.is_dir() else None


def _next_executable_action(canonical_state, art_gate, handoff_state, clasif, source_summary=None):
    if canonical_state == "REQUIERE_INVESTIGACION":
        # SYSTEM sigue siendo owner mientras la investigacion sea legitimamente
        # ejecutable; solo se distingue de un bloqueo REAL de acceso a fuentes
        # ya intentado (mandato de continuacion §1, §26). Nunca escala a HUMAN
        # solo porque el estado se llame REQUIERE_INVESTIGACION.
        if source_summary is not None:
            estado = source_verification.next_system_action(source_summary)
            if estado == source_verification.STATUS_BLOCKED_BY_SOURCE_ACCESS:
                return ACTION_BLOCKED_BY_SOURCE_ACCESS
        return ACTION_VERIFY_SOURCES
    if art_gate != "ABIERTO":
        return ACTION_HUMAN_LEGAL_REVIEW
    if handoff_state == "SIN_HANDOFF":
        return ACTION_EMIT_PRODUCTION_HANDOFF
    if clasif.mechanical_qa == NOT_AVAILABLE and clasif.raw_human_visual_review_state == "SIN_GENERACION":
        return ACTION_GENERATE_VISUAL
    if clasif.provider_is_simulated:
        return ACTION_WAIT_REAL_PROVIDER
    if clasif.mechanical_qa == NOT_AVAILABLE:
        return ACTION_AUTOMATED_VISUAL_QA
    if clasif.human_art_review == "PENDIENTE":
        return ACTION_HUMAN_VISUAL_REVIEW
    if clasif.human_art_review == "APPROVE_VISUAL":
        return ACTION_PUBLICATION_DECISION
    return ACTION_NO_ACTION


def _next_action_para(art_gate, handoff_state, canonical_state, clasif, source_summary=None):
    if canonical_state == "REQUIERE_INVESTIGACION":
        if source_summary is not None and source_verification.next_system_action(source_summary) == \
                source_verification.STATUS_BLOCKED_BY_SOURCE_ACCESS:
            return (f"investigacion de fuentes intentada de verdad y bloqueada por acceso "
                    f"({source_summary.inaccessible_count}/{len(source_summary.checks)} fuentes inaccesibles "
                    f"via egress); sigue siendo trabajo de SISTEMA, no un gate humano.")
        return "investigacion de fuentes SISTEMA en curso: aun quedan fuentes por verificar."
    if art_gate != "ABIERTO":
        return "requiere revision juridica humana que abra el gate de arte."
    if handoff_state == "SIN_HANDOFF":
        return "requiere ProductionHandoff humano antes de poder generar."
    if clasif.provider_is_simulated:
        return ("mecanica probada con FakeImageProvider (placeholder, no arte final): "
                "bloqueado por proveedor real, no por decision humana pendiente.")
    if clasif.human_art_review in ("PENDIENTE", "SIN_GENERACION"):
        return "requiere decision de revision visual humana (APPROVE_VISUAL / REGENERATE / REJECT_VISUAL)."
    if clasif.human_art_review == "REJECT_VISUAL":
        return "requiere una nueva regeneracion o el cierre humano de la pieza."
    if clasif.human_art_review == "APPROVE_VISUAL":
        return "visual aprobado; falta PublicationDecision humana explicita — nunca automatica."
    return "sin proxima accion determinable con el estado disponible."


def build_readiness():
    """Un ContentReadinessRecord real por cada pieza del piloto. Nunca abre nada."""
    piece_id_a_content_ids = {}
    territorio_por_pieza = {}
    for cid, path, modo in resolver.list_content_ids():
        d = _load(resolver.REPO / path)
        proc = (d or {}).get("procedencia") or {}
        pid = proc.get("piece_id")
        if pid:
            piece_id_a_content_ids.setdefault(pid, []).append(cid)
            if proc.get("jurisdiction_layer"):
                territorio_por_pieza[pid] = proc["jurisdiction_layer"]

    out = []
    for p in resolver.list_pieces():
        rec = ContentReadinessRecord(
            piece_id=p["piece_id"],
            canonical_state=p["estado_agregado"],
            art_gate=p["gate_global_arte"],
            territory=territorio_por_pieza.get(p["piece_id"], NOT_AVAILABLE),
            content_ids=sorted(piece_id_a_content_ids.get(p["piece_id"], [])),
        )
        if p["estado_agregado"] == "REQUIERE_INVESTIGACION":
            rec.blockers.append("estado_agregado=REQUIERE_INVESTIGACION: sin claims aprobados aun.")
        if p["gate_global_arte"] != "ABIERTO":
            rec.blockers.append(f"gate_global_arte={p['gate_global_arte']!r}: cerrado.")

        resoluciones = [resolver.resolve(cid) for cid in rec.content_ids]
        if any(r.handoff is not None for r in resoluciones):
            rec.handoff_state = "HANDOFF_EMITIDO"
        elif rec.content_ids:
            rec.blockers.append("sin ProductionHandoff emitido todavia para ningun content_id de la pieza.")

        packet = None
        for cid in rec.content_ids:
            packet = _review_packet_para(cid)
            if packet:
                break
        clasif = review_semantics.classify(packet)
        rec.provider_is_simulated = clasif.provider_is_simulated
        rec.mechanical_qa = clasif.mechanical_qa
        rec.copy_qa = clasif.copy_qa
        rec.brand_composition_qa = clasif.brand_composition_qa
        rec.real_art_semantic_qa = clasif.real_art_semantic_qa
        rec.human_art_review = clasif.human_art_review
        if packet:
            rec.latest_generation_id = packet.get("generation_id", "")
            rec.provider_mode = packet.get("provider", "")
        elif rec.handoff_state == "HANDOFF_EMITIDO":
            rec.blockers.append("handoff emitido pero sin ninguna materializacion de revision humana encontrada.")

        source_summary = None
        if rec.canonical_state == "REQUIERE_INVESTIGACION":
            claim_packet = _load(resolver.REPO / p["path"])
            source_summary = source_verification.summarize_piece(claim_packet)
            rec.source_summary = source_summary

        rec.next_action = _next_action_para(
            rec.art_gate, rec.handoff_state, rec.canonical_state, clasif, source_summary)
        rec.next_executable_action = _next_executable_action(
            rec.canonical_state, rec.art_gate, rec.handoff_state, clasif, source_summary)
        out.append(rec)
    return out


@dataclass
class InboxItem:
    decision_type: str
    piece_id: str
    detail: str
    actor: str = "humano"

    def to_dict(self):
        return {
            "decision_type": self.decision_type,
            "piece_id": self.piece_id,
            "detail": self.detail,
            "actor": self.actor,
        }


def build_inbox(readiness=None):
    """Solo decisiones IRREDUCIBLES que de verdad necesitan una persona.

    No incluye una revision visual FakeProvider como si fuera una decision
    artistica accionable: eso es exactamente el error que este mandato pide
    evitar (mandato de continuacion §4). No junta motivos con acciones: cada
    fila es una decision real, del vocabulario cerrado DECISION_*. Vacio no
    es un caso especial: una pieza sin bloqueos simplemente no aporta filas.
    """
    readiness = readiness if readiness is not None else build_readiness()
    items = []
    for r in readiness:
        if r.canonical_state == "REQUIERE_INVESTIGACION" or r.art_gate != "ABIERTO":
            if r.owner == OWNER_SYSTEM:
                # SISTEMA sigue siendo owner (investigacion en curso o
                # bloqueada por acceso a fuentes): esto NO es una decision
                # humana todavia (mandato de continuacion §1, §2). No se
                # gasta una fila del inbox humano en trabajo de sistema.
                continue
            items.append(InboxItem(
                DECISION_LEGAL_REVIEW, r.piece_id,
                f"canon={r.canonical_state} gate={r.art_gate}: exige revision juridica humana."))
            continue  # sin gate abierto no hay ninguna otra decision real que ofrecer.
        if r.handoff_state == "SIN_HANDOFF":
            items.append(InboxItem(
                DECISION_PRODUCTION_HANDOFF, r.piece_id,
                "gate ABIERTO sin ProductionHandoff: exige decision humana de produccion."))
            continue
        if r.provider_is_simulated:
            # Deliberadamente NO es una fila de VISUAL_REVIEW: no hay arte
            # real que evaluar. La decision humana verdadera aqui es de
            # negocio/costo (activar proveedor real), no artistica.
            items.append(InboxItem(
                DECISION_BUSINESS_COST, r.piece_id,
                f"mecanica probada (FakeImageProvider) en {r.latest_generation_id or '(ninguna)'}; "
                "requiere decision de negocio para activar un proveedor real (credenciales + gasto), "
                "no una revision artistica de un placeholder."))
            continue
        if r.human_art_review in ("PENDIENTE", "SIN_GENERACION"):
            items.append(InboxItem(
                DECISION_VISUAL_REVIEW, r.piece_id,
                f"generacion {r.latest_generation_id or '(ninguna)'} con arte REAL en {r.human_art_review}: "
                "exige APPROVE_VISUAL / REGENERATE / REJECT_VISUAL."))
        if r.human_art_review == "APPROVE_VISUAL":
            items.append(InboxItem(
                DECISION_PUBLICATION_AUTHORIZATION, r.piece_id,
                "visual aprobado; no existe PublicationDecision. Nunca se fabrica aqui."))
    return items


def executable_now(readiness=None):
    """¿Que puede hacer LegalMente AHORA sin intervencion humana?

    Solo las piezas cuyo next_executable_action es mecanico (AUTOMATIC_ACTIONS).
    Este motor NUNCA abre gates: solo observa lo que YA esta autorizado a
    correr (p. ej. GENERATE_VISUAL solo aparece cuando gate+handoff ya existen).
    """
    readiness = readiness if readiness is not None else build_readiness()
    return [r for r in readiness if r.next_executable_action in AUTOMATIC_ACTIONS]


def system_executable_queue(readiness=None):
    """Todo el trabajo de SISTEMA — ejecutable ahora o bloqueado por acceso —
    separado del HUMAN_DECISION_INBOX (mandato de continuacion §25). Incluye
    piezas en BLOCKED_BY_SOURCE_ACCESS: siguen siendo trabajo de sistema, solo
    que hoy no son ejecutables (la cola no miente sobre eso, ver §26)."""
    readiness = readiness if readiness is not None else build_readiness()
    return [r for r in readiness if r.owner == OWNER_SYSTEM and
            r.next_executable_action not in (ACTION_NO_ACTION,)]


def command_center_payload():
    """Contrato de datos de solo lectura para un futuro Command Center.

    Una fila por content_id real (no por piece_id): es la granularidad que
    consume produccion visual. No recalcula autoridad — cada campo es una
    lectura directa de resolver.py / review-packet.json.
    """
    readiness_por_pieza = {r.piece_id: r for r in build_readiness()}
    filas = []
    for cid, path, modo in resolver.list_content_ids():
        r = resolver.resolve(cid)
        d = _load(resolver.REPO / path) or {}
        piece_id = (d.get("procedencia") or {}).get("piece_id", "")
        rp = readiness_por_pieza.get(piece_id)
        filas.append({
            "content_id": cid,
            "piece_id": piece_id,
            "canonical_state": rp.canonical_state if rp else UNKNOWN,
            "art_gate": rp.art_gate if rp else UNKNOWN,
            "territory": rp.territory if rp else NOT_AVAILABLE,
            "handoff_state": "HANDOFF_EMITIDO" if r.handoff is not None else "SIN_HANDOFF",
            "visual_state": "PRODUCCION_AUTORIZADA" if r.production_ready else "BLOQUEADO",
            "latest_generation_id": rp.latest_generation_id if rp else "",
            "provider_mode": rp.provider_mode if rp else "",
            "provider_is_simulated": rp.provider_is_simulated if rp else True,
            "mechanical_qa": rp.mechanical_qa if rp else NOT_AVAILABLE,
            "real_art_semantic_qa": rp.real_art_semantic_qa if rp else NOT_AVAILABLE,
            "human_art_review": rp.human_art_review if rp else NOT_AVAILABLE,
            "publication_decision": rp.publication_decision if rp else "NO_EXISTE",
            "publication_state": rp.publication_state if rp else "NO_PUBLICADO",
            "measurement_state": rp.measurement_state if rp else "NO_MEDIDO",
            "blocker": r.blocking[0] if r.blocking else "",
            "next_action": rp.next_action if rp else "",
            "next_executable_action": rp.next_executable_action if rp else ACTION_BLOCKED,
            "provenance_mode": modo,
        })
    return filas
