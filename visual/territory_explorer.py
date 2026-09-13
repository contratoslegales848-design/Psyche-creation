"""Territory Explorer — Fase 3: dónde no hemos mirado todavía, y si vale la pena.

El mandato es explícito en dos direcciones a la vez:

    "NO debe limitarse a elegir aleatoriamente entre las 45 familias no
    utilizadas."
    "NOVEDAD SIN UTILIDAD NO ES CALIDAD."

Así que este módulo mide tres cosas DISTINTAS, nunca una sola puntuación
disfrazada de tres nombres:

    NOVELTY     — qué tan poco se ha tocado esta combinación materia×familia
                  frente a lo ya producido. Es una medida de VACÍO, no de
                  mérito: una combinación puede estar vacía porque nadie la
                  necesita, no sólo porque nadie la ha explorado.
    COVERAGE    — qué fracción del espacio materia×familia declarado
                  (`materias-seed-v1.json` × `editorial-universe-v1.json`) ya
                  se ha tocado con al menos una pieza. Es una propiedad del
                  MAPA completo, no de un candidato individual.
    OPPORTUNITY — NOVELTY ponderada por COHERENCIA declarada (¿la familia
                  editorial tiene afinidad real con esta necesidad o este rol
                  de lector, según `editorial.py`?). Un hueco vacío sin
                  ninguna afinidad declarada no es una oportunidad: es una
                  combinación que probablemente nadie necesita. Por eso
                  OPPORTUNITY nunca es sólo "1 − novelty invertida": la
                  coherencia actúa de multiplicador, nunca de bonus aditivo,
                  para que un hueco incoherente no pueda superar a uno
                  coherente sólo por estar más vacío.

ALCANCE DECLARADO, no escondido: el mapa combinatorio completo pedido por el
Founder tiene 8 ejes (MATERIA × SUBMATERIA × FAMILIA × NECESIDAD × PREGUNTA ×
ROL × CONTEXTO × PROFUNDIDAD). Con 174 piezas históricas y unos pocos cientos
de generaciones, trazar celda por celda un espacio de ese tamaño (decenas de
millones de combinaciones) no mediría nada real: casi toda celda estaría vacía
sólo por escasez de datos, no por vacío editorial genuino. Este módulo traza
la malla MATERIA × FAMILIA_EDITORIAL en detalle — es donde vive la evidencia
real (77 de 1.160 combinaciones producidas) — e informa la cobertura marginal
(1 eje a la vez) de NECESIDAD, ÁNGULO, ROL_LECTOR, CONTEXTO_FUNCIONAL y
PROFUNDIDAD como señal secundaria, sin fingir una malla de 8 dimensiones que
los datos no pueden sostener.
"""

from dataclasses import dataclass, field

from memory import normaliza

EJES_MARGINALES = ("necesidad", "angulo", "rol_lector", "contexto_funcional", "profundidad")

# Coherencia por defecto cuando la familia no declara afinidad para ningún eje
# (registro abierto: muchas familias del seed no declaran necesidades_afines).
# Ni penaliza ni premia: 0.7 es "razonablemente plausible, sin evidencia".
COHERENCIA_SIN_AFINIDAD_DECLARADA = 0.7
COHERENCIA_CON_AFINIDAD_QUE_ENCAJA = 1.0
COHERENCIA_CON_AFINIDAD_QUE_NO_ENCAJA = 0.4


class TerritoryError(ValueError):
    pass


@dataclass
class TerritoryMap:
    celdas: dict = field(default_factory=dict)          # (materia, familia) -> cuenta
    marginales: dict = field(default_factory=dict)        # eje -> {valor: cuenta}
    total_piezas: int = 0
    materias_universo: tuple = ()
    familias_universo: tuple = ()

    @property
    def celdas_tocadas(self):
        return len(self.celdas)

    @property
    def celdas_posibles(self):
        return len(self.materias_universo) * len(self.familias_universo)

    @property
    def coverage(self):
        """Fracción [0,1] del espacio materia×familia ya tocado por al menos
        una pieza. Es la respuesta cuantitativa a '¿qué parte del universo
        jurídico/editorial hemos cubierto?'."""
        posibles = self.celdas_posibles
        return round(self.celdas_tocadas / posibles, 4) if posibles else 0.0

    def to_dict(self):
        return {"celdas_tocadas": self.celdas_tocadas, "celdas_posibles": self.celdas_posibles,
                "coverage": self.coverage, "total_piezas": self.total_piezas,
                "marginales": {eje: dict(v) for eje, v in self.marginales.items()}}


def construir_mapa(fuentes, materias=None, universo=None):
    """`fuentes` es cualquier iterable de objetos con .materia y
    .familia_editorial (y opcionalmente los ejes marginales): sirve tanto
    para el corpus histórico (RegistroHistorico) como para memoria de
    producción reciente."""
    import editorial
    import universe as uni
    universo = universo or editorial.EditorialUniverse.load()
    if materias is None:
        _, materias = uni.cargar_materias()

    celdas, marginales, total = {}, {eje: {} for eje in EJES_MARGINALES}, 0
    for f in fuentes:
        mat = normaliza(getattr(f, "materia", "") or "")
        fam = normaliza(getattr(f, "familia_editorial", "") or "")
        if not mat or not fam or mat == "unknown" or fam == "unknown":
            continue
        total += 1
        celdas[(mat, fam)] = celdas.get((mat, fam), 0) + 1
        for eje in EJES_MARGINALES:
            v = normaliza(getattr(f, eje, "") or "")
            if v and v != "unknown":
                marginales[eje][v] = marginales[eje].get(v, 0) + 1

    return TerritoryMap(
        celdas=celdas, marginales=marginales, total_piezas=total,
        materias_universo=tuple(sorted(normaliza(m) for m in materias)),
        familias_universo=tuple(sorted(universo.names())))


