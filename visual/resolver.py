"""Resolucion de CONTENT_ID contra el canon REAL del repositorio.

Objetivo de uso: `visual dry-run CONTENT_ID` sin copiar JSON a mano.

No crea ningun ContentUnit paralelo (docs/contrato-motor-masivo.md §1-§2). Solo
localiza, en las estructuras que YA existen, las tres piezas que el pipeline
visual necesita, y dice exactamente cual falta:

    content/*.json                      artefacto de contenido (procedencia)
    pilot/claim-packets/*.json          paquete de claims (estado + gate)
    publication/records/*.json          ProductionHandoff (autorizacion de produccion)

Distingue siempre canon REAL de fixture de prueba: una fixture nunca se presenta
como contenido canonico.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CONTENT_DIR = REPO / "content"
SKILL = REPO / ".claude" / "skills" / "legalmente-legal-verification"
PACKETS_DIR = SKILL / "pilot" / "claim-packets"
RECORDS_DIR = SKILL / "publication" / "records"

REAL_CANONICAL = "REAL_CANONICAL"
TEST_FIXTURE = "TEST_FIXTURE"


@dataclass
class Resolution:
    content_id: str
    origin: str = REAL_CANONICAL
    artefacto: dict = None
    artefacto_path: str = ""
    packet: dict = None
    packet_path: str = ""
    handoff: dict = None
    handoff_path: str = ""
    blocking: list = field(default_factory=list)
    notes: list = field(default_factory=list)

    @property
    def resolved(self):
        """Resuelto = hay artefacto. Que ADEMAS pueda generar lo decide el gate."""
        return self.artefacto is not None

    @property
    def production_ready(self):
        return self.resolved and self.handoff is not None and not self.blocking


def _load(p):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception:
        return None


def _iter_json(d):
    return sorted(Path(d).glob("*.json")) if Path(d).is_dir() else []


def list_content_ids():
    """Todos los CONTENT_ID declarados por artefactos de contenido reales."""
    out = []
    for f in _iter_json(CONTENT_DIR):
        d = _load(f)
        proc = (d or {}).get("procedencia") or {}
        if proc.get("content_id"):
            out.append((proc["content_id"], str(f.relative_to(REPO)), proc.get("modo")))
    return sorted(out)


def list_pieces():
    """Piezas del piloto con su estado canonico real, sin reinterpretarlo."""
    out = []
    for f in _iter_json(PACKETS_DIR):
        d = _load(f)
        if not d:
            continue
        out.append({
            "piece_id": d.get("piece_id"),
            "path": str(f.relative_to(REPO)),
            "estado_agregado": d.get("estado_agregado"),
            "gate_global_arte": d.get("gate_global_arte"),
            "claims": len(d.get("claims", [])),
        })
    return out


def resolve(content_id, content_dir=None, packets_dir=None, records_dir=None):
    """Resuelve un CONTENT_ID. Nunca inventa lo que falta: lo declara."""
    r = Resolution(content_id=content_id)
    cdir = Path(content_dir or CONTENT_DIR)
    pdir = Path(packets_dir or PACKETS_DIR)
    rdir = Path(records_dir or RECORDS_DIR)

    for f in _iter_json(cdir):
        d = _load(f)
        if ((d or {}).get("procedencia") or {}).get("content_id") == content_id:
            r.artefacto, r.artefacto_path = d, str(f)
            break
    if r.artefacto is None:
        r.blocking.append(
            f"no existe ningun artefacto en {cdir.name}/ con content_id {content_id!r}. "
            "Sin artefacto de contenido no hay pieza que producir.")
        return r

    proc = r.artefacto.get("procedencia", {})
    modo = proc.get("modo")
    if modo == "EJEMPLO_TECNICO":
        r.origin = TEST_FIXTURE
        r.blocking.append(
            "modo EJEMPLO_TECNICO: material de prueba del pipeline, no contenido publicable.")

    piece_id = proc.get("piece_id")
    if piece_id:
        for f in _iter_json(pdir):
            d = _load(f)
            if (d or {}).get("piece_id") == piece_id:
                r.packet, r.packet_path = d, str(f)
                break
        if r.packet is None:
            r.blocking.append(f"la pieza declara piece_id {piece_id!r} y no existe su claim packet.")
        else:
            if r.packet.get("gate_global_arte") != "ABIERTO":
                r.blocking.append(
                    f"gate_global_arte={r.packet.get('gate_global_arte')!r} en "
                    f"{Path(r.packet_path).name}: la produccion visual exige gate ABIERTO, "
                    "que solo abre una aprobacion humana firmada.")
            pendientes = [c["claim_id"] for c in r.packet.get("claims", [])
                          if c.get("revision_humana", {}).get("estado") != "APROBADO"]
            if pendientes:
                r.blocking.append(f"claims sin aprobacion humana: {pendientes}.")
    elif modo == "GOBERNADO":
        r.blocking.append("modo GOBERNADO sin piece_id: no se puede localizar el claim packet.")

    hid = proc.get("handoff_id")
    if hid:
        for f in _iter_json(rdir):
            d = _load(f)
            for rec in (d if isinstance(d, list) else [d]):
                if isinstance(rec, dict) and rec.get("record_type") == "ProductionHandoff" \
                        and rec.get("handoff_id") == hid:
                    r.handoff, r.handoff_path = rec, str(f)
                    break
            if r.handoff:
                break
        if r.handoff is None:
            r.blocking.append(
                f"la pieza declara handoff_id {hid!r} y no existe ese ProductionHandoff en "
                f"{rdir.name}/. Sin handoff no hay produccion autorizada.")
    elif modo == "GOBERNADO":
        r.blocking.append("modo GOBERNADO sin handoff_id: no hay produccion autorizada que consumir.")

    return r


def _piece_id_de(content_id):
    for cid, path, _ in list_content_ids():
        if cid == content_id:
            d = _load(REPO / path)
            return (d or {}).get("procedencia", {}).get("piece_id")
    return None


def gate_summary():
    """Resumen de puertas por pieza. Solo estados existentes; ningun razonamiento nuevo.

    VISUAL_READY refleja la produccion REAL: si algun content_id gobernado
    resuelve en AUTORIZADA para este piece_id, no basta con mirar el gate del
    claim packet — eso quedaria obsoleto en cuanto exista handoff y artefacto.
    """
    piece_ids_con_produccion = set()
    for cid, path, modo in list_content_ids():
        if modo != "GOBERNADO":
            continue
        pid = _piece_id_de(cid)
        if pid and resolve(cid).production_ready:
            piece_ids_con_produccion.add(pid)

    filas = []
    for p in list_pieces():
        if p["gate_global_arte"] != "ABIERTO":
            visual = "NO"
        elif p["piece_id"] in piece_ids_con_produccion:
            visual = "READY_FOR_VISUAL"
        else:
            visual = "PENDIENTE_HANDOFF"
        filas.append({
            "PIECE_ID": p["piece_id"], "CANON": p["estado_agregado"],
            "ART_GATE": p["gate_global_arte"], "CLAIMS": p["claims"],
            "VISUAL_READY": visual,
        })
    return filas
