"""Disciplina de rotacion para lotes — mecanica, no juridica.

Adaptado de material de Drive marcado explicitamente "propuesta editable no
canonica" (protocolo de rotacion forzada v1.1 y reglas operativas v2): solo
se integra lo que es una comprobacion mecanica de variedad visual/tematica.
Nada aqui produce, verifica ni infiere una afirmacion juridica — eso sigue
exigiendo la skill legalmente-legal-verification, sin excepcion.

Dos reglas mecanicas reales:
  1. Entre dos piezas consecutivas, al menos 3 de 5 variables deben cambiar
     (escuela, escenario, mecanismo de revelacion/metafora, encuadre,
     presencia humana) — evita "solo cambie el fondo".
  2. Un lote debe cubrir un minimo de materias, escuelas visuales y
     encuadres distintos — evita que un lote entero use la misma formula.
"""

from dataclasses import dataclass, field

from memory import normaliza

# Los 5 ejes de variacion minima entre piezas consecutivas (Drive: "cambiar
# al menos 3 de 5 variables"). Cada nombre es el atributo real de
# VisualMemoryEntry — no se inventa ningun campo nuevo.
AXES_VARIACION_MINIMA = ("visual_family", "scene_type", "metaphor", "camera_angle", "human_presence")
MINIMO_EJES_CAMBIADOS = 3


def ejes_cambiados(anterior, actual, ejes=AXES_VARIACION_MINIMA):
    """Devuelve el subconjunto de `ejes` cuyo valor normalizado difiere entre
    dos VisualMemoryEntry. Ausencia de dato (campo vacio en ambos) cuenta
    como "sin cambio" — no se puede afirmar variacion sobre un dato ausente."""
    cambiados = set()
    for eje in ejes:
        va = normaliza(getattr(anterior, eje, ""))
        vb = normaliza(getattr(actual, eje, ""))
        if va != vb:
            cambiados.add(eje)
    return cambiados


@dataclass
class VariationCheck:
    ejes_cambiados: set
    minimo_alcanzado: bool
    detalle: str

    def to_dict(self):
        return {"ejes_cambiados": sorted(self.ejes_cambiados),
                "minimo_alcanzado": self.minimo_alcanzado, "detalle": self.detalle}


def verificar_variacion_minima(anterior, actual, minimo=MINIMO_EJES_CAMBIADOS):
    """¿La pieza `actual` cambia lo suficiente frente a la `anterior`
    inmediata? No sustituye a memory.assess() (que mira toda la ventana y
    puntua riesgo): esto es una regla dura de "no solo cambies el fondo"
    para dos piezas consecutivas."""
    if anterior is None:
        return VariationCheck(set(AXES_VARIACION_MINIMA), True,
                               "sin pieza anterior con que comparar: nada que verificar.")
    cambiados = ejes_cambiados(anterior, actual)
    ok = len(cambiados) >= minimo
    detalle = (f"{len(cambiados)}/{len(AXES_VARIACION_MINIMA)} ejes cambiados "
               f"(minimo exigido: {minimo}).")
    return VariationCheck(cambiados, ok, detalle)


@dataclass
class BatchDiversityReport:
    total: int
    materias_distintas: int
    familias_distintas: int
    encuadres_distintos: int
    minimos: dict
    incumplidos: list = field(default_factory=list)

    @property
    def cumple(self):
        return not self.incumplidos

    def to_dict(self):
        return {"total": self.total, "materias_distintas": self.materias_distintas,
                "familias_distintas": self.familias_distintas,
                "encuadres_distintos": self.encuadres_distintos,
                "minimos": dict(self.minimos), "incumplidos": list(self.incumplidos),
                "cumple": self.cumple}


def _distintos(entries, attr):
    return {normaliza(getattr(e, attr, "")) for e in entries if normaliza(getattr(e, attr, ""))}


def assess_batch_diversity(entries, min_materias=None, min_familias=None, min_encuadres=None):
    """Diversidad real de un lote de VisualMemoryEntry ya construidas —
    nunca inventa cuantas materias/familias 'deberian' existir: solo cuenta
    lo que hay. Los minimos por defecto siguen la proporcion del protocolo de
    Drive para un lote de 10 (6 materias, 4 escuelas, 7 encuadres), escalados
    al tamano real del lote — nunca exigidos sobre datos ausentes."""
    n = len(entries)
    if n == 0:
        return BatchDiversityReport(0, 0, 0, 0, {}, ["lote vacio: nada que evaluar."])

    def escala(base_10):
        return max(1, round(base_10 * n / 10))

    minimos = {
        "materias": min_materias if min_materias is not None else escala(6),
        "familias": min_familias if min_familias is not None else escala(4),
        "encuadres": min_encuadres if min_encuadres is not None else escala(7),
    }

    materias = _distintos(entries, "materia")
    familias = _distintos(entries, "visual_family")
    encuadres = _distintos(entries, "camera_angle")

    incumplidos = []
    if materias and len(materias) < minimos["materias"]:
        incumplidos.append(f"materias distintas: {len(materias)} < minimo {minimos['materias']}.")
    if familias and len(familias) < minimos["familias"]:
        incumplidos.append(f"familias visuales distintas: {len(familias)} < minimo {minimos['familias']}.")
    if encuadres and len(encuadres) < minimos["encuadres"]:
        incumplidos.append(f"encuadres distintos: {len(encuadres)} < minimo {minimos['encuadres']}.")

    return BatchDiversityReport(n, len(materias), len(familias), len(encuadres), minimos, incumplidos)
