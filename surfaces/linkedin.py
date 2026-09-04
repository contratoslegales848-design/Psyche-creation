"""Superficie profesional (LinkedIn): identidad propia, no el post publico con corbata.

La regla que ordena todo este modulo: la superficie profesional NO es el mismo
contenido publico explicado con mas tecnicismos. Si lo fuera, no haria falta —
bastaria con enlazar el post general. Lo que la justifica es que responde otra
pregunta.

    PUBLICO        "que me pasa y que significa"
    PROFESIONAL    "como se estructura, se documenta y se decide"

Un mismo concepto puede vivir en las dos superficies sin repetirse, siempre que
cambie la pregunta. Cambiar solo el vocabulario es repetir.

Clasificacion obligatoria de cada afirmacion. Es la que impide que la
experiencia profesional se convierta en norma:

    FACT                lo que consta en una fuente verificable
    DERIVED_KNOWLEDGE   lo que se sigue de un FACT por razonamiento explicito
    INFERENCE           lo que el autor cree probable; no es derecho
    EXTERNAL_RESEARCH   lo que dice un tercero identificable
    EDITORIAL           opinion o encuadre; nunca se presenta como regla

Confidencialidad. Ninguna pieza profesional puede contener clientes, marcas,
nombres, operaciones identificables, montos, escrituras, datos bancarios,
estrategias confidenciales ni clausulas textuales. La experiencia se usa como
PATRON ANONIMIZADO o no se usa.

Sin red. Determinista. No aprueba nada.
"""

import re
import unicodedata

# Las cinco categorias, cerradas.
FACT = "FACT"
DERIVED_KNOWLEDGE = "DERIVED_KNOWLEDGE"
INFERENCE = "INFERENCE"
EXTERNAL_RESEARCH = "EXTERNAL_RESEARCH"
EDITORIAL = "EDITORIAL"
CATEGORIAS = (FACT, DERIVED_KNOWLEDGE, INFERENCE, EXTERNAL_RESEARCH, EDITORIAL)

# Solo estas dos pueden presentarse como afirmacion sobre el derecho, y solo con
# fuente. Las otras tres son legitimas y utiles, pero no son derecho.
CATEGORIAS_CON_AUTORIDAD = (FACT, DERIVED_KNOWLEDGE)

# Dominios de la superficie profesional. Es donde vive la identidad propia.
DOMINIOS = (
    "gobierno_corporativo", "representacion", "delegacion", "facultades",
    "contratos", "negociacion", "due_diligence", "inmobiliario", "permisos",
    "urbanizacion", "financiamiento", "cobranza", "fiscalidad", "operaciones",
    "talento", "evidencia", "trazabilidad", "gestion_de_riesgos",
    "coordinacion_interdisciplinaria", "legal_operations",
)

# Senales de material identificable. La deteccion es deliberadamente sensible:
# un falso positivo cuesta una revision; un falso negativo cuesta un cliente.
RE_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
RE_TELEFONO = re.compile(r"(?<!\d)(?:\+\d{1,3}[\s-]?)?(?:\d[\s-]?){9,14}\d(?!\d)")
RE_IMPORTE = re.compile(
    r"(?:[$€£]\s?\d[\d.,]*)|(?:\d[\d.,]*\s?(?:mdp|millones|mil\s+pesos|euros|dolares|USD|MXN|EUR))",
    re.IGNORECASE)
RE_EXPEDIENTE = re.compile(
    # El separador puede ser punto, guion o barra: "escritura 44.812",
    # "expediente 214/2024-B", "folio 1.234". Exigir solo \w dejaba pasar el
    # formato mas comun, que es justamente el que lleva punto.
    r"\b(?:expediente|exp\.?|escritura|folio|partida|protocolo)\s*[:#nN°º]*\s*[\w][\w./-]{2,}",
    re.IGNORECASE)
RE_CLAUSULA_TEXTUAL = re.compile(r"[«\"“][^»\"”]{80,}[»\"”]")

# Nombre propio: dos o mas palabras capitalizadas seguidas. Se excluyen los
# arranques de frase y el vocabulario institucional para no ahogar el texto.
RE_NOMBRE_PROPIO = re.compile(r"(?<![.!?]\s)(?<!^)\b[A-ZÁÉÍÓÚÑ][a-záéíóúñ]{2,}\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]{2,}\b",
                              re.MULTILINE)
EXCEPCIONES_NOMBRE = {
    "legal mente", "legalmente", "derecho civil", "derecho laboral",
    "gobierno corporativo", "due diligence", "legal operations",
    "buenas practicas", "estados financieros", "consejo de administracion",
}


