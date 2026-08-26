#!/usr/bin/env python3
"""Valida la ESTRUCTURA de una PIEZA de verificación jurídica de LegalMente
(esquema v4: pieza -> claims -> fuentes con verificación de origen/contenido/
vigencia y jurisdicción propia, cada fuente oficial referenciando un registro
oficial único (hostname<->organismo<->tipo_fuente<->jurisdiccion, Fase 1D.1);
revisión humana ligada por hash al contenido exacto que aprobó; revisiones de
plataforma/confidencialidad como objetos).

Límite honesto: este script SOLO valida JSON. No autentica personas. Que un
campo 'revisor' contenga un nombre no prueba que esa persona escribió ese
JSON — un modelo o cualquier proceso puede rellenarlo. Por eso el gate
calculado aquí ('ABIERTO') es una condición NECESARIA pero NO SUFICIENTE
para producción real: reduce el riesgo de que el propio modelo se autoapruebe
sin dejar rastro verificable (liga la aprobación a un hash del contenido
exacto), pero la garantía de que un humano real aprobó de verdad requiere un
mecanismo externo de autenticación que esta skill NO implementa todavía.

No decide si una afirmación jurídica es correcta, ni si un dominio "oficial"
realmente pertenece al organismo que dice — eso lo confirma el humano que
llena 'verificacion_fuente'. Lo que este script sí impone, de forma
fail-closed: ningún campo autoafirmado por sí solo basta para abrir el gate;
hace falta que el hostname de la URL coincida, byte a byte por límites de
dominio (nunca por subcadena), con una lista cerrada de dominios oficiales
conocidos, Y que el propio JSON declare que el texto exacto fue consultado
y que su vigencia fue comprobada.

Solo biblioteca estándar de Python (json, sys, re, hashlib, pathlib,
urllib.parse, datetime). Sin dependencias externas.

Uso:
    python3 validate-claim-packet.py archivo1.json [archivo2.json ...]

Código de salida:
    0 si TODAS las piezas son estructuralmente válidas.
    1 si al menos una tiene errores estructurales, JSON mal formado, o un
      gate/estado declarado que no corresponde a lo que las reglas permiten.
"""

import hashlib
import json
import re
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

SCHEMA_VERSION = "4.0"

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

VALID_ALCANCE = {
    "CAPA_A_TRANSVERSAL",
    "CAPA_B_VARIABLE",
    "CAPA_C_NACIONAL",
    "NO_DETERMINADO",
    "NO_APLICA",
}

VALID_ESTADO = {
    "APTO_PARA_NARRATIVA",
    "APTO_CON_MATICES",
    "REQUIERE_INVESTIGACION",
    "BLOQUEADO",
    "PENDIENTE_APROBACION_HUMANA",
}

ESTADO_LADDER = ["REQUIERE_INVESTIGACION", "APTO_CON_MATICES", "APTO_PARA_NARRATIVA"]

VALID_UBICACION = {
    "titulo", "hook", "texto_imagen", "caption", "lista", "cta",
    "prompt_visual", "descripcion_tema",
}

VALID_TIPO = {
    "regla", "definicion", "cita", "atribucion", "dato",
    "procedimiento", "consecuencia", "consejo",
}

VALID_CONFIANZA = {"alta", "media", "baja"}
VALID_RIESGO = {"ninguno", "bajo", "medio", "alto"}

VALID_TIPO_FUENTE = {
    "NORMA_OFICIAL", "JURISPRUDENCIA_OFICIAL", "AUTORIDAD_PUBLICA_OFICIAL",
    "ACADEMICA_IDENTIFICABLE", "SECUNDARIA_ESPECIALIZADA", "DRIVE_INTERNO",
}
TIPOS_FUENTE_OFICIAL = {"NORMA_OFICIAL", "JURISPRUDENCIA_OFICIAL", "AUTORIDAD_PUBLICA_OFICIAL"}
TIPOS_FUENTE_SECUNDARIA_ACADEMICA = {"ACADEMICA_IDENTIFICABLE", "SECUNDARIA_ESPECIALIZADA"}

VALID_REVISION_ESTADO = {"PENDIENTE", "APROBADO", "RECHAZADO"}
VALID_REVIEW_STATUS = {"NO_APLICA", "PENDIENTE", "APROBADO", "RECHAZADO"}
VALID_GATE = {"CERRADO", "ABIERTO"}

ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

# REGISTRO ÚNICO de organismos oficiales conocidos (Fase 1D.1). Ya no hay dos
# listas manuales paralelas (OFFICIAL_HOSTNAMES / OFFICIAL_HOSTNAME_JURISDICTIONS
# de la Fase 1D) — toda validación de hostname, organismo, tipo de fuente
# permitido y jurisdicción/ámbito se deriva de un único archivo cerrado:
# references/official-source-registry.json. Un hostname/organismo legítimo
# que falte ahí falla cerrado (no alcanza Nivel 1) hasta que un humano añada
# la entrada explícitamente.
REGISTRY_PATH = Path(__file__).resolve().parent.parent / "references" / "official-source-registry.json"


def load_official_source_registry(path=REGISTRY_PATH):
    """Carga el registro oficial. Fail-closed: un archivo ausente, ilegible o
    con forma inesperada produce un registro VACÍO (ninguna fuente oficial
    puede alcanzar Nivel 1), nunca una excepción que tumbe el validador."""
    try:
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
    except (OSError, json.JSONDecodeError):
        return {"registry_version": None, "sources": []}
    if not isinstance(data, dict) or not isinstance(data.get("sources"), list):
        return {"registry_version": None, "sources": []}
    return data


def _build_registry_by_id(registry):
    """Índice id -> entrada. Un id duplicado en el registro falla cerrado:
    AMBAS entradas con ese id se descartan del índice (ninguna fuente puede
    referenciarlo válidamente) — un registro corrupto nunca abre un gate."""
    by_id = {}
    duplicated_ids = set()
    for entry in registry.get("sources", []):
        if not isinstance(entry, dict):
            continue
        eid = entry.get("id")
        if not isinstance(eid, str) or not eid:
            continue
        if eid in by_id:
            duplicated_ids.add(eid)
            continue
        by_id[eid] = entry
    for dup in duplicated_ids:
        by_id.pop(dup, None)
    return by_id


REGISTRY = load_official_source_registry()
REGISTRY_BY_ID = _build_registry_by_id(REGISTRY)


def match_registry_entry_for_url(url, registry):
    """Entrada del registro cuyo hostname coincide con la URL — exacto o por
    límite real de subdominio, nunca por subcadena. Cuando varias entradas
    coinciden (p. ej. 'dof.gob.mx' y la entrada genérica 'gob.mx'), gana la
    MÁS ESPECÍFICA: la de mayor longitud de hostname declarado."""
    host = extract_hostname(url)
    if not host:
        return None
    best = None
    best_len = -1
    for entry in registry.get("sources", []):
        if not isinstance(entry, dict):
            continue
        for allowed_host in entry.get("hostnames", []) or []:
            if not isinstance(allowed_host, str) or not allowed_host:
                continue
            if host == allowed_host or host.endswith("." + allowed_host):
                if len(allowed_host) > best_len:
                    best = entry
                    best_len = len(allowed_host)
    return best


def normalize_org(name):
    return " ".join((name or "").strip().casefold().split())


