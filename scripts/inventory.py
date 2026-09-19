#!/usr/bin/env python3
"""Inventario materializado de LegalMente.

Qué es
------
Un índice **derivado** de los artefactos que ya existen. Es la pieza que faltaba
para poder planificar producción a volumen: hoy cada control mira un archivo a la
vez, y a escala de cientos de piezas hace falta poder preguntar "¿qué está
publicado?", "¿qué toca medir?", "¿qué concepto ya está cubierto?".

Qué NO es
---------
**No es una base de datos nueva y no es autoridad sobre nada.** Cada dato sigue
viviendo en su artefacto:

| Dato | Vive en |
|---|---|
| taxonomía, content_id, capa | `content/*.json` |
| estado de producción | `ProductionHandoff` |
| estado de publicación, URL, vencimiento | `PublicationDecision` / `PublicationRecord` |
| estado de medición | `MeasurementRecord` |
| estado de verificación | claim packet |
| estado de las fuentes | libro mayor de vigencia |

El inventario se **regenera** desde ellos y se puede tirar sin perder nada. Si el
inventario y un artefacto discrepan, el artefacto tiene razón — y `check` está
precisamente para detectar esa discrepancia.

Determinismo
------------
La salida no lleva marca de tiempo ni nada que cambie entre ejecuciones: mismos
artefactos, mismo byte. Eso permite que `check` falle cuando el inventario está
obsoleto respecto de los artefactos (vector de red team "inventario stale").

Uso:
    python3 scripts/inventory.py build
    python3 scripts/inventory.py check
    python3 scripts/inventory.py query DUE_FOR_MEASUREMENT --today 2026-09-10
    python3 scripts/inventory.py query DUPLICADOS
"""
import argparse
import hashlib
import importlib.util
import json
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_ROOT = REPO_ROOT / ".claude" / "skills" / "legalmente-legal-verification"
DEFAULT_CONTENT_DIR = REPO_ROOT / "content"
DEFAULT_RECORDS_DIR = SKILL_ROOT / "publication" / "records"
DEFAULT_OUTPUT = REPO_ROOT / "inventory" / "inventory.json"

INVENTORY_VERSION = "1.0"

QUERIES = (
    "DUE_FOR_MEASUREMENT",   # publicadas hace 7+ días y sin medición
    "DUPLICADOS",            # colisiones deterministas
    "PUBLICADAS",
    "SIN_PUBLICAR",
    "REQUIERE_REVISION_FUENTES",
    "TODO",
)


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_helpers():
    """Reutiliza los módulos existentes en vez de reimplementar sus reglas."""
    scripts_dir = SKILL_ROOT / "scripts"
    sys.path.insert(0, str(scripts_dir))
    claim = _load(scripts_dir / "validate-claim-packet.py", "validate_claim_packet")
    freshness = _load(scripts_dir / "check-source-freshness.py", "check_source_freshness")
    provenance = _load(REPO_ROOT / "scripts" / "validate-content-provenance.py",
                       "validate_content_provenance")
    return claim, freshness, provenance


def _read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _records(records_dir):
    """Todos los registros de la cadena, aplanados y etiquetados por tipo."""
    por_tipo = {}
    if not Path(records_dir).is_dir():
        return por_tipo
    for path in sorted(Path(records_dir).rglob("*.json")):
        try:
            data = _read_json(path)
        except (OSError, json.JSONDecodeError):
            continue
        for rec in (data if isinstance(data, list) else [data]):
            if isinstance(rec, dict) and rec.get("record_type"):
                por_tipo.setdefault(rec["record_type"], []).append(rec)
    return por_tipo


# ---------------------------------------------------------------------------
# Derivación de estados
# ---------------------------------------------------------------------------

def _verification_state(claims):
    """Estado editorial agregado de los claims que respaldan la pieza."""
    if not claims:
        return "NO_APLICA"
    if any((c.get("revision_humana") or {}).get("estado") == "RECHAZADO" for c in claims):
        return "RECHAZADO"
    if all((c.get("revision_humana") or {}).get("estado") == "APROBADO" for c in claims):
        return "APROBADO"
    return "PENDIENTE_APROBACION_HUMANA"


