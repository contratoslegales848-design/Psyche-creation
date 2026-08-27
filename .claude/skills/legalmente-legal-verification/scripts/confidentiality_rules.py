#!/usr/bin/env python3
"""Control determinista de confidencialidad para claim packets de LegalMente.

Problema que cierra
-------------------
`confidentiality_review` existía como campo y podía cerrar el gate, pero nadie
comprobaba su contenido: bastaba con declarar `required: false` /
`status: "NO_APLICA"` para que una pieza basada en un caso reconocible avanzara.
El campo se rellenaba, no se revisaba.

Cómo lo cierra
--------------
Invirtiendo la carga de la prueba. Se escanean los campos de texto del claim con
un conjunto **cerrado y determinista** de indicadores de contenido identificable.
Si alguno dispara, el claim **no puede declarar** que la revisión de
confidencialidad no aplica: `required` pasa a ser obligatoriamente `true`, y el
gate solo se abre con una revisión humana firmada y motivada.

Lo que NO es
------------
No es un clasificador, no usa IA y no decide si algo es confidencial. Decide una
cosa mucho más modesta y mucho más verificable: **cuándo un humano está obligado
a mirar**. Un indicador que dispara es una obligación de revisión, no una
acusación. Un indicador que no dispara no es un certificado de que no haya
información identificable — la lista es un suelo, nunca un techo, y la revisión
humana sigue siendo obligatoria por decisión del fundador (CLAUDE.md §5).

Semántica de estados
--------------------
Se reutilizan los cuatro estados que ya existen en el sistema, en lugar de
introducir un vocabulario paralelo:

| `confidentiality_review.status` | Semántica |
|---|---|
| `NO_APLICA`  | no aplica (solo admisible si NINGÚN indicador dispara) |
| `PENDIENTE`  | requiere revisión — bloquea el gate |
| `APROBADO`   | revisado por un humano identificado — habilita el gate |
| `RECHAZADO`  | bloqueado — cierra el gate de forma definitiva |

Privacidad del propio control
-----------------------------
Los informes **nunca** reproducen el fragmento que disparó el indicador: un
mensaje de error que citara texto confidencial sería el mismo problema en otra
capa. Se reporta qué indicador, en qué campo y en qué posición.
"""
import re
import unicodedata

# Longitud mínima de las observaciones de una revisión de confidencialidad
# efectiva. No mide calidad; descarta el campo rellenado por inercia.
MIN_OBSERVACIONES_CHARS = 40

# Fórmulas vacías que no constituyen constancia de revisión.
OBSERVACIONES_VACIAS = {
    "ok", "okay", "revisado", "revisada", "sin problema", "sin problemas",
    "ninguno", "ninguna", "n/a", "na", "no aplica", "nada", "todo bien",
    "sin observaciones", "correcto", "aprobado", "listo", "-", "--",
}

# Campos del claim que pueden acabar, directa o indirectamente, en una pieza
# publicable. Deliberadamente NO se escanean los metadatos de fuentes
# (`titulo`, `organismo_autor`): ahí los nombres propios institucionales son
# correctos y esperados, y escanearlos solo produciría ruido.
SCANNED_FIELDS = (
    "texto_exacto",
    "nucleo_transversal",
    "variaciones_materiales",
    "diferencias_buscadas",
    "contraejemplos_encontrados",
    "justificacion_suficiencia_comparada",
    "redaccion_prohibida",
    "notas",
)

# Campos anidados: (ruta legible, [claves])
SCANNED_NESTED_FIELDS = (
    ("reformulacion_propuesta.texto", ("reformulacion_propuesta", "texto")),
)


def _normalize(text):
    """Minúsculas y sin acentos, para que los indicadores no dependan de tildes."""
    lowered = text.lower()
    decomposed = unicodedata.normalize("NFD", lowered)
    return "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")


# ---------------------------------------------------------------------------
# Indicadores
# ---------------------------------------------------------------------------
# Cada entrada: (id, patrón sobre texto normalizado, qué riesgo señala).
# Se aplican sobre texto SIN acentos y en minúsculas.

