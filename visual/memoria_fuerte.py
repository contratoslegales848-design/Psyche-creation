"""Ingestión de la fuente #5 del Contrato v4 — Memoria fuerte real.

Autorización del Founder (16-sep-2026): construir el wiring real de memoria
fuerte al selector, "sólo construcción y prueba en la rama actual — NO
autoriza merge, deploy ni publicación". Este módulo puebla `SemanticMemory`
(`semantic_memory.py`) con los datos reales de
"LegalMente — Memoria fuerte: piezas validadas por el Founder y video real
(fuente #5, Contrato v4)"
(https://docs.google.com/document/d/1s4YUmSgBsEwYziXA5EaTG2qvo21qMuWTND-nlFAhhd8/edit)
y da al selector (`art_direction.py::draft_visual_brief()`) una forma de
consultarla antes de compilar un prompt — ver `docs/memoria-fuerte-fuente-5-registro-2026-09-16.md`
para el registro completo de esta incorporación.

HECHOS VERBATIM vs. ESTRUCTURACIÓN DEL AGENTE — la distinción importa
(mandato: "NO reinterpretes... son hechos verificados, no hipótesis de
estilo"): título, cifras y descripción visual de cada pieza abajo son
literales del documento (`titulo_original`, `metricas`). La asignación de
`materia`/`submateria`/`concepto_nucleo`/`familia_editorial` a los campos
que exige `SemanticFingerprint` (22 campos) SÍ es estructuración de este
agente sobre esos hechos — igual disciplina que
`demo_produccion_real_10_temas_nuevos.py` con los 10 temas reales de la
Parte XIII: autoría legítima de campos de infraestructura, nunca una
afirmación jurídica nueva ni una reclasificación del Founder.

INCOMPATIBILIDAD DETECTADA Y CÓMO SE RESOLVIÓ (mandato: "si la estructura de
SemanticMemory no admite bien los rechazos cualitativos... no fuerces el
dato — documenta la incompatibilidad y propón la extensión mínima"):

Los 7 rechazos de la sección 4 de la fuente NO son huellas de piezas
generadas — son reglas negativas en lenguaje natural sobre paleta, técnica y
composición ("paleta azul tinta + teal + ámbar + oro", "collage/grid
multipanel"), sin materia, concepto ni necesidad jurídica de por medio.
Forzarlos dentro de `MemoryEntry`/`SemanticFingerprint` sería incorrecto por
tres razones verificadas leyendo el código real:

1. `SemanticFingerprint.distancia_semantica()` (usado por
   `SemanticMemory.evaluar()`) pondera EJES_SEMANTICOS (materia, concepto,
   necesidad...) — un rechazo sin esos datos sólo contribuiría "sin dato" a
   esos ejes y NUNCA dispararía un bloqueo por esa vía, dando una falsa
   sensación de cobertura.
2. `SemanticMemory.evaluar()` no calcula `distancia_visual()` en absoluto
   hoy (confirmado leyendo `semantic_memory.py` completo) — por eso este
   módulo también agrega `SemanticMemory.evaluar_visual_fuerte()` (extensión
   mínima, additiva, no rompe `evaluar()` existente) para la comparación
   contra piezas APROBADAS/PUBLICADAS/PRESELECCIONADAS por puesta en escena.
3. Un rechazo como "paleta limpia inventada (azul tinta #0d1826 + teal +
   ámbar + oro)" no es "parecido a una pieza": es una COMBINACIÓN de
   atributos prohibida en cualquier pieza, sin importar tema. Eso no es un
   problema de distancia entre dos huellas — es un chequeo de reglas.

Extensión mínima elegida: `ReglaRechazoFounder` + `verificar_rechazos_founder()`
— una lista de reglas explícitas (id, descripción verbatim, condiciones de
palabras clave), comparadas por coincidencia textual determinista contra los
campos libres de la huella visual real (`visual_fingerprint.VisualFingerprint`)
y del perfil emocional — misma disciplina "determinista y auditable, sin ML"
que ya declara `semantic_fingerprint.py`. Es deliberadamente un mecanismo
SEPARADO de `SemanticMemory`, no una extensión forzada de su esquema.

LÍMITE HONESTO (matching de `verificar_rechazos_founder`): reutiliza
`memory.normaliza()`, que descarta tokens con puntuación pegada (p. ej.
"teal," se pierde entero, no se reduce a "teal") en vez de despuntuarlos —
comportamiento ya existente del helper compartido, no algo que este módulo
reimplemente por separado. Esto puede producir un FALSO NEGATIVO (una
coincidencia real que no se detecta porque su token venía con una coma
pegada) en textos con puntuación — nunca un falso positivo nuevo por esta
causa. Verificado que el vocabulario real del catálogo maestro no usa comas
dentro de un mismo valor de campo; sí aparecen en algunos valores de
`emotion.py` (p. ej. `"cercana, altura de los ojos"`), donde el riesgo es
real aunque acotado a esos campos.

LÍMITE HONESTO: en la etapa de `draft_visual_brief()`, `escena` y
`objeto_protagonista` todavía son `PENDIENTE_CONTENIDO` (no se redactan
hasta después, sobre una pieza ya verificada — ver `art_direction.py`). La
comparación de "arquitectura/escena/objeto de marca" contra memoria fuerte
que exige el mandato sólo puede ejecutarse HOY sobre lo que el borrador ya
conoce en ese punto: dirección artística, medio, material, composición,
cámara e iluminación. La superficie física de marca ya rota por otro
mecanismo existente (`elegir_familia_visual`/`memoria_visual`, no
duplicado aquí). Escena/objeto de marca concretos deberán compararse contra
memoria fuerte en la etapa posterior donde se redactan — eso NO se
implementa en este cambio.
"""

