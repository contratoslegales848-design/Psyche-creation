"""Capa pedagógica del motor de conocimiento — Mandato Maestro §1-3
(17-sep-2026).

PROBLEMA reportado por el Founder: "LegalMente se está yendo demasiado hacia
situaciones humanas, dilemas narrativos o casos cotidianos... tampoco debe
dominar el sistema... debe sentirse principalmente como una plataforma que
ENSEÑA DERECHO."

EVIDENCIA (antes de tocar código, medida sobre una reserva real de 250
candidatos, `universe.build_reserve(seed=42, factor=25)`): la distribución
por `familia_editorial` YA es prácticamente uniforme sobre las 58 familias
del registro (`policy/editorial-universe-v1.json`) — ninguna domina, la más
frecuente ronda 5%. El generador de candidatos NO tiene sesgo narrativo
medible. Lo que sí existe: sólo 5 de 58 familias son intrínsecamente
narrativas/situacionales por su propia `funcion_editorial` declarada
(`caso_cotidiano`, `caso_historico`, `jurista`, `historia_del_derecho`,
`cultura_juridica` — ver `FAMILIAS_NARRATIVA` abajo, clasificación auditable
contra el texto real de cada `funcion_editorial`) — el resto (53/58) enseña
concepto, distinción, requisito, proceso, doctrina, etc. Sin un mecanismo
explícito, sin embargo, nada IMPIDE que una corrida concreta (selección
manual, lotes de demostración, o una futura señal de Founder/mercado
correlacionada con piezas narrativas de alto rendimiento real — ver
`memoria_fuerte.py`, cuyas piezas de mejor rendimiento histórico SÍ son
mayormente narrativas: Carnelutti, Onassis, Calamandrei, Beccaria, Antígona)
empuje el balance hacia narrativa con el tiempo. Este módulo construye el
mecanismo preventivo que el mandato pide, ANTES de que ese sesgo se
materialice, no como reacción a una medición ya torcida.

DISEÑO (mismo patrón que `generator.ajuste_afinidad_founder()` y
`generator.ajuste_senal_mercado()` — sesgo pequeño y acotado sobre el score,
NUNCA una cuota rígida ni una exclusión):

    ORIGEN_PEDAGOGICO   — CONOCIMIENTO_JURIDICO | SITUACION_NARRATIVA,
                          clasificación de la FAMILIA EDITORIAL (no del
                          candidato individual — la familia ya declara su
                          función; inventar una segunda clasificación por
                          candidato duplicaría el eje que `familia_editorial`
                          ya cubre).
    OBJETIVO_PEDAGOGICO — la propia `funcion_editorial` de la familia
                          (`editorial.py`/`editorial-universe-v1.json`):
                          YA es el objetivo pedagógico declarado; este
                          módulo lo expone con ese nombre en vez de
                          duplicarlo en un catálogo paralelo.
    TIPO_DE_APRENDIZAJE — derivado determinista de `necesidad` (15 valores
                          ya declarados en el registro editorial), mismo
                          patrón que `art_direction.FUNCION_POR_NECESIDAD`.
    PROFUNDIDAD         — ya existe (`profundidad_tipica`/`candidato.
                          perfil...`); no se duplica aquí.
    CONOCIMIENTO_PREVIO — ya existe como `rol_lector` (persona/profesional/
                          quien_ya_sabe, ver registro); no se duplica.
    RELACIÓN_JURÍDICA   — ya existe como `candidato.relacion`; no se duplica.
    UTILIDAD_PRÁCTICA   — ya se puntúa en `generator.py` (`utility`, vía
                          `territory_explorer.coherencia()`); no se duplica.

BALANCE (no cuota): `ajuste_balance_pedagogico()` sólo actúa cuando ya hay
lote en progreso (memoria del lote actual) y nunca excluye un candidato —
empuja el score hacia el objetivo configurable (70% conocimiento / 30%
narrativa por defecto, mandato §3) de forma proporcional al desvío real del
lote que se está construyendo, acotado igual que los otros dos ajustes.
Situaciones humanas/narrativa NUNCA se eliminan del universo: siguen siendo
una puerta editorial disponible, sólo dejan de tener ventaja estructural
para dominar un lote.
"""

from dataclasses import dataclass

import editorial
from memory import normaliza

CONOCIMIENTO_JURIDICO = "CONOCIMIENTO_JURIDICO"
SITUACION_NARRATIVA = "SITUACION_NARRATIVA"

# Clasificación auditable: las 5 familias cuya propia `funcion_editorial`
# (policy/editorial-universe-v1.json) describe narrar una situación,
# retratar una persona o entrar por una obra cultural — nunca por intuición.
#   caso_cotidiano       -> "narrar una situación reconocible"
#   caso_historico        -> "narrar un caso documentado"
#   jurista               -> "retratar a quien pensó una idea"
#   historia_del_derecho  -> "mostrar cómo nació una institución"
#   cultura_juridica      -> "entrar por una obra cultural"
# Las 53 restantes enseñan concepto/distinción/requisito/proceso/doctrina/etc
# — CONOCIMIENTO_JURIDICO por exclusión, verificado uno por uno contra el
# registro real (ver test_pedagogia.py::test_clasificacion_cubre_las_58).
FAMILIAS_NARRATIVA = frozenset({
    "caso_cotidiano", "caso_historico", "jurista", "historia_del_derecho",
    "cultura_juridica",
})

OBJETIVO_CONOCIMIENTO_DEFAULT = 0.70
AJUSTE_BALANCE_PEDAGOGICO_MAX = 0.10

