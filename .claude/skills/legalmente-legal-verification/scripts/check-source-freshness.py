#!/usr/bin/env python3
"""Vigencia de fuentes (source freshness) de LegalMente.

Riesgo que cierra
-----------------
Una fuente oficial puede derogarse, sustituirse o cambiar de URL y seguir
sosteniendo un claim ya aprobado. El validador jurídico no lo detecta —y no debe
detectarlo—, porque **no tiene red por diseño**: una skill que descarga páginas
durante la validación se puede envenenar desde fuera.

Cómo lo cierra
--------------
Separando la *investigación* de la *validación*. Un humano actualiza el libro
mayor de fuentes (`references/source-freshness.json`) como operación aparte; este
script es determinista, offline y sin reloj de red, y solo comprueba coherencia:

    FUENTE DESACTUALIZADA  →  CLAIM REQUIERE REVISIÓN

El veredicto se **deriva**, nunca se escribe dentro del claim packet. Escribirlo
cambiaría el contenido del claim y, por tanto, su `contenido_hash_sha256`,
invalidando en silencio la aprobación humana ya firmada. El contenido aprobado no
se toca: lo que ocurre es que el sistema deja de dejarlo avanzar.

Estados de una fuente
---------------------
| Estado | Significa |
|---|---|
| `CURRENT`      | un humano comprobó su vigencia y no consta sustituida |
| `NEEDS_REVIEW` | vencido el plazo de revisión, o marcado para revisar |
| `SUPERSEDED`   | sustituida por otra fuente registrada |
| `REPEALED`     | derogada |
| `UNKNOWN`      | registrada, pero sin comprobación de vigencia |

Veredicto de un claim (derivado, nunca almacenado)
--------------------------------------------------
| Veredicto | Cuándo |
|---|---|
| `CURRENT`           | todas sus fuentes registradas y CURRENT |
| `REQUIERE_REVISION` | alguna NEEDS_REVIEW, sin registrar, o UNKNOWN donde hace falta vigencia |
| `BLOQUEADO`         | alguna SUPERSEDED o REPEALED |

Regla fail-closed: un claim con `gate_arte: ABIERTO` cuyo veredicto no sea
`CURRENT` es un ERROR. Con el gate cerrado es una advertencia — todavía no hay
nada en riesgo.

Uso:
    python3 scripts/check-source-freshness.py pilot/claim-packets/*.json
    python3 scripts/check-source-freshness.py --today 2026-08-27 <paquetes...>
    python3 scripts/check-source-freshness.py --solo-libro-mayor
"""
import argparse
import hashlib
import json
import re
import sys
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

SKILL_ROOT = Path(__file__).resolve().parent.parent
LEDGER_PATH = SKILL_ROOT / "references" / "source-freshness.json"
REGISTRY_PATH = SKILL_ROOT / "references" / "official-source-registry.json"

LEDGER_VERSION = "1.0"

VALID_STATUS = {"CURRENT", "NEEDS_REVIEW", "SUPERSEDED", "REPEALED", "UNKNOWN"}
STATUS_QUE_BLOQUEAN = {"SUPERSEDED", "REPEALED"}

# Tipos de fuente para los que la vigencia es imprescindible: una norma que ya no
# está en vigor no sostiene nada. Una sentencia o una fuente secundaria no
# "caducan" del mismo modo, aunque puedan quedar superadas.
TIPOS_QUE_EXIGEN_VIGENCIA = {"NORMA_OFICIAL"}

# Plazo de revisión por tipo. No es una verdad jurídica: es la frecuencia con la
# que la casa se obliga a volver a mirar.
REVIEW_WINDOW_DAYS = {
    "NORMA_OFICIAL": 180,
    "JURISPRUDENCIA_OFICIAL": 365,
    "AUTORIDAD_PUBLICA_OFICIAL": 365,
    "SECUNDARIA_ESPECIALIZADA": 365,
    "DOCTRINA": 730,
    "OBRA_HISTORICA": 3650,
}
DEFAULT_REVIEW_WINDOW_DAYS = 365

