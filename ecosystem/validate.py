"""Validacion determinista del ecosistema + inyeccion de fallos.

Regla del prompt de integracion §11: cada fallo debe terminar en HOLD, REJECT,
FIX_REQUIRED o REVIEW_REQUIRED, nunca en una aprobacion silenciosa. Y no basta
con que un archivo exista: hay que comprobar conteos, IDs, referencias
cruzadas, campos obligatorios, duplicados, estados compatibles y reversibilidad.

Sin red. Sin escritura. Determinista: la misma copia del repositorio produce
siempre el mismo informe.
"""

from dataclasses import dataclass

from . import gate_matrix, help_protocols, registry, relations

HOLD = "HOLD"
REJECT = "REJECT"
FIX_REQUIRED = "FIX_REQUIRED"
REVIEW_REQUIRED = "REVIEW_REQUIRED"

SEVERITIES = frozenset({HOLD, REJECT, FIX_REQUIRED, REVIEW_REQUIRED})

# Tokens que jamas deben aparecer en el registro: convertirian una preparacion
# interna en una autorizacion.
FORBIDDEN_TOKENS = (
    "PUBLICATION_AUTHORIZED",
    "PUBLICADO",
    "APPROVED_FOR_PUBLICATION",
    "AUTO_PUBLISH",
    "DEPLOY_NOW",
)


@dataclass(frozen=True)
class Finding:
    code: str
    severity: str
    object_id: str
    detail: str


def _check_unique_ids(objects) -> list[Finding]:
    seen: dict[str, int] = {}
    for obj in objects:
        seen[obj.object_id] = seen.get(obj.object_id, 0) + 1
    return [
        Finding("DUPLICATE_OBJECT_ID", REJECT, oid, f"aparece {count} veces en el registro.")
        for oid, count in seen.items() if count > 1
    ]


def _check_mandatory_fields(objects) -> list[Finding]:
    findings: list[Finding] = []
    for obj in objects:
        if not obj.owner.strip():
            findings.append(Finding("MISSING_OWNER", FIX_REQUIRED, obj.object_id,
                                    "todo objeto debe declarar un responsable."))
        if not obj.next_action.strip():
            findings.append(Finding("MISSING_NEXT_ACTION", FIX_REQUIRED, obj.object_id,
                                    "todo objeto debe declarar su siguiente accion."))
        if obj.declared_state not in registry.DECLARABLE_STATES:
            findings.append(Finding("UNKNOWN_STATE", REJECT, obj.object_id,
                                    f"estado '{obj.declared_state}' fuera del vocabulario cerrado."))
        if obj.layer not in registry.LAYERS:
            findings.append(Finding("UNKNOWN_LAYER", REJECT, obj.object_id,
                                    f"capa '{obj.layer}' fuera del modelo unificado."))
    return findings


def _check_drift(objects) -> list[Finding]:
    """Un objeto que dice existir y no existe es deriva documental."""
    findings: list[Finding] = []
    for obj in objects:
        if obj.declared_state in registry.TERMINAL_ABSENT_STATES:
            continue
        if obj.resolve_state() == registry.MISSING_ARTIFACT:
            findings.append(Finding(
                "DECLARED_BUT_ABSENT", HOLD, obj.object_id,
                f"declara estado {obj.declared_state} y su ruta '{obj.path}' no existe."))
    return findings


def _check_blocked_not_canonical(objects) -> list[Finding]:
    findings: list[Finding] = []
    for obj in objects:
        if obj.blockers and obj.declared_state == registry.CANONICAL and obj.object_id != "PSY-VIS-ENGINE":
            findings.append(Finding(
                "BLOCKED_YET_CANONICAL", REVIEW_REQUIRED, obj.object_id,
                f"declara CANONICAL con bloqueos activos: {', '.join(obj.blockers)}."))
    return findings