@dataclass
class TerritoryScore:
    novelty: float = 0.0
    coverage: float = 0.0
    opportunity: float = 0.0
    ocurrencias_celda: int = 0
    coherencia: float = 0.0
    explicacion: list = field(default_factory=list)

    def to_dict(self):
        return {"novelty": self.novelty, "coverage": self.coverage,
                "opportunity": self.opportunity,
                "ocurrencias_celda": self.ocurrencias_celda,
                "coherencia": self.coherencia, "explicacion": list(self.explicacion)}


def coherencia(familia_nombre, necesidad, rol_lector, universo):
    """¿Esta necesidad/rol encajan con lo que la familia declara servir?
    Sin afinidad DECLARADA en absoluto, es neutral (ver constante del módulo):
    la mayoría de familias del seed no la declaran y eso no debe penalizarlas.
    """
    try:
        fam = universo.get(familia_nombre)
    except Exception:
        return COHERENCIA_SIN_AFINIDAD_DECLARADA, "familia no encontrada en el registro."

    if not necesidad and not rol_lector:
        # La celda se puntúa ANTES de elegir necesidad/rol (p. ej. en el
        # ranking de top_oportunidades, que recorre materia×familia sola).
        # Sin ellos no hay fit que evaluar todavía: penalizar aquí castigaría
        # a toda familia con afinidades declaradas por un dato que aún no
        # existe, justo lo contrario de lo que la coherencia debe medir.
        return COHERENCIA_SIN_AFINIDAD_DECLARADA, (
            "necesidad/rol aún no especificados: coherencia neutral, pendiente de elección.")

    afines_nec = fam.necesidades_afines
    afines_rol = fam.roles_lector_afines
    if not afines_nec and not afines_rol:
        return COHERENCIA_SIN_AFINIDAD_DECLARADA, (
            f"{familia_nombre!r} no declara afinidades: coherencia neutral.")

    encaja_nec = not afines_nec or normaliza(necesidad) in {normaliza(a) for a in afines_nec}
    encaja_rol = not afines_rol or normaliza(rol_lector) in {normaliza(a) for a in afines_rol}
    if encaja_nec and encaja_rol:
        return COHERENCIA_CON_AFINIDAD_QUE_ENCAJA, (
            f"necesidad y rol encajan con las afinidades declaradas de {familia_nombre!r}.")
    return COHERENCIA_CON_AFINIDAD_QUE_NO_ENCAJA, (
        f"{familia_nombre!r} declara afinidades y esta combinación no encaja con ellas.")


def score_candidate(candidato, mapa, universo=None):
    """NOVELTY, COVERAGE (del mapa completo) y OPPORTUNITY de un candidato
    concreto (materia, familia_editorial, necesidad, rol_lector)."""
    import editorial
    universo = universo or editorial.EditorialUniverse.load()

    mat = normaliza(getattr(candidato, "materia", "") or "")
    fam = normaliza(getattr(candidato, "familia_editorial", "") or "")
    if not mat or not fam:
        return TerritoryScore(explicacion=["materia o familia editorial ausentes: "
                                           "no se puede puntuar territorio."])

    n_celda = mapa.celdas.get((mat, fam), 0)
    max_celda = max(mapa.celdas.values(), default=1)
    novelty = round(1.0 - (n_celda / max_celda if max_celda else 0.0), 4)

    valor_coherencia, razon_coherencia = coherencia(
        getattr(candidato, "familia_editorial", ""), getattr(candidato, "necesidad", ""),
        getattr(candidato, "rol_lector", ""), universo)

    opportunity = round(novelty * valor_coherencia, 4)

    explicacion = []
    if n_celda == 0:
        explicacion.append(f"{mat} × {fam}: combinación nunca producida.")
    else:
        explicacion.append(f"{mat} × {fam}: producida {n_celda} veces "
                           f"(la celda más frecuente tiene {max_celda}).")
    explicacion.append(razon_coherencia)

    return TerritoryScore(novelty=novelty, coverage=mapa.coverage, opportunity=opportunity,
                          ocurrencias_celda=n_celda, coherencia=valor_coherencia,
                          explicacion=explicacion)


def top_oportunidades(mapa, universo=None, materias=None, n=20):
    """Ranking de celdas materia×familia por OPPORTUNITY — para informar,
    nunca para forzar una cuota. Incluye tanto celdas nunca tocadas como
    celdas poco tocadas frente a las más frecuentes; no restringe a materias
    ya abiertas, porque parte del territorio sin explorar son materias
    enteras (Fase D del informe anterior: 6 materias sin una sola pieza)."""
    import editorial
    import universe as uni
    universo = universo or editorial.EditorialUniverse.load()
    if materias is None:
        _, materias = uni.cargar_materias()

    class _Cand:
        def __init__(self, materia, familia):
            self.materia, self.familia_editorial = materia, familia
            self.necesidad, self.rol_lector = "", ""

    filas = []
    for mat in sorted(normaliza(m) for m in materias):
        for fam in universo.names():
            c = _Cand(mat, fam)
            score = score_candidate(c, mapa, universo)
            filas.append((score.opportunity, mat, fam, score.ocurrencias_celda))
    filas.sort(key=lambda t: (-t[0], t[1], t[2]))
    return filas[:n]
