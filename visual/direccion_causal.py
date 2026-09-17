"""Compilador causal de dirección artística — Mandato Maestro, continuación
(17-sep-2026): "la dirección artística debe seleccionarse DESPUÉS de
entender qué comunica la pieza."

PROBLEMA cerrado por este módulo (documentado como gap abierto en
`docs/mandato-maestro-cierre-2026-09-17.md`, fila 1 de la tabla
Drive↔código): `visual_fingerprint.seleccionar_huella()` elegía las 10
dimensiones de la huella por anti-repetición pura, sin leer nada del
candidato — el orden real era DIRECCIÓN ARTÍSTICA primero, significado
después (invertido respecto al Contrato v4 §4-5). Ese diseño era
deliberado por una razón real (no fabricar "concepto X pertenece a estilo
Y" sin evidencia) — la instrucción explícita de continuación pide construir
el orden causal SIN caer en esa tabla arbitraria. Este módulo hace
exactamente eso: separa SIGNIFICADO (A) de TRADUCCIÓN VISUAL (B) de
DIRECCIÓN ARTÍSTICA (C, filtrada por compatibilidad con A+B), usando
únicamente:

  1. campos que YA existen y son reales en `TopicCandidate`
     (necesidad, relacion, consecuencia, profundidad, familia_editorial);
  2. clasificaciones estructurales deterministas sobre esos campos, mismo
     patrón que `pedagogia.py`/`art_direction.FUNCION_POR_NECESIDAD`: son
     categorías editoriales, no afirmaciones jurídicas ni "el Founder
     prefiere";
  3. el VOCABULARIO REAL del catálogo maestro (`realism`, 20 valores;
     `visual_mechanism`, 46 valores) — la compatibilidad se calcula por
     COINCIDENCIA TEXTUAL auditable entre las palabras clave de cada
     categoría de significado y las palabras reales del catálogo (mismo
     mecanismo de solapamiento de tokens que `semantic_fingerprint.py` ya
     usa y en el que este repositorio ya confía), nunca por una tabla
     fija "concepto → estilo" inventada.

QUÉ SÍ SE CAUSA HOY (evidencia real, ver `test_direccion_causal.py`):
`grado_abstraccion` (de `profundidad`, ya real) restringe qué valores de
`realism` son elegibles; `movimiento_juridico` (de `necesidad`, ya real)
restringe qué valores de `visual_mechanism` son elegibles. Las 8
dimensiones restantes de la huella (`primary_direction`, `secondary_
direction`, `medium`, `lighting`, `composition`, `camera_optics`,
`palette`, `materiality`) SIGUEN rotando por anti-repetición pura sobre la
biblioteca abierta completa — filtrarlas también exigiría el mismo tipo de
afinidad inventada que este módulo evita a propósito. Es una causalidad
PARCIAL, real y auditable, no una causalidad total fingida.

QUÉ NO SE FABRICA (honestidad declarada, no oculta): `objeto_protagonista`,
`metáfora` y `escena` siguen `PENDIENTE_CONTENIDO` — son contenido
creativo/editorial concreto sobre una pieza verificada, no infraestructura
(mismo límite que `art_direction.py` ya declaraba). `presencia_humana`,
`contraste` y `temporalidad` se calculan y se reportan como parte del
SIGNIFICADO (el mandato los pide explícitamente) pero HOY no se usan para
filtrar ninguna dimensión del catálogo: no se encontró un eje real y
auditable del catálogo maestro al que asociarlos sin inventar una
correspondencia. Quedan disponibles para una extensión futura si aparece
esa evidencia — no se finge que ya filtran algo que no filtran.
"""

from dataclasses import dataclass, field

from memory import normaliza, normaliza_texto_libre as _texto_libre
from visual_fingerprint import (
    MasterCatalog, VisualFingerprint, seleccionar_huella as _seleccionar_huella_base,
)


# `_texto_libre` (bug real encontrado y corregido al construir este módulo:
# ver test_direccion_causal.py) ahora vive en `memory.normaliza_texto_libre`
# — promovida ahí (17-sep-2026, continuación safe zone) para que
# `safe_zone.py` la reutilice en vez de duplicarla otra vez. El alias local
# se conserva para no romper las llamadas `dc._texto_libre(...)` ya
# existentes en este módulo y en sus tests.

CONCRETO, INTERMEDIO, ABSTRACTO = "CONCRETO", "INTERMEDIO", "ABSTRACTO"

# grado_abstraccion <- profundidad (ya real en TopicCandidate/editorial-universe-v1.json:
# profundidades = base/media/alta). Mapeo directo, sin inventar un eje nuevo.
GRADO_ABSTRACCION_POR_PROFUNDIDAD = {"base": CONCRETO, "media": INTERMEDIO, "alta": ABSTRACTO}

