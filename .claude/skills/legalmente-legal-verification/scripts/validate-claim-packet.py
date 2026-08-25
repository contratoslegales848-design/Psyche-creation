#!/usr/bin/env python3
"""Valida la ESTRUCTURA de una PIEZA de verificación jurídica de LegalMente
(esquema v2: una pieza contiene una o varias afirmaciones/"claims").

No decide si una afirmación jurídica es correcta. No decide si una fuente
es realmente oficial. Decide si el paquete es estructuralmente completo,
internamente coherente, y si el "gate" de arte que declara corresponde
exactamente a lo que las reglas del esquema permiten — de forma fail-closed:
ante cualquier duda, el gate queda cerrado.

Solo biblioteca estándar de Python (json, sys, re, pathlib, urllib.parse,
datetime). Sin dependencias externas.

Uso:
    python3 validate-claim-packet.py archivo1.json [archivo2.json ...]

Código de salida:
    0 si TODAS las piezas son estructuralmente válidas (con o sin
      advertencias de fuente, con o sin gate abierto).
    1 si al menos una pieza tiene errores estructurales, JSON mal formado,
      o un gate declarado que no corresponde a lo que las reglas permiten.
"""

import json
import re
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

SCHEMA_VERSION = "2.0"

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

# Orden de "permisividad" de los tres estados que forman una escalera continua.
# BLOQUEADO y PENDIENTE_APROBACION_HUMANA son estados laterales restrictivos,
# no forman parte de esta escalera.
ESTADO_LADDER = ["REQUIERE_INVESTIGACION", "APTO_CON_MATICES", "APTO_PARA_NARRATIVA"]

VALID_UBICACION = {
    "titulo",
    "hook",
    "texto_imagen",
    "caption",
    "lista",
    "cta",
    "prompt_visual",
    "descripcion_tema",
}

VALID_TIPO = {
    "regla",
    "definicion",
    "cita",
    "atribucion",
    "dato",
    "procedimiento",
    "consecuencia",
    "consejo",
}

VALID_CONFIANZA = {"alta", "media", "baja"}
VALID_RIESGO = {"ninguno", "bajo", "medio", "alto"}

VALID_TIPO_FUENTE = {
    "NORMA_OFICIAL",
    "JURISPRUDENCIA_OFICIAL",
    "AUTORIDAD_PUBLICA_OFICIAL",
    "ACADEMICA_IDENTIFICABLE",
    "SECUNDARIA_ESPECIALIZADA",
    "DRIVE_INTERNO",
}

# Fuentes cuyo TIPO declara autoridad oficial. Para sostener APTO_PARA_NARRATIVA
# necesitan además dominio_oficial_confirmado=true (ver compute_fuente_nivel).
TIPOS_FUENTE_OFICIAL = {"NORMA_OFICIAL", "JURISPRUDENCIA_OFICIAL", "AUTORIDAD_PUBLICA_OFICIAL"}
TIPOS_FUENTE_SECUNDARIA_ACADEMICA = {"ACADEMICA_IDENTIFICABLE", "SECUNDARIA_ESPECIALIZADA"}

VALID_REVISION_HUMANA_ESTADO = {"PENDIENTE", "APROBADO", "RECHAZADO"}
VALID_GATE = {"CERRADO", "ABIERTO"}

# Heurística ORIENTATIVA de dominios oficiales conocidos. NO es prueba jurídica
# definitiva por sí sola — solo genera una advertencia si no coincide. Lo que
# de verdad abre o cierra la puerta a NIVEL_1 es el campo explícito
# 'dominio_oficial_confirmado', nunca esta lista por sí sola.
OFFICIAL_DOMAIN_HINTS = (
    ".gob.mx", ".gob.es", "boe.es", "diputados.gob.mx", "senado.gob.mx",
    "dof.gob.mx", "scjn.gob.mx", "gob.pe", "tc.gob.pe", "pj.gob.pe",
    "poderjudicial.es", "congreso.es", "boletinoficial.gob.ar",
    "infoleg.gob.ar", "csjn.gov.ar", "funcionpublica.gov.co",
    "corteconstitucional.gov.co", "eur-lex.europa.eu", ".gov", ".gov.co",
    ".gov.ar",
)

ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


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


def is_valid_iso_date(value):
    if not isinstance(value, str) or not ISO_DATE_RE.match(value):
        return False
    try:
        y, m, d = (int(part) for part in value.split("-"))
        date(y, m, d)
        return True
    except ValueError:
        return False