INDICATORS = (
    (
        "CASO_PROPIO",
        r"\b(mi|nuestro|nuestra)\s+(cliente|clienta|despacho|bufete|estudio\s+juridico)\b",
        "referencia a un cliente o despacho propio",
    ),
    (
        "EXPERIENCIA_PRIMERA_PERSONA",
        r"\b(asesore|represente|patrocine|litigue|defendi|atendi|redacte|negocie)\s+"
        r"(a|al|el|la|los|las|un|una|unos|unas)\b",
        "actuación profesional propia narrada en primera persona",
    ),
    (
        "CASO_CONCRETO",
        r"\b(en\s+un\s+caso\s+que|un\s+caso\s+que\s+llev|un\s+asunto\s+que|"
        r"recuerdo\s+un\s+caso|me\s+toco\s+un\s+caso|una\s+vez\s+un\s+cliente|"
        r"hace\s+unos\s+anos\s+un)\b",
        "narración de un caso concreto y potencialmente reconocible",
    ),
    (
        "EXPEDIENTE",
        r"\b(expediente|toca|juicio|carpeta\s+de\s+investigacion|causa)\s*"
        r"(num(ero)?\.?|n\.?º?|#)?\s*[\d/-]{2,}",
        "identificador de expediente, causa o carpeta",
    ),
    (
        "IDENTIFICADOR_PERSONAL",
        r"\b(rfc|curp|dni|nif|nie|cif|cuit|cuil|rut|nit|ine|"
        r"numero\s+de\s+seguridad\s+social|numero\s+de\s+pasaporte|pasaporte\s+n)\b",
        "identificador fiscal o personal",
    ),
    (
        "SOCIEDAD_IDENTIFICABLE",
        r"(\bs\.\s?a\.\s+de\s+c\.\s?v\.|\bs\.\s+de\s+r\.\s?l\.|\bs\.\s?a\.\s?s\.|"
        r"\bs\.\s?l\.\s|\bs\.\s?a\.\s|\bc\.\s?a\.\s)",
        "razón social identificable",
    ),
    (
        "MONTO_CONCRETO",
        r"(\$|€|£)\s?\d|\b\d[\d.,]{2,}\s*(pesos|euros|dolares|soles|bolivares|"
        r"quetzales|colones|mxn|usd|eur|cop|ars|clp|pen|uyu)\b",
        "importe concreto de una operación",
    ),
    (
        "REGISTRO_O_ESCRITURA",
        r"\b(escritura\s+publica\s+(num|n\.?º?|numero)|folio\s+real|folio\s+mercantil|"
        r"partida\s+registral|inscripcion\s+(num|numero)|protocolo\s+(num|numero))\b",
        "referencia registral o notarial identificable",
    ),
    (
        "CONTRATO_IDENTIFICABLE",
        r"\bel\s+contrato\s+(entre|firmado\s+por|celebrado\s+entre|suscrito\s+por)\b",
        "contrato concreto entre partes identificables",
    ),
    (
        "DATOS_DE_CONTACTO",
        r"[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}|\+\d{2,3}[\s.-]?\d{6,}",
        "dato de contacto (correo o teléfono)",
    ),
    (
        "TRATAMIENTO_Y_NOMBRE",
        r"\b(sr\.|sra\.|srta\.|don|dona|lic\.|licenciado|licenciada|ing\.|dr\.|dra\.|"
        r"mtro\.|mtra\.)\s+[a-z]{3,}",
        "tratamiento seguido de nombre propio",
    ),
    (
        "FECHA_DE_OPERACION",
        r"\b(firmado|celebrado|suscrito|otorgado|pactado)\s+el\s+\d",
        "fecha concreta de una operación",
    ),
)

COMPILED_INDICATORS = tuple(
    (ind_id, re.compile(pattern), descripcion)
    for ind_id, pattern, descripcion in INDICATORS
)


