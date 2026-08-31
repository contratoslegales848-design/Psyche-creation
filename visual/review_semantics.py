"""Que significa realmente un review-packet — nunca lo que su forma sugiere.

`human_visual_review_state = PENDIENTE` es correcto como hecho tecnico (nadie
ha decidido todavia), pero por si solo suena a "hay una imagen esperando que
la juzgues". Cuando el proveedor es FakeImageProvider, eso es falso: no hay
arte que juzgar, solo un placeholder mecanico. Este modulo separa ambas cosas
en vez de fabricar un estado de aprobacion o dejar la ambiguedad sin resolver.

No reescribe review-packet.json (la historia no se toca): clasifica al leer.
"""

from dataclasses import dataclass

MECHANICAL_QA = "MECHANICAL_QA"
COPY_QA = "COPY_QA"
BRAND_COMPOSITION_QA = "BRAND_COMPOSITION_QA"
REAL_ART_SEMANTIC_QA = "REAL_ART_SEMANTIC_QA"
HUMAN_ART_REVIEW = "HUMAN_ART_REVIEW"

PASS = "PASS"
FAIL = "FAIL"
NOT_AVAILABLE = "NOT_AVAILABLE"
NOT_ACTIONABLE_UNTIL_REAL_PROVIDER = "NOT_ACTIONABLE_UNTIL_REAL_PROVIDER"


@dataclass
class ReviewClassification:
    provider_is_simulated: bool
    mechanical_qa: str
    copy_qa: str
    brand_composition_qa: str
    real_art_semantic_qa: str
    human_art_review: str
    raw_human_visual_review_state: str

    def to_dict(self):
        return {
            "provider_is_simulated": self.provider_is_simulated,
            MECHANICAL_QA: self.mechanical_qa,
            COPY_QA: self.copy_qa,
            BRAND_COMPOSITION_QA: self.brand_composition_qa,
            REAL_ART_SEMANTIC_QA: self.real_art_semantic_qa,
            HUMAN_ART_REVIEW: self.human_art_review,
            "raw_human_visual_review_state": self.raw_human_visual_review_state,
        }


def _es_simulado(provider_str):
    p = str(provider_str or "").lower()
    return "simulat" in p or p.startswith("fake") or " fake" in p


def classify(packet):
    """Clasifica un review-packet.json ya cargado. No inventa datos ausentes:
    su ausencia se mapea a NOT_AVAILABLE, jamas a PASS ni a una aprobacion."""
    if not isinstance(packet, dict):
        return ReviewClassification(True, NOT_AVAILABLE, NOT_AVAILABLE, NOT_AVAILABLE,
                                     NOT_AVAILABLE, NOT_ACTIONABLE_UNTIL_REAL_PROVIDER, "SIN_GENERACION")

    provider = packet.get("provider", "")
    simulado = _es_simulado(provider)

    sq = packet.get("structural_qa")
    if isinstance(sq, dict) and "passed" in sq:
        mechanical = PASS if sq["passed"] else FAIL
    else:
        mechanical = NOT_AVAILABLE

    copy_qa = PASS if str(packet.get("exact_copy") or "").strip() else NOT_AVAILABLE
    brand_qa = PASS if packet.get("brand_mode") == "POST_COMPOSITE" else NOT_AVAILABLE

    raw_state = packet.get("human_visual_review_state", "DESCONOCIDO")
    if simulado:
        human_art_review = NOT_ACTIONABLE_UNTIL_REAL_PROVIDER
    else:
        human_art_review = raw_state

    return ReviewClassification(
        provider_is_simulated=simulado,
        mechanical_qa=mechanical,
        copy_qa=copy_qa,
        brand_composition_qa=brand_qa,
        real_art_semantic_qa=NOT_AVAILABLE,
        human_art_review=human_art_review,
        raw_human_visual_review_state=raw_state,
    )