def evaluate_fuente_registry(fuente):
    """Comprobaciones de registro oficial para UNA fuente cuyo tipo_fuente
    está en TIPOS_FUENTE_OFICIAL. Devuelve (nivel1_posible, errors, warnings):

    - Sin 'registro_oficial_id' (null): si el hostname de la URL SÍ resuelve
      a un organismo conocido, omitir el campo es un ERROR (evitable — hay
      que declararlo). Si el hostname es genuinamente desconocido (o no hay
      URL), es solo ADVERTENCIA — preserva el comportamiento fail-closed ya
      existente desde la Fase 1D: un dominio desconocido nunca alcanza
      Nivel 1, pero tampoco bloquea la pieza con un error duro por sí solo.
    - Con 'registro_oficial_id' declarado: TODO tiene que ser coherente —
      que el id exista en el registro, que el hostname de la URL resuelva a
      ESA misma entrada (nunca a otra, nunca por subcadena), que
      'organismo_autor' coincida (normalizado, exacto, nunca por subcadena)
      con el nombre canónico o un alias, que 'tipo_fuente' esté en
      'tipos_fuente_permitidos' de esa entrada, y que 'jurisdicciones_cubiertas'
      sea subconjunto de las jurisdicciones/ámbito autorizados. Cualquier
      incoherencia aquí es un ERROR — declarar un registro_oficial_id falso
      es una afirmación activa, no un silencio.
    - Sin 'url' (Fase 1D.2, Paso 2): aunque todo lo anterior sea coherente,
      Nivel 1 queda fuera de alcance — no hay ningún hostname real que
      verificar, así que 'registro_oficial_id'/'organismo_autor'/los tres
      booleanos de verificación son autoafirmaciones sin evidencia de
      dominio. Genera ADVERTENCIA (no error — sigue siendo estructuralmente
      válida, capada en Nivel 2), nunca abre el gate de arte."""
    tipo_fuente = fuente.get("tipo_fuente")
    url = fuente.get("url")
    has_url = url not in (None, "")
    registro_oficial_id = fuente.get("registro_oficial_id")
    jurisdicciones_cubiertas = fuente.get("jurisdicciones_cubiertas") or []
    errors = []
    warnings = []

    if registro_oficial_id is None:
        resolved = match_registry_entry_for_url(url, REGISTRY) if has_url else None
        if resolved is not None:
            errors.append(
                f"el hostname {extract_hostname(url)!r} corresponde al organismo registrado "
                f"{resolved.get('id')!r} ({resolved.get('organismo_canonico')}), pero la fuente no declaró su "
                "'registro_oficial_id' — decláralo explícitamente en vez de dejarlo en null."
            )
        else:
            detalle = (
                f"con hostname {extract_hostname(url)!r} que NO está en el registro oficial cerrado "
                "(references/official-source-registry.json)"
                if has_url else "sin URL para resolver contra el registro"
            )
            warnings.append(
                f"fuente oficial sin 'registro_oficial_id', {detalle}. Esta fuente NO puede sostener "
                "APTO_PARA_NARRATIVA — como máximo Nivel 2 — hasta que un humano confirme y registre el "
                "organismo real, o añada la entrada al registro si es legítima."
            )
        return False, errors, warnings

    entry = REGISTRY_BY_ID.get(registro_oficial_id)
    if entry is None:
        errors.append(
            f"'registro_oficial_id' {registro_oficial_id!r} no existe en el registro oficial "
            "(references/official-source-registry.json)."
        )
        return False, errors, warnings

    if has_url:
        resolved = match_registry_entry_for_url(url, REGISTRY)
        if resolved is None or resolved.get("id") != entry.get("id"):
            otro = f"{resolved.get('id')!r} ({resolved.get('organismo_canonico')})" if resolved else "ningún organismo registrado"
            errors.append(
                f"'registro_oficial_id' ({registro_oficial_id!r}) no corresponde al hostname real de la URL "
                f"({extract_hostname(url)!r}) — el hostname resuelve a {otro}."
            )
    else:
        # Fase 1D.2, Paso 2: sin URL no hay ningún hostname real que cruzar
        # contra el registro — 'registro_oficial_id', 'organismo_autor' y los
        # tres booleanos de 'verificacion_fuente' son en este caso
        # autoafirmaciones sin evidencia verificable de dominio, así que
        # Nivel 1 queda fuera de alcance sin importar qué tan coherentes
        # parezcan entre sí. Sigue siendo estructuralmente válida (puede
        # sostener como máximo Nivel 2 / APTO_CON_MATICES) — coherente con
        # que las fuentes físicas (identificador_bibliografico) son legítimas
        # para tipos académicos/secundarios.
        warnings.append(
            f"fuente oficial ({registro_oficial_id!r}) sin 'url' — no hay hostname real que verificar contra el "
            "registro. 'registro_oficial_id', 'organismo_autor' y 'verificacion_fuente' no verificables por "
            "dominio, por más coherentes que parezcan entre sí. Esta fuente NO puede sostener APTO_PARA_NARRATIVA "
            "— como máximo Nivel 2 — ni abrir el gate de arte."
        )

    organismo_declarado = normalize_org(fuente.get("organismo_autor"))
    permitidos_org = {normalize_org(entry.get("organismo_canonico"))} | {
        normalize_org(a) for a in (entry.get("organismo_aliases") or [])
    }
    if organismo_declarado not in permitidos_org:
        errors.append(
            f"'organismo_autor' ({fuente.get('organismo_autor')!r}) no coincide, tras normalizar, con el "
            f"organismo canónico ni con ningún alias registrado para {registro_oficial_id!r} "
            f"({entry.get('organismo_canonico')!r}). La comparación es exacta tras normalización, nunca por "
            "subcadena."
        )

    if tipo_fuente not in (entry.get("tipos_fuente_permitidos") or []):
        errors.append(
            f"el organismo {registro_oficial_id!r} ({entry.get('organismo_canonico')}) no tiene permitido el "
            f"tipo de fuente {tipo_fuente!r} — solo permite {entry.get('tipos_fuente_permitidos')!r}."
        )

    declaradas = normalize_countries_list(jurisdicciones_cubiertas)
    permitidas = [normalize_country(j) for j in (entry.get("jurisdicciones") or [])]
    ajenas = [j for j in declaradas if j not in permitidas]
    if ajenas:
        errors.append(
            f"fuente oficial ({registro_oficial_id!r}) declara en 'jurisdicciones_cubiertas' país/ámbito ajeno "
            f"a lo autorizado: {ajenas!r} — solo puede respaldar {sorted(permitidas)!r}."
        )

    nivel1_posible = (not errors) and has_url
    return nivel1_posible, errors, warnings


class Tag:
    ERROR = "[ERROR ESTRUCTURAL]"
    WARNING = "[ADVERTENCIA DE FUENTE]"
    GATE_CLOSED = "[GATE CERRADO]"
    OK_PENDING_HUMAN = "[OK ESTRUCTURAL — PENDIENTE HUMANO]"
    GATE_OPEN = "[GATE ABIERTO]"


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

def is_nonempty_str(value):
    return isinstance(value, str) and value.strip() != ""


def is_str_or_nonempty_list_of_str(value):
    """string no vacío, o lista no vacía de strings no vacíos."""
    if is_nonempty_str(value):
        return True
    if isinstance(value, list) and value:
        return all(is_nonempty_str(v) for v in value)
    return False


def is_nullable_str(value):
    return value is None or isinstance(value, str)


def is_valid_iso_date(value):
    if not isinstance(value, str) or not ISO_DATE_RE.match(value):
        return False
    try:
        y, m, d = (int(part) for part in value.split("-"))
        date(y, m, d)
        return True
    except ValueError:
        return False