def scan_text(text):
    """Devuelve [(indicador_id, descripcion, posicion)] sin reproducir el texto."""
    if not isinstance(text, str) or not text.strip():
        return []
    normalized = _normalize(text)
    hits = []
    for ind_id, pattern, descripcion in COMPILED_INDICATORS:
        match = pattern.search(normalized)
        if match:
            hits.append((ind_id, descripcion, match.start()))
    return hits


def scan_claim(claim):
    """Escanea los campos publicables de un claim.

    Devuelve [(campo, indicador_id, descripcion, posicion)]. Nunca incluye el
    fragmento coincidente: reproducirlo trasladaría el problema al informe.
    """
    if not isinstance(claim, dict):
        return []
    findings = []
    for field in SCANNED_FIELDS:
        for ind_id, descripcion, pos in scan_text(claim.get(field)):
            findings.append((field, ind_id, descripcion, pos))
    for label, path in SCANNED_NESTED_FIELDS:
        value = claim
        for key in path:
            value = value.get(key) if isinstance(value, dict) else None
        for ind_id, descripcion, pos in scan_text(value):
            findings.append((label, ind_id, descripcion, pos))
    return findings


def _observaciones_insuficientes(observaciones):
    if not isinstance(observaciones, str):
        return True
    limpio = observaciones.strip()
    if _normalize(limpio).rstrip(".") in OBSERVACIONES_VACIAS:
        return True
    return len(limpio) < MIN_OBSERVACIONES_CHARS


def confidentiality_errors(claim, path):
    """Reglas fail-closed sobre `confidentiality_review`.

    Devuelve (errores, advertencias). Los errores invalidan la pieza; las
    advertencias informan de qué disparó, para que la revisión humana sepa
    dónde mirar.
    """
    errors, warnings = [], []
    review = claim.get("confidentiality_review")
    if not isinstance(review, dict):
        # La forma del objeto ya la valida el validador canónico; aquí no se
        # duplica ese error.
        return errors, warnings

    findings = scan_claim(claim)
    required = review.get("required")
    status = review.get("status")

    if findings:
        indicadores = sorted({f"{ind_id}@{campo}" for campo, ind_id, _d, _p in findings})
        warnings.append(
            f"{path}.confidentiality_review: indicadores de contenido identificable "
            f"detectados en {len(findings)} punto(s): {indicadores}. "
            "Un indicador señala una OBLIGACIÓN DE REVISIÓN humana, no una acusación."
        )
        if required is not True:
            errors.append(
                f"{path}.confidentiality_review: el texto del claim dispara indicadores de "
                f"contenido identificable ({indicadores}), por lo que 'required' debe ser true. "
                "No se puede declarar que la revisión de confidencialidad no aplica sobre un "
                "texto que contiene señales de caso, cliente, expediente, identificador, "
                "importe o dato de contacto."
            )

    if required is True and status == "APROBADO":
        if not isinstance(review.get("revisor"), str) or not review["revisor"].strip():
            errors.append(
                f"{path}.confidentiality_review: una revisión de confidencialidad APROBADA exige "
                "'revisor' identificado — la responsabilidad es nominal."
            )
        if _observaciones_insuficientes(review.get("observaciones")):
            errors.append(
                f"{path}.confidentiality_review: una revisión de confidencialidad APROBADA exige "
                f"'observaciones' que dejen constancia de QUÉ se revisó (mínimo "
                f"{MIN_OBSERVACIONES_CHARS} caracteres, y no una fórmula vacía). "
                "Un campo rellenado por inercia no es una revisión."
            )

    if status == "RECHAZADO":
        if not isinstance(review.get("revisor"), str) or not review["revisor"].strip():
            errors.append(
                f"{path}.confidentiality_review: un bloqueo por confidencialidad exige 'revisor' "
                "identificado — bloquear también es una decisión con responsable."
            )
        if _observaciones_insuficientes(review.get("observaciones")):
            errors.append(
                f"{path}.confidentiality_review: un bloqueo por confidencialidad exige "
                f"'observaciones' que expliquen el motivo (mínimo {MIN_OBSERVACIONES_CHARS} "
                "caracteres, y no una fórmula vacía)."
            )

    return errors, warnings
