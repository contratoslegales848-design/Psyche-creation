"""Importador del corpus histórico real de LegalMente.

El motor tenía memoria implementada pero no MEMORIA DE SU PROPIA HISTORIA:
descubría como nuevo lo que LegalMente ya había contado 174 veces.

FUENTE (snapshot inmutable en `corpus/`, nunca se modifica):
  - `banco-v3-doc1-sistema-y-catalogo.txt` — Drive 1WOXtbYMQYx2yV2RlvCkV2J0hc6CMkqksuBpitZ67KK4
    Aporta: tema (24), guion (slug), titular/hook y metáfora de cada pieza.
  - `banco-v3-doc2-tabla.txt` — Drive 1MmDn8-1RGk_wpx9BNWHIo7s3wSsg6SMxaj5ouCwc-p0
    Aporta: ID LM-xxx, carril, escuela, escenario, encuadre, paleta, mecanismo,
    objeto de marca y aspecto.
Ambos se unen por el slug del guion y se validan cruzadamente (174 = 174).

REGLA CENTRAL DE ESTE MÓDULO: **no inventar**. El corpus histórico no declara
familia editorial, necesidad, rol del lector ni ángulo — no existían como eje
cuando se escribió. Se infieren SOLO cuando hay evidencia léxica real, y cada
inferencia viaja con su `confianza_extraccion`. Donde no hay evidencia se
escribe UNKNOWN, porque una clasificación falsa contamina la memoria de forma
irreversible: haría que el motor creyera haber cubierto una puerta editorial
que en realidad nunca abrió.

IDEMPOTENTE: la migración se identifica por `content_id` (LM-xxx). Re-ejecutarla
no duplica memoria — comprueba qué IDs ya están registrados y sólo añade los que
faltan.

Este módulo no verifica Derecho y no abre gates. Lee producción pasada.
"""

import json
import re
from dataclasses import dataclass, field, asdict
from pathlib import Path

from semantic_fingerprint import SemanticFingerprint

CORPUS_DIR = Path(__file__).resolve().parent.parent / "corpus"
DOC1 = CORPUS_DIR / "guiones-doc1.json"
DOC2 = CORPUS_DIR / "banco-v3-doc2-tabla.txt"

UNKNOWN = "UNKNOWN"

# Niveles de confianza de extracción. Se declaran por campo inferido.
ALTA = "ALTA"        # marcador explícito en el slug ("mito-", "concepto-")
MEDIA = "MEDIA"      # patrón léxico fuerte ("-vs-", "no-es-")
BAJA = "BAJA"        # forma narrativa reconocible, sin marcador de familia
NINGUNA = "NINGUNA"  # sin evidencia: el campo queda UNKNOWN

# --- tema del banco -> materia del motor -----------------------------------
# `migracion` y `derechos_humanos` no existían en materias-seed-v1: el corpus
# histórico demuestra que sí son zonas reales de producción. Se registran aquí
# como hallazgo, no se fuerzan a una materia vecina.
TEMA_A_MATERIA = {
    "ADMINISTRATIVO": "administrativo",
    "CIENCIAS-FORENSES": "criminalistica_forense",
    "CONSUMIDOR": "consumo",
    "CONTRATOS": "civil",
    "CRIMINALISTICA": "criminalistica_forense",
    "DATOS": "digital_datos",
    "DERECHO-PENAL": "penal",
    "DERECHOS-HUMANOS": "constitucional",
    "DIGITAL": "digital_datos",
    "DUE-DILIGENCE": "corporativo_compliance",
    "FAMILIA": "familiar",
    "FISCAL": "fiscal",
    "INMOBILIARIO": "inmobiliario",
    "INTERNACIONAL": "internacional_privado",
    "JUICIOS": "procesal",
    "LABORAL": "laboral",
    "LITERATURA-JURIDICA": "cultura_y_literatura_juridica",
    "MIGRACION": "migracion",
    "OBLIGACIONES": "civil",
    "PRINCIPIOS": "teoria_y_filosofia",
    "PROPIEDAD-INTELECTUAL": "propiedad_intelectual",
    "RIESGOS-PENALES-CONTRACTUALES": "penal",
    "SOCIETARIO": "mercantil",
    "USO-DE-SUELO": "administrativo",
}