def _norm(s):
    s = unicodedata.normalize("NFD", (s or "").casefold())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def detectar_material_identificable(texto):
    """Todo lo que podria identificar a una persona, empresa u operacion real.

    Devuelve motivos legibles. Vacio NO significa "es publicable": significa que
    estos controles concretos no encontraron nada. La revision humana de
    confidencialidad sigue siendo obligatoria.
    """
    motivos = []
    if RE_EMAIL.search(texto or ""):
        motivos.append("contiene una direccion de correo")
    if RE_TELEFONO.search(texto or ""):
        motivos.append("contiene algo con forma de telefono")
    m = RE_IMPORTE.search(texto or "")
    if m:
        motivos.append(f"contiene un importe: {m.group(0)!r}")
    m = RE_EXPEDIENTE.search(texto or "")
    if m:
        motivos.append(f"referencia un expediente o escritura: {m.group(0)!r}")
    if RE_CLAUSULA_TEXTUAL.search(texto or ""):
        motivos.append("reproduce una clausula textual larga entre comillas")
    for m in RE_NOMBRE_PROPIO.finditer(texto or ""):
        if _norm(m.group(0)) not in {_norm(e) for e in EXCEPCIONES_NOMBRE}:
            motivos.append(f"posible nombre propio: {m.group(0)!r}")
            break
    return motivos


def evaluar_afirmacion(af):
    """Una afirmacion profesional, con su categoria y lo que esa categoria exige."""
    problemas = []
    cat = af.get("categoria")
    texto = af.get("texto", "")

    if cat not in CATEGORIAS:
        problemas.append(f"categoria invalida: {cat!r} (una de {list(CATEGORIAS)})")

    if cat in CATEGORIAS_CON_AUTORIDAD and not af.get("fuentes"):
        problemas.append(
            f"{cat} sin fuente: solo {list(CATEGORIAS_CON_AUTORIDAD)} pueden "
            "sostener una afirmacion sobre el derecho, y solo con fuente")

    if cat == DERIVED_KNOWLEDGE and not str(af.get("razonamiento", "")).strip():
        problemas.append(
            "DERIVED_KNOWLEDGE sin razonamiento explicito: sin el, es una "
            "INFERENCE presentada como conocimiento")

    if cat == EXTERNAL_RESEARCH and not str(af.get("autor_identificable", "")).strip():
        problemas.append("EXTERNAL_RESEARCH sin autor identificable")

    if cat in (INFERENCE, EDITORIAL) and af.get("presentada_como_regla"):
        problemas.append(
            f"{cat} presentada como regla juridica: es opinion, y opinion "
            "presentada como norma es exactamente lo que no puede salir")

    problemas.extend(detectar_material_identificable(texto))

    return {
        "id": af.get("id"),
        "categoria": cat,
        "apta_para_preparar": not problemas,
        "problemas": problemas,
        "puede_sostener_derecho": cat in CATEGORIAS_CON_AUTORIDAD and bool(af.get("fuentes")),
    }


def evaluar_pieza(pieza):
    """Una pieza profesional entera. Nunca aprueba: prepara."""
    problemas = []

    if pieza.get("dominio") not in DOMINIOS:
        problemas.append(f"dominio fuera del vocabulario profesional: {pieza.get('dominio')!r}")

    pregunta = str(pieza.get("pregunta_profesional", "")).strip()
    if not pregunta:
        problemas.append(
            "no declara su pregunta profesional: sin ella no se puede saber si "
            "aporta algo distinto del post publico")

    # El control que da identidad propia a la superficie.
    if pieza.get("equivalente_publico") and not pieza.get("que_anade_sobre_el_publico"):
        problemas.append(
            "declara un equivalente publico pero no que anade sobre el: si solo "
            "cambia el vocabulario, es el mismo post con corbata")

    afirmaciones = [evaluar_afirmacion(a) for a in pieza.get("afirmaciones", [])]
    if not afirmaciones:
        problemas.append("la pieza no declara ninguna afirmacion clasificada")
    for a in afirmaciones:
        problemas.extend(f"{a['id']}: {p}" for p in a["problemas"])

    con_autoridad = [a for a in afirmaciones if a["puede_sostener_derecho"]]

    return {
        "id": pieza.get("id"),
        "dominio": pieza.get("dominio"),
        "afirmaciones": afirmaciones,
        "afirmaciones_con_autoridad": len(con_autoridad),
        "lista_para_revision_humana": not problemas,
        "problemas": problemas,
        # Invariantes. Igual que en el resto del sistema.
        "estado_juridico": "REQUIERE_INVESTIGACION",
        "gate_arte": "CERRADO",
        "revision_humana": "PENDIENTE",
        "revision_confidencialidad": "PENDIENTE",
        "publicacion": "NOT_PUBLISHED",
        "_nota": ("Los controles automaticos de confidencialidad reducen el "
                  "riesgo; no lo eliminan. Que no salte ninguno NO significa que "
                  "la pieza sea publicable: la revision humana de "
                  "confidencialidad sigue siendo obligatoria."),
    }
