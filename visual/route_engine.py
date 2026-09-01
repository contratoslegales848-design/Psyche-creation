"""Motor de Rutas LegalMente.

Convierte la logica de vinculacion conceptual (materia -> causa ->
consecuencia -> prueba -> procedimiento -> reparacion -> prevencion...) en un
motor ejecutable con memoria: cada entrada abre una ruta, cada paso se
registra en una matriz persistente en JSON, y cada pieza producida es un
BORRADOR sin verificar -- el motor nunca aprueba contenido juridico por si
mismo (CLAUDE.md S4: ninguna IA es fuente juridica; toda afirmacion pasa por
verificacion ANTES de generar arte).

El grafo de categorias (CAUSA, CONSECUENCIA, PRUEBA...) es estructura de
analisis juridico generica -- no una afirmacion sobre un pais concreto -- por
lo que no requiere verificacion legal para existir como grafo de navegacion.
Las piezas que este motor produce (hook/copy/prompt) SI la requieren antes de
cualquier generacion visual real: cada una nace con
estado_verificacion="NO_VERIFICADO" y su proxima_accion apunta a
`legalmente-legal-verification`, nunca a produccion directa.

Regla central: toda entrada genera una ruta; toda ruta genera piezas; toda
pieza registra sus nodos usados y abre la siguiente conexion.
"""

import hashlib
import json
from dataclasses import dataclass, field, asdict
from pathlib import Path

ROUTE_SCHEMA_VERSION = "1.0"

# --- el grafo canonico de categorias de nodo -------------------------------
# Aristas dirigidas: que categoria puede seguir naturalmente a otra.
CAT_MATERIA = "MATERIA"
CAT_CAUSA = "CAUSA"
CAT_BIEN_JURIDICO = "BIEN_JURIDICO"
CAT_CONSECUENCIA = "CONSECUENCIA"
CAT_RESPONSABILIDAD = "RESPONSABILIDAD"
CAT_PRUEBA = "PRUEBA"
CAT_PROCEDIMIENTO = "PROCEDIMIENTO"
CAT_DEFENSA = "DEFENSA"
CAT_REPARACION = "REPARACION"
CAT_PREVENCION = "PREVENCION"

GRAFO_CATEGORIAS = {
    CAT_MATERIA: [CAT_CAUSA],
    CAT_CAUSA: [CAT_BIEN_JURIDICO, CAT_CONSECUENCIA],
    CAT_BIEN_JURIDICO: [CAT_CONSECUENCIA],
    CAT_CONSECUENCIA: [CAT_RESPONSABILIDAD],
    CAT_RESPONSABILIDAD: [CAT_PRUEBA, CAT_DEFENSA],
    CAT_PRUEBA: [CAT_PROCEDIMIENTO],
    CAT_DEFENSA: [CAT_PROCEDIMIENTO],
    CAT_PROCEDIMIENTO: [CAT_REPARACION],
    CAT_REPARACION: [CAT_PREVENCION],
    CAT_PREVENCION: [],  # hoja: el motor nunca reabre CAUSA en automatico (evita ciclo infinito)
}

# Vocabulario por materia: etiqueta de NAVEGACION por defecto de cada
# categoria (nombres de las etapas del analisis), no una afirmacion juridica
# verificable -- por eso no pasa por verificacion legal. Materias sin
# entrada usan el nombre generico de la categoria.
VOCABULARIO_POR_MATERIA = {
    "penal": {
        CAT_CAUSA: "Delito",
        CAT_BIEN_JURIDICO: "Bien jurídico protegido",
        CAT_CONSECUENCIA: "Daño",
        CAT_RESPONSABILIDAD: "Responsabilidad civil",
        CAT_PRUEBA: "Prueba",
        CAT_PROCEDIMIENTO: "Proceso",
        CAT_DEFENSA: "Defensa",
        CAT_REPARACION: "Reparación",
        CAT_PREVENCION: "Prevención",
    },
    "civil": {
        CAT_CAUSA: "Incumplimiento",
        CAT_BIEN_JURIDICO: "Interés protegido",
        CAT_CONSECUENCIA: "Daño",
        CAT_RESPONSABILIDAD: "Responsabilidad civil",
        CAT_PRUEBA: "Prueba",
        CAT_PROCEDIMIENTO: "Proceso",
        CAT_DEFENSA: "Defensa",
        CAT_REPARACION: "Reparación / indemnización",
        CAT_PREVENCION: "Prevención contractual",
    },
    "laboral": {
        CAT_CAUSA: "Incumplimiento laboral",
        CAT_BIEN_JURIDICO: "Derecho laboral protegido",
        CAT_CONSECUENCIA: "Perjuicio",
        CAT_RESPONSABILIDAD: "Responsabilidad patronal",
        CAT_PRUEBA: "Prueba",
        CAT_PROCEDIMIENTO: "Proceso laboral",
        CAT_DEFENSA: "Defensa",
        CAT_REPARACION: "Reparación / indemnización",
        CAT_PREVENCION: "Prevención laboral",
    },
}


