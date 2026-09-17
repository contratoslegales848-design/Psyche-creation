"""Diversidad de arquetipo compositivo — Regla 3 del banco artístico
anterior ("HOTFIX — DISTANCIA VISUAL Y ANTI-MONOTONÍA", Drive, 8-sep-2026):

    "No más de 3 piezas del mismo arquetipo compositivo. Arquetipos a
    vigilar: objeto sobre superficie, retrato/persona frontal, documento en
    close-up, pasillo/arquitectura central, bodegón, escena de escritorio."

Este eje es DISTINTO del que ya cubre `visual_distance.py` (8 dimensiones
de la huella/memoria) — dos piezas pueden diferir en escuela, luz, material
y encuadre (pasar `visual_distance`) y AUN ASÍ compartir el mismo patrón
compositivo de fondo (p. ej. "un documento sobre una superficie", una y
otra vez). Es exactamente el hallazgo que el banco anterior documentó:
"la variedad se juzga en las imágenes, no en los nombres de técnicas."

QA estructural sobre texto declarado (`subject`/`environment` del
`VisualBrief` real), mismo patrón de coincidencia por palabras clave que
`memoria_fuerte.py`/`safe_zone.py` — nunca visión por computadora, nunca
se inventa una clasificación sin evidencia léxica (cae a SIN_CLASIFICAR).

CONTINUACIÓN (17-sep-2026, 4ª pasada — "no cierres todavía"): el Founder
señaló que "3 escritorios + 3 documentos" puede seguir siendo un lote
perceptualmente monótono aunque cada arquetipo individual respete su tope.
El banco anterior ya lo advertía en su propia Regla 9
("Revisión del lote como portafolio", HOTFIX 8-sep-2026): "Ver las 10
juntas y detectar familias visuales accidentales. Si 4 o más se sienten de
la misma sesión fotográfica, misma exposición, misma paleta, misma escala
o mismo decorado, sustituir las más débiles aunque individualmente hayan
pasado QA." Esta sección añade DOS controles de afinidad complementarios
(nunca sustituyen los de arriba, se suman):

    `verificar_afinidad_familias()`   — agrupa arquetipos perceptualmente
                                        cercanos (p. ej. documento-en-
                                        close-up y escena-de-escritorio
                                        son ambos "interior institucional
                                        con papel") y aplica un tope
                                        COMBINADO más estricto que la
                                        suma de topes individuales.
    `verificar_redundancia_ambientacion()` — eje DISTINTO del arquetipo
                                        (composición): vocabulario de
                                        ambientación compartido en
                                        `environment` (p. ej. "archivo"
                                        apareciendo en 3-4 de 10 piezas
                                        aunque sus arquetipos individuales
                                        sean distintos — hallazgo real de
                                        esta pasada, ver docs).
"""

from dataclasses import dataclass, field

from memory import normaliza_texto_libre as _texto_libre

DOCUMENTO_CLOSEUP = "DOCUMENTO_CLOSEUP"
ESCENA_ESCRITORIO = "ESCENA_ESCRITORIO"
PASILLO_ARQUITECTURA_CENTRAL = "PASILLO_ARQUITECTURA_CENTRAL"
RETRATO_PERSONA_FRONTAL = "RETRATO_PERSONA_FRONTAL"
BODEGON = "BODEGON"
OBJETO_SOBRE_SUPERFICIE = "OBJETO_SOBRE_SUPERFICIE"
SIN_CLASIFICAR = "SIN_CLASIFICAR"

MAX_POR_ARQUETIPO_DEFAULT = 3

# Orden de evaluación: el primero que coincide decide — de más específico
# (documento/mesa de reunión/arquitectura/retrato) a más genérico (objeto
# sobre superficie), para no clasificar por accidente una escena de
# negociación como "documento" solo porque hay papeles sobre la mesa.
_PALABRAS_ESCENA_ESCRITORIO = (
    "sala de negociacion", "sala de reuniones", "sala de juntas",
    "sala de conciliacion", "mesa redonda", "sillas frente a frente",
    "sillas enfrentadas", "despacho",
)
_PALABRAS_PASILLO_ARQUITECTURA = (
    "pasillo", "corredor", "vitrina", "museo", "archivo con estantes",
    "gabinete", "biblioteca",
)
_PALABRAS_RETRATO_PERSONA = (
    "retrato", "rostro", "persona de pie", "figura humana completa",
)
_PALABRAS_DOCUMENTO_CLOSEUP = (
    "documento", "clausula", "carta", "pagina", "escritura", "formulario",
    "diccionario", "tratado", "mensaje", "propuesta", "recibo", "acta",
    "contrato", "estatuto", "testamentaria", "libreta", "libro de actas",
)
_PALABRAS_BODEGON = (
    "varios objetos", "conjunto de objetos", "frascos alineados",
    "instrumental", "herramientas",
)
_PALABRAS_OBJETO_SUPERFICIE = (
    "una placa", "un sello", "una balanza", "un objeto", "sobre la mesa",
    "apoyado", "reposa",
)


