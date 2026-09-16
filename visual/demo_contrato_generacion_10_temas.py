"""Prueba de aceptación real + manifiesto — Hotfix post-implementación
(Founder, 16-sep-2026), secciones 11-12.

Reutiliza (NO inventa otros 10) los 10 temas ya generados por el motor
editorial real en `demo_produccion_real_10_temas_nuevos.py`
(`docs/prueba-real-produccion-10-temas-2026-09-16.md`) y compila de nuevo
ese mismo lote (misma semilla, determinista) para reportar el contrato de
salida de cada pieza: topic, generation_mode, source_image,
reference_images, edit_instruction, format, fingerprint, final_prompt.

Produce además el manifiesto machine-readable (JSON) que el mandato pide
en la sección 12 — sin bytes de imagen, sin referencias ficticias — para
que cualquier agente/generador externo pueda consumirlo sin adivinar
intención.

Estado de entrega declarado explícitamente: COMPILED. Ningún proveedor de
imagen real está conectado a este repositorio (ver
`docs/auditoria-inteligencia-tematica-2026-09-16.md` §3) — nada aquí se
envía a un proveedor ni se genera.

Uso: `cd visual && python3 demo_contrato_generacion_10_temas.py`
"""

import json
from pathlib import Path

import demo_produccion_real_10_temas_nuevos as prod
from providers.base import DELIVERY_COMPILED, GENERATION_MODE_TEXT_TO_IMAGE

MANIFEST_PATH = (Path(__file__).resolve().parent.parent / "corpus" /
                 "manifiesto-generacion-legalmente-general-2026-09-16.json")
REPORT_PATH = (Path(__file__).resolve().parent.parent / "docs" /
               "contrato-salida-10-temas-2026-09-16.md")


def construir_items(resultados):
    items = []
    for r in resultados:
        c, comp, h = r["candidato"], r["compilado"], r["huella"]
        items.append({
            "content_id": c.candidate_id,
            "topic": {
                "materia": c.materia, "submateria": c.submateria,
                "concepto_nucleo": c.concepto_nucleo,
                "legal_tension": c.relacion,
                "metaphor": r["direccion"]["metaphor"],
            },
            "generation_mode": comp.generation_mode,
            "source_image": comp.source_image,
            "reference_images": list(comp.reference_images),
            "edit_instruction": comp.edit_instruction,
            "format": {
                "aspect_ratio": comp.requested_aspect_ratio,
                "width": comp.requested_dimensions[0] if comp.requested_dimensions else None,
                "height": comp.requested_dimensions[1] if comp.requested_dimensions else None,
                "single_scene": True,
            },
            "fingerprint": {
                "primary_direction": h.primary_direction,
                "secondary_direction": h.secondary_direction,
                "medium": h.medium,
                "lighting": h.lighting,
                "palette": h.palette,
                "composition": h.composition,
                "materiality": h.materiality,
                "camera_optics": h.camera_optics,
                "realism": h.realism,
                "visual_mechanism": h.visual_mechanism,
            },
            "final_prompt": comp.positive_prompt,
            "negative_prompt": comp.negative_prompt,
            "delivery_status": DELIVERY_COMPILED,
        })
    return items


def construir_manifiesto(resultados):
    items = construir_items(resultados)
    return {
        "brand": "LegalMente",
        "channel": "general",
        "operation": "batch_generation",
        "format": "vertical_9_16",
        "count": len(items),
        "delivery_status": DELIVERY_COMPILED,
        "provider_connected": False,
        "items": items,
    }


def verificar_invariante(manifiesto):
    """Comprobaciones explícitas del criterio de éxito del mandato (§17,
    "resultado esperado"). Devuelve una lista de problemas -- vacía si el
    lote cumple las cuatro condiciones 10/10."""
    problemas = []
    items = manifiesto["items"]
    n = len(items)

    no_texto = [i for i in items if i["generation_mode"] != GENERATION_MODE_TEXT_TO_IMAGE]
    if no_texto:
        problemas.append(f"{len(no_texto)}/{n} piezas NO son TEXT_TO_IMAGE.")

    con_source = [i for i in items if i["source_image"] is not None]
    if con_source:
        problemas.append(f"{len(con_source)}/{n} piezas llevan source_image (deben ser null/ausente).")

    con_edit = [i for i in items if i["edit_instruction"] is not None]
    if con_edit:
        problemas.append(f"{len(con_edit)}/{n} piezas llevan edit_instruction (deben ser null/ausente).")

    ids = [i["content_id"] for i in items]
    if len(ids) != len(set(ids)):
        problemas.append("hay content_id repetidos: las piezas no son independientes.")

    return problemas


def reporte_markdown(manifiesto, problemas):
    items = manifiesto["items"]
    lineas = [
        "# Contrato de salida text-to-image — 10 temas (Hotfix, 16-sep-2026)",
        "",
        "Reutiliza el mismo lote de `docs/prueba-real-produccion-10-temas-2026-09-16.md` "
        "(misma semilla, determinista) — no se inventaron otros 10 temas.",
        "",
        f"**Resultado esperado vs. real**: {'CUMPLE 10/10' if not problemas else 'FALLA'} "
        f"— {len(items)}/{len(items)} TEXT_TO_IMAGE, "
        f"{len(items)}/{len(items)} source_image ausente, "
        f"{len(items)}/{len(items)} edit_instruction ausente, "
        f"{len(items)}/{len(items)} operaciones independientes.",
    ]
    if problemas:
        lineas.append("\n**Problemas encontrados:**")
        lineas.extend(f"- {p}" for p in problemas)
    lineas.append(f"\nManifiesto JSON: `{MANIFEST_PATH.relative_to(MANIFEST_PATH.parent.parent)}`")
    lineas.append("\n| # | topic | generation_mode | source_image | reference_images | "
                  "edit_instruction | format | final_prompt (primeras palabras) |")
    lineas.append("|---|---|---|---|---|---|---|---|")
    for i, it in enumerate(items, 1):
        prompt_corto = it["final_prompt"][:70] + "…"
        fmt = f"{it['format']['aspect_ratio']} ({it['format']['width']}×{it['format']['height']})"
        lineas.append(
            f"| {i} | {it['content_id']}: {it['topic']['concepto_nucleo'][:40]} | "
            f"{it['generation_mode']} | {it['source_image']} | {it['reference_images']} | "
            f"{it['edit_instruction']} | {fmt} | {prompt_corto} |")
    return "\n".join(lineas) + "\n"


def ejecutar():
    resultados, *_ = prod.ejecutar()
    manifiesto = construir_manifiesto(resultados)
    problemas = verificar_invariante(manifiesto)
    return manifiesto, problemas


if __name__ == "__main__":
    manifiesto, problemas = ejecutar()
    MANIFEST_PATH.write_text(json.dumps(manifiesto, indent=2, ensure_ascii=False) + "\n",
                             encoding="utf-8")
    reporte = reporte_markdown(manifiesto, problemas)
    REPORT_PATH.write_text(reporte, encoding="utf-8")
    print(reporte)
    print(f"\nManifiesto escrito en {MANIFEST_PATH}")
    print(f"Reporte escrito en {REPORT_PATH}")
    if problemas:
        raise SystemExit("El lote NO cumple el criterio de éxito del mandato: " + "; ".join(problemas))
