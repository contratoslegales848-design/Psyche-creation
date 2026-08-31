"""Puertas de entrada a la generacion visual.

Regla central (mandato §10, §16 y CLAUDE.md §3): este modulo **lee** el estado
canonico que produjo la verificacion juridica. No lo recalcula, no lo mejora y
no lo abre. Si el estado no se puede leer con certeza, cierra.

La autoridad juridica vive en
`.claude/skills/legalmente-legal-verification/` (claim packet, gate_arte,
ProductionHandoff). Aqui solo se decide si una pieza ya autorizada puede entrar
al pipeline visual.
"""

import importlib.util
import sys
from dataclasses import dataclass, field
from pathlib import Path

_SKILL_SCRIPTS = Path(__file__).resolve().parent.parent / ".claude" / "skills" / \
    "legalmente-legal-verification" / "scripts"


def _cargar_compute_content_hash():
    """Importa la funcion canonica de hash desde el validador de la skill.

    No se reimplementa aqui: reusar la MISMA funcion que aprueba los claims es
    lo unico que garantiza que "el hash cambio" signifique lo mismo en los dos
    sitios. Perezoso y opcional: si no esta disponible, el llamador decide.
    """
    ruta = _SKILL_SCRIPTS / "validate-claim-packet.py"
    if not ruta.is_file():
        return None
    nombre = "legalmente_validate_claim_packet"
    if nombre in sys.modules:
        return getattr(sys.modules[nombre], "compute_content_hash", None)
    if str(_SKILL_SCRIPTS) not in sys.path:
        sys.path.insert(0, str(_SKILL_SCRIPTS))
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    if spec is None or spec.loader is None:
        return None
    modulo = importlib.util.module_from_spec(spec)
    sys.modules[nombre] = modulo
    try:
        spec.loader.exec_module(modulo)
    except Exception:
        del sys.modules[nombre]
        return None
    return getattr(modulo, "compute_content_hash", None)

# Unico estado de handoff que habilita produccion visual.
HANDOFF_STATUS_PRODUCIBLE = "APROBADO_QA"

# Modos de procedencia de content/*.json (src/types.ts).
MODO_GOBERNADO = "GOBERNADO"
MODO_NO_APLICA = "NO_APLICA"
MODO_EJEMPLO_TECNICO = "EJEMPLO_TECNICO"


@dataclass
class GateDecision:
    """Resultado de una puerta. `permitido` nunca es True por omision."""

    permitido: bool = False
    motivos: list = field(default_factory=list)

    def __bool__(self):
        return self.permitido


def _cerrar(*motivos):
    return GateDecision(permitido=False, motivos=list(motivos))


def can_enter_visual_generation(procedencia, handoff=None, claim_packet=None):
    """¿Puede esta pieza entrar a generacion visual?

    `procedencia` es el bloque `procedencia` de un artefacto de content/.
    `handoff` es el ProductionHandoff ya validado por
    validate-publication-chain.py, o None si no se aporto.
    `claim_packet` es el claim packet REAL (dict cargado de
    pilot/claim-packets/*.json), cuando el llamador lo tiene disponible —
    resolver.py siempre lo tiene. Si se aporta, el hash que la pieza declara
    para cada claim se contrasta contra el hash REAL de la aprobacion humana
    en el paquete; una pieza no puede autoafirmar un hash aprobado que el
    canon no respalda. Si no se aporta (p. ej. en pruebas con fixtures
    sinteticos), el comportamiento es el de siempre: se confia en la forma del
    dato, no en su contenido contra disco.

    Falla cerrado ante: procedencia ausente, modo desconocido, campo canonico
    ausente, handoff ausente, handoff en un estado que no autoriza producir, o
    (con claim_packet) un hash que no coincide con la aprobacion humana real.
    """
    if not isinstance(procedencia, dict):
        return _cerrar("Sin bloque 'procedencia': un artefacto sin origen no entra al pipeline visual.")

    modo = procedencia.get("modo")

    if modo == MODO_EJEMPLO_TECNICO:
        return _cerrar(
            "modo EJEMPLO_TECNICO: material de prueba del pipeline, nunca material generable como pieza."
        )

    if modo == MODO_NO_APLICA:
        # NO_APLICA exige autorizacion humana explicita registrada en el artefacto.
        faltantes = [
            c for c in ("motivo_no_aplica", "autorizado_por", "fecha_autorizacion")
            if not str(procedencia.get(c) or "").strip()
        ]
        if faltantes:
            return _cerrar(
                "modo NO_APLICA sin autorizacion humana completa; faltan: " + ", ".join(faltantes)
            )
        return GateDecision(True, ["modo NO_APLICA con autorizacion humana registrada."])

    if modo != MODO_GOBERNADO:
        return _cerrar(f"modo de procedencia desconocido o ausente: {modo!r}. Estado canonico no legible -> cierra.")

    # --- modo GOBERNADO ---
    handoff_id = str(procedencia.get("handoff_id") or "").strip()
    if not handoff_id:
        return _cerrar("modo GOBERNADO sin 'handoff_id': no hay produccion autorizada que consumir.")

    claims = procedencia.get("claims")
    if not isinstance(claims, list) or not claims:
        return _cerrar("modo GOBERNADO sin claims ligados: sin hash aprobado no hay procedencia verificable.")
    for i, c in enumerate(claims):
        if not isinstance(c, dict) or not str(c.get("claim_id") or "").strip() \
                or not str(c.get("approved_claim_hash") or "").strip():
            return _cerrar(f"claim #{i} incompleto: exige 'claim_id' y 'approved_claim_hash'.")

    if claim_packet is not None:
        motivo = _verificar_hashes_contra_paquete(claims, claim_packet)
        if motivo:
            return _cerrar(motivo)

    if handoff is None:
        return _cerrar(
            f"handoff {handoff_id!r} no aportado. El pipeline visual no infiere el estado de produccion: "
            "sin el registro no se abre."
        )
    if not isinstance(handoff, dict):
        return _cerrar("handoff con forma invalida.")

    if handoff.get("handoff_id") != handoff_id:
        return _cerrar(
            f"el handoff aportado ({handoff.get('handoff_id')!r}) no es el declarado por la pieza ({handoff_id!r})."
        )
    if handoff.get("content_id") != procedencia.get("content_id"):
        return _cerrar("content_id de la pieza y del handoff no coinciden.")

    status = handoff.get("status")
    if status != HANDOFF_STATUS_PRODUCIBLE:
        return _cerrar(
            f"handoff en status {status!r}; solo {HANDOFF_STATUS_PRODUCIBLE!r} autoriza produccion visual."
        )

    # El handoff solo existe si el validador canonico vio gate_arte ABIERTO
    # (validate-publication-chain.py §validate_handoff). No se re-deriva aqui.
    return GateDecision(True, [f"handoff {handoff_id!r} en {status}."])