# Marcadores EXPLÍCITOS de familia editorial en el slug. Evidencia de nivel ALTA:
# quien escribió el guion nombró la puerta editorial en el propio identificador.
PREFIJO_FAMILIA = {
    "mito": "mito",
    "concepto": "concepto",
    "diferencia": "diferencia",
    "comparacion": "diferencia",
    "pasos": "primeros_pasos",
    "listado": "checklist",
    "consejo": "asesoria_orientacion",
    "pregunta": "duda_frecuente",
    "tecnicismo": "lenguaje_juridico_explicado",
    "cita": "maxima_aforismo",
    "consecuencia": "consecuencia",
    "situacion": "caso_cotidiano",
    "narrativa": "caso_cotidiano",
    "historia": "caso_cotidiano",
}

# Familia -> necesidad y rol por defecto, tomados del registro editorial. Sólo
# se aplican cuando la familia se pudo inferir: si no hay familia, tampoco hay
# necesidad que derivar.
NECESIDAD_POR_FAMILIA = {
    "mito": "corregir", "concepto": "entender", "diferencia": "distinguir",
    "primeros_pasos": "actuar", "checklist": "prepararse",
    "asesoria_orientacion": "prepararse", "duda_frecuente": "entender",
    "lenguaje_juridico_explicado": "entender", "maxima_aforismo": "recordar",
    "consecuencia": "prevenir", "caso_cotidiano": "entender",
    "confusion_habitual": "distinguir",
}


@dataclass
class RegistroHistorico:
    """Una pieza del corpus, con la procedencia y la confianza de cada campo."""

    fuente: str = ""
    content_id: str = ""
    fecha: str = ""
    guion: str = ""
    tema_original: str = ""
    titular: str = ""
    materia: str = UNKNOWN
    submateria: str = UNKNOWN
    concepto_nucleo: str = UNKNOWN
    familia_editorial: str = UNKNOWN
    necesidad: str = UNKNOWN
    pregunta_resuelta: str = UNKNOWN
    angulo: str = UNKNOWN
    contexto_funcional: str = UNKNOWN
    rol_lector: str = UNKNOWN
    consecuencia: str = UNKNOWN
    hook: str = ""
    formato: str = UNKNOWN
    metafora: str = ""
    direccion_artistica: str = ""
    escena: str = ""
    composicion: str = ""
    objeto_protagonista: str = ""
    material: str = ""
    camara: str = ""
    iluminacion: str = UNKNOWN
    emocion: str = UNKNOWN
    carril: str = ""
    aspecto: str = ""
    estado: str = ""
    confianza_extraccion: dict = field(default_factory=dict)

    def to_dict(self):
        return asdict(self)

    def fingerprint(self):
        """Huella semántica. UNKNOWN se traduce a cadena vacía a propósito:
        `semantic_fingerprint` ya trata la ausencia como 'sin evidencia' y la
        excluye del cálculo. Dejar el literal 'UNKNOWN' haría que dos piezas
        sin dato parecieran coincidir en ese eje."""
        def v(x):
            return "" if x == UNKNOWN else (x or "")
        return SemanticFingerprint(
            content_id=self.content_id, materia=v(self.materia),
            submateria=v(self.submateria), concepto_nucleo=v(self.concepto_nucleo),
            relacion="", familia_editorial=v(self.familia_editorial),
            necesidad=v(self.necesidad), pregunta_resuelta=v(self.pregunta_resuelta),
            angulo=v(self.angulo), contexto_funcional=v(self.contexto_funcional),
            rol_lector=v(self.rol_lector), consecuencia=v(self.consecuencia),
            hook=v(self.hook), formato=v(self.formato), emocion=v(self.emocion),
            metafora=v(self.metafora), escena=v(self.escena),
            composicion=v(self.composicion),
            objeto_protagonista=v(self.objeto_protagonista),
            material=v(self.material), camara=v(self.camara),
            iluminacion=v(self.iluminacion),
            direccion_artistica=v(self.direccion_artistica))


# El tema del banco es una carpeta editorial, no una materia jurídica, y el
# mapeo pierde información: las 4 piezas de sucesiones (testamento, herencia)
# están archivadas bajo FAMILIA, de modo que `sucesorio` parecería no haberse
# tocado nunca. Ese falso vacío es peor que no medir: mandaría al motor a
# "explorar" territorio ya explorado. Se refina por evidencia léxica del slug.
REFINAR_MATERIA = (
    (("herencia", "testamento", "legitima", "sucesion", "albacea", "heredero"),
     "sucesorio"),
    (("servidumbre", "arrendamiento", "condominio", "preventa", "inmueble"),
     "inmobiliario"),
)


