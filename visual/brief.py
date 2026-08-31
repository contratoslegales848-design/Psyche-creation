"""VisualBrief y VisualPolicy.

Un brief NO es texto libre: es una estructura que el compilador puede leer,
comprobar y versionar. Esto es lo que permite que la inteligencia visual sea de
LegalMente y no del proveedor de turno (mandato §1).
"""

import json
from dataclasses import dataclass, field
from pathlib import Path

POLICY_DIR = Path(__file__).resolve().parent / "policy"
DEFAULT_POLICY = POLICY_DIR / "legalmente-visual-policy-v1.json"

TEXT_MODES = {"IMAGE_ONLY", "POST_COMPOSITE", "NATIVE_TEXT"}


class PolicyError(ValueError):
    pass


class BriefError(ValueError):
    pass


@dataclass
class VisualPolicy:
    version: str
    data: dict

    @classmethod
    def load(cls, path=None):
        p = Path(path) if path else DEFAULT_POLICY
        if not p.is_file():
            raise PolicyError(f"politica visual no encontrada: {p}")
        data = json.loads(p.read_text(encoding="utf-8"))
        v = data.get("policy_version")
        if not v:
            raise PolicyError("la politica visual no declara 'policy_version'.")
        return cls(version=str(v), data=data)

    def formato(self, nombre):
        f = self.data.get("formatos", {}).get(nombre)
        if not f:
            raise PolicyError(
                f"formato {nombre!r} no permitido; admitidos: {sorted(self.data.get('formatos', {}))}"
            )
        return f

    @property
    def familias(self):
        return list(self.data.get("familias_visuales", []))

    @property
    def marca_escribe_generador(self):
        """'SI' | 'NO' | 'NO_RESUELTO'. NO_RESUELTO bloquea (conflicto abierto)."""
        return self.data.get("marca", {}).get("texto_marca_lo_escribe_el_generador", "NO_RESUELTO")


@dataclass
class VisualBrief:
    content_id: str
    formato: str                    # clave de policy.formatos
    visual_family: str
    subject: str
    environment: str
    camera: str
    focal_point: str
    text_rendering_mode: str = "POST_COMPOSITE"
    metaphor: str = ""
    negative_space: str = ""
    key_light: str = ""
    brightness_intent: str = ""
    acento_frio_objeto: str = ""     # objeto fisico real que aporta el azul petroleo
    marca_superficie: str = ""       # superficie fisica donde vive la marca
    marca_texto_en_imagen: bool = False   # ¿debe el GENERADOR escribir "LegalMente"?
    constraints: list = field(default_factory=list)
    negative_constraints: list = field(default_factory=list)
    tiene_carga_juridica: bool = True
    brief_version: str = "1.0"

    def validate(self, policy):
        """Comprueba el brief contra la politica. Devuelve lista de errores."""
        e = []
        if not str(self.content_id or "").strip():
            e.append("content_id vacio.")

        try:
            policy.formato(self.formato)
        except PolicyError as exc:
            e.append(str(exc))

        if self.visual_family not in policy.familias:
            e.append(
                f"visual_family {self.visual_family!r} fuera del catalogo: {policy.familias}"
            )

        for campo in ("subject", "environment", "camera", "focal_point"):
            if not str(getattr(self, campo) or "").strip():
                e.append(f"composicion incompleta: '{campo}' vacio.")

        if self.text_rendering_mode not in TEXT_MODES:
            e.append(f"text_rendering_mode invalido: {self.text_rendering_mode!r}")

        texto_pol = policy.data.get("texto", {})
        if self.text_rendering_mode not in texto_pol.get("modos_permitidos", []):
            if self.text_rendering_mode == "NATIVE_TEXT":
                e.append(
                    "NATIVE_TEXT exige un proveedor con capacidad de texto demostrada; "
                    "la negociacion de capacidades lo comprueba, la politica no lo permite por defecto."
                )
            else:
                e.append(f"text_rendering_mode {self.text_rendering_mode!r} no permitido por la politica.")

        if self.tiene_carga_juridica and texto_pol.get("contenido_juridico_exige_post_composite"):
            if self.text_rendering_mode == "NATIVE_TEXT":
                e.append(
                    "contenido con carga juridica: el texto se monta despues de forma determinista, "
                    "nunca lo escribe el generador."
                )

        paleta = policy.data.get("paleta", {})
        if paleta.get("acento_frio_debe_ser_objeto_fisico") and not str(self.acento_frio_objeto).strip():
            e.append(
                "la politica exige que el acento azul petroleo lo produzca un objeto fisico real de la escena; "
                "'acento_frio_objeto' esta vacio."
            )

        marca = policy.data.get("marca", {})
        if marca.get("integracion_fisica_requerida"):
            if not str(self.marca_superficie).strip():
                e.append("la marca exige integracion fisica: 'marca_superficie' esta vacio.")
            elif self.marca_superficie not in marca.get("superficies_permitidas", []):
                e.append(
                    f"marca_superficie {self.marca_superficie!r} fuera de las superficies permitidas."
                )

        # --- conflicto abierto, resuelto fail-closed ---
        if self.marca_texto_en_imagen:
            decidido = policy.marca_escribe_generador
            if decidido != "SI":
                e.append(
                    "CONFLICTO NO RESUELTO: el brief pide que el generador escriba 'LegalMente' dentro de la "
                    "imagen, pero la politica declara "
                    f"texto_marca_lo_escribe_el_generador={decidido!r}. Requiere decision expresa del fundador "
                    "(ver docs/decision-visual-marca-sin-texto.md). Hasta entonces se bloquea."
                )
        return e
