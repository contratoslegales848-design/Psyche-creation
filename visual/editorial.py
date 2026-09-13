"""Registro del universo EDITORIAL — el eje que faltaba.

`families.py` registra familias VISUALES (óleo, claroscuro, hiperrealismo): el
lenguaje con que se dibuja una pieza. Este módulo registra familias
EDITORIALES (mito, diferencia, checklist, historia del Derecho, etimología):
la FUNCIÓN que la pieza cumple para quien la lee. Son ejes ortogonales y
confundirlos es la raíz del defecto que reporta el fundador: diez piezas con
diez estilos distintos siguen siendo diez definiciones.

Autoridad: Drive `Capa canónica de diversidad editorial y universo temático v1`
(§1 la declara dimensión canónica de selección; §11 la declara abierta) y
`00 LEER PRIMERO` §4. La lista es SEMILLA, nunca techo: `register_familia`
existe porque el canon lo exige, no como conveniencia.

Nada aquí es fuente jurídica. Estos ejes deciden QUÉ FORMA tiene una pieza y
CONTRA QUÉ se compara para no repetirse; jamás si una afirmación es cierta.
Eso sigue siendo exclusivo de `legalmente-legal-verification` (CLAUDE.md §4).
"""

import json
from dataclasses import dataclass
from pathlib import Path

REGISTRY_PATH = Path(__file__).resolve().parent / "policy" / "editorial-universe-v1.json"


class EditorialError(ValueError):
    pass


@dataclass(frozen=True)
class FamiliaEditorial:
    nombre: str
    funcion_editorial: str
    tension_tipica: str
    necesidades_afines: tuple = ()
    roles_lector_afines: tuple = ()
    profundidad_tipica: str = "base"


class EditorialUniverse:
    """Universo editorial abierto. Cuenta lo que hay; no inventa lo que falta."""

    def __init__(self, version, familias, necesidades, roles, angulos,
                 contextos, profundidades, formatos):
        self.version = version
        self._familias = dict(familias)
        self.necesidades = dict(necesidades)
        self.roles_lector = dict(roles)
        self.angulos = dict(angulos)
        self.contextos_funcionales = dict(contextos)
        self.profundidades = dict(profundidades)
        self.formatos_editoriales = dict(formatos)

    @classmethod
    def load(cls, path=None):
        p = Path(path) if path else REGISTRY_PATH
        if not p.is_file():
            raise EditorialError(f"registro editorial no encontrado: {p}")
        data = json.loads(p.read_text(encoding="utf-8"))
        v = data.get("registry_version")
        if not v:
            raise EditorialError("el registro editorial no declara 'registry_version'.")
        fams = {}
        for nombre, f in (data.get("familias_editoriales") or {}).items():
            fams[nombre] = FamiliaEditorial(
                nombre=nombre,
                funcion_editorial=f.get("funcion_editorial", ""),
                tension_tipica=f.get("tension_tipica", ""),
                necesidades_afines=tuple(f.get("necesidades_afines", ())),
                roles_lector_afines=tuple(f.get("roles_lector_afines", ())),
                profundidad_tipica=f.get("profundidad_tipica", "base"),
            )
        if not fams:
            raise EditorialError("el registro editorial está vacío.")
        return cls(str(v), fams,
                   data.get("necesidades") or {}, data.get("roles_lector") or {},
                   data.get("angulos") or {}, data.get("contextos_funcionales") or {},
                   data.get("profundidades") or {}, data.get("formatos_editoriales") or {})

    def get(self, nombre):
        f = self._familias.get(nombre)
        if f is None:
            raise EditorialError(
                f"familia editorial desconocida: {nombre!r}. El registro es abierto: "
                "usa register_familia() para darla de alta explícitamente, pero nunca "
                "se infiere una familia que nadie declaró.")
        return f

    def names(self):
        return sorted(self._familias)

    def __len__(self):
        return len(self._familias)

    def register_familia(self, familia):
        """Alta de familia nueva (canon §11: las listas son semilla, no techo).

        Se rechaza el duplicado exacto de nombre. NO se intenta detectar
        duplicidad semántica automáticamente: el canon exige que la familia
        nueva 'no duplique semánticamente otra ya existente', y esa es una
        valoración editorial humana. El registro deja constancia del alta;
        no finge un juicio que no puede hacer.
        """
        if not isinstance(familia, FamiliaEditorial):
            raise EditorialError("register_familia espera una FamiliaEditorial.")
        if not str(familia.nombre or "").strip():
            raise EditorialError("una familia editorial necesita nombre.")
        if familia.nombre in self._familias:
            raise EditorialError(f"familia editorial ya registrada: {familia.nombre!r}")
        if not str(familia.funcion_editorial or "").strip():
            raise EditorialError(
                f"familia {familia.nombre!r} sin funcion_editorial: una familia que no "
                "declara para qué sirve no es distinguible y el canon la rechaza.")
        self._familias[familia.nombre] = familia
        return familia

    # --- afinidad: qué familias sirven a una necesidad / a un rol ----------
    def familias_para_necesidad(self, necesidad):
        return sorted(n for n, f in self._familias.items() if necesidad in f.necesidades_afines)

    def familias_para_rol(self, rol):
        return sorted(n for n, f in self._familias.items() if rol in f.roles_lector_afines)
