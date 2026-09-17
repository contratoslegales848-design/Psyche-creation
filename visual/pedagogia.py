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

CONTINUACIÓN EJECUTIVA — prioridad pedagógica (17-sep-2026, mismo día,
segunda pasada): el Founder aceptó el Mandato Maestro técnico y pidió una
precisión editorial adicional, EXPLÍCITAMENTE sin crear un segundo motor:
"conocimiento primero, formato después". Esta sección extiende el mismo
módulo, reutilizando el mismo patrón de ajuste acotado y el mismo registro
editorial real — nunca un catálogo paralelo.

    DIMENSIONES_CONOCIMIENTO — las 20 dimensiones de conocimiento jurídico
                          que el mandato lista en su §1/§8 (qué es, qué no
                          es, con qué se confunde, elementos, requisitos,
                          clasificación, tipos, sujetos, funcionamiento,
                          etapas, relación con otras figuras, efectos,
                          consecuencias, límites, excepciones, prueba o
                          documento, ejemplo, aplicación práctica, síntesis,
                          siguiente pregunta). No es una taxonomía nueva de
                          candidato: es la lente con la que se lee la
                          `familia_editorial` ya elegida — cada familia real
                          del registro (`editorial-universe-v1.json`) ya
                          declara, en su `funcion_editorial`, cuál de estas
                          dimensiones enseña. `DIMENSION_POR_FAMILIA` hace
                          esa lectura explícita y auditable, familia por
                          familia, contra el texto real — igual que
                          `FAMILIAS_NARRATIVA` arriba.

    7 familias NUEVAS registradas esta pasada en `editorial-universe-v1.json`
    (altas reales vía el mecanismo ya existente, ninguna reemplaza ni
    duplica una familia previa — verificado contra las 58 anteriores antes
    de darlas de alta): `clasificacion`, `elementos`, `mapa_de_materia`,
    `institucion_juridica`, `para_recordar`, `quiz_juridico`,
    `relacion_figuras`. Cubren los ítems del mandato §3 que NINGUNA de las
    58 familias previas representaba ya (verificado uno por uno contra las
    58 `funcion_editorial` reales antes de decidir que hacía falta alta
    nueva — el resto de los ítems del mandato §3 —p.ej. "requisitos",
    "documento clave", "excepción", "mito", "prueba"— ya tenían familia
    real y no se duplican). "Ruta de aprendizaje" (mandato §4) NO es una
    familia: es una propiedad de un CONJUNTO de candidatos que comparten
    `concepto_nucleo` — se mide con `cubre_dimensiones_distintas()`, no se
    inventa una familia "ruta".

    aprendizaje_concreto()  — el chequeo de QA del mandato §7 ("¿la persona
                          aprendió algo jurídico concreto?"). Proxy
                          estructural sobre campos YA existentes de
                          `TopicCandidate` (`concepto_nucleo`,
                          `pregunta_resuelta`, `consecuencia`, `relacion`):
                          nunca evalúa el contenido real de la pieza (eso
                          excede este módulo — es verificación jurídica o
                          juicio humano), sólo si el candidato TRAE consigo
                          evidencia estructural de enseñanza. Sin esa
                          evidencia, informa REWORK — nunca descarta por sí
                          solo (mismo criterio de no-exclusión-silenciosa
                          que el resto del módulo: quien decide REWORK es la
                          capa de QA que consulte esta función, no esta
                          función).

    formato_sugerido()     — sugerencia (nunca obligación, mandato §6) de
                          formato editorial según profundidad y cuántas
                          dimensiones de conocimiento hay disponibles para
                          la pieza. Reutiliza el vocabulario YA existente de
                          `formatos_editoriales`; nunca inventa un formato
                          nuevo ni fuerza una elección.
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


# Las 20 dimensiones de conocimiento jurídico del mandato §1/§8 — vocabulario
# cerrado (es la lista textual del mandato), pero su USO sobre familias es
# abierto: una familia nueva que no encaje se marca SIN_CLASIFICAR, nunca se
# fuerza en la dimensión más parecida.
DIMENSIONES_CONOCIMIENTO = (
    "QUE_ES", "QUE_NO_ES", "CONFUSION_FRECUENTE", "ELEMENTOS", "REQUISITOS",
    "CLASIFICACION", "TIPOS", "SUJETOS", "FUNCIONAMIENTO", "ETAPAS",
    "RELACION_CON_OTRAS_FIGURAS", "EFECTOS", "CONSECUENCIAS", "LIMITES",
    "EXCEPCIONES", "PRUEBA_O_DOCUMENTO", "EJEMPLO", "APLICACION_PRACTICA",
    "SINTESIS", "SIGUIENTE_PREGUNTA",
)

# familia_editorial (65, ya declaradas en editorial-universe-v1.json) ->
# dimensión de conocimiento que su propia `funcion_editorial` enseña.
# Lectura auditable, familia por familia, del texto real del registro — no
# una taxonomía inventada aparte. Una familia mapea a UNA dimensión
# primaria (no todas las dimensiones deben aparecer por pieza, mandato §1);
# eso basta para medir cobertura de una ruta de aprendizaje sin pretender
# que cada pieza agote todas las dimensiones posibles.
DIMENSION_POR_FAMILIA = {
    "duda_frecuente": "QUE_ES",
    "asesoria_orientacion": "APLICACION_PRACTICA",
    "concepto": "QUE_ES",
    "definicion_operativa": "QUE_ES",
    "diferencia": "RELACION_CON_OTRAS_FIGURAS",
    "confusion_habitual": "CONFUSION_FRECUENTE",
    "mito": "QUE_NO_ES",
    "error_frecuente": "QUE_NO_ES",
    "creencia_popular": "QUE_NO_ES",
    "costumbre_juridica": "CONFUSION_FRECUENTE",
    "ley_regla": "QUE_ES",
    "excepcion": "EXCEPCIONES",
    "requisito": "REQUISITOS",
    "prohibicion": "LIMITES",
    "derecho": "QUE_ES",
    "obligacion": "QUE_ES",
    "consecuencia": "CONSECUENCIAS",
    "riesgo": "EFECTOS",
    "senal_de_alerta": "APLICACION_PRACTICA",
    "que_hacer": "APLICACION_PRACTICA",
    "que_no_hacer": "APLICACION_PRACTICA",
    "primeros_pasos": "ETAPAS",
    "checklist": "REQUISITOS",
    "documento_clave": "PRUEBA_O_DOCUMENTO",
    "clausula_bajo_lupa": "ELEMENTOS",
    "contrato_bajo_lupa": "ELEMENTOS",
    "proceso": "ETAPAS",
    "etapa_procesal": "ETAPAS",
    "prueba": "PRUEBA_O_DOCUMENTO",
    "carga_de_la_prueba": "SUJETOS",
    "responsabilidad": "SUJETOS",
    "plazo_prescripcion": "LIMITES",
    "autoridad_competente": "SUJETOS",
    "caso_cotidiano": "EJEMPLO",
    "caso_historico": "EJEMPLO",
    "historia_del_derecho": "EJEMPLO",
    "jurista": "EJEMPLO",
    "doctrina": "QUE_ES",
    "maxima_aforismo": "SINTESIS",
    "etimologia": "QUE_ES",
    "rareza_juridica": "EJEMPLO",
    "comparacion_sistemas": "RELACION_CON_OTRAS_FIGURAS",
    "criminalistica_forense": "PRUEBA_O_DOCUMENTO",
    "medicina_legal": "PRUEBA_O_DOCUMENTO",
    "evidencia_digital": "PRUEBA_O_DOCUMENTO",
    "herramienta_practica": "APLICACION_PRACTICA",
    "prevencion": "APLICACION_PRACTICA",
    "negociacion": "FUNCIONAMIENTO",
    "conciliacion_mediacion": "FUNCIONAMIENTO",
    "reparacion": "CONSECUENCIAS",
    "cumplimiento_compliance": "APLICACION_PRACTICA",
    "incumplimiento": "EFECTOS",
    "actualizacion_normativa": "CONSECUENCIAS",
    "interpretacion": "FUNCIONAMIENTO",
    "lenguaje_juridico_explicado": "QUE_ES",
    "paradoja_tension": "QUE_ES",
    "cultura_juridica": "EJEMPLO",
    "pregunta_avanzada": "SIGUIENTE_PREGUNTA",
    "clasificacion": "CLASIFICACION",
    "elementos": "ELEMENTOS",
    "mapa_de_materia": "FUNCIONAMIENTO",
    "institucion_juridica": "QUE_ES",
    "para_recordar": "SINTESIS",
    "quiz_juridico": "SIGUIENTE_PREGUNTA",
    "relacion_figuras": "RELACION_CON_OTRAS_FIGURAS",
}

# profundidad (3, ya declaradas en editorial-universe-v1.json) -> formatos
# editoriales (9, ya declarados) recomendados por defecto para esa
# profundidad. Sugerencia, no obligación (mandato §6).
FORMATOS_POR_PROFUNDIDAD = {
    "base": ("frase", "concepto"),
    "media": ("concepto", "diferencia", "listado", "proceso"),
    "alta": ("proceso", "documento", "historia"),
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


def dimension_de_familia(familia_editorial):
    """Dimensión de conocimiento (de `DIMENSIONES_CONOCIMIENTO`) que enseña
    esta familia — "SIN_CLASIFICAR" para una familia futura no mapeada
    todavía (nunca se adivina, mismo criterio que `tipo_de_aprendizaje`)."""
    fam = normaliza(familia_editorial)
    for clave, valor in DIMENSION_POR_FAMILIA.items():
        if normaliza(clave) == fam:
            return valor
    return "SIN_CLASIFICAR"


def cubre_dimensiones_distintas(candidatos):
    """True si un conjunto de candidatos (p.ej. una ruta de aprendizaje sobre
    un mismo `concepto_nucleo`, mandato §4) cubre más de una dimensión de
    conocimiento — evidencia de que la ruta enseña ángulos distintos y no
    repite el mismo ángulo con distinto envoltorio. Un solo candidato, o un
    conjunto que sólo cubre "SIN_CLASIFICAR", nunca cuenta como ruta."""
    dims = {dimension_de_familia(c.familia_editorial) for c in candidatos}
    dims.discard("SIN_CLASIFICAR")
    return len(dims) > 1


def aprendizaje_concreto(candidato):
    """QA estructural del mandato §7: '¿la persona aprendió algo jurídico
    concreto?'. Proxy auditable sobre campos YA existentes de
    `TopicCandidate` — nunca evalúa el contenido real (eso es verificación
    jurídica o juicio humano, fuera de este módulo). (bool, motivo); False
    es una señal de REWORK para quien haga QA, nunca un descarte por sí
    solo."""
    concepto = (getattr(candidato, "concepto_nucleo", "") or "").strip()
    señales = (
        (getattr(candidato, "pregunta_resuelta", "") or "").strip(),
        (getattr(candidato, "consecuencia", "") or "").strip(),
        (getattr(candidato, "relacion", "") or "").strip(),
    )
    if not concepto:
        return False, "sin concepto_nucleo: no hay evidencia de qué enseña la pieza (mandato §7)."
    if not any(señales):
        return False, ("concepto_nucleo declarado pero sin pregunta_resuelta/consecuencia/"
                       "relacion: riesgo de pieza sin sustancia jurídica concreta (mandato §7).")
    return True, "concepto_nucleo y al menos una señal de contenido jurídico concreto declarados."


def formato_sugerido(profundidad, n_dimensiones_disponibles=1):
    """Sugerencia (nunca obligación, mandato §6) de formato editorial según
    profundidad y cuántas dimensiones de conocimiento hay disponibles para
    la pieza. Reutiliza `formatos_editoriales` ya declarado; nunca inventa
    un formato nuevo. `n_dimensiones_disponibles` alto empuja hacia un
    formato que secuencie en vez de comprimir — 'si no cabe, nunca elimines
    relaciones importantes: selecciona otro formato o divide la enseñanza'.
    """
    prof = normaliza(profundidad)
    candidatos = FORMATOS_POR_PROFUNDIDAD.get(prof, FORMATOS_POR_PROFUNDIDAD["media"])
    if n_dimensiones_disponibles >= 3 and prof != "alta":
        return "proceso", (f"{n_dimensiones_disponibles} dimensiones disponibles para "
                           f"profundidad={profundidad!r}: preferir un formato que las "
                           "secuencie en vez de comprimirlas en una sola pieza.")
    return candidatos[0], f"profundidad={profundidad!r}: formato por defecto de esa profundidad."
