"""Puente EmotionalProfile → argumento visual → VisualBrief (borrador).

Cierra la brecha que Paso 6/7 de la reconciliación señalan y que la rama
`chatgpt/image-generator-reconciliation-v2-2026-09-13` de `legalmente-web`
sólo DECLARA sin aplicar: su `IMAGE_GENERATOR_INVARIANTS` incluye
`emotionChangesVisualTreatment: true`, pero `emotion` en ese código es un
string libre que sólo se valida como no-vacío y se copia literalmente al
prompt (`Emotion: ${b.emotion}.`) — nada obliga a que cambiarlo cambie
cámara, luz o composición. Es exactamente el caso que el mandato prohíbe:
"emotion = 'tension' si después la imagen se genera exactamente igual".

En este repo la emoción YA modifica cámara/luz/composición de forma causal
(`emotion.py`: `EmotionalProfile.camara/luz/composicion` nacen del propio
perfil, no se escriben aparte). Lo que faltaba era el siguiente eslabón:
argumento visual (qué hace la imagen, no sólo qué siente) y selección de
familia visual con antirrepetición real. Este módulo los añade.

ORDEN OBLIGATORIO (idéntico al que ya regía en emotion.py/universe.py,
ahora explícito en un solo lugar):

    NECESIDAD (TopicCandidate.necesidad)
    → FUNCIÓN EDITORIAL (TopicCandidate.familia_editorial)
    → EMOCIÓN (EmotionalProfile, ya derivado — emotion.py)
    → ARGUMENTO VISUAL (visual_function: qué hace la imagen — este módulo)
    → COMPOSICIÓN / CÁMARA / LUZ (ya en EmotionalProfile — se propagan, nunca
      se reinventan)
    → LENGUAJE ARTÍSTICO (VisualFamily, elegido por rotación antirrepetición,
      nunca por regla fija materia→estilo)
    → MATERIAL / SUPERFICIE DE MARCA (de la VisualFamily elegida)

LÍMITE HONESTO: esto produce un BORRADOR, nunca un VisualBrief autorizado.
Un VisualBrief real (`brief.py`) exige política + verificación jurídica
previa (CLAUDE.md §4) y aprobación humana del gate de arte — ninguna de las
dos existe todavía para un TopicCandidate. Tampoco inventa METÁFORA ni
ESCENA concretas: son contenido creativo verificable, no infraestructura, y
seguirán PENDIENTES hasta que alguien (persona o pipeline posterior) las
redacte sobre una pieza ya verificada.
"""

from dataclasses import dataclass, field

from memory import normaliza

# Vocabulario abierto — mismo espíritu que VISUAL_FUNCTIONS en
# legalmente-web/visual-argument, implementación propia. Describe QUÉ HACE
# la imagen (su función), no cómo se ve (eso es la familia visual).
VISUAL_FUNCTIONS = (
    "EXPLAIN", "SEPARATE", "COMPARE", "REVEAL", "WARN", "TENSION",
    "HUMANIZE", "SHOW_PROCESS", "SHOW_CONSEQUENCE",
    "MATERIALIZE_ABSTRACTION", "PROVOKE_REFLECTION",
)

# Mapeo por FAMILIA EDITORIAL cuando la función editorial ya lo deja claro
# (ver editorial.py: funcion_editorial de cada familia). Sólo se mapean
# familias donde la evidencia es directa; el resto cae al fallback por
# necesidad — no se fuerza un mapeo dudoso.
FUNCION_POR_FAMILIA = {
    "diferencia": "SEPARATE", "comparacion_sistemas": "COMPARE",
    "mito": "REVEAL", "confusion_habitual": "REVEAL", "creencia_popular": "REVEAL",
    "senal_de_alerta": "WARN", "riesgo": "WARN", "prohibicion": "WARN",
    "error_frecuente": "WARN",
    "clausula_bajo_lupa": "TENSION", "carga_de_la_prueba": "TENSION",
    "paradoja_tension": "TENSION",
    "caso_cotidiano": "HUMANIZE", "caso_historico": "HUMANIZE", "jurista": "HUMANIZE",
    "historia_del_derecho": "HUMANIZE",
    "proceso": "SHOW_PROCESS", "etapa_procesal": "SHOW_PROCESS",
    "checklist": "SHOW_PROCESS", "primeros_pasos": "SHOW_PROCESS",
    "documento_clave": "SHOW_PROCESS", "contrato_bajo_lupa": "SHOW_PROCESS",
    "consecuencia": "SHOW_CONSEQUENCE", "incumplimiento": "SHOW_CONSEQUENCE",
    "reparacion": "SHOW_CONSEQUENCE", "responsabilidad": "SHOW_CONSEQUENCE",
    "concepto": "MATERIALIZE_ABSTRACTION", "definicion_operativa": "MATERIALIZE_ABSTRACTION",
    "lenguaje_juridico_explicado": "MATERIALIZE_ABSTRACTION",
    "etimologia": "MATERIALIZE_ABSTRACTION",
    "pregunta_avanzada": "PROVOKE_REFLECTION", "doctrina": "PROVOKE_REFLECTION",
    "cultura_juridica": "PROVOKE_REFLECTION",
}