def is_valid_http_url(value):
    if not isinstance(value, str) or not value:
        return False
    parsed = urlparse(value)
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def domain_matches_official_hint(url):
    if not isinstance(url, str):
        return False
    netloc = urlparse(url).netloc.lower()
    return any(hint in netloc for hint in OFFICIAL_DOMAIN_HINTS)


def normalize_country(name):
    return " ".join(name.strip().casefold().split())


def as_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


# ---------------------------------------------------------------------------
# Validación de una fuente
# ---------------------------------------------------------------------------

FUENTE_REQUIRED_FIELDS = [
    "id", "tipo_fuente", "titulo", "organismo_autor", "fecha_consulta",
    "localizador", "dominio_oficial_confirmado",
]


def validate_fuente(fuente, path):
    errors = []
    warnings = []

    if not isinstance(fuente, dict):
        return [f"{path}: la fuente no es un objeto JSON."], []

    for field in FUENTE_REQUIRED_FIELDS:
        if field not in fuente:
            errors.append(f"{path}: falta el campo obligatorio '{field}'.")
    # url e identificador_bibliografico se validan aparte (uno de los dos, no ambos obligatorios)
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
        errors.append(f"{path}: 'localizador' debe describir un artículo, página, sentencia o sección concreta — no puede estar vacío.")
    if not isinstance(fuente.get("dominio_oficial_confirmado"), bool):
        errors.append(f"{path}: 'dominio_oficial_confirmado' debe ser booleano (true/false).")

    url = fuente.get("url")
    identificador = fuente.get("identificador_bibliografico")
    has_url = url not in (None, "")
    has_id_biblio = is_nonempty_str(identificador)

    if not has_url and not has_id_biblio:
        errors.append(f"{path}: necesita 'url' (http/https) o 'identificador_bibliografico' — no puede carecer de ambos.")
    if has_url and not is_valid_http_url(url):
        errors.append(f"{path}: 'url' presente pero no es una URL http/https válida: {url!r}.")

    if has_url and tipo_fuente in TIPOS_FUENTE_OFICIAL and not domain_matches_official_hint(url):
        warnings.append(
            f"{path}: el dominio de la URL no coincide con la lista heurística de dominios "
            f"oficiales conocidos ({urlparse(url).netloc!r}). Esta lista es orientativa, "
            "NO es prueba jurídica definitiva por sí sola — pero si 'dominio_oficial_confirmado' "
            "tampoco es true, esta fuente no puede sostener APTO_PARA_NARRATIVA."
        )

    return errors, warnings


NIVEL_1_CONFIRMADO = 1       # oficial + confirmado -> puede sostener APTO_PARA_NARRATIVA
NIVEL_2_DECLARADO_NO_VERIFICADO = 2  # oficial pero no confirmado -> tope APTO_CON_MATICES
NIVEL_3_ACADEMICA_SECUNDARIA = 3     # académica/secundaria -> tope APTO_CON_MATICES
NIVEL_4_DRIVE = 4             # Drive interno -> nunca sostiene un estado apto


def compute_fuente_nivel(fuente):
    tipo_fuente = fuente.get("tipo_fuente")
    if tipo_fuente == "DRIVE_INTERNO":
        return NIVEL_4_DRIVE
    if tipo_fuente in TIPOS_FUENTE_OFICIAL:
        if fuente.get("dominio_oficial_confirmado") is True:
            return NIVEL_1_CONFIRMADO
        return NIVEL_2_DECLARADO_NO_VERIFICADO
    if tipo_fuente in TIPOS_FUENTE_SECUNDARIA_ACADEMICA:
        return NIVEL_3_ACADEMICA_SECUNDARIA
    return NIVEL_4_DRIVE  # tipo desconocido ya fue rechazado antes; por defecto, el nivel más bajo


def compute_max_estado_por_fuentes(fuentes):
    """Techo de 'estado' que las fuentes pueden sostener, en la escalera
    REQUIERE_INVESTIGACION < APTO_CON_MATICES < APTO_PARA_NARRATIVA."""
    if not fuentes:
        return "REQUIERE_INVESTIGACION"
    niveles = [compute_fuente_nivel(f) for f in fuentes if isinstance(f, dict)]
    if not niveles or all(n == NIVEL_4_DRIVE for n in niveles):
        # Drive nunca puede sostener, por sí solo, un estado apto.
        return "REQUIERE_INVESTIGACION"
    if any(n == NIVEL_1_CONFIRMADO for n in niveles):
        return "APTO_PARA_NARRATIVA"
    if any(n in (NIVEL_2_DECLARADO_NO_VERIFICADO, NIVEL_3_ACADEMICA_SECUNDARIA) for n in niveles):
        return "APTO_CON_MATICES"
    return "REQUIERE_INVESTIGACION"


