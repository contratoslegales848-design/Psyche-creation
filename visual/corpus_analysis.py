"""Análisis del corpus histórico — ¿qué ha contado LegalMente y qué no?

Dos preguntas distintas, ambas necesarias:

  REPETICIÓN  — qué ejes se han agotado y dónde el catálogo se repite a sí
                mismo aunque cada pieza tenga título propio.
  VACÍO       — qué zonas del Derecho y qué puertas editoriales no se han
                abierto nunca. Es la pregunta más valiosa: el objetivo final no
                es evitar repetición, es descubrir territorio.

Los clusters usan enlace simple sobre la distancia semántica ya definida en
`semantic_fingerprint`. Sin ML y sin dependencias: el resultado se puede
recalcular a mano y explicar. Determinista.

No verifica Derecho. Cuenta producción pasada.
"""

from dataclasses import dataclass, field

from memory import normaliza
from semantic_fingerprint import UMBRAL_EQUIVALENCIA

UNKNOWN = "UNKNOWN"


def _frec(registros, attr):
    out = {}
    for r in registros:
        v = getattr(r, attr, "") or ""
        if v and v != UNKNOWN:
            out[v] = out.get(v, 0) + 1
    return dict(sorted(out.items(), key=lambda kv: (-kv[1], kv[0])))


def _frec_pares(registros, a, b):
    out = {}
    for r in registros:
        va, vb = getattr(r, a, ""), getattr(r, b, "")
        if va and vb and va != UNKNOWN and vb != UNKNOWN:
            k = f"{va} + {vb}"
            out[k] = out.get(k, 0) + 1
    return dict(sorted(out.items(), key=lambda kv: (-kv[1], kv[0])))


def perfil_de_repeticion(registros):
    """Frecuencias reales por eje. Los UNKNOWN se excluyen del recuento y se
    informan aparte: contarlos como una categoría más fingiría que 29 piezas
    comparten una familia editorial llamada 'UNKNOWN'."""
    ejes = ("materia", "tema_original", "familia_editorial", "necesidad",
            "concepto_nucleo", "metafora", "direccion_artistica", "escena",
            "composicion", "camara", "material", "objeto_protagonista",
            "carril", "aspecto", "emocion")
    perfil = {eje: _frec(registros, eje) for eje in ejes}
    perfil["materia+familia_editorial"] = _frec_pares(
        registros, "materia", "familia_editorial")
    perfil["_sin_dato"] = {
        eje: sum(1 for r in registros
                 if not getattr(r, eje, "") or getattr(r, eje, "") == UNKNOWN)
        for eje in ejes}
    return perfil


@dataclass
class Cluster:
    miembros: list = field(default_factory=list)   # (content_id, guion)
    distancia_media: float = 0.0
    materia: str = ""

    @property
    def tamano(self):
        return len(self.miembros)


def clusters_semanticos(registros, umbral=UMBRAL_EQUIVALENCIA, minimo=2):
    """Agrupa por enlace simple: dos piezas caen en el mismo cluster si su
    distancia semántica es menor que `umbral`.

    Un cluster de 10 significa diez piezas con título propio que resuelven
    prácticamente la misma pregunta jurídica. Es exactamente lo que el fundador
    percibe como "se sienten repetidos".
    """
    fps = [(r, r.fingerprint()) for r in registros]
    n = len(fps)
    padre = list(range(n))

    def raiz(i):
        while padre[i] != i:
            padre[i] = padre[padre[i]]
            i = padre[i]
        return i

    pares = []
    for i in range(n):
        for j in range(i + 1, n):
            d = fps[i][1].distancia_semantica(fps[j][1])
            if d.comparable and d.valor < umbral:
                pares.append((d.valor, i, j))
                ri, rj = raiz(i), raiz(j)
                if ri != rj:
                    padre[ri] = rj

    grupos = {}
    for i in range(n):
        grupos.setdefault(raiz(i), []).append(i)

    salida = []
    for miembros in grupos.values():
        if len(miembros) < minimo:
            continue
        internos = [p[0] for p in pares
                    if p[1] in miembros and p[2] in miembros]
        materias = {fps[i][0].materia for i in miembros}
        salida.append(Cluster(
            miembros=[(fps[i][0].content_id, fps[i][0].guion) for i in sorted(miembros)],
            distancia_media=round(sum(internos) / len(internos), 4) if internos else 0.0,
            materia=", ".join(sorted(materias))))
    return sorted(salida, key=lambda c: -c.tamano)


def zonas_sin_explorar(registros, universo=None, materias=None):
    """Lo que NUNCA se ha tocado. La pregunta que abre territorio.

    Compara el corpus contra el universo declarado (materias seed y familias
    editoriales) y devuelve lo ausente. No es una recomendación de publicar:
    es un mapa de dónde todavía no se ha mirado.
    """
    import editorial
    import universe as uni
    universo = universo or editorial.EditorialUniverse.load()
    if materias is None:
        _, materias = uni.cargar_materias()

    usadas_mat = {normaliza(r.materia) for r in registros
                  if r.materia and r.materia != UNKNOWN}
    usadas_fam = {normaliza(r.familia_editorial) for r in registros
                  if r.familia_editorial and r.familia_editorial != UNKNOWN}

    materias_sin_tocar = sorted(m for m in materias if normaliza(m) not in usadas_mat)
    familias_sin_tocar = sorted(f for f in universo.names() if normaliza(f) not in usadas_fam)

    # Materias del corpus que el seed no contempla: el corpus enseña al seed.
    del_corpus = {r.materia for r in registros if r.materia and r.materia != UNKNOWN}
    fuera_del_seed = sorted(m for m in del_corpus if m not in materias)

    # Combinaciones materia × familia nunca producidas, limitadas a lo que ya
    # se ha tocado en ambos ejes (no se proponen materias que nadie ha abierto).
    combos = {f"{r.materia} + {r.familia_editorial}" for r in registros
              if r.materia != UNKNOWN and r.familia_editorial != UNKNOWN}
    huecos = []
    for m in sorted(usadas_mat):
        for f in sorted(universo.names()):
            if f"{m} + {f}" not in {normaliza(c.split(' + ')[0]) + " + " + c.split(' + ')[1]
                                    for c in combos}:
                huecos.append(f"{m} + {f}")

    return {
        "materias_del_seed_sin_una_sola_pieza": materias_sin_tocar,
        "familias_editoriales_nunca_usadas": familias_sin_tocar,
        "materias_del_corpus_fuera_del_seed": fuera_del_seed,
        "combinaciones_materia_familia_producidas": len(combos),
        "combinaciones_posibles_sobre_materias_ya_abiertas": len(usadas_mat) * len(universo),
        "muestra_de_huecos": huecos[:25],
    }
