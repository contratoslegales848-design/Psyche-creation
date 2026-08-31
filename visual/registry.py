"""Registro de assets en sistema de ficheros. Sin base de datos.

Estructura:

    artifacts/visual/<CONTENT_ID>/<GENERATION_ID>/
        raw/<asset_id>.png
        composed/<asset_id>.png
        receipt.json

Toda ruta se construye desde identificadores VALIDADOS, nunca desde texto libre
del proveedor o del usuario. El registro no inventa aprobacion: si no hay
receipt de decision humana, no hay asset aprobado.
"""

import json
import re
from pathlib import Path

from errors import StoragePathError, ReceiptIntegrityError
import receipts as receipts_mod

# Identificadores admisibles. Deliberadamente estrictos.
ID_SEGURO = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
PROHIBIDOS = ("..", "/", "\\", "\x00", ":")


def assert_id_seguro(valor, campo):
    v = str(valor or "")
    if not v or any(p in v for p in PROHIBIDOS) or not ID_SEGURO.match(v):
        raise StoragePathError(f"{campo} inseguro o invalido: {valor!r}")
    return v


class AssetRegistry:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    # --- rutas ---
    def _dir(self, content_id, generation_id):
        c = assert_id_seguro(content_id, "content_id")
        g = assert_id_seguro(generation_id, "generation_id")
        d = (self.root / c / g).resolve()
        # Defensa en profundidad: aunque los ids pasen, la ruta final debe caer
        # dentro de la raiz. Cubre symlinks y sorpresas del sistema de ficheros.
        if not str(d).startswith(str(self.root) + "/") and d != self.root:
            raise StoragePathError(f"ruta fuera de la raiz del registro: {d}")
        return d

    # --- escritura ---
    def store(self, receipt, raw_bytes=b"", composed_bytes=b""):
        d = self._dir(receipt.content_id, receipt.generation_id)
        if (d / "receipt.json").exists():
            raise ReceiptIntegrityError(
                f"ya existe un receipt para {receipt.generation_id}; no se sobrescribe historia.")
        d.mkdir(parents=True, exist_ok=True)
        asset_id = assert_id_seguro(receipt.asset_id or receipt.generation_id, "asset_id")
        if raw_bytes:
            (d / "raw").mkdir(exist_ok=True)
            (d / "raw" / f"{asset_id}.png").write_bytes(raw_bytes)
        if composed_bytes:
            (d / "composed").mkdir(exist_ok=True)
            (d / "composed" / f"{asset_id}.png").write_bytes(composed_bytes)
        (d / "receipt.json").write_text(
            json.dumps(receipt.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8")
        return d

    # --- lectura ---
    def get_generation(self, content_id, generation_id):
        f = self._dir(content_id, generation_id) / "receipt.json"
        if not f.is_file():
            return None
        return json.loads(f.read_text(encoding="utf-8"))

    def generations_for(self, content_id):
        c = assert_id_seguro(content_id, "content_id")
        base = self.root / c
        if not base.is_dir():
            return []
        out = []
        for d in sorted(base.iterdir()):
            f = d / "receipt.json"
            if f.is_file():
                out.append(json.loads(f.read_text(encoding="utf-8")))
        return sorted(out, key=lambda r: r.get("created_at", ""))

    def latest_generation(self, content_id):
        gens = self.generations_for(content_id)
        return gens[-1] if gens else None

    def failed_generations(self, content_id):
        malos = {"GENERACION_FALLIDA", "QA_FALLIDO", "PROVEEDOR_INCOMPATIBLE",
                 "GATE_CERRADO", "BRIEF_INVALIDO"}
        return [g for g in self.generations_for(content_id) if g.get("status") in malos]

    def composed_asset_path(self, content_id, generation_id, asset_id):
        p = self._dir(content_id, generation_id) / "composed" / f"{assert_id_seguro(asset_id, 'asset_id')}.png"
        return p if p.is_file() else None

    def human_approved_asset(self, content_id):
        """Solo devuelve algo si existe un HumanDecisionReceipt real y APROBADO.

        La aprobacion NUNCA se lee del generation receipt: son documentos
        distintos (lo que hizo la maquina vs. lo que decidio una persona).
        """
        for g in self.generations_for(content_id):
            d = self._dir(content_id, g["generation_id"]) / "human_decision.json"
            if d.is_file():
                dec = json.loads(d.read_text(encoding="utf-8"))
                if dec.get("decision") == "APROBADO" and dec.get("revisor"):
                    return {"generation": g, "decision": dec}
        return None

    def record_human_decision(self, content_id, generation_id, decision, revisor, observaciones=""):
        """Receipt de decision humana, SEPARADO del generation receipt."""
        if decision not in ("APROBADO", "RECHAZADO"):
            raise ValueError(f"decision humana invalida: {decision!r}")
        if not str(revisor or "").strip():
            raise ValueError("una decision humana exige revisor identificado.")
        d = self._dir(content_id, generation_id)
        if not (d / "receipt.json").is_file():
            raise ReceiptIntegrityError("no se puede decidir sobre una generacion inexistente.")
        f = d / "human_decision.json"
        if f.exists():
            raise ReceiptIntegrityError("ya existe una decision humana; no se reescribe.")
        payload = {"record_type": "HumanDecisionReceipt", "schema_version": "1.0",
                   "content_id": content_id, "generation_id": generation_id,
                   "decision": decision, "revisor": revisor, "observaciones": observaciones}
        f.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                     encoding="utf-8")
        return f


def verify_receipt_integrity(receipt_dict, asset_bytes=None, expected_content_id=None):
    """Coherencia del receipt. Fail-closed."""
    import hashlib
    problemas = []
    if expected_content_id and receipt_dict.get("content_id") != expected_content_id:
        problemas.append(
            f"el receipt apunta a otro CONTENT_ID: {receipt_dict.get('content_id')!r} != {expected_content_id!r}")
    if not receipt_dict.get("generation_id"):
        problemas.append("receipt sin generation_id.")
    if asset_bytes is not None:
        real = hashlib.sha256(asset_bytes).hexdigest()
        if receipt_dict.get("asset_sha256") and receipt_dict["asset_sha256"] != real:
            problemas.append("asset hash mismatch: el receipt no describe este asset.")
    if receipt_dict.get("status") == "PENDIENTE_REVISION_HUMANA" \
            and receipt_dict.get("human_visual_approval") not in (None, "", "PENDIENTE"):
        problemas.append("un generation receipt no puede declarar aprobacion humana.")
    return problemas


def find_equivalent_generation(registry, content_id, plan_hash):
    """Busca una generacion previa EXITOSA con el mismo plan.

    Base de la idempotencia: un reintento de red, un rerun de CI o una segunda
    ejecucion del CLI no deben producir una generacion nueva. Regenerar exige
    intencion explicita (§30, §31).
    """
    if not plan_hash:
        return None
    for g in registry.generations_for(content_id):
        if g.get("generation_plan_hash") == plan_hash \
                and g.get("status") == "PENDIENTE_REVISION_HUMANA":
            return g
    return None