from dataclasses import dataclass, field

from memory import normaliza

# Palabras que niegan lo que sigue en el vocabulario real del catálogo
# maestro ("fotografía de hora dorada SIN DOMINANTE SEPIA", "van dyke brown
# SIN DOMINANTE sepia artificial" — verificado con grep real sobre
# policy/catalogo-maestro-v1.json). Sin este chequeo, RECHAZO-5 dispararía
# sobre una dirección que EXCLUYE sepia explícitamente — el falso positivo
# opuesto al que la regla existe para prevenir.
_NEGACIONES = frozenset({"sin", "no", "nunca", "jamas"})
from semantic_fingerprint import SemanticFingerprint
from semantic_memory import PRESELECCIONADA, PUBLICADA, SemanticMemory

FUENTE_DOCUMENTO_TITULO = ("LegalMente — Memoria fuerte: piezas validadas por el Founder y "
                          "video real (fuente #5, Contrato v4)")
FUENTE_DOCUMENTO_URL = "https://docs.google.com/document/d/1s4YUmSgBsEwYziXA5EaTG2qvo21qMuWTND-nlFAhhd8/edit"
LOTE_ID_FUENTE_5 = "fuente-5-memoria-fuerte-2026-09-16"


def citar_fuente():
    return f"{FUENTE_DOCUMENTO_TITULO}: {FUENTE_DOCUMENTO_URL}"