SOURCE_ID = re.compile(r"^SRC-[0-9a-f]{12}$")
ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

LEDGER_FIELDS = (
    "source_id", "titulo", "jurisdiction", "source_type", "canonical_url",
    "registro_oficial_id", "published_at", "effective_from", "effective_to",
    "last_verified_at", "verified_by", "verification_status", "supersedes",
    "superseded_by", "review_due_at",
)


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


def normalize_url(url):
    """Forma canónica de una URL para emparejar fuentes.

    Esquema y host en minúsculas, sin puerto por defecto, sin barra final. El
    query y el fragmento SE CONSERVAN: hay repositorios oficiales (SPIJ de Perú)
    donde la norma concreta vive en el fragmento, y descartarlo fundiría fuentes
    distintas en una sola.
    """
    if not _str(url):
        return ""
    parts = urlsplit(url.strip())
    host = parts.hostname or ""
    if parts.port and not (
        (parts.scheme == "https" and parts.port == 443)
        or (parts.scheme == "http" and parts.port == 80)
    ):
        host = f"{host}:{parts.port}"
    path = parts.path.rstrip("/") or "/"
    return urlunsplit((parts.scheme.lower(), host.lower(), path, parts.query, parts.fragment))


def source_id_for(url):
    """Identificador estable y determinista derivado de la URL canónica.

    Derivarlo del contenido —y no de un contador— significa que regenerar o
    reordenar el libro mayor nunca renumera nada.
    """
    digest = hashlib.sha256(normalize_url(url).encode("utf-8")).hexdigest()
    return f"SRC-{digest[:12]}"


def review_window_days(source_type):
    return REVIEW_WINDOW_DAYS.get(source_type, DEFAULT_REVIEW_WINDOW_DAYS)


def expected_review_due(last_verified_at, source_type):
    return (date.fromisoformat(last_verified_at)
            + timedelta(days=review_window_days(source_type))).isoformat()


# ---------------------------------------------------------------------------
# Libro mayor
# ---------------------------------------------------------------------------

def load_ledger(path=LEDGER_PATH):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_registry(path=REGISTRY_PATH):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return {e["id"]: e for e in data.get("sources", [])}


