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
"""

import json
from dataclasses import dataclass, field
from pathlib import Path

import resolver

HUMAN_REVIEW_DIR = resolver.REPO / "artifacts" / "human-review"

# Vocabulario cerrado de tipos de decision humana pendiente. No se inventan
# categorias nuevas aqui: cada una corresponde a un gate real ya modelado en
# gates.py / resolver.py / el esquema de ProductionHandoff.
DECISION_LEGAL_REVIEW = "LEGAL_REVIEW"
DECISION_PRODUCTION_HANDOFF = "PRODUCTION_HANDOFF"
DECISION_VISUAL_REVIEW = "VISUAL_REVIEW"
DECISION_PUBLICATION_AUTHORIZATION = "PUBLICATION_AUTHORIZATION"


def _load(p):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception:
        return None


@dataclass
class ContentReadinessRecord:
    """Estado real de una pieza, derivado — nunca inventado ni recalculado."""

    piece_id: str
    canonical_state: str = "DESCONOCIDO"
    art_gate: str = "DESCONOCIDO"
    content_ids: list = field(default_factory=list)
    handoff_state: str = "SIN_HANDOFF"
    latest_generation_id: str = ""
    human_visual_review_state: str = "SIN_GENERACION"
    provider_mode: str = ""
    blockers: list = field(default_factory=list)
    next_action: str = ""

    def to_dict(self):
        return {
            "piece_id": self.piece_id,
            "canonical_state": self.canonical_state,
            "art_gate": self.art_gate,
            "content_ids": list(self.content_ids),
            "handoff_state": self.handoff_state,
            "latest_generation_id": self.latest_generation_id,
            "human_visual_review_state": self.human_visual_review_state,
            "provider_mode": self.provider_mode,
            "blockers": list(self.blockers),
            "next_action": self.next_action,
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


def _next_action_para(art_gate, handoff_state, review_state, canonical_state):
    if canonical_state == "REQUIERE_INVESTIGACION":
        return "requiere investigacion juridica humana antes de reabrir el gate de arte."
    if art_gate != "ABIERTO":
        return "requiere revision juridica humana que abra el gate de arte."
    if handoff_state == "SIN_HANDOFF":
        return "requiere ProductionHandoff humano antes de poder generar."
    if review_state in ("PENDIENTE", "SIN_GENERACION"):
        return "requiere decision de revision visual humana (APPROVE_VISUAL / REGENERATE / REJECT_VISUAL)."
    if review_state == "REJECT_VISUAL":
        return "requiere una nueva regeneracion o el cierre humano de la pieza."
    if review_state == "APPROVE_VISUAL":
        return "visual aprobado; falta PublicationDecision humana explicita — nunca automatica."
    return "sin proxima accion determinable con el estado disponible."


def build_readiness():
    """Un ContentReadinessRecord real por cada pieza del piloto. Nunca abre nada."""
    piece_id_a_content_ids = {}
    for cid, path, modo in resolver.list_content_ids():
        d = _load(resolver.REPO / path)
        pid = ((d or {}).get("procedencia") or {}).get("piece_id")
        if pid:
            piece_id_a_content_ids.setdefault(pid, []).append(cid)

    out = []
    for p in resolver.list_pieces():
        rec = ContentReadinessRecord(
            piece_id=p["piece_id"],
            canonical_state=p["estado_agregado"],
            art_gate=p["gate_global_arte"],
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
        if packet:
            rec.latest_generation_id = packet.get("generation_id", "")
            rec.human_visual_review_state = packet.get("human_visual_review_state", "DESCONOCIDO")
            rec.provider_mode = packet.get("provider", "")
        elif rec.handoff_state == "HANDOFF_EMITIDO":
            rec.blockers.append("handoff emitido pero sin ninguna materializacion de revision humana encontrada.")

        rec.next_action = _next_action_para(
            rec.art_gate, rec.handoff_state, rec.human_visual_review_state, rec.canonical_state)
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
    """Todo lo que espera una decision humana AHORA, en un solo lugar.

    No junta motivos con acciones: cada fila es una decision real, del
    vocabulario cerrado DECISION_*. Vacio no es un caso especial: una pieza
    sin bloqueos simplemente no aporta filas.
    """
    readiness = readiness if readiness is not None else build_readiness()
    items = []
    for r in readiness:
        if r.canonical_state == "REQUIERE_INVESTIGACION" or r.art_gate != "ABIERTO":
            items.append(InboxItem(
                DECISION_LEGAL_REVIEW, r.piece_id,
                f"canon={r.canonical_state} gate={r.art_gate}: exige revision juridica humana."))
            continue  # sin gate abierto no hay ninguna otra decision real que ofrecer.
        if r.handoff_state == "SIN_HANDOFF":
            items.append(InboxItem(
                DECISION_PRODUCTION_HANDOFF, r.piece_id,
                "gate ABIERTO sin ProductionHandoff: exige decision humana de produccion."))
        if r.human_visual_review_state in ("PENDIENTE", "SIN_GENERACION") and r.handoff_state == "HANDOFF_EMITIDO":
            items.append(InboxItem(
                DECISION_VISUAL_REVIEW, r.piece_id,
                f"generacion {r.latest_generation_id or '(ninguna)'} en {r.human_visual_review_state}: "
                "exige APPROVE_VISUAL / REGENERATE / REJECT_VISUAL."))
        if r.human_visual_review_state == "APPROVE_VISUAL":
            items.append(InboxItem(
                DECISION_PUBLICATION_AUTHORIZATION, r.piece_id,
                "visual aprobado; no existe PublicationDecision. Nunca se fabrica aqui."))
    return items


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
        packet = _review_packet_para(cid)
        filas.append({
            "content_id": cid,
            "piece_id": piece_id,
            "canonical_state": rp.canonical_state if rp else "DESCONOCIDO",
            "art_gate": rp.art_gate if rp else "DESCONOCIDO",
            "handoff_state": "HANDOFF_EMITIDO" if r.handoff is not None else "SIN_HANDOFF",
            "visual_state": "PRODUCCION_AUTORIZADA" if r.production_ready else "BLOQUEADO",
            "latest_generation_id": packet.get("generation_id", "") if packet else "",
            "provider_mode": packet.get("provider", "") if packet else "",
            "qa_state": (packet.get("structural_qa", {}) or {}).get("passed") if packet else None,
            "human_visual_review_state": packet.get("human_visual_review_state", "") if packet else "SIN_GENERACION",
            "blocker": r.blocking[0] if r.blocking else "",
            "next_action": rp.next_action if rp else "",
            "provenance_mode": modo,
        })
    return filas
