#!/usr/bin/env python3
"""Control de gobernanza para los paquetes reales del piloto (no fixtures).

Verifica, sobre un claim packet ya estructuralmente válido, que ningún gate
de arte esté abierto y que ninguna revisión humana esté ya aprobada — el
piloto debe permanecer con aprobación humana pendiente hasta que un revisor
real lo apruebe fuera de este script. No sustituye a validate-claim-packet.py
(que ya calcula gate_arte/gate_global_arte de forma fail-closed): esta
verificación es una salvaguarda adicional explícita para CI, para que un
paquete del piloto con el gate abierto por error nunca pase inadvertido.

Uso: python3 check_pilot_governance.py <archivo.json> [<archivo2.json> ...]
Sale con 0 si todos los archivos cumplen; con 1 si alguno no cumple o no es
JSON válido.
"""
import json
import sys


def check_pilot_governance(piece):
    """Devuelve una lista de problemas (vacía si todo está en orden)."""
    problems = []
    if piece.get("schema_version") != "4.0":
        problems.append(
            f"schema_version debe ser exactamente '4.0', es {piece.get('schema_version')!r}"
        )
    if piece.get("gate_global_arte") != "CERRADO":
        problems.append(
            f"gate_global_arte debe ser 'CERRADO' en el piloto, es {piece.get('gate_global_arte')!r}"
        )
    for claim in piece.get("claims", []):
        claim_id = claim.get("claim_id")
        estado = claim.get("revision_humana", {}).get("estado")
        if estado != "PENDIENTE":
            problems.append(
                f"claim {claim_id!r}: revision_humana.estado debe ser 'PENDIENTE' en el piloto, es {estado!r}"
            )
        if claim.get("gate_arte") != "CERRADO":
            problems.append(
                f"claim {claim_id!r}: gate_arte debe ser 'CERRADO' en el piloto, es {claim.get('gate_arte')!r}"
            )
    return problems


def main(argv):
    if not argv:
        print("Uso: check_pilot_governance.py <archivo.json> [...]", file=sys.stderr)
        return 1
    overall_ok = True
    for path in argv:
        try:
            with open(path, encoding="utf-8") as fh:
                piece = json.load(fh)
        except (OSError, json.JSONDecodeError) as exc:
            print(f"FALLÓ: no se pudo leer/parsear {path}: {exc}")
            overall_ok = False
            continue
        problems = check_pilot_governance(piece)
        if problems:
            print(f"FALLÓ el control de gobernanza del piloto para {path}:")
            for p in problems:
                print(f"  - {p}")
            overall_ok = False
        else:
            print(f"OK: {path} — schema_version 4.0, revision_humana PENDIENTE y gate CERRADO en todos los claims.")
    return 0 if overall_ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
