"""Compositor determinista: RAW ASSET + planes -> COMPOSED ASSET.

Frontera fundamental (mandato §40):

    EL PROVEEDOR POSEE:   la generacion del arte en bruto.
    LEGALMENTE POSEE:     el texto exacto, la marca, la composicion, el QA,
                          los receipts y la historia.

Por eso esto vive aqui y no en Canva, ni en el proveedor, ni en un prompt.
Canva podra ser en el futuro un destino de exportacion; nunca la fuente de verdad.

Dependencia: Pillow (MIT-CMU), la unica del repositorio. Justificada en
docs/adr/0003-dependencia-pillow-compositor.md.

Limites declarados:
- La superficie de marca debe venir DECLARADA: no hay vision que la detecte.
  Puede declararse como rectangulo, como rectangulo con angulo, o como las
  cuatro esquinas reales que tiene en la escena; con las esquinas, la marca
  sigue la perspectiva del objeto en vez de quedar pegada de frente.
- Lo que sigue sin hacerse: deducir esa geometria mirando la imagen, y componer
  sobre una superficie que NO sea un plano (un lacre con relieve, una botella).
- Ante superficie compleja, ausente, no declarada o mal declarada ->
  NEEDS_HUMAN_REVIEW. Nunca degrada a watermark, logo flotante ni firma en una
  esquina.

Detalle artistico que SI se comprueba aqui (skill §6, politica `tipografia`):
- El contraste real entre cada bloque de texto y los pixeles que quedan debajo,
  medido en celdas (WCAG). Por debajo del minimo aprobado la pieza escala a
  revision humana. NUNCA se resuelve pintando una caja opaca detras del texto:
  la skill exige resolverlo con la luz de la propia escena.
- Que ningun bloque de texto caiga sobre la superficie de marca.
- La marca se rasteriza como GRABADO (sombra hundida + luz de canto), no como
  texto plano pegado, y solo si contrasta con su superficie.
"""

import hashlib
import io
from dataclasses import dataclass, field, asdict
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageStat

COMPOSITOR_VERSION = "1.3"

