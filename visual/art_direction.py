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

CORRECCIÓN DE LA DESCONEXIÓN (mandato "Fase post-implementación", Parte
XII, 16-sep-2026): hasta esta fase, "LENGUAJE ARTÍSTICO" en el ORDEN
OBLIGATORIO de arriba se resolvía con `elegir_familia_visual()` sobre
`families.py` — el registro de 8 familias reducidas que el mandato
ANTERIOR ("Súper Prompt — dirección artística") ya había diagnosticado
como Hallazgo 3 de monotonía visual y reemplazado por el catálogo maestro
de 767 módulos (`visual_fingerprint.py`). Esa sustitución nunca llegó
hasta aquí: `draft_visual_brief()` seguía leyendo el catálogo viejo.
Ahora usa `visual_fingerprint.seleccionar_huella()` — real, con las 10
dimensiones del catálogo maestro y anti-repetición calibrada. `families.py`
no se elimina: `elegir_familia_visual()` sigue siendo la fuente real y
correcta para UNA cosa distinta, no visual: qué superficie física de marca
sugerir (eso nunca fue parte del hallazgo de monotonía).
"""

from dataclasses import dataclass, field, replace

import memoria_fuerte as mf
import visual_fingerprint as vf
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
    familia_visual: str = ""          # etiqueta legible derivada de la huella (ver to_dict)
    primary_direction: str = ""       # catálogo maestro — visual_fingerprint.py
    secondary_direction: str = ""
    medium: str = ""
    palette: str = ""
    camera_optics: str = ""
    realism: str = ""
    visual_mechanism: str = ""
    material_sugerido: str = ""       # = huella.materiality
    superficie_marca_sugerida: str = ""  # de families.py — eje de marca, no de monotonía visual
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
    # Memoria fuerte (fuente #5, Contrato v4) — ver memoria_fuerte.py.
    # El CALLER debe comprobar este campo ANTES de compilar el prompt final:
    # draft_visual_brief() nunca lanza excepción ni detiene la generación por
    # sí solo (mismo patrón que validate_generation_contract()/negotiate()):
    # devuelve el problema para que quien orquesta decida, y así el bloqueo
    # ocurre antes de generar, nunca después (mandato Hotfix memoria fuerte).
    bloqueado_memoria_fuerte: bool = False
    motivos_bloqueo_memoria_fuerte: list = field(default_factory=list)

    def to_dict(self):
        from dataclasses import asdict
        return asdict(self)


PENDIENTE_CONTENIDO = "PENDIENTE_CONTENIDO — requiere redacción humana o de pipeline posterior sobre pieza ya verificada."


def verificar_diversidad_de_estilos(drafts, catalogo_maestro=None, n_esperado=None,
                                    registro_familias=None):
    """Hueco encontrado al reconciliar: legalmente-web exige 10 estilos
    distintos en un lote independiente de 10 piezas
    (`tenDistinctArtStylesForIndependentGeneralPieces`), con un catálogo de
    estilo declarado ABIERTO (`artStyleRegistryIsOpen: true`) — un string
    libre, validado sólo por unicidad.

    CORREGIDO (Parte XII, 16-sep-2026): el techo real ya NO es
    `min(8, n)` — esa cifra era el registro de 8 familias reducidas
    (`families.py`), exactamente el catálogo cerrado que este mismo
    hallazgo señalaba como el síntoma. El techo real hoy es
    `min(total_direcciones_del_catalogo_maestro, n)` — 504 direcciones,
    así que para cualquier lote realista (n<=504) el techo es `n`: la
    "biblioteca artística abierta" que antes era aspiracional ya existe.
    `registro_familias` se acepta solo por compatibilidad retroactiva de
    llamadas antiguas — usar `catalogo_maestro` siempre que sea posible.
    """
    n_esperado = n_esperado if n_esperado is not None else len(drafts)
    if catalogo_maestro is not None:
        total = sum(len(v) for v in catalogo_maestro.direcciones.values())
        fuente = f"catálogo maestro: {total} direcciones en {len(catalogo_maestro.direcciones)} categorías"
    elif registro_familias is not None:
        total = len(registro_familias.names())
        fuente = f"catálogo actual: {total} familias (compatibilidad retroactiva, families.py)"
    else:
        raise ValueError("verificar_diversidad_de_estilos requiere catalogo_maestro o, "
                         "por compatibilidad, registro_familias.")
    techo = min(total, n_esperado)
    distintos = {normaliza(d.familia_visual) for d in drafts if d.familia_visual}
    detalle = f"{len(distintos)}/{techo} estilos distintos ({fuente})."
    return len(distintos) >= techo, detalle


def draft_visual_brief(candidato, perfil_emocional, catalogo_maestro=None,
                       memoria_huellas=None, canal="", registro_familias=None,
                       memoria_visual=None, evitar_familias=(),
                       memoria_fuerte=None, reglas_rechazo_founder=None):
    """Construye el borrador. `perfil_emocional` es el dict que ya trae el
    candidato (`candidato.perfil_emocional`, poblado por emotion.py) — no se
    vuelve a derivar aquí: una capa posterior nunca reinfiere lo que una
    capa anterior ya decidió (mandato Paso 3).

    `catalogo_maestro` (`visual_fingerprint.MasterCatalog`) y
    `memoria_huellas` (`visual_fingerprint.FingerprintMemory`) son la
    fuente real de "LENGUAJE ARTÍSTICO" desde la Parte XII (16-sep-2026) —
    ver docstring del módulo. Si se omite `catalogo_maestro`, se carga el
    catálogo real por defecto (`MasterCatalog.load()`): nunca cae de vuelta
    al registro de 8 familias reducidas para la dirección artística.

    `registro_familias`/`memoria_visual`/`evitar_familias` sólo aportan
    `superficie_marca_sugerida` ahora (un eje de marca, no de monotonía
    visual) — se aceptan por compatibilidad, y son opcionales: sin ellos,
    `superficie_marca_sugerida` queda vacía en vez de forzar un valor.

    `memoria_fuerte` (`semantic_memory.SemanticMemory`, normalmente
    `memoria_fuerte.cargar_memoria_fuerte()`) y `reglas_rechazo_founder`
    (`memoria_fuerte.REGLAS_RECHAZO_FOUNDER` por defecto) son el wiring de
    la fuente #5 del Contrato v4 (Hotfix memoria fuerte, 16-sep-2026): antes
    de que el llamador compile el prompt final, este borrador ya trae
    `bloqueado_memoria_fuerte`/`motivos_bloqueo_memoria_fuerte` poblados si
    el candidato repite tema o puesta en escena de una pieza APROBADA/
    PUBLICADA/PRESELECCIONADA, o si su dirección artística reproduce un
    rechazo explícito del Founder (sección 4 de la fuente). `memoria_fuerte`
    es opcional (`None` desactiva la comparación contra piezas reales — no
    hay memoria fuerte que consultar sin ella); los 7 rechazos SÍ se
    verifican siempre por defecto, porque son reglas de diseño permanentes,
    no una memoria que dependa de estar poblada. Este método NUNCA lanza
    excepción ni detiene nada por sí solo: el llamador debe comprobar
    `bloqueado_memoria_fuerte` antes de seguir (mismo patrón que
    `validate_generation_contract()`/`negotiate()` en providers/base.py).
    """
    funcion, razon = derivar_funcion_visual(candidato.familia_editorial, candidato.necesidad)

    catalogo_maestro = catalogo_maestro or vf.MasterCatalog.load()
    memoria_huellas = memoria_huellas if memoria_huellas is not None else vf.FingerprintMemory()
    huella = vf.seleccionar_huella(candidato.candidate_id, catalogo=catalogo_maestro,
                                   memoria=memoria_huellas, canal=canal)

    superficie = ""
    if registro_familias is not None:
        familia_marca = elegir_familia_visual(registro_familias, memoria_visual, evitar_familias)
        superficie = (familia_marca.brand_surface_preferences[0]
                     if familia_marca.brand_surface_preferences else "")

    motivos_bloqueo = list(mf.verificar_rechazos_founder(huella, perfil_emocional,
                                                         reglas_rechazo_founder))
    if memoria_fuerte is not None:
        huella_comparacion = replace(
            candidato.fingerprint(), direccion_artistica=huella.primary_direction,
            material=huella.materiality, composicion=perfil_emocional.get("composicion", ""),
            camara=perfil_emocional.get("camara", ""), iluminacion=perfil_emocional.get("luz", ""))
        veredicto_tema = memoria_fuerte.evaluar(huella_comparacion)
        if veredicto_tema.bloquea:
            motivos_bloqueo.append(f"tema ya en memoria fuerte: {veredicto_tema.motivo} "
                                   f"(fuente: {mf.citar_fuente()})")
        veredicto_escena = memoria_fuerte.evaluar_visual_fuerte(huella_comparacion)
        if veredicto_escena.bloquea:
            motivos_bloqueo.append(f"puesta en escena ya en memoria fuerte: "
                                   f"{veredicto_escena.motivo} (fuente: {mf.citar_fuente()})")

    return VisualBriefDraft(
        content_id=candidato.candidate_id, visual_function=funcion, razon_funcion=razon,
        familia_visual=f"{huella.primary_direction} ({huella.medium.replace('_', ' ')})",
        primary_direction=huella.primary_direction, secondary_direction=huella.secondary_direction,
        medium=huella.medium, palette=huella.palette, camera_optics=huella.camera_optics,
        realism=huella.realism, visual_mechanism=huella.visual_mechanism,
        material_sugerido=huella.materiality, superficie_marca_sugerida=superficie,
        composicion=perfil_emocional.get("composicion", ""),
        camara=perfil_emocional.get("camara", ""),
        luz=perfil_emocional.get("luz", ""),
        escala=perfil_emocional.get("escala", ""),
        textura=perfil_emocional.get("textura", ""),
        ritmo=perfil_emocional.get("ritmo", ""),
        escena=PENDIENTE_CONTENIDO, metafora=PENDIENTE_CONTENIDO,
        autorizado=False,
        nota="Borrador pre-verificación. No autoriza producción ni sustituye brief.py.",
        bloqueado_memoria_fuerte=bool(motivos_bloqueo),
        motivos_bloqueo_memoria_fuerte=motivos_bloqueo)
