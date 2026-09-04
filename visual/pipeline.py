"""Orquestador del pipeline visual.

    canonical input -> gate -> brief/policy/family -> memoria -> compilador
    -> plan -> seleccion y negociacion de proveedor -> [DRY RUN corta aqui]
    -> generacion -> QA estructural -> QA semantica -> planes de composicion
    -> receipt -> registro -> [GATE HUMANO]

Ningun camino de este archivo produce APROBADO_PARA_PRODUCCION. El mejor
desenlace posible es PENDIENTE_REVISION_HUMANA.
"""

from dataclasses import dataclass, field, replace

import gates
import receipts as receipts_mod
from composition import build_typography_plan, ExactCopyViolation
from brief import PolicyError
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


def _entry_desde_brief(content_id, brief, generation_id="", taxonomia=None):
    """Huella de memoria derivada del brief. Un solo lugar que la construye.

    `taxonomia` es el bloque REAL `content/*.json`.taxonomia del artefacto (si
    el llamador lo tiene) — nunca se infiere ni se inventa aqui. Sin el, la
    entrada simplemente no participa del eje materia+concepto (ver memory.py).
    """
    tax = taxonomia or {}
    return VisualMemoryEntry(
        content_id=content_id, generation_id=generation_id,
        visual_family=brief.visual_family, scene_type=brief.environment,
        main_subject=brief.subject, camera_angle=brief.camera,
        metaphor=brief.metaphor, brand_surface=brief.marca_superficie,
        secondary_objects=[brief.acento_frio_objeto] if brief.acento_frio_objeto else [],
        materia=str(tax.get("materia") or ""), concepto=str(tax.get("concepto") or ""))


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


def _zona_ocupada_por_el_texto(typo, width, height):
    """Banda que el texto ocupara de verdad, en porcentaje de la altura.

    Se calcula desde los bloques reales del plan —cuantas lineas y de que
    tamano— y NO desde `safe_area`. La distincion importa: el safe_area de una
    pieza 9:16 cubre casi todo el lienzo (153..1767 de 1920), asi que usarlo
    equivaldria a pedirle al generador que dejara vacia el 89 % de la imagen. Eso
    no reserva una zona: mata la escena.

    El interlineado se toma alto a proposito. Reservar de mas cuesta un poco de
    escena; reservar de menos deja texto sobre un objeto, que es justo el defecto
    que esto corrige.
    """
    INTERLINEADO = 1.45          # cota superior, no medida exacta
    SEPARACION_ENTRE_BLOQUES = 28

    _sx, sy, _sw, sh = typo.safe_area
    alto_texto = 0
    for i, b in enumerate(typo.blocks or []):
        lineas = len(getattr(b, "lines", None) or (b.get("lines") if isinstance(b, dict) else []) or [])
        tam = getattr(b, "size_px", None) or (b.get("size_px") if isinstance(b, dict) else 0) or 0
        if not lineas or not tam:
            continue
        alto_texto += int(lineas * tam * INTERLINEADO)
        if i:
            alto_texto += SEPARACION_ENTRE_BLOQUES

    if not alto_texto:
        # Sin metricas de bloque no se inventa una banda estrecha: se declara que
        # no se pudo derivar y el prompt se queda como estaba.
        return None

    y0 = sy
    y1 = min(sy + alto_texto, sy + sh)
    alto = max(height, 1)
    inicio = max(0, int(100 * y0 / alto) - 2)
    fin = min(100, int(100 * y1 / alto) + 3)
    return 0, inicio, 100, max(fin - inicio, 1)


