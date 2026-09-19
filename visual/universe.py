"""Universo temático combinatorio y selección de lote — P0 del Handoff §3.

El defecto que corrige: "NO seleccionar directamente desde una lista pequeña".
El motor de rutas (`route_engine.py`) camina un grafo lineal por materia; los
bancos de Drive son listas finitas. Ninguno produce el espacio combinatorio
que el canon exige:

    CANDIDATO = MATERIA × SUBMATERIA × NECESIDAD × FAMILIA_EDITORIAL × PUERTA
              × CONCEPTO × RELACIÓN × ÁNGULO × CONTEXTO × ROL_LECTOR
              × PROFUNDIDAD × FORMATO × MEMORIA

Aquí se genera primero una RESERVA AMPLIA y sólo después se selecciona. La
aleatoriedad es CONTROLADA: `random.Random(seed)` — mismo seed, mismo lote, de
modo que un lote puede auditarse y reproducirse. Sin seed no habría forma de
demostrar nada en una prueba.

LÍMITE JURÍDICO, EXPLÍCITO: este módulo produce CANDIDATOS, nunca verdad.
Cada candidato nace con `estado_verificacion="NO_VERIFICADO"` y su
`proxima_accion` apunta a `legalmente-legal-verification`, igual que hace
route_engine.py. Combinar etiquetas de navegación no afirma nada sobre el
Derecho de ningún país (CLAUDE.md §4).
"""

import json
import random
from dataclasses import dataclass, field, asdict
from pathlib import Path

import emotion
import editorial
from memory import normaliza
from semantic_fingerprint import SemanticFingerprint, mas_similar, UMBRAL_EQUIVALENCIA

MATERIAS_PATH = Path(__file__).resolve().parent / "policy" / "materias-seed-v1.json"

NO_VERIFICADO = "NO_VERIFICADO"
ACCION_VERIFICACION = "legalmente-legal-verification"

# Un lote de 10 debe tocar 8–10 materias/familias distintas ("00 LEER PRIMERO"
# §3.A). Se expresa como proporción para que escale a lotes de otro tamaño.
MIN_MATERIAS_POR_10 = 8
MIN_FAMILIAS_POR_10 = 8
MAX_POR_EMOCION_POR_10 = 2
RESERVA_MINIMA_POR_PIEZA = 4      # canon: reserva mínima de 40 candidatos para 10


class UniverseError(ValueError):
    pass


def cargar_materias(path=None):
    p = Path(path) if path else MATERIAS_PATH
    if not p.is_file():
        raise UniverseError(f"semilla de materias no encontrada: {p}")
    data = json.loads(p.read_text(encoding="utf-8"))
    materias = data.get("materias") or {}
    if not materias:
        raise UniverseError("la semilla de materias está vacía.")
    return str(data.get("registry_version", "")), materias


@dataclass
class TopicCandidate:
    """Un candidato. NO es una pieza y NO es una afirmación jurídica."""

    candidate_id: str
    materia: str = ""
    submateria: str = ""
    familia_editorial: str = ""
    necesidad: str = ""
    rol_lector: str = ""
    angulo: str = ""
    contexto_funcional: str = ""
    profundidad: str = ""
    formato: str = ""
    concepto_nucleo: str = ""
    relacion: str = ""
    pregunta_resuelta: str = ""
    consecuencia: str = ""
    hook: str = ""
    perfil_emocional: dict = field(default_factory=dict)
    estado_verificacion: str = NO_VERIFICADO
    proxima_accion: str = ACCION_VERIFICACION

    def to_dict(self):
        return asdict(self)

    @property
    def emocion(self):
        return self.perfil_emocional.get("emocion", "")

    def fingerprint(self):
        """Huella semántica del candidato. Los ejes visuales quedan vacíos:
        todavía no hay plan visual, y fingir uno sería inventar datos."""
        return SemanticFingerprint(
            content_id=self.candidate_id, materia=self.materia,
            submateria=self.submateria, concepto_nucleo=self.concepto_nucleo,
            relacion=self.relacion, familia_editorial=self.familia_editorial,
            necesidad=self.necesidad, pregunta_resuelta=self.pregunta_resuelta,
            angulo=self.angulo, contexto_funcional=self.contexto_funcional,
            rol_lector=self.rol_lector, consecuencia=self.consecuencia,
            hook=self.hook, formato=self.formato, emocion=self.emocion)