def _contiene_alguna(texto_normalizado, frases):
    return any(_texto_libre(f) in texto_normalizado for f in frases)


def clasificar_arquetipo(subject, environment=""):
    """Determinista, basado en coincidencia léxica sobre `subject` (con
    `environment` como apoyo para escenas de mesa/arquitectura). Sin
    evidencia clara, SIN_CLASIFICAR — nunca se adivina."""
    s = _texto_libre(subject)
    e = _texto_libre(environment)
    combinado = f"{s} {e}"

    if _contiene_alguna(combinado, _PALABRAS_ESCENA_ESCRITORIO):
        return ESCENA_ESCRITORIO, "subject/environment describen una mesa de reunión o negociación."
    if _contiene_alguna(e, _PALABRAS_PASILLO_ARQUITECTURA):
        return PASILLO_ARQUITECTURA_CENTRAL, "environment describe un espacio arquitectónico central."
    if _contiene_alguna(s, _PALABRAS_RETRATO_PERSONA):
        return RETRATO_PERSONA_FRONTAL, "subject describe una figura humana frontal."
    if _contiene_alguna(s, _PALABRAS_DOCUMENTO_CLOSEUP):
        return DOCUMENTO_CLOSEUP, "subject centra la escena en un documento o texto escrito."
    if _contiene_alguna(s, _PALABRAS_BODEGON):
        return BODEGON, "subject describe varios objetos dispuestos juntos."
    if _contiene_alguna(s, _PALABRAS_OBJETO_SUPERFICIE):
        return OBJETO_SOBRE_SUPERFICIE, "subject describe un solo objeto sobre una superficie."
    return SIN_CLASIFICAR, "sin coincidencia léxica clara con ningún arquetipo vigilado."


@dataclass
class VerificacionArquetipos:
    conteo: dict = field(default_factory=dict)
    detalle: dict = field(default_factory=dict)         # content_id -> (arquetipo, razon)
    max_por_arquetipo: int = MAX_POR_ARQUETIPO_DEFAULT

    @property
    def excedidos(self):
        return {a: n for a, n in self.conteo.items()
                if a != SIN_CLASIFICAR and n > self.max_por_arquetipo}

    @property
    def ok(self):
        return not self.excedidos

    def to_dict(self):
        return {"ok": self.ok, "conteo": dict(self.conteo), "excedidos": self.excedidos,
                "detalle": {k: list(v) for k, v in self.detalle.items()},
                "max_por_arquetipo": self.max_por_arquetipo}


def verificar_diversidad_arquetipos(piezas, max_por_arquetipo=MAX_POR_ARQUETIPO_DEFAULT):
    """`piezas`: iterable de (content_id, subject, environment). Regla 3:
    no más de `max_por_arquetipo` piezas del mismo arquetipo en un lote —
    SIN_CLASIFICAR nunca cuenta contra el tope (no hay evidencia de
    repetición si no se pudo clasificar)."""
    conteo, detalle = {}, {}
    for content_id, subject, environment in piezas:
        arquetipo, razon = clasificar_arquetipo(subject, environment)
        conteo[arquetipo] = conteo.get(arquetipo, 0) + 1
        detalle[content_id] = (arquetipo, razon)
    return VerificacionArquetipos(conteo=conteo, detalle=detalle, max_por_arquetipo=max_por_arquetipo)


# --- Afinidad entre arquetipos cercanos (Regla 9 del banco anterior) ------
# Agrupación real, auditable contra la propia definición de cada arquetipo:
# "documento en close-up" y "escena de escritorio" son ambos interiores
# institucionales centrados en papel/mobiliario de oficina; "pasillo/
# arquitectura central" comparte el mismo registro (interior formal,
# vitrinas/archivos/corredores). "objeto sobre superficie" y "bodegón" son
# ambos composiciones de objeto(s) aislado(s) sin escena humana ni
# arquitectura. RETRATO_PERSONA_FRONTAL y SIN_CLASIFICAR no se agrupan: no
# hay evidencia de que compartan registro perceptual con ningún otro.
FAMILIAS_PERCEPTUALES = {
    "INTERIOR_INSTITUCIONAL": (DOCUMENTO_CLOSEUP, ESCENA_ESCRITORIO, PASILLO_ARQUITECTURA_CENTRAL),
    "OBJETO_AISLADO": (OBJETO_SOBRE_SUPERFICIE, BODEGON),
}

# Regla 9 literal: "si 4 o más se sienten de la misma sesión... sustituir
# las más débiles". El tope de familia es ese mismo umbral — más estricto
# que la suma de los topes individuales de sus arquetipos miembro.
MAX_POR_FAMILIA_DEFAULT = 4


