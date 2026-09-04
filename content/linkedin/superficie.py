"""Superficie profesional de LinkedIn: alimenta el motor visual, no lo duplica.

Lo que este modulo NO es. No es un motor de imagen. El motor es `visual/` y ya
funciona: familias, compilador, composicion, gates y recibos. Aqui solo se
construye el `VisualBrief` que ese motor consume, en formato SOCIAL_4_5, que la
politica visual ya declaraba. Cero proveedores nuevos, cero canon nuevo.

Por que la superficie profesional necesita algo propio. Porque responde otra
pregunta:

    PUBLICO        "que me pasa y que significa"
    PROFESIONAL    "como se estructura, se documenta y se decide"

Un mismo concepto puede vivir en las dos sin repetirse, siempre que cambie la
pregunta. Cambiar solo el vocabulario es repetir con corbata.

De donde salen los temas. De Drive, del «Artefacto 05 — LinkedIn Strategy» y sus
dos ampliaciones. NO se inventan aqui: siete pilares, cuarenta y cuatro temas,
transcritos. Su clasificacion de origen se conserva —el cuerpo de la estrategia
es PROPUESTA/HIPOTESIS; la ampliacion de experiencia es HECHO DOCUMENTADO— y esa
diferencia no se colapsa.

Confidencialidad. Es el riesgo propio de esta superficie y no lo cubre ningun
otro control del repositorio: el septimo pilar nace de practica real. La regla de
Drive es explicita —sin nombres de empresas, clientes, escrituras, notarias,
fechas operativas, montos, clausulas textuales ni datos bancarios— y aqui se
comprueba por PATRON, no por lista literal. La distincion es deliberada: una
lista de proyectos reales obligaria a escribir esos nombres en un repositorio
publico, que es exactamente lo que hay que evitar.

Sin red. Determinista. No abre gates, no aprueba y no autoriza publicacion.
"""

import json
import re
import sys
import unicodedata
from pathlib import Path

AQUI = Path(__file__).resolve().parent
REPO = AQUI.parent.parent
sys.path.insert(0, str(REPO / "visual"))

PILARES_PATH = AQUI / "pilares-v1.json"

# El formato de LinkedIn en el feed. Ya estaba declarado en la politica visual
# (visual/policy/legalmente-visual-policy-v1.json): no se añade ninguno.
FORMATO_LINKEDIN = "SOCIAL_4_5"

# Clasificacion obligatoria de cada afirmacion. Es lo que impide que la
# experiencia profesional se publique como si fuera norma.
FACT = "FACT"                            # consta en una fuente verificable
DERIVED_KNOWLEDGE = "DERIVED_KNOWLEDGE"  # se sigue de un FACT por razonamiento explicito
INFERENCE = "INFERENCE"                  # el autor lo cree probable; no es derecho
EXTERNAL_RESEARCH = "EXTERNAL_RESEARCH"  # lo dice un tercero identificable
EDITORIAL = "EDITORIAL"                  # encuadre; nunca se presenta como regla
CATEGORIAS = (FACT, DERIVED_KNOWLEDGE, INFERENCE, EXTERNAL_RESEARCH, EDITORIAL)

# Solo estas dos pueden sostener una afirmacion sobre el derecho, y solo con
# fuente. Las otras tres son legitimas y utiles, pero no son derecho.
CATEGORIAS_CON_AUTORIDAD = (FACT, DERIVED_KNOWLEDGE)

# --- Deteccion de material identificable, por patron ------------------------
# Sensible a proposito: un falso positivo cuesta una revision; un falso negativo
# cuesta un cliente.
RE_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
RE_TELEFONO = re.compile(r"(?<!\d)(?:\+\d{1,3}[\s-]?)?(?:\d[\s-]?){9,14}\d(?!\d)")
RE_IMPORTE = re.compile(
    r"(?:[$€£]\s?\d[\d.,]*)|(?:\d[\d.,]*\s?(?:mdp|millones|mil\s+pesos|euros|dolares|USD|MXN|EUR))",
    re.IGNORECASE)
