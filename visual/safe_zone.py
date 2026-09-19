"""Safe zone multiformato 9:16 -> 4:5 (Founder, 17-sep-2026, tarea 78).

Regla canónica: "9:16 visualmente amplio; 4:5 semánticamente completo."

Toda pieza maestra `VERTICAL_9_16` (1080x1920) debe seguir siendo semántica
y visualmente completa si una superficie (Facebook u otra) le aplica un
recorte CENTRAL `SOCIAL_4_5` (1080x1350). Esto NO es "generar dos
versiones": el asset maestro sigue siendo 9:16 — lo que cambia es la
arquitectura de composición: el contenido indispensable vive dentro de una
safe zone interior al área que sobrevive al recorte, y la zona exterior se
usa activamente como expansión artística (atmósfera, profundidad, puesta en
escena), nunca como "sujeto centrado + fondo vacío".

GEOMETRÍA: se deriva SIEMPRE de `policy.formato()` — `VERTICAL_9_16` y
`SOCIAL_4_5` ya están declarados en `legalmente-visual-policy-v1.json`.
Ningún número de canvas/crop se repite aparte aquí; sólo el padding interno
(también declarado en la política, `safe_zone.padding_interno_ratio`) es
propio de este módulo, y existe precisamente porque distintas superficies no
garantizan recortar exactamente igual — el margen es deliberadamente
conservador, nunca el borde exacto del crop.

CLASIFICACIÓN ESENCIAL/DECORATIVO: reutiliza los campos YA declarados de
`brief.VisualBrief` — no crea un segundo modelo de "elementos de la escena".
`subject`/`focal_point`/`metaphor`/`acento_objeto` son, por su propia
definición en `brief.py`, lo que la pieza comunica; `environment`/`camera`/
`negative_space`/`key_light`/`brightness_intent` son, también por su propia
definición, atmósfera/puesta en escena — exactamente la distinción que pide
el mandato ("actor/objeto/documento focal" vs. "atmósfera... iluminación...
profundidad"). `marca_superficie` se trata como esencial SOLO cuando la
política exige integración física de marca (mismo criterio que
`composition.build_brand_plan`).

QA: no existen coordenadas ni bounding boxes reales para la escena que
genera el proveedor de imagen (no hay visión por computadora en este
repositorio — mismo límite honesto que `compositor.py` declara para la
superficie de marca). `crop_safe_4_5()` por tanto NO inventa precisión
geométrica sobre la escena: opera sobre la representación semántica REAL que
el sistema sí controla — el texto declarado de cada campo del brief — con el
mismo patrón de coincidencia por patrones de riesgo, consciente de negación,
que ya usa `memoria_fuerte.py` para los 7 rechazos del Founder. Un campo
ESENCIAL cuyo texto declara una ubicación de riesgo (extremo superior,
extremo inferior, fuera del recorte) FALLA; el mismo texto en un campo
DECORATIVO no falla nunca — ahí es exactamente donde debe vivir.
"""

from dataclasses import dataclass, asdict

from memory import normaliza_texto_libre as _texto_libre

FORMATO_MAESTRO = "VERTICAL_9_16"

# Campos de VisualBrief cuyo propio significado (ver brief.py) los vuelve
# indispensables para que la pieza se entienda — deben sobrevivir el recorte.
CAMPOS_ESENCIALES = ("subject", "focal_point", "metaphor", "acento_objeto")

# Campos cuyo propio significado es atmósfera/puesta en escena — pueden
# vivir en la extensión superior/inferior que el recorte 4:5 elimina.
CAMPOS_DECORATIVOS = ("environment", "camera", "negative_space", "key_light",
                      "brightness_intent")

