"""QA del LOTE como sistema — P0 del Handoff §8.

"No validar únicamente pieza por pieza. Evaluar las 10 COMO SISTEMA. Si el
lote parece 'la misma sesión con diez disfraces': RECHAZARLO Y REGENERAR."

`rotation.assess_batch_diversity()` ya mide tres ejes VISUALES (materias,
familias visuales, encuadres). Este módulo NO lo sustituye: lo invoca y le
añade las capas que faltaban — semántica, editorial y emocional — más la
telemetría que pide el Handoff §14.

El veredicto es RECHAZADO o ACEPTADO. Rechazar significa REGENERAR, nunca
rellenar: "nunca rellenar un lote con candidatos débiles sólo para llegar a
diez".

Nada aquí aprueba contenido jurídico ni abre un gate. Mide variedad.
"""

from dataclasses import dataclass, field

import rotation
from memory import normaliza
from semantic_fingerprint import EJES_SEMANTICOS

BATCH_QA_SCHEMA_VERSION = "1.0"

ACEPTADO, RECHAZADO = "ACEPTADO", "RECHAZADO"

# Mínimos para un lote de 10, escalados al tamaño real ("00 LEER PRIMERO" §3.A:
# preferir 8-10 materias/familias distintas; máximo 2 de una misma materia).
MIN_MATERIAS_10 = 8
MIN_FAMILIAS_EDITORIALES_10 = 8
MIN_NECESIDADES_10 = 5
MIN_ANGULOS_10 = 5
MIN_EMOCIONES_10 = 4
MAX_POR_MATERIA_10 = 2
# Distancia semántica mínima entre las dos piezas más parecidas del lote.
MIN_DISTANCIA_PAR = 0.30
MIN_DISTANCIA_MEDIA = 0.55


def _cuenta(fps, eje):
    return {normaliza(getattr(f, eje, "")) for f in fps if normaliza(getattr(f, eje, ""))}


def _frecuencias(fps, eje):
    out = {}
    for f in fps:
        v = normaliza(getattr(f, eje, ""))
        if v:
            out[v] = out.get(v, 0) + 1
    return dict(sorted(out.items(), key=lambda kv: (-kv[1], kv[0])))


@dataclass
class BatchQAReport:
    veredicto: str = RECHAZADO
    total: int = 0
    incumplimientos: list = field(default_factory=list)
    avisos: list = field(default_factory=list)
    telemetria: dict = field(default_factory=dict)
    diversidad_visual: dict = field(default_factory=dict)
    pares_mas_proximos: list = field(default_factory=list)
    schema_version: str = BATCH_QA_SCHEMA_VERSION

    @property
    def aceptado(self):
        return self.veredicto == ACEPTADO

    def to_dict(self):
        return {"veredicto": self.veredicto, "total": self.total,
                "incumplimientos": list(self.incumplimientos),
                "avisos": list(self.avisos), "telemetria": dict(self.telemetria),
                "diversidad_visual": dict(self.diversidad_visual),
                "pares_mas_proximos": list(self.pares_mas_proximos),
                "schema_version": self.schema_version}


