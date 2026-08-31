"""Compositor determinista: RAW ASSET + planes -> COMPOSED ASSET.

Frontera fundamental (mandato §40):

    EL PROVEEDOR POSEE:   la generacion del arte en bruto.
    LEGALMENTE POSEE:     el texto exacto, la marca, la composicion, el QA,
                          los receipts y la historia.

Por eso esto vive aqui y no en Canva, ni en el proveedor, ni en un prompt.
Canva podra ser en el futuro un destino de exportacion; nunca la fuente de verdad.

Dependencia: Pillow (MIT-CMU), la unica del repositorio. Justificada en
docs/adr/0003-dependencia-pillow-compositor.md.

Limites declarados de la V1:
- Solo compone marca sobre una superficie reservada PLANA o casi plana, y sus
  coordenadas deben venir DECLARADAS: no hay vision que las detecte.
- Ante superficie compleja, ausente o no declarada -> NEEDS_HUMAN_REVIEW.
  Nunca degrada a watermark, logo flotante ni firma en una esquina.
"""

import hashlib
import io
from dataclasses import dataclass, field, asdict
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

COMPOSITOR_VERSION = "1.0"

# Limites de recursos (§44). No es DRM: evita fallos triviales y bombas obvias.
MAX_DIMENSION = 8192
MAX_PIXELS = 40_000_000
MAX_TEXT_CHARS = 4000

