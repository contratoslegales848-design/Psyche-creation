"""Tabla real CONCEPTO -> DIRECCIÓN ARTÍSTICA con evidencia empírica.

Autorización del Founder (18-sep-2026): construir la tabla que el Contrato
v4 §4 exige y que `docs/mandato-maestro-cierre-2026-09-17.md` (fila 1,
17-sep-2026) dejó documentada como gap real: "8/10 dimensiones de la
huella, incluida la biblioteca de 504 direcciones, siguen rotando por
anti-repetición pura -- filtrarlas exigiría la misma afinidad fabricada
que se evitó a propósito". Este módulo cierra esa parte del gap, pero
SOLO hasta donde la evidencia real alcanza -- nunca más.

FUENTE ÚNICA: `memoria_fuerte.py` (fuente #5 del Contrato v4). De sus 16
piezas reales (`PIEZAS_PUBLICADAS` + `PIEZAS_PRESELECCIONADAS`), sólo 4
traen `direccion_artistica` verbatim documentada junto con rendimiento
real verificado -- MF-10 (Carnelutti, likes/compartidos reales), MF-11
(Onassis, likes/compartidos reales), MF-12 (Calamandrei, likes/compartidos
reales), MF-13 (Surrealista estructurado, confirmación explícita del
Founder: "me gustaron"). Las otras 12 sólo documentan materia/concepto/
título, sin dirección artística asociada. Esa es TODA la evidencia real
que existe hoy sobre "qué dirección artística funcionó para qué concepto"
-- no se completa con nada inventado.

HONESTIDAD DECLARADA DESDE EL DISEÑO (no como hallazgo de cierre): el
mandato original describe una tabla CONCEPTO -> TENSIÓN -> METÁFORA ->
DIRECCIÓN ARTÍSTICA de 4 eslabones. La fuente real NO documenta `relacion`
(tensión) ni `metafora` para NINGUNA de las 16 piezas -- son campos que
`memoria_fuerte.py` nunca pobló porque la fuente original no los describe
así (verificado: `grep -n "relacion=\\|metafora=" memoria_fuerte.py` no
tiene resultados). La tabla que SÍ se puede construir con evidencia real
es de 2 eslabones -- CONCEPTO -> DIRECCIÓN ARTÍSTICA (+ composición/
material cuando la fuente los documenta) -- y así se declara, en vez de
fabricar tensión/metáfora para completar la forma que el mandato imaginó.

DOS PASOS, DOS TIPOS DE EVIDENCIA DISTINTOS -- no se mezclan:

  1. ¿El concepto del candidato se PARECE a un concepto ya documentado?
     Comparación de texto libre (mismo mecanismo de solapamiento de
     tokens que `semantic_fingerprint.py` ya usa para `concepto_nucleo`;
     se reutiliza `_similitud`/`_tokens`, no se reimplementa).
  2. Si hay concepto parecido: ¿su dirección artística histórica (texto
     libre, anterior al catálogo maestro estructurado de 504 direcciones)
     comparte VOCABULARIO REAL con alguna entrada real del catálogo?
     Coincidencia textual literal (mismo mecanismo que
     `direccion_causal._valores_permitidos_mecanismo`). Si no comparte
     ninguna palabra real, NO se inventa una traducción -- se deja
     constancia y no se restringe nada (ver `cobertura()` más abajo: 3 de
     las 4 evidencias reales pasan este segundo filtro; Onassis no
     comparte ninguna palabra real con el catálogo maestro).

NUNCA FUERZA: paso 1 sin coincidencia -> sin evidencia, catálogo abierto
igual que hoy. Paso 1 con coincidencia pero paso 2 sin vocabulario
compartido -> se informa (queda en la explicación), pero tampoco se
restringe nada -- inventar una traducción libre->catálogo sería
exactamente la afinidad fabricada que este repositorio evita en todos sus
demás módulos (`direccion_causal.py`, KEEP/ADAPT/REJECT de
`visual/README.md`).

NUNCA GANA a una regla ya vigente: esta tabla sólo puede AMPLIAR o
RESTRINGIR el conjunto de direcciones candidatas antes de la selección
por anti-repetición -- nunca toca `memoria_fuerte.verificar_rechazos_founder()`
ni `SemanticMemory.evaluar()`/`evaluar_visual_fuerte()`, que corren
DESPUÉS, sobre la huella ya elegida, en `art_direction.draft_visual_brief()`
sin ningún cambio. Si la dirección informada por esta tabla resulta ser
justo la que memoria fuerte ya bloquea (por repetir la puesta en escena de
la propia pieza fuente), el bloqueo gana -- ver
`test_concepto_direccion.py::TestAdversarial`.
"""

