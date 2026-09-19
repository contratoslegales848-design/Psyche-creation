"""QA de LOTE para huellas visuales — Fases 6-7 del mandato "Súper Prompt"
(Founder, 16-sep-2026).

`batch_qa.py` ya evalúa el lote como sistema sobre el fingerprint EDITORIAL
de 22 campos (materia, familia_editorial, necesidad, ángulo, emoción...) —
ese módulo no se toca ni se duplica aquí. Este módulo cubre un eje distinto
y nuevo: el lote de 10 sobre las 10 dimensiones del `VisualFingerprint` del
catálogo maestro (Fase 4), que `batch_qa.py` no conoce. Reutiliza
`distancia()` de `visual_fingerprint.py` — la misma lógica de comparación
por valor normalizado, no una copia.

Reglas del mandato (Fase 7), escaladas al tamaño real del lote igual que
`batch_qa.py` hace con sus propios mínimos:
- al menos 7/10 huellas distintas entre sí (no la "misma sesión con diez
  disfraces").
- al menos 5/10 medios/familias (categorías del catálogo) distintos.
- máximo 2 piezas por medio/familia.
- ninguna dimensión dominante (primary_direction, composition, lighting,
  palette) se repite en dos piezas CONSECUTIVAS del lote.
- cada pieza difiere de la inmediatamente anterior en al menos 4
  dimensiones (re-verificación de sistema — `seleccionar_huella()` ya lo
  exige al construir cada huella; esto detecta el caso de un lote
  ensamblado por otra vía, sin pasar por esa función).
"""

from dataclasses import dataclass, field

import visual_fingerprint as vf
from memory import normaliza
from visual_fingerprint import DIMENSIONES_HUELLA, MIN_DIMENSIONES_DIFERENTES_CONSECUTIVAS, distancia

MAX_INTENTOS_LOTE = 8

ACEPTADO, RECHAZADO = "ACEPTADO", "RECHAZADO"

MIN_HUELLAS_DISTINTAS_10 = 7
MIN_MEDIOS_DISTINTOS_10 = 5
MAX_POR_MEDIO_10 = 2

DIMENSIONES_SIN_REPETICION_CONSECUTIVA = ("primary_direction", "composition", "lighting", "palette")


def _frecuencias(fps, dimension):
    out = {}
    for f in fps:
        v = normaliza(f.valor(dimension))
        if v:
            out[v] = out.get(v, 0) + 1
    return dict(sorted(out.items(), key=lambda kv: (-kv[1], kv[0])))


def _firma(f):
    """Tupla normalizada de las 10 dimensiones — dos huellas con la misma
    firma son la misma pieza con otro content_id, no una huella distinta."""
    return tuple(normaliza(f.valor(d)) for d in DIMENSIONES_HUELLA)


@dataclass
class LoteVisualQAReport:
    veredicto: str = RECHAZADO
    total: int = 0
    incumplimientos: list = field(default_factory=list)
    telemetria: dict = field(default_factory=dict)

    @property
    def aceptado(self):
        return self.veredicto == ACEPTADO

    def to_dict(self):
        return {"veredicto": self.veredicto, "total": self.total,
                "incumplimientos": list(self.incumplimientos),
                "telemetria": dict(self.telemetria)}


