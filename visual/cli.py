#!/usr/bin/env python3
"""CLI minima del pipeline visual.

Permite que otro agente (o una persona) ejerza la arquitectura sin escribir
codigo. Nunca llama a un proveedor real: el unico proveedor registrado es el
falso.

    python3 cli.py families
    python3 cli.py policy
    python3 cli.py validate   <artefacto.json>
    python3 cli.py dry-run    <artefacto.json> [--handoff h.json]
    python3 cli.py simulate   <artefacto.json> [--handoff h.json] [--out DIR]
    python3 cli.py batch-dry-run <dir_con_artefactos>
    python3 cli.py show-receipt   <DIR> <CONTENT_ID> <GENERATION_ID>
    python3 cli.py show-history   <DIR> <CONTENT_ID>
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import canonical
import pipeline
import registry as registry_mod
from brief import VisualBrief, VisualPolicy
from errors import VisualInputInvalidError
from families import VisualFamilyRegistry
from providers import FakeImageProvider


def _load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def brief_desde(vi, policy, fams):
    """Brief minimo derivado del artefacto. No sustituye al criterio humano."""
    familia = fams.names()[0]
    return VisualBrief(
        content_id=vi.content_id,
        formato="VERTICAL_9_16",
        visual_family=familia,
        subject="escena derivada del artefacto (placeholder de CLI)",
        environment="entorno segun familia visual",
        camera=fams.get(familia).camera_tendencies[0],
        focal_point="objeto principal",
        acento_frio_objeto="objeto de vidrio azul petroleo",
        marca_superficie=fams.get(familia).brand_surface_preferences[0],
    )


def main(argv=None):
    ap = argparse.ArgumentParser(description="Pipeline visual de LegalMente (proveedor falso).")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("families")
    sub.add_parser("policy")
    for c in ("validate", "dry-run", "simulate"):
        s = sub.add_parser(c)
        s.add_argument("artefacto")
        s.add_argument("--handoff")
        if c == "simulate":
            s.add_argument("--out", default="artifacts/visual")
    s = sub.add_parser("batch-dry-run"); s.add_argument("directorio")
    s = sub.add_parser("show-receipt")
    s.add_argument("root"); s.add_argument("content_id"); s.add_argument("generation_id")
    s = sub.add_parser("show-history"); s.add_argument("root"); s.add_argument("content_id")
    a = ap.parse_args(argv)

    policy = VisualPolicy.load()
    fams = VisualFamilyRegistry.load()

    if a.cmd == "families":
        for n in fams.names():
            print(f"  {n}")
        return 0

    if a.cmd == "policy":
        print(f"policy_version={policy.version}")
        print(f"formatos={sorted(policy.data['formatos'])}")
        print(f"marca.generador_escribe_texto={policy.marca_escribe_generador}")
        return 0

    if a.cmd in ("validate", "dry-run", "simulate"):
        art = _load(a.artefacto)
        handoff = _load(a.handoff) if a.handoff else None
        try:
            vi = canonical.build_visual_input(art, handoff)
        except VisualInputInvalidError as exc:
            print(f"RECHAZADO: {exc}")
            return 1
        if a.cmd == "validate":
            print(f"OK content_id={vi.content_id} modo={vi.provenance_mode} "
                  f"gate={vi.art_gate_state} claims={len(vi.claim_refs)}")
            return 0

        brief = brief_desde(vi, policy, fams)
        reg = registry_mod.AssetRegistry(a.out) if a.cmd == "simulate" else None
        run = pipeline.generate_visual(
            art["procedencia"], brief, policy, FakeImageProvider(), handoff=handoff,
            family=fams.get(brief.visual_family), families_version=fams.version,
            dry_run=(a.cmd == "dry-run"), registry=reg,
            exact_copy=vi.exact_copy, author=vi.author, content_type=vi.content_type)
        print(f"status={run.receipt.status} generation_id={run.receipt.generation_id}")
        if run.plan:
            print(f"plan_hash={run.plan.plan_hash()[:16]} compat={run.plan.provider_compatibility} "
                  f"brand={run.plan.brand_mode} text={run.plan.text_mode}")
            for e in run.plan.explanation:
                print(f"  · {e}")
        for m in run.receipt.motivos:
            print(f"  ! {m}")
        return 0 if run.receipt.status in ("DRY_RUN", "PENDIENTE_REVISION_HUMANA") else 1

    if a.cmd == "batch-dry-run":
        items = []
        for f in sorted(Path(a.directorio).glob("*.json")):
            art = _load(f)
            proc = art.get("procedencia", {})
            items.append(pipeline.BatchItem(
                proc, brief_desde(canonical.VisualInput(
                    content_id=proc.get("content_id", f.stem), provenance_mode=proc.get("modo", ""),
                    jurisdiction_layer="", publicable=False), policy, fams),
                None, art.get("frase", "")))
        batch = pipeline.run_batch(items, policy, FakeImageProvider(), dry_run=True)
        s = batch.summary()
        print(json.dumps(s, indent=2))
        return 0

    reg = registry_mod.AssetRegistry(a.root)
    if a.cmd == "show-receipt":
        r = reg.get_generation(a.content_id, a.generation_id)
        print(json.dumps(r, ensure_ascii=False, indent=2) if r else "no encontrado")
        return 0 if r else 1
    if a.cmd == "show-history":
        for g in reg.generations_for(a.content_id):
            print(f"{g['created_at']}  {g['generation_id']}  {g['status']}  "
                  f"parent={g.get('parent_generation_id') or '-'}")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
