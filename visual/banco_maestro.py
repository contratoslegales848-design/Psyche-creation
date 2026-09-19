"""Banco maestro de temas/prompts — motor real, no el Excel legacy.

Mandato del Founder: "Revisa y mejora el generador de imágenes de LegalMente
[...] Actualiza el Excel maestro con suficientes prompts nuevos para sostener
la producción continua" (19-sep-2026).

AUTORIZACIÓN EXPRESA (resuelve el conflicto con CLAUDE.md §6): CLAUDE.md §6
prohíbe producir un banco grande nuevo de temas/prompts mientras el lote
piloto activo no se haya publicado ni medido, "salvo orden expresa del
fundador" — y no existe ningún `PublicationDecision` en el repo (el piloto
sigue sin publicarse). Ante ese conflicto, y ante la ambigüedad de "Excel
maestro" (el único artefacto con ese nombre en Drive es
`legalmente-generador-aleatorio.xlsx`, etiquetado por el propio Drive
"[USO LIMITADO — temas; no dirección artística]" — el motor legacy que este
mismo repo ya reemplazó por el motor combinatorio real), se preguntó
explícitamente al Founder. Su respuesta ("Usar el motor real, no el Excel
legacy") autoriza este módulo y fija su alcance: generar el banco con
`universe.py`/`editorial.py`/`generator.py`/`semantic_memory.py` (ya
construidos, probados y en producción real vía `production_run.py`) y
exportar el resultado a Excel/CSV como entregable — SIN reactivar
`legalmente-generador-aleatorio.xlsx` como motor.

Nada de lo que produce este módulo es un candidato jurídicamente verificado:
todo nace `NO_VERIFICADO` (`universe.TopicCandidate`) con `proxima_accion`
hacia `legalmente-legal-verification` (CLAUDE.md §4), y este módulo no abre
ningún gate ni publica nada (CLAUDE.md §6).
"""

import csv
import random
from dataclasses import dataclass, field
from pathlib import Path

import corpus_import as ci
import editorial
import memoria_fuerte as mf
import universe
from semantic_fingerprint import SemanticFingerprint, mas_similar
from semantic_memory import ENTREGADO, SemanticMemory

try:
    import openpyxl
except ImportError:  # pragma: no cover — entorno sin openpyxl instalado
    openpyxl = None

BANCO_DIR = Path(__file__).resolve().parent.parent / "corpus"
BANCO_MEMORIA_PATH = BANCO_DIR / "banco-maestro-memoria.json"
BANCO_EXCEL_PATH = BANCO_DIR / "banco-maestro.xlsx"
BANCO_CSV_PATH = BANCO_DIR / "banco-maestro.csv"

LOTE_ID_BANCO_MAESTRO = "banco-maestro"

# Las 8 categorías que pidió el Founder, mapeadas a familias editoriales YA
# REGISTRADAS en policy/editorial-universe-v1.json (ninguna se inventa aquí —
# CLAUDE.md §2: "Antes de asumir que algo existe [...] verificar el archivo
# real"). Cuando una categoría del Founder cubre más de un matiz real del
# universo editorial (p. ej. "errores frecuentes" también es
# `confusion_habitual`/`que_no_hacer`), se listan todas: la variedad real
# (requisito 6) exige no encoger una categoría amplia a una sola familia.
CATEGORIAS_FOUNDER = {
    "mitos_juridicos": ("mito",),
    "diferencias": ("diferencia",),
    "conceptos": ("concepto", "definicion_operativa", "lenguaje_juridico_explicado", "etimologia"),
    "pasos_practicos": ("primeros_pasos", "que_hacer", "checklist", "herramienta_practica"),
    "errores_frecuentes": ("error_frecuente", "confusion_habitual", "que_no_hacer"),
    "derechos": ("derecho",),
    "obligaciones": ("obligacion",),
    "casos": ("caso_cotidiano", "caso_historico"),
}

