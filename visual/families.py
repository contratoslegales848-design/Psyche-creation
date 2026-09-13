"""Registro versionado de familias visuales.

LegalMente no debe producir todas las imagenes con la misma formula. Una familia
aporta DATOS al compilador (luz, camara, materiales, entornos, tropos
prohibidos), nunca un prompt monolitico.

Desde el registro 1.1 una familia aporta tambien DETALLE ARTISTICO: profundidad
de campo, acabado de superficie, firma de imperfeccion, temperatura de color,
curva de contraste, sesgo de composicion, grano y entornos cotidianos. Sin estos
ejes el prompt describia QUE hay en la escena pero no COMO esta hecha, que es
justamente donde se pierde el detalle artistico. Todos son opcionales: un
registro antiguo (1.0) sigue cargando, simplemente sin detalle que aportar.
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
    # --- detalle artistico (registro >= 1.1; vacio en registros antiguos) ---
    carril: str = ""
    depth_of_field: str = ""
    surface_finish: str = ""
    imperfection_signature: tuple = ()
    color_temperature: str = ""
    contrast_curve: str = ""
    composition_bias: str = ""
    everyday_environments: tuple = ()
    grain: str = ""

    @property
    def tiene_detalle_artistico(self):
        """¿Esta familia puede aportar detalle, o solo tema y encuadre?"""
        return bool(self.depth_of_field or self.surface_finish or self.contrast_curve)


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
                carril=f.get("carril", ""),
                depth_of_field=f.get("depth_of_field", ""),
                surface_finish=f.get("surface_finish", ""),
                imperfection_signature=tuple(f.get("imperfection_signature", ())),
                color_temperature=f.get("color_temperature", ""),
                contrast_curve=f.get("contrast_curve", ""),
                composition_bias=f.get("composition_bias", ""),
                everyday_environments=tuple(f.get("everyday_environments", ())),
                grain=f.get("grain", ""),
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
