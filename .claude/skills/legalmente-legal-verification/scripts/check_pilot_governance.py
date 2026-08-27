#!/usr/bin/env python3
"""Control de gobernanza para los paquetes reales del piloto (no fixtures).

Verifica que el gate de arte declarado en cada claim y en la pieza COINCIDA
EXACTAMENTE con el que las reglas fail-closed del validador permiten — ni
abierto de más, ni cerrado de menos.

Semántica fijada por decisión del fundador (2026-08-27):

  - `APTO_PARA_NARRATIVA` significa que la evidencia permite SOMETER el claim
    a aprobación humana. No es una aprobación.
  - `revision_humana.estado = APROBADO` significa que un humano aprobó
    exactamente el contenido ligado al hash canónico. No abre nada por sí solo.
  - `gate_arte = ABIERTO` significa EXCLUSIVAMENTE que puede comenzar la
    narrativa y la producción visual.
  - `gate_arte = ABIERTO` **NO** constituye autorización de publicación. La
    publicación exige una decisión humana posterior, externa y separada, que
    este repositorio todavía no implementa como control. Mientras ese control
    no exista, ninguna skill, workflow o agente tiene autorización para
    publicar.

Por qué este archivo cambió (deadlock corregido): la versión anterior exigía
`gate_arte = CERRADO` de forma INCONDICIONAL en todo el piloto. En cuanto un
claim alcanzó `APTO_PARA_NARRATIVA`, registrar la aprobación humana pasó a ser
imposible sin dejar CI en rojo: el validador OBLIGA a declarar `ABIERTO`
(un gate declarado `CERRADO` cuando las reglas dan `ABIERTO` es
`[ERROR ESTRUCTURAL]`), mientras esta gobernanza OBLIGABA a `CERRADO`. Ambos
programas corren en el mismo job de CI, así que ninguna combinación pasaba.
La causa de fondo era conceptual: se estaba usando el gate de ARTE como si
fuera un permiso de PUBLICACIÓN, congelándolo en `CERRADO` para impedir que
el piloto se publicara. Son dos cosas distintas y ahora se tratan como tales.

Qué comprueba entonces esta gobernanza, que el validador por sí solo no
subraya:

  1. `schema_version` exactamente "4.0".
  2. En el piloto, `revision_humana.estado` solo puede ser PENDIENTE o
     APROBADO.
  3. Una aprobación solo se acepta como legítima si está firmada de forma
     verificable: `revisor` y `fecha` ISO no vacíos y `contenido_hash_sha256`
     con 64 caracteres hexadecimales.
  4. El `gate_arte` declarado en cada claim coincide EXACTAMENTE con el gate
     canónico que calcula el validador, y el `gate_global_arte` declarado
     coincide con el agregado canónico de esos gates.

Fail-closed: cualquier incoherencia, cualquier claim estructuralmente
inválido y cualquier gate que no se pueda calcular se tratan como CERRADO y,
si se declaró ABIERTO, como rechazo.

NO reimplementa ninguna regla jurídica. La decisión de si un gate puede
abrirse la toma SIEMPRE `validate-claim-packet.py` a través de
`validate_claim()`; este archivo solo compara lo declarado contra esa
decisión y explica por qué. No existe una segunda implementación de
`compute_content_hash` ni de la lógica de gate — se importan del validador.

Ningún agente puede autoasignarse como revisor: que este script acepte una
firma no prueba que la escribiera un humano. Solo comprueba que la firma
exista, esté bien formada y ligue al contenido exacto.

Uso: python3 check_pilot_governance.py <archivo.json> [<archivo2.json> ...]
Sale con 0 si todos los archivos cumplen; con 1 si alguno no cumple o no es
JSON válido.
"""
import importlib.util
import json
import re
import sys
from pathlib import Path

HASH_HEX_64 = re.compile(r"^[0-9a-fA-F]{64}$")

VALIDATOR_PATH = Path(__file__).resolve().parent / "validate-claim-packet.py"

REVISION_ESTADOS_PILOTO = ("PENDIENTE", "APROBADO")


