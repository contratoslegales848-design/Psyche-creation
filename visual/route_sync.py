"""Sincronizacion de la matriz de rutas LegalMente con una hoja externa.

Fase 6 del mandato de auditoria integral. Una sola capa responsable de
convertir el estado real del motor de rutas (`route_engine.RouteEngine`) en
filas de un contrato de 14 campos, y de exportarlas de forma determinista,
idempotente y auditable. Esta capa NUNCA decide autoridad juridica: solo lee
lo que `RouteMatrixRow` ya tiene y lo serializa.

Contrato canonico de 14 campos (orden fijo, ver CANONICAL_FIELDS):

    1. ruta_id             8. concepto
    2. content_id          9. formato
    3. nodo_anterior       10. estado
    4. nodo_actual         11. fuente
    5. siguiente_vinculo   12. jurisdiccion
    6. materia             13. estado_verificacion
    7. submateria          14. proxima_accion

Mapeo de nombres (el repositorio ya tenia nombres equivalentes; se conservan
los internos y se documenta el mapeo aqui en vez de renombrar otra vez un
campo que ya migro una vez en `71b79ca`):

    - `estado_verificacion` (contrato) <- `RouteMatrixRow.verificacion` (interno)
    - `nodo_anterior`/`nodo_actual` (contrato) <- combinan categoria + etiqueta
      legible del campo interno correspondiente (`nodo_actual` +
      `nodo_actual_label`), como "CATEGORIA — Etiqueta", para que la hoja sea
      legible por un humano sin perder el codigo maquina. La fila inicial usa
      "" para nodo_anterior (no un texto decorativo): un dato ausente se
      representa vacio, nunca inventado.
    - `siguiente_vinculo` (contrato) <- `json.dumps(sorted(...))` de la lista
      interna: serializacion JSON estable, nunca el orden de insercion (que
      no es determinista entre corridas equivalentes).

Todos los demas campos del contrato tienen el mismo nombre en
`RouteMatrixRow` y se copian tal cual.
"""

import csv
import hashlib
import io
import json
from dataclasses import dataclass, field
from pathlib import Path

import route_engine

SYNC_SCHEMA_VERSION = "1.0"

CANONICAL_FIELDS = [
    "ruta_id", "content_id", "nodo_anterior", "nodo_actual", "siguiente_vinculo",
    "materia", "submateria", "concepto", "formato", "estado", "fuente",
    "jurisdiccion", "estado_verificacion", "proxima_accion",
]


def _nodo_legible(categoria, etiqueta):
    """Combina categoria + etiqueta en un solo texto legible. Vacio si no
    hay categoria (p.ej. nodo_anterior de la primera fila de una ruta)."""
    if not categoria:
        return ""
    if etiqueta and etiqueta != categoria:
        return f"{categoria} — {etiqueta}"
    return categoria


def export_row(fila):
    """Convierte una `RouteMatrixRow` real a un dict con EXACTAMENTE los 14
    campos del contrato canonico, en el orden fijo. No inventa ningun valor
    ausente: lo que la fila no tiene, se exporta vacio ("" o "[]")."""
    return {
        "ruta_id": fila.ruta_id,
        "content_id": fila.content_id,
        "nodo_anterior": _nodo_legible(fila.nodo_anterior, fila.nodo_anterior_label),
        "nodo_actual": _nodo_legible(fila.nodo_actual, fila.nodo_actual_label),
        "siguiente_vinculo": json.dumps(sorted(fila.siguiente_vinculo), ensure_ascii=False),
        "materia": fila.materia,
        "submateria": fila.submateria,
        "concepto": fila.concepto,
        "formato": fila.formato,
        "estado": fila.estado,
        "fuente": fila.fuente,
        "jurisdiccion": fila.jurisdiccion,
        "estado_verificacion": fila.verificacion,
        "proxima_accion": fila.proxima_accion,
    }


