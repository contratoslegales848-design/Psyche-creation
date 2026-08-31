"""Planes de composicion posterior: tipografia y marca.

Estado honesto: estos son CONTRATOS EJECUTABLES + PLANES DETERMINISTAS. El
rasterizado real NO esta implementado — el repositorio no tiene Pillow ni
ninguna dependencia de imagen, y fabricar un rasterizador tipografico a mano
seria peor que declarar el limite.

Lo que si es real y probado aqui: el plan que un compositor (Canva, script con
Pillow, o quien sea) debe ejecutar, y la garantia de que `exact_copy` no se
altera jamas para hacer caber el texto.
"""

from dataclasses import dataclass, field, asdict

LAYOUT_TYPES = {
    "SHORT_QUOTE", "LONG_QUOTE", "LEGAL_CONCEPT", "COMPARISON",
    "MYTH", "AUTHOR_IDEA", "EXPLAINER", "LIST_ITEM",
}

# Umbral de caracteres que separa cita corta de cita larga.
UMBRAL_CITA_CORTA = 90

# Margen seguro como fraccion del lado. Nada de texto fuera de esta caja.
SAFE_AREA_RATIO = 0.08

# Tamaño minimo legible en movil, en px sobre el lienzo de 1080 de ancho.
MIN_READABLE_PX = 34


class ExactCopyViolation(ValueError):
    """El compositor intento cambiar el texto exacto. Nunca permitido."""


@dataclass
class TextBlock:
    role: str            # QUOTE | AUTHOR | CONTEXT | LABEL
    text: str
    font_role: str
    size_px: int
    max_width_px: int
    lines: list = field(default_factory=list)


@dataclass
class TypographyPlan:
    layout_type: str
    canvas: tuple
    safe_area: tuple                 # (x, y, w, h)
    alignment: str = "left"
    blocks: list = field(default_factory=list)
    minimum_readable_size: int = MIN_READABLE_PX
    line_break_strategy: str = "PALABRA_COMPLETA"
    warnings: list = field(default_factory=list)

    def to_dict(self):
        d = asdict(self)
        d["blocks"] = [asdict(b) if not isinstance(b, dict) else b for b in self.blocks]
        return d

    def rendered_text(self):
        """Texto que el compositor colocara, reconstruido desde las lineas."""
        for b in self.blocks:
            if b.role == "QUOTE":
                return " ".join(" ".join(l.split()) for l in b.lines).strip()
        return ""


def infer_layout_type(content_type, exact_copy):
    """Deduce el layout desde la taxonomia canonica; cae a longitud si no la hay."""
    mapa = {
        "concepto": "LEGAL_CONCEPT", "tecnicismo": "LEGAL_CONCEPT",
        "mito": "MYTH", "diferencia": "COMPARISON", "listado": "LIST_ITEM",
        "consecuencia": "EXPLAINER", "aforismo": "SHORT_QUOTE",
        "maxima": "SHORT_QUOTE", "frase": "SHORT_QUOTE",
    }
    t = mapa.get(str(content_type or "").strip().lower())
    if t:
        if t == "SHORT_QUOTE" and len(exact_copy or "") > UMBRAL_CITA_CORTA:
            return "LONG_QUOTE"
        return t
    return "SHORT_QUOTE" if len(exact_copy or "") <= UMBRAL_CITA_CORTA else "LONG_QUOTE"


def _wrap(texto, max_chars):
    """Corte por palabra completa. NUNCA parte ni abrevia una palabra."""
    palabras, lineas, actual = texto.split(), [], ""
    for p in palabras:
        cand = f"{actual} {p}".strip()
        if len(cand) <= max_chars or not actual:
            actual = cand
        else:
            lineas.append(actual)
            actual = p
    if actual:
        lineas.append(actual)
    return lineas