# Espacios (0x20) y caracteres de control (0x00-0x1f, 0x7f) — nunca válidos
# dentro de una URL bien formada; aceptarlos abre ambigüedad de parseo.
CONTROL_OR_SPACE_RE = re.compile(r"[\x00-\x20\x7f]")


def parse_official_url(value):
    """Única función CANÓNICA de validación + extracción de hostname de una
    URL (Fase 1D.2, Paso 1). Toda comprobación de URL/hostname del validador
    pasa por aquí — no hay una segunda función que parsee por su cuenta.

    Fail-closed ante cualquier ambigüedad, en vez de intentar normalizar:

    - Rechaza barra invertida en cualquier posición. Es el vector real del
      bypass reproducido en esta fase: 'https://evil.example\\@boe.es/falso'
      — un parser ingenuo (incluido `urllib.parse` de Python) dispone la
      barra invertida dentro de netloc/userinfo sin más, y termina
      calculando el host como 'boe.es'; un navegador conforme a WHATWG trata
      la barra invertida como equivalente a '/' en esquemas especiales
      (http/https) ANTES de parsear, así que la misma cadena se convierte en
      'https://evil.example/@boe.es/falso' y el host real es 'evil.example'.
      En vez de reimplementar esa normalización (con el riesgo de introducir
      un desacuerdo distinto con algún otro parser), se rechaza directamente
      cualquier URL con barra invertida: la ambigüedad entre parsers es en
      sí misma la señal de fallo.
    - Rechaza userinfo (cualquier '@' dentro del netloc) — una fuente
      oficial nunca necesita usuario/contraseña en la URL, y el propio
      userinfo es collateral del vector de arriba.
    - Rechaza espacios y caracteres de control.
    - Rechaza cualquier esquema que no sea http/https.
    - Rechaza puertos inválidos (fuera de 0-65535, o no numéricos) — vía
      'parsed.port', que ya lanza ValueError en esos casos.

    Devuelve (ok: bool, hostname: str o None, motivo: str o None).
    'hostname' viene ya en minúsculas (propiedad .hostname de urlparse)."""
    if not isinstance(value, str) or not value:
        return False, None, "no es un string no vacío"
    if "\\" in value:
        return False, None, "contiene una barra invertida — ambigua entre parsers (WHATWG la trata como separador de host en esquemas http/https)"
    if CONTROL_OR_SPACE_RE.search(value):
        return False, None, "contiene espacios o caracteres de control"
    try:
        parsed = urlparse(value)
    except ValueError:
        return False, None, "no se pudo interpretar como URL"
    if parsed.scheme not in ("http", "https"):
        return False, None, "el esquema debe ser http o https"
    if not parsed.netloc:
        return False, None, "falta el netloc (host)"
    if "@" in parsed.netloc:
        return False, None, "contiene userinfo (usuario/contraseña antes del host) — no permitido"
    try:
        hostname = parsed.hostname
        _port = parsed.port  # dispara ValueError si el puerto es inválido
    except ValueError:
        return False, None, "hostname o puerto inválido"
    if not hostname:
        return False, None, "hostname vacío"
    return True, hostname, None


def is_valid_http_url(value):
    ok, _hostname, _reason = parse_official_url(value)
    return ok


def extract_hostname(url):
    ok, hostname, _reason = parse_official_url(url)
    return hostname if ok else ""


def hostname_matches_official(url):
    """Compatibilidad: True si el hostname de la URL coincide (exacto o por
    subdominio real, nunca por subcadena) con ALGUNA entrada del registro
    único — usado solo para mensajes informativos, no para gating de
    Nivel 1 (eso lo decide evaluate_fuente_registry, que exige además
    'registro_oficial_id', organismo, tipo permitido y jurisdicción)."""
    return match_registry_entry_for_url(url, REGISTRY) is not None


def normalize_country(name):
    return " ".join(name.strip().casefold().split())


def normalize_countries_list(value):
    return [normalize_country(v) for v in value] if isinstance(value, list) else []


def as_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


# Campos EXCLUIDOS del hash de aprobación, y por qué:
#   - 'revision_humana': es el objeto que CONTIENE el hash — incluirlo sería
#     circular (el hash tendría que incluirse a sí mismo).
#   - 'gate_arte': es un veredicto CALCULADO por el validador a partir de todo
#     lo demás, no contenido que alguien pueda aprobar; recalcularlo tras
#     cambiar cualquier otro campo es correcto y no debe invalidar el hash.
# TODO lo demás del claim (texto, ubicación, tipo, alcance, jurisdicción,
# variaciones, evidencia comparada, confianza, riesgos, estado, la lista
# COMPLETA de fuentes con cada uno de sus campos — título, organismo/autor,
# url/identificador, fecha de consulta, localizador, jurisdicciones
# cubiertas, verificación completa —, platform_review, confidentiality_review,
# reformulacion_propuesta y redaccion_prohibida) SÍ forma parte del hash: es
# la opción más segura (Fase 1D, Paso 5) — cualquier cambio en cualquiera de
# esos campos después de aprobar invalida la aprobación.
HASH_EXCLUDED_FIELDS = {"revision_humana", "gate_arte"}


def canonical_claim_content(claim):
    """Todo el claim excepto HASH_EXCLUDED_FIELDS — ver arriba por qué esos
    dos, y solo esos dos, quedan fuera del hash de aprobación."""
    return {k: v for k, v in claim.items() if k not in HASH_EXCLUDED_FIELDS}


