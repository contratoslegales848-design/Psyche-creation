"""Generation receipts — trazabilidad de cada intento, no solo de los exitosos.

Un receipt se emite SIEMPRE: tambien cuando el gate cierra, cuando el brief no
valida y cuando el proveedor falla. Un sistema que solo registra sus exitos no
tiene trazabilidad, tiene publicidad.

Un generation receipt describe LO QUE HIZO LA MAQUINA. La decision humana vive
en un documento separado (HumanDecisionReceipt, en registry.py): nunca se edita
un generation receipt para aparentar aprobacion.

Los receipts no se borran ni se reescriben.
"""

import hashlib
import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path

RECEIPT_SCHEMA_VERSION = "2.0"

STATUS = (
    "GATE_CERRADO",
    "BRIEF_INVALIDO",
    "PROVEEDOR_INCOMPATIBLE",
    "DRY_RUN",
    "GENERACION_FALLIDA",
    "QA_FALLIDO",
    "PENDIENTE_REVISION_HUMANA",
)


@dataclass
class GenerationReceipt:
    content_id: str
    status: str
    content_hash: str = ""
    generation_id: str = field(default_factory=lambda: f"gen-{uuid.uuid4().hex[:12]}")
    asset_id: str = ""
    asset_sha256: str = ""
    parent_generation_id: str = ""
    provider: str = ""
    model: str = ""
    provider_capabilities_snapshot: dict = field(default_factory=dict)
    prompt_compiler_version: str = ""
    visual_policy_version: str = ""
    visual_family: str = ""
    visual_family_registry_version: str = ""
    visual_brief_version: str = ""
    prompt_sha256: str = ""
    negative_prompt_sha256: str = ""
    compiled_request_hash: str = ""
    generation_plan_hash: str = ""
    seed: int = None
    text_mode: str = ""
    brand_mode: str = ""
    brand_plan: dict = field(default_factory=dict)
    typography_plan: dict = field(default_factory=dict)
    parametros: dict = field(default_factory=dict)
    procedencia: dict = field(default_factory=dict)
    structural_qa: dict = field(default_factory=dict)
    semantic_qa: dict = field(default_factory=dict)
    qa_problemas: list = field(default_factory=list)
    qa_avisos: list = field(default_factory=list)
    motivos: list = field(default_factory=list)
    explanation: list = field(default_factory=list)
    feedback_codes: list = field(default_factory=list)
    changed_fields: dict = field(default_factory=dict)
    events: list = field(default_factory=list)
    cost_class: str = "UNKNOWN"
    human_visual_approval: str = "PENDIENTE"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    schema_version: str = RECEIPT_SCHEMA_VERSION

    def __post_init__(self):
        if self.status not in STATUS:
            raise ValueError(f"status de receipt desconocido: {self.status!r} (uno de {list(STATUS)})")

    def to_dict(self):
        return asdict(self)

    def write(self, directory):
        """Escribe el receipt. Nunca sobrescribe uno existente."""
        d = Path(directory)
        d.mkdir(parents=True, exist_ok=True)
        path = d / f"{self.generation_id}.json"
        if path.exists():
            raise FileExistsError(f"receipt ya existente, no se sobrescribe: {path}")
        path.write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8")
        return path


def asset_id_for(content_id, asset_sha256):
    base = f"{content_id}|{asset_sha256}".encode("utf-8")
    return "asset-" + hashlib.sha256(base).hexdigest()[:16]


def build_human_review_packet(run, exact_copy="", author=""):
    """Objeto estructurado para una futura UI de revision humana (§39).

    No implementa UI: prepara exactamente lo que una persona necesita ver para
    decidir, y las opciones de feedback que puede elegir.
    """
    from feedback import FEEDBACK_CODES
    r = run.receipt
    return {
        "content_id": r.content_id,
        "generation_id": r.generation_id,
        "asset_id": r.asset_id,
        "asset_sha256": r.asset_sha256,
        "expected_exact_copy": exact_copy,
        "author": author,
        "brief_summary": {
            "visual_family": r.visual_family,
            "text_mode": r.text_mode,
            "brand_mode": r.brand_mode,
            "formato": r.parametros.get("aspect_ratio", ""),
        },
        "provider": r.provider,
        "explanation": list(r.explanation),
        "warnings": list(r.motivos),
        "structural_qa": r.structural_qa,
        "semantic_qa": r.semantic_qa,
        "typography_plan": r.typography_plan,
        "brand_plan": r.brand_plan,
        "feedback_reason_choices": sorted(FEEDBACK_CODES),
        "decision_required": True,
        "nota": "Ninguna parte de este paquete constituye aprobacion. La decision humana se registra aparte.",
    }
