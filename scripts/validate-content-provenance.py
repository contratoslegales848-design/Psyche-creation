#!/usr/bin/env python3
"""Valida la PROCEDENCIA de los artefactos de contenido de LegalMente.

Problema que cierra
-------------------
`content/*.json` alimentaba directamente al renderizador de Remotion. `src/content.ts`
comprobaba la FORMA (id, título, frase, remate, marca, imagen, duración) y nada más:
no existía ningún campo que ligara una pieza renderizada a un claim packet aprobado.
La cadena estaba cortada en dos mitades que no se hablaban — la jurídica y la de
producción — y cualquier JSON bien formado podía renderizarse como pieza publicable.

Cómo lo cierra
--------------
Cada artefacto de contenido declara su `procedencia`, con uno de tres modos:

  GOBERNADO       — hay un ProductionHandoff válido detrás. Se comprueba de verdad:
                    el handoff existe, la cadena valida, el claim packet está
                    aprobado, los hashes coinciden y la capa jurisdiccional declarada
                    es la del claim. Publicable.
  NO_APLICA       — por decisión de gobernanza no hay afirmación jurídica que
                    verificar (cita histórica, formato de marca, contenido no
                    jurídico). Publicable, pero exige motivo tipificado,
                    justificación y un humano identificado que lo decidió. NO es
                    una vía de escape: es una decisión con responsable.
  EJEMPLO_TECNICO — material de prueba del pipeline. Se renderiza, pero
                    `publicable` debe ser false y nunca puede entrar en la cadena.

Fail-closed: un artefacto sin `procedencia`, con un modo desconocido o con un
handoff que no valida, se rechaza. No hay modo por defecto.

Lo que este validador NO hace
-----------------------------
No autoriza publicar. Un artefacto GOBERNADO válido significa "esto puede
producirse y su origen es verificable", no "esto puede publicarse". Publicar sigue
exigiendo una PublicationDecision humana (ver publication/README.md).

Uso:
    python3 scripts/validate-content-provenance.py
    python3 scripts/validate-content-provenance.py content/ejemplo.json
"""
import argparse
import importlib.util
import json
import re
import sys
import unicodedata
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = REPO_ROOT / "content"
SKILL_ROOT = REPO_ROOT / ".claude" / "skills" / "legalmente-legal-verification"
RECORDS_DIR = SKILL_ROOT / "publication" / "records"

VALID_MODOS = {"GOBERNADO", "NO_APLICA", "EJEMPLO_TECNICO"}

# Motivos tipificados por los que una pieza legítimamente no lleva claim jurídico.
# Cerrado a propósito: "no aplica" sin motivo tipificado es una vía de escape.
VALID_MOTIVOS_NO_APLICA = {
    "CITA_HISTORICA",          # máxima, aforismo o cita de dominio histórico
    "FORMATO_DE_GOBERNANZA",   # formato de marca definido por gobernanza
    "CONTENIDO_NO_JURIDICO",   # anuncio, comunidad, meta-contenido
}

VALID_JURISDICTION_LAYER = {
    "CAPA_A_TRANSVERSAL", "CAPA_B_VARIABLE", "CAPA_C_NACIONAL", "NO_APLICA",
}

# El único estado de producción que habilita a un artefacto GOBERNADO.
PRODUCTION_STATUS_OK = "APROBADO_QA"

CONTENT_ID = re.compile(r"^[A-Z0-9][A-Z0-9\-]{2,63}$")
HASH_HEX_64 = re.compile(r"^[0-9a-fA-F]{64}$")
ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

# Taxonomía editorial mínima. Es también la clave anti-duplicados: dos piezas
# publicables no pueden ocupar la misma casilla de materia/submateria/concepto.
TAXONOMIA_FIELDS = ("materia", "submateria", "concepto", "situacion_humana", "content_type")


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_validators():
    """Carga el validador canónico y el de la cadena post-aprobación.

    Fail-closed: sin ellos este script no puede afirmar nada sobre procedencia.
    """
    scripts_dir = SKILL_ROOT / "scripts"
    sys.path.insert(0, str(scripts_dir))
    claim = _load(scripts_dir / "validate-claim-packet.py", "validate_claim_packet")
    chain = _load(scripts_dir / "validate-publication-chain.py", "validate_publication_chain")
    return claim, chain


