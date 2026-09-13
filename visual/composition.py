"""Planes de composicion posterior: tipografia y marca.

Aqui vive el PLAN (medidas, escalones, cortes, color, jerarquia); el rasterizado
real lo ejecuta `compositor.py` con Pillow (ADR 0003), o un compositor externo
que reciba este mismo plan. La separacion importa: el plan es auditable sin
abrir un solo pixel.

Garantia no negociable: `exact_copy` no se altera jamas para hacer caber el
texto.

Los parametros tipograficos NO se inventan aqui. Vienen del bloque `tipografia`
de la politica visual, que transcribe la seccion §6 de la skill
legalmente-visual-system: zona segura real del feed, escalones de cuerpo por
longitud, maximo de lineas, contraste minimo y color por rol tomado de la paleta
institucional. Antes estaban dispersos como numeros magicos en este archivo y en
el compositor, y habian derivado de lo que la marca tiene aprobado.
"""

from dataclasses import dataclass, field, asdict

LAYOUT_TYPES = {
    "SHORT_QUOTE", "LONG_QUOTE", "LEGAL_CONCEPT", "COMPARISON",
    "MYTH", "AUTHOR_IDEA", "EXPLAINER", "LIST_ITEM",
}

# Umbral de caracteres que separa cita corta de cita larga.
UMBRAL_CITA_CORTA = 90

# Margen seguro como fraccion del lado, SOLO para formatos sin zona segura
# medida en la politica. Nada de texto fuera de esta caja.
SAFE_AREA_RATIO = 0.08

# Piso absoluto de legibilidad en movil, en px sobre el lienzo de 1080 de ancho.
# No es el minimo de cada bloque: cada escalon tipografico trae el suyo, mayor.
MIN_READABLE_PX = 34

# Interlineado y avance entre bloques, en múltiplos del cuerpo.
LINE_HEIGHT = 1.32
BLOQUE_GAP = 0.5


_POLICY_CACHE = None


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
    # Cada bloque trae su propio piso: el cuerpo principal no puede caer al
    # tamaño de un pie de foto solo porque el texto es largo (skill §6).
    min_size_px: int = MIN_READABLE_PX
    max_size_px: int = 0
    color_hex: str = ""          # derivado de la paleta institucional, nunca inventado
    line_height: float = LINE_HEIGHT
    # --- composicion editorial (politica 1.3) ---
    tracking_em: float = 0.0     # espaciado entre letras, en fracciones de cuerpo
    versalitas: bool = False     # se dibuja en mayusculas con tracking abierto
    indent_px: int = 0           # sangria del bloque; la comilla cuelga en ese hueco
    rule_after: bool = False     # filete de laton debajo del bloque


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
    # --- parametros de la skill que el compositor debe respetar y el auditor comprobar ---
    max_lineas: int = 0
    contraste_minimo: float = 0.0
    contraste_ideal: float = 0.0
    detalle_maximo_relativo: float = 0.0
    safe_area_origen: str = ""       # "politica" | "ratio_por_defecto"
    typography_policy_version: str = ""
    # --- composicion editorial (politica 1.3) ---
    anchor: str = "AUTO"             # AUTO | SUPERIOR | INFERIOR
    quotes: tuple = ()               # ("«", "»") si la pieza es una cita
    quote_scale: float = 1.15
    quote_opacity: float = 0.55
    rule_thickness: int = 0
    rule_width: int = 0

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


def _wrap_simple(texto, max_chars):
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


def es_huerfana(lineas):
    """Ultima linea de una sola palabra teniendo mas de una linea: defecto
    tipografico clasico. Arruina el bloque aunque cada linea sea legible."""
    return len(lineas) > 1 and len(lineas[-1].split()) == 1