# Lo que vuelve identificable a un expediente, una escritura o una notaria es su
# NUMERO, no la palabra. "escritura publica" es vocabulario juridico corriente;
# "escritura 44.812" señala un documento concreto. Por eso se exige un digito en
# el identificador, con lookahead.
#
# Tres falsos positivos que esta version corrige y la anterior producia:
#   - 'exp\.?' con el punto opcional cazaba "explica", "experiencia", "exponer".
#     Ahora el punto es obligatorio: solo la abreviatura real.
#   - sin \b tras la palabra clave, "escritura" cazaba dentro de "escriturarse".
#   - exigir tres caracteres dejaba escapar "notaria 15".
RE_EXPEDIENTE = re.compile(
    # La abreviatura 'exp.' va aparte: el punto ya la delimita, y exigirle \b
    # despues la dejaba escapar porque entre '.' y ' ' no hay limite de palabra.
    r"\b(?:(?:expediente|escritura|folio|partida|protocolo|notar[ií]a)\b|exp\.)"
    r"\s*[:#nN°º]*\s*(?=[\w./-]*\d)[\w][\w./-]*", re.IGNORECASE)
RE_CLAUSULA_TEXTUAL = re.compile(r"[«\"“][^»\"”]{80,}[»\"”]")
# Nombre propio compuesto: dos palabras capitalizadas seguidas. Es el patron que
# atrapa un nombre de proyecto, de despacho o de persona sin tener que nombrarlos.
RE_NOMBRE_PROPIO = re.compile(
    r"(?<![.!?]\s)(?<!^)\b[A-ZÁÉÍÓÚÑ][a-záéíóúñ]{2,}\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]{2,}\b",
    re.MULTILINE)
# Vocabulario institucional que no es un nombre propio y ahogaria el texto.
EXCEPCIONES_NOMBRE = (
    "legal mente", "legalmente", "derecho civil", "derecho laboral",
    "gobierno corporativo", "due diligence", "legal operations",
    "buenas practicas", "estados financieros", "consejo de administracion",
    "registro publico", "proyecto ejecutivo", "predio matriz",
    "direccion legal", "propiedad intelectual", "uso de suelo",
)


def _norm(s):
    s = unicodedata.normalize("NFD", (s or "").casefold())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


_EXCEPCIONES_NORM = frozenset(_norm(e) for e in EXCEPCIONES_NOMBRE)


def detectar_material_identificable(texto):
    """Todo lo que podria identificar a una persona, empresa u operacion real.

    Vacio NO significa "es publicable": significa que estos controles concretos
    no encontraron nada. La revision humana de confidencialidad sigue siendo
    obligatoria, y asi lo declara cada pieza.
    """
    texto = texto or ""
    motivos = []
    if RE_EMAIL.search(texto):
        motivos.append("contiene una direccion de correo")
    if RE_TELEFONO.search(texto):
        motivos.append("contiene algo con forma de telefono")
    for regex, etiqueta in ((RE_IMPORTE, "un importe"),
                            (RE_EXPEDIENTE, "un expediente, escritura o notaria")):
        m = regex.search(texto)
        if m:
            motivos.append(f"contiene {etiqueta}: {m.group(0)!r}")
    if RE_CLAUSULA_TEXTUAL.search(texto):
        motivos.append("reproduce una clausula textual larga entre comillas")
    for m in RE_NOMBRE_PROPIO.finditer(texto):
        if _norm(m.group(0)) not in _EXCEPCIONES_NORM:
            motivos.append(f"posible nombre propio (proyecto, despacho o persona): {m.group(0)!r}")
            break
    return motivos


# ---------------------------------------------------------------------------
# Pilares y temas
# ---------------------------------------------------------------------------

def cargar_pilares(path=None):
    p = Path(path) if path else PILARES_PATH
    return json.loads(p.read_text(encoding="utf-8"))


def pilar(pilar_id, datos=None):
    d = datos if datos is not None else cargar_pilares()
    for p in d["pilares"]:
        if p["id"] == pilar_id:
            return p
    return None