def generate_visual(procedencia, brief, policy, provider, handoff=None,
                    memory=None, known_hashes=(), family=None, repetition=None,
                    inspector=None, dry_run=False, registry=None,
                    parent_generation_id="", feedback_codes=(), changed_fields=None,
                    claim_packet=None,
                    allow_regeneration=False,
                    exact_copy="", author="", content_type="", families_version="",
                    reserved_surface=None, compose_asset=True, taxonomia=None):
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
        repetition = memory.assess(_entry_desde_brief(base["content_id"], brief, taxonomia=taxonomia))

    # 1c. Zona tipografica reservada, ANTES de compilar.
    #
    # El defecto que esto corrige: el plan tipografico se calculaba en el paso 8,
    # despues de generar la imagen, asi que el prompt nunca sabia donde iba a caer
    # el texto juridico. El generador colocaba objetos, luz y detalle justo ahi, y
    # la copia exacta acababa montada sobre una zona ocupada. En la practica es la
    # causa mas frecuente de "la imagen no salio bien": no es que el arte sea malo,
    # es que compite con el texto que tiene que sostener.
    #
    # 'negative_space' ya existia en el brief y el compilador ya lo emitia al
    # prompt (compiler.py). Simplemente nadie lo rellenaba nunca: ni brief_desde(),
    # ni el brief revisado por un humano de GEN3. Aqui se deriva del layout REAL,
    # no de una estimacion: mismas dimensiones, mismo texto exacto, misma funcion
    # que compondra despues.
    #
    # Si el brief ya trae un negative_space escrito a mano, se respeta: la
    # direccion de arte humana manda sobre la derivacion automatica.
    if exact_copy and not brief.negative_space:
        try:
            _f = policy.formato(brief.formato)
            _typo_previo = build_typography_plan(
                exact_copy, author, _f["width"], _f["height"], content_type=content_type)
            _zona = _zona_ocupada_por_el_texto(_typo_previo, _f["width"], _f["height"])
            if _zona is None:
                raise ValueError("no se pudo derivar la zona tipografica")
            _x, _y, _w, _h = _zona
            brief = replace(brief, negative_space=(
                f"la banda entre el {_y}% y el {_y + _h}% de la altura, de borde a "
                f"borde, queda en calma: fondo continuo, sin objetos, sin bordes "
                f"marcados y sin foco. Ahi se compone despues el texto juridico y "
                f"debe leerse sin competir con la escena"))
            log.emit("visual.negative_space.derived", content_id=base["content_id"],
                     banda=f"{_y}%-{_y + _h}%")
        except (ExactCopyViolation, PolicyError, KeyError, ValueError):
            # Derivar la zona es una mejora, no un requisito: si falla, el pipeline
            # sigue exactamente como antes en vez de bloquear una generacion.
            pass

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
    taxonomia: dict = None
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
                              reserved_surface=it.reserved_surface,
                              taxonomia=it.taxonomia, **kw)
        it.run = run
        it.state = NEEDS_REVIEW if run.receipt.status == "DRY_RUN" else run.item_state
        if run.receipt.asset_sha256:
            hashes.add(run.receipt.asset_sha256)
        if run.ok:
            memoria.record(_entry_desde_brief(it.content_id, it.brief,
                                              run.receipt.generation_id, taxonomia=it.taxonomia))
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


# --- entrada canónica desde content/*.json -------------------------------
def generate_visual_from_content_id(content_id, brief, policy, provider,
                                     vinculo_visual="", **kwargs):
    """Ejecuta el pipeline a partir de un CONTENT_ID real.

    La función conecta resolver -> canonical -> generate_visual. Nunca infiere
    procedencia ni abre gates: el ``handoff`` y el claim packet se transportan
    tal como están y el pipeline devuelve ``GATE_CERRADO`` si falta aprobación.
    El brief visual sigue siendo obligatorio porque la taxonomía editorial no
    debe inventar una dirección de arte.

    ``vinculo_visual`` (opcional) es la metáfora de una transición de ruta
    (``route_engine.RouteMatrixRow.vinculo_visual``): si se aporta y el brief
    no trae ya una metáfora propia, se usa como ``brief.metaphor`` — el mismo
    campo que ``compiler.py`` ya inserta literalmente en el prompt compilado
    ("Metafora visual: ..."). No es contenido jurídico ni un dato que
    requiera verificación: solo orienta la dirección de arte hacia el
    vínculo editorial entre el nodo anterior y el actual.
    """
    import resolver as resolver_mod
    from canonical import build_visual_input
    from dataclasses import replace as _replace

    resolution = resolver_mod.resolve(content_id)
    if not resolution.resolved:
        raise ValueError("CONTENT_ID no resuelto: " + "; ".join(resolution.blocking))

    visual_input = build_visual_input(resolution.artefacto, resolution.handoff)
    procedencia = resolution.artefacto["procedencia"]
    taxonomia = resolution.artefacto.get("taxonomia") or {}

    if vinculo_visual and not getattr(brief, "metaphor", ""):
        brief = _replace(brief, metaphor=str(vinculo_visual))

    params = dict(kwargs)
    params.setdefault("handoff", resolution.handoff)
    params.setdefault("claim_packet", resolution.packet)
    params.setdefault("exact_copy", visual_input.exact_copy)
    params.setdefault("author", visual_input.author)
    params.setdefault("content_type", visual_input.content_type)
    params.setdefault("taxonomia", taxonomia)
    return generate_visual(procedencia, brief, policy, provider, **params)


def generate_visual_from_route_row(route_row, brief, policy, provider, **kwargs):
    """Consume una fila producida por RouteEngine y conserva su vínculo visual.

    ``route_row.content_id`` debe ser un CONTENT_ID real (el campo dedicado,
    nunca ``route_row.fuente`` -- ``fuente`` es la referencia evidencial de
    la pieza, un concepto distinto). La fila solo aporta la metáfora de
    transición; la autoridad sigue resolviéndose desde el canon real vía
    ``generate_visual_from_content_id``, que es quien evalúa el gate.
    """
    content_id = str(getattr(route_row, "content_id", "") or "").strip()
    if not content_id:
        raise ValueError(
            "la fila de ruta no declara content_id: abre la ruta con "
            "RouteEngine.leer_entrada_desde_artefacto() para tener un CONTENT_ID real."
        )
    return generate_visual_from_content_id(
        content_id, brief, policy, provider,
        vinculo_visual=getattr(route_row, "vinculo_visual", ""), **kwargs
    )
