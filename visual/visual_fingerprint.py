"""Motor de dirección artística — huella visual de 10 dimensiones.

Mandato "Súper Prompt" (Founder, 16-sep-2026), Fases 4-7: dejar de pensar
"elige un estilo" (8 familias, 4 colores obligatorios — ver
`docs/auditoria-monotonia-visual-2026-09-16.md`) y construir, para cada
pieza, una huella sobre el catálogo maestro real de 767 módulos
(`policy/catalogo-maestro-v1.md`, parseado por `catalog_parser.py`):

    visual_fingerprint = {
        primary_direction, secondary_direction?, medium, lighting, palette,
        composition, materiality, camera_optics, realism, visual_mechanism
    }

`medium` no se elige aparte: es la categoría del catálogo maestro (una de
las 10 de la sección 3) de la que sale `primary_direction` — así el
recuento de "familias/medios principales" del mandato (Fase 7) es
automático y nunca puede desalinearse del catálogo real.

SELECCIÓN (Fase 5): no es random puro. El filtro de compatibilidad
semántica declarado en el mandato NO se fabrica aquí como afinidad
inventada tema→categoría (este repositorio no tiene evidencia real de qué
categoría "conviene" a qué materia jurídica, y no se finge una que no
existe — mismo criterio fail-closed que `territory_explorer.coherencia()`
con familias sin afinidad declarada). Todas las categorías arrancan
elegibles por igual; lo que SÍ es real y verificable es la ANTI-REPETICIÓN:
la selección favorece valores poco usados recientemente y, si la huella
resultante coincide en demasiadas dimensiones con el historial, se muta
hasta cumplir la distancia mínima — exactamente como pide la Fase 5
("selección de huella distante") y la Fase 6 (memoria por similitud, no
por igualdad de nombre).
"""

import hashlib
import random
from dataclasses import dataclass, field, asdict
from pathlib import Path

import catalog_parser as cp
from memory import normaliza

CATALOGO_JSON_PATH = Path(__file__).resolve().parent / "policy" / "catalogo-maestro-v1.json"

DIMENSIONES_AUXILIARES = ("lighting", "composition", "camera_optics", "palette",
                          "materiality", "realism", "visual_mechanism")
# Las 10 dimensiones de la huella para comparación de distancia (Fase 6/7).
DIMENSIONES_HUELLA = ("primary_direction", "secondary_direction", "medium") + DIMENSIONES_AUXILIARES

MIN_DIMENSIONES_DIFERENTES_CONSECUTIVAS = 4   # Fase 7: "al menos 4 dimensiones" vs la pieza anterior
MIN_DIMENSIONES_DIFERENTES_HISTORIAL = 3      # Fase 5: "mutar al menos 3 dimensiones" si coincide demasiado
MAX_INTENTOS_MUTACION = 12


class CatalogNotLoadedError(ValueError):
    pass


class MasterCatalog:
    """Envoltura de solo lectura sobre el catálogo maestro derivado. Si el
    JSON derivado no existe, lo genera desde el .md (nunca inventa datos)."""

    def __init__(self, direcciones, auxiliares):
        self.direcciones = direcciones      # categoria -> [entradas]
        self.auxiliares = auxiliares        # dimension -> [entradas]

    @classmethod
    def load(cls, path=None):
        p = Path(path or CATALOGO_JSON_PATH)
        if not p.is_file():
            catalogo = cp.generar_json(path_json=p)
        else:
            import json
            data = json.loads(p.read_text(encoding="utf-8"))
            catalogo = cp.CatalogoParseado(
                direcciones=data["direcciones"], auxiliares=data["auxiliares"],
                total_direcciones=data["total_direcciones"],
                total_auxiliares=data["total_auxiliares"])
        if catalogo.total_direcciones < 100 or catalogo.total_auxiliares < 100:
            raise CatalogNotLoadedError(
                "el catálogo cargado es sospechosamente pequeño "
                f"({catalogo.total_direcciones} direcciones, "
                f"{catalogo.total_auxiliares} auxiliares) — no se usa como catálogo reducido "
                "por accidente. Regenerar con catalog_parser.generar_json().")
        return cls(catalogo.direcciones, catalogo.auxiliares)

    def categorias(self):
        return sorted(self.direcciones)

    def todas_las_direcciones(self):
        """[(categoria, entrada), ...] — plano, para muestreo uniforme real
        entre las 504 (una categoría con más entradas no domina la muestra
        solo por tener más filas escritas en el documento)."""
        return [(cat, e) for cat, entradas in self.direcciones.items() for e in entradas]

    def valores(self, dimension):
        return self.auxiliares[dimension]