def export_ruta(engine, ruta_id):
    """Exporta las filas de UNA ruta, en el orden real en que se produjeron
    (RouteEngine.filas_de ya conserva orden de insercion == orden de ruta)."""
    return [export_row(f) for f in engine.filas_de(ruta_id)]


def export_all(engine):
    """Exporta TODAS las rutas conocidas por el motor, agrupadas por
    ruta_id en el orden en que se vieron por primera vez, y dentro de cada
    ruta en el orden real de sus nodos. Determinista: dos llamadas sobre el
    mismo estado del motor producen exactamente la misma lista."""
    vistas = []
    for f in engine._filas:  # orden de insercion real, nunca reordenado
        if f.ruta_id not in vistas:
            vistas.append(f.ruta_id)
    filas = []
    for ruta_id in vistas:
        filas.extend(export_ruta(engine, ruta_id))
    return filas


def assert_no_duplicate_rows(rows):
    """Cada (ruta_id, nodo_actual) debe aparecer una sola vez en un export.
    Si no, algo en el motor esta produciendo nodos repetidos -- exactamente
    lo que `valida_continuidad()` ya vigila del lado del motor; esta es la
    misma garantia vista del lado del export."""
    vistos = set()
    dup = []
    for r in rows:
        clave = (r["ruta_id"], r["nodo_actual"])
        if clave in vistos:
            dup.append(clave)
        vistos.add(clave)
    if dup:
        raise ValueError(f"export con filas duplicadas (ruta_id, nodo_actual): {dup}")
    return True


def rows_signature(rows):
    """Huella determinista del contenido exportado. Dos exports del mismo
    estado producen la MISMA firma (idempotencia verificable); dos exports
    de estados distintos producen firmas distintas."""
    canonical = json.dumps(rows, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def to_csv_text(rows):
    """Serializa las filas a CSV con el encabezado exacto del contrato, en
    el orden fijo de CANONICAL_FIELDS -- el formato que create_file sabe
    convertir a una hoja de Google Sheets nativa."""
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=CANONICAL_FIELDS, lineterminator="\n")
    writer.writeheader()
    for r in rows:
        writer.writerow({k: r.get(k, "") for k in CANONICAL_FIELDS})
    return buf.getvalue()


@dataclass
class SyncReceipt:
    """Recibo local de una sincronizacion: que se exporto, cuando, y con
    que firma -- para poder detectar despues si una corrida nueva cambio
    algo o fue un no-op exacto (idempotencia verificable sin recalcular)."""

    schema_version: str
    fields: list
    row_count: int
    content_sha256: str
    rows: list = field(default_factory=list)

    def to_dict(self):
        return {
            "schema_version": self.schema_version,
            "fields": list(self.fields),
            "row_count": self.row_count,
            "content_sha256": self.content_sha256,
            "rows": self.rows,
        }


def build_receipt(rows):
    assert_no_duplicate_rows(rows)
    return SyncReceipt(
        schema_version=SYNC_SCHEMA_VERSION,
        fields=list(CANONICAL_FIELDS),
        row_count=len(rows),
        content_sha256=rows_signature(rows),
        rows=rows,
    )


