"""GenerationPlan — lo que se va a hacer, ANTES de hacerlo.

Serializable y hasheable. Permite dry-run, revision, diffing y deteccion de
deriva sin gastar un solo credito.
"""

import hashlib
import json
from dataclasses import dataclass, field, asdict

PLAN_SCHEMA_VERSION = "1.0"

ACCEPT, ADAPT, REJECT = "ACCEPT", "ADAPT", "REJECT"


@dataclass
class GenerationPlan:
    content_id: str
    content_hash: str = ""
    formato: str = ""
    width: int = 0
    height: int = 0
    aspect_ratio: str = ""
    visual_family: str = ""
    provider: str = ""
    provider_compatibility: str = REJECT
    compatibility_notes: list = field(default_factory=list)
    text_mode: str = ""
    brand_mode: str = ""
    repetition_level: str = ""
    repetition_score: int = 0
    repetition_warnings: list = field(default_factory=list)
    explanation: list = field(default_factory=list)
    visual_policy_version: str = ""
    visual_family_registry_version: str = ""
    visual_brief_version: str = ""
    prompt_compiler_version: str = ""
    compiled_request_hash: str = ""
    provider_capabilities_snapshot: dict = field(default_factory=dict)
    cost_class: str = "UNKNOWN"
    schema_version: str = PLAN_SCHEMA_VERSION

    def to_dict(self):
        return asdict(self)

    def plan_hash(self):
        return canonical_hash(self.to_dict())

    @property
    def executable(self):
        return self.provider_compatibility in (ACCEPT, ADAPT)


def canonical_hash(obj):
    """Hash estable de una serializacion canonica. Base de reproducibilidad."""
    return hashlib.sha256(
        json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