# necesidad (15, ya declaradas en editorial-universe-v1.json) -> tipo de
# aprendizaje que produce. Mismo patrón que
# art_direction.FUNCION_POR_NECESIDAD: mapeo determinista sobre vocabulario
# YA existente, no una taxonomía inventada aparte.
TIPO_APRENDIZAJE_POR_NECESIDAD = {
    "entender": "COMPRENSION",
    "distinguir": "DISCRIMINACION_CONCEPTUAL",
    "prevenir": "ANTICIPACION_DE_RIESGO",
    "prepararse": "PREPARACION_PROCEDIMENTAL",
    "decidir": "JUICIO_APLICADO",
    "actuar": "PROCEDIMIENTO",
    "reclamar": "EJERCICIO_DE_DERECHOS",
    "corregir": "CORRECCION_DE_ERROR",
    "cumplir": "CUMPLIMIENTO_NORMATIVO",
    "detectar": "RECONOCIMIENTO_DE_SEÑAL",
    "acordar": "NEGOCIACION",
    "recordar": "MEMORIZACION_UTIL",
    "aplicar": "APLICACION_PRACTICA",
    "actualizar": "ACTUALIZACION_NORMATIVA",
    "reflexionar": "REFLEXION_CRITICA",
}


class PedagogiaError(ValueError):
    pass


def clasificar_origen_pedagogico(familia_editorial):
    """(origen, razón) — determinista, auditable. Familia desconocida no se
    adivina: error explícito, mismo criterio que `EditorialUniverse.get()`."""
    fam = normaliza(familia_editorial)
    conocidas_narrativa = {normaliza(f) for f in FAMILIAS_NARRATIVA}
    if not fam:
        raise PedagogiaError("familia_editorial vacía: no se puede clasificar sin dato.")
    if fam in conocidas_narrativa:
        return SITUACION_NARRATIVA, f"{familia_editorial!r} está en FAMILIAS_NARRATIVA."
    return CONOCIMIENTO_JURIDICO, f"{familia_editorial!r} no está en FAMILIAS_NARRATIVA (53/58 restantes)."


def objetivo_pedagogico(familia_editorial, universo=None):
    """La `funcion_editorial` declarada de la familia — no se duplica en un
    catálogo aparte, se expone con el nombre que pide el mandato."""
    universo = universo or editorial.EditorialUniverse.load()
    return universo.get(familia_editorial).funcion_editorial


def tipo_de_aprendizaje(necesidad):
    nec = normaliza(necesidad)
    for clave, valor in TIPO_APRENDIZAJE_POR_NECESIDAD.items():
        if normaliza(clave) == nec:
            return valor
    return "SIN_CLASIFICAR"


@dataclass
class PerfilPedagogico:
    familia_editorial: str = ""
    origen: str = ""
    razon_origen: str = ""
    objetivo: str = ""
    tipo_aprendizaje: str = ""

    def to_dict(self):
        from dataclasses import asdict
        return asdict(self)


def perfil_pedagogico(candidato, universo=None):
    origen, razon = clasificar_origen_pedagogico(candidato.familia_editorial)
    return PerfilPedagogico(
        familia_editorial=candidato.familia_editorial, origen=origen, razon_origen=razon,
        objetivo=objetivo_pedagogico(candidato.familia_editorial, universo),
        tipo_aprendizaje=tipo_de_aprendizaje(candidato.necesidad))


def ajuste_balance_pedagogico(candidato, lote_en_progreso,
                              objetivo_conocimiento=OBJETIVO_CONOCIMIENTO_DEFAULT):
    """Empujón pequeño y acotado hacia `objetivo_conocimiento` (70% por
    defecto, mandato §3) — nunca una cuota: el candidato del lado
    infrarrepresentado en EL LOTE QUE SE ESTÁ CONSTRUYENDO recibe un
    empujón positivo proporcional al desvío real; el otro lado, uno
    negativo. Lote vacío -> 0.0 exacto (mismo criterio que
    `ajuste_afinidad_founder`: sin evidencia de lote, no hay desvío que
    corregir). `objetivo_conocimiento` es un parámetro, no una constante
    fija en el código que llama — "no lo conviertas en regla rígida"
    (mandato §3): un llamador puede pasar cualquier valor o desactivarlo
    con `objetivo_conocimiento=None`.
    """
    if not lote_en_progreso:
        return 0.0, "lote vacío: sin evidencia de balance todavía."
    if objetivo_conocimiento is None:
        return 0.0, "balance pedagógico desactivado explícitamente por el llamador."

    total = len(lote_en_progreso)
    n_conocimiento = sum(
        1 for c in lote_en_progreso
        if clasificar_origen_pedagogico(c.familia_editorial)[0] == CONOCIMIENTO_JURIDICO)
    ratio_actual = n_conocimiento / total
    origen, _ = clasificar_origen_pedagogico(candidato.familia_editorial)
    desvio = objetivo_conocimiento - ratio_actual  # >0: falta conocimiento en el lote
    cruda = desvio if origen == CONOCIMIENTO_JURIDICO else -desvio
    ajuste = max(-AJUSTE_BALANCE_PEDAGOGICO_MAX,
                min(AJUSTE_BALANCE_PEDAGOGICO_MAX, cruda * AJUSTE_BALANCE_PEDAGOGICO_MAX))
    razon = (f"lote parcial: {n_conocimiento}/{total} conocimiento ({ratio_actual:.0%}) vs "
            f"objetivo {objetivo_conocimiento:.0%}; candidato es {origen}, ajuste {ajuste:+.4f}.")
    return round(ajuste, 4), razon