def _elige(rng, secuencia, preferidas=()):
    """Elige respetando afinidad declarada cuando existe.

    La coherencia importa: 'checklist' sirve a 'prepararse', no a 'reflexionar'.
    Elegir uniformemente produciría combinaciones absurdas que el QA tendría
    que descartar después. Si no hay afinidad declarada, se usa todo el rango.
    """
    opciones = [x for x in preferidas if x in secuencia] or list(secuencia)
    return rng.choice(sorted(opciones))


def generar_candidato(rng, universo, materias, idx, materia=None, familia=None):
    """`familia` (hallazgo real, mandato "Revisa y mejora el generador de
    imágenes", 19-sep-2026): opcional, fuerza la familia editorial del
    candidato en vez de dejarla a `_elige` uniforme sobre las 65. Existe
    porque un banco maestro de producción continua necesita GARANTIZAR las
    puertas editoriales que el Founder nombró (mito, diferencia, concepto,
    pasos prácticos, errores frecuentes, derechos, obligaciones, casos), no
    sólo esperarlas por azar sobre un universo de 65 familias. `None`
    preserva el comportamiento exacto de antes (`build_reserve` no la usa)."""
    mat = materia or _elige(rng, sorted(materias))
    sub = rng.choice(sorted(materias[mat]["submaterias"]))
    fam_nombre = familia if familia else _elige(rng, universo.names())
    fam = universo.get(fam_nombre)

    nec = _elige(rng, sorted(universo.necesidades), fam.necesidades_afines)
    rol = _elige(rng, sorted(universo.roles_lector), fam.roles_lector_afines)
    ang = _elige(rng, sorted(universo.angulos))
    ctx = _elige(rng, sorted(universo.contextos_funcionales))
    prof = fam.profundidad_tipica if fam.profundidad_tipica in universo.profundidades \
        else _elige(rng, sorted(universo.profundidades))
    fmt = _elige(rng, sorted(universo.formatos_editoriales))

    concepto = f"{sub.replace('_', ' ')} — {fam.funcion_editorial}"
    relacion = fam.tension_tipica
    pregunta = (f"¿{universo.angulos.get(ang, ang)} en {sub.replace('_', ' ')} "
                f"cuando alguien necesita {nec}?")
    # La consecuencia sólo se declara si la familia editorial realmente la
    # implica. Inventarla para todas dispararía emociones de alta intensidad
    # sobre piezas que no las sostienen (ver emotion.py, regla fail-closed).
    consecuencia = fam.tension_tipica if fam.nombre in (
        "consecuencia", "responsabilidad", "incumplimiento", "riesgo",
        "plazo_prescripcion", "senal_de_alerta", "error_frecuente",
        "prohibicion", "reparacion", "carga_de_la_prueba", "derecho",
        "obligacion", "cumplimiento_compliance", "actualizacion_normativa",
        "excepcion", "clausula_bajo_lupa") else ""

    perfil = emotion.derivar(necesidad=nec, familia_editorial=fam_nombre,
                             consecuencia=consecuencia, rol_lector=rol)
    return TopicCandidate(
        candidate_id=f"CAND-{idx:04d}", materia=mat, submateria=sub,
        familia_editorial=fam_nombre, necesidad=nec, rol_lector=rol, angulo=ang,
        contexto_funcional=ctx, profundidad=prof, formato=fmt,
        concepto_nucleo=concepto, relacion=relacion, pregunta_resuelta=pregunta,
        consecuencia=consecuencia, perfil_emocional=perfil.to_dict())


def build_reserve(objetivo_lote=10, seed=None, universo=None, materias=None,
                  factor=RESERVA_MINIMA_POR_PIEZA):
    """Reserva amplia y heterogénea. Nunca se selecciona directamente de aquí.

    Recorre las materias en rotación (round-robin) antes de permitir
    repeticiones: si se dejara al azar puro, una reserva de 40 dejaría materias
    enteras sin representar y la selección no podría cubrir 8 distintas.
    """
    rng = random.Random(seed)
    universo = universo or editorial.EditorialUniverse.load()
    if materias is None:
        _, materias = cargar_materias()
    total = max(int(objetivo_lote) * int(factor), int(objetivo_lote))
    orden = sorted(materias)
    rng.shuffle(orden)
    return [generar_candidato(rng, universo, materias, i,
                              materia=orden[i % len(orden)])
            for i in range(total)]