def _verificar_hashes_contra_paquete(claims_declarados, claim_packet):
    """Contrasta los hashes que la pieza declara contra el paquete real.

    Una pieza no puede autoafirmar un `approved_claim_hash` que el claim
    packet no respalda: exige que el claim exista en el paquete, este
    APROBADO por un humano, y que el hash coincida EXACTAMENTE con el que
    quedo registrado en esa aprobacion. Devuelve el motivo de cierre, o None
    si todo coincide.

    Ademas, cuando esta disponible, recalcula el hash REAL y actual del claim
    con la misma funcion canonica que usa el validador (`compute_content_hash`)
    y lo compara contra el snapshot congelado en la aprobacion. Sin esto, un
    claim que mutara DESPUES de aprobado (con el snapshot de la aprobacion sin
    refrescar) seguiria abriendo el gate: el snapshot y el declarado
    coincidirian entre si sin que ninguno de los dos reflejara ya el contenido
    real. Es exactamente el ataque que scripts/validate-content-provenance.py
    bloquea a nivel de artefacto; aqui se cierra la misma puerta a nivel de gate,
    para los llamadores que no pasan por ese script (p. ej. resolver.py).
    """
    if not isinstance(claim_packet, dict):
        return "claim_packet con forma invalida: no se puede verificar contra el canon."
    por_id = {
        c.get("claim_id"): c for c in (claim_packet.get("claims") or [])
        if isinstance(c, dict)
    }
    compute_content_hash = _cargar_compute_content_hash()
    for c in claims_declarados:
        cid, declarado = c.get("claim_id"), c.get("approved_claim_hash")
        real = por_id.get(cid)
        if real is None:
            return f"claim {cid!r} no existe en el claim packet real: no se autoafirma un claim ajeno."
        rev = real.get("revision_humana") or {}
        if rev.get("estado") != "APROBADO":
            return f"claim {cid!r} no tiene revision_humana.estado=APROBADO en el canon real."
        real_hash = rev.get("contenido_hash_sha256")
        if not real_hash or declarado != real_hash:
            return (f"claim {cid!r}: el hash declarado no coincide con el hash de la aprobacion "
                    "humana real. Una pieza no puede autoafirmar un hash que el canon no respalda.")
        if compute_content_hash is not None:
            try:
                actual = compute_content_hash(real)
            except Exception:
                return (f"claim {cid!r}: no se pudo recalcular el hash actual del claim; "
                        "fail-closed ante un canon que no se puede verificar.")
            if actual != real_hash:
                return (f"claim {cid!r}: el contenido del claim cambio despues de la aprobacion "
                        "(el hash actual ya no coincide con el snapshot aprobado). "
                        "Una aprobacion vieja no puede autorizar canon nuevo en silencio.")
    return None


def requires_human_visual_review(qa_report):
    """La revision humana visual es obligatoria SIEMPRE.

    El QA automatico puede anadir motivos, nunca puede retirarlos. No existe
    ninguna ruta por la que un asset llegue a produccion sin firma humana
    (CLAUDE.md §4, mandato §4).
    """
    motivos = ["La aprobacion visual final es siempre humana; el QA automatico no la sustituye."]
    if qa_report is not None and not qa_report.passed:
        motivos.extend(f"QA estructural fallido: {p}" for p in qa_report.problemas)
    return motivos


def can_enter_production(gate, qa_report, human_visual_approval):
    """Ultimo cierre: nada entra a produccion sin gate + QA + firma humana."""
    if not gate or not gate.permitido:
        return _cerrar("gate de entrada visual cerrado.")
    if qa_report is None or not qa_report.passed:
        return _cerrar("QA estructural no superado.")
    if human_visual_approval is not True:
        return _cerrar("falta aprobacion visual humana explicita.")
    return GateDecision(True, ["gate abierto, QA superado y aprobacion humana registrada."])
