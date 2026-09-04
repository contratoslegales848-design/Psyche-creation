"""Barrera de anclaje nacional: descarta lo que YA se ve nacional. Nada mas.

Este modulo NO decide si un tema es Capa A. Ningun filtro de texto puede.

El problema que resuelve. La generacion venia derivando hacia lo nacional: de las
diez piezas del ultimo lote, seis eran de un solo pais, y cuatro se DECLARARON
panhispanicas aportando fuentes de una sola jurisdiccion. Nada lo detectaba al
proponer el tema, solo mucho despues, al revisar las fuentes.

Lo que el filtro demuestra, dicho con exactitud:

    NO_EXPLICIT_NATIONAL_ANCHOR

Es decir: el TEXTO del candidato no nombra pais, ley nacional, moneda ni plazo.
Eso es una propiedad de la redaccion, no del derecho. NO demuestra
CAPA_A_TRANSVERSAL, y confundir ambas cosas seria repetir el error con mejor
letra: cuatro de aquellas diez piezas estaban escritas sin un solo toponimo y
describian el derecho de un unico pais.

CUIDADO — un tema tampoco es terreno neutral. Un titulo, una pregunta, un
contraste o una justificacion pueden contener una proposicion juridica. Decir
"esta distincion existe en toda la tradicion civil" es afirmar algo sobre mas de
veinte ordenamientos sin haber leido ninguno. Por eso el catalogo guarda esas
justificaciones como LEGAL_HYPOTHESIS y no como hechos, y por eso este modulo no
puede sostener que un candidato carezca de riesgo juridico.

Escalera epistemica, de menor a mayor exigencia:

    TOPIC_CANDIDATE        pregunta humana que merece investigarse
    LEGAL_HYPOTHESIS       relacion plausible, todavia no demostrada
    VERIFIED_CLAIM         con fuente, territorio, vigencia y limites
    HUMAN_APPROVED_CONTENT texto exacto aprobado por un humano

Este modulo emite el PRIMERO y no puede conceder ninguno de los otros tres.

Y sobre la cobertura: tres jurisdicciones con evidencia propia demuestran
cobertura comparada DE ESAS TRES. No universalidad panhispanica. Hay mas de
veinte ordenamientos hispanohablantes; tres no son todos.

Sin red. Determinista. Solo lee el catalogo y el registro oficial.
"""

import json
import re
import unicodedata
from pathlib import Path

AQUI = Path(__file__).resolve().parent
CATALOGO_PATH = AQUI / "catalogo-transversal-v1.json"

# Jurisdicciones mínimas con fuente propia para que la cobertura comparada sea
# siquiera evaluable. NO es un umbral que conceda capa: alcanzarlo demuestra
# cobertura comparada en esas jurisdicciones y nada más.
MINIMO_JURISDICCIONES_COMPARADAS = 3
# Alias retirado a propósito: se llamaba MINIMO_JURISDICCIONES_COMPARADAS, y el
# nombre invitaba a leer "tres países => Capa A", que es la conclusión que este
# módulo existe para impedir.

# Lo que tres jurisdicciones con fuente propia SÍ demuestran.
COBERTURA_COMPARADA_VERIFICADA = "COBERTURA_COMPARADA_VERIFICADA"

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

# Escalera epistemica. Ningun escalon se alcanza por el paso del tiempo ni por
# la ausencia de objeciones, y este modulo NO puede subir ninguno por su cuenta:
# solo emite el primero.
TOPIC_CANDIDATE = "TOPIC_CANDIDATE"          # pregunta humana que merece investigarse
LEGAL_HYPOTHESIS = "LEGAL_HYPOTHESIS"        # relacion plausible, no demostrada
VERIFIED_CLAIM = "VERIFIED_CLAIM"            # con fuente, territorio, vigencia y limites
HUMAN_APPROVED_CONTENT = "HUMAN_APPROVED_CONTENT"  # texto exacto aprobado por un humano

# Lo unico que demuestra pasar el filtro de texto. NO es una capa jurisdiccional
# y no debe compararse con ninguna: describe una propiedad del TEXTO del
# candidato, no del derecho.
NO_EXPLICIT_NATIONAL_ANCHOR = "NO_EXPLICIT_NATIONAL_ANCHOR"

# Cuando no se ha podido consultar el inventario de piezas vigentes.
INVENTORY_NOT_CHECKED = "INVENTORY_NOT_CHECKED"