from dataclasses import dataclass, field

import memoria_fuerte as mf
from memory import normaliza
from semantic_fingerprint import _similitud, _tokens

# Conservador a propósito: con sólo 4 registros de evidencia real, un
# umbral bajo generaría falsos positivos (conceptos distintos que
# comparten un par de palabras comunes). No hay corpus de pares
# concepto-concepto etiquetados para calibrarlo empíricamente (a
# diferencia de `semantic_fingerprint.UMBRAL_EQUIVALENCIA`, calibrado
# contra 174 piezas reales) -- se declara como criterio editorial
# explícito, no como cifra calibrada.
UMBRAL_COINCIDENCIA_CONCEPTO = 0.34

# Palabras de 4+ letras para evitar coincidencias triviales de conectores
# ("de", "con", "una") al comparar la dirección artística histórica (texto
# libre) contra el vocabulario real del catálogo maestro.
LONGITUD_MINIMA_PALABRA_CLAVE = 4


@dataclass
class EvidenciaConceptoDireccion:
    """Una fila real de la tabla -- nunca sintética."""

    content_id: str
    concepto_nucleo: str
    materia: str
    direccion_artistica: str
    composicion: str = ""
    material: str = ""
    estado: str = ""            # PUBLICADA / PRESELECCIONADA (semantic_memory.py)
    rendimiento: dict = field(default_factory=dict)  # metricas verbatim de memoria_fuerte
    fuente: str = ""

    def to_dict(self):
        from dataclasses import asdict
        return asdict(self)


def _construir_tabla():
    filas = []
    for registros, estado in ((mf.PIEZAS_PUBLICADAS, "PUBLICADA"),
                              (mf.PIEZAS_PRESELECCIONADAS, "PRESELECCIONADA")):
        for r in registros:
            direccion = r.get("direccion_artistica")
            if not direccion:
                continue
            filas.append(EvidenciaConceptoDireccion(
                content_id=r["content_id"], concepto_nucleo=r["concepto_nucleo"],
                materia=r.get("materia", ""), direccion_artistica=direccion,
                composicion=r.get("composicion", ""), material=r.get("material", ""),
                estado=estado, rendimiento=dict(r.get("metricas", {})),
                fuente=mf.citar_fuente()))
    return tuple(filas)


# Construida una sola vez al importar -- fuente `memoria_fuerte.py` es
# estática en este repositorio (literales del documento del Founder, no
# una consulta en vivo).
TABLA_CONCEPTO_DIRECCION = _construir_tabla()


def buscar_evidencia_concepto(concepto_nucleo, tabla=None, umbral=UMBRAL_COINCIDENCIA_CONCEPTO):
    """(evidencia | None, similitud). `similitud` se devuelve SIEMPRE (aunque
    no alcance el umbral) para que quien llame pueda auditar por qué no
    hubo coincidencia, no sólo que no la hubo."""
    tabla = TABLA_CONCEPTO_DIRECCION if tabla is None else tabla
    if not concepto_nucleo or not tabla:
        return None, 0.0
    mejor, mejor_similitud = None, 0.0
    for evidencia in tabla:
        similitud = _similitud(concepto_nucleo, evidencia.concepto_nucleo, True) or 0.0
        if similitud > mejor_similitud:
            mejor, mejor_similitud = evidencia, similitud
    if mejor is not None and mejor_similitud >= umbral:
        return mejor, round(mejor_similitud, 4)
    return None, round(mejor_similitud, 4)


