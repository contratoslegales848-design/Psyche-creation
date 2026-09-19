"""El ciclo vertical del organismo — Handoff §16.

    SEÑAL/NECESIDAD → CANDIDATO → HUELLA SEMÁNTICA → RESERVA/DIVERSIDAD
    → PERFIL EMOCIONAL → QA DE LOTE → CURATION_READY
    → SELECCIÓN/DESCARTE DEL FOUNDER → MEMORIA → APRENDIZAJE → NUEVA GENERACIÓN

Este módulo NO es un motor nuevo: es el cableado de los que ya existen
(`universe`, `emotion`, `semantic_memory`, `batch_qa`, `rotation`, `memory`,
`lanes`). Su única responsabilidad es que el ciclo se cierre y deje evidencia.

CORRECCIÓN EXPRESA DEL FOUNDER (Handoff §5), implementada literalmente:

    NO se exige autorización humana antes de generar cada pieza.
    El sistema GENERA → QA → entrega CURATION_READY → el Founder
    SELECCIONA/DESCARTA → el sistema APRENDE.

Por eso `producir_lote()` no recibe ni consulta ninguna aprobación previa. Lo
que sí conserva, intacto, es la separación de gates posteriores: el estado
terminal de este módulo es CURATION_READY y nada más. No existe aquí ninguna
transición a PUBLICADA, ni a merge, ni a deploy, ni a gasto externo. Producir
no es publicar; la curaduría es feedback, no permiso.

Y ningún candidato lleva verdad jurídica: todos nacen NO_VERIFICADO y su
próxima acción es `legalmente-legal-verification` (CLAUDE.md §4).
"""

from dataclasses import dataclass, field

import batch_qa
import lanes
import universe
from semantic_memory import SemanticMemory, GENERADA

ORGANISM_SCHEMA_VERSION = "1.0"

CURATION_READY = "CURATION_READY"
REGENERAR = "REGENERAR"

MAX_INTENTOS = 4


@dataclass
class CurationBatch:
    """Un lote entregado a curaduría. Estado terminal: CURATION_READY."""

    lote_id: str
    estado: str = REGENERAR
    carril: str = lanes.LEGALMENTE_GENERAL
    candidatos: list = field(default_factory=list)
    qa: dict = field(default_factory=dict)
    seleccion: dict = field(default_factory=dict)
    intentos: int = 0
    reserva_total: int = 0
    avisos: list = field(default_factory=list)
    schema_version: str = ORGANISM_SCHEMA_VERSION

    @property
    def listo(self):
        return self.estado == CURATION_READY

    def fingerprints(self):
        return [c.fingerprint() for c in self.candidatos]

    def to_dict(self):
        return {"lote_id": self.lote_id, "estado": self.estado, "carril": self.carril,
                "candidatos": [c.to_dict() for c in self.candidatos],
                "qa": dict(self.qa), "seleccion": dict(self.seleccion),
                "intentos": self.intentos, "reserva_total": self.reserva_total,
                "avisos": list(self.avisos), "schema_version": self.schema_version}


def producir_lote(lote_id, n=10, seed=None, memoria=None,
                  carril=lanes.LEGALMENTE_GENERAL, max_intentos=MAX_INTENTOS,
                  factor_reserva=universe.RESERVA_MINIMA_POR_PIEZA):
    """Produce un lote y lo entrega a curaduría. Sin autorización previa.

    Si el QA rechaza el lote, REGENERA con una reserva más amplia en vez de
    rellenar con candidatos débiles. Si tras `max_intentos` sigue sin pasar,
    devuelve el lote en estado REGENERAR con el QA que lo explica: entregar un
    lote malo diciendo que es bueno sería peor que no entregarlo.
    """
    memoria = memoria if memoria is not None else SemanticMemory()
    cfg = lanes.get(carril)
    ultimo, intentos = None, 0

    for intento in range(1, int(max_intentos) + 1):
        intentos = intento
        semilla = None if seed is None else seed + intento - 1
        reserva = universe.build_reserve(objetivo_lote=n, seed=semilla,
                                         factor=factor_reserva + intento - 1)
        reserva = [c for c in reserva
                   if lanes.validar_candidato(c, carril).admitido] if cfg.familias_permitidas \
            else reserva

        seleccion = universe.select_batch(reserva, n=n, memoria=memoria)
        qa = batch_qa.evaluar_lote([c.fingerprint() for c in seleccion.seleccionados],
                                   objetivo=n, memoria=memoria,
                                   regeneraciones=intento - 1)
        ultimo = CurationBatch(
            lote_id=lote_id, carril=carril, candidatos=seleccion.seleccionados,
            qa=qa.to_dict(), intentos=intento, reserva_total=seleccion.reserva_total,
            avisos=list(seleccion.avisos))
        if qa.aceptado:
            ultimo.estado = CURATION_READY
            break

    # La huella de lo producido entra en memoria corta AUNQUE nadie la apruebe:
    # es exactamente la distinción producir/aprobar. Generar deja rastro de
    # fatiga; sólo la curaduría posterior puede convertirlo en señal positiva.
    if ultimo is not None:
        for c in ultimo.candidatos:
            memoria.record(c.fingerprint(), GENERADA, lote_id)
        ultimo.intentos = intentos
    return ultimo


def registrar_curaduria(batch, seleccionados_ids, memoria):
    """El Founder conserva unas piezas y descarta otras. El sistema aprende.

    `seleccionados_ids` son los candidate_id que el Founder quiere conservar.
    Todo lo demás del lote se registra como DESCARTADA — con la ventana de
    cooldown más corta, porque un descarte no cancela una rama del
    conocimiento (ver semantic_memory).
    """
    ids = set(seleccionados_ids)
    desconocidos = ids - {c.candidate_id for c in batch.candidatos}
    if desconocidos:
        raise ValueError(
            f"no pertenecen a este lote: {sorted(desconocidos)}. La curaduría sólo "
            "puede pronunciarse sobre lo que el lote realmente contiene.")

    elegidos = [c.fingerprint() for c in batch.candidatos if c.candidate_id in ids]
    descartados = [c.fingerprint() for c in batch.candidatos if c.candidate_id not in ids]
    resumen = memoria.registrar_seleccion(elegidos, descartados, batch.lote_id)
    batch.seleccion = resumen
    return resumen