# ---------------------------------------------------------------------------
# Validación de un claim
# ---------------------------------------------------------------------------

CLAIM_REQUIRED_FIELDS = [
    "claim_id", "texto_exacto", "ubicacion", "tipo", "alcance",
    "confianza", "riesgo_falsa_universalizacion", "riesgo_asesoria",
    "platform_review_required", "confidentiality_review_required",
    "fuentes", "estado", "revision_humana", "gate_arte",
    "reformulacion_propuesta",
]

CAPA_A_JUSTIFICATION_FIELDS = [
    "diferencias_buscadas", "contraejemplos_encontrados", "justificacion_suficiencia_comparada",
]

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
    for bool_field in ("platform_review_required", "confidentiality_review_required"):
        if not isinstance(claim.get(bool_field), bool):
            errors.append(f"{path}: '{bool_field}' debe ser booleano.")

    # --- revision_humana ---
    revision = claim.get("revision_humana")
    if not isinstance(revision, dict):
        errors.append(f"{path}.revision_humana: debe ser un objeto.")
    else:
        rh_estado = revision.get("estado")
        if rh_estado not in VALID_REVISION_HUMANA_ESTADO:
            errors.append(f"{path}.revision_humana.estado: inválido: {rh_estado!r} (debe ser uno de {sorted(VALID_REVISION_HUMANA_ESTADO)}).")
        if "revisor" not in revision or "fecha" not in revision or "observaciones" not in revision:
            errors.append(f"{path}.revision_humana: faltan campos ('revisor', 'fecha', 'observaciones' deben existir, aunque sean null).")
        if rh_estado == "APROBADO":
            if not is_nonempty_str(revision.get("revisor")):
                errors.append(f"{path}.revision_humana: estado APROBADO requiere 'revisor' identificado.")
            if not is_valid_iso_date(revision.get("fecha")):
                errors.append(f"{path}.revision_humana: estado APROBADO requiere 'fecha' ISO válida.")

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
        if reform.get("texto") not in (None, "") and reform.get("verificada") is True and not is_nonempty_str(reform.get("nuevo_claim_id")):
            errors.append(
                f"{path}.reformulacion_propuesta: no puede declararse 'verificada: true' sin "
                "'nuevo_claim_id' apuntando al claim que la re-verificó. Una reformulación con una "
                "nueva afirmación jurídica nunca hereda automáticamente las fuentes/estado del texto original."
            )

    # --- fuentes ---
    fuentes = claim.get("fuentes")
    fuente_ids = set()
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

    if errors:
        # Con fuentes mal formadas no tiene sentido seguir con las reglas de alcance/estado.
        return errors, warnings, None, None

    # --- reglas de alcance ---
    if alcance == "CAPA_C_NACIONAL" and not claim.get("jurisdiccion"):
        errors.append(f"{path}: Capa C (CAPA_C_NACIONAL) requiere 'jurisdiccion' con al menos un país.")

    if alcance == "CAPA_B_VARIABLE" and not claim.get("variaciones_materiales"):
        errors.append(f"{path}: Capa B (CAPA_B_VARIABLE) requiere 'variaciones_materiales'.")

    if alcance == "NO_DETERMINADO" and estado != "REQUIERE_INVESTIGACION":
        errors.append(
            f"{path}: alcance NO_DETERMINADO solo puede combinarse con estado REQUIERE_INVESTIGACION "
            f"(falta de investigación), no con {estado!r}. Si la investigación SÍ concluyó algo firme "
            "(p. ej. una atribución refutada), usa NO_APLICA, no NO_DETERMINADO."
        )

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
                    errors.append(f"{path}.jurisdicciones_revisadas[{j_idx}]: debe ser {{'pais': str, 'fuente_ids': [ids de fuentes]}}.")
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
                if not isinstance(f_ids, list) or not f_ids:
                    errors.append(f"{path}.jurisdicciones_revisadas[{j_idx}] ({pais}): 'fuente_ids' no puede estar vacío — cada jurisdicción declarada necesita evidencia identificable.")
                else:
                    for fid in f_ids:
                        if fid not in fuente_ids:
                            errors.append(f"{path}.jurisdicciones_revisadas[{j_idx}] ({pais}): fuente_id {fid!r} no existe entre las 'fuentes' del claim.")
            if len(seen_normalized) < MIN_JURISDICCIONES_REVISADAS_CAPA_A:
                errors.append(
                    f"{path}: Capa A requiere al menos {MIN_JURISDICCIONES_REVISADAS_CAPA_A} jurisdicciones "
                    f"distintas y normalizadas con evidencia propia; hay {len(seen_normalized)}. "
                    "El conteo de países nunca sustituye la justificación comparada — ambas cosas se exigen."
                )

    if errors:
        return errors, warnings, None, None

    # --- reglas de suficiencia de fuentes vs. estado declarado ---
    max_estado = compute_max_estado_por_fuentes(fuentes)
    if estado in ESTADO_LADDER:
        declared_rank = ESTADO_LADDER.index(estado)
        max_rank = ESTADO_LADDER.index(max_estado)
        if declared_rank > max_rank:
            errors.append(
                f"{path}: estado declarado '{estado}' excede lo que las fuentes permiten "
                f"(máximo sostenible: '{max_estado}'). Ver niveles de fuente en references/source-policy.md."
            )
        if estado in ("APTO_CON_MATICES", "APTO_PARA_NARRATIVA") and claim.get("confianza") == "baja":
            errors.append(f"{path}: estado '{estado}' no puede tener confianza='baja'.")

    # --- gate a nivel de claim ---
    computed_gate = compute_claim_gate(claim, estado)
    declared_gate = claim.get("gate_arte")
    if declared_gate not in VALID_GATE:
        errors.append(f"{path}.gate_arte: inválido: {declared_gate!r} (debe ser CERRADO o ABIERTO).")
    elif declared_gate != computed_gate:
        errors.append(
            f"{path}.gate_arte: declarado '{declared_gate}' pero las reglas solo permiten '{computed_gate}' "
            "(requiere estado=APTO_PARA_NARRATIVA + revision_humana.estado=APROBADO + sin revisiones "
            "de plataforma/confidencialidad pendientes)."
        )

    return errors, warnings, max_estado, computed_gate


