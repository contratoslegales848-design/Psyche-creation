"""Read-model de verificacion de fuentes sobre los claim packets REALES.

No es un segundo canon: lee `claims[].fuentes[].verificacion_fuente`, que ya
existe en pilot/claim-packets/*.json (esquema de la skill
legalmente-legal-verification), y deriva un resumen legible. Nunca escribe
sobre el claim packet, nunca cambia `revision_humana`, nunca abre un gate.

Distincion central del mandato de continuacion (§13-14):
  SOURCE_ACCESSIBLE   != CLAIM_LEGALLY_SUFFICIENT
  SOURCE_VERIFIED     != HUMAN_APPROVED
Este modulo solo calcula la primera mitad de cada par. La segunda mitad
(suficiencia juridica, aprobacion humana) nunca se deriva aqui.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path

DIRECT_SUPPORT = "DIRECT_SUPPORT"
NOT_VERIFIED = "NOT_VERIFIED"
INACCESSIBLE = "INACCESSIBLE"

STATUS_VERIFY_SOURCES = "VERIFY_SOURCES"                 # SYSTEM: aun no se ha intentado / puede reintentarse
STATUS_BLOCKED_BY_SOURCE_ACCESS = "BLOCKED_BY_SOURCE_ACCESS"  # SYSTEM: se intento de verdad y fallo el acceso
STATUS_READY_FOR_HUMAN_LEGAL_REVIEW = "READY_FOR_HUMAN_LEGAL_REVIEW"  # HUMAN: evidencia suficiente reunida


def _load(p):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception:
        return None


@dataclass
class SourceCheck:
    source_id: str
    claim_id: str
    url: str
    localizador: str
    result: str  # DIRECT_SUPPORT | NOT_VERIFIED | INACCESSIBLE
    evidence_origin: str  # "session_direct" | "external_independent" | "none"
    observaciones: str


@dataclass
class ClaimVerification:
    claim_id: str
    checks: list = field(default_factory=list)
    sufficient: bool = False  # NUNCA se pone True aqui salvo lectura fiel del dato existente


@dataclass
class PieceSourceSummary:
    piece_id: str
    checks: list = field(default_factory=list)
    accessible_count: int = 0
    inaccessible_count: int = 0
    not_verified_count: int = 0

    @property
    def all_sources_attempted_and_blocked(self):
        return self.checks and self.inaccessible_count == len(self.checks)

    @property
    def any_unverified(self):
        return self.not_verified_count > 0 or self.inaccessible_count > 0


def _clasificar_check(fuente, claim_id):
    vf = fuente.get("verificacion_fuente") or {}
    obs = str(vf.get("observaciones") or "")
    if vf.get("origen_oficial_confirmado") and vf.get("texto_exacto_consultado"):
        origen = "external_independent" if "externa" in obs.lower() or "codex" in obs.lower() else "session_direct"
        resultado = DIRECT_SUPPORT
    elif "EGRESS_BLOCKED" in obs or "bloqueada" in obs.lower():
        origen = "none"
        resultado = INACCESSIBLE
    else:
        origen = "none"
        resultado = NOT_VERIFIED
    return SourceCheck(
        source_id=fuente.get("id", ""), claim_id=claim_id, url=fuente.get("url", ""),
        localizador=fuente.get("localizador", ""), result=resultado,
        evidence_origin=origen, observaciones=obs)


def summarize_piece(packet):
    """Resumen honesto de accesibilidad de fuentes para un claim packet real.
    No evalua suficiencia juridica (eso exige lectura humana de las
    proposiciones, no un booleano derivable de verificacion_fuente)."""
    if not isinstance(packet, dict):
        return PieceSourceSummary(piece_id="DESCONOCIDO")
    resumen = PieceSourceSummary(piece_id=packet.get("piece_id", "DESCONOCIDO"))
    for c in packet.get("claims", []):
        for f in c.get("fuentes", []):
            chk = _clasificar_check(f, c.get("claim_id", ""))
            resumen.checks.append(chk)
            if chk.result == DIRECT_SUPPORT:
                resumen.accessible_count += 1
            elif chk.result == INACCESSIBLE:
                resumen.inaccessible_count += 1
            else:
                resumen.not_verified_count += 1
    return resumen


def next_system_action(summary):
    """SYSTEM_ACTION derivada solo de accesibilidad — nunca abre el gate,
    nunca declara suficiencia juridica. READY_FOR_HUMAN_LEGAL_REVIEW jamas se
    devuelve aqui: eso exige ademas evaluar cada proposicion material, que
    este modulo no hace (ver mandato §6E, fuera de alcance de un read-model
    de accesibilidad)."""
    if not summary.checks:
        return STATUS_VERIFY_SOURCES
    if summary.all_sources_attempted_and_blocked:
        return STATUS_BLOCKED_BY_SOURCE_ACCESS
    if summary.not_verified_count > 0:
        return STATUS_VERIFY_SOURCES
    return STATUS_BLOCKED_BY_SOURCE_ACCESS if summary.inaccessible_count else STATUS_VERIFY_SOURCES