def evaluar_lote(fingerprints, objetivo=None, memoria=None, regeneraciones=0,
                 seleccionadas=None):
    """Evalúa el lote como sistema y devuelve veredicto + telemetría."""
    fps = list(fingerprints)
    n = len(fps)
    if n == 0:
        return BatchQAReport(RECHAZADO, 0, ["lote vacío: nada que evaluar."])

    objetivo = int(objetivo or n)
    escala = n / 10.0

    def minimo(base_10):
        return max(1, round(base_10 * escala))

    incumplimientos, avisos = [], []

    # --- diversidad temática y editorial ---
    ejes_min = {
        "materia": minimo(MIN_MATERIAS_10),
        "familia_editorial": minimo(MIN_FAMILIAS_EDITORIALES_10),
        "necesidad": minimo(MIN_NECESIDADES_10),
        "angulo": minimo(MIN_ANGULOS_10),
        "emocion": minimo(MIN_EMOCIONES_10),
    }
    distintos = {}
    for eje, minimo_exigido in ejes_min.items():
        vals = _cuenta(fps, eje)
        distintos[eje] = len(vals)
        if not vals:
            # FAIL-CLOSED. No basta con avisar: si nadie declara el eje, el lote
            # NO puede acreditar diversidad en él, y un lote sin evidencia no se
            # aprueba. Es la misma doctrina que inventory.py ("ausencia de dato
            # != cero ni PASS"). Antes de esta regla, diez huellas vacías
            # obtenían ACEPTADO porque ningún control llegaba a dispararse.
            incumplimientos.append(
                f"{eje}: ningún elemento lo declara. No se puede acreditar diversidad "
                "sobre un dato ausente, y la ausencia de evidencia no es un aprobado.")
        elif len(vals) < minimo_exigido:
            incumplimientos.append(
                f"{eje}: {len(vals)} distintos < mínimo {minimo_exigido} para un lote de {n}.")

    # --- sobreexplotación de una materia ---
    frec_materia = _frecuencias(fps, "materia")
    tope = minimo(MAX_POR_MATERIA_10)
    for mat, cuenta in frec_materia.items():
        if cuenta > tope:
            incumplimientos.append(
                f"materia {mat!r} aparece {cuenta} veces (tope {tope}): sobreexplotación.")

    # --- distancia semántica por pares ---
    pares = []
    for i in range(n):
        for j in range(i + 1, n):
            d = fps[i].distancia_semantica(fps[j])
            if d.comparable:
                pares.append((d.valor, fps[i].content_id, fps[j].content_id))
    pares.sort()
    if pares:
        d_min = pares[0][0]
        d_media = round(sum(p[0] for p in pares) / len(pares), 4)
        if d_min < MIN_DISTANCIA_PAR:
            incumplimientos.append(
                f"dos piezas del lote están a distancia semántica {d_min} "
                f"(< {MIN_DISTANCIA_PAR}): {pares[0][1]} y {pares[0][2]} son el mismo "
                "contenido con otra ropa.")
        if d_media < MIN_DISTANCIA_MEDIA:
            incumplimientos.append(
                f"distancia semántica media {d_media} < {MIN_DISTANCIA_MEDIA}: el lote se "
                "siente como la misma sesión con disfraces distintos.")
    else:
        d_min = d_media = None
        incumplimientos.append(
            "ningún par de huellas era comparable: el lote no aporta ninguna evidencia "
            "de diversidad semántica. Ausencia de dato no es un aprobado.")

    # --- capa visual: se reutiliza el motor existente, no se duplica ---
    entries = [f.visual_entry() for f in fps]
    visual = rotation.assess_batch_diversity(entries)
    if not visual.cumple:
        incumplimientos.extend(f"[visual] {x}" for x in visual.incumplidos)

    pares_visuales = []
    for i in range(n):
        for j in range(i + 1, n):
            dv = fps[i].distancia_visual(fps[j])
            if dv.comparable:
                pares_visuales.append(dv.valor)
    visual_distance = round(sum(pares_visuales) / len(pares_visuales), 4) if pares_visuales else None

    # --- telemetría (Handoff §14) ---
    cooldown_age = None
    if memoria is not None:
        distancias = [memoria.evaluar(f).distancia for f in fps]
        cooldown_age = round(sum(distancias) / len(distancias), 4) if distancias else None

    selection_rate = None
    if seleccionadas is not None and n:
        selection_rate = round(len(seleccionadas) / n, 4)

    # topic_repetition: fracción de pares por debajo del umbral de equivalencia.
    topic_repetition = round(
        sum(1 for p in pares if p[0] < MIN_DISTANCIA_PAR) / len(pares), 4) if pares else None

    telemetria = {
        "selection_rate": selection_rate,
        "semantic_distance_min": d_min,
        "semantic_distance_media": d_media,
        "topic_repetition": topic_repetition,
        "family_coverage": round(distintos.get("familia_editorial", 0) / n, 4),
        "matter_coverage": round(distintos.get("materia", 0) / n, 4),
        "emotional_rotation": round(distintos.get("emocion", 0) / n, 4),
        "visual_distance": visual_distance,
        "style_frequency": _frecuencias(fps, "direccion_artistica"),
        "composition_frequency": _frecuencias(fps, "composicion"),
        "cooldown_age": cooldown_age,
        "regeneration_rate": round(regeneraciones / max(1, objetivo), 4),
        "distintos": distintos,
        "frecuencia_materia": frec_materia,
    }

    if n < objetivo:
        incumplimientos.append(
            f"lote incompleto: {n}/{objetivo}. No se rellena con candidatos débiles; "
            "amplía la reserva y regenera.")

    veredicto = ACEPTADO if not incumplimientos else RECHAZADO
    return BatchQAReport(veredicto, n, incumplimientos, avisos, telemetria,
                         visual.to_dict(), pares[:3])
