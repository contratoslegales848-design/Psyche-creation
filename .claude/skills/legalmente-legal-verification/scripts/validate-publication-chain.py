#!/usr/bin/env python3
"""Valida la CADENA POST-APROBACIÓN de LegalMente, fail-closed.

Cierra el hueco estructural detectado en la auditoría técnica: el validador de
claim packets termina en `gate_global_arte`, y a partir de ahí no existía
ninguna representación en código de lo que ocurre después. El resultado era que
la cadena jurídica (claim -> aprobación -> gate) y la cadena de producción
(content/*.json -> render) nunca se tocaban, y nada impedía renderizar o
publicar contenido sin respaldo jurídico.

La cadena que este script valida:

    ProductionHandoff   (qué se autorizó producir, ligado por hash)
      -> PublicationDecision  (DECISIÓN HUMANA SEPARADA de publicar)
        -> PublicationRecord  (qué se publicó realmente, dónde y cuándo)
          -> MeasurementRecord (métricas de esa publicación)
            -> Learning        (qué se aprendió)

REGLA NO NEGOCIABLE (Constitución §7 y §8): `gate_arte: ABIERTO` habilita
narrativa y producción visual y NUNCA autoriza publicación. Publicar exige una
`PublicationDecision` humana, posterior y separada. Este script es el mecanismo
que hace esa separación verificable en vez de meramente documental.

Por qué los registros viven FUERA del claim packet: el hash canónico de
aprobación (`compute_content_hash`) cubre todo el claim salvo `revision_humana`
y `gate_arte`. Añadir campos de publicación dentro del claim cambiaría ese hash
e invalidaría cualquier aprobación humana ya registrada. Estos registros son
artefactos separados que REFERENCIAN el claim packet por ruta y por hash.

Límite honesto, igual que en el resto de la skill: esto solo lee y escribe JSON.
No autentica personas. Que `decisor` contenga un nombre no prueba que esa
persona lo escribiera. El script comprueba que la firma exista, esté bien
formada y ligue al contenido exacto; la garantía de que la decisión fue humana
requiere un mecanismo externo que esta skill NO implementa.

Uso:
    python3 validate-publication-chain.py <archivo.json> [<archivo2.json> ...]
    python3 validate-publication-chain.py --dir <directorio>

Código de salida:
    0 si todos los registros son válidos y la cadena es coherente.
    1 si algún registro es inválido, la cadena está rota, o hay duplicados.
"""
import argparse
import importlib.util
import json
import re
import sys
from datetime import date, timedelta
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
VALIDATOR_PATH = Path(__file__).resolve().parent / "validate-claim-packet.py"

SCHEMA_VERSION = "1.0"
HASH_HEX_64 = re.compile(r"^[0-9a-fA-F]{64}$")
ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
CONTENT_ID = re.compile(r"^[A-Z0-9][A-Z0-9\-]{2,63}$")

RECORD_TYPES = {
    "ProductionHandoff",
    "PublicationDecision",
    "PublicationRecord",
    "MeasurementRecord",
    "Learning",
}

VALID_DECISION = {"AUTORIZADA", "RECHAZADA", "PENDIENTE"}
VALID_PUBLICATION_STATUS = {"PUBLICADA", "RETIRADA", "PROGRAMADA"}
VALID_HANDOFF_STATUS = {"PENDIENTE", "EN_PRODUCCION", "LISTO_PARA_QA", "APROBADO_QA"}

# Ventana de medición fijada por la Constitución §7 ("métricas a siete días").
MEASUREMENT_WINDOW_DAYS = 7

# Comprobaciones de QA deterministas exigidas antes de autorizar publicación.
# Deliberadamente NO incluye calidad estética ni juicio profesional: eso no se
# automatiza.
REQUIRED_QA_CHECKS = (
    "provenance_claim_packet",       # el asset procede de un claim packet identificado
    "hash_coincide",                 # los hashes aprobados siguen coincidiendo
    "jurisdiccion_visible",          # la jurisdicción aparece en la pieza
    "advertencia_editorial_presente",  # el disclaimer obligatorio está en la pieza
    "texto_coincide_con_aprobado",   # el texto publicable no altera el aprobado
    "legibilidad_movil",             # revisado a tamaño móvil real
)


