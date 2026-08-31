"""Orquestador del pipeline visual.

    canonical input -> gate -> brief/policy/family -> memoria -> compilador
    -> plan -> seleccion y negociacion de proveedor -> [DRY RUN corta aqui]
    -> generacion -> QA estructural -> QA semantica -> planes de composicion
    -> receipt -> registro -> [GATE HUMANO]

Ningun camino de este archivo produce APROBADO_PARA_PRODUCCION. El mejor
desenlace posible es PENDIENTE_REVISION_HUMANA.
"""

from dataclasses import dataclass, field

import gates
import receipts as receipts_mod
from composition import build_typography_plan, ExactCopyViolation
from compiler import compile_request
from compositor import CompositionError, CompositionOverflow, compose, composition_qa
from inspection import NoopSemanticInspector, FAIL, NEEDS_HUMAN_REVIEW
from memory import VisualMemory, VisualMemoryEntry
from observability import EventLog
from plan import GenerationPlan, REJECT
from providers.base import NormalizedImageRequest
from providers.selection import evaluate
from qa import structural_qa

# Estados por item de lote (§28). No existe un estado GENERATED: un asset
# producido queda SIEMPRE en NEEDS_HUMAN_REVIEW, porque nada lo aprueba solo.
PENDING, RUNNING, BLOCKED, FAILED, NEEDS_REVIEW = (
    "PENDING", "RUNNING", "BLOCKED", "FAILED", "NEEDS_HUMAN_REVIEW")


@dataclass
class VisualRun:
    receipt: receipts_mod.GenerationReceipt
    plan: GenerationPlan = None
    compiled: object = None
    asset_bytes: bytes = b""
    qa_report: object = None
    semantic: object = None
    typography_plan: object = None
    composed_bytes: bytes = b""
    events: list = field(default_factory=list)

    @property
    def ok(self):
        return self.receipt.status == "PENDIENTE_REVISION_HUMANA"

    @property
    def item_state(self):
        s = self.receipt.status
        if s == "PENDIENTE_REVISION_HUMANA":
            return NEEDS_REVIEW
        if s in ("GATE_CERRADO", "BRIEF_INVALIDO", "PROVEEDOR_INCOMPATIBLE",
                 "COMPOSICION_DESBORDADA"):
            return BLOCKED
        return FAILED


def _entry_desde_brief(content_id, brief, generation_id=""):
    """Huella de memoria derivada del brief. Un solo lugar que la construye."""
    return VisualMemoryEntry(
        content_id=content_id, generation_id=generation_id,
        visual_family=brief.visual_family, scene_type=brief.environment,
        main_subject=brief.subject, camera_angle=brief.camera,
        metaphor=brief.metaphor, brand_surface=brief.marca_superficie,
        secondary_objects=[brief.acento_frio_objeto] if brief.acento_frio_objeto else [])


def _receipt_base(procedencia, brief, policy, families_version=""):
    return dict(
        content_id=str(procedencia.get("content_id") or brief.content_id or ""),
        visual_policy_version=policy.version,
        visual_brief_version=brief.brief_version,
        visual_family=brief.visual_family,
        visual_family_registry_version=families_version,
        procedencia={
            "modo": procedencia.get("modo"),
            "handoff_id": procedencia.get("handoff_id"),
            "claims": procedencia.get("claims", []),
        },
        content_hash=(procedencia.get("claims") or [{}])[0].get("approved_claim_hash", ""),
    )