def load_validator(path=VALIDATOR_PATH):
    """Importa validate-claim-packet.py como módulo.

    El nombre del archivo lleva guiones, así que no puede importarse con un
    `import` normal: se carga explícitamente con importlib. Fail-closed: si el
    validador no está o no se puede cargar, esta gobernanza NO puede decidir
    nada y aborta con una excepción — nunca aprueba a ciegas.
    """
    module_name = "validate_claim_packet"
    cached = sys.modules.get(module_name)
    if cached is not None and getattr(cached, "__file__", None) == str(path):
        return cached
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"No se pudo preparar la importación del validador en {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def canonical_gate_arte(validator, claim, path):
    """Gate canónico de UN claim, decidido por el validador, no por aquí.

    `validate_claim` devuelve (errores, advertencias, techo_estado, gate). Ese
    cuarto valor ES la decisión fail-closed del validador. Devuelve None cuando
    el claim es tan incompleto que ni siquiera puede evaluarse; en ese caso se
    trata como CERRADO, que es la lectura fail-closed correcta: un claim
    estructuralmente inválido nunca puede tener el gate abierto.
    """
    _errors, _warnings, _techo, gate = validator.validate_claim(claim, path)
    return gate if gate in validator.VALID_GATE else "CERRADO"


def gate_closed_reasons(validator, claim):
    """Diagnóstico legible de POR QUÉ el gate canónico quedó cerrado.

    Es solo explicación para el humano que lee el fallo de CI: la decisión ya
    la tomó `canonical_gate_arte`. Reutiliza los helpers del validador; no
    reimplementa ninguna regla.
    """
    reasons = []
    revision = claim.get("revision_humana") or {}
    if claim.get("estado") != "APTO_PARA_NARRATIVA":
        reasons.append(f"estado={claim.get('estado')!r} (se exige 'APTO_PARA_NARRATIVA')")
    if revision.get("estado") != "APROBADO":
        reasons.append(f"revision_humana.estado={revision.get('estado')!r} (se exige 'APROBADO')")
    else:
        if not validator.is_nonempty_str(revision.get("revisor")):
            reasons.append("revision_humana.revisor ausente o vacío")
        if not validator.is_valid_iso_date(revision.get("fecha")):
            reasons.append("revision_humana.fecha ausente o no ISO")
        hash_val = revision.get("contenido_hash_sha256")
        if not (isinstance(hash_val, str) and HASH_HEX_64.match(hash_val)):
            reasons.append("revision_humana.contenido_hash_sha256 ausente o mal formado")
        elif hash_val != validator.compute_content_hash(claim):
            reasons.append(
                "revision_humana.contenido_hash_sha256 no coincide con el hash canónico del "
                "contenido actual: la aprobación no liga a este contenido"
            )
    if not validator.review_allows_gate(claim.get("platform_review") or {}):
        reasons.append("platform_review.status fuera de {NO_APLICA, APROBADO}")
    if not validator.review_allows_gate(claim.get("confidentiality_review") or {}):
        reasons.append("confidentiality_review.status fuera de {NO_APLICA, APROBADO}")
    if not reasons:
        reasons.append("el claim tiene errores estructurales que impiden abrir el gate")
    return reasons