def _familia_de(arquetipo):
    for familia, miembros in FAMILIAS_PERCEPTUALES.items():
        if arquetipo in miembros:
            return familia
    return None


@dataclass
class VerificacionFamilias:
    conteo: dict = field(default_factory=dict)
    detalle: dict = field(default_factory=dict)          # content_id -> (arquetipo, familia)
    max_por_familia: int = MAX_POR_FAMILIA_DEFAULT

    @property
    def excedidas(self):
        return {f: n for f, n in self.conteo.items() if n > self.max_por_familia}

    @property
    def ok(self):
        return not self.excedidas

    def to_dict(self):
        return {"ok": self.ok, "conteo": dict(self.conteo), "excedidas": self.excedidas,
                "detalle": {k: list(v) for k, v in self.detalle.items()},
                "max_por_familia": self.max_por_familia}


def verificar_afinidad_familias(piezas, max_por_familia=MAX_POR_FAMILIA_DEFAULT):
    """Complementa `verificar_diversidad_arquetipos`: agrupa arquetipos
    perceptualmente cercanos (`FAMILIAS_PERCEPTUALES`) y aplica un tope
    COMBINADO — un lote puede tener 3 `DOCUMENTO_CLOSEUP` + 3
    `ESCENA_ESCRITORIO` (ambos dentro de su propio tope de 3) y aun así
    sentirse monótono si los 6 son "interior institucional con papel"; este
    chequeo lo atrapa. Arquetipos sin familia declarada (retrato, sin
    clasificar) no se agrupan ni cuentan aquí."""
    conteo, detalle = {}, {}
    for content_id, subject, environment in piezas:
        arquetipo, _ = clasificar_arquetipo(subject, environment)
        familia = _familia_de(arquetipo)
        if familia is None:
            continue
        conteo[familia] = conteo.get(familia, 0) + 1
        detalle[content_id] = (arquetipo, familia)
    return VerificacionFamilias(conteo=conteo, detalle=detalle, max_por_familia=max_por_familia)


# --- Redundancia de vocabulario de ambientación ---------------------------
# Eje DISTINTO del arquetipo compositivo (cómo se compone la toma): aquí se
# vigila QUÉ TIPO DE LUGAR describe `environment`, por vocabulario real
# repetido — puede haber dos piezas de arquetipos distintos (una
# DOCUMENTO_CLOSEUP, otra ESCENA_ESCRITORIO) que aun así comparten la
# palabra "archivo"/"archivadores" en su entorno. Hallazgo real de esta
# pasada: 4 de las 10 piezas del lote real mencionaban archivo/archivador
# en su `environment` pese a tener arquetipos distintos.
FAMILIAS_AMBIENTACION = {
    "ARCHIVO": ("archivo", "archivador"),
    "DESPACHO_OFICINA": ("despacho", "oficina"),
    "SALA_DE_REUNION": ("sala de reuniones", "sala de juntas", "sala de negociacion",
                        "sala de conciliacion"),
    "LABORATORIO": ("laboratorio",),
    "MUSEO_VITRINA": ("museo", "vitrina"),
    "TERRENO_EXTERIOR": ("terreno", "borde de un terreno"),
}

MAX_POR_AMBIENTACION_DEFAULT = 3


def _familia_ambientacion(environment):
    e = _texto_libre(environment)
    if not e:
        return None
    for familia, frases in FAMILIAS_AMBIENTACION.items():
        if _contiene_alguna(e, frases):
            return familia
    return None


@dataclass
class VerificacionAmbientacion:
    conteo: dict = field(default_factory=dict)
    detalle: dict = field(default_factory=dict)          # content_id -> familia
    max_por_familia: int = MAX_POR_AMBIENTACION_DEFAULT

    @property
    def excedidas(self):
        return {f: n for f, n in self.conteo.items() if n > self.max_por_familia}

    @property
    def ok(self):
        return not self.excedidas

    def to_dict(self):
        return {"ok": self.ok, "conteo": dict(self.conteo), "excedidas": self.excedidas,
                "detalle": dict(self.detalle), "max_por_familia": self.max_por_familia}


def verificar_redundancia_ambientacion(piezas, max_por_familia=MAX_POR_AMBIENTACION_DEFAULT):
    """`piezas`: iterable de (content_id, environment). Sin coincidencia
    léxica con `FAMILIAS_AMBIENTACION`, la pieza no cuenta contra ningún
    tope (nunca se adivina un tipo de lugar sin evidencia textual)."""
    conteo, detalle = {}, {}
    for content_id, environment in piezas:
        familia = _familia_ambientacion(environment)
        if familia is None:
            continue
        conteo[familia] = conteo.get(familia, 0) + 1
        detalle[content_id] = familia
    return VerificacionAmbientacion(conteo=conteo, detalle=detalle, max_por_familia=max_por_familia)