# ---------------------------------------------------------------------------
# Secciones 1 y 2 — piezas con rendimiento real más alto / mayor impacto
# histórico. PUBLICADA: son piezas ya publicadas, con métricas reales
# verificadas por el Founder en la Biblioteca de contenido de Facebook
# (sección 1, 15-sep-2026) o en capturas de jul-2026 (sección 2).
# `titulo_original` y `metricas` son literales del documento; el resto de
# campos es estructuración de este agente (ver docstring del módulo).
PIEZAS_PUBLICADAS = (
    dict(content_id="MF-01-SERVIDUMBRE-PASO",
         titulo_original="La servidumbre de paso... (derecho de paso vs. propiedad) — LA MÁS VIRAL DE TODAS",
         materia="civil", submateria="servidumbres",
         concepto_nucleo="servidumbre de paso frente a propiedad",
         metricas={"vistas": 13700, "interacciones": 560}),
    dict(content_id="MF-02-BECCARIA",
         titulo_original="Beccaria cambió la idea del castigo (figura histórica + hito del derecho penal)",
         materia="historia_del_derecho", submateria="juristas",
         concepto_nucleo="Beccaria y el cambio en la idea del castigo",
         metricas={"vistas": 10244, "interacciones": 413}),
    dict(content_id="MF-03-SOSPECHA-NO-RESPONSABILIDAD",
         titulo_original="Sospecha no es responsabilidad penal (mito desmentido + presunción de inocencia)",
         materia="penal", submateria="presuncion_de_inocencia",
         concepto_nucleo="la sospecha no equivale a responsabilidad penal",
         metricas={"vistas": 8407, "interacciones": 351}),
    dict(content_id="MF-04-ANTIGONA",
         titulo_original="Antígona: cuando obedecer la ley entra en conflicto con obedecer la "
                         "conciencia (Derecho y Literatura, Sófocles) — MAYOR INTERACCIÓN ABSOLUTA",
         materia="historia_del_derecho", submateria="derecho_y_literatura",
         concepto_nucleo="conflicto entre obedecer la ley y obedecer la conciencia (Antígona)",
         metricas={"vistas": 7420, "interacciones": 576}),
    dict(content_id="MF-05-LINDEROS",
         titulo_original="Una cerca puede mostrar dónde alguien cree que termina su terreno... (linderos)",
         materia="civil", submateria="linderos",
         concepto_nucleo="una cerca y la creencia sobre dónde termina un terreno",
         metricas={"vistas": 6862, "interacciones": 233}),
    dict(content_id="MF-06-MEDIDA-CAUTELAR",
         titulo_original="Una medida cautelar no es una sentencia (provisionalidad procesal)",
         materia="procesal", submateria="provisionalidad_procesal",
         concepto_nucleo="una medida cautelar no es una sentencia",
         metricas={"vistas": 6114, "interacciones": 398}),
    dict(content_id="MF-07-PROPIEDAD-POSESION-USUFRUCTO",
         titulo_original="Una misma casa puede involucrar relaciones jurídicas distintas "
                         "(propiedad/posesión/usufructo)",
         materia="civil", submateria="propiedad_posesion_usufructo",
         concepto_nucleo="una misma casa y relaciones jurídicas distintas sobre ella",
         metricas={"vistas": 3039, "interacciones": 166}),
    dict(content_id="MF-08-DANO-PRUEBA",
         titulo_original="Un daño no se acredita únicamente diciendo que ocurrió (daños/prueba)",
         materia="civil", submateria="danos_prueba",
         concepto_nucleo="un daño no se acredita únicamente diciendo que ocurrió",
         metricas={"vistas": 2610, "interacciones": 89}),
    dict(content_id="MF-09-COPIA-ORIGINAL",
         titulo_original="Una copia puede parecer idéntica al original (prueba documental)",
         materia="procesal", submateria="prueba_documental",
         concepto_nucleo="una copia puede parecer idéntica al original",
         metricas={"vistas": 2227, "interacciones": 86}),
    dict(content_id="MF-10-CARNELUTTI",
         titulo_original="Carnelutti — \"El abogado no defiende al culpable ni al inocente: "
                         "defiende al hombre\"",
         materia="historia_del_derecho", submateria="juristas",
         concepto_nucleo="el abogado no defiende al culpable ni al inocente: defiende al hombre",
         direccion_artistica="pergamino dorado con cita larga legible",
         composicion="pergamino con cita larga + dos abogados de espaldas mirándolo",
         material="pergamino / banda dorada",
         metricas={"likes": 2224, "compartidos": 1195}),
    dict(content_id="MF-11-ONASSIS",
         titulo_original="VIDEO — retrato de Aristóteles Onassis con frase en mayúsculas bold "
                         "sobre el retrato",
         materia="historia_del_derecho", submateria="cultura_juridica",
         concepto_nucleo="retrato de Aristóteles Onassis con frase en mayúsculas bold",
         direccion_artistica="retrato con frase en mayúsculas bold superpuesta",
         formato="video",
         metricas={"likes": 3686, "compartidos": 4268}),
    dict(content_id="MF-12-CALAMANDREI",
         titulo_original="VIDEO — Calamandrei — escena de tribunal pintada arriba + bloque de "
                         "papel rasgado abajo con cita larga en serif oscura legible",
         materia="historia_del_derecho", submateria="juristas",
         concepto_nucleo="Calamandrei: escena de tribunal pintada y papel rasgado con cita",
         direccion_artistica="escena de tribunal pintada arriba + papel rasgado abajo",
         material="papel rasgado",
         formato="video",
         metricas={"likes": 1305, "compartidos": 978}),
)