def _check_forbidden_tokens(objects) -> list[Finding]:
    findings: list[Finding] = []
    for obj in objects:
        blob = " ".join((obj.label, obj.notes, obj.next_action, obj.declared_state))
        for token in FORBIDDEN_TOKENS:
            if token in blob:
                findings.append(Finding(
                    "FORBIDDEN_PUBLICATION_TOKEN", REJECT, obj.object_id,
                    f"contiene el token prohibido '{token}'."))
    return findings


def _check_relations_resolve(objects) -> list[Finding]:
    """Toda relacion de ecosistema debe apuntar a un objeto conocido.

    Se exceptuan los destinos externos documentados, que no son objetos del
    registro sino nodos del grafo heredado o del mundo real.
    """
    known = {obj.object_id for obj in objects}
    external = {
        "publication_decision", "distribution_linkedin", "HELP-001..005", "ecosystem",
    }
    findings: list[Finding] = []
    for link in relations.ecosystem_links():
        for endpoint in (link["source"], link["target"]):
            if endpoint in known or endpoint in external:
                continue
            findings.append(Finding(
                "DANGLING_RELATION", FIX_REQUIRED, endpoint,
                f"la relacion {link['source']} -> {link['target']} apunta a un objeto desconocido."))
        if link["state"] not in relations.RELATION_STATES:
            findings.append(Finding(
                "UNKNOWN_RELATION_STATE", REJECT, link["target"],
                f"estado de relacion '{link['state']}' fuera del vocabulario."))
    return findings


def _check_gates() -> list[Finding]:
    findings = [
        Finding("GATE_CHAINING", REJECT, "GATE_MATRIX", violation)
        for violation in gate_matrix.chaining_violations()
    ]
    if not gate_matrix.human_gates():
        findings.append(Finding(
            "NO_HUMAN_GATE", REJECT, "GATE_MATRIX",
            "un ecosistema sin gate humano no puede publicar nada con seguridad."))
    return findings


def _check_help_protocols() -> list[Finding]:
    findings: list[Finding] = []
    for pid in help_protocols.protocols_without_stop_condition():
        findings.append(Finding(
            "HELP_WITHOUT_STOP", REJECT, pid,
            "un protocolo de ayuda sin condicion de parada no es publicable."))
    for pid in help_protocols.protocols_bearing_claims():
        findings.append(Finding(
            "HELP_BEARS_CLAIM", HOLD, pid,
            "un protocolo con claim o copy exacto exige fuente, territorio y vigencia."))
    return findings


def validate(objects=None) -> list[Finding]:
    """Informe completo. Lista vacia significa: sin hallazgos, no 'aprobado'."""
    objects = objects if objects is not None else registry.ALL_OBJECTS
    findings: list[Finding] = []
    findings.extend(_check_unique_ids(objects))
    findings.extend(_check_mandatory_fields(objects))
    findings.extend(_check_drift(objects))
    findings.extend(_check_blocked_not_canonical(objects))
    findings.extend(_check_forbidden_tokens(objects))
    findings.extend(_check_relations_resolve(objects))
    findings.extend(_check_gates())
    findings.extend(_check_help_protocols())
    return findings


def summary() -> dict:
    findings = validate()
    resolved = registry.resolved_registry()
    counts: dict[str, int] = {}
    for _, state in resolved:
        counts[state] = counts.get(state, 0) + 1
    return {
        "objetos_totales": len(resolved),
        "por_estado": dict(sorted(counts.items())),
        "hallazgos": len(findings),
        "por_severidad": {
            sev: len([f for f in findings if f.severity == sev]) for sev in sorted(SEVERITIES)
        },
        "gates_existentes": len(gate_matrix.gates_that_exist()),
        "gates_totales": len(gate_matrix.GATE_MATRIX),
        "protocolos_ayuda": len(help_protocols.HELP_PROTOCOLS),
        "huecos_de_integracion": len(relations.integration_gaps()),
        "estado_publicacion": "NOT_PUBLISHED",
    }


if __name__ == "__main__":  # pragma: no cover
    import json

    report = summary()
    print(json.dumps(report, indent=2, ensure_ascii=False))
    for finding in validate():
        print(f"[{finding.severity}] {finding.code} {finding.object_id}: {finding.detail}")