# Fallback por NECESIDAD cuando la familia no tiene mapeo directo. Cubre las
# 15 necesidades declaradas en editorial-universe-v1.json.
FUNCION_POR_NECESIDAD = {
    "entender": "EXPLAIN", "distinguir": "SEPARATE", "prevenir": "WARN",
    "prepararse": "SHOW_PROCESS", "decidir": "TENSION", "actuar": "SHOW_PROCESS",
    "reclamar": "SHOW_CONSEQUENCE", "cumplir": "SHOW_PROCESS", "detectar": "WARN",
    "acordar": "HUMANIZE", "recordar": "MATERIALIZE_ABSTRACTION",
    "aplicar": "SHOW_PROCESS", "actualizar": "WARN", "reflexionar": "PROVOKE_REFLECTION",
    "corregir": "REVEAL",
}

# Familias editoriales cuya representación natural es una ESCENA CONCRETA
# (operativa: documento, proceso, prueba) frente a las que suelen resolverse
# con una METÁFORA (abstracción, máxima, rareza). Es informativo — orienta
# la selección, nunca fuerza una familia visual concreta.
FAMILIAS_OPERATIVAS = frozenset({
    "proceso", "etapa_procesal", "checklist", "primeros_pasos", "documento_clave",
    "contrato_bajo_lupa", "clausula_bajo_lupa", "carga_de_la_prueba", "prueba",
    "cumplimiento_compliance", "requisito", "autoridad_competente",
})


def derivar_funcion_visual(familia_editorial, necesidad):
    """Determinista, con procedencia declarada: por familia si hay evidencia
    directa, si no por necesidad, si no EXPLAIN (el fallback más neutro,
    nunca uno con carga — no se puede afirmar TENSION sin evidencia)."""
    fam = normaliza(familia_editorial)
    nec = normaliza(necesidad)
    for clave, valor in FUNCION_POR_FAMILIA.items():
        if normaliza(clave) == fam:
            return valor, f"familia editorial {familia_editorial!r} determina la función."
    for clave, valor in FUNCION_POR_NECESIDAD.items():
        if normaliza(clave) == nec:
            return valor, f"necesidad {necesidad!r} determina la función (sin mapeo directo de familia)."
    return "EXPLAIN", "sin evidencia de familia ni necesidad: función neutra por defecto."


def elegir_familia_visual(registro_familias, memoria_visual=None, evitar=()):
    """Elige una VisualFamily por rotación antirrepetición — NUNCA por una
    regla fija materia→estilo (mandato §7 original y Fase de emoción: 'no
    existe una única unión rígida materia=estilo').

    Usa `memoria_visual` (visual/memory.VisualMemory) si se da: penaliza la
    familia más usada recientemente. Sin memoria, elige la primera
    disponible del registro (determinista, no aleatoria — la aleatoriedad
    controlada vive en universe.py, aquí sólo se evita repetir lo último).
    """
    nombres = [n for n in registro_familias.names() if n not in set(evitar)]
    if not nombres:
        nombres = list(registro_familias.names())
    if memoria_visual is None or not len(memoria_visual):
        return registro_familias.get(nombres[0])

    recientes = memoria_visual.recent()
    usos = {}
    for e in recientes:
        v = normaliza(e.visual_family)
        if v:
            usos[v] = usos.get(v, 0) + 1
    nombres.sort(key=lambda n: (usos.get(normaliza(n), 0), n))
    return registro_familias.get(nombres[0])


