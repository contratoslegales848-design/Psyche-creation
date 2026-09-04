"""Lista, sin ambiguedad, que fuente sigue sin verificacion primaria.

Hoy eso se revisa abriendo cada claim-packet a mano. Este script solo
agrega lo que ya esta escrito en cada JSON -- no infiere nada, no marca
nada como verificado, no toca ningun archivo. Su unica utilidad es
ahorrar la lectura manual de N archivos para encontrar la siguiente accion
ejecutable real (leer un texto oficial concreto).

Nivel 1 de verificacion (`legalmente-legal-verification`) exige los tres
booleanos en true: `origen_oficial_confirmado`, `texto_exacto_consultado`,
`vigencia_comprobada`. Una fuente con cualquiera de los tres en false
sigue bloqueando el gate de arte de su claim.

Sin red. Determinista. Solo lectura.
"""

import json
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent

CAMPOS_NIVEL_1 = ("origen_oficial_confirmado", "texto_exacto_consultado", "vigencia_comprobada")


def _fuentes_pendientes(claim):
    pendientes = []
    for fuente in claim.get("fuentes") or []:
        v = fuente.get("verificacion_fuente") or {}
        faltan = [c for c in CAMPOS_NIVEL_1 if not v.get(c)]
        if faltan:
            pendientes.append({
                "fuente_id": fuente.get("id"),
                "titulo": fuente.get("titulo"),
                "url": fuente.get("url"),
                "jurisdicciones": fuente.get("jurisdicciones_cubiertas"),
                "campos_pendientes": faltan,
                "observaciones": v.get("observaciones") or "",
            })
    return pendientes


def brecha_del_paquete(path):
    """Un paquete -> lista de {claim_id, estado, fuentes_pendientes}."""
    datos = json.loads(Path(path).read_text(encoding="utf-8"))
    resultado = []
    for claim in datos.get("claims", []):
        pendientes = _fuentes_pendientes(claim)
        if pendientes:
            resultado.append({
                "piece_id": datos.get("piece_id"),
                "claim_id": claim.get("claim_id"),
                "estado": claim.get("estado"),
                "fuentes_pendientes": pendientes,
            })
    return resultado


def brecha_del_directorio(directorio=None):
    directorio = Path(directorio) if directorio else AQUI
    filas = []
    for archivo in sorted(directorio.glob("*.json")):
        filas.extend(brecha_del_paquete(archivo))
    return filas


def main(argv=None):
    import argparse

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--directorio", default=None)
    args = ap.parse_args(argv)

    filas = brecha_del_directorio(args.directorio)

    if args.json:
        print(json.dumps(filas, ensure_ascii=False, indent=2))
        return 0

    if not filas:
        print("Sin brechas: todas las fuentes tienen nivel 1 completo (o no hay claim-packets).")
        return 0

    total_fuentes = sum(len(f["fuentes_pendientes"]) for f in filas)
    print(f"{len(filas)} claims con fuentes pendientes, {total_fuentes} fuentes en total.\n")
    for fila in filas:
        print(f"[{fila['piece_id']}] {fila['claim_id']}  (estado: {fila['estado']})")
        for f in fila["fuentes_pendientes"]:
            print(f"    - {f['fuente_id']}: {f['titulo']}")
            print(f"      falta: {', '.join(f['campos_pendientes'])}")
            if f["observaciones"]:
                print(f"      nota: {f['observaciones']}")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