# Patrones de riesgo de zona (mandato §"ANTI-PATRONES A BLOQUEAR"), en el
# mismo espíritu que `memoria_fuerte.REGLAS_RECHAZO_FOUNDER`: frases REALES
# tomadas literalmente del mandato, nunca inferidas. `_texto_libre` (no
# `memory.normaliza`) porque varias frases usan "/" o números pegados a
# texto ("250-300 px") que `normaliza` colapsaría a cadena vacía — el mismo
# bug ya documentado en `direccion_causal.py`.
PATRONES_RIESGO_ZONA = {
    "EXTREMO_SUPERIOR": (
        "pegado arriba", "parte superior extrema", "borde superior",
        "extremo superior", "tercio superior extremo", "franja superior",
        "arriba del todo", "titulo pegado arriba",
    ),
    "EXTREMO_INFERIOR": (
        "tercio inferior extremo", "borde inferior", "extremo inferior",
        "parte inferior extrema", "ultimos 250 px", "ultimos 300 px",
        "franja inferior", "abajo del todo",
    ),
    "FUERA_DE_CROP": (
        "fuera del recorte", "fuera del encuadre 4:5", "fuera del crop",
        "fuera de la zona segura", "desaparece en el recorte",
        "desaparece en 4:5", "no visible en el recorte",
    ),
}


class SafeZoneError(ValueError):
    pass


@dataclass(frozen=True)
class SafeZoneGeometry:
    """Geometría en px, canvas maestro con origen (0,0) arriba-izquierda."""

    canvas_width: int
    canvas_height: int
    crop_width: int
    crop_height: int
    crop_top: int          # y donde empieza el recorte central
    crop_bottom: int        # y donde termina el recorte central
    safe_top: int           # y donde empieza la safe zone (con padding interno)
    safe_bottom: int        # y donde termina la safe zone
    padding_interno_px: int
    padding_interno_ratio: float

    @property
    def crop_offset_top(self):
        return self.crop_top

    @property
    def crop_offset_bottom(self):
        return self.canvas_height - self.crop_bottom

    @property
    def safe_height(self):
        return self.safe_bottom - self.safe_top

    def to_dict(self):
        return asdict(self)


def calcular_geometria(policy, formato_maestro=FORMATO_MAESTRO, formato_crop=None,
                       padding_ratio=None):
    """Deriva la geometría del recorte central desde los formatos YA
    declarados en `policy` — nunca números propios aparte de aquí. Recorte
    CENTRAL: mismo ancho, alto reducido simétricamente arriba/abajo."""
    maestro = policy.formato(formato_maestro)
    formato_crop = formato_crop or maestro.get("crop_safe_for")
    if not formato_crop:
        raise SafeZoneError(
            f"{formato_maestro!r} no declara 'crop_safe_for' en la política: "
            "no hay recorte compatible que calcular.")
    crop = policy.formato(formato_crop)

    if maestro["width"] != crop["width"]:
        raise SafeZoneError(
            f"el recorte {formato_crop!r} no comparte ancho con {formato_maestro!r}: "
            "un recorte central 4:5 sólo reduce el alto, nunca el ancho.")
    if crop["height"] > maestro["height"]:
        raise SafeZoneError(
            f"{formato_crop!r} ({crop['height']}px de alto) es más alto que "
            f"{formato_maestro!r} ({maestro['height']}px): no es un recorte.")

    if padding_ratio is None:
        padding_ratio = policy.data.get("safe_zone", {}).get("padding_interno_ratio", 0.06)

    sobra = maestro["height"] - crop["height"]
    offset = sobra // 2  # recorte CENTRAL: mismo margen arriba y abajo
    crop_top = offset
    crop_bottom = offset + crop["height"]
    padding_px = int(crop["height"] * padding_ratio)

    return SafeZoneGeometry(
        canvas_width=maestro["width"], canvas_height=maestro["height"],
        crop_width=crop["width"], crop_height=crop["height"],
        crop_top=crop_top, crop_bottom=crop_bottom,
        safe_top=crop_top + padding_px, safe_bottom=crop_bottom - padding_px,
        padding_interno_px=padding_px, padding_interno_ratio=padding_ratio)


def instruccion_compilada(geometria):
    """Frase determinista para el prompt compilado (compiler.py) —
    representación estructurada (la geometría) traducida a UNA frase, no un
    texto libre inventado en cada llamada."""
    return (
        f"Componer nativamente para {geometria.canvas_width}x{geometria.canvas_height} "
        f"completo aprovechando la verticalidad, pero mantener TODO el contenido "
        f"semánticamente esencial (título, concepto jurídico, objeto o documento focal, "
        f"metáfora principal, marca cuando corresponda) dentro del área central segura "
        f"entre los píxeles {geometria.safe_top} y {geometria.safe_bottom} desde arriba "
        f"(equivalente al recorte {geometria.crop_width}x{geometria.crop_height}, con margen "
        f"interno conservador). Usar la extensión superior (0-{geometria.crop_top}px) e "
        f"inferior ({geometria.crop_bottom}-{geometria.canvas_height}px) sólo para atmósfera, "
        f"profundidad y expansión visual no indispensable — nunca para el mensaje jurídico."
    )