@dataclass
class VisualBriefDraft:
    """Borrador. `autorizado` es siempre False: nunca sustituye a un
    VisualBrief real validado por política y gate jurídico."""

    content_id: str = ""
    visual_function: str = ""
    razon_funcion: str = ""
    familia_visual: str = ""
    material_sugerido: str = ""
    superficie_marca_sugerida: str = ""
    composicion: str = ""
    camara: str = ""
    luz: str = ""
    escala: str = ""
    textura: str = ""
    ritmo: str = ""
    escena: str = ""      # PENDIENTE_CONTENIDO deliberado — ver docstring del módulo
    metafora: str = ""    # PENDIENTE_CONTENIDO deliberado
    autorizado: bool = False
    nota: str = ""

    def to_dict(self):
        from dataclasses import asdict
        return asdict(self)


PENDIENTE_CONTENIDO = "PENDIENTE_CONTENIDO — requiere redacción humana o de pipeline posterior sobre pieza ya verificada."


def verificar_diversidad_de_estilos(drafts, registro_familias, n_esperado=None):
    """Hueco encontrado al reconciliar: legalmente-web exige 10 estilos
    distintos en un lote independiente de 10 piezas
    (`tenDistinctArtStylesForIndependentGeneralPieces`), con un catálogo de
    estilo declarado ABIERTO (`artStyleRegistryIsOpen: true`) — un string
    libre, validado sólo por unicidad.

    El registro de familias visuales de este repo (`families.py`) es
    CERRADO: hoy tiene 8 entradas, no un catálogo abierto. Exigir 10
    distintas sobre 8 posibles sería fabricar un requisito que los datos no
    pueden sostener — el mismo error que ya se corrigió en el motor
    editorial (ver corpus_analysis / territory_explorer). El techo real es
    `min(len(registro), n)`, y se documenta como límite, no se esconde.
    """
    n_esperado = n_esperado if n_esperado is not None else len(drafts)
    techo = min(len(registro_familias.names()), n_esperado)
    distintos = {normaliza(d.familia_visual) for d in drafts if d.familia_visual}
    detalle = (f"{len(distintos)}/{techo} estilos distintos "
              f"(catálogo actual: {len(registro_familias.names())} familias; "
              f"'biblioteca artística abierta' sigue siendo aspiracional, no implementada).")
    return len(distintos) >= techo, detalle


def draft_visual_brief(candidato, perfil_emocional, registro_familias,
                       memoria_visual=None, evitar_familias=()):
    """Construye el borrador. `perfil_emocional` es el dict que ya trae el
    candidato (`candidato.perfil_emocional`, poblado por emotion.py) — no se
    vuelve a derivar aquí: una capa posterior nunca reinfiere lo que una
    capa anterior ya decidió (mandato Paso 3)."""
    funcion, razon = derivar_funcion_visual(candidato.familia_editorial, candidato.necesidad)
    familia = elegir_familia_visual(registro_familias, memoria_visual, evitar_familias)

    material = familia.material_vocabulary[0] if familia.material_vocabulary else ""
    superficie = familia.brand_surface_preferences[0] if familia.brand_surface_preferences else ""

    return VisualBriefDraft(
        content_id=candidato.candidate_id, visual_function=funcion, razon_funcion=razon,
        familia_visual=familia.name, material_sugerido=material,
        superficie_marca_sugerida=superficie,
        composicion=perfil_emocional.get("composicion", ""),
        camara=perfil_emocional.get("camara", ""),
        luz=perfil_emocional.get("luz", ""),
        escala=perfil_emocional.get("escala", ""),
        textura=perfil_emocional.get("textura", ""),
        ritmo=perfil_emocional.get("ritmo", ""),
        escena=PENDIENTE_CONTENIDO, metafora=PENDIENTE_CONTENIDO,
        autorizado=False,
        nota="Borrador pre-verificación. No autoriza producción ni sustituye brief.py.")
