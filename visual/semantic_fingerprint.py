"""Huella semántica de una pieza — P0 del Handoff Founder 2026-09-13 §4.

El problema medido: en lotes de 10, sólo 1–2 son aprovechables porque los
demás "se sienten repetidos". `memory.py` no podía detectarlo porque sólo
recuerda ejes VISUALES (escena, sujeto, cámara, metáfora, objeto) más el par
materia+concepto. Cambiar el estilo artístico bastaba para pasar su control.

Regla central del canon, y por tanto de este módulo:

    DOS CONTENIDOS SEMÁNTICAMENTE EQUIVALENTES NO SON NUEVOS PORQUE CAMBIE
    EL TÍTULO, EL HOOK O EL ESTILO.

De ahí la decisión de diseño más importante: `hook`, `formato` y `emocion` NO
participan en la distancia semántica. Están en la huella —se registran, se
rotan y se miden en el QA de lote— pero no pueden comprar novedad. La
distancia la domina el núcleo: concepto, familia editorial, necesidad y
pregunta resuelta.

Determinista y auditable, sin ML (misma disciplina que memory.py): cada
distancia se puede recalcular a mano y explicar en una frase.

Nada aquí es fuente jurídica. Mide PARECIDO EDITORIAL, jamás verdad.
"""

from dataclasses import dataclass, field, asdict

from memory import normaliza

FINGERPRINT_SCHEMA_VERSION = "1.0"

# --- los tres estratos de la huella ---------------------------------------
# NÚCLEO: de qué trata y qué función cumple. Domina la distancia semántica.
EJES_SEMANTICOS = {
    "materia": 0.09,
    "submateria": 0.06,
    "concepto_nucleo": 0.20,
    "relacion": 0.08,
    "familia_editorial": 0.17,
    "necesidad": 0.11,
    "pregunta_resuelta": 0.11,
    "angulo": 0.07,
    "contexto_funcional": 0.05,
    "rol_lector": 0.03,
    "consecuencia": 0.03,
}

# EXPRESIVOS: cómo se dice. Se registran y se rotan, pero NO compran novedad.
EJES_EXPRESIVOS = ("hook", "formato", "emocion")

# VISUALES: cómo se dibuja. Distancia propia, separada de la semántica.
EJES_VISUALES = {
    "metafora": 0.22,
    "escena": 0.16,
    "composicion": 0.13,
    "objeto_protagonista": 0.13,
    "direccion_artistica": 0.10,
    "material": 0.09,
    "camara": 0.09,
    "iluminacion": 0.08,
}

# Ejes de vocabulario ABIERTO: se comparan por solapamiento de tokens, porque
# "usucapión" y "usucapión y prescripción adquisitiva" son el mismo tema
# escrito distinto — exactamente el caso que el fundador reporta. El resto son
# vocabularios CERRADOS (materia, familia_editorial, rol_lector...), donde la
# igualdad estricta es la comparación correcta y auditable.
EJES_TEXTO_LIBRE = {
    "concepto_nucleo", "pregunta_resuelta", "consecuencia", "relacion",
    "metafora", "escena", "objeto_protagonista", "composicion", "hook",
}

# Por debajo de esta distancia semántica, dos piezas son el mismo contenido
# con otra ropa. Calibrado en test_semantic_fingerprint.py contra pares reales.
UMBRAL_EQUIVALENCIA = 0.30


def _similitud(a, b, texto_libre):
    """1.0 = idénticos, 0.0 = sin nada en común. Determinista."""
    na, nb = normaliza(a), normaliza(b)
    if not na and not nb:
        return None                      # sin dato: no prueba parecido NI diferencia
    if not na or not nb:
        return 0.0                       # uno declara y el otro no: son distintos
    if na == nb:
        return 1.0
    if not texto_libre:
        return 0.0                       # vocabulario cerrado: o es el mismo valor o no
    ta, tb = set(na.split()), set(nb.split())
    union = ta | tb
    return len(ta & tb) / len(union) if union else 0.0


@dataclass
class DistanceReport:
    """Distancia entre dos huellas, con el detalle que la justifica.

    `comparable` es la salvaguarda importante: si ningún eje tenía dato en
    ninguno de los dos lados, la distancia NO es 0.0 (que significaría
    'idénticos' y bloquearía contenido legítimo) ni 1.0 (que significaría
    'distintos' y dejaría pasar repetición). Es incomparable, y quien llama
    debe tratarlo como ausencia de evidencia.
    """

    valor: float = 0.0
    comparable: bool = False
    ejes_evaluados: int = 0
    ejes_sin_dato: list = field(default_factory=list)
    coincidencias: list = field(default_factory=list)

    def to_dict(self):
        return asdict(self)