def validate_ledger(ledger, registry, today=None):
    """Coherencia interna del libro mayor. Sin reloj salvo que se pase `today`."""
    errors, warnings = [], []
    if ledger.get("ledger_version") != LEDGER_VERSION:
        errors.append(
            f"libro mayor: 'ledger_version' debe ser {LEDGER_VERSION!r}, "
            f"es {ledger.get('ledger_version')!r}."
        )
    sources = ledger.get("sources")
    if not isinstance(sources, list):
        return errors + ["libro mayor: 'sources' debe ser una lista."], warnings

    por_id, por_url = {}, {}
    for i, s in enumerate(sources):
        label = f"sources[{i}]"
        if not isinstance(s, dict):
            errors.append(f"{label}: cada entrada debe ser un objeto.")
            continue
        faltan = [f for f in LEDGER_FIELDS if f not in s]
        if faltan:
            errors.append(f"{label}: faltan campos obligatorios: {faltan!r} "
                          "(pueden ser null, pero deben existir).")
            continue

        sid = s["source_id"]
        label = f"{sid}"
        if not SOURCE_ID.match(sid or ""):
            errors.append(f"{label}: 'source_id' debe tener la forma SRC-<12 hex>.")
        elif sid != source_id_for(s.get("canonical_url")):
            errors.append(
                f"{label}: 'source_id' no se deriva de su 'canonical_url'. "
                "El identificador es una función de la URL canónica; si la URL cambia, "
                "es OTRA fuente y necesita su propia entrada con supersedes/superseded_by."
            )
        if sid in por_id:
            errors.append(f"{label}: 'source_id' duplicado.")
        por_id[sid] = s

        url = normalize_url(s.get("canonical_url"))
        if not url.startswith(("http://", "https://")):
            errors.append(f"{label}: 'canonical_url' debe ser http/https.")
        elif url in por_url:
            errors.append(
                f"{label}: 'canonical_url' duplicada (ya en {por_url[url]}). "
                "Dos entradas para la misma fuente crearían dos verdades sobre su vigencia."
            )
        else:
            por_url[url] = sid

        status = s.get("verification_status")
        if status not in VALID_STATUS:
            errors.append(f"{label}: 'verification_status' inválido: {status!r} "
                          f"(uno de {sorted(VALID_STATUS)}).")
            continue

        for campo in ("published_at", "effective_from", "effective_to", "last_verified_at"):
            v = s.get(campo)
            if v is not None and not _iso(v):
                errors.append(f"{label}: '{campo}' debe ser fecha ISO o null, es {v!r}.")

        # --- vigencia declarada ---
        if status == "CURRENT":
            if not _iso(s.get("last_verified_at")):
                errors.append(f"{label}: CURRENT exige 'last_verified_at' ISO — alguien tuvo "
                              "que comprobarlo, y cuándo.")
            if not _str(s.get("verified_by")):
                errors.append(f"{label}: CURRENT exige 'verified_by' identificado — la "
                              "comprobación de vigencia es un acto humano con responsable.")
            if s.get("effective_to") is not None:
                errors.append(f"{label}: CURRENT con 'effective_to' declarado es contradictorio: "
                              "una fuente con fecha de fin no está vigente sin más.")
            if s.get("superseded_by") is not None:
                errors.append(f"{label}: CURRENT no puede declarar 'superseded_by'.")

        if status in STATUS_QUE_BLOQUEAN:
            if not _str(s.get("verified_by")):
                errors.append(f"{label}: marcar {status} exige 'verified_by' — retirar una "
                              "fuente también es una decisión con responsable.")
        if status == "SUPERSEDED" and not _str(s.get("superseded_by")):
            errors.append(f"{label}: SUPERSEDED exige 'superseded_by' — decir que algo fue "
                          "sustituido sin decir por qué fuente no es información utilizable.")

        # --- plazo de revisión ---
        if _iso(s.get("last_verified_at")):
            esperado = expected_review_due(s["last_verified_at"], s.get("source_type"))
            if s.get("review_due_at") != esperado:
                errors.append(
                    f"{label}: 'review_due_at' debe ser last_verified_at + "
                    f"{review_window_days(s.get('source_type'))} días ({esperado}), "
                    f"es {s.get('review_due_at')!r}."
                )
        elif s.get("review_due_at") is not None:
            errors.append(f"{label}: sin 'last_verified_at' no puede haber 'review_due_at'.")

        # --- coherencia con el registro de organismos (autoridad única) ---
        reg_id = s.get("registro_oficial_id")
        if reg_id is not None:
            entrada = registry.get(reg_id)
            if entrada is None:
                errors.append(f"{label}: 'registro_oficial_id' {reg_id!r} no existe en el "
                              "registro de organismos oficiales.")
            else:
                host = (urlsplit(s.get("canonical_url") or "").hostname or "").lower()
                if not any(host == h or host.endswith("." + h) for h in entrada.get("hostnames", [])):
                    errors.append(
                        f"{label}: el hostname {host!r} no pertenece al organismo "
                        f"{reg_id!r} ({entrada.get('hostnames')}). Se compara por frontera "
                        "real de subdominio, nunca por subcadena."
                    )
                if s.get("jurisdiction") not in entrada.get("jurisdicciones", []):
                    errors.append(
                        f"{label}: jurisdicción {s.get('jurisdiction')!r} no está entre las "
                        f"del organismo {reg_id!r} ({entrada.get('jurisdicciones')})."
                    )
                if s.get("source_type") not in entrada.get("tipos_fuente_permitidos", []):
                    errors.append(
                        f"{label}: tipo {s.get('source_type')!r} no permitido para el "
                        f"organismo {reg_id!r} ({entrada.get('tipos_fuente_permitidos')})."
                    )

    # --- enlaces de sustitución ---
    for sid, s in por_id.items():
        destino = s.get("superseded_by")
        if destino is not None:
            if destino not in por_id:
                errors.append(f"{sid}: 'superseded_by' apunta a {destino!r}, que no está "
                              "registrado. La fuente sustituta debe existir.")
            elif sid not in (por_id[destino].get("supersedes") or []):
                errors.append(
                    f"{sid}: enlace de sustitución asimétrico — {destino} no declara "
                    f"'supersedes' con {sid}. Un enlace en un solo sentido se pierde al leer "
                    "desde el otro lado."
                )
        for anterior in s.get("supersedes") or []:
            if anterior not in por_id:
                errors.append(f"{sid}: 'supersedes' menciona {anterior!r}, que no está registrado.")
            elif por_id[anterior].get("superseded_by") != sid:
                errors.append(f"{sid}: enlace de sustitución asimétrico con {anterior}.")

    # --- ciclos ---
    for sid in por_id:
        visto, actual = set(), sid
        while actual is not None and actual in por_id:
            if actual in visto:
                errors.append(f"{sid}: cadena de sustitución cíclica — una fuente no puede "
                              "acabar sustituyéndose a sí misma.")
                break
            visto.add(actual)
            actual = por_id[actual].get("superseded_by")

    # --- reloj (opcional) ---
    if today is not None:
        for sid, s in por_id.items():
            due = s.get("review_due_at")
            if _iso(due) and date.fromisoformat(due) <= today and s.get("verification_status") == "CURRENT":
                warnings.append(
                    f"{sid}: 'review_due_at' ({due}) vencido el {today.isoformat()} — "
                    "se trata como NEEDS_REVIEW aunque el libro mayor diga CURRENT."
                )
    return errors, warnings