DEFAULT_OBJETIVO = 120
DEFAULT_FACTOR_RESERVA = 3
DEFAULT_SEED = 9200

COLUMNAS = ["candidate_id", "categoria_founder", "materia", "submateria",
            "familia_editorial", "necesidad", "rol_lector", "angulo",
            "contexto_funcional", "profundidad", "formato", "concepto_nucleo",
            "relacion", "pregunta_resuelta", "consecuencia", "hook", "emocion",
            "estado", "proxima_accion"]


class BancoMaestroError(ValueError):
    pass


def familia_a_categoria(familia_editorial):
    """A qué categoría del Founder pertenece una familia editorial real, o
    'otros_formatos_ya_definidos' si es una de las 57 restantes del universo
    abierto (requisito 2: "...y otros formatos ya definidos en el sistema")."""
    for categoria, familias in CATEGORIAS_FOUNDER.items():
        if familia_editorial in familias:
            return categoria
    return "otros_formatos_ya_definidos"


def _grupos_de_generacion(universo):
    """Las 8 categorías nombradas + 'otros_formatos_ya_definidos' con el
    resto del universo editorial abierto, para que el banco recorra en
    round-robin las puertas que el Founder nombró Y siga cubriendo el resto
    (requisito 6: "variedad real de [...] ángulos, hooks, narrativas y
    estilos visuales" — encoger a sólo 8 familias violaría ese requisito)."""
    todas = set(universo.names())
    nombradas = set()
    for familias in CATEGORIAS_FOUNDER.values():
        nombradas |= set(familias)
    faltantes = nombradas - todas
    if faltantes:
        raise BancoMaestroError(
            f"CATEGORIAS_FOUNDER referencia familias que no existen en el registro real: "
            f"{sorted(faltantes)}. El registro es la fuente de verdad, nunca esta tabla.")
    otras = tuple(sorted(todas - nombradas))
    grupos = list(CATEGORIAS_FOUNDER.items())
    grupos.append(("otros_formatos_ya_definidos", otras))
    return grupos


def generar_reserva_categorizada(rng, universo, materias, objetivo,
                                 factor_reserva=DEFAULT_FACTOR_RESERVA):
    """Reserva grande que GARANTIZA las 8 categorías del Founder en vez de
    dejarlas a elección uniforme entre las 65 familias (lo que haría
    `universe.build_reserve` sin más). Recorre grupo y materia en
    round-robin, misma lógica de `build_reserve` para evitar que una
    reserva grande deje materias o categorías sin representar."""
    grupos = _grupos_de_generacion(universo)
    orden_materias = sorted(materias)
    rng.shuffle(orden_materias)

    total = max(int(objetivo) * int(factor_reserva), int(objetivo))
    candidatos = []
    for idx in range(total):
        cat_nombre, fams_cat = grupos[idx % len(grupos)]
        fam_nombre = rng.choice(fams_cat)
        mat = orden_materias[idx % len(orden_materias)]
        c = universe.generar_candidato(rng, universo, materias, idx, materia=mat,
                                       familia=fam_nombre)
        candidatos.append(c)
    return candidatos


def _fingerprint_de_registro(registro):
    campos = {k: v for k, v in registro.items() if k in SemanticFingerprint.__dataclass_fields__}
    return SemanticFingerprint(**campos)


def cargar_banco_previo(path=None):
    """Sólo lo que ESTE módulo ya entregó en corridas anteriores (ENTREGADO),
    persistido aparte — nunca el corpus histórico ni memoria fuerte, que se
    reconstruyen frescos desde su propia fuente en cada corrida (mismo
    patrón que `memoria_fuerte.py`: instancias separadas por origen, sólo
    fusionadas para comparar)."""
    return SemanticMemory.load(path or BANCO_MEMORIA_PATH)