@dataclass
class SelectionReport:
    seleccionados: list = field(default_factory=list)
    descartados: list = field(default_factory=list)   # (candidate_id, motivo)
    reserva_total: int = 0
    objetivo: int = 0
    completo: bool = False
    avisos: list = field(default_factory=list)

    def to_dict(self):
        return {"seleccionados": [c.candidate_id for c in self.seleccionados],
                "descartados": list(self.descartados),
                "reserva_total": self.reserva_total, "objetivo": self.objetivo,
                "completo": self.completo, "avisos": list(self.avisos)}


def select_batch(reserva, n=10, memoria=None, materias=None,
                 umbral_distancia=UMBRAL_EQUIVALENCIA):
    """Selección jerárquica con cuotas duras y máxima distancia semántica.

    Orden de filtrado:
      1. memoria (equivalencia semántica fuerte / cooldown corto),
      2. cuotas duras (materia, familia editorial, emoción),
      3. distancia mínima contra lo ya seleccionado en ESTE lote.

    Nunca rellena con candidatos débiles: si las cuotas impiden llegar a `n`,
    devuelve menos y lo declara. El canon es explícito — "nunca rellenar un
    lote con candidatos débiles sólo para llegar a diez".
    """
    if materias is None:
        _, materias = cargar_materias()
    escala = max(1, n) / 10.0
    max_emocion = max(1, round(MAX_POR_EMOCION_POR_10 * escala))

    seleccion, descartados, avisos = [], [], []
    usos_materia, usos_familia, usos_emocion = {}, {}, {}

    def cuota_materia(mat):
        base = materias.get(mat, {}).get("cuota_max_por_lote_10", 2)
        return max(1, round(base * escala))

    candidatos = list(reserva)
    if memoria is not None:
        vivos = []
        for c in candidatos:
            veredicto = memoria.evaluar(c.fingerprint())
            if veredicto.bloquea:
                descartados.append((c.candidate_id, veredicto.motivo))
            else:
                vivos.append(c)
        candidatos = vivos

    while len(seleccion) < n and candidatos:
        elegidos_fp = [c.fingerprint() for c in seleccion]
        mejor, mejor_score, mejor_motivos = None, None, {}
        for c in candidatos:
            mat, fam, emo = c.materia, c.familia_editorial, c.emocion
            if usos_materia.get(mat, 0) >= cuota_materia(mat):
                continue
            if usos_familia.get(fam, 0) >= 1:
                continue
            if emo and usos_emocion.get(emo, 0) >= max_emocion:
                continue
            fp = c.fingerprint()
            if elegidos_fp:
                _, d = mas_similar(fp, elegidos_fp)
                score = d.valor if d is not None else 1.0
            else:
                score = 1.0
            if score < umbral_distancia:
                continue                    # demasiado próximo a algo ya elegido
            if mejor_score is None or score > mejor_score:
                mejor, mejor_score = c, score
        if mejor is None:
            break
        seleccion.append(mejor)
        candidatos.remove(mejor)
        usos_materia[mejor.materia] = usos_materia.get(mejor.materia, 0) + 1
        usos_familia[mejor.familia_editorial] = usos_familia.get(mejor.familia_editorial, 0) + 1
        if mejor.emocion:
            usos_emocion[mejor.emocion] = usos_emocion.get(mejor.emocion, 0) + 1

    completo = len(seleccion) == n
    if not completo:
        avisos.append(
            f"sólo {len(seleccion)}/{n} candidatos superaron las cuotas y la distancia "
            f"mínima. NO se rellena con candidatos débiles: amplía la reserva "
            f"(actual: {len(reserva)}) o revisa la memoria.")
    if len(reserva) < n * RESERVA_MINIMA_POR_PIEZA:
        avisos.append(
            f"reserva de {len(reserva)} para un lote de {n}: por debajo del mínimo "
            f"canónico de {n * RESERVA_MINIMA_POR_PIEZA}.")
    return SelectionReport(seleccion, descartados, len(reserva), n, completo, avisos)
