"""Barrera de transversalidad: el filtro que decide si un tema es Capa A.

El problema real que resuelve. La generación de contenido venía derivando hacia
lo nacional: de las diez piezas del último lote, seis eran de un solo país, y
cuatro de ellas además se habían DECLARADO panhispánicas aportando fuentes de una
sola jurisdicción. Esa es la falsa universalización que la Capa A existe para
impedir, y hasta ahora nada la detectaba en el momento de proponer el tema — solo
mucho después, al revisar las fuentes.

Este módulo mueve la comprobación al principio. Un tema que nombra un país, una
ley nacional, una moneda o un organismo nacional no es transversal, y aquí se
rechaza antes de que llegue a costar arte, copy o revisión humana.

Lo que este módulo NO hace, y no debe hacer nunca:

  - No afirma nada jurídico. Un tema es una pregunta, no una regla.
  - No aprueba, no abre gates y no sustituye la verificación de fuentes.
  - Un tema que pasa este filtro sigue en REQUIERE_INVESTIGACION con gate CERRADO
    hasta que tenga fuentes oficiales propias de al menos tres jurisdicciones.

Pasar el filtro significa exactamente una cosa: que el tema MERECE que se busquen
esas fuentes. Nada más.

Sin red. Determinista. Solo lee el catálogo.
"""

import json
import re
import unicodedata
from pathlib import Path

AQUI = Path(__file__).resolve().parent
CATALOGO_PATH = AQUI / "catalogo-transversal-v1.json"

# Jurisdicciones mínimas para que un claim pueda declararse CAPA_A_TRANSVERSAL,
# cada una con fuentes propias. Es el mismo umbral que aplica la skill de
# verificación jurídica; se repite aquí para que el filtro de temas no pueda
# quedarse por detrás de él sin que una prueba lo note.
MINIMO_JURISDICCIONES_CAPA_A = 3

# Países y gentilicios hispanohablantes. Nombrar uno dentro de un tema lo saca de
# la Capa A por definición: el tema pasaría a describir un ordenamiento concreto.
PAISES = (
    "españa", "español", "española", "españoles", "españolas",
    "méxico", "mexico", "mexicano", "mexicana", "mexicanos", "mexicanas",
    "argentina", "argentino", "argentinos",
    "colombia", "colombiano", "colombianos",
    "perú", "peru", "peruano", "peruanos",
    "chile", "chileno", "chilenos",
    "uruguay", "uruguayo", "uruguayos",
    "paraguay", "paraguayo", "paraguayos",
    "bolivia", "boliviano", "bolivianos",
    "ecuador", "ecuatoriano", "ecuatorianos",
    "venezuela", "venezolano", "venezolanos",
    "guatemala", "guatemalteco", "guatemaltecos",
    "honduras", "hondureño", "hondurenos",
    "nicaragua", "nicaragüense", "nicaraguense",
    "costa rica", "costarricense", "costarricenses",
    "panamá", "panama", "panameño", "panamenos",
    "cuba", "cubano", "cubanos",
    "república dominicana", "republica dominicana", "dominicano", "dominicanos",
    "puerto rico", "puertorriqueño", "puertorriqueno",
    "el salvador", "salvadoreño", "salvadorenos",
)

# Nombres de cuerpos normativos y organismos nacionales. Un tema que los cita ya
# no es conceptual: describe una fuente concreta de un ordenamiento concreto.
NORMAS_Y_ORGANISMOS = (
    "código civil", "codigo civil", "código penal", "codigo penal",
    "código de comercio", "codigo de comercio", "código del trabajo",
    "ley federal del trabajo", "estatuto de los trabajadores",
    "constitución política", "constitucion politica",
    "boletín oficial", "boletin oficial", "diario oficial",
    "suprema corte", "tribunal supremo", "tribunal constitucional",
    "corte constitucional", "corte suprema", "consejo general del poder judicial",
    "reglamento general de protección de datos", "rgpd",
    "ley general", "ley orgánica", "ley organica", "real decreto",
    "decreto ley", "decreto legislativo",
)

# Monedas: una cifra en moneda nacional ancla el tema a un país aunque no lo
# nombre.
MONEDAS = (
    "euro", "euros", "peso", "pesos", "sol", "soles", "bolívar", "bolivar",
    "quetzal", "quetzales", "córdoba", "cordoba", "colón", "colon", "colones",
    "guaraní", "guarani", "lempira", "lempiras", "boliviano", "bolivianos",
)

# Una cantidad de días/meses/años convierte un mecanismo en un plazo nacional.
PLAZO_RE = re.compile(
    r"\b\d+\s*(d[ií]as?|meses?|a[nñ]os?|semanas?)\b", re.IGNORECASE)

# Un porcentaje o un importe hacen lo mismo.
CIFRA_RE = re.compile(r"\d+\s*%|\b\d[\d.,]*\s*(?=%)")