def cargar_memoria_historial_completo(banco_previo_path=None):
    """"Historial completo de piezas entregadas" (requisito 3): corpus
    histórico real (174 piezas, HISTORICA) + memoria fuerte real (16 piezas,
    PUBLICADA/PRESELECCIONADA) + todo lo que el banco maestro ya entregó en
    corridas anteriores (ENTREGADO). Las tres fuentes existen y están
    probadas en `production_run.cargar_contexto()`; este módulo las combina
    en una sola `SemanticMemory` porque `evaluar()` sólo compara dentro de
    una misma instancia."""
    regs, _ = ci.construir_registros()
    memoria = SemanticMemory()
    ci.importar(memoria, regs)

    fuerte = mf.cargar_memoria_fuerte()
    for e in fuerte.entries():
        memoria.record(e.fp(), e.estado, e.lote_id)

    previo = cargar_banco_previo(banco_previo_path)
    for e in previo.entries():
        memoria.record(e.fp(), e.estado, e.lote_id)

    return memoria


@dataclass
class ReporteBanco:
    """Clasificación clara de prompts disponibles/utilizados/bloqueados
    (entregable explícito del mandato)."""

    objetivo: int = 0
    entregados: list = field(default_factory=list)     # utilizados: ENTREGADO
    disponibles: list = field(default_factory=list)    # validados, no usados todavía
    bloqueados: list = field(default_factory=list)      # (candidate_id, motivo)
    reserva_total: int = 0
    distribucion_categoria: dict = field(default_factory=dict)
    distribucion_materia: dict = field(default_factory=dict)

    def to_dict(self):
        return {
            "objetivo": self.objetivo,
            "n_entregados": len(self.entregados),
            "entregados": [c.candidate_id for c in self.entregados],
            "n_disponibles": len(self.disponibles),
            "disponibles": [c.candidate_id for c in self.disponibles],
            "n_bloqueados": len(self.bloqueados),
            "bloqueados": list(self.bloqueados),
            "reserva_total": self.reserva_total,
            "distribucion_categoria": dict(self.distribucion_categoria),
            "distribucion_materia": dict(self.distribucion_materia),
        }


def construir_banco(objetivo=DEFAULT_OBJETIVO, seed=DEFAULT_SEED,
                    factor_reserva=DEFAULT_FACTOR_RESERVA, memoria=None,
                    universo=None, materias=None, lote_id=LOTE_ID_BANCO_MAESTRO,
                    banco_previo_path=None, persistir=True):
    """Genera el banco con el motor real y lo audita contra el historial
    completo ANTES de aceptar nada (requisito 3), rechazando duplicados por
    equivalencia semántica —no sólo por título literal— dentro del propio
    banco (requisito 5, `semantic_fingerprint.equivalente_a`/`mas_similar`,
    ya calibrados contra el corpus real, ver `semantic_fingerprint.py`).

    La reserva se genera más grande que `objetivo` (`factor_reserva`): los
    primeros `objetivo` candidatos que superan la auditoría se marcan
    ENTREGADO (utilizados, bloqueados para el futuro — requisito 4); el
    resto que también supera la auditoría queda DISPONIBLE (validado, listo
    para la próxima corrida sin volver a generarse) en vez de descartarse.
    """
    universo = universo or editorial.EditorialUniverse.load()
    if materias is None:
        _, materias = universe.cargar_materias()
    memoria = memoria if memoria is not None else cargar_memoria_historial_completo(
        banco_previo_path)
    banco_previo = cargar_banco_previo(banco_previo_path)

    rng = random.Random(seed)
    reserva = generar_reserva_categorizada(rng, universo, materias, objetivo, factor_reserva)

    entregados, disponibles, bloqueados = [], [], []
    vistos_fp = []  # entregados + disponibles de ESTA corrida: dedup interna

    for c in reserva:
        fp = c.fingerprint()
        veredicto = memoria.evaluar(fp)
        if veredicto.bloquea:
            bloqueados.append((c.candidate_id, veredicto.motivo))
            continue
        if vistos_fp:
            _, d = mas_similar(fp, vistos_fp)
            if d is not None and d.valor < memoria.umbral:
                bloqueados.append((c.candidate_id,
                    f"equivalente dentro de este mismo banco a distancia {d.valor} < "
                    f"umbral {memoria.umbral} — cambiar palabras no lo convierte en nuevo "
                    "(requisito 5)."))
                continue
        vistos_fp.append(fp)
        if len(entregados) < objetivo:
            entregados.append(c)
            memoria.record(fp, ENTREGADO, lote_id)
            banco_previo.record(fp, ENTREGADO, lote_id)
        else:
            disponibles.append(c)

    if persistir:
        banco_previo.save(banco_previo_path or BANCO_MEMORIA_PATH)

    dist_cat, dist_mat = {}, {}
    for c in entregados:
        cat = familia_a_categoria(c.familia_editorial)
        dist_cat[cat] = dist_cat.get(cat, 0) + 1
        dist_mat[c.materia] = dist_mat.get(c.materia, 0) + 1

    return ReporteBanco(objetivo=objetivo, entregados=entregados, disponibles=disponibles,
                        bloqueados=bloqueados, reserva_total=len(reserva),
                        distribucion_categoria=dist_cat, distribucion_materia=dist_mat)