def generate_visual(procedencia, brief, policy, provider, handoff=None,
                    memory=None, known_hashes=(), family=None, repetition=None,
                    inspector=None, dry_run=False, registry=None,
                    parent_generation_id="", feedback_codes=(), changed_fields=None,
                    claim_packet=None,
                    allow_regeneration=False,
                    exact_copy="", author="", content_type="", families_version="",
                    reserved_surface=None, compose_asset=True):
    """Ejecuta el pipeline. Con dry_run=True no se llama al proveedor (0 llamadas)."""
    log = EventLog()
    base = _receipt_base(procedencia, brief, policy, families_version)
    base.update(parent_generation_id=parent_generation_id,
                feedback_codes=list(feedback_codes),
                changed_fields=changed_fields or {})

    def fin(status, **kw):
        r = receipts_mod.GenerationReceipt(status=status, **{**base, **kw})
        r.events = log.to_list()
        return r

    # 1. Gate — estado canonico leido, nunca recalculado.
    decision = gates.can_enter_visual_generation(procedencia, handoff, claim_packet=claim_packet)
    if not decision.permitido:
        log.emit("visual.gate.rejected", content_id=base["content_id"], reason=decision.motivos[:1])
        return VisualRun(fin("GATE_CERRADO", motivos=decision.motivos), events=log.to_list())
    log.emit("visual.input.accepted", content_id=base["content_id"])

    # 1b. Riesgo de repeticion: si hay memoria y no se paso una evaluacion ya
    # hecha, se calcula aqui. Antes este parametro se transportaba sin usarse.
    if repetition is None and memory is not None:
        repetition = memory.assess(_entry_desde_brief(base["content_id"], brief))

    # 2. Compilacion.
    caps = provider.capabilities()
    try:
        compiled = compile_request(brief, policy, family=family, capabilities=caps,
                                   repetition=repetition)
    except ValueError as exc:
        return VisualRun(fin("BRIEF_INVALIDO", motivos=str(exc).splitlines()), events=log.to_list())
    log.emit("visual.brief.created", content_id=base["content_id"])
    log.emit("visual.prompt.compiled", content_id=base["content_id"],
             compiler=compiled.metadata["prompt_compiler_version"])

    params = compiled.provider_parameters
    base.update(
        prompt_compiler_version=compiled.metadata["prompt_compiler_version"],
        prompt_sha256=compiled.metadata["prompt_sha256"],
        negative_prompt_sha256=compiled.metadata["negative_prompt_sha256"],
        compiled_request_hash=compiled.request_hash(),
        parametros=params,
        provider=caps.provider_id,
        brand_mode=compiled.brand_mode,
        text_mode=compiled.text_mode,
        explanation=list(compiled.explanation),
    )

    request = NormalizedImageRequest(
        content_id=base["content_id"],
        prompt=compiled.positive_prompt,
        negative_prompt=compiled.negative_prompt,
        width=params["width"], height=params["height"],
        aspect_ratio=params["aspect_ratio"], seed=params.get("seed"),
        requires_text_rendering=(compiled.text_mode == "NATIVE_TEXT"),
        metadata=compiled.metadata,
    )

    # 3. Negociacion explicita: ACCEPT / ADAPT / REJECT.
    compat, notas = evaluate(request, caps)
    plan = GenerationPlan(
        content_id=base["content_id"], content_hash=base["content_hash"],
        formato=brief.formato, width=params["width"], height=params["height"],
        aspect_ratio=params["aspect_ratio"], visual_family=brief.visual_family,
        provider=caps.provider_id, provider_compatibility=compat, compatibility_notes=notas,
        text_mode=compiled.text_mode, brand_mode=compiled.brand_mode,
        repetition_level=(repetition.nivel if repetition else "NO_EVALUADO"),
        repetition_score=(repetition.score if repetition else 0),
        repetition_warnings=(list(repetition.razones) if repetition else []),
        explanation=list(compiled.explanation),
        visual_policy_version=policy.version,
        visual_family_registry_version=families_version,
        visual_brief_version=brief.brief_version,
        prompt_compiler_version=compiled.metadata["prompt_compiler_version"],
        compiled_request_hash=compiled.request_hash(),
        provider_capabilities_snapshot=caps.__dict__ if hasattr(caps, "__dict__") else dict(
            provider_id=caps.provider_id, aspect_ratios=list(caps.aspect_ratios)),
    )
    base["generation_plan_hash"] = plan.plan_hash()

    # 3b. Idempotencia: un plan identico ya generado no se repite por accidente.
    # Regenerar es un acto intencional (allow_regeneration / regenerate()).
    if registry is not None and not allow_regeneration and not parent_generation_id:
        from registry import find_equivalent_generation
        previa = find_equivalent_generation(registry, base["content_id"], base["generation_plan_hash"])
        if previa is not None:
            return VisualRun(fin("DRY_RUN", motivos=[
                f"generacion equivalente ya existente ({previa['generation_id']}); "
                "no se repite sin intencion explicita de regenerar."]),
                plan=plan, compiled=compiled, events=log.to_list())

    if compat == REJECT:
        log.emit("visual.generation.failed", content_id=base["content_id"], reason="incompatible")
        return VisualRun(fin("PROVEEDOR_INCOMPATIBLE", motivos=notas), plan=plan,
                         compiled=compiled, events=log.to_list())
    log.emit("visual.provider.selected", content_id=base["content_id"],
             provider=caps.provider_id, decision=compat)

    # 4. DRY RUN: se detiene con plan, sin gastar nada.
    if dry_run:
        return VisualRun(fin("DRY_RUN", motivos=["plan generado sin llamar al proveedor."]),
                         plan=plan, compiled=compiled, events=log.to_list())

    # 5. Generacion.
    log.emit("visual.generation.started", content_id=base["content_id"], provider=caps.provider_id)
    result = provider.generate(request)
    base.update(model=getattr(result, "model", ""), seed=getattr(result, "seed", None),
                provider_capabilities_snapshot=plan.provider_capabilities_snapshot)
    if not result.ok:
        log.emit("visual.generation.failed", content_id=base["content_id"], reason=result.error)
        return VisualRun(fin("GENERACION_FALLIDA", motivos=[result.error]), plan=plan,
                         compiled=compiled, events=log.to_list())
    log.emit("visual.generation.completed", content_id=base["content_id"])

    # 6. QA estructural.
    rep = structural_qa(result, params, known_hashes=known_hashes)
    base.update(asset_sha256=rep.asset_sha256, qa_problemas=rep.problemas, qa_avisos=rep.avisos,
                structural_qa=rep.to_dict())
    log.emit("visual.qa.completed", content_id=base["content_id"], passed=rep.passed)
    if not rep.passed:
        return VisualRun(fin("QA_FALLIDO"), plan=plan, compiled=compiled,
                         qa_report=rep, events=log.to_list())

    # 7. QA semantica: por defecto NOT_EVALUATED. Nunca finge.
    sem = (inspector or NoopSemanticInspector()).inspect(result.image_bytes)
    base["semantic_qa"] = {"state": sem.state, "inspector": sem.inspector,
                           "reason_codes": list(sem.reason_codes), "metrics": sem.metrics}
    if sem.state == FAIL:
        return VisualRun(fin("QA_FALLIDO", qa_problemas=rep.problemas + [
            f"QA semantica: {sem.reason_codes}"]), plan=plan, compiled=compiled,
            qa_report=rep, semantic=sem, events=log.to_list())

    # 8. Plan de composicion posterior (contrato; el rasterizado no vive aqui).
    typo = None
    if exact_copy:
        try:
            typo = build_typography_plan(exact_copy, author, params["width"], params["height"],
                                         content_type=content_type)
            base["typography_plan"] = typo.to_dict()
        except ExactCopyViolation as exc:
            return VisualRun(fin("QA_FALLIDO", qa_problemas=[str(exc)]), plan=plan,
                             compiled=compiled, qa_report=rep, semantic=sem, events=log.to_list())

    base["brand_plan"] = compiled.brand_plan

    # 8b. Composicion determinista: el texto exacto y la marca los pone
    # LegalMente, nunca el proveedor. El raw jamas se modifica.
    composed_bytes = b""
    comp_avisos = []
    if typo is not None and compose_asset:
        try:
            comp = compose(result.image_bytes, typo, compiled.brand_plan,
                           reserved_surface=reserved_surface)
        except CompositionOverflow as exc:
            return VisualRun(fin("COMPOSICION_DESBORDADA", qa_problemas=[str(exc)]),
                             plan=plan, compiled=compiled, qa_report=rep, semantic=sem,
                             typography_plan=typo, events=log.to_list())
        except CompositionError as exc:
            return VisualRun(fin("QA_FALLIDO", qa_problemas=[f"composicion: {exc}"]),
                             plan=plan, compiled=compiled, qa_report=rep, semantic=sem,
                             events=log.to_list())

        problemas_comp = composition_qa(comp, result.image_bytes, typo, exact_copy)
        if problemas_comp:
            return VisualRun(fin("QA_FALLIDO", qa_problemas=problemas_comp), plan=plan,
                             compiled=compiled, qa_report=rep, semantic=sem,
                             typography_plan=typo, events=log.to_list())

        composed_bytes = comp.composed_bytes
        comp_avisos = list(comp.warnings)
        base.update(
            composition=comp.to_dict(),
            composed_sha256=comp.composed_sha256,
            compositor_version=comp.compositor_version,
            raw_asset_id=receipts_mod.asset_id_for(base["content_id"], rep.asset_sha256),
            composed_asset_id=receipts_mod.asset_id_for(
                base["content_id"] + "|composed", comp.composed_sha256),
        )

    motivos = gates.requires_human_visual_review(rep)
    motivos.extend(comp_avisos)
    if sem.state == NEEDS_HUMAN_REVIEW:
        motivos.append(f"heuristicas visuales: {sem.reason_codes}")
    if typo is not None and typo.warnings:
        motivos.extend(typo.warnings)

    receipt = fin("PENDIENTE_REVISION_HUMANA",
                  asset_id=receipts_mod.asset_id_for(base["content_id"], rep.asset_sha256),
                  motivos=motivos)
    run = VisualRun(receipt, plan=plan, compiled=compiled, asset_bytes=result.image_bytes,
                    qa_report=rep, semantic=sem, typography_plan=typo,
                    composed_bytes=composed_bytes, events=log.to_list())

    if registry is not None:
        registry.store(receipt, raw_bytes=result.image_bytes, composed_bytes=composed_bytes)
    return run