def compute_claim_gate(claim, estado):
    if estado != "APTO_PARA_NARRATIVA":
        return "CERRADO"
    revision = claim.get("revision_humana") or {}
    if revision.get("estado") != "APROBADO":
        return "CERRADO"
    if claim.get("platform_review_required") is True:
        return "CERRADO"
    if claim.get("confidentiality_review_required") is True:
        return "CERRADO"
    return "ABIERTO"


# ---------------------------------------------------------------------------
# Validación de una pieza (schema v2)
# ---------------------------------------------------------------------------

PIECE_REQUIRED_FIELDS = ["schema_version", "piece_id", "claims", "estado_agregado", "revisiones_pendientes", "gate_global_arte"]

ESTADO_AGREGADO_PRIORITY = [
    "BLOQUEADO",
    "REQUIERE_INVESTIGACION",
    "PENDIENTE_APROBACION_HUMANA",
    "APTO_CON_MATICES",
    "APTO_PARA_NARRATIVA",
]


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
        needs = (
            claim.get("estado") != "APTO_PARA_NARRATIVA"
            or revision.get("estado") != "APROBADO"
            or claim.get("platform_review_required") is True
            or claim.get("confidentiality_review_required") is True
        )
        if needs:
            pending.append(claim.get("claim_id"))
    return pending