# Sección 5 — validado positivamente (confirmación explícita, no sólo
# ausencia de rechazo). PRESELECCIONADA por instrucción expresa del Founder
# en este mandato (no PUBLICADA/APROBADA: son señales de aprobación de
# dirección, no piezas individuales publicadas con métricas propias, salvo
# el Poder Notarial y el Reel de Couture, que sí se produjeron).
PIEZAS_PRESELECCIONADAS = (
    dict(content_id="MF-13-SURREALISTA-ESTRUCTURADO",
         titulo_original="Formato surrealista estructurado (fusión de partes del cuerpo humano "
                         "con objetos jurídicos, estructura Título/Frase/Remate) — el Founder "
                         "confirmó \"me gustaron\" y pidió una segunda tanda",
         materia="", submateria="",
         concepto_nucleo="formato surrealista estructurado validado por el Founder",
         direccion_artistica="surrealismo estructurado: fusión de partes del cuerpo humano con "
                             "objetos jurídicos",
         composicion="estructura Título/Frase/Remate"),
    dict(content_id="MF-14-CITAS-PERILLO-IUS",
         titulo_original="Citas reales incorporadas de @perillo_ius: Luigi Lucchini (\"La culpa "
                         "y no la inocencia debe ser demostrada\") y José Cafferata Nores (\"Son "
                         "las pruebas, no los jueces, los que condenan\") — usadas en el lote "
                         "surrealista final",
         materia="penal", submateria="prueba_penal",
         concepto_nucleo="citas reales de juristas (Lucchini, Cafferata Nores) sobre culpa y prueba"),
    dict(content_id="MF-15-PODER-NOTARIAL",
         titulo_original="Pieza del Poder Notarial (\"Un poder mal dado abre todas tus puertas\") "
                         "— producida con éxito como imagen; el Founder decidió animarla en video",
         materia="civil", submateria="poder_notarial",
         concepto_nucleo="un poder mal dado abre todas tus puertas"),
    dict(content_id="MF-16-REEL-COUTURE",
         titulo_original="Reel \"El primer mandamiento del abogado: estudiar\" (cita de Eduardo "
                         "Couture) — elegido por el Founder como primer Reel para impulsar con "
                         "pauta paga real",
         materia="historia_del_derecho", submateria="juristas",
         concepto_nucleo="el primer mandamiento del abogado: estudiar (cita de Couture)",
         formato="video"),
)


def _fingerprint_de(registro):
    campos = {k: v for k, v in registro.items()
             if k in SemanticFingerprint.__dataclass_fields__}
    return SemanticFingerprint(**campos)


def cargar_memoria_fuerte(umbral=None):
    """Construye una `SemanticMemory` poblada exclusivamente con la fuente
    #5 — deliberadamente separada de la memoria de ejecución normal
    (`SemanticMemory()` vacía que instancia `production_run.py` para
    generación/descarte de la corrida en curso): mezclar ambas confundiría
    "esto ya se contó en este lote" con "esto ya lo aprobó el Founder de
    verdad", que son señales distintas.
    """
    memoria = SemanticMemory() if umbral is None else SemanticMemory(umbral=umbral)
    for registro in PIEZAS_PUBLICADAS:
        memoria.record(_fingerprint_de(registro), PUBLICADA, lote_id=LOTE_ID_FUENTE_5)
    for registro in PIEZAS_PRESELECCIONADAS:
        memoria.record(_fingerprint_de(registro), PRESELECCIONADA, lote_id=LOTE_ID_FUENTE_5)
    return memoria


# ---------------------------------------------------------------------------
# Sección 4 — 7 rechazos explícitos del Founder. Reglas negativas explícitas,
# NO huellas (ver docstring del módulo). Coincidencia textual determinista
# contra los campos libres de la huella visual real y del perfil emocional.

@dataclass
class ReglaRechazoFounder:
    id: str
    descripcion: str  # cita verbatim de la sección 4 de la fuente
    disyunciones: tuple  # dispara si CUALQUIER condición se cumple
    # condición = tupla de grupos; se cumple si TODOS sus grupos coinciden
    # grupo = tupla de sinónimos; coincide si CUALQUIERA aparece en el texto
    palabras_ausentes: tuple = ()  # si aparece cualquiera, la regla NO dispara

    def to_dict(self):
        return {"id": self.id, "descripcion": self.descripcion}