RIESGOS_VALIDOS = ("bajo", "medio", "alto")
FORMATOS_VALIDOS = ("DIFERENCIAS", "MITO", "CONSECUENCIA", "LISTADO")


def normalizar(texto):
    """Minúsculas y sin tildes, para que 'España' y 'espana' se detecten igual.

    La comparación posterior es por palabra completa, nunca por subcadena: 'peru'
    dentro de 'perutenencia' no debe disparar nada, y 'panama' no debe saltar
    dentro de una palabra que la contenga por casualidad.
    """
    s = unicodedata.normalize("NFD", (texto or "").casefold())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def _contiene_termino(texto_norm, termino):
    """Coincidencia por límites de palabra sobre el texto ya normalizado."""
    patron = r"(?<![0-9a-z])" + re.escape(normalizar(termino)) + r"(?![0-9a-z])"
    return re.search(patron, texto_norm) is not None


def texto_de_tema(tema):
    """Todo el texto libre del tema, que es donde puede colarse lo nacional."""
    campos = ("titulo_de_trabajo", "pregunta_central", "por_que_es_transversal",
              "situacion_humana", "concepto", "submateria", "materia")
    return " \n ".join(str(tema.get(c, "")) for c in campos)


def detectar_anclajes_nacionales(texto):
    """Motivos por los que un texto NO puede considerarse transversal.

    Devuelve una lista de motivos legibles. Vacía significa: nada en el texto lo
    ata a un ordenamiento concreto. NO significa que el tema sea correcto — eso
    lo deciden las fuentes, mucho más tarde.

    El campo 'advertencia' de cada tema queda deliberadamente FUERA de esta
    comprobación: ahí es donde el catálogo dice qué parte del asunto sí es
    nacional, y penalizar esa honestidad empujaría a no escribirla.
    """
    n = normalizar(texto)
    motivos = []
    for pais in PAISES:
        if _contiene_termino(n, pais):
            motivos.append(f"nombra un país o gentilicio: {pais!r}")
    for norma in NORMAS_Y_ORGANISMOS:
        if _contiene_termino(n, norma):
            motivos.append(f"cita una norma u organismo nacional: {norma!r}")
    for moneda in MONEDAS:
        if _contiene_termino(n, moneda):
            motivos.append(f"usa una moneda nacional: {moneda!r}")
    m = PLAZO_RE.search(texto or "")
    if m:
        motivos.append(f"fija un plazo concreto: {m.group(0)!r} — los plazos son nacionales")
    if CIFRA_RE.search(texto or ""):
        motivos.append("fija un porcentaje o importe concreto")
    return motivos


def evaluar_tema(tema):
    """Dictamen completo sobre un tema. Nunca lanza: informa.

    'admisible' significa admisible COMO TEMA, no como pieza. Un tema admisible
    entra en la cola de investigación; no entra en producción.
    """
    motivos = detectar_anclajes_nacionales(texto_de_tema(tema))
    errores = []
    for campo in ("id", "formato", "materia", "concepto", "titulo_de_trabajo",
                  "pregunta_central", "por_que_es_transversal", "advertencia"):
        if not str(tema.get(campo, "")).strip():
            errores.append(f"falta el campo obligatorio {campo!r}")
    if tema.get("formato") not in FORMATOS_VALIDOS:
        errores.append(f"formato inválido: {tema.get('formato')!r}")
    if tema.get("riesgo_de_deriva_nacional") not in RIESGOS_VALIDOS:
        errores.append(f"riesgo inválido: {tema.get('riesgo_de_deriva_nacional')!r}")

    admisible = not motivos and not errores
    return {
        "id": tema.get("id"),
        "admisible_como_tema": admisible,
        "capa_propuesta": "CAPA_A_TRANSVERSAL" if admisible else "NO_DETERMINADO",
        "anclajes_nacionales": motivos,
        "errores_de_forma": errores,
        # Los tres campos siguientes son invariantes, no resultados: un tema
        # nunca los cambia. Se emiten para que ningún consumidor pueda leer un
        # dictamen positivo como si fuera una autorización.
        "estado_juridico": "REQUIERE_INVESTIGACION",
        "gate_arte": "CERRADO",
        "publicacion": "NOT_PUBLISHED",
        "siguiente_accion": (
            f"buscar fuente oficial propia en {MINIMO_JURISDICCIONES_CAPA_A} jurisdicciones"
            if admisible else "corregir o reclasificar: el tema no es transversal"
        ),
    }


def cargar_catalogo(path=None):
    p = Path(path) if path else CATALOGO_PATH
    return json.loads(p.read_text(encoding="utf-8"))


def evaluar_catalogo(path=None):
    return [evaluar_tema(t) for t in cargar_catalogo(path).get("temas", [])]