def build_typography_plan(exact_copy, author, width, height, content_type="", context=""):
    """Plan determinista. `exact_copy` se transporta intacto: se comprueba al final."""
    if exact_copy is None:
        raise ExactCopyViolation("no hay exact_copy que componer.")

    layout = infer_layout_type(content_type, exact_copy)
    mx = int(width * SAFE_AREA_RATIO)
    my = int(height * SAFE_AREA_RATIO)
    safe = (mx, my, width - 2 * mx, height - 2 * my)

    largo = len(exact_copy)
    size = 96 if largo <= 40 else 78 if largo <= UMBRAL_CITA_CORTA else 60 if largo <= 180 else 46
    warnings = []
    if size < MIN_READABLE_PX:
        size = MIN_READABLE_PX
    # Aproximacion tipografica: ~0.52 em de ancho medio por caracter.
    max_chars = max(8, int(safe[2] / (size * 0.52)))
    lineas = _wrap(exact_copy, max_chars)

    # Si no cabe en la caja segura, se AVISA y se escala hasta el minimo legible.
    # Por debajo del minimo se marca para revision humana; jamas se parafrasea.
    alto_disponible = safe[3] - (140 if author else 0)
    while len(lineas) * int(size * 1.32) > alto_disponible and size > MIN_READABLE_PX:
        size = max(MIN_READABLE_PX, int(size * 0.92))
        max_chars = max(8, int(safe[2] / (size * 0.52)))
        lineas = _wrap(exact_copy, max_chars)
    if len(lineas) * int(size * 1.32) > alto_disponible:
        warnings.append(
            "el texto exacto no cabe en el area segura al tamaño minimo legible: "
            "requiere revision humana (reencuadre o cambio de formato). NO se parafrasea."
        )

    blocks = [TextBlock("QUOTE", exact_copy, "serif_display", size, safe[2], lineas)]
    if author:
        blocks.append(TextBlock("AUTHOR", author, "sans_caption", max(MIN_READABLE_PX, int(size * 0.42)),
                                safe[2], _wrap(author, max(10, int(safe[2] / (size * 0.42 * 0.52))))))
    if context:
        blocks.append(TextBlock("CONTEXT", context, "sans_caption", MIN_READABLE_PX,
                                safe[2], _wrap(context, 60)))

    plan = TypographyPlan(layout, (width, height), safe, blocks=blocks, warnings=warnings)
    assert_exact_copy_preserved(exact_copy, plan)
    return plan


def assert_exact_copy_preserved(exact_copy, plan):
    """Invariante no negociable: el compositor no parafrasea para hacer caber texto."""
    if " ".join(exact_copy.split()) != plan.rendered_text():
        raise ExactCopyViolation(
            "el plan tipografico altera el texto exacto aprobado. Prohibido: el texto "
            "juridico aprobado por un humano no se reescribe para que quepa."
        )
    return True


@dataclass
class BrandCompositionPlan:
    required: bool
    text: str = "LegalMente"
    surface_type: str = ""
    placement_region: str = ""
    perspective_required: bool = True
    lighting_match_required: bool = True
    material_integration_required: bool = True
    generator_writes_text: bool = False
    coercion_note: str = ""

    def to_dict(self):
        return asdict(self)


def build_brand_plan(policy, surface, requested_generator_text=False):
    """Resuelve el modo de marca segun la politica vigente.

    Si la politica dice que el generador NO escribe la marca (decision del
    fundador 2026-08-31), una peticion de texto en imagen se CONVIERTE a
    composicion posterior y se deja constancia. Nunca llega al proveedor.
    """
    marca = policy.data.get("marca", {})
    required = bool(marca.get("integracion_fisica_requerida"))
    permite = marca.get("texto_marca_lo_escribe_el_generador") == "SI"

    nota = ""
    if requested_generator_text and not permite:
        nota = ("Se pidio que el generador escribiera la marca; la politica vigente lo prohibe. "
                "Convertido a composicion determinista posterior. La peticion no se envia al proveedor.")

    return BrandCompositionPlan(
        required=required,
        text=str(marca.get("brand_text") or "LegalMente"),
        surface_type=surface,
        placement_region="superficie fisica reservada en la escena",
        generator_writes_text=bool(permite and requested_generator_text),
        coercion_note=nota,
    )
