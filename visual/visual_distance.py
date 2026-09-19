"""Distancia visual estricta — 8 dimensiones, mínimo 5 cambiadas, 3 vecinos por ámbito.

Hueco encontrado al reconciliar contra `legalmente-web`
(`src/lib/production-policy/index.ts`, función `productionVisualDistance` +
el bucle de `validateProductionBatch` que revisa los 3 vecinos más cercanos
en CADA ámbito — lote e historial — por separado). `memory.py` de este repo
puntúa riesgo de repetición (0-100, ponderado), pero no exige un mínimo duro
de dimensiones cambiadas ni compara contra AMBOS ámbitos con evidencia
completa exigida. Este módulo cierra ese hueco con implementación propia en
Python — mismo principio verificado, sin copiar el TypeScript.

Las 8 dimensiones (mapeadas 1:1 a `memory.VisualMemoryEntry`, para no crear
un tercer vocabulario donde ya existen dos):

    visual_family · scene_type · metaphor · material (dominant_materials)
    · lighting_type · human_presence · cámara+encuadre combinados
    · brand_surface

FAIL-CLOSED: si una comparación no tiene las 8 dimensiones con dato en AMBOS
lados, es EVIDENCIA INCOMPLETA — nunca pasa por omisión. Si tiene las 8 pero
menos de 5 cambiaron, es DISTANCIA INSUFICIENTE. Ambos son motivo de rechazo,
igual que en la rama ChatGPT.
"""

from dataclasses import dataclass, field

from memory import normaliza

DIMENSIONES = ("visual_family", "scene_type", "metaphor", "material",
              "lighting_type", "human_presence", "camara_encuadre", "brand_surface")

MINIMO_DIMENSIONES_CONOCIDAS = 8
MINIMO_DIMENSIONES_CAMBIADAS = 5
VECINOS_POR_AMBITO = 3


def _valor_dimension(entry, dim):
    if dim == "material":
        return "|".join(sorted(normaliza(m) for m in (entry.dominant_materials or []) if normaliza(m)))
    if dim == "camara_encuadre":
        a, b = normaliza(entry.camera_angle), normaliza(entry.shot_distance)
        return f"{a}|{b}" if a and b else ""
    return normaliza(getattr(entry, dim, ""))


def distancia_estricta(a, b):
    """(dimensiones_cambiadas, dimensiones_conocidas) entre dos
    VisualMemoryEntry. Sólo cuenta dimensiones con dato en AMBOS lados."""
    cambiadas = conocidas = 0
    for dim in DIMENSIONES:
        va, vb = _valor_dimension(a, dim), _valor_dimension(b, dim)
        if va and vb:
            conocidas += 1
            if va != vb:
                cambiadas += 1
    return cambiadas, conocidas


@dataclass
class ComparacionVisual:
    content_id: str = ""
    comparado_id: str = ""
    ambito: str = ""             # LOTE | HISTORIA
    cambiadas: int = 0
    conocidas: int = 0

    @property
    def evidencia_incompleta(self):
        return self.conocidas < MINIMO_DIMENSIONES_CONOCIDAS

    @property
    def distancia_insuficiente(self):
        return not self.evidencia_incompleta and self.cambiadas < MINIMO_DIMENSIONES_CAMBIADAS

    @property
    def problema(self):
        if self.evidencia_incompleta:
            return (f"{self.content_id}: evidencia visual incompleta frente a "
                    f"{self.comparado_id} ({self.ambito}) — {self.conocidas}/8 dimensiones "
                    "con dato en ambos lados.")
        if self.distancia_insuficiente:
            return (f"{self.content_id}: distancia visual frente a {self.comparado_id} "
                    f"({self.ambito}) es {self.cambiadas}/8 (mínimo {MINIMO_DIMENSIONES_CAMBIADAS}).")
        return ""

    def to_dict(self):
        d = {"content_id": self.content_id, "comparado_id": self.comparado_id,
             "ambito": self.ambito, "cambiadas": self.cambiadas, "conocidas": self.conocidas,
             "evidencia_incompleta": self.evidencia_incompleta,
             "distancia_insuficiente": self.distancia_insuficiente}
        return d


def vecinos_mas_cercanos(entry, poblacion, n=VECINOS_POR_AMBITO):
    """Los `n` más parecidos (menos dimensiones cambiadas primero). Empates
    por content_id para ser determinista."""
    candidatos = [o for o in poblacion if o is not entry and
                 getattr(o, "content_id", None) != getattr(entry, "content_id", None)]
    calculadas = [(distancia_estricta(entry, o), o) for o in candidatos]
    calculadas.sort(key=lambda t: (t[0][0], t[1].content_id))
    return calculadas[:n]


@dataclass
class VerificacionLote:
    comparaciones: list = field(default_factory=list)   # ComparacionVisual con problema
    total_revisadas: int = 0

    @property
    def problemas(self):
        return [c.problema for c in self.comparaciones]

    @property
    def ok(self):
        return not self.comparaciones

    def to_dict(self):
        return {"ok": self.ok, "total_revisadas": self.total_revisadas,
                "problemas": self.problemas}


def verificar_lote_contra_historia(entries_lote, historia=(), n_vecinos=VECINOS_POR_AMBITO):
    """Para cada pieza del lote, revisa sus `n_vecinos` más cercanos en CADA
    ámbito (LOTE e HISTORIA) por separado — un historial grande no puede
    esconder una repetición dentro del propio lote, ni al revés."""
    problemas, total = [], 0
    for i, entry in enumerate(entries_lote):
        resto_lote = [e for j, e in enumerate(entries_lote) if j != i]
        for ambito, poblacion in (("LOTE", resto_lote), ("HISTORIA", list(historia))):
            for (cambiadas, conocidas), otro in vecinos_mas_cercanos(entry, poblacion, n_vecinos):
                total += 1
                comp = ComparacionVisual(content_id=entry.content_id, comparado_id=otro.content_id,
                                         ambito=ambito, cambiadas=cambiadas, conocidas=conocidas)
                if comp.problema:
                    problemas.append(comp)
    return VerificacionLote(comparaciones=problemas, total_revisadas=total)
