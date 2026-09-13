"""Saturación editorial — Fase 2: un control DISTINTO de la repetición semántica.

El Founder es explícito: son dos preguntas distintas y no deben compartir
score.

    REPETICIÓN SEMÁNTICA (`semantic_memory.SemanticMemory.evaluar`)
        ¿YA DIJIMOS SUSTANCIALMENTE ESTO? — mira el CONTENIDO: materia,
        concepto, pregunta resuelta. Compara contra TODO (incluida
        HISTORICA): el corpus entero es lo que "ya dijimos".

    SATURACIÓN EDITORIAL (este módulo)
        ¿ESTAMOS USANDO DEMASIADO LA MISMA MANERA DE CONTAR? — mira la
        FUNCIÓN: familia editorial y necesidad. Compara sólo contra
        producción RECIENTE (GENERADA/PRESELECCIONADA/APROBADA/PUBLICADA),
        nunca contra HISTORICA completa — si contara el corpus histórico
        entero, "caso_cotidiano" (48% del banco v3) quedaría saturado para
        siempre, y el mandato es corregir el sesgo hacia delante, no
        congelarlo como prohibición perpetua.

Una pieza puede ser jurídicamente NUEVA (otra materia, otro concepto, otra
pregunta — repetición semántica baja) y aun así estar SATURADA (la familia
editorial "caso_cotidiano" ya apareció tres veces en las últimas diez piezas
producidas). El mandato dice explícitamente: eso pudo ser uno de los
problemas históricos principales, y debe poder rechazar un candidato aunque
sea semánticamente nuevo.

Determinista, sin ML, misma disciplina que memory.py: el score se recalcula a
mano y se explica en una frase.
"""

from dataclasses import dataclass, field

from memory import normaliza

# Estados que cuentan como "producción reciente". HISTORICA queda fuera
# deliberadamente (ver docstring del módulo); DESCARTADA también: un rechazo
# del Founder no es lo mismo que "hemos insistido demasiado en esta función".
ESTADOS_RECIENTES = ("GENERADA", "PRESELECCIONADA", "APROBADA", "PUBLICADA")

VENTANA_SATURACION = 30

PESO_FAMILIA = 70
PESO_NECESIDAD = 30
MAX_OCURRENCIAS_ANTES_DE_SATURAR = 3

UMBRAL_ALTO = 60
UMBRAL_MEDIO = 30

# Nivel a partir del cual la saturación se convierte en HARD GATE — rechazo,
# no penalización. Ver generator.py (Fase 7).
NIVEL_BLOQUEA = "ALTO"


@dataclass
class SaturationAssessment:
    score: int = 0
    nivel: str = "BAJO"                 # BAJO | MEDIO | ALTO
    ocurrencias_familia: int = 0
    ocurrencias_necesidad: int = 0
    ventana_evaluada: int = 0
    razones: list = field(default_factory=list)

    @property
    def bloquea(self):
        return self.nivel == NIVEL_BLOQUEA

    def to_dict(self):
        return {"score": self.score, "nivel": self.nivel,
                "ocurrencias_familia": self.ocurrencias_familia,
                "ocurrencias_necesidad": self.ocurrencias_necesidad,
                "ventana_evaluada": self.ventana_evaluada,
                "bloquea": self.bloquea, "razones": list(self.razones)}


def _ventana_reciente(memoria, ventana):
    recientes = [e for e in memoria.entries() if e.estado in ESTADOS_RECIENTES]
    return recientes[:ventana]


def evaluar(familia_editorial, necesidad, memoria, ventana=VENTANA_SATURACION):
    """Riesgo de saturación editorial de (familia_editorial, necesidad)
    frente a la producción reciente en `memoria`."""
    recientes = _ventana_reciente(memoria, ventana)
    if not recientes:
        return SaturationAssessment(0, "BAJO", 0, 0, 0,
                                    ["sin producción reciente con qué comparar."])

    fam = normaliza(familia_editorial)
    nec = normaliza(necesidad)

    n_fam = sum(1 for e in recientes
               if normaliza(e.fingerprint.get("familia_editorial", "")) == fam) if fam else 0
    n_nec = sum(1 for e in recientes
               if normaliza(e.fingerprint.get("necesidad", "")) == nec) if nec else 0

    score = 0
    razones = []
    if fam and n_fam:
        score += min(PESO_FAMILIA, PESO_FAMILIA * n_fam // MAX_OCURRENCIAS_ANTES_DE_SATURAR)
        razones.append(f"familia editorial {familia_editorial!r} usada {n_fam} de las "
                       f"últimas {len(recientes)} piezas producidas.")
    if nec and n_nec:
        score += min(PESO_NECESIDAD, PESO_NECESIDAD * n_nec // MAX_OCURRENCIAS_ANTES_DE_SATURAR)
        razones.append(f"necesidad {necesidad!r} usada {n_nec} de las últimas "
                       f"{len(recientes)} piezas producidas.")

    score = min(100, score)
    nivel = "ALTO" if score >= UMBRAL_ALTO else "MEDIO" if score >= UMBRAL_MEDIO else "BAJO"
    if not razones:
        razones.append("ni la familia ni la necesidad coinciden con la producción reciente.")
    return SaturationAssessment(score, nivel, n_fam, n_nec, len(recientes), razones)


def distribucion_reciente(memoria, ventana=VENTANA_SATURACION, eje="familia_editorial"):
    """Frecuencias del eje pedido en la ventana reciente. Para mostrar en
    informes: qué tan concentrada está la producción de los últimos N."""
    recientes = _ventana_reciente(memoria, ventana)
    out = {}
    for e in recientes:
        v = normaliza(e.fingerprint.get(eje, ""))
        if v:
            out[v] = out.get(v, 0) + 1
    return dict(sorted(out.items(), key=lambda kv: (-kv[1], kv[0])))