def _territory(claims):
    """Países efectivamente revisados. Ordenado para que la salida sea estable."""
    paises = set()
    for c in claims:
        if isinstance(c.get("jurisdiccion"), str) and c["jurisdiccion"].strip():
            paises.add(c["jurisdiccion"].strip())
        for j in c.get("jurisdicciones_revisadas") or []:
            if isinstance(j, dict) and isinstance(j.get("pais"), str):
                paises.add(j["pais"].strip())
    return sorted(paises)


def _production_state(proc, handoff):
    modo = proc.get("modo")
    if modo == "EJEMPLO_TECNICO":
        return "EJEMPLO_TECNICO"
    if modo == "NO_APLICA":
        return "NO_APLICA"
    if handoff is None:
        return "SIN_HANDOFF"
    return handoff.get("status") or "DESCONOCIDO"


def _publication_state(content_id, decisions, publications):
    pubs = [p for p in publications if p.get("content_id") == content_id]
    if pubs:
        # Si hay varias, gana la más comprometida: publicada > programada > retirada.
        for estado in ("PUBLICADA", "PROGRAMADA", "RETIRADA"):
            if any(p.get("status") == estado for p in pubs):
                return estado, next(p for p in pubs if p.get("status") == estado)
        return pubs[0].get("status") or "DESCONOCIDO", pubs[0]
    decs = [d for d in decisions if d.get("content_id") == content_id]
    if any(d.get("decision") == "AUTORIZADA" for d in decs):
        return "AUTORIZADA_SIN_PUBLICAR", None
    if any(d.get("decision") == "RECHAZADA" for d in decs):
        return "RECHAZADA", None
    if decs:
        return "DECISION_PENDIENTE", None
    return "SIN_DECISION", None


def _metrics_state(content_id, publication, measurements):
    """Estado de medición SIN reloj: NO_APLICA / MEDIDA / PENDIENTE.

    El vencimiento (DUE_FOR_MEASUREMENT) se calcula en la consulta, no aquí. Si el
    inventario almacenado dependiera de la fecha, `check` empezaría a fallar solo
    por el paso del tiempo, sin que ningún artefacto hubiera cambiado — y un
    control que se rompe solo acaba desactivado.
    """
    if publication is None or publication.get("status") != "PUBLICADA":
        return "NO_APLICA"
    if any(m.get("content_id") == content_id for m in measurements):
        return "MEDIDA"
    return "PENDIENTE"


# ---------------------------------------------------------------------------
# Construcción
# ---------------------------------------------------------------------------