def validate_piece(data, source_name):
    errors = []
    warnings = []

    if not isinstance(data, dict):
        return ["El paquete no es un objeto JSON (debe ser una PIEZA con schema_version/piece_id/claims/...)."], []

    for field in PIECE_REQUIRED_FIELDS:
        if field not in data:
            errors.append(f"Falta el campo obligatorio de nivel pieza: '{field}'.")
    if errors:
        return errors, warnings

    if data.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"'schema_version' debe ser {SCHEMA_VERSION!r}, no {data.get('schema_version')!r}.")
    if not is_nonempty_str(data.get("piece_id")):
        errors.append("'piece_id' debe ser un string no vacío.")

    claims = data.get("claims")
    if not isinstance(claims, list) or not claims:
        errors.append("'claims' debe ser una lista con al menos un claim.")
        return errors, warnings

    seen_claim_ids = set()
    claim_results = []
    for idx, claim in enumerate(claims):
        c_errors, c_warnings, max_estado, gate = validate_claim(claim, f"claims[{idx}]")
        errors.extend(c_errors)
        warnings.extend(c_warnings)
        if isinstance(claim, dict) and is_nonempty_str(claim.get("claim_id")):
            cid = claim["claim_id"]
            if cid in seen_claim_ids:
                errors.append(f"claim_id duplicado dentro de la pieza: {cid!r}.")
            seen_claim_ids.add(cid)
        claim_results.append(claim if isinstance(claim, dict) else {})

    # Referencias cruzadas de reformulacion_propuesta.nuevo_claim_id -> debe existir en la pieza.
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
            f"'estado_agregado' declarado como {declared_estado_agregado!r} pero el cálculo real, "
            f"a partir de los estados de los claims {claim_estados}, da {computed_estado_agregado!r}. "
            "El estado agregado nunca se escribe a mano: se calcula."
        )

    computed_pending = sorted(compute_revisiones_pendientes(claim_results))
    declared_pending = data.get("revisiones_pendientes")
    if not isinstance(declared_pending, list) or sorted(declared_pending) != computed_pending:
        errors.append(
            f"'revisiones_pendientes' declarado como {declared_pending!r} pero el cálculo real da "
            f"{computed_pending!r}."
        )

    claim_gates = [c.get("gate_arte") for c in claim_results]
    computed_gate_global = "ABIERTO" if (
        computed_estado_agregado == "APTO_PARA_NARRATIVA" and claim_gates and all(g == "ABIERTO" for g in claim_gates)
    ) else "CERRADO"
    declared_gate_global = data.get("gate_global_arte")
    if declared_gate_global not in VALID_GATE:
        errors.append(f"'gate_global_arte' inválido: {declared_gate_global!r}.")
    elif declared_gate_global != computed_gate_global:
        errors.append(
            f"'gate_global_arte' declarado como {declared_gate_global!r} pero el cálculo real da "
            f"{computed_gate_global!r} (todos los claims deben estar en APTO_PARA_NARRATIVA con su "
            "propio gate_arte=ABIERTO para que el gate global se abra)."
        )

    return errors, warnings


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def validate_file(path: Path):
    """Devuelve (ok: bool, tags: list[str], lines: list[str])."""
    try:
        text = path.read_text(encoding="utf-8")
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        return False, [Tag.ERROR], [f"{Tag.ERROR} {path}: JSON mal formado — {exc}"]
    except OSError as exc:
        return False, [Tag.ERROR], [f"{Tag.ERROR} {path}: no se pudo leer — {exc}"]

    errors, warnings = validate_piece(data, str(path))

    lines = []
    if errors:
        lines.append(f"{Tag.ERROR} {path}")
        for e in errors:
            lines.append(f"  - {e}")
        return False, [Tag.ERROR], lines

    for w in warnings:
        lines.append(f"{Tag.WARNING} {path}: {w}")

    gate = data.get("gate_global_arte")
    estado_agregado = data.get("estado_agregado")
    if gate == "ABIERTO":
        lines.append(f"{Tag.GATE_OPEN} {path}: estado_agregado={estado_agregado}, todas las afirmaciones verificadas y aprobadas por un humano.")
        tags = [Tag.GATE_OPEN] + ([Tag.WARNING] if warnings else [])
    else:
        pending = data.get("revisiones_pendientes") or []
        if estado_agregado in ("REQUIERE_INVESTIGACION", "BLOQUEADO"):
            lines.append(f"{Tag.GATE_CLOSED} {path}: estado_agregado={estado_agregado}.")
            tags = [Tag.GATE_CLOSED] + ([Tag.WARNING] if warnings else [])
        else:
            lines.append(f"{Tag.OK_PENDING_HUMAN} {path}: estructuralmente correcto, gate cerrado a la espera de: {pending}.")
            lines.append(f"{Tag.GATE_CLOSED} {path}")
            tags = [Tag.OK_PENDING_HUMAN, Tag.GATE_CLOSED] + ([Tag.WARNING] if warnings else [])

    return True, tags, lines


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
        ok, _tags, lines = validate_file(path)
        for line in lines:
            print(line)
        if not ok:
            overall_ok = False

    return 0 if overall_ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