# ---------------------------------------------------------------------------
# Segunda mitad de la barrera: la cobertura real, no la prosa.
#
# El filtro de texto de arriba caza el caso evidente —un tema que nombra a un
# país— pero NO caza el peligroso, que es el contrario: una pieza que no nombra
# ningún país, se declara panhispánica, y se apoya en fuentes de uno solo. En el
# último lote, cuatro de diez piezas eran exactamente eso, y ninguna habría sido
# detectada leyendo su título.
#
# Por eso la cobertura se cuenta sobre las FUENTES, resolviendo cada una contra
# el registro oficial. Los países nombrados en la prosa no cuentan: solo cuenta
# el territorio que el registro autoriza a respaldar a cada fuente.
# ---------------------------------------------------------------------------

REGISTRO_PATH = (AQUI.parent.parent / ".claude" / "skills"
                 / "legalmente-legal-verification" / "references"
                 / "official-source-registry.json")

# Ámbitos que no son un país. Una fuente supranacional amplía el contexto pero
# NO suma jurisdicción nacional: si sumara, un solo tratado convertiría en
# transversal cualquier afirmación, que es la falsa universalización al revés.
AMBITOS_NO_NACIONALES = {"SUPRANACIONAL", "INTERNACIONAL"}


def cargar_registro(path=None):
    """Fail-closed igual que el validador: un registro ausente o ilegible deja la
    cobertura en cero, nunca la da por buena."""
    p = Path(path) if path else REGISTRO_PATH
    try:
        datos = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(datos, dict) or not isinstance(datos.get("sources"), list):
        return {}
    return {s["id"]: s for s in datos["sources"]
            if isinstance(s, dict) and isinstance(s.get("id"), str)}


def cobertura_por_fuentes(fuentes, registro=None):
    """Países realmente cubiertos por las fuentes de un claim.

    Devuelve (paises, notas). Una fuente sin 'registro_oficial_id', o con uno que
    no existe, no cubre nada: no se le concede el beneficio de la duda.
    """
    reg = registro if registro is not None else cargar_registro()
    paises = set()
    notas = []
    for f in fuentes or []:
        fid = f.get("id", "?")
        rid = f.get("registro_oficial_id")
        if not rid:
            notas.append(f"{fid}: sin 'registro_oficial_id' — no cubre ninguna jurisdicción")
            continue
        entrada = reg.get(rid)
        if entrada is None:
            notas.append(f"{fid}: {rid!r} no existe en el registro oficial")
            continue
        if entrada.get("ambito") in AMBITOS_NO_NACIONALES:
            notas.append(f"{fid}: {rid!r} es de ámbito {entrada.get('ambito')} — "
                         "aporta contexto, no jurisdicción nacional")
            continue
        for j in entrada.get("jurisdicciones", []) or []:
            paises.add(normalizar(j))
    return sorted(paises), notas


def evaluar_cobertura_de_claim(claim, registro=None):
    """¿Puede este claim sostener el alcance que declara?

    El techo es el mínimo real: un claim que declara CAPA_A_TRANSVERSAL con
    fuentes de dos países no es un claim casi transversal, es un claim mal
    declarado.
    """
    declarado = claim.get("alcance")
    paises, notas = cobertura_por_fuentes(claim.get("fuentes"), registro)
    suficiente = len(paises) >= MINIMO_JURISDICCIONES_CAPA_A
    problemas = list(notas)
    if declarado == "CAPA_A_TRANSVERSAL" and not suficiente:
        problemas.insert(0, (
            f"declara CAPA_A_TRANSVERSAL pero sus fuentes solo cubren {paises!r} "
            f"({len(paises)} de {MINIMO_JURISDICCIONES_CAPA_A} jurisdicciones mínimas) "
            "— esto es falsa universalización"))
    return {
        "claim_id": claim.get("claim_id"),
        "alcance_declarado": declarado,
        "paises_cubiertos_por_fuentes": paises,
        "cobertura_suficiente_para_capa_a": suficiente,
        "alcance_maximo_sostenible": (
            "CAPA_A_TRANSVERSAL" if suficiente
            else ("CAPA_C_NACIONAL" if len(paises) == 1 else "NO_DETERMINADO")),
        "problemas": problemas,
        "riesgo_falsa_universalizacion": (
            "alto" if declarado == "CAPA_A_TRANSVERSAL" and not suficiente
            else ("medio" if declarado in (None, "NO_DETERMINADO") else "bajo")),
    }


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    dictamenes = evaluar_catalogo()
    if args.json:
        print(json.dumps(dictamenes, ensure_ascii=False, indent=2))
        return 0
    ok = [d for d in dictamenes if d["admisible_como_tema"]]
    print(f"temas evaluados : {len(dictamenes)}")
    print(f"transversales   : {len(ok)}")
    print(f"rechazados      : {len(dictamenes) - len(ok)}")
    print("\nTodos en REQUIERE_INVESTIGACION, gate CERRADO, NOT_PUBLISHED.")
    for d in dictamenes:
        if d["admisible_como_tema"]:
            continue
        print(f"\n  {d['id']} — RECHAZADO")
        for m in d["anclajes_nacionales"] + d["errores_de_forma"]:
            print(f"    - {m}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