def refinar_materia(guion, materia_base):
    """Ajusta la materia cuando el slug lo demuestra. Devuelve (materia, confianza)."""
    slug = (guion or "").lower()
    for claves, destino in REFINAR_MATERIA:
        if any(k in slug for k in claves) and materia_base != destino:
            return destino, MEDIA
    return materia_base, ALTA if materia_base != UNKNOWN else NINGUNA


def clasificar_familia_editorial(guion, titular=""):
    """Clasificación editorial retroactiva. Devuelve (familia, confianza).

    El corpus es anterior a la capa de diversidad editorial, así que no declara
    familia. Se infiere sólo con evidencia real y jamás se fuerza: UNKNOWN es
    preferible a una clasificación falsa.
    """
    slug = (guion or "").lower()
    partes = slug.split("-")

    # 1. Marcador explícito, en primera posición o tras "linkedin".
    for i, p in enumerate(partes[:3]):
        if p in PREFIJO_FAMILIA and (i == 0 or partes[0] == "linkedin"
                                     or p in ("mito", "concepto", "diferencia",
                                              "consejo", "tecnicismo", "listado",
                                              "consecuencia", "pregunta")):
            return PREFIJO_FAMILIA[p], ALTA

    # 2. Patrones léxicos fuertes.
    if "-vs-" in slug:
        return "diferencia", MEDIA
    if re.search(r"\bno-es\b", slug) or slug.startswith("no-es"):
        return "confusion_habitual", MEDIA
    if re.search(r"-no-es-(?:el|la|lo|un|una)?-?", slug):
        return "confusion_habitual", MEDIA
    if re.match(r"^(diez|veinte|seis|catorce)-", slug):
        return "checklist", MEDIA
    if re.match(r"^(que|quien|como|cuando)-", slug) or (titular or "").strip().endswith("?"):
        return "duda_frecuente", MEDIA
    if re.match(r"^antes-de-|^.*-antes-de-", slug):
        return "prevencion", MEDIA

    # 3. Forma narrativa: artículo + sustantivo + oración de relativo en pasado
    #    ("el-acto-que-nadie-notifico", "la-multa-que-nunca-se-cobro"). Es un
    #    relato de caso, pero sin marcador editorial: confianza BAJA.
    if re.match(r"^(el|la|los|las|un|una)-\w+.*-que-", slug):
        return "caso_cotidiano", BAJA

    # 4. Sin evidencia. No se inventa.
    return UNKNOWN, NINGUNA


def cargar_fuente(doc1=None, doc2=None):
    """Une los dos documentos por slug y valida cruzadamente."""
    d1 = json.loads(Path(doc1 or DOC1).read_text(encoding="utf-8"))
    por_guion = {r["guion"]: r for r in d1}

    filas, errores = [], []
    for linea in Path(doc2 or DOC2).read_text(encoding="utf-8").splitlines():
        if not linea.strip():
            continue
        campos = [c.strip() for c in linea.split("|")]
        if len(campos) != 10:
            errores.append(f"fila con {len(campos)} campos (se esperan 10): {linea[:60]}")
            continue
        filas.append(campos)

    registros = []
    for campos in filas:
        (lm_id, guion, carril, escuela, escenario, encuadre, paleta,
         mecanismo, marca, aspecto) = campos
        g = por_guion.get(guion)
        if g is None:
            errores.append(f"{lm_id}: el guion {guion!r} no existe en el documento 1.")
            continue
        registros.append((lm_id, guion, g, carril, escuela, escenario, encuadre,
                          paleta, mecanismo, marca, aspecto))

    huerfanos = sorted(set(por_guion) - {r[1] for r in registros})
    for h in huerfanos:
        errores.append(f"guion sin fila en el documento 2: {h!r}")
    return registros, errores