@dataclass
class VisualFingerprint:
    content_id: str = ""
    primary_direction: str = ""
    secondary_direction: str = ""
    medium: str = ""
    lighting: str = ""
    composition: str = ""
    camera_optics: str = ""
    palette: str = ""
    materiality: str = ""
    realism: str = ""
    visual_mechanism: str = ""
    explanation: list = field(default_factory=list)

    def to_dict(self):
        return asdict(self)

    def valor(self, dimension):
        return getattr(self, dimension, "")


def distancia(a, b):
    """(dimensiones_distintas, dimensiones_conocidas) entre dos huellas.
    Compara por VALOR normalizado, no solo por nombre de campo — dos
    huellas con `secondary_direction` ambas vacías no cuentan esa
    dimensión como "coincidente": cuentan como sin evidencia, igual
    criterio fail-closed que `visual_distance.py`."""
    distintas = conocidas = 0
    for dim in DIMENSIONES_HUELLA:
        va, vb = normaliza(a.valor(dim)), normaliza(b.valor(dim))
        if va and vb:
            conocidas += 1
            if va != vb:
                distintas += 1
    return distintas, conocidas


@dataclass
class FingerprintMemoryEntry:
    content_id: str
    fingerprint: VisualFingerprint
    canal: str = ""


class FingerprintMemory:
    """Historial de huellas reales, en orden de generación. No persiste a
    disco por sí sola (igual que `memory.VisualMemory`) — quien orqueste el
    lote decide si la guarda; aquí solo vive la lógica de comparación."""

    def __init__(self, ventana=20):
        self.ventana = ventana
        self._entradas = []

    def record(self, content_id, fingerprint, canal=""):
        self._entradas.append(FingerprintMemoryEntry(content_id, fingerprint, canal))

    def recientes(self, canal=None, n=None):
        entradas = self._entradas if canal is None else [e for e in self._entradas if e.canal == canal]
        entradas = entradas[-self.ventana:]
        return entradas[-n:] if n else entradas

    def __len__(self):
        return len(self._entradas)


def _rng_para(content_id, sal=""):
    semilla = int(hashlib.sha256(f"{content_id}|{sal}".encode("utf-8")).hexdigest()[:12], 16)
    return random.Random(semilla)


def _frecuencia_reciente(memoria, dimension, canal=None):
    """Cuenta de uso reciente por valor normalizado — para desempatar hacia
    lo menos usado, no hacia lo random puro (Fase 5)."""
    conteo = {}
    for e in memoria.recientes(canal=canal):
        v = normaliza(e.fingerprint.valor(dimension))
        if v:
            conteo[v] = conteo.get(v, 0) + 1
    return conteo


def _elegir_menos_usado(rng, candidatos, conteo):
    """Entre los candidatos, prioriza los de menor frecuencia reciente;
    desempata con el rng determinista de la pieza (no random puro del
    proceso: reproducible por content_id)."""
    if not candidatos:
        return ""
    minimo = min(conteo.get(normaliza(c), 0) for c in candidatos)
    empatados = [c for c in candidatos if conteo.get(normaliza(c), 0) == minimo]
    return rng.choice(empatados)