# realism (20 valores reales, policy/catalogo-maestro-v1.json) clasificados
# por su propio texto -- ninguno se inventa, los 20 están cubiertos.
REALISM_POR_GRADO = {
    CONCRETO: (
        "hiperrealista", "fotorrealista", "naturalista", "realista editorial",
        "realista pictórico", "documental", "científico", "técnico",
        "arqueológico reconstructivo", "museográfico",
    ),
    INTERMEDIO: ("semi-realista", "estilización moderada", "materialista", "minimalista"),
    ABSTRACTO: (
        "estilización geométrica", "conceptual figurativo", "conceptual abstracto",
        "diagramático", "simbólico", "onírico controlado",
    ),
}

# movimiento_juridico <- necesidad (15 valores reales, editorial-universe-v1.json).
# Cada necesidad cae en EXACTAMENTE una categoría -- las 15 están cubiertas.
MOVIMIENTO_POR_NECESIDAD = {
    "actuar": "TRANSFORMACION", "aplicar": "TRANSFORMACION",
    "actualizar": "TRANSFORMACION", "corregir": "TRANSFORMACION",
    "decidir": "RUPTURA_TENSION", "reclamar": "RUPTURA_TENSION",
    "entender": "REVELACION", "detectar": "REVELACION", "reflexionar": "REVELACION",
    "cumplir": "CONSERVACION", "recordar": "CONSERVACION",
    "prevenir": "PREVENCION_UMBRAL", "prepararse": "PREVENCION_UMBRAL",
    "acordar": "VINCULO",
    "distinguir": "CONTRASTE",
}

# Palabras clave REALES tomadas literalmente del vocabulario de
# `visual_mechanism` (46 valores) -- cada entrada de abajo es una
# subcadena que existe de verdad en al menos un valor real del catálogo
# (verificado por test_direccion_causal.py::test_toda_palabra_clave_existe_en_el_catalogo_real).
# Esto es coincidencia textual auditable, no una tabla concepto->estilo:
# la categoría es editorial (movimiento jurídico derivado de `necesidad`,
# ya real), las palabras son literales del catálogo del Founder.
PALABRAS_CLAVE_MECANISMO = {
    "TRANSFORMACION": ("transformación material", "cambio de estado", "cristalización",
                       "revelado fotográfico", "anamorfosis"),
    "RUPTURA_TENSION": ("fractura controlada", "tensión de cuerda", "equilibrio precario",
                        "simetría rota", "interrupción del patrón"),
    "REVELACION": ("documento revelándose", "luz que revela información", "transparencia",
                   "capa superpuesta", "archivo desclasificado visual"),
    "CONSERVACION": ("huella/impresión", "capas geológicas", "estratificación",
                     "escala monumental", "repetición serial"),
    "PREVENCION_UMBRAL": ("umbral/puerta", "sombra que oculta información", "vacío/ausencia",
                          "objeto suspendido", "laberinto abstracto"),
    "VINCULO": ("nodo-red", "sutura/reparación", "capa superpuesta", "doble exposición"),
    "CONTRASTE": ("contraste de escala", "simetría rota", "fragmento faltante", "desplazamiento"),
}

# presencia_humana <- familia_editorial. Mismo criterio de evidencia que
# pedagogia.FAMILIAS_NARRATIVA: familias cuya propia funcion_editorial
# declara retratar/narrar a una persona.
FAMILIAS_PRESENCIA_HUMANA_ALTA = frozenset({
    "jurista", "caso_cotidiano", "caso_historico", "cultura_juridica",
})


class DireccionCausalError(ValueError):
    pass


@dataclass
class Significado:
    """(A) — qué comunica la pieza, antes de pensar en ningún recurso visual."""
    concepto: str = ""
    tension: str = ""              # = candidato.relacion, ya real
    movimiento_juridico: str = ""
    razon_movimiento: str = ""
    temporalidad: str = ""         # reportado, no wireado a ningún filtro hoy
    presencia_humana: str = ""     # reportado, no wireado a ningún filtro hoy
    grado_abstraccion: str = ""
    razon_abstraccion: str = ""
    contraste: str = ""            # reportado, no wireado a ningún filtro hoy
    objeto_protagonista: str = ""  # PENDIENTE_CONTENIDO deliberado

    def to_dict(self):
        from dataclasses import asdict
        return asdict(self)


