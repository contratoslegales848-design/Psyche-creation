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

Campos de la matriz (RouteMatrixRow), en el orden pedido: ID de ruta |
content_id | nodo anterior | nodo actual | siguiente vinculo | materia |
submateria | concepto | formato | estado | fuente | jurisdiccion |
verificacion | pieza producida | proxima accion | vinculo_visual (metafora de la transicion,
consumida por pipeline.generate_visual_from_content_id via brief.metaphor).
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

# Cada transicion tiene una metafora visual ejecutable. Es vocabulario de
# NAVEGACION -- expresa la relacion editorial entre nodos y alimenta
# brief.metaphor (ver pipeline.generate_visual_from_content_id) -- nunca una
# afirmacion juridica ni un dato que requiera verificacion.
VINCULOS_VISUALES = {
    (CAT_MATERIA, CAT_CAUSA): "una materia abstracta se concreta en una conducta observable",
    (CAT_CAUSA, CAT_BIEN_JURIDICO): "la conducta revela el bien jurídico que está en juego",
    (CAT_CAUSA, CAT_CONSECUENCIA): "una acción deja una huella visible en su consecuencia",
    (CAT_BIEN_JURIDICO, CAT_CONSECUENCIA): "lo protegido se transforma en un efecto identificable",
    (CAT_CONSECUENCIA, CAT_RESPONSABILIDAD): "el daño conecta físicamente con quien debe responder",
    (CAT_RESPONSABILIDAD, CAT_PRUEBA): "la responsabilidad se sostiene en rastros verificables",
    (CAT_RESPONSABILIDAD, CAT_DEFENSA): "la posición de una parte abre un espacio de defensa",
    (CAT_PRUEBA, CAT_PROCEDIMIENTO): "los rastros se ordenan en una ruta de actuación",
    (CAT_DEFENSA, CAT_PROCEDIMIENTO): "la defensa encuentra el cauce procedimental correspondiente",
    (CAT_PROCEDIMIENTO, CAT_REPARACION): "el camino procesal desemboca en una forma de reparación",
    (CAT_REPARACION, CAT_PREVENCION): "la reparación deja una barrera para evitar la repetición",
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

# Anulaciones mas especificas por (materia, submateria): la tabla de arriba
# es un promedio razonable por materia, pero "Incumplimiento" es vocabulario
# de obligaciones/contratos y NO encaja con derechos reales (propiedad,
# posesion, usucapion no nacen de un incumplimiento sino de un hecho o acto
# posesorio). Hallazgo real detectado al verificar la fila CAUSA de
# LM-PIEZA-01-REALES (civil/derechos_reales/propiedad_y_posesion) contra su
# claim packet real: ningun claim aprobado de esa pieza es sobre un
# incumplimiento -- son definiciones de propiedad/posesion y una regla de
# usucapion. Sigue siendo vocabulario de NAVEGACION generico (no una
# afirmacion juridica): no requiere verificacion legal, igual que el resto
# de esta tabla.
VOCABULARIO_POR_SUBMATERIA = {
    ("civil", "derechos_reales"): {
        CAT_CAUSA: "Hecho o acto posesorio",
        CAT_BIEN_JURIDICO: "Derecho real en juego",
        CAT_CONSECUENCIA: "Efecto sobre la posesión o propiedad",
    },
}


def _normaliza_materia(materia):
    return (materia or "").strip().lower()


def _etiqueta_por_defecto(materia, categoria, submateria=""):
    if categoria == CAT_MATERIA:
        return (materia or "").strip() or "Materia sin especificar"
    clave_sub = (_normaliza_materia(materia), _normaliza_materia(submateria))
    tabla_sub = VOCABULARIO_POR_SUBMATERIA.get(clave_sub, {})
    if categoria in tabla_sub:
        return tabla_sub[categoria]
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
    vinculo_visual: str = ""                  # metafora de la transicion anterior -> actual

    def to_dict(self):
        return asdict(self)


def _producir_pieza_borrador(materia, categoria_anterior, categoria_actual, etiqueta_actual, etiqueta_anterior):
    vinculo_visual = VINCULOS_VISUALES.get((categoria_anterior, categoria_actual), "") if categoria_anterior else ""
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
            + (f" El vínculo debe hacerse visible: {vinculo_visual}." if vinculo_visual else "")
        ),
        vinculo_visual=vinculo_visual,
    )


