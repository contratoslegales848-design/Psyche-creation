"""Generation receipts — trazabilidad de cada intento, no solo de los exitosos.

Un receipt se emite SIEMPRE: tambien cuando el gate cierra, cuando el brief no
valida y cuando el proveedor falla. Un sistema que solo registra sus exitos no
tiene trazabilidad, tiene publicidad.

Los receipts no se borran ni se reescriben (CLAUDE.md §4, mandato §4).
"""

import hashlib
import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path

RECEIPT_SCHEMA_VERSION = "1.0"

STATUS = (
    "GATE_CERRADO",
    "BRIEF_INVALIDO",
    "PROVEEDOR_INCOMPATIBLE",
    "GENERACION_FALLIDA",
    "QA_FALLIDO",
    "PENDIENTE_REVISION_HUMANA",
)


@dataclass
class GenerationReceipt:
    content_id: str
    status: str
    generation_id: str = field(default_factory=lambda: f"gen-{uuid.uuid4().hex[:12]}")
    asset_id: str = ""
    asset_sha256: str = ""
    provider: str = ""
    model: str = ""
    prompt_compiler_version: str = ""
    visual_policy_version: str = ""
    visual_brief_version: str = ""
    prompt_sha256: str = ""
    negative_prompt_sha256: str = ""
    seed: int = None
    parametros: dict = field(default_factory=dict)
    procedencia: dict = field(default_factory=dict)
    qa_problemas: list = field(default_factory=list)
    qa_avisos: list = field(default_factory=list)
    motivos: list = field(default_factory=list)
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
            encoding="utf-8",
        )
        return path


def asset_id_for(content_id, asset_sha256):
    base = f"{content_id}|{asset_sha256}".encode("utf-8")
    return "asset-" + hashlib.sha256(base).hexdigest()[:16]