def _str(v):
    return isinstance(v, str) and v.strip() != ""


def _repo_relative(path):
    """Ruta legible relativa al repositorio; absoluta si cae fuera de él."""
    try:
        return path.resolve().relative_to(REPO_ROOT)
    except ValueError:
        return path


def normalize_fingerprint(text):
    """Huella normalizada de un texto, para detectar la misma pieza con otro ID.

    Minúsculas, sin acentos, sin puntuación, espacios colapsados. Es un control
    barato y determinista: detecta la repetición literal y las variaciones
    triviales (mayúsculas, tildes, signos), no la paráfrasis. No pretende más.
    """
    if not isinstance(text, str):
        return ""
    lowered = unicodedata.normalize("NFD", text.lower())
    sin_acentos = "".join(ch for ch in lowered if unicodedata.category(ch) != "Mn")
    solo_palabras = re.sub(r"[^a-z0-9ñ\s]", " ", sin_acentos)
    return " ".join(solo_palabras.split())


# ---------------------------------------------------------------------------
# Carga de handoffs
# ---------------------------------------------------------------------------

def load_handoffs(chain):
    """Indexa por handoff_id los ProductionHandoff del repositorio.

    Devuelve (handoffs, errores). Un handoff que no valida NO se indexa: un
    artefacto que lo invoque quedará sin procedencia, que es el resultado
    correcto.
    """
    handoffs, errors = {}, []
    if not RECORDS_DIR.is_dir():
        return handoffs, errors
    for path in sorted(RECORDS_DIR.rglob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{_repo_relative(path)}: no se pudo leer/parsear: {exc}")
            continue
        registros = data if isinstance(data, list) else [data]
        for i, rec in enumerate(registros):
            if not isinstance(rec, dict) or rec.get("record_type") != "ProductionHandoff":
                continue
            label = f"{_repo_relative(path)}[{i}]"
            hid = rec.get("handoff_id")
            if hid in handoffs:
                errors.append(f"{label}: handoff_id duplicado: {hid!r}.")
                continue
            handoffs[hid] = (label, rec)
    return handoffs, errors


# ---------------------------------------------------------------------------
# Validación de un artefacto
# ---------------------------------------------------------------------------

def validate_taxonomia(art, label):
    errors = []
    tax = art.get("taxonomia")
    if not isinstance(tax, dict):
        return [f"{label}: 'taxonomia' es obligatoria en contenido publicable "
                f"(campos: {', '.join(TAXONOMIA_FIELDS)}) — es también la clave anti-duplicados."]
    for f in TAXONOMIA_FIELDS:
        if not _str(tax.get(f)):
            errors.append(f"{label}.taxonomia: '{f}' debe ser un string no vacío.")
    return errors


def validate_gobernado(proc, art, label, handoffs, claim_mod, chain_mod):
    errors = []
    hid = proc.get("handoff_id")
    if not _str(hid):
        return [f"{label}.procedencia: modo GOBERNADO exige 'handoff_id'."]

    entry = handoffs.get(hid)
    if entry is None:
        return [
            f"{label}.procedencia: 'handoff_id' {hid!r} no corresponde a ningún "
            f"ProductionHandoff válido en {_repo_relative(RECORDS_DIR)}/. "
            "Un contenido gobernado sin handoff no tiene procedencia verificable."
        ]
    h_label, handoff = entry

    # El handoff debe validar por sí mismo: eso ya comprueba gate de arte abierto,
    # hashes contra el claim packet y texto idéntico al aprobado.
    h_errors, _h_warnings = chain_mod.validate_record(handoff, claim_mod, h_label)
    if h_errors:
        errors.append(
            f"{label}.procedencia: el ProductionHandoff {hid!r} NO es válido "
            f"({len(h_errors)} error(es)); el primero: {h_errors[0]}"
        )
        return errors

    if handoff.get("status") != PRODUCTION_STATUS_OK:
        errors.append(
            f"{label}.procedencia: el handoff está en status={handoff.get('status')!r}; "
            f"solo {PRODUCTION_STATUS_OK!r} habilita un artefacto de contenido gobernado."
        )
    if proc.get("production_status") != PRODUCTION_STATUS_OK:
        errors.append(
            f"{label}.procedencia: 'production_status' debe ser {PRODUCTION_STATUS_OK!r}, "
            f"es {proc.get('production_status')!r}."
        )
    if handoff.get("content_id") != proc.get("content_id"):
        errors.append(
            f"{label}.procedencia: 'content_id' {proc.get('content_id')!r} no coincide "
            f"con el del handoff ({handoff.get('content_id')!r})."
        )
    if proc.get("piece_id") != handoff.get("piece_id"):
        errors.append(
            f"{label}.procedencia: 'piece_id' {proc.get('piece_id')!r} no coincide "
            f"con el del handoff ({handoff.get('piece_id')!r})."
        )

    # --- claims y hashes ---
    declarados = proc.get("claims")
    if not isinstance(declarados, list) or not declarados:
        errors.append(f"{label}.procedencia: modo GOBERNADO exige 'claims' como lista no vacía.")
        return errors

    por_id = {c.get("claim_id"): c for c in handoff.get("claims", []) if isinstance(c, dict)}
    packet_path = (SKILL_ROOT / (handoff.get("claim_packet") or "")).resolve()
    try:
        piece = json.loads(packet_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"{label}.procedencia: no se pudo leer el claim packet del handoff: {exc}")
        return errors
    claims_packet = {c.get("claim_id"): c for c in piece.get("claims", []) if isinstance(c, dict)}

    for i, dc in enumerate(declarados):
        cl = f"{label}.procedencia.claims[{i}]"
        if not isinstance(dc, dict):
            errors.append(f"{cl}: cada entrada debe ser un objeto.")
            continue
        cid = dc.get("claim_id")
        if not _str(cid):
            errors.append(f"{cl}: 'claim_id' es obligatorio.")
            continue
        if cid not in por_id:
            errors.append(
                f"{cl}: el claim {cid!r} no viaja en el handoff {hid!r}. "
                "Un artefacto no puede reclamar respaldo de un claim que no le fue entregado."
            )
            continue
        h = HASH_HEX_64.match(dc.get("approved_claim_hash") or "")
        if not h:
            errors.append(f"{cl}: 'approved_claim_hash' debe ser 64 hexadecimales.")
            continue
        if dc["approved_claim_hash"] != por_id[cid].get("approved_claim_hash"):
            errors.append(
                f"{cl}: 'approved_claim_hash' no coincide con el que transporta el handoff. "
                "La procedencia declarada por el artefacto es incoherente con lo aprobado."
            )
            continue
        claim = claims_packet.get(cid)
        if claim is None:
            errors.append(f"{cl}: el claim {cid!r} no existe en el claim packet.")
            continue
        real = claim_mod.compute_content_hash(claim)
        if dc["approved_claim_hash"] != real:
            errors.append(
                f"{cl}: 'approved_claim_hash' no coincide con el hash canónico actual del claim. "
                "El contenido cambió después de aprobarse."
            )
            continue
        # La capa jurisdiccional declarada por el artefacto debe ser la del claim.
        alcance = claim.get("alcance")
        if proc.get("jurisdiction_layer") != alcance:
            errors.append(
                f"{cl}: 'jurisdiction_layer' declarada {proc.get('jurisdiction_layer')!r} "
                f"no coincide con el alcance del claim ({alcance!r}). La jurisdicción no se "
                "reetiqueta al pasar a producción."
            )

    return errors


def validate_no_aplica(proc, label):
    errors = []
    motivo = proc.get("motivo_no_aplica")
    if motivo not in VALID_MOTIVOS_NO_APLICA:
        errors.append(
            f"{label}.procedencia: modo NO_APLICA exige 'motivo_no_aplica' tipificado "
            f"(uno de {sorted(VALID_MOTIVOS_NO_APLICA)}), es {motivo!r}. "
            "'No aplica' sin motivo tipificado sería una vía de escape."
        )
    if not _str(proc.get("justificacion_no_aplica")) or len(proc["justificacion_no_aplica"].strip()) < 30:
        errors.append(
            f"{label}.procedencia: modo NO_APLICA exige 'justificacion_no_aplica' que explique "
            "por qué esta pieza no contiene afirmación jurídica verificable (mínimo 30 caracteres)."
        )
    if not _str(proc.get("autorizado_por")):
        errors.append(
            f"{label}.procedencia: modo NO_APLICA exige 'autorizado_por' — decidir que una pieza "
            "no lleva claim jurídico es una decisión humana con responsable."
        )
    fecha = proc.get("fecha_autorizacion")
    if not _str(fecha) or not ISO_DATE.match(fecha):
        errors.append(f"{label}.procedencia: modo NO_APLICA exige 'fecha_autorizacion' ISO válida.")
    if proc.get("jurisdiction_layer") != "NO_APLICA":
        errors.append(
            f"{label}.procedencia: modo NO_APLICA exige 'jurisdiction_layer' = 'NO_APLICA', "
            f"es {proc.get('jurisdiction_layer')!r}."
        )
    return errors


def validate_artifact(art, label, handoffs, claim_mod, chain_mod):
    errors = []
    if not isinstance(art, dict):
        return [f"{label}: el artefacto no es un objeto JSON."]

    proc = art.get("procedencia")
    if not isinstance(proc, dict):
        return [
            f"{label}: falta el objeto 'procedencia'. Ningún contenido puede renderizarse "
            "como pieza publicable sin declarar de dónde viene. No hay modo por defecto."
        ]

    modo = proc.get("modo")
    if modo not in VALID_MODOS:
        return [f"{label}.procedencia: 'modo' inválido: {modo!r} (uno de {sorted(VALID_MODOS)})."]

    if not CONTENT_ID.match(proc.get("content_id") or ""):
        errors.append(
            f"{label}.procedencia: 'content_id' inválido "
            "(mayúsculas, dígitos y guiones, 3-64 caracteres)."
        )

    publicable = proc.get("publicable")
    if not isinstance(publicable, bool):
        errors.append(f"{label}.procedencia: 'publicable' debe ser booleano explícito.")

    if modo == "EJEMPLO_TECNICO":
        if publicable is not False:
            errors.append(
                f"{label}.procedencia: modo EJEMPLO_TECNICO exige 'publicable': false. "
                "El material de prueba del pipeline no entra en la cadena gobernada."
            )
        return errors

    # A partir de aquí: contenido que aspira a publicarse.
    if publicable is not True:
        errors.append(
            f"{label}.procedencia: modo {modo} describe contenido publicable; "
            "'publicable' debe ser true (o el modo correcto es EJEMPLO_TECNICO)."
        )
    errors.extend(validate_taxonomia(art, label))

    if proc.get("jurisdiction_layer") not in VALID_JURISDICTION_LAYER:
        errors.append(
            f"{label}.procedencia: 'jurisdiction_layer' inválida: "
            f"{proc.get('jurisdiction_layer')!r} (una de {sorted(VALID_JURISDICTION_LAYER)})."
        )

    if modo == "GOBERNADO":
        errors.extend(validate_gobernado(proc, art, label, handoffs, claim_mod, chain_mod))
    else:
        errors.extend(validate_no_aplica(proc, label))
    return errors


# ---------------------------------------------------------------------------
# Anti-duplicados entre artefactos
# ---------------------------------------------------------------------------

def validate_duplicates(artifacts):
    """Controles deterministas y baratos contra la producción masiva repetida.

    Detecta: el mismo content_id, el mismo id de composición, la misma frase con
    otro ID, y la misma casilla de taxonomía ocupada dos veces. NO detecta
    paráfrasis: eso exigiría un motor semántico, y hoy no lo hay.
    """
    errors = []
    por_content_id, por_composicion, por_huella, por_concepto = {}, {}, {}, {}

    for label, art in artifacts:
        if not isinstance(art, dict):
            continue
        proc = art.get("procedencia") or {}
        publicable = proc.get("publicable") is True

        cid = proc.get("content_id")
        if _str(cid):
            if cid in por_content_id:
                errors.append(
                    f"{label}: content_id duplicado: {cid!r} (ya en {por_content_id[cid]}). "
                    "Un Content ID identifica una pieza y solo una."
                )
            else:
                por_content_id[cid] = label

        comp = art.get("id")
        if _str(comp):
            if comp in por_composicion:
                errors.append(f"{label}: id de composición duplicado: {comp!r} (ya en {por_composicion[comp]}).")
            else:
                por_composicion[comp] = label

        if not publicable:
            continue

        huella = normalize_fingerprint(art.get("frase"))
        if huella:
            if huella in por_huella:
                errors.append(
                    f"{label}: la frase publicable es la misma que la de {por_huella[huella]} "
                    "salvo mayúsculas, tildes o signos — es la misma pieza con otro ID."
                )
            else:
                por_huella[huella] = label

        tax = art.get("taxonomia")
        if isinstance(tax, dict):
            clave = tuple(normalize_fingerprint(tax.get(f)) for f in ("materia", "submateria", "concepto"))
            if all(clave):
                if clave in por_concepto:
                    errors.append(
                        f"{label}: la casilla de taxonomía {clave} ya está ocupada por "
                        f"{por_concepto[clave]} — el mismo concepto no se produce dos veces."
                    )
                else:
                    por_concepto[clave] = label
    return errors


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def collect(paths):
    artifacts, errors = [], []
    for p in paths:
        path = Path(p)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"FALLÓ: no se pudo leer/parsear {path}: {exc}")
            continue
        artifacts.append((str(_repo_relative(path)), data))
    return artifacts, errors