def _wrap(texto, max_chars, evitar_huerfana=True, max_lineas=0):
    """Corte por palabra completa, reequilibrando la ultima linea.

    Si la ultima linea queda con una sola palabra se reintenta con la caja
    ligeramente mas estrecha (hasta un 30%): el texto NO se toca, solo cambia
    donde cae el corte. Se admite una linea de mas siempre que siga dentro del
    maximo aprobado. Si no hay reparto posible, se devuelve el mejor intento y
    quien audita lo marca — jamas se resuelve acortando la frase.
    """
    lineas = _wrap_simple(texto, max_chars)
    if not evitar_huerfana or not es_huerfana(lineas):
        return lineas
    techo = len(lineas) + 1 if (not max_lineas or len(lineas) < max_lineas) else len(lineas)
    piso = max(8, int(max_chars * 0.70))
    for ancho in range(max_chars - 1, piso - 1, -1):
        cand = _wrap_simple(texto, ancho)
        if len(cand) <= techo and not es_huerfana(cand):
            return cand
    return lineas


def _politica(policy=None):
    """Politica visual vigente. Se carga perezosamente para no obligar a cada
    llamador a pasarla, pero nunca se inventa un valor si falta el bloque."""
    global _POLICY_CACHE
    if policy is not None:
        return policy
    if _POLICY_CACHE is None:
        from brief import VisualPolicy
        _POLICY_CACHE = VisualPolicy.load()
    return _POLICY_CACHE


def safe_area_para(width, height, policy=None):
    """Zona segura real, no un margen inventado.

    La skill mide el recorte del feed SOLO en 9:16 (x 80-1000, y 290-1630 sobre
    1080x1920). Ese rectangulo se escala proporcionalmente a cualquier lienzo de
    la misma relacion. Para el resto de formatos se usa el margen proporcional
    por defecto y se declara el origen: no hay medida de recorte comprobada y no
    se va a fabricar una.
    """
    tip = _politica(policy).data.get("tipografia", {})
    for zona in (tip.get("zona_segura_declarada") or {}).values():
        bw, bh = zona.get("lienzo", [0, 0])
        if bw and bh and abs((width / height) - (bw / bh)) < 0.01:
            ex, ey = width / bw, height / bh
            x, y = int(zona["x"] * ex), int(zona["y"] * ey)
            return (x, y, int(zona["x2"] * ex) - x, int(zona["y2"] * ey) - y), "politica"
    ratio = float(tip.get("zona_segura_ratio_por_defecto", SAFE_AREA_RATIO))
    mx, my = int(width * ratio), int(height * ratio)
    return (mx, my, width - 2 * mx, height - 2 * my), "ratio_por_defecto"


def zona_visible_tras_recorte(width, height, policy=None):
    """Banda que el feed deja ver, escalada al lienzo. None si no hay medida.

    Solo existe para los formatos donde la skill midio el recorte real. Para el
    resto se devuelve None y quien audita lo dice: no hay medida, no hay juicio.
    """
    for fmt in (_politica(policy).data.get("formatos") or {}).values():
        zona = fmt.get("zona_visible_tras_recorte")
        if not zona:
            continue
        bw, bh = fmt.get("width", 0), fmt.get("height", 0)
        if bw and bh and abs((width / height) - (bw / bh)) < 0.01:
            ex, ey = width / bw, height / bh
            return (int(zona["x"] * ex), int(zona["y"] * ey),
                    int(zona["x2"] * ex), int(zona["y2"] * ey))
    return None


def escalon_para(n_caracteres, policy=None):
    """(px_min, px_max, dentro_de_tabla) del bloque principal segun longitud."""
    tip = _politica(policy).data.get("tipografia", {})
    escalones = tip.get("escalones_principal") or []
    for esc in escalones:
        if n_caracteres <= int(esc["max_caracteres"]):
            return int(esc["px_min"]), int(esc["px_max"]), True
    # Fuera de tabla no hay minimo aprobado: se aplica el MAS BAJO de los
    # aprobados (nunca el piso absoluto, que es para pies de foto) y la pieza
    # queda marcada. Degradar en silencio el cuerpo principal a tamaño de
    # leyenda seria resolver un problema de edicion con un defecto de arte.
    if escalones:
        return int(escalones[-1]["px_min"]), int(escalones[-1]["px_max"]), False
    return int(tip.get("piso_absoluto_px", MIN_READABLE_PX)), 82, False