@dataclass
class RouteMatrixRow:
    """Una fila real de la matriz de rutas. Los campos siguen el orden
    pedido: ID de ruta | content_id | nodo anterior | nodo actual |
    siguiente vínculo | materia | concepto | formato | estado | fuente |
    jurisdicción | verificación | pieza producida | próxima acción.

    `content_id` y `concepto` solo se llenan cuando la ruta se abrio desde
    un artefacto real (`leer_entrada_desde_artefacto`); una ruta manual los
    deja vacios en vez de inventarlos. `fuente` es la referencia evidencial
    (p.ej. una cita cuando exista); `verificacion` es el estado de
    verificacion juridica de la PIEZA de esta fila -- son dos cosas
    distintas y nunca deben compartir un solo campo."""

    ruta_id: str
    nodo_actual: str                          # categoria, p.ej. "CAUSA"
    nodo_actual_label: str                    # etiqueta legible, p.ej. "Delito"
    nodo_anterior: str = ""
    nodo_anterior_label: str = ""
    siguiente_vinculo: list = field(default_factory=list)   # categorias candidatas no explotadas
    materia: str = ""
    submateria: str = ""                      # taxonomia.submateria del artefacto real, nunca inventada
    concepto: str = ""                        # taxonomia.concepto del artefacto real, nunca inventado
    content_id: str = ""                      # content_id real del artefacto de origen, si lo hay
    formato: str = "NO_ASIGNADO"
    estado: str = "PENDIENTE"                 # PENDIENTE | PRODUCIDO | RUTA_COMPLETA
    fuente: str = ""                          # referencia evidencial (cita), vacia si no hay ninguna aun
    jurisdiccion: str = "PANHISPANICO_COMPARADO"
    verificacion: str = "NO_VERIFICADO"       # estado_verificacion de la pieza de ESTA fila
    pieza_producida: dict = None
    proxima_accion: str = "ABRIR_VINCULO"     # ABRIR_VINCULO | VERIFY_SOURCES | RUTA_COMPLETA
    vinculo_visual: str = ""                  # metafora de la transicion nodo_anterior -> nodo_actual

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
        etiqueta = _etiqueta_por_defecto(actual.materia, destino, submateria=actual.submateria)
        pieza = _producir_pieza_borrador(
            actual.materia, actual.nodo_actual, destino, etiqueta, actual.nodo_actual_label
        )
        siguiente = self._conexiones_no_explotadas(ruta_id, destino)

        fila = RouteMatrixRow(
            ruta_id=ruta_id,
            nodo_actual=destino,
            nodo_actual_label=etiqueta,
            nodo_anterior=actual.nodo_actual,
            nodo_anterior_label=actual.nodo_actual_label,
            siguiente_vinculo=siguiente,
            materia=actual.materia,
            # continuidad real: content_id/submateria/concepto/jurisdiccion
            # vienen del artefacto que abrio la ruta y deben sobrevivir cada
            # nodo, no solo el primero -- perderlos aqui seria perder el
            # contexto que justifico abrir la ruta.
            submateria=actual.submateria,
            concepto=actual.concepto,
            content_id=actual.content_id,
            jurisdiccion=actual.jurisdiccion,
            formato=formato,
            estado="PRODUCIDO",
            verificacion=pieza.estado_verificacion,
            pieza_producida=pieza.to_dict(),
            proxima_accion="RUTA_COMPLETA" if not siguiente else "VERIFY_SOURCES",
            vinculo_visual=pieza.vinculo_visual,
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

    def leer_entrada_desde_artefacto(self, artefacto):
        """Abre una ruta desde un artefacto real de ``content/*.json``.

        Solo extrae identidad editorial y taxonomía declaradas en el
        artefacto; no inventa materia, submateria, conceptos ni autoridad
        jurídica. La ruta sigue siendo una estructura de navegación y sus
        piezas permanecen sin verificar. `content_id`, `submateria` y
        `concepto` quedan registrados en CADA fila (incluidas las que se
        produzcan despues, via `producir_pieza`, que los propaga) -- nunca
        solo en la primera."""
        if not isinstance(artefacto, dict):
            raise ValueError("artefacto de contenido ausente o invalido.")
        proc = artefacto.get("procedencia") or {}
        tax = artefacto.get("taxonomia") or {}
        content_id = str(proc.get("content_id") or artefacto.get("id") or "").strip()
        materia = str(tax.get("materia") or "").strip()
        submateria = str(tax.get("submateria") or "").strip()
        concepto = str(tax.get("concepto") or "").strip()
        entrada = str(artefacto.get("titulo") or artefacto.get("frase") or "").strip()
        if not content_id:
            raise ValueError("artefacto sin procedencia.content_id ni id.")
        if not materia:
            raise ValueError(f"artefacto {content_id!r} sin taxonomia.materia.")
        if not entrada:
            raise ValueError(f"artefacto {content_id!r} sin titulo ni frase.")
        ruta_id = self.leer_entrada(entrada, materia)
        for fila in self.filas_de(ruta_id):
            fila.content_id = content_id
            fila.submateria = submateria
            fila.concepto = concepto
        return ruta_id


def abrir_ruta_desde_content_id(engine, content_id, resolver_module=None):
    """Resuelve un CONTENT_ID real y lo registra en el motor.

    La resolución fail-closed pertenece a ``resolver``; este helper no abre
    gates ni convierte el artefacto en publicable. Devuelve ``(resolution,
    ruta_id)`` para que el pipeline pueda consumir ambos contratos.
    """
    if resolver_module is None:
        import resolver as resolver_module
    resolution = resolver_module.resolve(content_id)
    if not resolution.resolved:
        raise ValueError("content_id no resuelto: " + "; ".join(resolution.blocking))
    ruta_id = engine.leer_entrada_desde_artefacto(resolution.artefacto)
    return resolution, ruta_id
