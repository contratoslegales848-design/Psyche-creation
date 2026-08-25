#!/usr/bin/env python3
"""Valida la ESTRUCTURA de un paquete de verificación jurídica de LegalMente.

No decide si una afirmación jurídica es correcta. Solo confirma que el
paquete YAML está completo, bien formado y es coherente consigo mismo,
según el esquema descrito en references/claim-packet-schema.md.

Sin dependencias externas (no requiere PyYAML): implementa un parser
mínimo suficiente para el subconjunto de YAML que usan estos paquetes
(mapas simples, listas de escalares, listas de mapas con "- clave: valor").

Uso:
    python3 validate-claim-packet.py archivo1.yaml [archivo2.yaml ...]

Código de salida:
    0 si TODOS los paquetes son válidos.
    1 si al menos un paquete tiene errores estructurales.
"""

import sys
from pathlib import Path

REQUIRED_SCALAR_FIELDS = [
    "claim_id",
    "texto_exacto",
    "ubicacion",
    "tipo",
    "alcance",
    "confianza",
    "riesgo_falsa_universalizacion",
    "riesgo_asesoria",
    "platform_review_required",
    "confidentiality_review_required",
    "estado",
    "revisor_humano_requerido",
]

VALID_ALCANCE = {
    "CAPA_A_TRANSVERSAL",
    "CAPA_B_VARIABLE",
    "CAPA_C_NACIONAL",
    "NO_DETERMINADO",
}

VALID_ESTADO = {
    "APTO_PARA_NARRATIVA",
    "APTO_CON_MATICES",
    "REQUIERE_INVESTIGACION",
    "BLOQUEADO",
    "PENDIENTE_APROBACION_HUMANA",
}

VALID_CONFIANZA = {"alta", "media", "baja"}
VALID_RIESGO = {"ninguno", "bajo", "medio", "alto"}
VALID_BOOL = {"true", "false"}

APTO_ESTADOS = {"APTO_PARA_NARRATIVA", "APTO_CON_MATICES"}

FUENTE_REQUIRED = {"titulo", "organismo_autor", "url", "fecha_consulta", "tipo_fuente"}


class ParseError(Exception):
    pass


def strip_quotes(value):
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        return value[1:-1]
    return value


def parse_claim_packet(text):
    """Parser mínimo para el subconjunto de YAML usado por estos paquetes.

    Soporta:
      clave: valor
      clave:
        - valor escalar
      clave:
        - subclave: valor
          subclave2: valor
    No soporta YAML arbitrario a propósito: el objetivo es un formato
    predecible y fácil de auditar, no un parser YAML de propósito general.
    """
    data = {}
    lines = text.splitlines()
    i = 0
    n = len(lines)

    def indent_of(line):
        return len(line) - len(line.lstrip(" "))

    while i < n:
        raw = lines[i]
        line = raw.rstrip()
        if not line.strip() or line.strip().startswith("#"):
            i += 1
            continue
        if indent_of(line) != 0:
            raise ParseError(f"Línea {i + 1}: indentación inesperada en nivel raíz: {raw!r}")
        if ":" not in line:
            raise ParseError(f"Línea {i + 1}: se esperaba 'clave: valor' o 'clave:': {raw!r}")
        key, _, rest = line.partition(":")
        key = key.strip()
        rest = rest.strip()
        i += 1
        if rest:
            data[key] = strip_quotes(rest)
            continue

        # Bloque: puede ser lista de escalares o lista de mapas.
        items = []
        while i < n:
            nxt = lines[i]
            if not nxt.strip():
                i += 1
                continue
            if indent_of(nxt) == 0:
                break
            stripped = nxt.strip()
            if not stripped.startswith("-"):
                raise ParseError(f"Línea {i + 1}: se esperaba un elemento de lista ('- ...'): {nxt!r}")
            after_dash = stripped[1:].strip()
            if ":" in after_dash:
                # Primer campo de un mapa dentro de la lista.
                sub = {}
                k0, _, v0 = after_dash.partition(":")
                sub[k0.strip()] = strip_quotes(v0.strip())
                base_indent = indent_of(nxt)
                i += 1
                while i < n:
                    cont = lines[i]
                    if not cont.strip():
                        i += 1
                        continue
                    if indent_of(cont) <= base_indent:
                        break
                    ck, _, cv = cont.strip().partition(":")
                    if ":" not in cont:
                        raise ParseError(f"Línea {i + 1}: se esperaba 'clave: valor' dentro de la lista: {cont!r}")
                    sub[ck.strip()] = strip_quotes(cv.strip())
                    i += 1
                items.append(sub)
            else:
                items.append(strip_quotes(after_dash))
                i += 1
        data[key] = items

    return data