def evaluar_lote_visual(fingerprints, objetivo=None):
    fps = list(fingerprints)
    n = len(fps)
    if n == 0:
        return LoteVisualQAReport(RECHAZADO, 0, ["lote vacío: nada que evaluar."])

    objetivo = int(objetivo or n)
    escala = n / 10.0

    def minimo(base_10):
        return max(1, round(base_10 * escala))

    incumplimientos = []

    # --- 1. huellas distintas entre sí ---
    firmas = {_firma(f) for f in fps}
    if len(firmas) < minimo(MIN_HUELLAS_DISTINTAS_10):
        incumplimientos.append(
            f"solo {len(firmas)}/{n} huellas son realmente distintas entre sí "
            f"(mínimo {minimo(MIN_HUELLAS_DISTINTAS_10)}) — el lote se repite a sí mismo.")

    # --- 2/3. medios/familias: cobertura mínima y tope por medio ---
    frec_medio = _frecuencias(fps, "medium")
    if len(frec_medio) < minimo(MIN_MEDIOS_DISTINTOS_10):
        incumplimientos.append(
            f"solo {len(frec_medio)} medios/familias distintos en el lote "
            f"(mínimo {minimo(MIN_MEDIOS_DISTINTOS_10)}).")
    tope_medio = minimo(MAX_POR_MEDIO_10)
    for medio, cuenta in frec_medio.items():
        if cuenta > tope_medio:
            incumplimientos.append(
                f"medio {medio!r} aparece {cuenta} veces (tope {tope_medio}): sobreexplotación.")

    # --- 4. sin repetición consecutiva en dimensiones dominantes ---
    for dim in DIMENSIONES_SIN_REPETICION_CONSECUTIVA:
        for a, b in zip(fps, fps[1:]):
            va, vb = normaliza(a.valor(dim)), normaliza(b.valor(dim))
            if va and vb and va == vb:
                incumplimientos.append(
                    f"{dim}: repetición consecutiva entre {a.content_id!r} y "
                    f"{b.content_id!r} ({va!r}).")

    # --- 5. distancia mínima vs. la pieza inmediatamente anterior ---
    for a, b in zip(fps, fps[1:]):
        distintas, conocidas = distancia(a, b)
        if conocidas >= len(DIMENSIONES_HUELLA) and distintas < MIN_DIMENSIONES_DIFERENTES_CONSECUTIVAS:
            incumplimientos.append(
                f"{a.content_id!r} -> {b.content_id!r}: solo {distintas}/{conocidas} "
                f"dimensiones distintas (mínimo {MIN_DIMENSIONES_DIFERENTES_CONSECUTIVAS}).")

    if n < objetivo:
        incumplimientos.append(
            f"lote incompleto: {n}/{objetivo}. No se rellena con candidatos débiles; "
            "amplía la reserva y regenera.")

    telemetria = {
        "huellas_distintas": len(firmas),
        "medios_distintos": len(frec_medio),
        "frecuencia_medio": frec_medio,
        "frecuencia_primary_direction": _frecuencias(fps, "primary_direction"),
        "frecuencia_lighting": _frecuencias(fps, "lighting"),
        "frecuencia_composition": _frecuencias(fps, "composition"),
        "frecuencia_palette": _frecuencias(fps, "palette"),
    }

    veredicto = ACEPTADO if not incumplimientos else RECHAZADO
    return LoteVisualQAReport(veredicto, n, incumplimientos, telemetria)


def generar_lote_visual(content_ids, catalogo=None, memoria_previa=None, canal="",
                        max_intentos=MAX_INTENTOS_LOTE):
    """Construye un lote completo y lo regenera (nunca lo rellena) hasta que
    pase `evaluar_lote_visual` o se agoten los intentos — mismo criterio que
    `batch_qa.py`: "rechazar significa regenerar, nunca rellenar con
    candidatos débiles sólo para llegar a diez". Si `memoria_previa` trae
    historial real (piezas ya publicadas), se respeta como punto de partida
    para que el lote nuevo tampoco repita contra lo ya usado.

    Devuelve (lote, reporte, intentos_usados). Si no converge, el lote y el
    reporte son los del último intento — RECHAZADO explícito, para revisión
    humana, nunca un lote que se cuela sin evaluar."""
    catalogo = catalogo or vf.MasterCatalog.load()
    ids = list(content_ids)
    lote, reporte, intentos_usados = [], None, 0
    for intento in range(max_intentos):
        intentos_usados = intento + 1
        memoria = vf.FingerprintMemory()
        if memoria_previa is not None:
            for e in memoria_previa.recientes():
                memoria.record(e.content_id, e.fingerprint, canal=e.canal)
        lote = []
        for cid in ids:
            semilla_id = cid if intento == 0 else f"{cid}#intento{intento}"
            h = vf.seleccionar_huella(semilla_id, catalogo=catalogo, memoria=memoria, canal=canal)
            h.content_id = cid
            memoria.record(cid, h, canal=canal)
            lote.append(h)
        reporte = evaluar_lote_visual(lote, objetivo=len(ids))
        if reporte.aceptado:
            break
    return lote, reporte, intentos_usados
