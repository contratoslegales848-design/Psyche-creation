#!/usr/bin/env python3
"""Reporte tecnico de bloqueo de los claim packets.

Un packet con el gate cerrado NO puede producir copy publicable, prompt visual
ni handshake web: eso seria una salida de autoridad sobre evidencia que no
existe. Lo que si puede producir es este reporte, que dice exactamente QUE
falta y CUAL es la siguiente accion tecnica por claim.

Es deliberadamente derivado: no escribe nada que no este ya en los packets. Si
un packet cambia, el reporte cambia con el; no hay una segunda fuente que
mantener sincronizada a mano.

Uso:
    python3 scripts/report_blocked_packets.py            # tabla legible
    python3 scripts/report_blocked_packets.py --json     # para otro programa

Sin red. Sin escritura sobre los packets. Determinista.
"""

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PACKETS_DIR = REPO / "content" / "claim-packets"

# Salidas que un packet bloqueado NO puede producir. La lista es explicita para
# que anadir una salida nueva obligue a decidir si respeta el gate.
SALIDAS_DE_AUTORIDAD = ("copy_social.md", "visual_prompt.json", "handshake_web.json")


def _motivo_de_bloqueo(claim):
    """Por que este claim no puede producir salida, en orden de gravedad."""
    motivos = []
    estado = claim.get("estado")
    if estado == "BLOQUEADO":
        motivos.append("claim BLOQUEADO: investigacion concluyo en contra")
    elif estado == "REQUIERE_INVESTIGACION":
        motivos.append("falta evidencia primaria")
    elif estado == "APTO_CON_MATICES":
        motivos.append("evidencia insuficiente para narrativa sin matices")

    if claim.get("alcance") == "NO_DETERMINADO":
        motivos.append("alcance sin determinar: no se sabe que territorio cubre")

    sin_nivel1 = []
    for f in claim.get("fuentes", []):
        v = f.get("verificacion_fuente", {})
        faltan = []
        if not v.get("texto_exacto_consultado"):
            faltan.append("texto no leido")
        if not v.get("vigencia_comprobada"):
            faltan.append("vigencia no comprobada")
        if f.get("registro_oficial_id") is None and f.get("tipo_fuente", "").endswith("OFICIAL"):
            faltan.append("organismo sin entrada en el registro")
        if faltan:
            sin_nivel1.append(f"{f['id']} ({', '.join(faltan)})")
    if sin_nivel1:
        motivos.append("ninguna fuente alcanza Nivel 1: " + "; ".join(sin_nivel1))

    rev = claim.get("revision_humana", {}) or {}
    if rev.get("estado") != "APROBADO":
        motivos.append(f"revision humana {rev.get('estado', 'AUSENTE')}")

    pr = claim.get("platform_review", {}) or {}
    if pr.get("required") and pr.get("status") not in ("NO_APLICA", "APROBADO"):
        motivos.append(f"platform_review {pr.get('status')}")

    return motivos


def analizar():
    if not PACKETS_DIR.is_dir():
        return []
    reporte = []
    for ruta in sorted(PACKETS_DIR.glob("*.json")):
        datos = json.loads(ruta.read_text(encoding="utf-8"))
        for claim in datos.get("claims", []):
            bloqueado = datos.get("gate_global_arte") != "ABIERTO"
            reporte.append({
                "archivo": ruta.name,
                "piece_id": datos.get("piece_id"),
                "claim_id": claim.get("claim_id"),
                "alcance": claim.get("alcance"),
                "jurisdiccion": claim.get("jurisdiccion"),
                "estado": claim.get("estado"),
                "gate_arte": claim.get("gate_arte"),
                "gate_global": datos.get("gate_global_arte"),
                "publicacion": "NOT_PUBLISHED",
                "salidas_permitidas": [] if bloqueado else list(SALIDAS_DE_AUTORIDAD),
                "salidas_bloqueadas": list(SALIDAS_DE_AUTORIDAD) if bloqueado else [],
                "motivos_de_bloqueo": _motivo_de_bloqueo(claim),
                "siguiente_accion": claim.get("notas") or "",
            })
    return reporte


def imprimir_tabla(reporte):
    print(f"{'PIEZA':<14} {'CLAIM':<22} {'ALCANCE':<20} {'ESTADO':<24} GATE")
    print("-" * 96)
    for r in reporte:
        print(f"{r['piece_id']:<14} {r['claim_id']:<22} {str(r['alcance']):<20} "
              f"{r['estado']:<24} {r['gate_arte']}")
    print()
    bloqueados = [r for r in reporte if r["salidas_bloqueadas"]]
    print(f"claims totales      : {len(reporte)}")
    print(f"claims bloqueados   : {len(bloqueados)}")
    print(f"salidas de autoridad: {sum(len(r['salidas_permitidas']) for r in reporte)} permitidas")
    print()
    if bloqueados:
        print("MOTIVOS POR CLAIM")
        for r in bloqueados:
            print(f"\n  {r['claim_id']}")
            for m in r["motivos_de_bloqueo"]:
                print(f"    - {m}")


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--json", action="store_true", help="salida legible por maquina")
    args = p.parse_args(argv)
    reporte = analizar()
    if args.json:
        json.dump(reporte, sys.stdout, ensure_ascii=False, indent=2)
        print()
    else:
        imprimir_tabla(reporte)
    # Codigo 0 siempre: informar de un bloqueo no es un fallo del programa.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