def compute_content_hash(claim):
    canonical = canonical_claim_content(claim)
    blob = json.dumps(canonical, sort_keys=True, ensure_ascii=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Validación de VERIFICACION_FUENTE
# ---------------------------------------------------------------------------

VERIFICACION_FIELDS = [
    "origen_oficial_confirmado", "texto_exacto_consultado", "vigencia_comprobada",
    "fecha_comprobacion", "metodo_o_evidencia", "observaciones",
]


def validate_verificacion_fuente(v, path):
    errors = []
    if not isinstance(v, dict):
        return [f"{path}: 'verificacion_fuente' debe ser un objeto."]
    for field in VERIFICACION_FIELDS:
        if field not in v:
            errors.append(f"{path}: falta el campo 'verificacion_fuente.{field}'.")
    if errors:
        return errors
    for bool_field in ("origen_oficial_confirmado", "texto_exacto_consultado", "vigencia_comprobada"):
        if not isinstance(v.get(bool_field), bool):
            errors.append(f"{path}.verificacion_fuente.{bool_field}: debe ser booleano.")
    if v.get("fecha_comprobacion") is not None and not is_valid_iso_date(v.get("fecha_comprobacion")):
        errors.append(f"{path}.verificacion_fuente.fecha_comprobacion: debe ser fecha ISO válida o null.")
    if not is_nullable_str(v.get("metodo_o_evidencia")):
        errors.append(f"{path}.verificacion_fuente.metodo_o_evidencia: debe ser string o null.")
    if not is_nullable_str(v.get("observaciones")):
        errors.append(f"{path}.verificacion_fuente.observaciones: debe ser string o null.")
    # Una fecha de consulta no equivale a verificación de vigencia: si se afirma
    # vigencia_comprobada=true, tiene que haber fecha y método/evidencia reales.
    if v.get("vigencia_comprobada") is True and not is_valid_iso_date(v.get("fecha_comprobacion")):
        errors.append(f"{path}.verificacion_fuente: 'vigencia_comprobada: true' requiere 'fecha_comprobacion' ISO real.")
    if v.get("texto_exacto_consultado") is True and not is_nonempty_str(v.get("metodo_o_evidencia")):
        errors.append(f"{path}.verificacion_fuente: 'texto_exacto_consultado: true' requiere 'metodo_o_evidencia' no vacío (cómo se consultó).")
    return errors


# ---------------------------------------------------------------------------
# Validación de una fuente
# ---------------------------------------------------------------------------

FUENTE_REQUIRED_FIELDS = [
    "id", "tipo_fuente", "titulo", "organismo_autor", "fecha_consulta",
    "localizador", "jurisdicciones_cubiertas", "verificacion_fuente",
    "registro_oficial_id",
]


def validate_fuente(fuente, path):
    errors = []
    warnings = []

    if not isinstance(fuente, dict):
        return [f"{path}: la fuente no es un objeto JSON."], []

    for field in FUENTE_REQUIRED_FIELDS:
        if field not in fuente:
            errors.append(f"{path}: falta el campo obligatorio '{field}'.")
    if errors:
        return errors, warnings

    if not is_nonempty_str(fuente.get("id")):
        errors.append(f"{path}: 'id' debe ser un string no vacío.")

    tipo_fuente = fuente.get("tipo_fuente")
    if tipo_fuente not in VALID_TIPO_FUENTE:
        errors.append(f"{path}: 'tipo_fuente' inválido: {tipo_fuente!r} (debe ser uno de {sorted(VALID_TIPO_FUENTE)}).")

    if not is_nonempty_str(fuente.get("titulo")):
        errors.append(f"{path}: 'titulo' debe ser un string no vacío.")
    if not is_nonempty_str(fuente.get("organismo_autor")):
        errors.append(f"{path}: 'organismo_autor' debe ser un string no vacío.")
    if not is_valid_iso_date(fuente.get("fecha_consulta")):
        errors.append(f"{path}: 'fecha_consulta' debe ser una fecha ISO válida (YYYY-MM-DD), no {fuente.get('fecha_consulta')!r}.")
    if not is_nonempty_str(fuente.get("localizador")):
        errors.append(f"{path}: 'localizador' debe describir un artículo, página, sentencia o sección concreta.")

    jurisdicciones_cubiertas = fuente.get("jurisdicciones_cubiertas")
    if not isinstance(jurisdicciones_cubiertas, list) or not jurisdicciones_cubiertas or not all(is_nonempty_str(j) for j in jurisdicciones_cubiertas):
        errors.append(f"{path}: 'jurisdicciones_cubiertas' debe ser una lista no vacía de países (strings no vacíos) que esta fuente realmente respalda.")

    errors.extend(validate_verificacion_fuente(fuente.get("verificacion_fuente"), path))

    url = fuente.get("url")
    identificador = fuente.get("identificador_bibliografico")
    has_url = url not in (None, "")
    has_id_biblio = is_nonempty_str(identificador)

    if not has_url and not has_id_biblio:
        errors.append(f"{path}: necesita 'url' (http/https) o 'identificador_bibliografico' — no puede carecer de ambos.")
    if has_url and not is_valid_http_url(url):
        errors.append(f"{path}: 'url' presente pero no es una URL http/https válida: {url!r}.")

    registro_oficial_id = fuente.get("registro_oficial_id")
    if registro_oficial_id is not None and not is_nonempty_str(registro_oficial_id):
        errors.append(f"{path}: 'registro_oficial_id' debe ser un string no vacío o null, no {registro_oficial_id!r}.")

    if errors:
        return errors, warnings

    # Registro oficial único (Fase 1D.1): toda la validación de
    # hostname↔organismo↔tipo_fuente↔jurisdicción para fuentes oficiales se
    # deriva de references/official-source-registry.json — ver
    # evaluate_fuente_registry para el detalle de cada comprobación.
    if tipo_fuente in TIPOS_FUENTE_OFICIAL:
        _nivel1_posible, reg_errors, reg_warnings = evaluate_fuente_registry(fuente)
        errors.extend(f"{path}: {e}" for e in reg_errors)
        warnings.extend(f"{path}: {w}" for w in reg_warnings)
    elif registro_oficial_id is not None:
        errors.append(
            f"{path}: 'registro_oficial_id' debe ser null para fuentes no oficiales (tipo_fuente={tipo_fuente!r}) "
            "— solo NORMA_OFICIAL/JURISPRUDENCIA_OFICIAL/AUTORIDAD_PUBLICA_OFICIAL pueden declarar un registro "
            "oficial."
        )

    return errors, warnings


NIVEL_1_CONFIRMADO = 1
NIVEL_2_DECLARADO_NO_VERIFICADO = 2
NIVEL_3_ACADEMICA_SECUNDARIA = 3
NIVEL_4_DRIVE = 4


def compute_fuente_nivel(fuente):
    tipo_fuente = fuente.get("tipo_fuente")
    if tipo_fuente == "DRIVE_INTERNO":
        return NIVEL_4_DRIVE
    if tipo_fuente in TIPOS_FUENTE_OFICIAL:
        v = fuente.get("verificacion_fuente") or {}
        # Fail-closed: TODAS las condiciones deben cumplirse para Nivel 1.
        # El booleano autoafirmado 'origen_oficial_confirmado' NUNCA basta
        # por sí solo — hace falta además que 'registro_oficial_id' apunte a
        # una entrada real del registro único, cuyo hostname, organismo,
        # tipo de fuente permitido y jurisdicción sean TODOS coherentes
        # (evaluate_fuente_registry), y que el propio JSON declare texto y
        # vigencia verificados (no solo "hay URL" o "hay fecha de consulta").
        nivel1_posible, _errors, _warnings = evaluate_fuente_registry(fuente)
        if (
            v.get("origen_oficial_confirmado") is True
            and nivel1_posible
            and v.get("texto_exacto_consultado") is True
            and v.get("vigencia_comprobada") is True
        ):
            return NIVEL_1_CONFIRMADO
        return NIVEL_2_DECLARADO_NO_VERIFICADO
    if tipo_fuente in TIPOS_FUENTE_SECUNDARIA_ACADEMICA:
        return NIVEL_3_ACADEMICA_SECUNDARIA
    return NIVEL_4_DRIVE


def nivel_to_estado_ceiling(niveles):
    if not niveles or all(n == NIVEL_4_DRIVE for n in niveles):
        return "REQUIERE_INVESTIGACION"
    if any(n == NIVEL_1_CONFIRMADO for n in niveles):
        return "APTO_PARA_NARRATIVA"
    if any(n in (NIVEL_2_DECLARADO_NO_VERIFICADO, NIVEL_3_ACADEMICA_SECUNDARIA) for n in niveles):
        return "APTO_CON_MATICES"
    return "REQUIERE_INVESTIGACION"


def compute_max_estado_por_fuentes(fuentes):
    niveles = [compute_fuente_nivel(f) for f in fuentes if isinstance(f, dict)]
    return nivel_to_estado_ceiling(niveles)


def estado_rank(estado):
    return ESTADO_LADDER.index(estado) if estado in ESTADO_LADDER else -1


def compute_ceiling_by_countries(paises_normalizados, fuentes):
    """Función compartida (Fase 1D, Paso 4) para Capa A y Capa C comparada:
    para cada país en 'paises_normalizados', calcula el techo con SOLO las
    fuentes cuyo 'jurisdicciones_cubiertas' realmente incluye ese país —
    nunca 'existe alguna fuente Nivel 1 en cualquier parte'. El techo final
    es el MÍNIMO entre todos los países: una fuente Nivel 1 en un país no
    compensa la falta de evidencia en otro."""
    ceilings = []
    for pais in paises_normalizados:
        niveles = [
            compute_fuente_nivel(f) for f in fuentes
            if isinstance(f, dict) and pais in normalize_countries_list(f.get("jurisdicciones_cubiertas"))
        ]
        ceilings.append(nivel_to_estado_ceiling(niveles))
    if not ceilings:
        return "REQUIERE_INVESTIGACION"
    return min(ceilings, key=estado_rank)


def compute_declared_countries_ceiling(jurisdiccion_field, fuentes):
    """Techo por país declarado cuando 'jurisdiccion' es uno o varios países,
    para CUALQUIER alcance que la declare (Capa C, Capa B y cualquier otro):
    reutiliza compute_ceiling_by_countries en vez de 'alguna fuente cubre
    alguno de los países' (esa era la falla — Bypass D de la Fase 1D, y su
    reaparición en Capa B — Fase 1E, Bypass E). En todo claim multijurisdiccional,
    incluido CAPA_B_VARIABLE, el techo jurídico se calcula como el mínimo de
    cobertura entre todas las jurisdicciones declaradas — nunca el máximo de
    cualquier fuente suelta."""
    paises = normalize_countries_list(jurisdiccion_field) if isinstance(jurisdiccion_field, list) else (
        [normalize_country(jurisdiccion_field)] if is_nonempty_str(jurisdiccion_field) else []
    )
    return compute_ceiling_by_countries(paises, fuentes)


def compute_capa_c_ceiling(jurisdiccion_field, fuentes):
    """Alias histórico de compute_declared_countries_ceiling, conservado por
    compatibilidad de nombre/API para Capa C — desde la Fase 1E la misma
    función de techo por país se usa también para Capa B (ver
    compute_declared_countries_ceiling y su uso en validate_claim)."""
    return compute_declared_countries_ceiling(jurisdiccion_field, fuentes)


def compute_capa_a_ceiling(claim, fuentes_by_id):
    """Para Capa A, el techo NO es 'existe alguna fuente Nivel 1 en cualquier
    parte' — es el mínimo entre los techos de CADA jurisdicción declarada,
    calculado solo con las fuentes que esa jurisdicción referencia y que
    además la cubren de verdad (jurisdicciones_cubiertas). Una fuente
    Nivel 1 más tres sin verificar da como techo el de la peor jurisdicción,
    no el de la mejor."""
    jurisdicciones = claim.get("jurisdicciones_revisadas") or []
    per_country_ceilings = []
    for entry in jurisdicciones:
        if not isinstance(entry, dict):
            continue
        pais_norm = normalize_country(entry.get("pais", ""))
        fuente_ids = entry.get("fuente_ids") or []
        niveles = []
        for fid in fuente_ids:
            f = fuentes_by_id.get(fid)
            if not f:
                continue
            cubiertas = normalize_countries_list(f.get("jurisdicciones_cubiertas"))
            if pais_norm not in cubiertas:
                # Esta fuente no respalda realmente esta jurisdicción -> no cuenta.
                continue
            niveles.append(compute_fuente_nivel(f))
        per_country_ceilings.append(nivel_to_estado_ceiling(niveles))
    if not per_country_ceilings:
        return "REQUIERE_INVESTIGACION"
    return min(per_country_ceilings, key=estado_rank)


# ---------------------------------------------------------------------------
# Validación de objetos de revisión (humana / plataforma / confidencialidad)
# ---------------------------------------------------------------------------

def validate_revision_humana(revision, path):
    errors = []
    if not isinstance(revision, dict):
        return [f"{path}: debe ser un objeto."]
    required = ["estado", "revisor", "fecha", "observaciones", "contenido_hash_sha256"]
    for f in required:
        if f not in revision:
            errors.append(f"{path}: falta el campo '{f}' (puede ser null salvo 'estado', pero debe existir).")
    if errors:
        return errors
    estado = revision.get("estado")
    if estado not in VALID_REVISION_ESTADO:
        errors.append(f"{path}.estado: inválido: {estado!r} (debe ser uno de {sorted(VALID_REVISION_ESTADO)}).")
    if estado == "APROBADO":
        if not is_nonempty_str(revision.get("revisor")):
            errors.append(f"{path}: estado APROBADO requiere 'revisor' identificado (puede ser un identificador ficticio en pruebas, nunca un nombre real en fixtures).")
        if not is_valid_iso_date(revision.get("fecha")):
            errors.append(f"{path}: estado APROBADO requiere 'fecha' ISO válida.")
        hash_val = revision.get("contenido_hash_sha256")
        if not isinstance(hash_val, str) or not SHA256_RE.match(hash_val):
            errors.append(f"{path}: estado APROBADO requiere 'contenido_hash_sha256' como 64 caracteres hexadecimales — liga la aprobación al contenido exacto que se aprobó.")
    return errors


def validate_review_object(review, path, label):
    errors = []
    if not isinstance(review, dict):
        return [f"{path}: '{label}' debe ser un objeto."]
    for f in ("required", "status", "revisor", "fecha", "observaciones"):
        if f not in review:
            errors.append(f"{path}.{label}: falta el campo '{f}'.")
    if errors:
        return errors
    if not isinstance(review.get("required"), bool):
        errors.append(f"{path}.{label}.required: debe ser booleano.")
    status = review.get("status")
    if status not in VALID_REVIEW_STATUS:
        errors.append(f"{path}.{label}.status: inválido: {status!r} (debe ser uno de {sorted(VALID_REVIEW_STATUS)}).")
    if review.get("required") is False and status != "NO_APLICA":
        errors.append(f"{path}.{label}: required=false implica status='NO_APLICA'.")
    if review.get("required") is True and status == "NO_APLICA":
        errors.append(f"{path}.{label}: required=true no puede tener status='NO_APLICA' (hace falta PENDIENTE/APROBADO/RECHAZADO).")
    if status == "APROBADO":
        if not is_nonempty_str(review.get("revisor")):
            errors.append(f"{path}.{label}: status APROBADO requiere 'revisor'.")
        if not is_valid_iso_date(review.get("fecha")):
            errors.append(f"{path}.{label}: status APROBADO requiere 'fecha' ISO válida.")
    return errors


def review_allows_gate(review):
    return isinstance(review, dict) and review.get("status") in ("NO_APLICA", "APROBADO")


# ---------------------------------------------------------------------------
# Validación de un claim
# ---------------------------------------------------------------------------

CLAIM_REQUIRED_FIELDS = [
    "claim_id", "texto_exacto", "ubicacion", "tipo", "alcance",
    "confianza", "riesgo_falsa_universalizacion", "riesgo_asesoria",
    "platform_review", "confidentiality_review",
    "fuentes", "estado", "revision_humana", "gate_arte",
    "reformulacion_propuesta",
]

CAPA_A_JUSTIFICATION_FIELDS = ["diferencias_buscadas", "contraejemplos_encontrados", "justificacion_suficiencia_comparada"]
MIN_JURISDICCIONES_REVISADAS_CAPA_A = 3


def validate_claim(claim, path):
    errors = []
    warnings = []

    if not isinstance(claim, dict):
        return [f"{path}: el claim no es un objeto JSON."], [], None, None

    for field in CLAIM_REQUIRED_FIELDS:
        if field not in claim:
            errors.append(f"{path}: falta el campo obligatorio '{field}'.")
    if errors:
        return errors, warnings, None, None

    if not is_nonempty_str(claim.get("claim_id")):
        errors.append(f"{path}: 'claim_id' debe ser un string no vacío.")
    if not is_nonempty_str(claim.get("texto_exacto")):
        errors.append(f"{path}: 'texto_exacto' debe ser un string no vacío.")
    if claim.get("ubicacion") not in VALID_UBICACION:
        errors.append(f"{path}: 'ubicacion' inválida: {claim.get('ubicacion')!r}.")
    if claim.get("tipo") not in VALID_TIPO:
        errors.append(f"{path}: 'tipo' inválido: {claim.get('tipo')!r} (debe ser uno de {sorted(VALID_TIPO)}).")

    alcance = claim.get("alcance")
    if alcance not in VALID_ALCANCE:
        errors.append(f"{path}: 'alcance' inválido: {alcance!r} (debe ser uno de {sorted(VALID_ALCANCE)}).")

    estado = claim.get("estado")
    if estado not in VALID_ESTADO:
        errors.append(f"{path}: 'estado' inválido: {estado!r} (debe ser uno de {sorted(VALID_ESTADO)}).")

    if claim.get("confianza") not in VALID_CONFIANZA:
        errors.append(f"{path}: 'confianza' inválida: {claim.get('confianza')!r}.")
    if claim.get("riesgo_falsa_universalizacion") not in VALID_RIESGO:
        errors.append(f"{path}: 'riesgo_falsa_universalizacion' inválido: {claim.get('riesgo_falsa_universalizacion')!r}.")
    if claim.get("riesgo_asesoria") not in VALID_RIESGO:
        errors.append(f"{path}: 'riesgo_asesoria' inválido: {claim.get('riesgo_asesoria')!r}.")

    # --- tipos estrictos ---
    jurisdiccion = claim.get("jurisdiccion")
    if jurisdiccion is not None and not is_str_or_nonempty_list_of_str(jurisdiccion):
        errors.append(f"{path}: 'jurisdiccion' debe ser string no vacío, lista no vacía de strings, o null — no {jurisdiccion!r}.")
    variaciones = claim.get("variaciones_materiales")
    if variaciones is not None and not is_str_or_nonempty_list_of_str(variaciones):
        errors.append(f"{path}: 'variaciones_materiales' debe ser string no vacío, lista no vacía de strings, o null — no {variaciones!r}.")
    if not is_nullable_str(claim.get("notas")):
        errors.append(f"{path}: 'notas' debe ser string o null.")
    if not is_nullable_str(claim.get("redaccion_prohibida")):
        errors.append(f"{path}: 'redaccion_prohibida' debe ser string o null.")

    # --- revision_humana / platform_review / confidentiality_review ---
    errors.extend(validate_revision_humana(claim.get("revision_humana"), f"{path}.revision_humana"))
    errors.extend(validate_review_object(claim.get("platform_review"), path, "platform_review"))
    errors.extend(validate_review_object(claim.get("confidentiality_review"), path, "confidentiality_review"))

    # --- reformulacion_propuesta ---
    reform = claim.get("reformulacion_propuesta")
    if not isinstance(reform, dict):
        errors.append(f"{path}.reformulacion_propuesta: debe ser un objeto.")
    else:
        for f in ("texto", "verificada", "nuevo_claim_id"):
            if f not in reform:
                errors.append(f"{path}.reformulacion_propuesta: falta el campo '{f}' (puede ser null, pero debe existir).")
        if "verificada" in reform and not isinstance(reform.get("verificada"), bool):
            errors.append(f"{path}.reformulacion_propuesta.verificada: debe ser booleano.")
        if "texto" in reform and not is_nullable_str(reform.get("texto")):
            errors.append(f"{path}.reformulacion_propuesta.texto: debe ser string o null.")
        if "nuevo_claim_id" in reform and not is_nullable_str(reform.get("nuevo_claim_id")):
            errors.append(f"{path}.reformulacion_propuesta.nuevo_claim_id: debe ser string o null.")
        if reform.get("texto") not in (None, "") and reform.get("verificada") is True and not is_nonempty_str(reform.get("nuevo_claim_id")):
            errors.append(
                f"{path}.reformulacion_propuesta: no puede declararse 'verificada: true' sin 'nuevo_claim_id' "
                "apuntando al claim que la re-verificó."
            )

    # --- fuentes ---
    fuentes = claim.get("fuentes")
    fuente_ids = set()
    fuentes_by_id = {}
    if not isinstance(fuentes, list):
        errors.append(f"{path}.fuentes: debe ser una lista (puede estar vacía).")
        fuentes = []
    else:
        for idx, fuente in enumerate(fuentes):
            f_errors, f_warnings = validate_fuente(fuente, f"{path}.fuentes[{idx}]")
            errors.extend(f_errors)
            warnings.extend(f_warnings)
            if isinstance(fuente, dict) and is_nonempty_str(fuente.get("id")):
                if fuente["id"] in fuente_ids:
                    errors.append(f"{path}.fuentes[{idx}]: id de fuente duplicado dentro del mismo claim: {fuente['id']!r}.")
                fuente_ids.add(fuente["id"])
                fuentes_by_id[fuente["id"]] = fuente

    if errors:
        return errors, warnings, None, None

    # --- reglas de alcance ---
    if alcance == "CAPA_C_NACIONAL" and not jurisdiccion:
        errors.append(f"{path}: Capa C (CAPA_C_NACIONAL) requiere 'jurisdiccion' con al menos un país.")
    if alcance == "CAPA_C_NACIONAL" and jurisdiccion:
        # Fase 1D, Paso 4: 'jurisdiccion' no puede estar vacía ni tener países
        # duplicados. La cobertura COMPLETA por país (no "alguna fuente cubre
        # alguno de los países declarados", el Bypass D) se aplica más abajo
        # a través de compute_capa_c_ceiling: un país sin fuente que lo cubra
        # topa el techo en REQUIERE_INVESTIGACION para TODA la Capa C, sin
        # bloquear con un error duro el caso legítimo de "todavía sin fuentes,
        # correctamente declarado REQUIERE_INVESTIGACION".
        paises_c_raw = jurisdiccion if isinstance(jurisdiccion, list) else [jurisdiccion]
        if not paises_c_raw:
            errors.append(f"{path}: Capa C con 'jurisdiccion' como lista no puede estar vacía.")
        else:
            seen_c = set()
            for p in paises_c_raw:
                norm = normalize_country(p) if is_nonempty_str(p) else None
                if norm is None:
                    continue
                if norm in seen_c:
                    errors.append(f"{path}: país duplicado (normalizado) en 'jurisdiccion': {p!r}.")
                    continue
                seen_c.add(norm)

    if alcance == "CAPA_B_VARIABLE" and not variaciones:
        errors.append(f"{path}: Capa B (CAPA_B_VARIABLE) requiere 'variaciones_materiales'.")

    if alcance == "NO_DETERMINADO" and estado != "REQUIERE_INVESTIGACION":
        errors.append(
            f"{path}: alcance NO_DETERMINADO solo puede combinarse con estado REQUIERE_INVESTIGACION. "
            "Si la investigación SÍ concluyó algo firme (p. ej. una atribución refutada), usa NO_APLICA."
        )

    capa_a_ceiling = None
    if alcance == "CAPA_A_TRANSVERSAL":
        jurisdicciones = claim.get("jurisdicciones_revisadas")
        missing_just = [f for f in CAPA_A_JUSTIFICATION_FIELDS if not claim.get(f)]
        if missing_just:
            errors.append(f"{path}: Capa A requiere justificación comparada explícita; faltan o vacíos: {missing_just}.")
        if not isinstance(jurisdicciones, list) or not jurisdicciones:
            errors.append(f"{path}: Capa A requiere 'jurisdicciones_revisadas' como lista de {{pais, fuente_ids}}.")
        else:
            seen_normalized = set()
            for j_idx, entry in enumerate(jurisdicciones):
                if not isinstance(entry, dict) or "pais" not in entry or "fuente_ids" not in entry:
                    errors.append(f"{path}.jurisdicciones_revisadas[{j_idx}]: debe ser {{'pais': str, 'fuente_ids': [ids]}}.")
                    continue
                pais = entry.get("pais")
                if not is_nonempty_str(pais):
                    errors.append(f"{path}.jurisdicciones_revisadas[{j_idx}]: 'pais' debe ser un string no vacío.")
                    continue
                norm = normalize_country(pais)
                if norm in seen_normalized:
                    errors.append(f"{path}.jurisdicciones_revisadas[{j_idx}]: país duplicado (normalizado): {pais!r}.")
                seen_normalized.add(norm)
                f_ids = entry.get("fuente_ids")
                if not isinstance(f_ids, list) or not f_ids or not all(is_nonempty_str(x) for x in f_ids):
                    errors.append(f"{path}.jurisdicciones_revisadas[{j_idx}] ({pais}): 'fuente_ids' debe ser una lista no vacía de strings.")
                    continue
                for fid in f_ids:
                    if fid not in fuente_ids:
                        errors.append(f"{path}.jurisdicciones_revisadas[{j_idx}] ({pais}): fuente_id {fid!r} no existe entre las 'fuentes' del claim.")
                        continue
                    f = fuentes_by_id[fid]
                    cubiertas = normalize_countries_list(f.get("jurisdicciones_cubiertas"))
                    if norm not in cubiertas:
                        errors.append(
                            f"{path}.jurisdicciones_revisadas[{j_idx}] ({pais}): la fuente {fid!r} no cubre esta "
                            f"jurisdicción — su 'jurisdicciones_cubiertas' es {f.get('jurisdicciones_cubiertas')!r}. "
                            "Una fuente de un país no respalda automáticamente a otro."
                        )
            if len(seen_normalized) < MIN_JURISDICCIONES_REVISADAS_CAPA_A:
                errors.append(
                    f"{path}: Capa A requiere al menos {MIN_JURISDICCIONES_REVISADAS_CAPA_A} jurisdicciones "
                    f"distintas y normalizadas con evidencia propia; hay {len(seen_normalized)}."
                )
        if not errors:
            capa_a_ceiling = compute_capa_a_ceiling(claim, fuentes_by_id)

    if errors:
        return errors, warnings, None, None

    # --- reglas de suficiencia de fuentes vs. estado declarado ---
    if alcance == "CAPA_A_TRANSVERSAL":
        max_estado = compute_capa_a_ceiling(claim, fuentes_by_id)
    elif jurisdiccion:
        # Fase 1E: CUALQUIER alcance con 'jurisdiccion' declarada (país o
        # lista de países) usa el techo POR PAÍS — nunca 'alguna fuente
        # Nivel 1 en cualquier parte'. Antes solo CAPA_C_NACIONAL tenía esta
        # protección; CAPA_B_VARIABLE (y cualquier otro alcance con
        # 'jurisdiccion' declarada) caía en la rama de abajo
        # (compute_max_estado_por_fuentes), que es un máximo plano sobre
        # TODAS las fuentes del claim sin partir por país — una sola fuente
        # Nivel 1 de México podía elevar a APTO_PARA_NARRATIVA un claim que
        # también declaraba España y Argentina, aunque Argentina solo
        # tuviera Nivel 2 o ninguna fuente propia. Ese bypass queda cerrado
        # aquí: se reutiliza la misma función que ya usaba Capa C
        # (compute_declared_countries_ceiling → compute_ceiling_by_countries),
        # que exige Nivel 1 en CADA país declarado y toma el mínimo entre
        # todos ellos.
        max_estado = compute_declared_countries_ceiling(jurisdiccion, fuentes)
    else:
        max_estado = compute_max_estado_por_fuentes(fuentes)
    if estado in ESTADO_LADDER:
        if estado_rank(estado) > estado_rank(max_estado):
            extra = (
                " Para Capa A, el techo es el mínimo entre todas las jurisdicciones declaradas, "
                "no el máximo de cualquier fuente suelta."
                if alcance == "CAPA_A_TRANSVERSAL" else (
                    " Con varios países declarados en 'jurisdiccion' (incluida CAPA_B_VARIABLE), "
                    "el techo es el mínimo entre todos ellos, no el máximo de cualquier fuente "
                    "suelta — una fuente Nivel 1 de un país no compensa la falta de cobertura en otro."
                    if isinstance(jurisdiccion, list) and len(jurisdiccion) > 1 else ""
                )
            )
            errors.append(
                f"{path}: estado declarado '{estado}' excede lo que las fuentes permiten "
                f"(máximo sostenible: '{max_estado}').{extra}"
            )
        if estado in ("APTO_CON_MATICES", "APTO_PARA_NARRATIVA") and claim.get("confianza") == "baja":
            errors.append(f"{path}: estado '{estado}' no puede tener confianza='baja'.")

    # --- gate a nivel de claim ---
    # Nota (Fase 1D.2): si ya hay un error previo en este claim (p. ej. el
    # 'estado' declarado excede lo que las fuentes permiten sostener), el
    # gate NUNCA puede computarse como ABIERTO — sin importar que
    # revision_humana/hash/reviews parezcan coherentes con ese 'estado'
    # inflado. Detectado durante las pruebas de esta fase: antes, una fuente
    # oficial sin URL con revisión "aprobada" (hash calculado sobre el
    # propio contenido inflado) podía hacer que este bloque calculara
    # 'ABIERTO' internamente, aunque el pipeline completo igual rechazaba el
    # paquete por el error de 'excede lo que las fuentes permiten' — un
    # valor interno engañoso que ya no se produce.
    revision = claim.get("revision_humana") or {}
    platform = claim.get("platform_review") or {}
    confidentiality = claim.get("confidentiality_review") or {}
    computed_gate = "CERRADO"
    if (
        not errors
        and estado == "APTO_PARA_NARRATIVA"
        and revision.get("estado") == "APROBADO"
        and review_allows_gate(platform)
        and review_allows_gate(confidentiality)
    ):
        expected_hash = compute_content_hash(claim)
        if revision.get("contenido_hash_sha256") == expected_hash:
            computed_gate = "ABIERTO"
        else:
            errors.append(
                f"{path}.revision_humana.contenido_hash_sha256: no coincide con el hash recalculado del "
                "contenido actual del claim — el texto, alcance, jurisdicción, fuentes o localizadores cambiaron "
                "después de la aprobación (o el hash nunca fue calculado sobre este contenido). La aprobación "
                "queda invalidada y el gate se mantiene CERRADO."
            )

    declared_gate = claim.get("gate_arte")
    if declared_gate not in VALID_GATE:
        errors.append(f"{path}.gate_arte: inválido: {declared_gate!r} (debe ser CERRADO o ABIERTO).")
    elif declared_gate != computed_gate:
        errors.append(
            f"{path}.gate_arte: declarado '{declared_gate}' pero las reglas solo permiten '{computed_gate}'."
        )

    return errors, warnings, max_estado, computed_gate


# ---------------------------------------------------------------------------
# Validación de una pieza (schema v3)
# ---------------------------------------------------------------------------

PIECE_REQUIRED_FIELDS = ["schema_version", "piece_id", "claims", "estado_agregado", "revisiones_pendientes", "gate_global_arte"]

ESTADO_AGREGADO_PRIORITY = ["BLOQUEADO", "REQUIERE_INVESTIGACION", "PENDIENTE_APROBACION_HUMANA", "APTO_CON_MATICES", "APTO_PARA_NARRATIVA"]


def compute_estado_agregado(claim_estados):
    for candidate in ESTADO_AGREGADO_PRIORITY:
        if candidate == "APTO_PARA_NARRATIVA":
            if claim_estados and all(e == "APTO_PARA_NARRATIVA" for e in claim_estados):
                return "APTO_PARA_NARRATIVA"
            continue
        if candidate in claim_estados:
            return candidate
    return "REQUIERE_INVESTIGACION"


def compute_revisiones_pendientes(claims):
    pending = []
    for claim in claims:
        revision = claim.get("revision_humana") or {}
        platform = claim.get("platform_review") or {}
        confidentiality = claim.get("confidentiality_review") or {}
        needs = (
            claim.get("estado") != "APTO_PARA_NARRATIVA"
            or revision.get("estado") != "APROBADO"
            or not review_allows_gate(platform)
            or not review_allows_gate(confidentiality)
        )
        if needs:
            pending.append(claim.get("claim_id"))
    return pending


def validate_piece(data, source_name):
    errors = []
    warnings = []

    if not isinstance(data, dict):
        return ["El paquete no es un objeto JSON."], []

    for field in PIECE_REQUIRED_FIELDS:
        if field not in data:
            errors.append(f"Falta el campo obligatorio de nivel pieza: '{field}'.")
    if errors:
        return errors, warnings

    declared_version = data.get("schema_version")
    if declared_version != SCHEMA_VERSION:
        if declared_version == "3.0":
            errors.append(
                "'schema_version' declara \"3.0\", pero el validador exige \"4.0\" desde la Fase 1D.1: cada fuente "
                "oficial ahora necesita 'registro_oficial_id' referenciando el registro único "
                "(references/official-source-registry.json), que cruza hostname, organismo, tipo de fuente "
                "permitido y jurisdicción. \"3.0\" ya NO es una versión vigente — migra el paquete añadiendo "
                "'registro_oficial_id' a cada fuente y actualizando 'schema_version' a \"4.0\"."
            )
        else:
            errors.append(f"'schema_version' debe ser {SCHEMA_VERSION!r}, no {declared_version!r}.")
    if not is_nonempty_str(data.get("piece_id")):
        errors.append("'piece_id' debe ser un string no vacío.")

    claims = data.get("claims")
    if not isinstance(claims, list) or not claims:
        errors.append("'claims' debe ser una lista con al menos un claim.")
        return errors, warnings

    seen_claim_ids = set()
    claim_results = []
    for idx, claim in enumerate(claims):
        c_errors, c_warnings, _max_estado, _gate = validate_claim(claim, f"claims[{idx}]")
        errors.extend(c_errors)
        warnings.extend(c_warnings)
        if isinstance(claim, dict) and is_nonempty_str(claim.get("claim_id")):
            cid = claim["claim_id"]
            if cid in seen_claim_ids:
                errors.append(f"claim_id duplicado dentro de la pieza: {cid!r}.")
            seen_claim_ids.add(cid)
        claim_results.append(claim if isinstance(claim, dict) else {})

    for idx, claim in enumerate(claim_results):
        reform = claim.get("reformulacion_propuesta") if isinstance(claim, dict) else None
        if isinstance(reform, dict):
            nuevo_id = reform.get("nuevo_claim_id")
            if nuevo_id and nuevo_id not in seen_claim_ids:
                errors.append(f"claims[{idx}].reformulacion_propuesta.nuevo_claim_id={nuevo_id!r} no existe como claim_id en esta pieza.")

    if errors:
        return errors, warnings

    claim_estados = [c.get("estado") for c in claim_results]
    computed_estado_agregado = compute_estado_agregado(claim_estados)
    declared_estado_agregado = data.get("estado_agregado")
    if declared_estado_agregado != computed_estado_agregado:
        errors.append(
            f"'estado_agregado' declarado como {declared_estado_agregado!r} pero el cálculo real da "
            f"{computed_estado_agregado!r} a partir de {claim_estados}."
        )

    computed_pending = sorted(compute_revisiones_pendientes(claim_results))
    declared_pending = data.get("revisiones_pendientes")
    if not isinstance(declared_pending, list) or sorted(declared_pending) != computed_pending:
        errors.append(f"'revisiones_pendientes' declarado como {declared_pending!r} pero el cálculo real da {computed_pending!r}.")

    claim_gates = []
    for c in claim_results:
        _e, _w, _m, gate = validate_claim(c, "recheck")
        claim_gates.append(gate)
    computed_gate_global = "ABIERTO" if (computed_estado_agregado == "APTO_PARA_NARRATIVA" and claim_gates and all(g == "ABIERTO" for g in claim_gates)) else "CERRADO"
    declared_gate_global = data.get("gate_global_arte")
    if declared_gate_global not in VALID_GATE:
        errors.append(f"'gate_global_arte' inválido: {declared_gate_global!r}.")
    elif declared_gate_global != computed_gate_global:
        errors.append(f"'gate_global_arte' declarado como {declared_gate_global!r} pero el cálculo real da {computed_gate_global!r}.")

    return errors, warnings


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def validate_file(path: Path):
    try:
        text = path.read_text(encoding="utf-8")
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        return False, [f"{Tag.ERROR} {path}: JSON mal formado — {exc}"]
    except OSError as exc:
        return False, [f"{Tag.ERROR} {path}: no se pudo leer — {exc}"]

    errors, warnings = validate_piece(data, str(path))

    lines = []
    if errors:
        lines.append(f"{Tag.ERROR} {path}")
        for e in errors:
            lines.append(f"  - {e}")
        return False, lines

    for w in warnings:
        lines.append(f"{Tag.WARNING} {path}: {w}")

    gate = data.get("gate_global_arte")
    estado_agregado = data.get("estado_agregado")
    if gate == "ABIERTO":
        lines.append(f"{Tag.GATE_OPEN} {path}: estado_agregado={estado_agregado}.")
    else:
        pending = data.get("revisiones_pendientes") or []
        if estado_agregado in ("REQUIERE_INVESTIGACION", "BLOQUEADO"):
            lines.append(f"{Tag.GATE_CLOSED} {path}: estado_agregado={estado_agregado}.")
        else:
            lines.append(f"{Tag.OK_PENDING_HUMAN} {path}: gate cerrado a la espera de: {pending}.")
            lines.append(f"{Tag.GATE_CLOSED} {path}")

    return True, lines


def main(argv):
    if not argv:
        print("Uso: validate-claim-packet.py archivo1.json [archivo2.json ...]", file=sys.stderr)
        return 1

    overall_ok = True
    for path_str in argv:
        path = Path(path_str)
        if not path.exists():
            print(f"{Tag.ERROR} {path_str}: archivo no encontrado")
            overall_ok = False
            continue
        ok, lines = validate_file(path)
        for line in lines:
            print(line)
        if not ok:
            overall_ok = False

    return 0 if overall_ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