def effective_status(entry, today=None):
    """Estado efectivo: el declarado, degradado por el reloj si procede."""
    status = entry.get("verification_status")
    if today is None or status != "CURRENT":
        return status
    due = entry.get("review_due_at")
    if _iso(due) and date.fromisoformat(due) <= today:
        return "NEEDS_REVIEW"
    return status


# ---------------------------------------------------------------------------
# Veredicto por claim
# ---------------------------------------------------------------------------

def claim_freshness(claim, por_url, today=None):
    """Deriva el veredicto de frescura de un claim. NUNCA lo escribe en el claim."""
    motivos, veredicto = [], "CURRENT"
    for fuente in claim.get("fuentes") or []:
        fid = fuente.get("id")
        url = normalize_url(fuente.get("url"))
        tipo = fuente.get("tipo_fuente")
        entrada = por_url.get(url) if url else None

        if entrada is None:
            motivos.append((fid, "SIN_REGISTRAR",
                            "la fuente no está en el libro mayor de vigencia"))
            veredicto = "REQUIERE_REVISION" if veredicto != "BLOQUEADO" else veredicto
            continue

        status = effective_status(entrada, today)
        if status in STATUS_QUE_BLOQUEAN:
            motivos.append((fid, status, f"la fuente está {status.lower()}"))
            veredicto = "BLOQUEADO"
        elif status == "NEEDS_REVIEW":
            motivos.append((fid, status, "la fuente necesita revisión"))
            if veredicto != "BLOQUEADO":
                veredicto = "REQUIERE_REVISION"
        elif status == "UNKNOWN":
            if tipo in TIPOS_QUE_EXIGEN_VIGENCIA:
                motivos.append((fid, status,
                                f"vigencia desconocida y el tipo {tipo} la exige"))
                if veredicto != "BLOQUEADO":
                    veredicto = "REQUIERE_REVISION"
            else:
                motivos.append((fid, "UNKNOWN_TOLERADO",
                                f"vigencia desconocida, tolerada para el tipo {tipo}"))
    return veredicto, motivos