def build(content_dir=DEFAULT_CONTENT_DIR, records_dir=DEFAULT_RECORDS_DIR):
    """Construye el índice a partir de los artefactos. SIN reloj, a propósito.

    Todo lo que dependa de la fecha —qué toca medir, qué fuente venció su plazo de
    revisión— se calcula en `query`, no se congela aquí.
    """
    claim_mod, freshness_mod, prov_mod = load_helpers()

    ledger = freshness_mod.load_ledger()
    por_url = {
        freshness_mod.normalize_url(s.get("canonical_url")): s
        for s in ledger.get("sources", []) if isinstance(s, dict)
    }

    recs = _records(records_dir)
    handoffs = {h.get("handoff_id"): h for h in recs.get("ProductionHandoff", [])}
    decisions = recs.get("PublicationDecision", [])
    publications = recs.get("PublicationRecord", [])
    measurements = recs.get("MeasurementRecord", [])
    learnings = recs.get("Learning", [])

    items = []
    for path in sorted(Path(content_dir).glob("*.json")):
        try:
            art = _read_json(path)
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(art, dict):
            continue
        proc = art.get("procedencia") or {}
        tax = art.get("taxonomia") or {}
        content_id = proc.get("content_id")
        handoff = handoffs.get(proc.get("handoff_id")) if proc.get("handoff_id") else None

        # Claims que respaldan la pieza, leídos del claim packet del handoff.
        claims = []
        if handoff:
            packet_path = (SKILL_ROOT / (handoff.get("claim_packet") or "")).resolve()
            try:
                piece = _read_json(packet_path)
            except (OSError, json.JSONDecodeError):
                piece = {}
            declarados = {c.get("claim_id") for c in handoff.get("claims", []) if isinstance(c, dict)}
            claims = [c for c in piece.get("claims", []) if c.get("claim_id") in declarados]

        # Estado de las fuentes: se deriva con las MISMAS reglas que el checker.
        if not claims:
            source_state = "NO_APLICA"
        else:
            veredictos = [freshness_mod.claim_freshness(c, por_url, None)[0] for c in claims]
            source_state = ("BLOQUEADO" if "BLOQUEADO" in veredictos
                            else "REQUIERE_REVISION" if "REQUIERE_REVISION" in veredictos
                            else "CURRENT")

        pub_state, publication = _publication_state(content_id, decisions, publications)

        items.append({
            "content_id": content_id,
            "composition_id": art.get("id"),
            "materia": tax.get("materia"),
            "submateria": tax.get("submateria"),
            "concepto": tax.get("concepto"),
            "situacion_humana": tax.get("situacion_humana"),
            "content_type": tax.get("content_type"),
            "jurisdiction_layer": proc.get("jurisdiction_layer"),
            "territory": _territory(claims),
            "modo_procedencia": proc.get("modo"),
            "publicable": proc.get("publicable"),
            "source_state": source_state,
            "verification_state": _verification_state(claims),
            "production_state": _production_state(proc, handoff),
            "publication_state": pub_state,
            "publication_url": (publication or {}).get("publication_url"),
            "measurement_due_at": (publication or {}).get("measurement_due_at"),
            "metrics_state": _metrics_state(content_id, publication, measurements),
            "fingerprint": prov_mod.normalize_fingerprint(art.get("frase")),
            "learning_count": sum(1 for l in learnings if l.get("content_id") == content_id),
            "artifact": str(Path(path).resolve().relative_to(REPO_ROOT))
            if Path(path).resolve().is_relative_to(REPO_ROOT) else str(path),
        })

    items.sort(key=lambda i: (i["content_id"] or "", i["artifact"]))
    inventory = {
        "inventory_version": INVENTORY_VERSION,
        "_nota": (
            "ÍNDICE DERIVADO Y REGENERABLE. No es autoridad sobre ningún dato: si discrepa "
            "de un artefacto, el artefacto tiene razón. Sin marca de tiempo, a propósito: "
            "mismos artefactos, mismo byte, para que `check` pueda detectar que está obsoleto."
        ),
        "items": items,
        "duplicates": detect_duplicates(items),
    }
    return inventory


# ---------------------------------------------------------------------------
# Anti-duplicados v2
# ---------------------------------------------------------------------------

def detect_duplicates(items):
    """Colisiones deterministas. Cinco tipos, ninguno semántico.

    Lo que NO detecta, y conviene tener presente: la paráfrasis. Dos piezas que
    dicen lo mismo con otras palabras pasan los cinco controles. Cerrarlo exigiría
    embeddings o un motor semántico, que hoy no existe y que no se construye aquí.
    """
    hallazgos = []

    def colisiones(clave_fn, tipo, descripcion, solo_publicables=False):
        grupos = {}
        for it in items:
            if solo_publicables and not it.get("publicable"):
                continue
            k = clave_fn(it)
            if k is None or k == "" or (isinstance(k, tuple) and not all(k)):
                continue
            grupos.setdefault(k, []).append(it["artifact"])
        for k, arts in sorted(grupos.items(), key=lambda kv: str(kv[0])):
            if len(arts) > 1:
                hallazgos.append({
                    "tipo": tipo,
                    "clave": list(k) if isinstance(k, tuple) else k,
                    "artefactos": sorted(arts),
                    "descripcion": descripcion,
                })

    colisiones(lambda i: i["content_id"], "CONTENT_ID_REPETIDO",
               "un Content ID identifica una pieza y solo una")
    colisiones(lambda i: i["composition_id"], "COMPOSICION_REPETIDA",
               "dos artefactos renderizarían la misma composición")
    colisiones(lambda i: (i["materia"], i["submateria"], i["concepto"]),
               "CONCEPTO_REPETIDO",
               "el mismo concepto producido dos veces", solo_publicables=True)
    colisiones(lambda i: i["fingerprint"], "FINGERPRINT_IDENTICO",
               "la misma frase salvo mayúsculas, tildes y signos", solo_publicables=True)
    colisiones(lambda i: i["publication_url"], "PUBLICACION_YA_REGISTRADA",
               "dos piezas apuntan a la misma publicación")
    return hallazgos