def _normaliza_materia(materia):
    return (materia or "").strip().lower()


def _etiqueta_por_defecto(materia, categoria):
    if categoria == CAT_MATERIA:
        return (materia or "").strip() or "Materia sin especificar"
    tabla = VOCABULARIO_POR_MATERIA.get(_normaliza_materia(materia), {})
    return tabla.get(categoria, categoria.replace("_", " ").title())


def _ruta_id(entrada, materia):
    base = f"{_normaliza_materia(materia)}::{(entrada or '').strip().lower()}"
    return "RUTA-" + hashlib.sha256(base.encode("utf-8")).hexdigest()[:12]


@dataclass
class PiezaEjecutivaBorrador:
    """Stub de contenido -- SIEMPRE sin verificar. Nunca se produce arte ni
    se publica a partir de esto sin pasar antes por
    legalmente-legal-verification (CLAUDE.md S4)."""

    hook: str
    copy_borrador: str
    texto_imagen: str
    nota_jurisdiccional: str
    prompt_borrador: str
    estado_verificacion: str = "NO_VERIFICADO"

    def to_dict(self):
        return asdict(self)


def _producir_pieza_borrador(materia, categoria_actual, etiqueta_actual, etiqueta_anterior):
    if etiqueta_anterior:
        hook = f"¿Qué ocurre cuando {etiqueta_anterior.lower()} conecta con {etiqueta_actual.lower()} en materia {materia}?"
    else:
        hook = f"¿Qué es {etiqueta_actual.lower()} en materia {materia}?"
    return PiezaEjecutivaBorrador(
        hook=hook,
        copy_borrador=(
            f"[BORRADOR NO VERIFICADO] Desarrollar {etiqueta_actual} dentro de {materia}"
            + (f", partiendo de {etiqueta_anterior}" if etiqueta_anterior else "")
            + ". Requiere verificación jurídica (legalmente-legal-verification) antes de "
            "convertirse en copy real."
        ),
        texto_imagen=f"{etiqueta_actual.upper()} — {materia}",
        nota_jurisdiccional=(
            "Panhispánico / comparado (Capa A/B por defecto) — clasificar Capa C explícita "
            "si el contenido final se vuelve país-específico. Ver CLAUDE.md §4."
        ),
        prompt_borrador=(
            f"[PENDIENTE legalmente-visual-system] Prompt visual para '{etiqueta_actual}' "
            f"({materia}) según política visual vigente y motor de rotación de estilos."
        ),
    )


@dataclass
class RouteMatrixRow:
    """Una fila real de la matriz de rutas. Los campos siguen el orden
    pedido: ID de ruta | nodo actual | nodo anterior | siguiente vínculo |
    materia | formato | estado | fuente | jurisdicción | pieza producida |
    próxima acción."""

    ruta_id: str
    nodo_actual: str                          # categoria, p.ej. "CAUSA"
    nodo_actual_label: str                    # etiqueta legible, p.ej. "Delito"
    nodo_anterior: str = ""
    nodo_anterior_label: str = ""
    siguiente_vinculo: list = field(default_factory=list)   # categorias candidatas no explotadas
    materia: str = ""
    formato: str = "NO_ASIGNADO"
    estado: str = "PENDIENTE"                 # PENDIENTE | PRODUCIDO | RUTA_COMPLETA
    fuente: str = "NO_VERIFICADO"
    jurisdiccion: str = "PANHISPANICO_COMPARADO"
    pieza_producida: dict = None
    proxima_accion: str = "ABRIR_VINCULO"     # ABRIR_VINCULO | VERIFY_SOURCES | RUTA_COMPLETA

    def to_dict(self):
        return asdict(self)