def check_pieces(paths, ledger, today=None):
    """Aplica el veredicto a cada claim. Fail-closed solo donde hay algo en riesgo."""
    errors, warnings, resumen = [], [], []
    por_url = {}
    for s in ledger.get("sources", []):
        if isinstance(s, dict):
            por_url[normalize_url(s.get("canonical_url"))] = s

    for p in paths:
        path = Path(p)
        try:
            piece = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"FALLÓ: no se pudo leer/parsear {path}: {exc}")
            continue
        for idx, claim in enumerate(piece.get("claims") or []):
            label = f"{path.name}:claims[{idx}]({claim.get('claim_id')})"
            veredicto, motivos = claim_freshness(claim, por_url, today)
            resumen.append((label, veredicto, claim.get("gate_arte")))
            if veredicto == "CURRENT":
                continue
            detalle = "; ".join(f"{fid}: {texto}" for fid, _c, texto in motivos
                                if not _c.endswith("_TOLERADO"))
            if not detalle:
                continue
            mensaje = (f"{label}: veredicto de frescura {veredicto} — {detalle}.")
            if claim.get("gate_arte") == "ABIERTO":
                errors.append(
                    mensaje + " El claim está APROBADO para producción y sus fuentes ya no "
                    "lo sostienen: REQUIERE REVISIÓN HUMANA. El contenido aprobado no se "
                    "modifica; simplemente deja de poder avanzar."
                )
            else:
                warnings.append(mensaje + " (gate cerrado: todavía no hay nada en riesgo).")
    return errors, warnings, resumen


def main(argv):
    ap = argparse.ArgumentParser(description="Comprueba la vigencia de las fuentes de LegalMente.")
    ap.add_argument("files", nargs="*", help="Claim packets a comprobar.")
    ap.add_argument("--today", help="Fecha ISO para el cálculo de vencimientos (por defecto, hoy).")
    ap.add_argument("--sin-reloj", action="store_true",
                    help="Ignora los vencimientos por fecha; solo estados declarados.")
    ap.add_argument("--solo-libro-mayor", action="store_true",
                    help="Valida únicamente la coherencia del libro mayor.")
    args = ap.parse_args(argv)

    if args.sin_reloj:
        today = None
    elif args.today:
        if not _iso(args.today):
            print(f"FALLÓ: --today inválido: {args.today!r}", file=sys.stderr)
            return 1
        today = date.fromisoformat(args.today)
    else:
        today = date.today()

    try:
        ledger = load_ledger()
        registry = load_registry()
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FALLÓ: no se pudo cargar el libro mayor o el registro: {exc}", file=sys.stderr)
        return 1

    errors, warnings = validate_ledger(ledger, registry, today)

    if not args.solo_libro_mayor:
        if not args.files:
            print("Uso: check-source-freshness.py <claim-packet.json> [...] "
                  "| --solo-libro-mayor", file=sys.stderr)
            return 1
        e, w, resumen = check_pieces(args.files, ledger, today)
        errors.extend(e)
        warnings.extend(w)
    else:
        resumen = []

    for w in warnings:
        print(f"[ADVERTENCIA DE VIGENCIA] {w}")
    if errors:
        print("[VIGENCIA INVÁLIDA]")
        for e in errors:
            print(f"  - {e}")
        return 1

    total = len(ledger.get("sources", []))
    if resumen:
        frescos = sum(1 for _l, v, _g in resumen if v == "CURRENT")
        print(f"[VIGENCIA COHERENTE] {total} fuente(s) en el libro mayor; "
              f"{frescos}/{len(resumen)} claim(s) con veredicto CURRENT.")
    else:
        print(f"[VIGENCIA COHERENTE] {total} fuente(s) en el libro mayor.")
    print("Recordatorio: actualizar el libro mayor es una operación de research separada. "
          "Este script no tiene red y nunca modifica un claim packet.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
