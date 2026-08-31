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
import resolver
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
    sub.add_parser("content")
    sub.add_parser("gates")
    s = sub.add_parser("resolve"); s.add_argument("content_id")
    for c in ("validate", "dry-run", "simulate"):
        s = sub.add_parser(c)
        s.add_argument("artefacto")
        s.add_argument("--handoff")
        s.add_argument("--claim-packet",
                       help="claim packet real para verificar el hash contra la aprobacion humana; "
                            "si se omite, se busca por piece_id en pilot/claim-packets/.")
        if c == "simulate":
            s.add_argument("--out", default="artifacts/visual")
    s = sub.add_parser("batch-dry-run"); s.add_argument("directorio")
    s = sub.add_parser("show-receipt")
    s.add_argument("root"); s.add_argument("content_id"); s.add_argument("generation_id")
    s = sub.add_parser("show-history"); s.add_argument("root"); s.add_argument("content_id")
    s = sub.add_parser("explain")
    s.add_argument("root"); s.add_argument("content_id"); s.add_argument("generation_id")
    a = ap.parse_args(argv)

    policy = VisualPolicy.load()
    fams = VisualFamilyRegistry.load()

    if a.cmd == "content":
        for cid, path, modo in resolver.list_content_ids():
            print(f"  {cid:28} {modo:16} {path}")
        return 0

    if a.cmd == "gates":
        for f in resolver.gate_summary():
            print(f"  {f['PIECE_ID']:20} canon={f['CANON']:24} gate={f['ART_GATE']:8} "
                  f"claims={f['CLAIMS']:2} visual={f['VISUAL_READY']}")
        return 0

    if a.cmd == "resolve":
        r = resolver.resolve(a.content_id)
        print(f"  content_id : {r.content_id}")
        print(f"  origen     : {r.origin}")
        print(f"  artefacto  : {r.artefacto_path or 'NO ENCONTRADO'}")
        print(f"  claim pack : {r.packet_path or '-'}")
        print(f"  handoff    : {r.handoff_path or 'NO EXISTE'}")
        print(f"  produccion : {'AUTORIZADA' if r.production_ready else 'BLOQUEADA'}")
        for b in r.blocking:
            print(f"  ! {b}")
        return 0 if r.production_ready else 1

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

        claim_packet = _load(a.claim_packet) if a.claim_packet else None
        if claim_packet is None:
            piece_id = art.get("procedencia", {}).get("piece_id")
            for cid, path, _ in [(p["piece_id"], p["path"], None) for p in resolver.list_pieces()]:
                if cid == piece_id:
                    claim_packet = _load(resolver.REPO / path)
                    break

        brief = brief_desde(vi, policy, fams)
        reg = registry_mod.AssetRegistry(a.out) if a.cmd == "simulate" else None
        run = pipeline.generate_visual(
            art["procedencia"], brief, policy, FakeImageProvider(), handoff=handoff,
            family=fams.get(brief.visual_family), families_version=fams.version,
            dry_run=(a.cmd == "dry-run"), registry=reg, claim_packet=claim_packet,
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
                  f"parent={g.get('parent_generation_id') or '-'}  "
                  f"feedback={g.get('feedback_codes') or '-'}")
        return 0

    if a.cmd == "explain":
        g = reg.get_generation(a.content_id, a.generation_id)
        if not g:
            print("generacion no encontrada")
            return 1
        print(f"POR QUE SALIO ESTA IMAGEN — {g['generation_id']}")
        print(f"\n  CONTENIDO")
        print(f"    content_id     {g['content_id']}")
        print(f"    content_hash   {g.get('content_hash') or '-'}")
        print(f"    procedencia    {g.get('procedencia', {}).get('modo')} "
              f"handoff={g.get('procedencia', {}).get('handoff_id')}")
        print(f"\n  VERSIONES")
        for k in ("visual_policy_version", "visual_family_registry_version",
                  "visual_brief_version", "prompt_compiler_version", "compositor_version"):
            if g.get(k):
                print(f"    {k:32} {g[k]}")
        print(f"\n  DECISIONES")
        for e in g.get("explanation", []):
            print(f"    · {e}")
        print(f"\n  PROVEEDOR")
        print(f"    {g.get('provider')} / {g.get('model') or '-'}  seed={g.get('seed')}")
        print(f"    prompt_sha256  {g.get('prompt_sha256', '')[:32]}")
        print(f"    plan_hash      {g.get('generation_plan_hash', '')[:32]}")
        print(f"\n  ASSETS")
        print(f"    raw       {g.get('raw_asset_id') or '-'}  {g.get('asset_sha256','')[:16]}")
        print(f"    compuesto {g.get('composed_asset_id') or '-'}  {g.get('composed_sha256','')[:16]}")
        print(f"\n  QA")
        sq = g.get("structural_qa", {})
        print(f"    estructural  passed={sq.get('passed')} {sq.get('detected_mime','')}")
        se = g.get("semantic_qa", {})
        print(f"    semantica    {se.get('state')} ({se.get('inspector')}) {se.get('reason_codes') or ''}")
        if g.get("parent_generation_id"):
            print(f"\n  LINAJE")
            print(f"    regenerada desde {g['parent_generation_id']}")
            print(f"    feedback         {g.get('feedback_codes')}")
            for campo, v in (g.get("changed_fields") or {}).items():
                print(f"    cambio  {campo}: {str(v.get('antes'))[:40]!r} -> {str(v.get('despues'))[:40]!r}")
        print(f"\n  APROBACION HUMANA: {g.get('human_visual_approval')}")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
