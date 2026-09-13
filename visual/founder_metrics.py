"""Founder Selection Rate — Fase 10.

    FOUNDER SELECTION RATE = seleccionadas / generadas

es el KPI crítico de producción (ya lo declaraba el Handoff original). Este
módulo lo desglosa por eje editorial, con una regla que el mandato pide en
mayúsculas: "NO sacar conclusiones fuertes con muestras pequeñas". Cada fila
lleva su tamaño de muestra al lado del porcentaje, y por debajo de
`MUESTRA_MINIMA` la tasa se calcula igual (no se oculta el número) pero se
marca `muestra_suficiente: False` explícitamente — la decisión de si es
utilizable queda con quien lee el informe, no oculta en el dato.

Se mide sobre `SemanticMemory`: PRESELECCIONADA cuenta como "seleccionada",
DESCARTADA cuenta como "no seleccionada". GENERADA/HISTORICA/APROBADA/
PUBLICADA no entran en la tasa — sólo hay tasa donde hubo una DECISIÓN real
del Founder (`organism.registrar_curaduria`).

Ejes con datos hoy: materia, familia_editorial, necesidad, emocion (todos
viajan en el `TopicCandidate` desde `universe.py`). Ejes que el mandato pide
pero que la etapa actual no puede medir — `direccion_artistica`, `hook` — se
reportan con muestra 0 y una nota explícita: el candidato combinatorio no
lleva plan visual ni copy todavía (eso ocurre después de la verificación
jurídica, en `brief.py`/`pipeline.py`). No se inventa una tasa sobre un dato
que no existe.
"""

from dataclasses import dataclass, field

from memory import normaliza
from semantic_memory import PRESELECCIONADA, DESCARTADA

MUESTRA_MINIMA = 5

# Ejes que SÍ viajan en la huella de un TopicCandidate hoy.
EJES_DISPONIBLES = ("materia", "familia_editorial", "necesidad", "emocion")
# Ejes que el mandato pide pero la etapa actual no puede poblar todavía.
EJES_PENDIENTES = ("direccion_artistica", "hook")


@dataclass
class TasaEje:
    valor: str = ""
    preseleccionadas: int = 0
    descartadas: int = 0

    @property
    def total_decididas(self):
        return self.preseleccionadas + self.descartadas

    @property
    def tasa(self):
        return round(self.preseleccionadas / self.total_decididas, 4) if self.total_decididas else None

    @property
    def muestra_suficiente(self):
        return self.total_decididas >= MUESTRA_MINIMA

    def to_dict(self):
        return {"valor": self.valor, "preseleccionadas": self.preseleccionadas,
                "descartadas": self.descartadas, "total_decididas": self.total_decididas,
                "tasa": self.tasa, "muestra_suficiente": self.muestra_suficiente}


@dataclass
class InformeSelectionRate:
    tasa_global: float = None
    total_decididas: int = 0
    por_eje: dict = field(default_factory=dict)          # eje -> [TasaEje, ...]
    ejes_sin_datos: list = field(default_factory=list)
    avisos: list = field(default_factory=list)

    def to_dict(self):
        return {"tasa_global": self.tasa_global, "total_decididas": self.total_decididas,
                "por_eje": {eje: [t.to_dict() for t in filas]
                           for eje, filas in self.por_eje.items()},
                "ejes_sin_datos": list(self.ejes_sin_datos),
                "avisos": list(self.avisos)}


def _decididas(memoria):
    return [e for e in memoria.entries() if e.estado in (PRESELECCIONADA, DESCARTADA)]


def tasa_global(memoria):
    decididas = _decididas(memoria)
    pre = sum(1 for e in decididas if e.estado == PRESELECCIONADA)
    return round(pre / len(decididas), 4) if decididas else None


def tasa_por_eje(memoria, eje):
    decididas = _decididas(memoria)
    acumulado = {}
    for e in decididas:
        valor = normaliza(e.fingerprint.get(eje, ""))
        if not valor:
            continue
        t = acumulado.setdefault(valor, TasaEje(valor=valor))
        if e.estado == PRESELECCIONADA:
            t.preseleccionadas += 1
        else:
            t.descartadas += 1
    return sorted(acumulado.values(), key=lambda t: (-t.total_decididas, t.valor))


def informe(memoria, ejes=EJES_DISPONIBLES):
    """Selection rate global y por cada eje pedido. Los ejes en
    `EJES_PENDIENTES` que se incluyan aquí aparecen en `ejes_sin_datos` con
    el porqué, nunca con una tasa fabricada."""
    decididas = _decididas(memoria)
    avisos = []
    if len(decididas) < MUESTRA_MINIMA:
        avisos.append(
            f"sólo {len(decididas)} decisiones registradas en total (mínimo recomendado "
            f"{MUESTRA_MINIMA}): la tasa global es informativa, no concluyente.")

    por_eje, sin_datos = {}, []
    for eje in ejes:
        filas = tasa_por_eje(memoria, eje)
        if not filas and eje in EJES_PENDIENTES:
            sin_datos.append(eje)
            continue
        por_eje[eje] = filas
        insuficientes = [f.valor for f in filas if not f.muestra_suficiente]
        if insuficientes:
            avisos.append(f"{eje}: muestra insuficiente (<{MUESTRA_MINIMA}) para "
                          f"{len(insuficientes)} valor(es) — no saques conclusiones fuertes "
                          f"de {insuficientes[:5]}.")

    if "direccion_artistica" in ejes and "direccion_artistica" not in por_eje:
        avisos.append("direccion_artistica: sin datos todavía — el candidato combinatorio "
                      "no lleva plan visual hasta pasar por brief.py/pipeline.py.")
    if "hook" in ejes and "hook" not in por_eje:
        avisos.append("hook: sin datos todavía — el copy no se escribe en esta etapa.")

    return InformeSelectionRate(tasa_global=tasa_global(memoria), total_decididas=len(decididas),
                                por_eje=por_eje, ejes_sin_datos=sin_datos, avisos=avisos)