def derivar_significado(candidato):
    """Determinista, auditable: cada campo cita el campo real del que sale."""
    nec = normaliza(candidato.necesidad)
    prof = normaliza(getattr(candidato, "profundidad", ""))

    movimiento = MOVIMIENTO_POR_NECESIDAD.get(nec)
    razon_mov = (f"necesidad {candidato.necesidad!r} -> {movimiento}" if movimiento
                else f"necesidad {candidato.necesidad!r} sin categoría de movimiento declarada.")

    grado = GRADO_ABSTRACCION_POR_PROFUNDIDAD.get(prof)
    razon_abs = (f"profundidad {candidato.profundidad!r} -> {grado}" if grado
                else f"profundidad {getattr(candidato, 'profundidad', '')!r} sin mapeo declarado.")

    fam = normaliza(candidato.familia_editorial)
    presencia = ("ALTA" if fam in {normaliza(f) for f in FAMILIAS_PRESENCIA_HUMANA_ALTA}
                else "BAJA")

    # temporalidad: eje reportado sin evidencia catalogada suficiente para
    # una clasificación fina; se declara INDETERMINADA en vez de inventar
    # una regla sin respaldo (mismo criterio fail-closed del resto del repo).
    temporalidad = "INDETERMINADA"

    contraste = "ALTO" if getattr(candidato, "consecuencia", "") else "BAJO"

    return Significado(
        concepto=candidato.concepto_nucleo, tension=candidato.relacion,
        movimiento_juridico=movimiento or "SIN_CLASIFICAR", razon_movimiento=razon_mov,
        temporalidad=temporalidad, presencia_humana=presencia,
        grado_abstraccion=grado or "SIN_CLASIFICAR", razon_abstraccion=razon_abs,
        contraste=contraste, objeto_protagonista="PENDIENTE_CONTENIDO")


def _valores_permitidos_realism(significado):
    return REALISM_POR_GRADO.get(significado.grado_abstraccion)


def _valores_permitidos_mecanismo(catalogo, significado):
    palabras = PALABRAS_CLAVE_MECANISMO.get(significado.movimiento_juridico)
    if not palabras:
        return None
    pool = catalogo.valores("visual_mechanism")
    claves = [_texto_libre(p) for p in palabras]
    claves = [c for c in claves if c]  # nunca una clave vacía puede "coincidir" con todo
    if not claves:
        return None
    permitidos = [v for v in pool if any(c in _texto_libre(v) for c in claves)]
    return permitidos or None


def _catalogo_causal(catalogo, significado):
    """Vista del catálogo con realism/visual_mechanism restringidos por
    significado — las otras 8 dimensiones (incluida la biblioteca de 504
    direcciones) quedan intactas y abiertas: no hay evidencia real para
    restringirlas sin fabricar afinidad."""
    aux = dict(catalogo.auxiliares)
    explicacion = []

    permitidos_realism = _valores_permitidos_realism(significado)
    if permitidos_realism:
        aux["realism"] = list(permitidos_realism)
        explicacion.append(
            f"realism restringido a {len(permitidos_realism)}/{len(catalogo.valores('realism'))} "
            f"valores compatibles con grado_abstraccion={significado.grado_abstraccion} "
            f"({significado.razon_abstraccion}).")
    else:
        explicacion.append(
            f"realism sin restricción: grado_abstraccion={significado.grado_abstraccion!r} "
            "no tiene bucket declarado.")

    permitidos_mecanismo = _valores_permitidos_mecanismo(catalogo, significado)
    if permitidos_mecanismo:
        aux["visual_mechanism"] = permitidos_mecanismo
        explicacion.append(
            f"visual_mechanism restringido a {len(permitidos_mecanismo)}/"
            f"{len(catalogo.valores('visual_mechanism'))} valores con parentesco textual a "
            f"movimiento_juridico={significado.movimiento_juridico} "
            f"({significado.razon_movimiento}).")
    else:
        explicacion.append(
            f"visual_mechanism sin restricción: movimiento_juridico="
            f"{significado.movimiento_juridico!r} no tiene palabras clave declaradas o ninguna "
            "coincidió en el catálogo real.")

    return MasterCatalog(catalogo.direcciones, aux), explicacion


def seleccionar_direccion_causal(candidato, catalogo=None, memoria=None, canal="", **kw):
    """CONCEPTO -> TENSIÓN -> MOVIMIENTO/GRADO DE ABSTRACCIÓN (significado,
    real) -> RESTRICCIÓN del catálogo (realism + visual_mechanism, por
    coincidencia textual auditable) -> SELECCIÓN (anti-repetición + memoria,
    reutilizando `visual_fingerprint.seleccionar_huella()` sin duplicar su
    lógica). Devuelve (VisualFingerprint, Significado, explicación combinada).

    `**kw` se reenvía a `seleccionar_huella()` (memoria, canal, umbrales de
    mutación) — mismo contrato, nunca lanza excepción por sí solo.
    """
    catalogo = catalogo or MasterCatalog.load()
    significado = derivar_significado(candidato)
    catalogo_causal, explicacion_filtro = _catalogo_causal(catalogo, significado)
    huella = _seleccionar_huella_base(candidato.candidate_id, catalogo=catalogo_causal,
                                      memoria=memoria, canal=canal, **kw)
    huella.explanation = list(explicacion_filtro) + list(huella.explanation)
    return huella, significado, huella.explanation
