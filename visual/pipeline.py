"""Orquestador del pipeline visual.

    procedencia + handoff
        -> gate de entrada
        -> brief + politica
        -> compilador de prompt
        -> negociacion de capacidades
        -> adapter del proveedor
        -> QA estructural
        -> [GATE HUMANO]  <- el pipeline SE DETIENE aqui, siempre
        -> registro + receipt

Ningun camino de este archivo produce APROBADO_PARA_PRODUCCION. El mejor
desenlace posible es PENDIENTE_REVISION_HUMANA. Abrir ese gate es un acto
humano, fuera del codigo (CLAUDE.md §4 y §6).
"""

from dataclasses import dataclass, field

import gates
import receipts as receipts_mod
from compiler import compile_prompt
from providers.base import NormalizedImageRequest, negotiate
from qa import structural_qa


@dataclass
class VisualRun:
    receipt: receipts_mod.GenerationReceipt
    asset_bytes: bytes = b""
    prompt: str = ""
    negative_prompt: str = ""
    qa_report: object = None

    @property
    def ok(self):
        """True solo si el asset quedo listo para que un humano lo revise."""
        return self.receipt.status == "PENDIENTE_REVISION_HUMANA"


def generate_visual(procedencia, brief, policy, provider, handoff=None,
                    recent_memory=(), known_hashes=()):
    """Ejecuta el pipeline completo para una pieza. Devuelve un VisualRun.

    Emite receipt en todos los desenlaces, incluidos los fallidos.
    """
    content_id = str(procedencia.get("content_id") or brief.content_id or "")
    base = dict(
        content_id=content_id,
        visual_policy_version=policy.version,
        visual_brief_version=brief.brief_version,
        procedencia={
            "modo": procedencia.get("modo"),
            "handoff_id": procedencia.get("handoff_id"),
            "claims": procedencia.get("claims", []),
        },
    )

    # 1. Gate de entrada — estado canonico leido, nunca recalculado.
    decision = gates.can_enter_visual_generation(procedencia, handoff)
    if not decision.permitido:
        return VisualRun(receipts_mod.GenerationReceipt(
            status="GATE_CERRADO", motivos=decision.motivos, **base))

    # 2. Brief + politica -> prompt compilado.
    caps = provider.capabilities()
    try:
        prompt, negative_prompt, parametros, meta = compile_prompt(
            brief, policy, capabilities=caps, recent_memory=recent_memory)
    except ValueError as exc:
        return VisualRun(receipts_mod.GenerationReceipt(
            status="BRIEF_INVALIDO", motivos=str(exc).splitlines(), **base))

    base.update(
        prompt_compiler_version=meta["prompt_compiler_version"],
        prompt_sha256=meta["prompt_sha256"],
        negative_prompt_sha256=meta["negative_prompt_sha256"],
        parametros=parametros,
        provider=caps.provider_id,
    )

    request = NormalizedImageRequest(
        content_id=content_id,
        prompt=prompt,
        negative_prompt=negative_prompt,
        width=parametros["width"],
        height=parametros["height"],
        aspect_ratio=parametros["aspect_ratio"],
        seed=parametros.get("seed"),
        requires_text_rendering=(brief.text_rendering_mode == "NATIVE_TEXT"),
        metadata=meta,
    )

    # 3. Negociacion de capacidades — rechaza antes de gastar la llamada.
    incompat = negotiate(request, caps)
    if incompat:
        return VisualRun(
            receipts_mod.GenerationReceipt(status="PROVEEDOR_INCOMPATIBLE", motivos=incompat, **base),
            prompt=prompt, negative_prompt=negative_prompt)

    # 4. Generacion.
    result = provider.generate(request)
    base.update(model=getattr(result, "model", ""), seed=getattr(result, "seed", None))
    if not result.ok:
        return VisualRun(
            receipts_mod.GenerationReceipt(
                status="GENERACION_FALLIDA", motivos=[result.error], **base),
            prompt=prompt, negative_prompt=negative_prompt)

    # 5. QA estructural.
    rep = structural_qa(result, parametros, known_hashes=known_hashes)
    base.update(asset_sha256=rep.asset_sha256, qa_problemas=rep.problemas, qa_avisos=rep.avisos)
    if not rep.passed:
        return VisualRun(
            receipts_mod.GenerationReceipt(status="QA_FALLIDO", **base),
            prompt=prompt, negative_prompt=negative_prompt, qa_report=rep)

    # 6. Fin del camino automatico. El gate humano no lo abre este codigo.
    receipt = receipts_mod.GenerationReceipt(
        status="PENDIENTE_REVISION_HUMANA",
        asset_id=receipts_mod.asset_id_for(content_id, rep.asset_sha256),
        motivos=gates.requires_human_visual_review(rep),
        **base)
    return VisualRun(receipt, asset_bytes=result.image_bytes, prompt=prompt,
                     negative_prompt=negative_prompt, qa_report=rep)


def generate_batch(items, policy, provider, recent_memory=(), known_hashes=()):
    """Lote. La memoria visual y los hashes conocidos se acumulan sobre la marcha,
    de modo que una pieza del lote no puede repetir el asset de otra."""
    memoria = list(recent_memory)
    hashes = set(known_hashes)
    runs = []
    for procedencia, brief, handoff in items:
        run = generate_visual(procedencia, brief, policy, provider, handoff=handoff,
                              recent_memory=memoria, known_hashes=hashes)
        runs.append(run)
        if run.receipt.asset_sha256:
            hashes.add(run.receipt.asset_sha256)
        if run.ok:
            memoria.insert(0, brief.subject)
    return runs