class RouteEngine:
    """Motor de rutas con memoria persistente en JSON.

    Cada ruta es una secuencia de RouteMatrixRow. El motor nunca repite una
    arista (categoria_origen -> categoria_destino) ya usada DENTRO de la
    misma ruta -- por eso rastrea aristas_usadas por ruta_id ("evitar
    desperdicio": no volver a proponer una conexion ya explotada).
    """

    def __init__(self, filas=(), aristas_usadas=None):
        self._filas = list(filas)
        self._aristas_usadas = {k: set(v) for k, v in (aristas_usadas or {}).items()}

    def __len__(self):
        return len(self._filas)

    # --- persistencia -------------------------------------------------
    def save(self, path):
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps({
            "schema_version": ROUTE_SCHEMA_VERSION,
            "filas": [f.to_dict() for f in self._filas],
            "aristas_usadas": {
                rid: sorted(list(pares)) for rid, pares in self._aristas_usadas.items()
            },
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return p

    @classmethod
    def load(cls, path):
        p = Path(path)
        if not p.is_file():
            return cls()
        data = json.loads(p.read_text(encoding="utf-8"))
        if data.get("schema_version") != ROUTE_SCHEMA_VERSION:
            # Version desconocida: se ignora en vez de malinterpretarla (fail-closed).
            return cls()
        filas = [RouteMatrixRow(**f) for f in data.get("filas", [])]
        aristas = {
            rid: {tuple(par) for par in pares}
            for rid, pares in data.get("aristas_usadas", {}).items()
        }
        return cls(filas, aristas)

    # --- lectura --------------------------------------------------------
    def filas_de(self, ruta_id):
        return [f for f in self._filas if f.ruta_id == ruta_id]

    def ultima_fila(self, ruta_id):
        filas = self.filas_de(ruta_id)
        return filas[-1] if filas else None

    def nodos_visitados(self, ruta_id):
        return [f.nodo_actual for f in self.filas_de(ruta_id)]

    def valida_continuidad(self, ruta_id):
        """Verifica que la ruta no repite nodos y que cada fila enlaza
        correctamente con la anterior. Devuelve (ok: bool, problemas: list)."""
        filas = self.filas_de(ruta_id)
        problemas = []
        vistos = set()
        for i, f in enumerate(filas):
            if f.nodo_actual in vistos:
                problemas.append(f"nodo {f.nodo_actual!r} repetido en la fila {i}.")
            vistos.add(f.nodo_actual)
            if i > 0 and f.nodo_anterior != filas[i - 1].nodo_actual:
                problemas.append(
                    f"fila {i}: nodo_anterior={f.nodo_anterior!r} no coincide con el "
                    f"nodo_actual de la fila previa ({filas[i - 1].nodo_actual!r})."
                )
        return (not problemas, problemas)

    # --- las 5 funciones pedidas ----------------------------------------
    def leer_entrada(self, entrada, materia):
        """1. Recibe un tema/documento/pregunta y abre una ruta (o continua
        la existente si la misma entrada+materia ya tiene una)."""
        if not entrada or not entrada.strip():
            raise ValueError("entrada vacia: el motor no puede abrir una ruta sin tema.")
        ruta_id = _ruta_id(entrada, materia)
        if self.filas_de(ruta_id):
            return ruta_id  # misma entrada+materia: se continua, no se duplica
        etiqueta = _etiqueta_por_defecto(materia, CAT_MATERIA)
        siguiente = list(GRAFO_CATEGORIAS[CAT_MATERIA])
        fila = RouteMatrixRow(
            ruta_id=ruta_id,
            nodo_actual=CAT_MATERIA,
            nodo_actual_label=etiqueta,
            siguiente_vinculo=siguiente,
            materia=materia,
            proxima_accion="ABRIR_VINCULO" if siguiente else "RUTA_COMPLETA",
        )
        self._filas.append(fila)
        self._aristas_usadas.setdefault(ruta_id, set())
        return ruta_id

    def _conexiones_no_explotadas(self, ruta_id, categoria_origen):
        """3. Evitar desperdicio: solo ofrece aristas (origen, destino) que
        esta ruta todavia no uso."""
        usadas = self._aristas_usadas.get(ruta_id, set())
        return [
            destino for destino in GRAFO_CATEGORIAS.get(categoria_origen, [])
            if (categoria_origen, destino) not in usadas
        ]

    def crear_vinculo(self, ruta_id, categoria_elegida=None):
        """2. Detecta/elige el siguiente vinculo (causa, consecuencia,
        prueba...) a partir del nodo actual, sin repetir aristas ya usadas
        en esta ruta. None si el nodo actual ya agoto sus conexiones."""
        actual = self.ultima_fila(ruta_id)
        if actual is None:
            raise ValueError(f"ruta {ruta_id!r} no existe: llama a leer_entrada primero.")
        candidatas = self._conexiones_no_explotadas(ruta_id, actual.nodo_actual)
        if not candidatas:
            return None
        if categoria_elegida is not None:
            if categoria_elegida not in candidatas:
                raise ValueError(
                    f"{categoria_elegida!r} no es una conexion valida y no explotada desde "
                    f"{actual.nodo_actual!r}; opciones: {candidatas}"
                )
            return categoria_elegida
        return candidatas[0]

    def producir_pieza(self, ruta_id, categoria_elegida=None, formato="NO_ASIGNADO"):
        """4. Convierte el vinculo elegido en una fila nueva con una pieza
        ejecutiva BORRADOR. 5. Registra continuidad (nodo actual/anterior,
        siguiente pendiente) para que la proxima llamada continue sin
        perder informacion. Si la ruta ya esta agotada desde el nodo
        actual, marca esa fila como RUTA_COMPLETA y no crea una fila nueva."""
        actual = self.ultima_fila(ruta_id)
        if actual is None:
            raise ValueError(f"ruta {ruta_id!r} no existe: llama a leer_entrada primero.")
        destino = self.crear_vinculo(ruta_id, categoria_elegida)
        if destino is None:
            actual.estado = "RUTA_COMPLETA"
            actual.proxima_accion = "RUTA_COMPLETA"
            return actual

        self._aristas_usadas.setdefault(ruta_id, set()).add((actual.nodo_actual, destino))
        etiqueta = _etiqueta_por_defecto(actual.materia, destino)
        pieza = _producir_pieza_borrador(actual.materia, destino, etiqueta, actual.nodo_actual_label)
        siguiente = self._conexiones_no_explotadas(ruta_id, destino)

        fila = RouteMatrixRow(
            ruta_id=ruta_id,
            nodo_actual=destino,
            nodo_actual_label=etiqueta,
            nodo_anterior=actual.nodo_actual,
            nodo_anterior_label=actual.nodo_actual_label,
            siguiente_vinculo=siguiente,
            materia=actual.materia,
            formato=formato,
            estado="PRODUCIDO",
            pieza_producida=pieza.to_dict(),
            proxima_accion="RUTA_COMPLETA" if not siguiente else "VERIFY_SOURCES",
        )
        if actual.estado == "PENDIENTE":
            actual.estado = "PRODUCIDO"
        self._filas.append(fila)
        return fila

    def avanzar_ruta_completa(self, entrada, materia, secuencia_categorias=None, formato="NO_ASIGNADO"):
        """Conveniencia: abre la ruta y la recorre.

        Si `secuencia_categorias` se especifica, sigue exactamente esa
        secuencia y se detiene al agotarla (aunque queden conexiones
        posibles) -- para reproducir una ruta concreta bajo demanda. Si es
        None, explora tomando siempre la primera conexion no explotada
        hasta que la ruta se agote naturalmente. En ambos casos nunca repite
        ni pierde continuidad (ver `valida_continuidad`)."""
        ruta_id = self.leer_entrada(entrada, materia)
        filas = [self.ultima_fila(ruta_id)]
        secuencia_explicita = secuencia_categorias is not None
        pendientes = list(secuencia_categorias or [])
        while True:
            if secuencia_explicita and not pendientes:
                break
            elegida = pendientes.pop(0) if pendientes else None
            antes = len(self._filas)
            resultado = self.producir_pieza(ruta_id, categoria_elegida=elegida, formato=formato)
            if len(self._filas) == antes:
                break  # ruta agotada: no se creo fila nueva
            filas.append(resultado)
            if resultado.proxima_accion == "RUTA_COMPLETA":
                break
        return filas