def _clasificar_texto(texto, patrones):
    hallazgos = []
    t = _texto_libre(texto)
    if not t:
        return hallazgos
    for categoria, frases in patrones.items():
        for frase in frases:
            frase_norm = _texto_libre(frase)
            if frase_norm and frase_norm in t:
                hallazgos.append((categoria, frase))
    return hallazgos


def crop_safe_4_5(brief, policy=None, geometria=None):
    """QA estructural/semántico (no visión por computadora — ver docstring
    del módulo): FAIL si algún campo ESENCIAL del brief declara una
    ubicación de riesgo; PASS si sólo aparecen en campos decorativos o no
    aparecen. `(ok, reason_codes, detalle)`.

    Si el `formato` del brief no declara `crop_safe_for` en la política, la
    regla NO APLICA (nunca se fuerza un formato distinto al pedido
    explícitamente — mandato: 'no cambies por tu cuenta la regla de
    selección de formato solicitada por el Founder')."""
    reason_codes = []
    fmt = None
    if policy is not None:
        try:
            fmt = policy.formato(brief.formato)
        except Exception:
            fmt = None

    aplica = bool(fmt and fmt.get("crop_safe_for")) if policy is not None else True
    if not aplica:
        return True, [], {
            "aplica": False,
            "motivo": f"formato {brief.formato!r} no declara crop_safe_for: la regla no aplica.",
        }

    hallazgos_esenciales = {}
    for campo in CAMPOS_ESENCIALES:
        texto = getattr(brief, campo, "") or ""
        hallazgos = _clasificar_texto(texto, PATRONES_RIESGO_ZONA)
        if hallazgos:
            hallazgos_esenciales[campo] = hallazgos
            for categoria, frase in hallazgos:
                reason_codes.append(
                    f"CAMPO_ESENCIAL_EN_ZONA_DE_RIESGO: '{campo}' declara {categoria} "
                    f"(coincide con {frase!r}) — el contenido indispensable no puede "
                    "depender de una zona que el recorte 4:5 puede eliminar.")

    # Marca: esencial SOLO si la política exige integración física (mismo
    # criterio que composition.build_brand_plan).
    marca_requerida = bool(policy.data.get("marca", {}).get("integracion_fisica_requerida")) \
        if policy is not None else False
    if marca_requerida:
        texto = getattr(brief, "marca_superficie", "") or ""
        hallazgos = _clasificar_texto(texto, PATRONES_RIESGO_ZONA)
        if hallazgos:
            hallazgos_esenciales["marca_superficie"] = hallazgos
            for categoria, frase in hallazgos:
                reason_codes.append(
                    f"MARCA_EN_ZONA_DE_RIESGO: 'marca_superficie' declara {categoria} "
                    f"(coincide con {frase!r}) — LegalMente no puede desaparecer en el "
                    "recorte 4:5.")

    hallazgos_decorativos = {}
    for campo in CAMPOS_DECORATIVOS:
        texto = getattr(brief, campo, "") or ""
        hallazgos = _clasificar_texto(texto, PATRONES_RIESGO_ZONA)
        if hallazgos:
            hallazgos_decorativos[campo] = hallazgos

    ok = not hallazgos_esenciales
    detalle = {
        "aplica": True,
        "geometria": geometria.to_dict() if geometria is not None else None,
        "campos_esenciales_en_riesgo": hallazgos_esenciales,
        "campos_decorativos_en_extension": hallazgos_decorativos,
        "nota": ("QA estructural sobre texto declarado, no visión por computadora: no hay "
                "bounding boxes reales para la escena generada por el proveedor. Un campo "
                "decorativo en la extensión NO es un fallo — es exactamente para eso."),
    }
    return ok, reason_codes, detalle