def construir_registros(doc1=None, doc2=None):
    crudos, errores = cargar_fuente(doc1, doc2)
    registros = []
    for (lm_id, guion, g, carril, escuela, escenario, encuadre,
         paleta, mecanismo, marca, aspecto) in crudos:
        tema = g.get("tema", "")
        familia, conf_fam = clasificar_familia_editorial(guion, g.get("titular", ""))
        materia, conf_materia = refinar_materia(
            guion, TEMA_A_MATERIA.get(tema, UNKNOWN))
        necesidad = NECESIDAD_POR_FAMILIA.get(familia, UNKNOWN)

        confianza = {
            "materia": conf_materia,
            "familia_editorial": conf_fam,
            # La necesidad se deriva de la familia: no puede ser más fiable que ella.
            "necesidad": conf_fam if necesidad != UNKNOWN else NINGUNA,
            "concepto_nucleo": MEDIA,   # del slug, que describe el asunto real
            "hook": ALTA,               # titular literal del documento
            "metafora": ALTA,           # texto literal del documento
            "direccion_artistica": ALTA, "escena": ALTA, "camara": ALTA,
            "composicion": ALTA, "material": ALTA, "objeto_protagonista": ALTA,
            # Nadie declaró estos ejes y no hay de dónde inferirlos.
            "angulo": NINGUNA, "contexto_funcional": NINGUNA,
            "rol_lector": NINGUNA, "consecuencia": NINGUNA,
            "pregunta_resuelta": NINGUNA, "emocion": NINGUNA,
            "submateria": NINGUNA, "iluminacion": NINGUNA, "formato": NINGUNA,
        }
        registros.append(RegistroHistorico(
            fuente="drive:banco-prompts-v3", content_id=lm_id, fecha="2026-09-08",
            guion=guion, tema_original=tema, titular=g.get("titular", ""),
            materia=materia, concepto_nucleo=guion.replace("-", " "),
            familia_editorial=familia, necesidad=necesidad,
            hook=g.get("titular", ""), metafora=g.get("metafora", ""),
            direccion_artistica=escuela, escena=escenario, camara=encuadre,
            composicion=mecanismo, objeto_protagonista=marca, material=paleta,
            carril=carril, aspecto=aspecto, estado="GENERADA",
            confianza_extraccion=confianza))
    return registros, errores


@dataclass
class ReporteImportacion:
    total_fuente: int = 0
    importados: int = 0
    ya_presentes: int = 0
    errores: list = field(default_factory=list)
    duplicados_exactos: list = field(default_factory=list)
    campos_faltantes: dict = field(default_factory=dict)
    confianza: dict = field(default_factory=dict)

    def to_dict(self):
        return asdict(self)


def importar(memoria, registros=None, estado=None, doc1=None, doc2=None):
    """Migración idempotente del corpus a la memoria semántica.

    Re-ejecutarla no duplica: los `content_id` ya presentes se cuentan como
    `ya_presentes` y no se vuelven a registrar.
    """
    from semantic_memory import HISTORICA
    # HISTORICA, no GENERADA: el corpus es registro acumulado, no un lote
    # recién producido, y su ventana de comparación debe cubrirlo entero.
    estado = estado or HISTORICA
    if registros is None:
        registros, errores = construir_registros(doc1, doc2)
    else:
        errores = []

    presentes = {e.fingerprint.get("content_id") for e in memoria.entries()}
    rep = ReporteImportacion(total_fuente=len(registros), errores=list(errores))

    # Duplicados exactos dentro de la propia fuente (mismo slug, mismo asunto).
    vistos = {}
    for r in registros:
        vistos.setdefault(r.guion, []).append(r.content_id)
    rep.duplicados_exactos = [(g, ids) for g, ids in sorted(vistos.items()) if len(ids) > 1]

    faltantes, conf_acum = {}, {}
    for r in registros:
        for campo, nivel in r.confianza_extraccion.items():
            conf_acum.setdefault(nivel, 0)
            conf_acum[nivel] += 1
            if nivel == NINGUNA:
                faltantes[campo] = faltantes.get(campo, 0) + 1
        if r.content_id in presentes:
            rep.ya_presentes += 1
            continue
        memoria.record(r.fingerprint(), estado, lote_id="corpus-historico")
        presentes.add(r.content_id)
        rep.importados += 1

    rep.campos_faltantes = dict(sorted(faltantes.items(), key=lambda kv: -kv[1]))
    rep.confianza = dict(sorted(conf_acum.items()))
    return rep
