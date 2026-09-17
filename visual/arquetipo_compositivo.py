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