def _construir_huella(content_id, catalogo, memoria, canal, rng, evitar_categoria_medium=None):
    direcciones = catalogo.todas_las_direcciones()
    conteo_dir = _frecuencia_reciente(memoria, "primary_direction", canal)
    if evitar_categoria_medium:
        candidatas = [d for d in direcciones if d[0] != evitar_categoria_medium] or direcciones
    else:
        candidatas = direcciones
    minimo = min(conteo_dir.get(normaliza(e), 0) for _, e in candidatas)
    empatadas = [d for d in candidatas if conteo_dir.get(normaliza(d[1]), 0) == minimo]
    medium, primary = rng.choice(empatadas)

    otras_categorias = [d for d in direcciones if d[0] != medium]
    secondary = ""
    if rng.random() < 0.5 and otras_categorias:
        conteo_sec = _frecuencia_reciente(memoria, "secondary_direction", canal)
        _, secondary = _elegir_par_menos_usado(rng, otras_categorias, conteo_sec)

    valores = {"primary_direction": primary, "secondary_direction": secondary, "medium": medium}
    for dim in DIMENSIONES_AUXILIARES:
        candidatos_dim = catalogo.valores(dim)
        conteo_dim = _frecuencia_reciente(memoria, dim, canal)
        valores[dim] = _elegir_menos_usado(rng, candidatos_dim, conteo_dim)

    return VisualFingerprint(content_id=content_id, **valores)


def _elegir_par_menos_usado(rng, pares, conteo):
    minimo = min(conteo.get(normaliza(v), 0) for _, v in pares)
    empatados = [p for p in pares if conteo.get(normaliza(p[1]), 0) == minimo]
    return rng.choice(empatados)


def seleccionar_huella(content_id, catalogo=None, memoria=None, canal="",
                       min_dimensiones_vs_ultima=MIN_DIMENSIONES_DIFERENTES_CONSECUTIVAS,
                       min_dimensiones_vs_historial=MIN_DIMENSIONES_DIFERENTES_HISTORIAL):
    """Pipeline de selección semántica (Fase 5). No recibe tema/tensión/
    metáfora como filtro de compatibilidad de catálogo (ver docstring del
    módulo: no se inventa esa afinidad) — sí las recibe y transporta
    `art_direction.py` para el resto del brief (asunto, metáfora, entorno),
    que no cambia por esta corrección."""
    catalogo = catalogo or MasterCatalog.load()
    memoria = memoria if memoria is not None else FingerprintMemory()
    rng = _rng_para(content_id, sal=str(len(memoria)))

    explicacion = []
    ultima = memoria.recientes(canal=canal, n=1)
    ultima = ultima[0].fingerprint if ultima else None

    intento = 0
    huella = _construir_huella(content_id, catalogo, memoria, canal, rng)
    while intento < MAX_INTENTOS_MUTACION:
        problemas = []
        if ultima is not None:
            distintas, conocidas = distancia(huella, ultima)
            if conocidas >= len(DIMENSIONES_HUELLA) and distintas < min_dimensiones_vs_ultima:
                problemas.append(
                    f"solo {distintas}/{conocidas} dimensiones distintas vs la pieza inmediatamente "
                    f"anterior (mínimo {min_dimensiones_vs_ultima}).")
        peor_vs_historial = 0
        for e in memoria.recientes(canal=canal):
            distintas, conocidas = distancia(huella, e.fingerprint)
            if conocidas >= len(DIMENSIONES_HUELLA):
                peor_vs_historial = max(peor_vs_historial, len(DIMENSIONES_HUELLA) - distintas)
        if peor_vs_historial > len(DIMENSIONES_HUELLA) - min_dimensiones_vs_historial:
            problemas.append(
                f"coincide demasiado con una pieza del historial reciente "
                f"({peor_vs_historial} dimensiones iguales).")

        if not problemas:
            if intento > 0:
                explicacion.append(f"reseleccionada tras {intento} mutación(es) por proximidad excesiva.")
            break
        explicacion.extend(problemas)
        intento += 1
        rng = _rng_para(content_id, sal=f"{len(memoria)}|{intento}")
        huella = _construir_huella(content_id, catalogo, memoria, canal, rng,
                                   evitar_categoria_medium=huella.medium)
    else:
        explicacion.append(
            f"no se alcanzó la distancia mínima tras {MAX_INTENTOS_MUTACION} intentos; "
            "se entrega la última huella probada — requiere revisión humana del lote.")

    huella.explanation = explicacion
    return huella