RIESGOS_VALIDOS = ("bajo", "medio", "alto")
# El vocabulario de formas vive en lote.py, que es su dueno. Aqui se importa
# tarde para no crear un ciclo, y no se duplica: dos listas de formas volverian a
# derivar como derivaron las capas jurisdiccionales.
def formas_editoriales():
    from lote import FORMAS_EDITORIALES
    return FORMAS_EDITORIALES


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
    campos = ("titulo_de_trabajo", "pregunta_central", "hipotesis_de_transversalidad",
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
    for campo in ("id", "forma_editorial", "materia", "concepto", "titulo_de_trabajo",
                  "pregunta_central", "hipotesis_de_transversalidad", "advertencia"):
        if not str(tema.get(campo, "")).strip():
            errores.append(f"falta el campo obligatorio {campo!r}")
    if tema.get("forma_editorial") not in formas_editoriales():
        errores.append(f"forma editorial inválida: {tema.get('forma_editorial')!r}")
    if tema.get("riesgo_de_deriva_nacional") not in RIESGOS_VALIDOS:
        errores.append(f"riesgo inválido: {tema.get('riesgo_de_deriva_nacional')!r}")

    admisible = not motivos and not errores
    return {
        "id": tema.get("id"),
        "admisible_como_tema": admisible,
        # Lo que el filtro demuestra, dicho con exactitud. La version anterior
        # ponia aqui "CAPA_A_TRANSVERSAL", y eso era un salto injustificado: que
        # un texto no nombre paises no dice nada sobre el derecho de esos paises.
        # Cuatro de las diez piezas del ultimo lote estaban redactadas sin un solo
        # toponimo y describian el derecho de uno solo.
        "demostrado_por_el_filtro": (
            NO_EXPLICIT_NATIONAL_ANCHOR if admisible else "ANCLAJE_NACIONAL_PRESENTE"),
        "capa_jurisdiccional": "NO_DETERMINADO",
        "estado_epistemico": TOPIC_CANDIDATE,
        "_no_demostrado": (
            "El filtro NO demuestra CAPA_A_TRANSVERSAL. La capa solo puede "
            "establecerse con evidencia oficial por jurisdiccion, y ni siquiera "
            "entonces se convierte en universalidad panhispanica."),
        "anclajes_nacionales": motivos,
        "errores_de_forma": errores,
        # Los tres campos siguientes son invariantes, no resultados: un tema
        # nunca los cambia. Se emiten para que ningún consumidor pueda leer un
        # dictamen positivo como si fuera una autorización.
        "estado_juridico": "REQUIERE_INVESTIGACION",
        "gate_arte": "CERRADO",
        "publicacion": "NOT_PUBLISHED",
        "siguiente_accion": (
            f"buscar fuente oficial propia en {MINIMO_JURISDICCIONES_COMPARADAS} jurisdicciones"
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
    suficiente = len(paises) >= MINIMO_JURISDICCIONES_COMPARADAS
    problemas = list(notas)
    if declarado == "CAPA_A_TRANSVERSAL" and not suficiente:
        problemas.insert(0, (
            f"declara CAPA_A_TRANSVERSAL pero sus fuentes solo cubren {paises!r} "
            f"({len(paises)} de {MINIMO_JURISDICCIONES_COMPARADAS} jurisdicciones "
            "comparadas mínimas) — esto es falsa universalización"))

    # Lo que la cobertura permite sostener. NUNCA una capa jurisdiccional: tres
    # jurisdicciones con fuente propia demuestran cobertura comparada EN ESAS
    # TRES, no una regla del ámbito hispanohablante. Hay más de veinte
    # ordenamientos; concederle CAPA_A a un mínimo de tres seria la misma falsa
    # universalizacion con el listón tres veces más alto.
    if suficiente:
        maximo = COBERTURA_COMPARADA_VERIFICADA
    elif len(paises) == 1:
        maximo = "CAPA_C_NACIONAL"
    else:
        maximo = "NO_DETERMINADO"

    return {
        "claim_id": claim.get("claim_id"),
        "alcance_declarado": declarado,
        "paises_cubiertos_por_fuentes": paises,
        "cobertura_comparada_suficiente": suficiente,
        "cobertura_comparada_de": list(paises),
        "es_universalidad_panhispanica": False,
        "_nota_alcance": (
            f"Evidencia comparada en {len(paises)} jurisdiccion(es): {paises}. "
            "No se extrapola al resto del ambito hispanohablante."),
        "sostenible_por_la_evidencia": maximo,
        "_capa_no_se_concede_aqui": (
            "Ni siquiera con cobertura comparada verificada este modulo emite "
            "CAPA_A_TRANSVERSAL. La capa la declara el claim packet y la valida "
            "la skill juridica; aqui solo se dice hasta donde llega la evidencia."),
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
    print(f"candidatos evaluados          : {len(dictamenes)}")
    print(f"sin anclaje nacional explicito : {len(ok)}")
    print(f"rechazados                     : {len(dictamenes) - len(ok)}")
    print("\nNO_EXPLICIT_NATIONAL_ANCHOR no es CAPA_A_TRANSVERSAL: solo dice que el")
    print("texto del candidato no nombra pais, ley, moneda ni plazo. La capa")
    print("jurisdiccional sigue en NO_DETERMINADO para los 24.")
    print("Estado epistemico: TOPIC_CANDIDATE. Gate CERRADO. NOT_PUBLISHED.")
    for d in dictamenes:
        if d["admisible_como_tema"]:
            continue
        print(f"\n  {d['id']} — RECHAZADO")
        for m in d["anclajes_nacionales"] + d["errores_de_forma"]:
            print(f"    - {m}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