def color_de_rol(rol, policy=None):
    """Color del rol tomado de la PALETA institucional. Sin hexadecimales sueltos."""
    pol = _politica(policy)
    tip = pol.data.get("tipografia", {})
    ref = (tip.get("colores_por_rol") or {}).get(rol)
    if not ref:
        return ""
    tonos = (pol.data.get("paleta", {}).get("requerida", {}) or {}).get(ref.get("paleta"), [])
    idx = int(ref.get("indice", 0))
    return tonos[idx] if idx < len(tonos) else (tonos[0] if tonos else "")


def hex_a_rgb(valor):
    v = str(valor or "").strip().lstrip("#")
    if len(v) != 6:
        return None
    try:
        return tuple(int(v[i:i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        return None


def build_typography_plan(exact_copy, author, width, height, content_type="", context="",
                          policy=None):
    """Plan determinista. `exact_copy` se transporta intacto: se comprueba al final."""
    if exact_copy is None:
        raise ExactCopyViolation("no hay exact_copy que componer.")

    pol = _politica(policy)
    tip = pol.data.get("tipografia", {})
    layout = infer_layout_type(content_type, exact_copy)
    safe, origen_safe = safe_area_para(width, height, pol)

    max_lineas = int(tip.get("max_lineas", 6))
    sec = tip.get("secundario", {}) or {}
    sec_min = int(sec.get("px_min", MIN_READABLE_PX))
    sec_max = int(sec.get("px_max", 44))

    largo = len(exact_copy)
    px_min, px_max, en_tabla = escalon_para(largo, pol)
    warnings = []
    if not en_tabla:
        warnings.append(
            f"el texto principal tiene {largo} caracteres y queda FUERA de la tabla tipografica "
            f"aprobada (maximo declarado: 140). No hay cuerpo minimo aprobado para ese caso: la "
            "pieza necesita decision humana (reencuadre, otro formato o carrusel). "
            "NO se parafrasea ni se reduce el texto.")

    # Escala de referencia: los escalones estan medidos sobre 1080 px de ancho.
    escala = width / 1080.0
    size = max(1, int(px_max * escala))
    piso = max(1, int(px_min * escala))

    # --- recursos de composicion editorial (politica 1.3) ---
    orn = tip.get("ornamentos", {}) or {}
    comillas = tuple()
    if orn.get("comillas_en_citas") and layout in ("SHORT_QUOTE", "LONG_QUOTE"):
        c = orn.get("comillas", {}) or {}
        comillas = (c.get("apertura", "«"), c.get("cierre", "»"))
    filete = orn.get("filete", {}) or {}

    # La comilla de apertura CUELGA EN EL MARGEN, fuera de la columna de texto.
    # Esa es la puntuacion colgante de verdad: el texto conserva toda su medida y
    # la primera linea arranca alineada con las demas. Sangrar el bloque para
    # hacerle sitio (el error de la primera version) estrecha la columna, añade
    # una linea y empuja el resto de la pieza sobre lo que haya debajo.
    def sangria_para(cuerpo):
        return 0

    # Aproximacion tipografica: ~0.52 em de ancho medio por caracter. El
    # compositor vuelve a medir con la metrica real de la fuente.
    def corta(cuerpo):
        util = safe[2] - sangria_para(cuerpo)
        return _wrap(exact_copy, max(8, int(util / (cuerpo * 0.52))), max_lineas=max_lineas)

    alto_reservado = int((sec_max * escala) * 2.6) if author else 0
    alto_disponible = safe[3] - alto_reservado
    lineas = corta(size)
    # Se reduce el cuerpo mientras no quepa o exceda el maximo de lineas. Reducir
    # mete mas caracteres por linea, asi que ambas cosas mejoran a la vez.
    while (len(lineas) * int(size * LINE_HEIGHT) > alto_disponible
           or len(lineas) > max_lineas) and size > piso:
        size = max(piso, int(size * 0.92))
        lineas = corta(size)

    if len(lineas) * int(size * LINE_HEIGHT) > alto_disponible:
        warnings.append(
            "el texto exacto no cabe en el area segura al cuerpo minimo aprobado para su escalon: "
            "requiere revision humana (reencuadre o cambio de formato). NO se parafrasea.")
    if len(lineas) > max_lineas:
        warnings.append(
            f"el bloque principal ocupa {len(lineas)} lineas y el maximo aprobado es {max_lineas}: "
            "decision humana (dividir en carrusel o acortar el texto EN LA FUENTE, nunca aqui).")
    if es_huerfana(lineas):
        warnings.append(
            "la ultima linea del bloque principal queda con una sola palabra (huerfana) y no hay "
            "reparto posible sin tocar el texto: ajustar encuadre o cuerpo en revision humana.")

    sangria = 0
    ancho_cita = safe[2]

    blocks = [TextBlock("QUOTE", exact_copy, "serif_display", size, ancho_cita, lineas,
                        min_size_px=piso, max_size_px=max(1, int(px_max * escala)),
                        color_hex=color_de_rol("QUOTE", pol),
                        tracking_em=float(orn.get("tracking_display_em", 0.0)),
                        indent_px=sangria,
                        rule_after=bool(author and filete.get("visible"))) ]
    if author:
        cuerpo_autor = max(int(sec_min * escala),
                           min(int(sec_max * escala), int(size * 0.42)))
        blocks.append(TextBlock(
            "AUTHOR", author, "sans_caption", cuerpo_autor, safe[2],
            _wrap(author, max(10, int(safe[2] / (cuerpo_autor * 0.52)))),
            min_size_px=int(sec_min * escala), max_size_px=int(sec_max * escala),
            color_hex=color_de_rol("AUTHOR", pol),
            versalitas=bool(orn.get("versalitas_en_autor")),
            tracking_em=float(orn.get("tracking_versalitas_em", 0.0))))
    if context:
        cuerpo_ctx = int(sec_min * escala)
        blocks.append(TextBlock(
            "CONTEXT", context, "sans_caption", cuerpo_ctx, safe[2],
            _wrap(context, max(10, int(safe[2] / (cuerpo_ctx * 0.52)))),
            min_size_px=cuerpo_ctx, max_size_px=int(sec_max * escala),
            color_hex=color_de_rol("CONTEXT", pol)))

    plan = TypographyPlan(
        layout, (width, height), safe, blocks=blocks, warnings=warnings,
        minimum_readable_size=piso if en_tabla else max(1, int(MIN_READABLE_PX * escala)),
        max_lineas=max_lineas,
        contraste_minimo=float(tip.get("contraste_minimo", 0.0)),
        contraste_ideal=float(tip.get("contraste_ideal", 0.0)),
        detalle_maximo_relativo=float(tip.get("detalle_maximo_relativo_bajo_texto", 0.0)),
        safe_area_origen=origen_safe,
        typography_policy_version=pol.version,
        anchor=("AUTO" if orn.get("anclaje_automatico") else "SUPERIOR"),
        quotes=comillas,
        quote_scale=float((orn.get("comillas", {}) or {}).get("escala", 1.15)),
        quote_opacity=float((orn.get("comillas", {}) or {}).get("opacidad", 0.55)),
        rule_thickness=int(filete.get("grosor_px", 0)) if filete.get("visible") else 0,
        rule_width=int(safe[2] * float(filete.get("ancho_relativo", 0.14))))
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
    # --- acabado (politica `marca`) ---
    engraved: bool = True          # grabado con sombra y luz de canto, no texto plano pegado
    text_color_hex: str = ""       # laton viejo de la paleta; nunca un dorado inventado
    contraste_minimo: float = 0.0  # la marca tambien tiene que leerse

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
        engraved=bool(marca.get("acabado_grabado", True)),
        text_color_hex=color_de_rol("LABEL", policy),
        contraste_minimo=float(policy.data.get("tipografia", {}).get("contraste_minimo", 0.0)),
    )