# Rejilla de muestreo del fondo bajo cada bloque de texto. Suficiente para
# detectar una zona clara bajo texto claro; barata y determinista.
CONTRASTE_COLUMNAS = 8
CONTRASTE_FILAS = 4

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

    Debe declararse: no existe deteccion visual en este repositorio. Nada de
    esto se adivina mirando la imagen — lo escribe una persona que sabe donde
    puso la placa.

    Tres formas de declararla, de menos a mas expresiva:

    1. Rectangulo (x, y, width, height): la placa mira a camara.
    2. Rectangulo + `rotation_deg`: la placa esta girada en el plano de la
       imagen. El angulo lo declara un humano, asi que no se finge nada.
    3. `quad`: las cuatro esquinas reales (arriba-izq, arriba-der, abajo-der,
       abajo-izq) de la superficie tal como se ven en la escena. Es lo que
       permite que la marca siga la perspectiva de un lomo, una placa inclinada
       o un umbral visto de lado, en vez de quedar pegada de frente encima.

    `flat=False` significa que la superficie NO es un plano (un lacre con
    relieve, una botella). Un quad describe un plano, asi que declarar las dos
    cosas a la vez es contradictorio y se rechaza: preferimos decirlo a componer
    una marca que se despega del objeto.
    """

    x: int
    y: int
    width: int
    height: int
    flat: bool = True
    rotation_deg: float = 0.0
    quad: tuple = ()          # ((x,y) x4) en orden TL, TR, BR, BL

    def to_dict(self):
        d = asdict(self)
        d["quad"] = [list(p) for p in (self.quad or ())]
        return d

    # --- geometria declarada ---

    @property
    def quad_declarado(self):
        """¿Se intento declarar un plano? Aunque venga mal escrito."""
        return bool(self.quad)

    @property
    def tiene_quad(self):
        return bool(self.quad) and len(self.quad) == 4

    @property
    def quad_valido(self):
        """Cuatro puntos que forman un cuadrilatero convexo con area real.

        Un quad degenerado (puntos repetidos, colineales, o en orden cruzado)
        produciria una transformacion sin solucion o una marca retorcida. Se
        rechaza antes de intentarlo.
        """
        if not self.tiene_quad:
            return False
        try:
            pts = [(float(x), float(y)) for x, y in self.quad]
        except (TypeError, ValueError):
            return False
        if abs(_area_poligono(pts)) < 16:      # menos de 16 px2 no es una placa
            return False
        return _es_convexo(pts)

    @property
    def plano_declarado(self):
        """Las cuatro esquinas sobre las que se compone, vengan de donde vengan.

        Sin quad, el rectangulo (girado si se declaro angulo) es el plano.
        """
        if self.tiene_quad:
            return tuple((float(x), float(y)) for x, y in self.quad)
        return _rect_rotado(self.x, self.y, self.width, self.height, self.rotation_deg)

    @property
    def caja(self):
        """Rectangulo que envuelve al plano declarado."""
        pts = self.plano_declarado
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        return (int(min(xs)), int(min(ys)), int(max(xs)) + 1, int(max(ys)) + 1)

    @property
    def en_perspectiva(self):
        """¿Hace falta deformar, o basta con dibujar de frente?"""
        return self.tiene_quad or abs(self.rotation_deg) > 3.0

    @property
    def usable(self):
        if self.width <= 0 or self.height <= 0:
            return False
        if self.quad_declarado:
            # Un quad describe un plano; con flat=False la declaracion se
            # contradice a si misma. Y un quad mal escrito (tres puntos, area
            # nula, esquinas cruzadas) NO degrada en silencio al rectangulo:
            # alguien quiso declarar un plano y hay que decirle que no vale.
            return self.flat and self.quad_valido
        return self.flat


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
    # Medidas de detalle artistico: contraste real por bloque y de la marca.
    text_contrast: dict = field(default_factory=dict)
    text_busyness: dict = field(default_factory=dict)
    anchor: str = ""
    anchor_metrics: dict = field(default_factory=dict)
    brand_contrast: dict = field(default_factory=dict)

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


def luminancia_relativa(rgb):
    """Luminancia relativa sRGB (WCAG 2.1). Linealiza antes de ponderar."""
    def canal(v):
        v = v / 255.0
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (canal(c) for c in rgb[:3])
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def ratio_contraste(rgb_a, rgb_b):
    """Razon de contraste WCAG entre dos colores. 1.0 = invisible, 21 = maximo."""
    la, lb = luminancia_relativa(rgb_a), luminancia_relativa(rgb_b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def contraste_sobre_region(img, box, color_texto,
                           columnas=CONTRASTE_COLUMNAS, filas=CONTRASTE_FILAS):
    """Contraste del texto contra el fondo REAL, celda a celda.

    Promediar toda la region esconde el caso que arruina la pieza: un texto
    claro legible salvo donde cruza una ventana encendida. Se devuelve el
    minimo por celda, que es el que decide la legibilidad.
    """
    x0, y0, x1, y1 = (int(v) for v in box)
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(img.width, x1), min(img.height, y1)
    if x1 <= x0 or y1 <= y0:
        return None
    cols = max(1, min(columnas, x1 - x0))
    fils = max(1, min(filas, y1 - y0))
    celdas = img.crop((x0, y0, x1, y1)).convert("RGB").resize((cols, fils), Image.BOX)
    px = celdas.load()
    valores = [ratio_contraste(color_texto, px[cx, cy])
               for cy in range(fils) for cx in range(cols)]
    return {"min": round(min(valores), 2),
            "medio": round(sum(valores) / len(valores), 2),
            "celdas": cols * fils}


def energia_de_borde(img, box=None):
    """Densidad de detalle de una region: energia de borde media.

    No es percepcion. No sabe que hay un rostro. Mide cuanta estructura fina
    tiene una zona, que es lo que compite con el texto puesto encima. Un
    degradado fuerte tambien sube el valor: por eso solo escala a revision, y
    la comparacion es SIEMPRE relativa al resto de la imagen, nunca absoluta.
    """
    region = img.crop(box) if box else img
    if region.width < 4 or region.height < 4:
        return None
    gris = region.convert("L")
    # Se submuestrea a lo ancho de una pantalla de movil: el detalle que importa
    # es el que se ve al publicar, no el del pixel.
    if gris.width > 540:
        gris = gris.resize((540, max(1, int(gris.height * 540 / gris.width))), Image.BOX)
    bordes = gris.filter(ImageFilter.FIND_EDGES)
    # El filtro deja un marco artificial en el borde del recorte: se descarta.
    if bordes.width > 6 and bordes.height > 6:
        bordes = bordes.crop((2, 2, bordes.width - 2, bordes.height - 2))
    return round(ImageStat.Stat(bordes).mean[0], 3)


def detalle_relativo(img, box):
    """Cuanto mas cargada esta la region que la imagen entera. 1.0 = igual."""
    region = energia_de_borde(img, box)
    entera = energia_de_borde(img)
    if region is None or not entera:
        return None
    return round(region / entera, 3)


def _solapan(a, b):
    """¿Se cruzan dos rectangulos (x0, y0, x1, y1)?"""
    return not (a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1])


def _tono(rgb, factor):
    """Version mas clara (>1) o mas oscura (<1) del MISMO color institucional.
    No introduce un color nuevo: solo modula el que la paleta ya aprobo."""
    return tuple(max(0, min(255, int(round(c * factor)))) for c in rgb[:3])


# Colores de reserva si el plan no trae color (planes anteriores a la politica
# 1.2). Son EXACTAMENTE los tonos de la paleta institucional: marfil editorial
# para el cuerpo, laton viejo para el resto.
COLOR_RESERVA = {"QUOTE": (252, 250, 242)}
COLOR_RESERVA_OTROS = (197, 160, 89)


def _color_de_bloque(b):
    """Color del bloque: el que declara el plan (derivado de la paleta) o el de
    reserva. Nunca un color inventado en el rasterizador."""
    from composition import hex_a_rgb
    rgb = hex_a_rgb(getattr(b, "color_hex", ""))
    if rgb:
        return rgb
    return COLOR_RESERVA.get(b.role, COLOR_RESERVA_OTROS)


# --- geometria declarada del plano de marca -------------------------------

def _area_poligono(pts):
    """Area con signo (formula del cordon). El signo da la orientacion."""
    n = len(pts)
    return sum(pts[i][0] * pts[(i + 1) % n][1] - pts[(i + 1) % n][0] * pts[i][1]
               for i in range(n)) / 2.0


def _es_convexo(pts):
    """Convexo y sin cruces: todos los productos cruzados con el mismo signo."""
    n, signos = len(pts), set()
    for i in range(n):
        ax, ay = pts[i]
        bx, by = pts[(i + 1) % n]
        cx, cy = pts[(i + 2) % n]
        cruz = (bx - ax) * (cy - by) - (by - ay) * (cx - bx)
        if abs(cruz) < 1e-9:
            continue          # tres puntos alineados: tolerado, no decide
        signos.add(cruz > 0)
    return len(signos) == 1


def _rect_rotado(x, y, w, h, grados):
    """Las cuatro esquinas del rectangulo girado sobre su centro."""
    import math
    cx, cy = x + w / 2.0, y + h / 2.0
    r = math.radians(grados)
    cos, sin = math.cos(r), math.sin(r)
    esquinas = ((x, y), (x + w, y), (x + w, y + h), (x, y + h))
    return tuple((cx + (px - cx) * cos - (py - cy) * sin,
                  cy + (px - cx) * sin + (py - cy) * cos) for px, py in esquinas)


def _resolver(matriz, terminos):
    """Gauss con pivoteo parcial. Devuelve None si el sistema es singular.

    Ocho ecuaciones y ocho incognitas no justifican traer numpy a un repositorio
    que tiene una sola dependencia (ADR 0003), y un sistema singular es
    exactamente la señal de que el quad declarado no describe un plano.
    """
    n = len(matriz)
    m = [fila[:] + [terminos[i]] for i, fila in enumerate(matriz)]
    for col in range(n):
        piv = max(range(col, n), key=lambda r: abs(m[r][col]))
        if abs(m[piv][col]) < 1e-9:
            return None
        m[col], m[piv] = m[piv], m[col]
        for fila in range(n):
            if fila == col:
                continue
            factor = m[fila][col] / m[col][col]
            if factor:
                for k in range(col, n + 1):
                    m[fila][k] -= factor * m[col][k]
    return [m[i][n] / m[i][i] for i in range(n)]


def coeficientes_perspectiva(destino, origen):
    """Coeficientes de PIL.Image.PERSPECTIVE: mapean DESTINO -> ORIGEN.

    Pillow recorre los pixeles de salida y pregunta de donde sacarlos, asi que
    la transformacion se resuelve en ese sentido. `destino` son las cuatro
    esquinas en el lienzo de salida y `origen` las de la capa plana de marca.
    Devuelve None si no hay solucion: el quad no describe un plano.
    """
    filas, terminos = [], []
    for (dx, dy), (sx, sy) in zip(destino, origen):
        filas.append([dx, dy, 1, 0, 0, 0, -dx * sx, -dy * sx])
        terminos.append(sx)
        filas.append([0, 0, 0, dx, dy, 1, -dx * sy, -dy * sy])
        terminos.append(sy)
    return _resolver(filas, terminos)


def dibujar_con_tracking(draw, xy, texto, font, fill, tracking_px):
    """Dibuja letra a letra para abrir el espaciado.

    Pillow no tiene letter-spacing. Las versalitas SIN tracking se cierran y se
    leen como un bloque gris; es el defecto clasico de componer mayusculas. Solo
    se usa en bloques cortos (autor, etiqueta): el cuerpo se dibuja de una vez.
    """
    x, y = xy
    for caracter in texto:
        draw.text((x, y), caracter, font=font, fill=fill)
        x += measure(caracter, font)[0] + tracking_px
    return x - xy[0] - tracking_px


def ancho_con_tracking(texto, font, tracking_px):
    if not texto:
        return 0
    return sum(measure(c, font)[0] for c in texto) + tracking_px * (len(texto) - 1)


def elegir_anclaje(img, safe_area, cajas_relativas, colores, margen=1.12):
    """¿Arriba o abajo? Donde cada bloque se lea, no donde la banda promedie bien.

    Hasta la politica 1.3 el texto caia siempre arriba — por omision, no por
    criterio. Promediar la banda entera tampoco sirve: una banda puede medir
    bien y aun asi dejar el autor justo sobre un rostro. Se evalua cada posicion
    candidata bloque a bloque y gana la que deja PEOR bloque menos malo:
    primero que ninguno caiga sobre la zona cargada, luego el contraste.

    `cajas_relativas` son (desplazamiento_desde_el_inicio, alto) por bloque, en
    el mismo orden que `colores`.
    """
    sx, sy, sw, sh = safe_area
    if not cajas_relativas:
        return "SUPERIOR", {}
    alto_columna = max(d + a for d, a in cajas_relativas)
    candidatos = {"SUPERIOR": sy, "INFERIOR": sy + max(0, sh - alto_columna)}

    evaluacion = {}
    for nombre, y0 in candidatos.items():
        peor_carga, peor_contraste = 0.0, 99.0
        for (desplazamiento, alto), color in zip(cajas_relativas, colores):
            caja = (sx, y0 + desplazamiento, sx + sw, y0 + desplazamiento + alto)
            carga = detalle_relativo(img, caja)
            medida = contraste_sobre_region(img, caja, color)
            if carga is not None:
                peor_carga = max(peor_carga, carga)
            if medida:
                peor_contraste = min(peor_contraste, medida["min"])
        evaluacion[nombre] = {"peor_detalle": round(peor_carga, 3),
                              "peor_contraste": round(peor_contraste, 2)}

    arriba, abajo = evaluacion["SUPERIOR"], evaluacion["INFERIOR"]
    elegido = "SUPERIOR"
    # Menos carga gana; con carga pareja (dentro del margen), decide el contraste.
    if abajo["peor_detalle"] * margen < arriba["peor_detalle"]:
        elegido = "INFERIOR"
    elif arriba["peor_detalle"] * margen >= abajo["peor_detalle"] * margen \
            and abajo["peor_contraste"] > arriba["peor_contraste"] * margen:
        elegido = "INFERIOR"
    return elegido, {"evaluacion": evaluacion, "elegido": elegido}


def _contenido_en(caja, marco):
    """¿El rectangulo `caja` cabe entero dentro de `marco`?"""
    return (caja[0] >= marco[0] and caja[1] >= marco[1]
            and caja[2] <= marco[2] and caja[3] <= marco[3])


def _dibujar_grabado(draw, origen, texto, font, color, size):
    """Marca GRABADA, no pegada.

    Una palabra plana sobre una placa delata el montaje: lo que hace creible una
    marca fisica es el canto. Se dibuja la sombra del corte arriba-izquierda y la
    luz del bisel abajo-derecha, ambas derivadas del MISMO laton de la paleta, y
    encima el relleno. Determinista: el desplazamiento sale del cuerpo de letra.
    """
    x, y = origen
    d = max(1, int(round(size / 28.0)))
    sombra, luz = _tono(color, 0.42), _tono(color, 1.35)
    draw.text((x - d, y - d), texto, font=font, fill=sombra)
    draw.text((x + d, y + d), texto, font=font, fill=luz)
    draw.text((x, y), texto, font=font, fill=color)


def _colocar_en_el_plano(capa, rs):
    """Lleva la capa plana de marca al plano declarado de la escena.

    Devuelve (parche RGBA, esquina donde pegarlo) o None si el plano declarado
    no admite transformacion. El parche se calcula solo sobre la caja del plano,
    no sobre el lienzo entero: no hay motivo para deformar dos millones de
    pixeles para colocar una placa.
    """
    x0, y0, x1, y1 = rs.caja
    ancho, alto = x1 - x0, y1 - y0
    if ancho <= 0 or alto <= 0:
        return None
    destino_local = tuple((px - x0, py - y0) for px, py in rs.plano_declarado)
    origen = ((0, 0), (capa.width, 0), (capa.width, capa.height), (0, capa.height))
    coef = coeficientes_perspectiva(destino_local, origen)
    if coef is None:
        return None
    parche = capa.transform((ancho, alto), Image.PERSPECTIVE, coef,
                            resample=Image.BICUBIC)
    return parche, (x0, y0)


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
    color_filete = (brand_plan or {}).get("text_color_hex", "")
    sx, sy, sw, sh = typography_plan.safe_area
    fonts_used, warnings, reason_codes = {}, list(typography_plan.warnings), []
    contraste_minimo = float(getattr(typography_plan, "contraste_minimo", 0.0) or 0.0)
    contraste_ideal = float(getattr(typography_plan, "contraste_ideal", 0.0) or 0.0)
    umbral_detalle = float(getattr(typography_plan, "detalle_maximo_relativo", 0.0) or 0.0)
    medidas_contraste, medidas_detalle = {}, {}

    # --- tipografia ---
    # Primera pasada: cuerpo definitivo, cortes reales y ALTURA de cada bloque,
    # todavia sin decidir donde empieza la columna. El alto total es lo que
    # permite anclarla arriba o abajo sin recalcular nada.
    y = sy
    bloques_render = []
    for b in typography_plan.blocks:
        size = b.size_px
        # Cada bloque tiene su propio piso aprobado (skill §6): el cuerpo
        # principal no baja al tamaño de un pie de foto para hacer sitio.
        piso = int(getattr(b, "min_size_px", 0) or typography_plan.minimum_readable_size)
        interlineado = float(getattr(b, "line_height", 1.32) or 1.32)
        sangria = int(getattr(b, "indent_px", 0) or 0)
        tracking_em = float(getattr(b, "tracking_em", 0.0) or 0.0)
        versalitas = bool(getattr(b, "versalitas", False))
        ancho_util = sw - sangria
        texto = b.text.upper() if versalitas else b.text
        font, nombre = _font(b.font_role, size)
        fonts_used[b.role] = nombre

        def _corta(f, cuerpo):
            t = int(cuerpo * tracking_em)
            if not t:
                return wrap_to_width(texto, f, ancho_util)
            palabras, lineas_, actual = texto.split(), [], ""
            for w_ in palabras:
                cand = f"{actual} {w_}".strip()
                if ancho_con_tracking(cand, f, t) <= ancho_util or not actual:
                    actual = cand
                else:
                    lineas_.append(actual)
                    actual = w_
            if actual:
                lineas_.append(actual)
            return lineas_

        lineas = _corta(font, size)

        def _cabe(f, cuerpo, ls):
            t = int(cuerpo * tracking_em)
            return all(ancho_con_tracking(l, f, t) <= ancho_util for l in ls)

        # Reduce hasta ese piso; por debajo, desborda y se declara.
        while size > piso:
            alto = len(lineas) * int(size * interlineado)
            if y + alto <= sy + sh and _cabe(font, size, lineas):
                break
            size = max(piso, int(size * 0.92))
            font, nombre = _font(b.font_role, size)
            lineas = _corta(font, size)

        alto = len(lineas) * int(size * interlineado)
        desborda = (y + alto > sy + sh) or not _cabe(font, size, lineas)
        if desborda:
            raise CompositionOverflow(
                f"COMPOSITION_OVERFLOW: el bloque {b.role} no cabe en el area segura "
                f"al cuerpo minimo aprobado para su escalon ({piso}px). "
                "El texto exacto aprobado NO se acorta, reformula ni reescribe: "
                "la pieza necesita otro formato o decision humana."
            )
        bloques_render.append([b, font, lineas, size, y, interlineado, sangria,
                               int(size * tracking_em), versalitas])
        # El filete NO añade altura: se dibuja centrado en el aire que ya existe
        # entre bloques. Un adorno que desplaza el texto sobre un rostro no es
        # un adorno, es un defecto — medido en la primera version de esto.
        y += alto + int(size * 0.5)

    # Segunda pasada: ¿arriba o abajo? La columna entera se desplaza, no se
    # recompone: el corte del texto no depende de donde caiga.
    cajas = [(fila[4] - sy, len(fila[2]) * int(fila[3] * fila[5])) for fila in bloques_render]
    colores_bloque = [_color_de_bloque(fila[0]) for fila in bloques_render]
    alto_columna = max((d + a for d, a in cajas), default=1)
    anclaje = getattr(typography_plan, "anchor", "SUPERIOR") or "SUPERIOR"
    metricas_anclaje = {}
    if anclaje == "AUTO":
        anclaje, metricas_anclaje = elegir_anclaje(
            img, (sx, sy, sw, sh), cajas, colores_bloque,
            margen=float(getattr(typography_plan, "anchor_margin", 0) or 1.12))
    if anclaje == "INFERIOR":
        desplazamiento = max(0, sh - alto_columna)
        for fila in bloques_render:
            fila[4] += desplazamiento

    # --- detalle artistico: contraste real y colision con la marca ---
    # Se mide ANTES de dibujar: lo que decide la legibilidad es el fondo que
    # queda debajo, no el resultado ya pintado.
    # La caja de marca es la del PLANO DECLARADO: con la placa girada o en
    # perspectiva, su rectangulo recto ya no dice donde esta de verdad.
    caja_marca = reserved_surface.caja if reserved_surface is not None else None

    for b, font, lineas, size, top, interlineado, sangria, tracking, versalitas in bloques_render:
        color = _color_de_bloque(b)
        caja = (sx + sangria, top, sx + sw, top + len(lineas) * int(size * interlineado))
        medida = contraste_sobre_region(img, caja, color)
        carga = detalle_relativo(img, caja)
        if carga is not None:
            medidas_detalle[b.role] = carga
            if umbral_detalle and carga > umbral_detalle:
                reason_codes.append("TEXT_OVER_BUSY_AREA")
                warnings.append(
                    f"el bloque {b.role} cae sobre la parte mas cargada de la escena "
                    f"({carga}x el detalle medio de la imagen). Ahi es donde suelen estar el "
                    "rostro, las manos o el objeto de la revelacion, y la regla vigente prohibe "
                    "poner texto encima. La medida no reconoce que hay debajo: lo mira una persona.")
        if medida:
            medidas_contraste[b.role] = medida
            if contraste_minimo and medida["min"] < contraste_minimo:
                reason_codes.append("TEXT_CONTRAST_BELOW_MINIMUM")
                warnings.append(
                    f"el bloque {b.role} cae sobre un fondo que deja un contraste minimo de "
                    f"{medida['min']}:1, por debajo del {contraste_minimo}:1 exigido. "
                    "No se pinta caja opaca detras del texto (prohibido): el contraste se "
                    "resuelve con la luz de la escena, asi que la pieza necesita revision humana.")
            elif contraste_ideal and medida["min"] < contraste_ideal:
                warnings.append(
                    f"el bloque {b.role} cumple el minimo pero no el contraste ideal "
                    f"({medida['min']}:1 frente a {contraste_ideal}:1).")
        if caja_marca and _solapan(caja, caja_marca):
            reason_codes.append("TEXT_OVER_BRAND_SURFACE")
            warnings.append(
                f"el bloque {b.role} se superpone a la superficie de marca declarada; la regla "
                "vigente prohibe texto sobre el objeto de marca. No se desplaza el texto por "
                "cuenta propia: lo decide una persona.")

    # Capa de ornamentos: comillas y filete van con opacidad, y eso exige RGBA.
    ornamentos = Image.new("RGBA", img.size, (0, 0, 0, 0))
    dibujo_orn = ImageDraw.Draw(ornamentos)

    for b, font, lineas, size, top, interlineado, sangria, tracking, versalitas in bloques_render:
        color = _color_de_bloque(b)
        yy = top
        texto_lineas = [l.upper() for l in lineas] if versalitas else lineas
        for linea in texto_lineas:
            if tracking:
                dibujar_con_tracking(draw, (sx + sangria, yy), linea, font, color, tracking)
            else:
                draw.text((sx + sangria, yy), linea, font=font, fill=color)
            yy += int(size * interlineado)

        # Comillas de cita: la de apertura CUELGA en la sangria, la de cierre
        # sigue al final de la ultima linea. Nunca se tocan las letras del texto.
        if b.role == "QUOTE" and typography_plan.quotes:
            abre, cierra = typography_plan.quotes
            cuerpo_comilla = max(8, int(size * float(typography_plan.quote_scale or 1.0)))
            fuente_comilla, _ = _font("serif_display", cuerpo_comilla)
            alfa = int(255 * float(typography_plan.quote_opacity or 1.0))
            tinta = _color_de_bloque(b) + (alfa,)
            caja_abre = fuente_comilla.getbbox(abre)
            ancho_abre = caja_abre[2] - caja_abre[0]
            # Cuelga hacia el margen; si el margen no da, se apoya en el borde de
            # la columna en vez de salirse de lo que el feed deja ver.
            from composition import zona_visible_tras_recorte
            visible = zona_visible_tras_recorte(img.width, img.height)
            limite = (visible[0] if visible else 0) + 4
            x_abre = max(limite, sx - ancho_abre - int(size * 0.10))
            dibujo_orn.text((x_abre - caja_abre[0], top - caja_abre[1] + int(size * 0.12)),
                            abre, font=fuente_comilla, fill=tinta)
            fin_x = sx + sangria + measure(texto_lineas[-1], font)[0] + int(size * 0.12)
            ultima_y = top + (len(texto_lineas) - 1) * int(size * interlineado)
            caja_cierra = fuente_comilla.getbbox(cierra)
            dibujo_orn.text((fin_x - caja_cierra[0], ultima_y - caja_cierra[1] + int(size * 0.12)),
                            cierra, font=fuente_comilla, fill=tinta)

        # Filete de laton: separa la cita de su autor sin caja, que es lo unico
        # que la marca permite.
        if getattr(b, "rule_after", False) and typography_plan.rule_thickness:
            base = top + len(lineas) * int(size * interlineado) + int(size * 0.25)
            laton = _color_de_bloque(b) if b.role != "QUOTE" else COLOR_RESERVA_OTROS
            from composition import hex_a_rgb
            laton = hex_a_rgb(color_filete) or laton
            dibujo_orn.rectangle(
                [sx + sangria, base, sx + sangria + typography_plan.rule_width,
                 base + typography_plan.rule_thickness - 1],
                fill=laton + (235,))

    img = Image.alpha_composite(img.convert("RGBA"), ornamentos).convert("RGB")
    draw = ImageDraw.Draw(img)

    # --- marca ---
    brand_applied = False
    brand_contrast = {}
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
                from composition import hex_a_rgb, zona_visible_tras_recorte
                color = hex_a_rgb(brand_plan.get("text_color_hex")) or COLOR_RESERVA_OTROS
                caja_rs = rs.caja

                # La marca tambien tiene que LEERSE sobre su superficie. Si no
                # contrasta, no se recolorea por cuenta propia (el laton viejo
                # es paleta aprobada): la escena tiene que cambiar.
                medida = contraste_sobre_region(img, caja_rs, color, columnas=4, filas=2)
                if medida:
                    brand_contrast = medida
                    minimo = float(brand_plan.get("contraste_minimo") or 0.0)
                    if minimo and medida["min"] < minimo:
                        reason_codes.append("BRAND_CONTRAST_BELOW_MINIMUM")
                        warnings.append(
                            f"la marca queda a {medida['min']}:1 sobre su superficie, por debajo "
                            f"del {minimo}:1 exigido: sobre ese material no se lee. No se cambia "
                            "el color de marca ni se añade caja; lo decide una persona.")
                        estado = NEEDS_HUMAN_REVIEW

                # Lo que el feed recorta no existe. Si la superficie de marca cae
                # fuera de la banda visible, la integracion fisica se pierde.
                visible = zona_visible_tras_recorte(img.width, img.height)
                if visible and not _contenido_en(caja_rs, visible):
                    reason_codes.append("BRAND_SURFACE_OUTSIDE_VISIBLE_AREA")
                    warnings.append(
                        "la superficie de marca cae total o parcialmente fuera de la banda que el "
                        "feed deja ver: la marca puede quedar recortada. Reencuadre humano.")

                # La marca se compone SIEMPRE sobre una capa plana propia y
                # luego se lleva al plano declarado. Asi el grabado se calcula
                # una sola vez y la perspectiva no es un caso aparte: cuando la
                # placa mira a camara, la transformacion es la identidad.
                capa = Image.new("RGBA", (rs.width, rs.height), (0, 0, 0, 0))
                bbox = font.getbbox(texto)
                origen_local = ((rs.width - w) // 2 - bbox[0], (rs.height - h) // 2 - bbox[1])
                dibujo_capa = ImageDraw.Draw(capa)
                if brand_plan.get("engraved", True):
                    _dibujar_grabado(dibujo_capa, origen_local, texto, font, color, size)
                else:
                    dibujo_capa.text(origen_local, texto, font=font, fill=color)

                if not rs.en_perspectiva:
                    img.paste(capa, (rs.x, rs.y), capa)
                    brand_applied = True
                else:
                    colocada = _colocar_en_el_plano(capa, rs)
                    if colocada is None:
                        reason_codes.append("BRAND_SURFACE_NOT_FLAT")
                        warnings.append(
                            "las cuatro esquinas declaradas para la marca no describen un plano: "
                            "no hay transformacion posible y no se finge una. Revision humana.")
                        estado = NEEDS_HUMAN_REVIEW
                    else:
                        parche, destino = colocada
                        img.paste(parche, destino, parche)
                        brand_applied = True

                if brand_applied:
                    fonts_used["BRAND"] = nombre

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
        reason_codes=sorted(set(reason_codes)),
        text_contrast=medidas_contraste,
        text_busyness=medidas_detalle,
        anchor=anclaje,
        anchor_metrics=metricas_anclaje,
        brand_contrast=brand_contrast,
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
