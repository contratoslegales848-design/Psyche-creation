#!/usr/bin/env python3
"""Valida la ESTRUCTURA de un paquete de verificación jurídica de LegalMente.

No decide si una afirmación jurídica es correcta. Solo confirma que el
paquete JSON está completo, bien formado y es coherente consigo mismo,
según el esquema descrito en references/claim-packet-schema.md.

El artefacto validado por máquina es JSON (biblioteca estándar `json`,
sin dependencias externas y sin parser YAML propio). Un paquete puede
mostrarse a un humano como YAML o como texto legible en otra parte del
flujo, pero lo que este script valida es siempre el .json.

Uso:
    python3 validate-claim-packet.py archivo1.json [archivo2.json ...]

Código de salida:
    0 si TODOS los paquetes son válidos.
    1 si al menos un paquete tiene errores estructurales o el JSON
      está mal formado.
"""

import json
import sys
from pathlib import Path

REQUIRED_FIELDS = [
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
    "apto_para_arte",
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

VALID_CONFIANZA = {"alta", "media", "baja"}
VALID_RIESGO = {"ninguno", "bajo", "medio", "alto"}

APTO_ESTADOS = {"APTO_PARA_NARRATIVA", "APTO_CON_MATICES"}
# Confianza insuficiente para dejar una pieza en estado apto.
INSUFFICIENT_CONFIANZA_FOR_APTO = {"baja"}

FUENTE_REQUIRED = {"titulo", "organismo_autor", "url", "fecha_consulta", "tipo_fuente"}

# Campos que Capa A debe justificar explícitamente (Paso 5 de la revisión):
# no basta con 1-2 jurisdicciones, hace falta evidencia comparada real.
CAPA_A_JUSTIFICATION_FIELDS = [
    "jurisdicciones_revisadas",
    "diferencias_buscadas",
    "contraejemplos_encontrados",
    "justificacion_suficiencia_comparada",
]

MIN_JURISDICCIONES_REVISADAS_CAPA_A = 3


def load_packet(path: Path):
    text = path.read_text(encoding="utf-8")
    return json.loads(text)  # puede lanzar json.JSONDecodeError


def as_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def validate_packet(data):
    errors = []

    if not isinstance(data, dict):
        return ["El paquete no es un objeto JSON (debe ser un objeto con las claves del esquema)."]

    for field in REQUIRED_FIELDS:
        if field not in data or data[field] in (None, "", []):
            errors.append(f"Campo obligatorio ausente o vacío: '{field}'")

    if errors:
        # Sin los campos base no tiene sentido evaluar las dependencias.
        return errors

    alcance = data.get("alcance")
    if alcance not in VALID_ALCANCE:
        errors.append(f"'alcance' inválido: {alcance!r} (debe ser uno de {sorted(VALID_ALCANCE)})")

    ubicacion = data.get("ubicacion")
    if ubicacion not in VALID_UBICACION:
        errors.append(f"'ubicacion' inválida: {ubicacion!r} (debe ser una de {sorted(VALID_UBICACION)})")

    estado = data.get("estado")
    if estado not in VALID_ESTADO:
        errors.append(f"'estado' inválido: {estado!r} (debe ser uno de {sorted(VALID_ESTADO)})")

    if data.get("confianza") not in VALID_CONFIANZA:
        errors.append(f"'confianza' inválida: {data.get('confianza')!r}")

    if data.get("riesgo_falsa_universalizacion") not in VALID_RIESGO:
        errors.append(f"'riesgo_falsa_universalizacion' inválido: {data.get('riesgo_falsa_universalizacion')!r}")

    if data.get("riesgo_asesoria") not in VALID_RIESGO:
        errors.append(f"'riesgo_asesoria' inválido: {data.get('riesgo_asesoria')!r}")

    for bool_field in (
        "platform_review_required",
        "confidentiality_review_required",
        "apto_para_arte",
        "revisor_humano_requerido",
    ):
        if not isinstance(data.get(bool_field), bool):
            errors.append(f"'{bool_field}' debe ser booleano (true/false), no {data.get(bool_field)!r}")

    # Esta skill nunca es la última palabra: revisor humano siempre requerido.
    if data.get("revisor_humano_requerido") is False:
        errors.append(
            "'revisor_humano_requerido' no puede ser false — esta skill nunca aprueba de forma definitiva, "
            "todo paquete requiere revisión humana."
        )

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

    # Capa A exige justificación comparada explícita — no basta con 1-2 países
    # ni con la ausencia de contradicción conocida sin haberla buscado.
    if alcance == "CAPA_A_TRANSVERSAL":
        missing = [f for f in CAPA_A_JUSTIFICATION_FIELDS if not data.get(f)]
        if missing:
            errors.append(
                "Capa A (CAPA_A_TRANSVERSAL) requiere justificación comparada explícita; "
                f"faltan o están vacíos: {missing}"
            )
        else:
            jurisdicciones = as_list(data.get("jurisdicciones_revisadas"))
            if len(jurisdicciones) < MIN_JURISDICCIONES_REVISADAS_CAPA_A:
                errors.append(
                    "Capa A requiere evidencia comparada suficiente: "
                    f"'jurisdicciones_revisadas' tiene {len(jurisdicciones)} entrada(s), "
                    f"se esperan al menos {MIN_JURISDICCIONES_REVISADAS_CAPA_A}."
                )

    # Estados aptos exigen al menos una fuente válida y confianza suficiente.
    if estado in APTO_ESTADOS:
        if data.get("confianza") in INSUFFICIENT_CONFIANZA_FOR_APTO:
            errors.append(
                f"Estado '{estado}' no puede tener confianza='{data.get('confianza')}' "
                "(confianza insuficiente para un estado apto)."
            )

        fuentes = data.get("fuentes")
        if not fuentes or not isinstance(fuentes, list):
            errors.append(f"Estado '{estado}' requiere al menos una fuente en 'fuentes'.")
        else:
            for idx, fuente in enumerate(fuentes):
                if not isinstance(fuente, dict):
                    errors.append(f"fuentes[{idx}] no es un objeto con campos (titulo/organismo_autor/url/...).")
                    continue
                missing = FUENTE_REQUIRED - set(k for k, v in fuente.items() if v not in (None, ""))
                if missing:
                    errors.append(f"fuentes[{idx}] incompleta, faltan: {sorted(missing)}")
                url = fuente.get("url") or ""
                titulo = fuente.get("titulo") or ""
                if not url and not titulo:
                    errors.append(f"fuentes[{idx}] no tiene 'url' ni 'titulo' suficiente para identificarla.")

    # apto_para_arte solo puede ser true cuando el estado es plenamente apto
    # para narrativa. Un paquete que aún requiere investigación, tiene
    # matices, está bloqueado o pendiente de humano NO puede marcarse listo
    # para producción visual.
    if data.get("apto_para_arte") is True and estado != "APTO_PARA_NARRATIVA":
        errors.append(
            f"'apto_para_arte' no puede ser true cuando estado='{estado}' "
            "(solo APTO_PARA_NARRATIVA puede pasar a producción visual)."
        )

    # PENDIENTE_APROBACION_HUMANA es, por definición, no apto para arte todavía.
    if estado == "PENDIENTE_APROBACION_HUMANA" and data.get("apto_para_arte") is True:
        errors.append("estado='PENDIENTE_APROBACION_HUMANA' es incoherente con apto_para_arte=true.")

    return errors


def main(argv):
    if not argv:
        print("Uso: validate-claim-packet.py archivo1.json [archivo2.json ...]", file=sys.stderr)
        return 1

    overall_ok = True
    for path_str in argv:
        path = Path(path_str)
        if not path.exists():
            print(f"[ERROR] {path_str}: archivo no encontrado")
            overall_ok = False
            continue

        try:
            data = load_packet(path)
        except json.JSONDecodeError as exc:
            print(f"[ERROR] {path_str}: JSON mal formado — {exc}")
            overall_ok = False
            continue

        errors = validate_packet(data)
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