def _distancia(a, b, pesos):
    total_peso, acumulado = 0.0, 0.0
    sin_dato, coincidencias = [], []
    for eje, peso in pesos.items():
        s = _similitud(getattr(a, eje, ""), getattr(b, eje, ""), eje in EJES_TEXTO_LIBRE)
        if s is None:
            sin_dato.append(eje)
            continue
        total_peso += peso
        acumulado += peso * s
        if s >= 0.5:
            coincidencias.append(f"{eje}: {round(s, 2)}")
    if total_peso == 0.0:
        return DistanceReport(0.0, False, 0, sorted(sin_dato), [])
    # Renormalizado sobre los ejes CON dato: un eje ausente no diluye la señal
    # de los presentes hacia un falso "muy distintos".
    return DistanceReport(round(1.0 - acumulado / total_peso, 4), True,
                          len(pesos) - len(sin_dato), sorted(sin_dato),
                          sorted(coincidencias))


@dataclass
class SemanticFingerprint:
    """Los 22 campos que exige el Handoff §4, en un solo objeto serializable."""

    content_id: str = ""
    # núcleo semántico
    materia: str = ""
    submateria: str = ""
    concepto_nucleo: str = ""
    relacion: str = ""
    familia_editorial: str = ""
    necesidad: str = ""
    pregunta_resuelta: str = ""
    angulo: str = ""
    contexto_funcional: str = ""
    rol_lector: str = ""
    consecuencia: str = ""
    # expresivos
    hook: str = ""
    formato: str = ""
    emocion: str = ""
    # visuales
    metafora: str = ""
    escena: str = ""
    composicion: str = ""
    objeto_protagonista: str = ""
    material: str = ""
    camara: str = ""
    iluminacion: str = ""
    direccion_artistica: str = ""
    schema_version: str = FINGERPRINT_SCHEMA_VERSION

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, d):
        campos = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in (d or {}).items() if k in campos})

    # --- distancias ---
    def distancia_semantica(self, otra):
        return _distancia(self, otra, EJES_SEMANTICOS)

    def distancia_visual(self, otra):
        return _distancia(self, otra, EJES_VISUALES)

    def equivalente_a(self, otra, umbral=UMBRAL_EQUIVALENCIA):
        """¿Es la misma pieza con otra ropa? Sin evidencia comparable, NO se
        afirma equivalencia: afirmarla bloquearía contenido legítimo."""
        d = self.distancia_semantica(otra)
        return bool(d.comparable and d.valor < umbral)

    # --- puente con la memoria visual ya existente ------------------------
    def visual_entry(self, generation_id="", visual_family="", **extra):
        """Devuelve la `VisualMemoryEntry` equivalente.

        Este puente es la razón de que esto NO sea un sistema paralelo: la
        huella semántica alimenta la memoria visual que ya existe, en vez de
        sustituirla. `memory.assess()` y `rotation.assess_batch_diversity()`
        siguen funcionando exactamente igual sobre los ejes visuales.
        """
        from memory import VisualMemoryEntry
        return VisualMemoryEntry(
            content_id=self.content_id,
            generation_id=generation_id,
            visual_family=visual_family or self.direccion_artistica,
            scene_type=self.escena,
            main_subject=self.objeto_protagonista,
            secondary_objects=[m for m in [self.material] if m],
            camera_angle=self.camara,
            lighting_type=self.iluminacion,
            metaphor=self.metafora,
            materia=self.materia,
            concepto=self.concepto_nucleo,
            **extra)


def mas_similar(candidata, poblacion):
    """(huella, DistanceReport) más cercana semánticamente, o (None, None).

    Sólo considera comparaciones con evidencia: una huella vacía no puede
    declararse "la más parecida" a nada.
    """
    mejor, mejor_d = None, None
    for otra in poblacion:
        d = candidata.distancia_semantica(otra)
        if not d.comparable:
            continue
        if mejor_d is None or d.valor < mejor_d.valor:
            mejor, mejor_d = otra, d
    return mejor, mejor_d
