"""Registro versionado de familias visuales.

LegalMente no debe producir todas las imagenes con la misma formula. Una familia
aporta DATOS al compilador (luz, camara, materiales, entornos, tropos
prohibidos), nunca un prompt monolitico.
"""

import json
from dataclasses import dataclass
from pathlib import Path

REGISTRY_PATH = Path(__file__).resolve().parent / "policy" / "visual-families-v1.json"


class FamilyError(ValueError):
    pass


@dataclass(frozen=True)
class VisualFamily:
    name: str
    lighting_intent: str
    camera_tendencies: tuple
    material_vocabulary: tuple
    preferred_environments: tuple
    palette_tendency: tuple
    human_presence: str
    brand_surface_preferences: tuple
    forbidden_tropes: tuple


class VisualFamilyRegistry:
    def __init__(self, version, familias):
        self.version = version
        self._familias = familias

    @classmethod
    def load(cls, path=None):
        p = Path(path) if path else REGISTRY_PATH
        if not p.is_file():
            raise FamilyError(f"registro de familias no encontrado: {p}")
        data = json.loads(p.read_text(encoding="utf-8"))
        v = data.get("registry_version")
        if not v:
            raise FamilyError("el registro de familias no declara 'registry_version'.")
        fams = {}
        for name, f in (data.get("familias") or {}).items():
            fams[name] = VisualFamily(
                name=name,
                lighting_intent=f.get("lighting_intent", ""),
                camera_tendencies=tuple(f.get("camera_tendencies", ())),
                material_vocabulary=tuple(f.get("material_vocabulary", ())),
                preferred_environments=tuple(f.get("preferred_environments", ())),
                palette_tendency=tuple(f.get("palette_tendency", ())),
                human_presence=f.get("human_presence", ""),
                brand_surface_preferences=tuple(f.get("brand_surface_preferences", ())),
                forbidden_tropes=tuple(f.get("forbidden_tropes", ())),
            )
        if not fams:
            raise FamilyError("el registro de familias esta vacio.")
        return cls(str(v), fams)

    def get(self, name):
        f = self._familias.get(name)
        if f is None:
            raise FamilyError(f"familia visual desconocida: {name!r} (conocidas: {sorted(self._familias)})")
        return f

    def names(self):
        return sorted(self._familias)