def temas(datos=None):
    """Todos los temas del banco, con su pilar. Un tema no es un claim."""
    d = datos if datos is not None else cargar_pilares()
    return [{"pilar_id": p["id"], "pilar": p["nombre"], "audiencia": p["audiencia"],
             "promesa": p["promesa"], "formato_editorial": p["formato_editorial"],
             "familia_visual": p["familia_visual_sugerida"], "tema": t}
            for p in d["pilares"] for t in p["temas"]]


def cta_para(tipo_de_pieza, datos=None):
    """CTA segun la politica de Drive. Por defecto, ninguno."""
    d = datos if datos is not None else cargar_pilares()
    pol = d["politica_de_cta"]
    return pol.get(tipo_de_pieza, pol["_por_defecto"])


# ---------------------------------------------------------------------------
# Afirmaciones
# ---------------------------------------------------------------------------

def evaluar_afirmacion(af):
    """Una afirmacion profesional con su categoria y lo que esa categoria exige."""
    problemas = []
    cat = af.get("categoria")
    if cat not in CATEGORIAS:
        problemas.append(f"categoria invalida: {cat!r} (una de {list(CATEGORIAS)})")
    if cat in CATEGORIAS_CON_AUTORIDAD and not af.get("fuentes"):
        problemas.append(
            f"{cat} sin fuente: solo {list(CATEGORIAS_CON_AUTORIDAD)} pueden sostener "
            "una afirmacion sobre el derecho, y solo con fuente")
    if cat == DERIVED_KNOWLEDGE and not str(af.get("razonamiento", "")).strip():
        problemas.append("DERIVED_KNOWLEDGE sin razonamiento explicito: sin el, es una "
                         "INFERENCE presentada como conocimiento")
    if cat == EXTERNAL_RESEARCH and not str(af.get("autor_identificable", "")).strip():
        problemas.append("EXTERNAL_RESEARCH sin autor identificable: una atribucion "
                         "viral no es una fuente")
    if cat in (INFERENCE, EDITORIAL) and af.get("presentada_como_regla"):
        problemas.append(f"{cat} presentada como regla juridica: es opinion, y opinion "
                         "presentada como norma es lo que no puede salir")
    problemas.extend(detectar_material_identificable(af.get("texto", "")))
    return {
        "id": af.get("id"),
        "categoria": cat,
        "apta_para_preparar": not problemas,
        "problemas": problemas,
        "puede_sostener_derecho": cat in CATEGORIAS_CON_AUTORIDAD and bool(af.get("fuentes")),
    }


# ---------------------------------------------------------------------------
# El puente al motor visual existente
# ---------------------------------------------------------------------------

def construir_brief(tema, escena, datos=None):
    """Devuelve un VisualBrief que `visual/pipeline.py` consume tal cual.

    `escena` la aporta quien dirige el arte: sujeto, entorno, camara, punto focal
    y metafora. No se inventa aqui, igual que no se inventa en la superficie
    publica: una escena generada por plantilla produce piezas intercambiables.

    El brief NO trae `negative_space`: lo deriva el pipeline del texto real que se
    compondra despues. Escribirlo aqui a mano lo pisaria.
    """
    from brief import VisualBrief  # noqa: PLC0415 - el motor vive en visual/
    from families import VisualFamilyRegistry  # noqa: PLC0415

    d = datos if datos is not None else cargar_pilares()
    fams = VisualFamilyRegistry.load()
    familia = tema["familia_visual"]
    if familia not in fams.names():
        raise ValueError(
            f"familia visual {familia!r} no existe en el registro del motor: "
            f"{fams.names()}. La superficie no declara familias propias.")

    if not str(tema.get("content_id", "")).strip():
        raise ValueError(
            "el tema no trae content_id: un brief sin CONTENT_ID real no puede "
            "resolverse contra el canon, y el compilador lo rechazaria mas tarde "
            "con un mensaje mas opaco")

    faltan = [c for c in ("subject", "environment", "camera", "focal_point", "metaphor")
              if not str(escena.get(c, "")).strip()]
    if faltan:
        raise ValueError(f"la escena no esta dirigida: faltan {faltan}")

    return VisualBrief(
        content_id=tema.get("content_id", ""),
        formato=FORMATO_LINKEDIN,
        visual_family=familia,
        subject=escena["subject"],
        environment=escena["environment"],
        camera=escena["camera"],
        focal_point=escena["focal_point"],
        metaphor=escena["metaphor"],
        acento_frio_objeto=escena.get("acento_frio_objeto", "objeto de vidrio azul petroleo"),
        marca_superficie=escena.get("marca_superficie",
                                    fams.get(familia).brand_surface_preferences[0]),
    )