def as_bool(value):
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() == "true"


def validate_packet(data, source_name):
    errors = []

    for field in REQUIRED_SCALAR_FIELDS:
        if field not in data or data[field] in (None, "", []):
            errors.append(f"Campo obligatorio ausente o vacío: '{field}'")

    if errors:
        # Sin los campos base no tiene sentido seguir validando dependencias.
        return errors

    alcance = data.get("alcance")
    if alcance not in VALID_ALCANCE:
        errors.append(f"'alcance' inválido: {alcance!r} (debe ser uno de {sorted(VALID_ALCANCE)})")

    estado = data.get("estado")
    if estado not in VALID_ESTADO:
        errors.append(f"'estado' inválido: {estado!r} (debe ser uno de {sorted(VALID_ESTADO)})")

    if data.get("confianza") not in VALID_CONFIANZA:
        errors.append(f"'confianza' inválida: {data.get('confianza')!r}")

    if data.get("riesgo_falsa_universalizacion") not in VALID_RIESGO:
        errors.append(f"'riesgo_falsa_universalizacion' inválido: {data.get('riesgo_falsa_universalizacion')!r}")

    if data.get("riesgo_asesoria") not in VALID_RIESGO:
        errors.append(f"'riesgo_asesoria' inválido: {data.get('riesgo_asesoria')!r}")

    for bool_field in ("platform_review_required", "confidentiality_review_required", "revisor_humano_requerido"):
        raw = str(data.get(bool_field)).strip().lower()
        if raw not in VALID_BOOL:
            errors.append(f"'{bool_field}' debe ser 'true' o 'false', no {data.get(bool_field)!r}")

    # Capa C exige jurisdicción.
    if alcance == "CAPA_C_NACIONAL":
        jurisdiccion = data.get("jurisdiccion")
        if not jurisdiccion:
            errors.append("Capa C (CAPA_C_NACIONAL) requiere el campo 'jurisdiccion' con al menos un país.")

    # Capa B exige variaciones materiales.
    if alcance == "CAPA_B_VARIABLE":
        variaciones = data.get("variaciones_materiales")
        if not variaciones:
            errors.append("Capa B (CAPA_B_VARIABLE) requiere el campo 'variaciones_materiales'.")

    # Estados aptos exigen al menos una fuente válida.
    if estado in APTO_ESTADOS:
        fuentes = data.get("fuentes")
        if not fuentes or not isinstance(fuentes, list):
            errors.append(f"Estado '{estado}' requiere al menos una fuente en 'fuentes'.")
        else:
            for idx, fuente in enumerate(fuentes):
                if not isinstance(fuente, dict):
                    errors.append(f"fuentes[{idx}] no es un registro con campos (titulo/organismo_autor/url/...).")
                    continue
                missing = FUENTE_REQUIRED - set(k for k, v in fuente.items() if v not in (None, ""))
                if missing:
                    errors.append(f"fuentes[{idx}] incompleta, faltan: {sorted(missing)}")
                url = fuente.get("url", "")
                titulo = fuente.get("titulo", "")
                if not url and not titulo:
                    errors.append(f"fuentes[{idx}] no tiene 'url' ni 'titulo' suficiente para identificarla — fuente inválida.")

    # PENDIENTE_APROBACION_HUMANA no puede tener revisor_humano_requerido=false.
    if estado == "PENDIENTE_APROBACION_HUMANA" and not as_bool(data.get("revisor_humano_requerido")):
        errors.append("estado='PENDIENTE_APROBACION_HUMANA' es incoherente con revisor_humano_requerido=false.")

    return errors


def main(argv):
    if not argv:
        print("Uso: validate-claim-packet.py archivo1.yaml [archivo2.yaml ...]", file=sys.stderr)
        return 1

    overall_ok = True
    for path_str in argv:
        path = Path(path_str)
        if not path.exists():
            print(f"[ERROR] {path_str}: archivo no encontrado")
            overall_ok = False
            continue

        text = path.read_text(encoding="utf-8")
        try:
            data = parse_claim_packet(text)
        except ParseError as exc:
            print(f"[ERROR] {path_str}: paquete mal formado — {exc}")
            overall_ok = False
            continue

        errors = validate_packet(data, path_str)
        if errors:
            overall_ok = False
            print(f"[BLOQUEADO ESTRUCTURALMENTE] {path_str}")
            for err in errors:
                print(f"  - {err}")
        else:
            estado = data.get("estado")
            print(f"[OK] {path_str}: paquete completo y coherente (estado declarado: {estado})")

    return 0 if overall_ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