def check_pilot_governance(piece, validator=None):
    """Devuelve una lista de problemas (vacía si todo está en orden)."""
    if validator is None:
        validator = load_validator()

    problems = []

    if piece.get("schema_version") != "4.0":
        problems.append(
            f"schema_version debe ser exactamente '4.0', es {piece.get('schema_version')!r}"
        )

    claims = piece.get("claims")
    if not isinstance(claims, list) or not claims:
        problems.append("'claims' debe ser una lista con al menos un claim.")
        return problems

    canonical_gates = []
    for idx, claim in enumerate(claims):
        if not isinstance(claim, dict):
            problems.append(f"claims[{idx}]: el claim no es un objeto JSON.")
            canonical_gates.append("CERRADO")
            continue

        claim_id = claim.get("claim_id")
        revision = claim.get("revision_humana") or {}
        estado_revision = revision.get("estado")

        # --- revisión humana: estados admitidos y firma verificable ---
        if estado_revision not in REVISION_ESTADOS_PILOTO:
            problems.append(
                f"claim {claim_id!r}: revision_humana.estado debe ser 'PENDIENTE' o 'APROBADO' "
                f"en el piloto, es {estado_revision!r}"
            )
        elif estado_revision == "APROBADO":
            if not validator.is_nonempty_str(revision.get("revisor")):
                problems.append(
                    f"claim {claim_id!r}: revision_humana.estado='APROBADO' requiere 'revisor' no vacío."
                )
            if not validator.is_valid_iso_date(revision.get("fecha")):
                problems.append(
                    f"claim {claim_id!r}: revision_humana.estado='APROBADO' requiere 'fecha' ISO válida."
                )
            hash_val = revision.get("contenido_hash_sha256")
            if not (isinstance(hash_val, str) and HASH_HEX_64.match(hash_val)):
                problems.append(
                    f"claim {claim_id!r}: revision_humana.estado='APROBADO' requiere "
                    "'contenido_hash_sha256' como 64 caracteres hexadecimales."
                )

        # --- gate de arte: debe coincidir con la decisión canónica del validador ---
        canonical = canonical_gate_arte(validator, claim, f"claims[{idx}]")
        canonical_gates.append(canonical)
        declared = claim.get("gate_arte")
        if declared not in validator.VALID_GATE:
            problems.append(
                f"claim {claim_id!r}: gate_arte inválido: {declared!r} "
                f"(debe ser uno de {sorted(validator.VALID_GATE)})."
            )
        elif declared != canonical:
            if canonical == "CERRADO":
                motivos = "; ".join(gate_closed_reasons(validator, claim))
                problems.append(
                    f"claim {claim_id!r}: gate_arte declarado 'ABIERTO' pero las reglas fail-closed "
                    f"del validador lo mantienen 'CERRADO' — {motivos}."
                )
            else:
                problems.append(
                    f"claim {claim_id!r}: gate_arte declarado 'CERRADO' pero las reglas del validador "
                    "obligan a 'ABIERTO' (estado APTO_PARA_NARRATIVA, aprobación humana firmada y hash "
                    "canónico coincidente). Un gate de arte abierto habilita narrativa y producción "
                    "visual; NO autoriza publicación, que sigue siendo una decisión humana separada."
                )

    # --- gate global: agregado canónico de los gates de claim ---
    # Misma regla que aplica el validador a nivel de pieza. Los insumos
    # (estado agregado y gates de claim) se obtienen de sus funciones reales,
    # no se recalculan aquí. La prueba
    # `test_gobernanza_y_validador_coinciden_en_gate_global` verifica que
    # ambos programas no puedan divergir en silencio.
    estado_agregado = validator.compute_estado_agregado(
        [c.get("estado") for c in claims if isinstance(c, dict)]
    )
    expected_global = (
        "ABIERTO"
        if (
            estado_agregado == "APTO_PARA_NARRATIVA"
            and canonical_gates
            and all(g == "ABIERTO" for g in canonical_gates)
        )
        else "CERRADO"
    )
    declared_global = piece.get("gate_global_arte")
    if declared_global not in validator.VALID_GATE:
        problems.append(
            f"gate_global_arte inválido: {declared_global!r} "
            f"(debe ser uno de {sorted(validator.VALID_GATE)})."
        )
    elif declared_global != expected_global:
        problems.append(
            f"gate_global_arte declarado {declared_global!r} pero el cálculo canónico da "
            f"{expected_global!r} (estado_agregado={estado_agregado!r}, "
            f"gates de claim={canonical_gates})."
        )

    return problems


def main(argv):
    if not argv:
        print("Uso: check_pilot_governance.py <archivo.json> [...]", file=sys.stderr)
        return 1
    try:
        validator = load_validator()
    except (ImportError, OSError, SyntaxError) as exc:
        print(f"FALLÓ: no se pudo cargar el validador canónico: {exc}", file=sys.stderr)
        return 1
    overall_ok = True
    for path in argv:
        try:
            with open(path, encoding="utf-8") as fh:
                piece = json.load(fh)
        except (OSError, json.JSONDecodeError) as exc:
            print(f"FALLÓ: no se pudo leer/parsear {path}: {exc}")
            overall_ok = False
            continue
        if not isinstance(piece, dict):
            print(f"FALLÓ el control de gobernanza del piloto para {path}:")
            print("  - el paquete no es un objeto JSON.")
            overall_ok = False
            continue
        problems = check_pilot_governance(piece, validator)
        if problems:
            print(f"FALLÓ el control de gobernanza del piloto para {path}:")
            for p in problems:
                print(f"  - {p}")
            overall_ok = False
        else:
            gate = piece.get("gate_global_arte")
            if gate == "ABIERTO":
                detalle = (
                    "gate de arte ABIERTO y coherente con las reglas del validador — habilita "
                    "narrativa y producción visual; NO autoriza publicación"
                )
            else:
                detalle = "gate de arte CERRADO y coherente con las reglas del validador"
            print(
                f"OK: {path} — schema_version 4.0, revision_humana PENDIENTE o APROBADA con firma "
                f"verificable, y {detalle}."
            )
    return 0 if overall_ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