# ---------------------------------------------------------------------------
# Exportación — "Excel maestro actualizado" (entregable explícito).

def _fila(candidato, estado=ENTREGADO):
    return [candidato.candidate_id, familia_a_categoria(candidato.familia_editorial),
            candidato.materia, candidato.submateria, candidato.familia_editorial,
            candidato.necesidad, candidato.rol_lector, candidato.angulo,
            candidato.contexto_funcional, candidato.profundidad, candidato.formato,
            candidato.concepto_nucleo, candidato.relacion, candidato.pregunta_resuelta,
            candidato.consecuencia, candidato.hook, candidato.emocion, estado,
            candidato.proxima_accion]


def exportar_csv(candidatos, path=None, estado=ENTREGADO):
    path = Path(path) if path else BANCO_CSV_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(COLUMNAS)
        for c in candidatos:
            w.writerow(_fila(c, estado))
    return path


def exportar_excel(candidatos, path=None, estado=ENTREGADO, hoja="banco_maestro"):
    if openpyxl is None:
        raise BancoMaestroError(
            "openpyxl no está disponible en este entorno: usa exportar_csv() en su lugar.")
    path = Path(path) if path else BANCO_EXCEL_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = hoja[:31]  # límite real de Excel para nombres de hoja
    ws.append(COLUMNAS)
    for c in candidatos:
        ws.append(_fila(c, estado))
    wb.save(path)
    return path


def exportar_banco(reporte, excel_path=None, csv_path=None):
    """Exporta ENTREGADOS y DISPONIBLES en hojas/archivos separados —
    clasificación explícita, nunca mezclada en una sola lista sin etiqueta."""
    rutas = {"csv_entregados": exportar_csv(reporte.entregados, csv_path, ENTREGADO)}
    if openpyxl is not None:
        path = Path(excel_path) if excel_path else BANCO_EXCEL_PATH
        path.parent.mkdir(parents=True, exist_ok=True)
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "ENTREGADO"
        ws.append(COLUMNAS)
        for c in reporte.entregados:
            ws.append(_fila(c, ENTREGADO))
        ws2 = wb.create_sheet("DISPONIBLE")
        ws2.append(COLUMNAS)
        for c in reporte.disponibles:
            ws2.append(_fila(c, "DISPONIBLE"))
        ws3 = wb.create_sheet("BLOQUEADO")
        ws3.append(["candidate_id", "motivo"])
        for cid, motivo in reporte.bloqueados:
            ws3.append([cid, motivo])
        wb.save(path)
        rutas["excel"] = path
    return rutas


if __name__ == "__main__":
    import json
    reporte = construir_banco()
    rutas = exportar_banco(reporte)
    print(json.dumps({**reporte.to_dict(), "rutas": {k: str(v) for k, v in rutas.items()}},
                     indent=2, ensure_ascii=False)[:4000])