def evaluar_pieza(pieza, datos=None):
    """Dictamen completo de una pieza profesional. Prepara; nunca aprueba."""
    d = datos if datos is not None else cargar_pilares()
    problemas = []

    p = pilar(pieza.get("pilar_id", ""), d)
    if p is None:
        problemas.append(f"pilar desconocido: {pieza.get('pilar_id')!r}")

    if not str(pieza.get("pregunta_profesional", "")).strip():
        problemas.append("no declara su pregunta profesional: sin ella no se puede "
                         "saber si aporta algo distinto del post publico")

    # El control que da identidad propia a la superficie.
    if pieza.get("equivalente_publico") and not pieza.get("que_anade_sobre_el_publico"):
        problemas.append("declara un equivalente publico pero no que anade sobre el: "
                         "si solo cambia el vocabulario, es el mismo post con corbata")

    afirmaciones = [evaluar_afirmacion(a) for a in pieza.get("afirmaciones", [])]
    if not afirmaciones:
        problemas.append("la pieza no declara ninguna afirmacion clasificada")
    for a in afirmaciones:
        problemas.extend(f"{a['id']}: {x}" for x in a["problemas"])

    return {
        "id": pieza.get("id"),
        "pilar_id": pieza.get("pilar_id"),
        "superficie": d["superficie"],
        "formato_visual": FORMATO_LINKEDIN,
        "afirmaciones": afirmaciones,
        "afirmaciones_con_autoridad": sum(1 for a in afirmaciones if a["puede_sostener_derecho"]),
        "cta": cta_para(pieza.get("tipo_de_pieza", ""), d),
        "lista_para_revision_humana": not problemas,
        "problemas": problemas,
        # Invariantes, identicos a los de la superficie publica.
        "estado_juridico": "REQUIERE_INVESTIGACION",
        "gate_arte": "CERRADO",
        "revision_humana": "PENDIENTE",
        "revision_confidencialidad": "PENDIENTE",
        "publicacion": "NOT_PUBLISHED",
        "_nota": ("Los controles automaticos de confidencialidad reducen el riesgo; "
                  "no lo eliminan. Que no salte ninguno NO significa que la pieza sea "
                  "publicable: la revision humana de confidencialidad sigue siendo "
                  "obligatoria, y la aprobacion final es del fundador."),
    }


def main(argv=None):
    import argparse
    from collections import Counter
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--pilar", help="mostrar solo este pilar")
    args = ap.parse_args(argv)

    d = cargar_pilares()
    banco = temas(d)
    if args.pilar:
        banco = [t for t in banco if t["pilar_id"] == args.pilar]
    if args.json:
        print(json.dumps(banco, ensure_ascii=False, indent=2))
        return 0

    print(f"superficie : {d['superficie']}   formato visual: {FORMATO_LINKEDIN}")
    print(f"pilares    : {len(d['pilares'])}   temas: {len(banco)}\n")
    for p in d["pilares"]:
        n = sum(1 for t in banco if t["pilar_id"] == p["id"])
        if n:
            print(f"  {p['id']:<32} {n:>2} temas · {p['promesa']}")
    print("\nEl motor de imagen es visual/: esta superficie solo le entrega el brief.")
    print("Ningun tema abre gate ni acredita nada. Gate CERRADO, NOT_PUBLISHED.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