def _palabras_clave(evidencia):
    texto = " ".join(x for x in (evidencia.direccion_artistica, evidencia.composicion,
                                 evidencia.material) if x)
    return {t for t in _tokens(normaliza(texto)) if len(t) >= LONGITUD_MINIMA_PALABRA_CLAVE}


def direcciones_informadas_por_evidencia(catalogo, evidencia):
    """Entradas REALES del catálogo maestro cuyo texto comparte al menos una
    palabra clave real con la dirección artística histórica de `evidencia`.

    Coincidencia textual literal, mismo mecanismo que
    `direccion_causal._valores_permitidos_mecanismo` -- nunca una
    traducción inventada libre->catálogo. Puede devolver una lista vacía
    (ocurre de verdad para 1 de las 4 evidencias reales: Onassis no
    comparte ninguna palabra con el vocabulario del catálogo maestro) --
    eso es la respuesta honesta, no un error.

    LÍMITE HONESTO heredado del mismo mecanismo que ya existe en
    `direccion_causal.py`: una coincidencia de una sola palabra puede ser
    temáticamente débil (p. ej. "larga" en "cita larga legible" coincide
    con "fotografía de larga exposición" sin relación real de fondo). No
    se corrige con heurísticas nuevas no probadas -- es el mismo costo ya
    aceptado en `_valores_permitidos_mecanismo`, documentado ahí también.
    Por eso esta función INFORMA (amplía qué aparece en la explicación),
    nunca decide sola: la selección real sigue pasando por anti-repetición
    sobre el conjunto resultante, nunca por esta única palabra."""
    claves = _palabras_clave(evidencia)
    if not claves:
        return []
    todas = catalogo.todas_las_direcciones()
    return [(cat, e) for cat, e in todas if any(c in normaliza(e) for c in claves)]


def cobertura(catalogo=None):
    """Qué tan completa (o no) está esta tabla -- reportado con precisión,
    nunca como 'cobertura del catálogo': esta tabla no cubre el catálogo,
    cubre los conceptos de la fuente #5 que documentan dirección artística.
    """
    import visual_fingerprint as vf
    catalogo = catalogo or vf.MasterCatalog.load()
    total_piezas_fuente_5 = len(mf.PIEZAS_PUBLICADAS) + len(mf.PIEZAS_PRESELECCIONADAS)
    con_direccion = len(TABLA_CONCEPTO_DIRECCION)
    con_vocabulario_real = sum(
        1 for ev in TABLA_CONCEPTO_DIRECCION if direcciones_informadas_por_evidencia(catalogo, ev))
    total_direcciones_catalogo = sum(len(v) for v in catalogo.direcciones.values())
    return {
        "piezas_fuente_5": total_piezas_fuente_5,
        "piezas_con_direccion_artistica_documentada": con_direccion,
        "ratio_piezas_con_evidencia": round(con_direccion / total_piezas_fuente_5, 4)
                                      if total_piezas_fuente_5 else 0.0,
        "evidencias_con_vocabulario_real_en_catalogo": con_vocabulario_real,
        "ratio_evidencia_traducible_a_catalogo": round(con_vocabulario_real / con_direccion, 4)
                                                 if con_direccion else 0.0,
        "total_direcciones_catalogo_maestro": total_direcciones_catalogo,
        "nota": ("esta tabla NO cubre el catálogo maestro (504 direcciones): cubre los "
                "conceptos de memoria fuerte que documentan dirección artística real. "
                "Para cualquier concepto nuevo sin parecido real a esos 4, el catálogo "
                "sigue abierto y sin restringir, exactamente igual que antes de este módulo."),
    }