def main(argv):
    ap = argparse.ArgumentParser(description="Valida la procedencia de los artefactos de contenido.")
    ap.add_argument("files", nargs="*", help="Artefactos JSON; vacío = todo content/.")
    args = ap.parse_args(argv)

    paths = [Path(f) for f in args.files] or sorted(CONTENT_DIR.glob("*.json"))
    if not paths:
        print(f"FALLÓ: no hay artefactos de contenido en {CONTENT_DIR}.", file=sys.stderr)
        return 1

    try:
        claim_mod, chain_mod = load_validators()
    except (ImportError, OSError, SyntaxError) as exc:
        print(f"FALLÓ: no se pudieron cargar los validadores de la skill: {exc}", file=sys.stderr)
        return 1

    handoffs, handoff_errors = load_handoffs(chain_mod)
    artifacts, read_errors = collect(paths)

    all_errors = list(read_errors) + list(handoff_errors)
    for label, art in artifacts:
        all_errors.extend(validate_artifact(art, label, handoffs, claim_mod, chain_mod))
    all_errors.extend(validate_duplicates(artifacts))

    if all_errors:
        print("[PROCEDENCIA INVÁLIDA]")
        for e in all_errors:
            print(f"  - {e}")
        return 1

    gobernados = sum(1 for _l, a in artifacts
                     if (a.get("procedencia") or {}).get("modo") == "GOBERNADO")
    publicables = sum(1 for _l, a in artifacts
                      if (a.get("procedencia") or {}).get("publicable") is True)
    print(
        f"[PROCEDENCIA VÁLIDA] {len(artifacts)} artefacto(s): "
        f"{gobernados} gobernado(s), {publicables} publicable(s)."
    )
    print("Recordatorio: procedencia verificable habilita PRODUCIR, no publicar. "
          "Publicar exige una PublicationDecision humana.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