def load_validator(path=VALIDATOR_PATH):
    """Importa validate-claim-packet.py (nombre con guiones -> importlib).

    Fail-closed: sin el validador canónico esta cadena no puede decidir nada.
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


# ---------------------------------------------------------------------------
# Helpers de forma
# ---------------------------------------------------------------------------

def _str(v):
    return isinstance(v, str) and v.strip() != ""


def _iso(v):
    if not _str(v) or not ISO_DATE.match(v):
        return False
    try:
        date.fromisoformat(v)
    except ValueError:
        return False
    return True


def _require(record, fields, errors, label):
    missing = [f for f in fields if f not in record]
    for f in missing:
        errors.append(f"{label}: falta el campo obligatorio '{f}'.")
    return not missing


def _resolve_packet(rel_path):
    """Resuelve la ruta del claim packet relativa a la raíz de la skill."""
    if not _str(rel_path):
        return None
    candidate = (SKILL_ROOT / rel_path).resolve()
    try:
        candidate.relative_to(SKILL_ROOT)
    except ValueError:
        return None  # fuera de la skill: no se acepta
    return candidate if candidate.is_file() else None


# ---------------------------------------------------------------------------
# ProductionHandoff
# ---------------------------------------------------------------------------

HANDOFF_FIELDS = [
    "record_type", "schema_version", "handoff_id", "content_id", "piece_id",
    "claim_packet", "claims", "jurisdiccion", "alcance", "advertencia_editorial",
    "redacciones_prohibidas", "status", "creado_en",
]


def validate_handoff(rec, validator, label):
    """Un handoff transporta a producción EXACTAMENTE lo aprobado.

    No puede existir si el gate global de la pieza no está ABIERTO, y cada claim
    que transporta debe seguir ligado por hash al contenido aprobado. Eso impide
    que la proposición aprobada se modifique silenciosamente camino de arte.
    """
    errors, warnings = [], []
    if not _require(rec, HANDOFF_FIELDS, errors, label):
        return errors, warnings

    if not CONTENT_ID.match(rec.get("content_id") or ""):
        errors.append(f"{label}: 'content_id' inválido (mayúsculas, dígitos y guiones, 3-64).")
    if not _str(rec.get("handoff_id")):
        errors.append(f"{label}: 'handoff_id' debe ser un string no vacío.")
    if not _iso(rec.get("creado_en")):
        errors.append(f"{label}: 'creado_en' debe ser fecha ISO válida.")
    if rec.get("status") not in VALID_HANDOFF_STATUS:
        errors.append(f"{label}: 'status' inválido: {rec.get('status')!r} (uno de {sorted(VALID_HANDOFF_STATUS)}).")
    if not _str(rec.get("advertencia_editorial")):
        errors.append(f"{label}: 'advertencia_editorial' es obligatoria y no puede estar vacía.")

    packet_path = _resolve_packet(rec.get("claim_packet"))
    if packet_path is None:
        errors.append(f"{label}: 'claim_packet' no resuelve a un archivo real dentro de la skill: {rec.get('claim_packet')!r}.")
        return errors, warnings

    try:
        piece = json.loads(packet_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"{label}: no se pudo leer el claim packet referenciado: {exc}")
        return errors, warnings

    p_errors, _p_warnings = validator.validate_piece(json.loads(json.dumps(piece)), str(packet_path))
    if p_errors:
        errors.append(f"{label}: el claim packet referenciado NO es estructuralmente válido ({len(p_errors)} errores) — un handoff nunca puede apoyarse en una pieza inválida.")
        return errors, warnings

    if piece.get("piece_id") != rec.get("piece_id"):
        errors.append(f"{label}: 'piece_id' {rec.get('piece_id')!r} no coincide con el del claim packet ({piece.get('piece_id')!r}).")

    # El gate de ARTE debe estar abierto: es lo que habilita producir.
    if piece.get("gate_global_arte") != "ABIERTO":
        errors.append(
            f"{label}: el claim packet tiene gate_global_arte={piece.get('gate_global_arte')!r}. "
            "Un ProductionHandoff exige gate de arte ABIERTO (aprobación humana firmada). "
            "Recuerda: gate abierto habilita producción, NO publicación."
        )

    claims_by_id = {c.get("claim_id"): c for c in piece.get("claims", [])}
    declared = rec.get("claims")
    if not isinstance(declared, list) or not declared:
        errors.append(f"{label}: 'claims' debe ser una lista no vacía.")
        return errors, warnings

    seen = set()
    for i, dc in enumerate(declared):
        cl = f"{label}.claims[{i}]"
        if not isinstance(dc, dict):
            errors.append(f"{cl}: cada entrada debe ser un objeto.")
            continue
        if not _require(dc, ["claim_id", "approved_claim_hash", "approved_text"], errors, cl):
            continue
        cid = dc["claim_id"]
        if cid in seen:
            errors.append(f"{cl}: claim_id duplicado dentro del handoff: {cid!r}.")
        seen.add(cid)
        claim = claims_by_id.get(cid)
        if claim is None:
            errors.append(f"{cl}: el claim {cid!r} no existe en el claim packet referenciado.")
            continue
        if not HASH_HEX_64.match(dc.get("approved_claim_hash") or ""):
            errors.append(f"{cl}: 'approved_claim_hash' debe ser 64 hexadecimales.")
            continue
        real_hash = validator.compute_content_hash(claim)
        if dc["approved_claim_hash"] != real_hash:
            errors.append(
                f"{cl}: 'approved_claim_hash' no coincide con el hash canónico actual del claim. "
                "El contenido cambió después de aprobar, o el hash nunca correspondió a este claim."
            )
        if claim.get("gate_arte") != "ABIERTO":
            errors.append(f"{cl}: el claim {cid!r} tiene gate_arte={claim.get('gate_arte')!r}; no puede entrar en producción.")
        if dc["approved_text"] != claim.get("texto_exacto"):
            errors.append(
                f"{cl}: 'approved_text' NO coincide literalmente con 'texto_exacto' del claim aprobado. "
                "La proposición aprobada no puede modificarse en el handoff."
            )
        prohibidas = rec.get("redacciones_prohibidas")
        if isinstance(prohibidas, list) and _str(claim.get("redaccion_prohibida")):
            if claim["redaccion_prohibida"] not in prohibidas:
                errors.append(
                    f"{cl}: el claim declara una 'redaccion_prohibida' que el handoff no transporta en "
                    "'redacciones_prohibidas' — la prohibición debe viajar con el contenido."
                )

    faltantes = [c.get("claim_id") for c in piece.get("claims", []) if c.get("claim_id") not in seen]
    if faltantes:
        warnings.append(f"{label}: el handoff no transporta todos los claims de la pieza; faltan {faltantes!r}.")

    return errors, warnings


# ---------------------------------------------------------------------------
# PublicationDecision — la decisión humana separada
# ---------------------------------------------------------------------------

DECISION_FIELDS = [
    "record_type", "schema_version", "decision_id", "content_id", "handoff_id",
    "decision", "decisor", "fecha", "observaciones", "plataformas_autorizadas",
    "qa", "advertencia_editorial_verificada",
]


def validate_decision(rec, label):
    """Autorización humana de publicación. Separada del gate de arte por diseño.

    Fail-closed: cualquier ausencia, firma incompleta o QA no superado deja la
    decisión sin efecto autorizante.
    """
    errors, warnings = [], []
    if not _require(rec, DECISION_FIELDS, errors, label):
        return errors, warnings

    if not CONTENT_ID.match(rec.get("content_id") or ""):
        errors.append(f"{label}: 'content_id' inválido.")
    if not _str(rec.get("decision_id")):
        errors.append(f"{label}: 'decision_id' debe ser un string no vacío.")
    if not _str(rec.get("handoff_id")):
        errors.append(f"{label}: 'handoff_id' debe referenciar un ProductionHandoff.")

    decision = rec.get("decision")
    if decision not in VALID_DECISION:
        errors.append(f"{label}: 'decision' inválida: {decision!r} (uno de {sorted(VALID_DECISION)}).")
        return errors, warnings

    plataformas = rec.get("plataformas_autorizadas")
    if not isinstance(plataformas, list):
        errors.append(f"{label}: 'plataformas_autorizadas' debe ser una lista.")
        plataformas = []

    qa = rec.get("qa")
    if not isinstance(qa, dict):
        errors.append(f"{label}: 'qa' debe ser un objeto con las comprobaciones deterministas.")
        qa = {}

    if decision != "AUTORIZADA":
        # Solo una decisión AUTORIZADA habilita publicar. El resto no exige firma
        # completa, pero tampoco autoriza nada.
        if plataformas:
            warnings.append(f"{label}: decision={decision!r} pero declara plataformas autorizadas; no autorizan nada.")
        return errors, warnings

    # --- a partir de aquí: requisitos duros de una autorización real ---
    if not _str(rec.get("decisor")):
        errors.append(f"{label}: 'decision'='AUTORIZADA' exige 'decisor' identificado no vacío.")
    if not _iso(rec.get("fecha")):
        errors.append(f"{label}: 'decision'='AUTORIZADA' exige 'fecha' ISO válida.")
    if not _str(rec.get("observaciones")):
        errors.append(f"{label}: 'decision'='AUTORIZADA' exige 'observaciones' con la decisión en palabras del humano.")
    if rec.get("advertencia_editorial_verificada") is not True:
        errors.append(
            f"{label}: 'advertencia_editorial_verificada' debe ser exactamente true para autorizar. "
            "La advertencia editorial obligatoria tiene que estar comprobada en la pieza."
        )
    if not plataformas:
        errors.append(f"{label}: una autorización debe enumerar al menos una plataforma en 'plataformas_autorizadas'.")

    faltan_qa = [c for c in REQUIRED_QA_CHECKS if c not in qa]
    if faltan_qa:
        errors.append(f"{label}.qa: faltan comprobaciones obligatorias: {faltan_qa!r}.")
    no_superadas = [c for c in REQUIRED_QA_CHECKS if qa.get(c) is not True]
    no_superadas = [c for c in no_superadas if c not in faltan_qa]
    if no_superadas:
        errors.append(
            f"{label}.qa: comprobaciones no superadas: {no_superadas!r}. "
            "Todas las comprobaciones deterministas deben estar en true para autorizar."
        )
    return errors, warnings


# ---------------------------------------------------------------------------
# PublicationRecord
# ---------------------------------------------------------------------------

RECORD_FIELDS = [
    "record_type", "schema_version", "content_id", "piece_id", "platform",
    "format", "publication_url", "published_at", "publication_decision_id",
    "asset_version", "status", "measurement_due_at",
]


def validate_publication_record(rec, label):
    errors, warnings = [], []
    if not _require(rec, RECORD_FIELDS, errors, label):
        return errors, warnings

    if not CONTENT_ID.match(rec.get("content_id") or ""):
        errors.append(f"{label}: 'content_id' inválido.")
    if not _str(rec.get("publication_decision_id")):
        errors.append(f"{label}: 'publication_decision_id' es obligatorio — no se publica sin decisión humana.")
    if rec.get("status") not in VALID_PUBLICATION_STATUS:
        errors.append(f"{label}: 'status' inválido: {rec.get('status')!r} (uno de {sorted(VALID_PUBLICATION_STATUS)}).")
    if not _iso(rec.get("published_at")):
        errors.append(f"{label}: 'published_at' debe ser fecha ISO válida.")
    if not _str(rec.get("platform")):
        errors.append(f"{label}: 'platform' es obligatorio.")
    if not _str(rec.get("asset_version")):
        errors.append(f"{label}: 'asset_version' es obligatorio para poder reproducir qué se publicó.")

    url = rec.get("publication_url")
    if rec.get("status") == "PUBLICADA":
        if not _str(url) or not url.startswith(("http://", "https://")):
            errors.append(f"{label}: una publicación con status 'PUBLICADA' exige 'publication_url' http/https real.")

    # Recordatorio de medición a 7 días (Constitución §7): dato, no infraestructura.
    if _iso(rec.get("published_at")) and _iso(rec.get("measurement_due_at")):
        esperado = date.fromisoformat(rec["published_at"]) + timedelta(days=MEASUREMENT_WINDOW_DAYS)
        if date.fromisoformat(rec["measurement_due_at"]) != esperado:
            errors.append(
                f"{label}: 'measurement_due_at' debe ser exactamente published_at + {MEASUREMENT_WINDOW_DAYS} días "
                f"({esperado.isoformat()}), es {rec['measurement_due_at']!r}."
            )
    elif not _iso(rec.get("measurement_due_at")):
        errors.append(f"{label}: 'measurement_due_at' debe ser fecha ISO válida.")
    return errors, warnings


# ---------------------------------------------------------------------------
# MeasurementRecord y Learning
# ---------------------------------------------------------------------------

MEASUREMENT_FIELDS = [
    "record_type", "schema_version", "content_id", "platform", "captured_at",
    "window_days", "metrics", "available_metrics", "source",
]


def validate_measurement(rec, label):
    errors, warnings = [], []
    if not _require(rec, MEASUREMENT_FIELDS, errors, label):
        return errors, warnings
    if not CONTENT_ID.match(rec.get("content_id") or ""):
        errors.append(f"{label}: 'content_id' inválido.")
    if not _iso(rec.get("captured_at")):
        errors.append(f"{label}: 'captured_at' debe ser fecha ISO válida.")
    if not isinstance(rec.get("window_days"), int) or rec["window_days"] <= 0:
        errors.append(f"{label}: 'window_days' debe ser un entero positivo.")
    if not isinstance(rec.get("metrics"), dict):
        errors.append(f"{label}: 'metrics' debe ser un objeto.")
    if not isinstance(rec.get("available_metrics"), list) or not rec["available_metrics"]:
        errors.append(f"{label}: 'available_metrics' debe listar qué métricas ofreció la plataforma.")
    if not _str(rec.get("source")):
        errors.append(f"{label}: 'source' es obligatorio (de dónde salieron las cifras).")
    # Nunca inventar métricas: una métrica declarada disponible pero ausente, o
    # presente sin declararse disponible, es incoherencia.
    if isinstance(rec.get("metrics"), dict) and isinstance(rec.get("available_metrics"), list):
        ausentes = [k for k in rec["available_metrics"] if k not in rec["metrics"]]
        if ausentes:
            errors.append(f"{label}: métricas declaradas disponibles pero ausentes en 'metrics': {ausentes!r}.")
        extra = [k for k in rec["metrics"] if k not in rec["available_metrics"]]
        if extra:
            errors.append(f"{label}: 'metrics' contiene claves no declaradas en 'available_metrics': {extra!r}.")
    return errors, warnings


LEARNING_FIELDS = [
    "record_type", "schema_version", "learning_id", "content_id",
    "observation", "hypothesis", "decision", "reuse", "next_action",
]


def validate_learning(rec, label):
    errors, warnings = [], []
    if not _require(rec, LEARNING_FIELDS, errors, label):
        return errors, warnings
    if not CONTENT_ID.match(rec.get("content_id") or ""):
        errors.append(f"{label}: 'content_id' inválido.")
    for f in ("observation", "hypothesis", "decision", "reuse", "next_action"):
        if not _str(rec.get(f)):
            errors.append(f"{label}: '{f}' debe ser un string no vacío.")
    return errors, warnings


# ---------------------------------------------------------------------------
# Validación de un registro suelto y de la cadena completa
# ---------------------------------------------------------------------------

def validate_record(rec, validator, label):
    errors, warnings = [], []
    if not isinstance(rec, dict):
        return [f"{label}: el registro no es un objeto JSON."], []
    rt = rec.get("record_type")
    if rt not in RECORD_TYPES:
        return [f"{label}: 'record_type' inválido: {rt!r} (uno de {sorted(RECORD_TYPES)})."], []
    if rec.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"{label}: 'schema_version' debe ser {SCHEMA_VERSION!r}, es {rec.get('schema_version')!r}.")
    dispatch = {
        "ProductionHandoff": lambda: validate_handoff(rec, validator, label),
        "PublicationDecision": lambda: validate_decision(rec, label),
        "PublicationRecord": lambda: validate_publication_record(rec, label),
        "MeasurementRecord": lambda: validate_measurement(rec, label),
        "Learning": lambda: validate_learning(rec, label),
    }
    e, w = dispatch[rt]()
    return errors + e, warnings + w


def validate_chain(records):
    """Coherencia entre registros: nadie puede saltarse un eslabón anterior.

    `records` es una lista de (label, dict).
    """
    errors, warnings = [], []
    handoffs, decisions, publications, measurements = {}, {}, {}, []

    # --- unicidad de identificadores (anti-duplicado) ---
    for label, r in records:
        rt = r.get("record_type")
        if rt == "ProductionHandoff":
            k = r.get("handoff_id")
            if k in handoffs:
                errors.append(f"{label}: handoff_id duplicado: {k!r} (ya en {handoffs[k][0]}).")
            else:
                handoffs[k] = (label, r)
        elif rt == "PublicationDecision":
            k = r.get("decision_id")
            if k in decisions:
                errors.append(f"{label}: decision_id duplicado: {k!r} (ya en {decisions[k][0]}).")
            else:
                decisions[k] = (label, r)
        elif rt == "PublicationRecord":
            k = (r.get("content_id"), r.get("platform"))
            if k in publications:
                errors.append(
                    f"{label}: publicación duplicada para content_id/platform {k!r} "
                    f"(ya en {publications[k][0]}) — una misma pieza no se registra dos veces en la misma plataforma."
                )
            else:
                publications[k] = (label, r)
        elif rt == "MeasurementRecord":
            measurements.append((label, r))

    # --- decisión -> handoff ---
    for label, dec in decisions.values():
        hid = dec.get("handoff_id")
        if hid not in handoffs:
            errors.append(
                f"{label}: 'handoff_id' {hid!r} no corresponde a ningún ProductionHandoff del conjunto. "
                "No se autoriza publicar contenido que no pasó por handoff."
            )
            continue
        h = handoffs[hid][1]
        if h.get("content_id") != dec.get("content_id"):
            errors.append(f"{label}: content_id {dec.get('content_id')!r} no coincide con el del handoff ({h.get('content_id')!r}).")

    # --- publicación -> decisión AUTORIZADA ---
    for label, pub in publications.values():
        did = pub.get("publication_decision_id")
        entry = decisions.get(did)
        if entry is None:
            errors.append(
                f"{label}: 'publication_decision_id' {did!r} no corresponde a ninguna PublicationDecision. "
                "PUBLICAR SIN DECISIÓN HUMANA ES INVÁLIDO."
            )
            continue
        dec = entry[1]
        if dec.get("decision") != "AUTORIZADA":
            errors.append(
                f"{label}: la decisión {did!r} tiene decision={dec.get('decision')!r}. "
                "Solo una decisión AUTORIZADA habilita publicar."
            )
        if dec.get("content_id") != pub.get("content_id"):
            errors.append(f"{label}: content_id no coincide con el de su decisión ({dec.get('content_id')!r}).")
        plataformas = dec.get("plataformas_autorizadas") or []
        if pub.get("platform") not in plataformas:
            errors.append(
                f"{label}: se publicó en {pub.get('platform')!r}, que no está entre las plataformas "
                f"autorizadas por la decisión ({plataformas!r})."
            )

    # --- medición -> publicación ---
    pub_by_content = {}
    for (cid, _plat), (label, pub) in publications.items():
        pub_by_content.setdefault(cid, []).append(pub)
    for label, meas in measurements:
        cid = meas.get("content_id")
        pubs = pub_by_content.get(cid)
        if not pubs:
            errors.append(
                f"{label}: no existe PublicationRecord para content_id {cid!r}. "
                "No se miden publicaciones que no constan."
            )
            continue
        if meas.get("platform") not in {p.get("platform") for p in pubs}:
            errors.append(f"{label}: no hay publicación de {cid!r} en la plataforma {meas.get('platform')!r}.")

    # --- learning -> medición ---
    measured = {m.get("content_id") for _l, m in measurements}
    for label, r in records:
        if r.get("record_type") == "Learning" and r.get("content_id") not in measured:
            errors.append(
                f"{label}: Learning sobre content_id {r.get('content_id')!r} sin ningún MeasurementRecord. "
                "No se extraen aprendizajes de métricas inexistentes."
            )
    return errors, warnings


def collect(paths):
    records, read_errors = [], []
    for p in paths:
        try:
            data = json.loads(Path(p).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            read_errors.append(f"FALLÓ: no se pudo leer/parsear {p}: {exc}")
            continue
        if isinstance(data, list):
            for i, r in enumerate(data):
                records.append((f"{p}[{i}]", r))
        else:
            records.append((str(p), data))
    return records, read_errors


def main(argv):
    ap = argparse.ArgumentParser(description="Valida la cadena post-aprobación de LegalMente.")
    ap.add_argument("files", nargs="*", help="Archivos JSON de registros.")
    ap.add_argument("--dir", help="Directorio con registros JSON (recursivo).")
    args = ap.parse_args(argv)

    paths = list(args.files)
    if args.dir:
        paths.extend(str(p) for p in sorted(Path(args.dir).rglob("*.json")))
    if not paths:
        print("Uso: validate-publication-chain.py <archivo.json> [...] | --dir <directorio>", file=sys.stderr)
        return 1

    try:
        validator = load_validator()
    except (ImportError, OSError, SyntaxError) as exc:
        print(f"FALLÓ: no se pudo cargar el validador canónico: {exc}", file=sys.stderr)
        return 1

    records, read_errors = collect(paths)
    for e in read_errors:
        print(e)

    all_errors, all_warnings = list(read_errors), []
    for label, rec in records:
        e, w = validate_record(rec, validator, label)
        all_errors.extend(e)
        all_warnings.extend(w)

    valid = [(l, r) for l, r in records if isinstance(r, dict) and r.get("record_type") in RECORD_TYPES]
    ce, cw = validate_chain(valid)
    all_errors.extend(ce)
    all_warnings.extend(cw)

    for w in all_warnings:
        print(f"[ADVERTENCIA DE CADENA] {w}")
    if all_errors:
        print("[CADENA INVÁLIDA]")
        for e in all_errors:
            print(f"  - {e}")
        return 1

    autorizadas = sum(1 for _l, r in valid if r.get("record_type") == "PublicationDecision" and r.get("decision") == "AUTORIZADA")
    publicadas = sum(1 for _l, r in valid if r.get("record_type") == "PublicationRecord")
    print(
        f"[CADENA VÁLIDA] {len(valid)} registros coherentes "
        f"({autorizadas} autorización(es) de publicación, {publicadas} publicación(es) registrada(s))."
    )
    print("Recordatorio: un gate de arte ABIERTO habilita producción; solo una PublicationDecision AUTORIZADA habilita publicar.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
