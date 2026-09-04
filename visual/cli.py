#!/usr/bin/env python3
"""CLI minima del pipeline visual.

Permite que otro agente (o una persona) ejerza la arquitectura sin escribir
codigo. Nunca llama a un proveedor real: el unico proveedor registrado es el
falso.

    python3 cli.py families
    python3 cli.py policy
    python3 cli.py validate   <artefacto.json>
    python3 cli.py dry-run    <artefacto.json> [--handoff h.json]
    python3 cli.py simulate   <artefacto.json> [--handoff h.json] [--out DIR] [--live]
    python3 cli.py batch-dry-run <dir_con_artefactos>
    python3 cli.py show-receipt   <DIR> <CONTENT_ID> <GENERATION_ID>
    python3 cli.py show-history   <DIR> <CONTENT_ID>
    python3 cli.py route-avanzar  <CONTENT_ID> [--categoria C] [--formato F] [--matriz ruta.json]
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import canonical
import command_center
import compositor
import inventory
import pipeline
import provider_preflight
import resolver
import route_engine
import route_sync
import runtime_config
import topology
import registry as registry_mod
from brief import VisualBrief, VisualPolicy
from errors import StoragePathError, VisualInputInvalidError
from families import VisualFamilyRegistry
from providers import FakeImageProvider


def _load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def gen3_brief_pieza01(policy, fams):
    """Reconstruye el VisualBrief de GEN3 desde el puntero persistente.

    El AssetRegistry que produjo GEN3 vivia en /tmp (hueco conocido, ver
    runtime_config.py) y no sobrevive entre sesiones; el brief original no
    quedo comitado como objeto. Lo que SI persiste es
    review-packet-gen-2f2dfb9c6f2f.json, con cada `changed_fields` que la
    regeneracion aplico (antes/despues). Se reconstruye aplicando esos
    "despues" sobre la base que ya genera brief_desde() para este content_id
    — no se inventa ningun valor nuevo.
    """
    art = _load(resolver.REPO / "content" / "pieza-01-reales.json")
    from canonical import VisualInput
    proc = art["procedencia"]
    vi = VisualInput(content_id=proc["content_id"], provenance_mode=proc["modo"],
                      jurisdiction_layer=proc.get("jurisdiction_layer", ""),
                      publicable=bool(proc.get("publicable")))
    brief = brief_desde(vi, policy, fams)
    packet = _load(resolver.REPO / "artifacts" / "human-review" / "LM-PIEZA-01-REALES" /
                    "review-packet-gen-2f2dfb9c6f2f.json")
    for campo, cambio in (packet.get("changed_fields") or {}).items():
        if hasattr(brief, campo):
            setattr(brief, campo, cambio.get("despues"))
    return brief


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
    sub.add_parser("inventory")
    sub.add_parser("inbox")
    sub.add_parser("system-queue")
    s = sub.add_parser("next")
    s.add_argument("--executable", action="store_true",
                    help="solo lo que LegalMente puede ejecutar AHORA sin intervencion humana.")
    s = sub.add_parser("command-center"); s.add_argument("--json", action="store_true")
    sub.add_parser("provider-preflight")
    sub.add_parser("providers")
    sub.add_parser("provider-request")
    sub.add_parser("topology")
    s = sub.add_parser("resolve"); s.add_argument("content_id")
    s = sub.add_parser("route-avanzar")
    s.add_argument("content_id")
    s.add_argument("--categoria", default=None,
                   help="categoria de nodo elegida explicitamente; por defecto, la siguiente natural.")
    s.add_argument("--formato", default="NO_ASIGNADO")
    s.add_argument("--matriz", default=None,
                   help="ruta al JSON de la matriz de rutas persistida; por defecto, la raiz "
                        "runtime persistente (LEGALMENTE_RUNTIME_ROOT o .runtime/visual-registry).")
    for c in ("validate", "dry-run", "simulate"):
        s = sub.add_parser(c)
        s.add_argument("artefacto")
        s.add_argument("--handoff")
        s.add_argument("--claim-packet",
                       help="claim packet real para verificar el hash contra la aprobacion humana; "
                            "si se omite, se busca por piece_id en pilot/claim-packets/.")
        s.add_argument("--reserved-surface", metavar="X,Y,W,H",
                       help="superficie fisica reservada para la marca, en pixeles del lienzo. "
                            "Sin esto la marca no se compone (NEEDS_HUMAN_REVIEW), nunca watermark.")
        if c == "simulate":
            s.add_argument("--out", default=None,
                           help="raiz del registro de generaciones. Por defecto, la raiz runtime "
                                "persistente (LEGALMENTE_RUNTIME_ROOT o .runtime/visual-registry), "
                                "nunca /tmp.")
            s.add_argument("--live", action="store_true",
                           help="usar el proveedor HTTP real configurado por "
                                "LEGALMENTE_IMAGE_PROVIDER_ENDPOINT/_API_KEY en vez del proveedor "
                                "falso. Sin esto, 'simulate' SIEMPRE genera un placeholder, "
                                "aunque haya credenciales configuradas: nunca envia una peticion "
                                "real sin este flag explicito.")
            s.add_argument("--proveedor", default=None,
                           help="id del perfil de proveedor a usar con --live "
                                "(ver 'python3 cli.py providers'). Por defecto, "
                                "generic-http-image-v1.")
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

    if a.cmd == "inventory":
        for r in inventory.build_readiness():
            print(f"  {r.piece_id:20} canon={r.canonical_state:24} gate={r.art_gate:8} "
                  f"handoff={r.handoff_state:16} gen={r.latest_generation_id or '-':16}")
            print(f"      mechanical_qa={r.mechanical_qa:14} real_art_semantic_qa={r.real_art_semantic_qa:14} "
                  f"human_art_review={r.human_art_review:34} simulated={r.provider_is_simulated}")
            print(f"      next_executable_action={r.next_executable_action}")
            for b in r.blockers:
                print(f"      ! {b}")
        return 0

    if a.cmd == "system-queue":
        cola = inventory.system_executable_queue()
        if not cola:
            print("  (sin trabajo de sistema pendiente)")
            return 0
        for r in cola:
            print(f"  {r.piece_id:20} accion={r.next_executable_action:28} owner={r.owner}")
            if r.source_summary is not None:
                s = r.source_summary
                print(f"      fuentes: accesibles={s.accessible_count} inaccesibles={s.inaccessible_count} "
                      f"sin_verificar={s.not_verified_count} de {len(s.checks)}")
        return 0

    if a.cmd == "inbox":
        items = inventory.build_inbox()
        if not items:
            print("  (vacio: nada espera decision humana ahora mismo)")
            return 0
        for it in items:
            print(f"  [{it.decision_type:26}] {it.piece_id:20} {it.detail}")
        return 0

    if a.cmd == "next":
        readiness = inventory.build_readiness()
        if a.executable:
            ejecutables = inventory.executable_now(readiness)
            if not ejecutables:
                print("  (nada ejecutable ahora mismo sin intervencion humana)")
                return 0
            for r in ejecutables:
                print(f"  {r.piece_id:20} accion={r.next_executable_action}")
            return 0
        candidatos = [r for r in readiness if r.canonical_state != "REQUIERE_INVESTIGACION"]
        candidatos.sort(key=lambda r: len(r.blockers))
        if not candidatos:
            print("  (sin candidatos: todas las piezas requieren investigacion juridica)")
            return 0
        for r in candidatos[:5]:
            print(f"  {r.piece_id:20} bloqueos={len(r.blockers):2} accion={r.next_executable_action:26} "
                  f"siguiente={r.next_action}")
        return 0

    if a.cmd == "command-center":
        envelope = command_center.build_envelope()
        if a.json:
            print(json.dumps(envelope, ensure_ascii=False, indent=2))
        else:
            for f in envelope["content"]:
                print(f"  {f['content_id']:24} piece={f['piece_id']:20} visual={f['visual_state']:18} "
                      f"human_art_review={f['human_art_review']:34} next={f['next_executable_action']}")
        return 0

    if a.cmd == "provider-preflight":
        r = provider_preflight.preflight()
        print(json.dumps(r.to_dict(), ensure_ascii=False, indent=2))
        return 0 if r.status == provider_preflight.READY else 1

    if a.cmd == "provider-request":
        brief = gen3_brief_pieza01(policy, fams)
        from providers.base import ProviderCapabilities
        caps = ProviderCapabilities(provider_id=provider_preflight.DEFAULT_PROFILE.provider_id,
                                     aspect_ratios=provider_preflight.DEFAULT_PROFILE.aspect_ratios)
        req = provider_preflight.build_pieza01_request(brief, policy, fams.get(brief.visual_family), caps)
        print(json.dumps(req, ensure_ascii=False, indent=2))
        print("\nZERO network execution. ZERO credits. Esta peticion no fue enviada a nadie.")
        return 0

    if a.cmd == "topology":
        for link in topology.build_topology():
            print(f"  {link['source']:32} -> {link['target']:28} {link['state']:16} {link['reason']}")
        print("\n  -- content factory (idea -> ProductionHandoff) --")
        for link in topology.content_factory_topology():
            print(f"  {link['source']:24} -> {link['target']:24} {link['state']:18} {link['reason']}")
        print("\n  -- publication / measurement / learning --")
        for link in topology.publication_measurement_learning_topology():
            print(f"  {link['source']:28} -> {link['target']:28} {link['state']:12} {link['reason']}")
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

    if a.cmd == "providers":
        from providers import profiles
        for pid, estado, nota in profiles.listar():
            cfg = profiles.cargar(pid)
            pre = provider_preflight.preflight(cfg)
            marca = "por defecto" if pid == profiles.POR_DEFECTO else ""
            print(f"  {pid} {marca}")
            print(f"    estado de verificacion : {estado}")
            print(f"    nota                   : {nota}")
            print(f"    endpoint configurado   : {'si' if pre.endpoint_configured else 'NO'}")
            print(f"    credencial presente    : {'si' if pre.auth_present else 'NO'} "
                  f"(variable {cfg.api_key_env})")
            print(f"    preflight              : {pre.status}"
                  + (f" — {pre.blocking_reason}" if pre.blocking_reason else ""))
            print()
        return 0

    if a.cmd == "route-avanzar":
        matriz_path = Path(a.matriz) if a.matriz else runtime_config.default_registry_root() / "route-matrix.json"
        motor = route_engine.RouteEngine.load(matriz_path)
        resolution, filas = route_sync.avanzar_desde_content_id(
            motor, a.content_id, categoria_elegida=a.categoria, formato=a.formato)
        motor.save(matriz_path)
        print(f"  content_id : {a.content_id}")
        print(f"  matriz     : {matriz_path}")
        for fila in filas:
            print(f"  nodo_actual        : {fila['nodo_actual']}")
            print(f"  siguiente_vinculo  : {fila['siguiente_vinculo']}")
            print(f"  proxima_accion     : {fila['proxima_accion']}")
        return 0

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

        surface = None
        if a.reserved_surface:
            x, y, w, h = (int(n) for n in a.reserved_surface.split(","))
            surface = compositor.ReservedSurface(x, y, w, h)

        brief = brief_desde(vi, policy, fams)
        out_root = a.out if (a.cmd == "simulate" and a.out) else runtime_config.default_registry_root()
        reg = registry_mod.AssetRegistry(out_root) if a.cmd == "simulate" else None

        provider = FakeImageProvider()
        if a.cmd == "simulate" and getattr(a, "live", False):
            from providers import profiles
            from providers.http_provider import HttpImageProvider
            pid = getattr(a, "proveedor", None) or profiles.POR_DEFECTO
            try:
                cfg = profiles.cargar(pid)
            except ValueError as exc:
                print(f"NO SE PUEDE USAR --live: {exc}")
                return 1
            pre = provider_preflight.preflight(cfg)
            if pre.status != provider_preflight.READY:
                print(f"NO SE PUEDE USAR --live ({pid}): {pre.blocking_reason}")
                print("Nada se envio a ningun proveedor. Revisa "
                      "'python3 cli.py providers' para ver que variables espera este perfil.")
                return 1
            estado, nota = profiles.estado_de_verificacion(pid)
            provider = HttpImageProvider(cfg)
            print(f"--live: usando el proveedor real ({pid}).")
            if estado != profiles.VERIFICADO:
                print(f"  ! PERFIL {estado}: {nota}")
                print("  ! Si la respuesta no trae imagen, el error dira que claves SI llegaron; "
                      "con eso se corrige response_paths en providers/profiles.py.")

        run = pipeline.generate_visual(
            art["procedencia"], brief, policy, provider, handoff=handoff,
            family=fams.get(brief.visual_family), families_version=fams.version,
            dry_run=(a.cmd == "dry-run"), registry=reg, claim_packet=claim_packet,
            reserved_surface=surface,
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
    try:
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
    except StoragePathError as exc:
        print(f"RECHAZADO: {exc}")
        return 1

    if a.cmd == "explain":
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