# ---------------------------------------------------------------------------
# Consultas
# ---------------------------------------------------------------------------

def _vencida(item, today):
    """¿Publicada, sin medir y con el plazo de siete días ya cumplido?"""
    if item.get("metrics_state") != "PENDIENTE" or today is None:
        return False
    due = item.get("measurement_due_at")
    if not isinstance(due, str):
        return False
    try:
        return date.fromisoformat(due) <= today
    except ValueError:
        return False


def query(inventory, name, today=None):
    """Consultas sobre el índice. Aquí SÍ entra el reloj."""
    items = inventory.get("items", [])
    if name == "DUE_FOR_MEASUREMENT":
        return [i for i in items if _vencida(i, today)]
    if name == "DUPLICADOS":
        return inventory.get("duplicates", [])
    if name == "PUBLICADAS":
        return [i for i in items if i["publication_state"] == "PUBLICADA"]
    if name == "SIN_PUBLICAR":
        return [i for i in items if i["publication_state"] != "PUBLICADA" and i.get("publicable")]
    if name == "REQUIERE_REVISION_FUENTES":
        return [i for i in items if i["source_state"] in ("REQUIERE_REVISION", "BLOQUEADO")]
    if name == "TODO":
        return items
    raise ValueError(f"consulta desconocida: {name!r} (una de {sorted(QUERIES)})")


def serialize(inventory):
    return json.dumps(inventory, ensure_ascii=False, indent=2, sort_keys=False) + "\n"


def digest(inventory):
    """Huella del inventario, para comparar sin depender del formateo."""
    canonical = json.dumps(inventory, sort_keys=True, ensure_ascii=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv):
    ap = argparse.ArgumentParser(description="Inventario materializado de LegalMente.")
    ap.add_argument("command", choices=("build", "check", "query"))
    ap.add_argument("query_name", nargs="?", help=f"Consulta: {', '.join(QUERIES)}")
    ap.add_argument("--content-dir", default=str(DEFAULT_CONTENT_DIR))
    ap.add_argument("--records-dir", default=str(DEFAULT_RECORDS_DIR))
    ap.add_argument("--output", default=str(DEFAULT_OUTPUT))
    ap.add_argument("--today", help="Fecha ISO para los vencimientos (por defecto, hoy).")
    args = ap.parse_args(argv)

    today = date.fromisoformat(args.today) if args.today else date.today()
    inv = build(Path(args.content_dir), Path(args.records_dir))
    out = Path(args.output)

    if args.command == "build":
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(serialize(inv), encoding="utf-8")
        print(f"[INVENTARIO GENERADO] {len(inv['items'])} pieza(s) en {out.relative_to(REPO_ROOT)}; "
              f"{len(inv['duplicates'])} colisión(es).")
        return 0

    if args.command == "check":
        if not out.is_file():
            print(f"[INVENTARIO OBSOLETO] no existe {out}. Ejecuta: "
                  "python3 scripts/inventory.py build", file=sys.stderr)
            return 1
        try:
            actual = _read_json(out)
        except (OSError, json.JSONDecodeError) as exc:
            print(f"[INVENTARIO ILEGIBLE] {exc}", file=sys.stderr)
            return 1
        if digest(actual) != digest(inv):
            print("[INVENTARIO OBSOLETO] el inventario registrado no coincide con los "
                  "artefactos actuales. Los artefactos son la autoridad: regenera con "
                  "`python3 scripts/inventory.py build`.", file=sys.stderr)
            return 1
        if inv["duplicates"]:
            print("[DUPLICADOS DETECTADOS]")
            for d in inv["duplicates"]:
                print(f"  - {d['tipo']}: {d['clave']!r} en {d['artefactos']} — {d['descripcion']}")
            return 1
        print(f"[INVENTARIO AL DÍA] {len(inv['items'])} pieza(s), sin colisiones.")
        return 0

    if not args.query_name:
        print(f"Uso: inventory.py query <{'|'.join(QUERIES)}>", file=sys.stderr)
        return 1
    try:
        resultado = query(inv, args.query_name, today)
    except ValueError as exc:
        print(f"FALLÓ: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(resultado, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