# ---------------------------------------------------------------- lotes

@dataclass
class BatchItem:
    procedencia: dict
    brief: object
    handoff: dict = None
    exact_copy: str = ""
    author: str = ""
    content_type: str = ""
    reserved_surface: object = None
    state: str = PENDING
    run: VisualRun = None

    @property
    def content_id(self):
        return self.procedencia.get("content_id", "")


@dataclass
class BatchResult:
    batch_id: str
    items: list = field(default_factory=list)

    def summary(self):
        c = {"total": len(self.items), "ready": 0, "generated": 0, "failed": 0,
             "blocked": 0, "needs_review": 0, "dry_run": 0}
        for it in self.items:
            if it.state == NEEDS_REVIEW:
                c["needs_review"] += 1
                c["generated"] += 1
            elif it.state == BLOCKED:
                c["blocked"] += 1
            elif it.state == FAILED:
                c["failed"] += 1
            if it.run is not None and it.run.receipt.status == "DRY_RUN":
                c["dry_run"] += 1
                c["ready"] += 1
        return c

    def failed_items(self):
        return [i for i in self.items if i.state == FAILED]


def run_batch(items, policy, provider, batch_id="batch-1", dry_run=False, **kw):
    """Cada item conserva identidad y estado propios. Sin status opaco de lote."""
    # Comprobacion explicita contra None: VisualMemory define __len__, asi que una
    # memoria vacia es "falsy" y un `or` descartaria silenciosamente la del que llama.
    memoria = kw.pop("memory", None)
    if memoria is None:
        memoria = VisualMemory(
            ventana=int(policy.data.get("unicidad", {}).get("ventana_memoria_visual", 12)))
    hashes = set(kw.pop("known_hashes", []))
    for it in items:
        it.state = RUNNING
        run = generate_visual(it.procedencia, it.brief, policy, provider,
                              handoff=it.handoff, memory=memoria,
                              known_hashes=hashes, dry_run=dry_run,
                              exact_copy=it.exact_copy, author=it.author,
                              content_type=it.content_type,
                              reserved_surface=it.reserved_surface, **kw)
        it.run = run
        it.state = NEEDS_REVIEW if run.receipt.status == "DRY_RUN" else run.item_state
        if run.receipt.asset_sha256:
            hashes.add(run.receipt.asset_sha256)
        if run.ok:
            memoria.record(_entry_desde_brief(it.content_id, it.brief,
                                              run.receipt.generation_id))
    return BatchResult(batch_id, list(items))


def retry_failed(batch, policy, provider, **kw):
    """Reintenta SOLO los fallidos. Los exitosos no se regeneran."""
    fallidos = batch.failed_items()
    for it in fallidos:
        it.state = RUNNING
        run = generate_visual(it.procedencia, it.brief, policy, provider,
                              handoff=it.handoff, exact_copy=it.exact_copy,
                              author=it.author, content_type=it.content_type,
                              reserved_surface=it.reserved_surface, **kw)
        it.run = run
        it.state = run.item_state
    return batch


def regenerate(previous_run, brief_revisado, policy, provider, procedencia, codes,
               changed_fields, **kw):
    """Crea una generacion NUEVA. La anterior nunca se muta (§31)."""
    return generate_visual(
        procedencia, brief_revisado, policy, provider,
        parent_generation_id=previous_run.receipt.generation_id,
        feedback_codes=list(codes), changed_fields=changed_fields,
        allow_regeneration=True, **kw)