REGLAS_RECHAZO_FOUNDER = (
    ReglaRechazoFounder(
        id="RECHAZO-1-PALETA-LIMPIA-INVENTADA",
        descripcion="Paleta \"limpia\" inventada (azul tinta #0d1826 + teal + ámbar + oro) — "
                    "rechazada, \"fea\"/\"asquerosa\".",
        disyunciones=((("azul tinta", "0d1826"), ("teal",), ("ambar",), ("oro",)),)),
    ReglaRechazoFounder(
        id="RECHAZO-2-HIPERREALISTA-4-CAPAS-TEXTO",
        descripcion="Fotografía hiperrealista con 4 capas de texto (máximas, hitos históricos, "
                    "ciencia, naturaleza, símbolos, literatura) — rechazada: \"no me gustaron, "
                    "no me gustan para mi página\".",
        disyunciones=((("hiperrealista", "hiperrealismo"),
                       ("capas de texto", "4 capas", "cuatro capas")),)),
    ReglaRechazoFounder(
        id="RECHAZO-3-OBJETO-FRIO-SIN-FIGURA-HUMANA",
        descripcion="Escenas de objeto/metáfora fría sin figura humana con emoción real (manos, "
                    "puertas, cadenas) — rechazadas: \"horribles\"/\"basura\", indignas de la "
                    "página.",
        disyunciones=((("manos", "mano"),), (("puerta", "puertas"),), (("cadena", "cadenas"),)),
        palabras_ausentes=("humana", "persona", "rostro", "figura humana", "hombre", "mujer")),
    ReglaRechazoFounder(
        id="RECHAZO-4-FLAT-ILLUSTRATION-BOLD",
        descripcion="Flat illustration en colores bold (primer intento del Lote \"Cotidianas\") — "
                    "rechazada: \"feo y simple sin llamar a la interacción\".",
        disyunciones=((("flat illustration", "ilustracion plana"), ("bold",)),)),
    ReglaRechazoFounder(
        id="RECHAZO-5-SEPIA-MURKY-ILEGIBLE",
        descripcion="Sepia monocromo plano y negrura murky ilegible — rechazados de forma "
                    "permanente.",
        disyunciones=((("sepia",),), (("murky",),), (("monocromo",), ("plano",)))),
    ReglaRechazoFounder(
        id="RECHAZO-6-NEGATIVE-SPACE-BANDS",
        descripcion="Prompts con \"negative space upper/lower band\" — rechazados porque generan "
                    "bandas/recuadros separados; reemplazados por la regla full-bleed.",
        disyunciones=((("negative space", "espacio negativo"),
                       ("upper band", "lower band", "banda superior", "banda inferior")),)),
    ReglaRechazoFounder(
        id="RECHAZO-7-COLLAGE-GRID-MULTIPANEL",
        descripcion="Formato collage/grid multipanel como sustituto de piezas individuales — "
                    "rechazado.",
        disyunciones=((("collage",),), (("grid multipanel", "multipanel", "grid multi panel"),))),
)

_CAMPOS_HUELLA = ("primary_direction", "secondary_direction", "medium", "lighting",
                  "composition", "camera_optics", "palette", "materiality", "realism",
                  "visual_mechanism")
_CAMPOS_PERFIL_EMOCIONAL = ("composicion", "camara", "luz", "escala", "textura", "ritmo")


def _aparece_sin_negacion(tokens_texto, frase):
    """¿Aparece `frase` en `tokens_texto` sin que la precedan `sin`/`no`/
    `nunca`/`jamás` (hasta 2 tokens antes)? Ver `_NEGACIONES` — evita que
    "sin dominante sepia" cuente como una mención positiva de sepia."""
    ft = normaliza(frase).split()
    n = len(ft)
    if not ft:
        return False
    for i in range(len(tokens_texto) - n + 1):
        if tokens_texto[i:i + n] != ft:
            continue
        precedentes = tokens_texto[max(0, i - 2):i]
        if any(p in _NEGACIONES for p in precedentes):
            continue
        return True
    return False


def _condicion_cumple(tokens_texto, condicion):
    return all(any(_aparece_sin_negacion(tokens_texto, s) for s in grupo) for grupo in condicion)


def _regla_dispara(tokens_texto, regla):
    if any(_aparece_sin_negacion(tokens_texto, p) for p in regla.palabras_ausentes):
        return False
    return any(_condicion_cumple(tokens_texto, cond) for cond in regla.disyunciones)


def verificar_rechazos_founder(huella, perfil_emocional=None, reglas=None):
    """Compara la huella visual real (y, si se da, el perfil emocional) del
    candidato contra los 7 rechazos explícitos de la sección 4 de la fuente
    #5. Devuelve la lista de violaciones (vacía si no hay ninguna) — cita el
    documento en cada una, per mandato §5 ("citando el documento como
    fuente")."""
    reglas = reglas if reglas is not None else REGLAS_RECHAZO_FOUNDER
    campos = [getattr(huella, c, "") for c in _CAMPOS_HUELLA]
    if perfil_emocional:
        campos += [perfil_emocional.get(c, "") for c in _CAMPOS_PERFIL_EMOCIONAL]
    tokens = normaliza(" ".join(c for c in campos if c)).split()
    if not tokens:
        return []
    return [f"{r.id}: coincide con rechazo explícito del Founder — {r.descripcion} "
           f"(fuente: {citar_fuente()})"
           for r in reglas if _regla_dispara(tokens, r)]