# Fuentes preferidas, en orden. Se registra cual se uso: el resultado debe ser
# explicable y reproducible en la maquina donde se genero.
FONT_CANDIDATES = {
    "serif_display": ("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
                      "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"),
    "sans_caption": ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",),
    "brand": ("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
}


class CompositionOverflow(ValueError):
    """El texto exacto no cabe. NUNCA se resuelve modificando el texto."""


class CompositionError(ValueError):
    pass


NEEDS_HUMAN_REVIEW = "NEEDS_HUMAN_REVIEW"
COMPOSED = "COMPOSED"


@dataclass
class ReservedSurface:
    """Region fisica declarada donde vive la marca.

    Debe declararse: no existe deteccion visual en este repositorio. `flat`
    indica que la superficie es plana o casi plana; si no lo es, la V1 no
    intenta fingir perspectiva.
    """

    x: int
    y: int
    width: int
    height: int
    flat: bool = True
    rotation_deg: float = 0.0

    def to_dict(self):
        return asdict(self)

    @property
    def usable(self):
        return (self.flat and abs(self.rotation_deg) <= 3.0
                and self.width > 0 and self.height > 0)


@dataclass
class CompositionResult:
    state: str
    raw_sha256: str = ""
    composed_sha256: str = ""
    composed_bytes: bytes = b""
    width: int = 0
    height: int = 0
    compositor_version: str = COMPOSITOR_VERSION
    typography_plan_hash: str = ""
    brand_plan_hash: str = ""
    composition_plan_hash: str = ""
    fonts_used: dict = field(default_factory=dict)
    brand_applied: bool = False
    warnings: list = field(default_factory=list)
    reason_codes: list = field(default_factory=list)

    def to_dict(self):
        d = asdict(self)
        d.pop("composed_bytes", None)
        return d


def _font(role, size):
    """Fuente determinista. Cae a la que Pillow trae si el sistema no tiene DejaVu."""
    for path in FONT_CANDIDATES.get(role, ()):
        if Path(path).is_file():
            return ImageFont.truetype(path, size), Path(path).name
    return ImageFont.load_default(size=size), "pillow-default"


def measure(text, font):
    """Ancho y alto reales del texto con la fuente dada."""
    if not text:
        return 0, 0
    box = font.getbbox(text)
    return box[2] - box[0], box[3] - box[1]


def wrap_to_width(text, font, max_width):
    """Corte por palabra completa usando METRICA REAL. Nunca parte una palabra.

    Si una sola palabra no cabe, se devuelve igualmente en su propia linea: el
    desbordamiento se reporta arriba, jamas se abrevia la palabra.
    """
    palabras, lineas, actual = text.split(), [], ""
    for p in palabras:
        cand = f"{actual} {p}".strip()
        if measure(cand, font)[0] <= max_width or not actual:
            actual = cand
        else:
            lineas.append(actual)
            actual = p
    if actual:
        lineas.append(actual)
    return lineas


def _sha(b):
    return hashlib.sha256(b).hexdigest()


def _validar_recursos(img, textos):
    if img.width > MAX_DIMENSION or img.height > MAX_DIMENSION:
        raise CompositionError(f"imagen demasiado grande: {img.width}x{img.height}")
    if img.width * img.height > MAX_PIXELS:
        raise CompositionError(f"imagen excede {MAX_PIXELS} pixeles")
    for t in textos:
        if t and len(t) > MAX_TEXT_CHARS:
            raise CompositionError(f"texto de {len(t)} caracteres excede el maximo {MAX_TEXT_CHARS}")


def compose(raw_bytes, typography_plan, brand_plan=None, reserved_surface=None,
            target_size=None):
    """Compone el asset final. NO modifica el raw: trabaja sobre una copia.

    Devuelve CompositionResult. Lanza CompositionOverflow si el texto exacto no
    cabe al tamaño minimo legible — el texto no se toca jamas.
    """
    if not raw_bytes:
        raise CompositionError("no hay asset en bruto que componer.")

    raw_sha = _sha(raw_bytes)
    try:
        base = Image.open(io.BytesIO(raw_bytes))
        base.load()
    except Exception as exc:
        raise CompositionError(f"asset en bruto no legible: {exc}")

    textos = [b.text for b in typography_plan.blocks]
    _validar_recursos(base, textos)

    img = base.convert("RGB")
    # El raw solo se escala si el plan pide un lienzo distinto (p. ej. el
    # proveedor entrego una miniatura). El original en disco nunca se toca.
    destino = target_size or tuple(typography_plan.canvas)
    if (img.width, img.height) != destino:
        img = img.resize(destino, Image.LANCZOS)

    draw = ImageDraw.Draw(img)
    sx, sy, sw, sh = typography_plan.safe_area
    fonts_used, warnings, reason_codes = {}, list(typography_plan.warnings), []

    # --- tipografia ---
    y = sy
    bloques_render = []
    for b in typography_plan.blocks:
        size = b.size_px
        font, nombre = _font(b.font_role, size)
        fonts_used[b.role] = nombre
        lineas = wrap_to_width(b.text, font, sw)

        # Reduce hasta el minimo legible; por debajo, desborda y se declara.
        while size > typography_plan.minimum_readable_size:
            alto = len(lineas) * int(size * 1.32)
            if y + alto <= sy + sh and all(measure(l, font)[0] <= sw for l in lineas):
                break
            size = max(typography_plan.minimum_readable_size, int(size * 0.92))
            font, nombre = _font(b.font_role, size)
            lineas = wrap_to_width(b.text, font, sw)

        alto = len(lineas) * int(size * 1.32)
        desborda = (y + alto > sy + sh) or any(measure(l, font)[0] > sw for l in lineas)
        if desborda:
            raise CompositionOverflow(
                f"COMPOSITION_OVERFLOW: el bloque {b.role} no cabe en el area segura "
                f"al tamaño minimo legible ({typography_plan.minimum_readable_size}px). "
                "El texto exacto aprobado NO se acorta, reformula ni reescribe: "
                "la pieza necesita otro formato o decision humana."
            )
        bloques_render.append((b, font, lineas, size, y))
        y += alto + int(size * 0.5)

    for b, font, lineas, size, top in bloques_render:
        color = (252, 250, 242) if b.role == "QUOTE" else (197, 160, 89)
        yy = top
        for linea in lineas:
            draw.text((sx, yy), linea, font=font, fill=color)
            yy += int(size * 1.32)

    # --- marca ---
    brand_applied = False
    estado = COMPOSED
    if brand_plan is not None and brand_plan.get("required"):
        if brand_plan.get("generator_writes_text"):
            # No deberia ocurrir con la politica vigente; si ocurre, no se compone.
            reason_codes.append("BRAND_DELEGATED_TO_GENERATOR")
            estado = NEEDS_HUMAN_REVIEW
        elif reserved_surface is None:
            reason_codes.append("BRAND_SURFACE_NOT_DECLARED")
            warnings.append(
                "la marca exige integracion fisica y no se declaro superficie reservada; "
                "no se compone marca y la pieza requiere revision humana. "
                "No se degrada a watermark ni a logo flotante.")
            estado = NEEDS_HUMAN_REVIEW
        elif not reserved_surface.usable:
            reason_codes.append("BRAND_SURFACE_NOT_FLAT")
            warnings.append(
                "superficie de marca no plana o rotada mas alla del limite de la V1; "
                "no se finge perspectiva. Requiere revision humana.")
            estado = NEEDS_HUMAN_REVIEW
        else:
            texto = brand_plan.get("text") or "LegalMente"
            rs = reserved_surface
            size = max(10, int(rs.height * 0.62))
            font, nombre = _font("brand", size)
            while size > 8 and measure(texto, font)[0] > rs.width:
                size = int(size * 0.92)
                font, nombre = _font("brand", size)
            w, h = measure(texto, font)
            if w > rs.width or h > rs.height:
                reason_codes.append("BRAND_DOES_NOT_FIT")
                warnings.append("la marca no cabe en la superficie reservada declarada.")
                estado = NEEDS_HUMAN_REVIEW
            else:
                bbox = font.getbbox(texto)
                draw.text((rs.x + (rs.width - w) // 2 - bbox[0],
                           rs.y + (rs.height - h) // 2 - bbox[1]),
                          texto, font=font, fill=(197, 160, 89))
                fonts_used["BRAND"] = nombre
                brand_applied = True

    out = io.BytesIO()
    img.save(out, format="PNG", optimize=False)
    composed = out.getvalue()

    from plan import canonical_hash
    tph = canonical_hash(typography_plan.to_dict())
    bph = canonical_hash(brand_plan or {})

    return CompositionResult(
        state=estado,
        raw_sha256=raw_sha,
        composed_sha256=_sha(composed),
        composed_bytes=composed,
        width=img.width, height=img.height,
        typography_plan_hash=tph,
        brand_plan_hash=bph,
        composition_plan_hash=canonical_hash(
            {"t": tph, "b": bph, "v": COMPOSITOR_VERSION,
             "s": (reserved_surface.to_dict() if reserved_surface else None)}),
        fonts_used=fonts_used,
        brand_applied=brand_applied,
        warnings=warnings,
        reason_codes=reason_codes,
    )


def composition_qa(result, raw_bytes, typography_plan, expected_text):
    """QA de composicion. Solo lo comprobable: nada de percepcion semantica."""
    problemas = []
    if not result.composed_bytes:
        problemas.append("no se produjo asset compuesto.")
        return problemas
    if _sha(raw_bytes) != result.raw_sha256:
        problemas.append("el asset en bruto cambio durante la composicion.")
    if result.composed_sha256 == result.raw_sha256:
        problemas.append("el compuesto es identico al bruto: no se compuso nada.")
    if (result.width, result.height) != tuple(typography_plan.canvas):
        problemas.append(
            f"dimensiones del compuesto {result.width}x{result.height} != lienzo del plan "
            f"{typography_plan.canvas}.")
    if expected_text and typography_plan.rendered_text() != " ".join(expected_text.split()):
        problemas.append("el plan no transporta el texto exacto esperado.")
    sx, sy, sw, sh = typography_plan.safe_area
    if sx < 0 or sy < 0 or sx + sw > result.width or sy + sh > result.height:
        problemas.append("el area segura se sale del lienzo.")
    return problemas