def write_receipt(receipt, path):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(receipt.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return p


class UnknownSyncSchema(Exception):
    """El recibo persistido no coincide con el esquema/campos actuales.
    Fail-closed: nunca se reinterpreta un recibo de otro esquema como si
    fuera compatible."""


def load_receipt(path):
    """Carga un recibo persistido. Fail-closed ante version o campos
    desconocidos: levanta UnknownSyncSchema en vez de adivinar, para que el
    llamador decida (nunca se sincroniza "a ciegas" sobre un esquema que
    cambio)."""
    p = Path(path)
    if not p.is_file():
        return None
    data = json.loads(p.read_text(encoding="utf-8"))
    if data.get("schema_version") != SYNC_SCHEMA_VERSION:
        raise UnknownSyncSchema(
            f"recibo con schema_version {data.get('schema_version')!r}, "
            f"esperado {SYNC_SCHEMA_VERSION!r}."
        )
    if list(data.get("fields") or []) != CANONICAL_FIELDS:
        raise UnknownSyncSchema(
            f"recibo con campos {data.get('fields')!r}, esperado {CANONICAL_FIELDS!r}."
        )
    return SyncReceipt(**data)


def avanzar_desde_content_id(engine, content_id, categoria_elegida=None,
                              formato="NO_ASIGNADO", resolver_module=None):
    """Punto de entrada de alto nivel (Fase 4): recibe un CONTENT_ID real,
    resuelve el artefacto canonico, abre o CONTINUA su ruta (nunca la
    duplica), produce el siguiente nodo natural -- o el elegido
    explicitamente -- registrando la arista usada, y devuelve
    (resolution, filas_exportadas) con las 14 columnas del contrato.

    Reanudable sin perder contexto: si ya existe una ruta para este
    content_id (misma entrada+materia), `leer_entrada_desde_artefacto` la
    continua en vez de crear una nueva, y `producir_pieza` nunca repite una
    arista ya explotada en esa ruta -- llamar esta funcion varias veces
    sobre el mismo content_id avanza la ruta un nodo por llamada, sin
    duplicar ningun nodo anterior.

    No abre ningun gate: la autoridad de produccion visual sigue
    resolviendose exclusivamente en `pipeline.generate_visual_from_content_id`
    / `gates.can_enter_visual_generation`, nunca aqui.
    """
    resolution, ruta_id = route_engine.abrir_ruta_desde_content_id(
        engine, content_id, resolver_module=resolver_module)
    fila = engine.producir_pieza(ruta_id, categoria_elegida=categoria_elegida, formato=formato)
    return resolution, export_ruta(engine, ruta_id)


@dataclass
class CicloResultado:
    """Resultado de un ciclo operativo completo (pasos 1-13 del mandato).
    No es un campo nuevo de la matriz -- es el reporte de UNA ejecucion del
    ciclo, para que el llamador (CLI, otra sesion, un humano) sepa
    exactamente que paso y cual es la unica proxima accion."""

    resolution: object
    fila: object                    # RouteMatrixRow real (no el dict exportado)
    fila_exportada: dict            # las 14 columnas del contrato
    continuidad_ok: bool
    problemas_continuidad: list
    visual_intentado: bool
    visual_status: str              # "" si no se intento; si no, el status real del receipt
    visual_error: str               # "" si no hubo excepcion
    proxima_accion: str             # UNA sola frase ejecutable

    def to_dict(self):
        d = dict(self.fila_exportada)
        d["_continuidad_ok"] = self.continuidad_ok
        d["_visual_intentado"] = self.visual_intentado
        d["_visual_status"] = self.visual_status
        d["_proxima_accion_ciclo"] = self.proxima_accion
        return d


def ejecutar_ciclo_operativo(engine, content_id, categoria_elegida=None, formato="NO_ASIGNADO",
                              brief=None, policy=None, provider=None, dry_run=True,
                              resolver_module=None, pipeline_module=None):
    """El ciclo operativo completo (pasos 1-13 del mandato de operacion
    continua), en una sola llamada:

    1-2. Lee el estado real y valida el content_id contra el canon
         (`route_engine.abrir_ruta_desde_content_id` -> `resolver.resolve`,
         fail-closed: ValueError si no resuelve).
    3-4. Elige el siguiente nodo natural no utilizado y construye el
         vinculo (`RouteEngine.producir_pieza`, nunca repite una arista).
    5-6. Crea la pieza ejecutiva BORRADOR, siempre NO_VERIFICADO
         (`route_engine._producir_pieza_borrador`).
    7.   `proxima_accion` queda VERIFY_SOURCES o RUTA_COMPLETA segun
         corresponda (ya calculado por `producir_pieza`).
    8-10. SOLO si el llamador aporta `brief` + `policy` + `provider`, envia
         la fila al pipeline canonico via
         `pipeline.generate_visual_from_route_row` -- que evalua el gate
         real y jamas produce mas que PENDIENTE_REVISION_HUMANA. Si no se
         aportan los tres, el ciclo se detiene despues del paso 7 sin
         inventar un brief (la direccion de arte no debe inventarse).
    11.  El resultado del intento visual (status del receipt, o el error si
         algo exploto) se registra en `fila.pieza_producida`, nunca en un
         campo nuevo de las 14 columnas del contrato.
    12.  La fila ya vive en `engine` (mutacion in-place vía
         `RouteEngine.producir_pieza`) -- exportarla es idempotente
         (`export_row`), no se duplica nada.
    13.  Se relee `engine.filas_de(ruta_id)` y se corre
         `valida_continuidad()` ANTES de devolver el resultado: si algo se
         perdio, `continuidad_ok` es False y `problemas_continuidad` lo dice
         explicito -- nunca se devuelve un resultado silenciosamente
         corrupto.

    Un fallo del intento visual (paso 8-10) NUNCA corrompe el estado de la
    ruta: la pieza y su registro en la matriz ya existen antes de intentar
    el paso visual, y una excepcion ahi se captura y se reporta en
    `visual_error` en vez de propagarse y dejar la matriz en un estado
    ambiguo.
    """
    resolution, ruta_id = route_engine.abrir_ruta_desde_content_id(
        engine, content_id, resolver_module=resolver_module)
    fila = engine.producir_pieza(ruta_id, categoria_elegida=categoria_elegida, formato=formato)

    visual_intentado = False
    visual_status = ""
    visual_error = ""
    if brief is not None and policy is not None and provider is not None:
        visual_intentado = True
        pl = pipeline_module
        if pl is None:
            import pipeline as pl
        try:
            run = pl.generate_visual_from_route_row(fila, brief, policy, provider, dry_run=dry_run)
            visual_status = run.receipt.status
            if fila.pieza_producida is not None:
                fila.pieza_producida["visual_run_status"] = visual_status
        except Exception as exc:  # nunca deja el ciclo a medias: se reporta, no se propaga
            visual_error = f"{type(exc).__name__}: {exc}"
            if fila.pieza_producida is not None:
                fila.pieza_producida["visual_run_error"] = visual_error

    # Paso 13: releer y comprobar que la informacion no se perdio ANTES de devolver.
    continuidad_ok, problemas_continuidad = engine.valida_continuidad(ruta_id)

    if visual_error:
        proxima_accion = f"REVISAR_ERROR_VISUAL: {visual_error}"
    elif visual_status == "GATE_CERRADO":
        proxima_accion = "GATE_CERRADO: resolver bloqueo juridico antes de reintentar (ver receipt.motivos)."
    elif visual_status in ("DRY_RUN", "PENDIENTE_REVISION_HUMANA"):
        proxima_accion = (
            "REVISION_HUMANA_VISUAL_PENDIENTE" if visual_status == "PENDIENTE_REVISION_HUMANA"
            else "DRY_RUN_OK: repetir con dry_run=False y proveedor real para producir el asset."
        )
    else:
        proxima_accion = fila.proxima_accion  # VERIFY_SOURCES | RUTA_COMPLETA | ABRIR_VINCULO

    return CicloResultado(
        resolution=resolution,
        fila=fila,
        fila_exportada=export_row(fila),
        continuidad_ok=continuidad_ok,
        problemas_continuidad=problemas_continuidad,
        visual_intentado=visual_intentado,
        visual_status=visual_status,
        visual_error=visual_error,
        proxima_accion=proxima_accion,
    )


def sync_is_noop(engine, receipt_path):
    """True si el estado ACTUAL del motor produce exactamente la misma
    firma que el ultimo recibo persistido -- es decir, sincronizar de nuevo
    no añadiria ni cambiaria ninguna fila. False si hay recibo previo y
    difiere, o si no hay recibo previo (primera sincronizacion)."""
    anterior = load_receipt(receipt_path)
    if anterior is None:
        return False
    actuales = export_all(engine)
    return rows_signature(actuales) == anterior.content_sha256
