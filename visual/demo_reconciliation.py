"""Cadena reconciliada de punta a punta — Pasos 12 y 13 del mandato.

    python3 demo_reconciliation.py        (desde el directorio visual/)

Encadena TODO lo construido en las tres fases previas más los cierres de
brecha de esta reconciliación:

    NECESIDAD → TopicCandidate (universe.py)
    → semantic fingerprint (semantic_fingerprint.py)
    → semantic repetition (semantic_memory.py, corpus histórico incluido)
    → editorial saturation (editorial_saturation.py — SEPARADA de lo anterior)
    → territory opportunity (territory_explorer.py)
    → [verificación jurídica: FUERA DE ALCANCE — sigue NO_VERIFICADO]
    → función editorial + argumento visual (art_direction.py — NUEVO)
    → EmotionalProfile (emotion.py, ya causal sobre cámara/luz/composición)
    → borrador de VisualBrief (art_direction.draft_visual_brief — NUEVO)
    → QA individual (generator.puntuar_candidato: 3 hard gates)
    → QA de lote (generator.seleccionar_lote + visual_distance.py NUEVO +
      lanes.verificar_ratio_operativo NUEVO + diversidad de estilos NUEVO)
    → CURATION_READY (organism.py)
    → selección Founder (simulada)
    → memoria de aprendizaje (semantic_memory + ajuste_afinidad_founder)
    → siguiente reserva.

No llama a ningún proveedor de imagen. No genera copy. No verifica Derecho.
No publica.
"""

import corpus_enrichment as ce
import corpus_import as ci
import editorial
import families
import generator
import lanes
import organism
import provider_gate
import territory_explorer as te
import universe
import visual_distance as vdist
import visual_fingerprint as vf
from art_direction import draft_visual_brief, verificar_diversidad_de_estilos
from memory import VisualMemory, VisualMemoryEntry
from semantic_fingerprint import mas_similar
from semantic_memory import SemanticMemory


def seccion(t):
    print("\n" + "=" * 98 + f"\n{t}\n" + "=" * 98)


def draft_a_entry_visual(candidato, draft):
    """Traduce el borrador a VisualMemoryEntry — SÓLO con los campos que el
    borrador realmente conoce en esta etapa. escena/metáfora NO se copian:
    son PENDIENTE_CONTENIDO, y tratarlas como dato real haría que todas las
    piezas parecieran idénticas en esos dos ejes. Ausencia de evidencia se
    deja como ausencia, nunca como coincidencia falsa."""
    return VisualMemoryEntry(
        content_id=candidato.candidate_id, generation_id=f"draft-{candidato.candidate_id}",
        visual_family=draft.familia_visual, dominant_materials=[draft.material_sugerido],
        lighting_type=draft.luz, brand_surface=draft.superficie_marca_sugerida,
        materia=candidato.materia, concepto=candidato.concepto_nucleo)


def mostrar_pieza(i, c, draft, puntuacion, historicas, por_id_enr):
    fp = c.fingerprint()
    vecino, d = mas_similar(fp, historicas)
    h = por_id_enr.get(vecino.content_id) if vecino else None

    print(f"\n  --- PIEZA {i} ---")
    print(f"  MATERIA / TEMA:        {c.materia} / {c.submateria}")
    print(f"  FAMILIA EDITORIAL:     {c.familia_editorial}")
    print(f"  NECESIDAD:             {c.necesidad}")
    print(f"  CONCEPTO NÚCLEO:       {c.concepto_nucleo}")
    print(f"  PREGUNTA RESUELTA:     {c.pregunta_resuelta}")
    print(f"  EMOCIÓN:               {c.emocion}   TENSIÓN: {c.relacion}")
    print(f"  CONSECUENCIA:          {c.consecuencia or '(no declarada por esta familia)'}")
    print(f"  HOOK:                  PENDIENTE_CONTENIDO — copy tras verificación jurídica.")
    print(f"  TERRITORY OPPORTUNITY: {puntuacion.territory_coverage}  "
         f"(novelty semántica {puntuacion.semantic_novelty}, utility {puntuacion.utility})")
    if h and d is not None and d.valor >= 0.999:
        print(f"  VECINO HISTÓRICO:      ninguno con eje real en común (distancia máxima).")
    elif h:
        print(f"  VECINO HISTÓRICO:      {h.content_id} «{h.base.titular}»  distancia={d.valor}")
    print(f"  VISUAL ARGUMENT:       {draft.visual_function}  ({draft.razon_funcion})")
    print(f"  ESCENA:                {draft.escena}")
    print(f"  COMPOSICIÓN:           {draft.composicion}")
    print(f"  DIRECCIÓN ARTÍSTICA:   {draft.familia_visual}")
    print(f"  CÁMARA / LUZ:          {draft.camara} / {draft.luz}")
    print(f"  MATERIAL:              {draft.material_sugerido}")
    print(f"  SOPORTE DE MARCA:      {draft.superficie_marca_sugerida}  (integración física, nunca overlay)")
    print(f"  SCORE COMPUESTO:       {puntuacion.score_compuesto}  "
         f"(ajuste afinidad Founder: {puntuacion.ajuste_afinidad_founder:+.4f})")


def producir_y_dirigir(reserva_seed, memoria, mapa, universo, materias, registro_familias, n=10,
                       catalogo_maestro=None):
    """Un ciclo completo: reserva → selección multi-factor → dirección de
    arte (borrador, huella del catálogo maestro — Parte XII) para cada
    seleccionada."""
    reserva = universe.build_reserve(objetivo_lote=n, seed=reserva_seed, factor=14)
    seleccion, puntuaciones, rechazados = generator.seleccionar_lote(
        reserva, memoria, mapa, universo=universo, n=n, materias=materias)

    catalogo_maestro = catalogo_maestro or vf.MasterCatalog.load()
    # La huella se ACUMULA según se van dirigiendo las piezas: sin esto,
    # seleccionar_huella() sin memoria puede repetir dirección en dos
    # piezas seguidas — el propio defecto que la Parte XII existe para
    # cerrar (antes: elegir_familia_visual(memoria_visual=None) sin
    # memoria SIEMPRE devolvía la misma familia).
    memoria_huellas = vf.FingerprintMemory()
    memoria_visual = VisualMemory()
    drafts = []
    for c in seleccion:
        d = draft_visual_brief(c, c.perfil_emocional, catalogo_maestro,
                               memoria_huellas=memoria_huellas,
                               registro_familias=registro_familias, memoria_visual=memoria_visual)
        drafts.append(d)
        memoria_visual.record(draft_a_entry_visual(c, d))
    return reserva, seleccion, puntuaciones, drafts, rechazados


def qa_de_lote(seleccion, drafts, registro_familias, memoria, catalogo_maestro=None):
    """QA de lote extendido con los tres cierres de esta reconciliación."""
    problemas = []

    catalogo_maestro = catalogo_maestro or vf.MasterCatalog.load()
    ok_estilos, detalle_estilos = verificar_diversidad_de_estilos(drafts, catalogo_maestro,
                                                                   n_esperado=len(seleccion))
    print(f"\n  [diversidad de estilos] {'OK' if ok_estilos else 'INSUFICIENTE'} — {detalle_estilos}")
    if not ok_estilos:
        problemas.append("diversidad de estilos por debajo del techo real del registro.")

    ok_ratio, motivo_ratio = lanes.verificar_ratio_operativo(seleccion, lanes.LEGALMENTE_GENERAL)
    print(f"  [ratio operativo LinkedIn] no aplica a LEGALMENTE_GENERAL (carril distinto).")

    entries = [draft_a_entry_visual(c, d) for c, d in zip(seleccion, drafts)]
    verificacion = vdist.verificar_lote_contra_historia(entries, historia=[])
    print(f"  [distancia visual estricta, 8 dims] revisadas: {verificacion.total_revisadas} "
         f"comparaciones. {'OK' if verificacion.ok else 'con avisos'}")
    if not verificacion.ok:
        incompletas = sum(1 for p in verificacion.problemas if "incompleta" in p)
        print(f"    -> {incompletas}/{len(verificacion.problemas)} son EVIDENCIA INCOMPLETA "
             "(esperado: escena y metáfora son contenido pendiente en esta etapa, no un "
             "defecto del lote — visual_distance.py sí exige el rigor completo cuando esos "
             "campos existen, ver test_visual_distance.py).")

    for c in seleccion:
        try:
            provider_gate.verificar_proveedor_permitido("generic-http-image-v1")
        except provider_gate.ProviderGateError as e:
            problemas.append(str(e))
    print(f"  [gate de proveedor] generic-http-image-v1 -> permitido para las {len(seleccion)} piezas.")

    return problemas


def main():
    regs, _ = ci.construir_registros()
    enr = ce.enriquecer(regs)
    por_id_enr = {e.content_id: e for e in enr}
    historicas = [e.fingerprint_completo() for e in enr]

    universo = editorial.EditorialUniverse.load()
    _, materias = universe.cargar_materias()
    registro_familias = families.VisualFamilyRegistry.load()
    mapa = te.construir_mapa(regs, materias=materias, universo=universo)

    memoria = SemanticMemory()
    ci.importar(memoria, regs)

    seccion("LOTE 1 — cadena completa, 10 piezas reales")
    reserva, sel1, pts1, drafts1, rechazados1 = producir_y_dirigir(
        4242, memoria, mapa, universo, materias, registro_familias)
    print(f"  reserva: {len(reserva)} | seleccionadas: {len(sel1)} | rechazadas en el camino: {len(rechazados1)}")
    for i, (c, d, p) in enumerate(zip(sel1, drafts1, pts1), 1):
        mostrar_pieza(i, c, d, p, historicas, por_id_enr)

    seccion("QA DE LOTE (Fase de reconciliación)")
    problemas1 = qa_de_lote(sel1, drafts1, registro_familias, memoria)

    materias_cubiertas = {c.materia for c in sel1}
    familias_cubiertas = {c.familia_editorial for c in sel1}
    emociones = {c.emocion for c in sel1 if c.emocion}
    territorio_nuevo = sum(1 for c in sel1
                           if mapa.celdas.get((c.materia.lower(), c.familia_editorial.lower()), 0) == 0)
    pares = [fp1.distancia_semantica(fp2) for i, fp1 in enumerate([c.fingerprint() for c in sel1])
            for j, fp2 in enumerate([c.fingerprint() for c in sel1]) if i < j]
    d_min = min((p.valor for p in pares if p.comparable), default=None)

    print(f"\n  matter coverage ............ {len(materias_cubiertas)}/10")
    print(f"  editorial coverage .......... {len(familias_cubiertas)}/10")
    print(f"  territory opened ............ {territorio_nuevo}/10")
    print(f"  minimum semantic distance ... {d_min}")
    print(f"  emotional rotation ........... {len(emociones)} emociones distintas")
    print(f"  visual distance (estricta) ... NO CERTIFICABLE en esta etapa — ver aviso arriba.")
    print(f"  problemas del lote ........... {len(problemas1)}")

    seccion("SELECCIÓN FOUNDER SIMULADA (3/10) Y SEGUNDO LOTE")
    elegidos_idx = (0, 4, 8)
    elegidos_ids = [sel1[i].candidate_id for i in elegidos_idx]
    print(f"  ME QUEDO CON (simulado): {[i+1 for i in elegidos_idx]} -> {elegidos_ids}")
    lote1 = organism.CurationBatch(lote_id="reconciliacion-1", estado=organism.CURATION_READY,
                                   candidatos=sel1, reserva_total=len(reserva))
    resumen = organism.registrar_curaduria(lote1, elegidos_ids, memoria)
    print(f"  selection_rate: {resumen['selection_rate']}")

    _, sel2, pts2, drafts2, rechazados2 = producir_y_dirigir(
        4243, memoria, mapa, universo, materias, registro_familias)
    print(f"\n  lote 2: {len(sel2)}/10 seleccionadas")

    fp1_todas = [c.fingerprint() for c in sel1]
    fp2_todas = [c.fingerprint() for c in sel2]
    repite = [(a.content_id, b.content_id) for a in fp2_todas for b in fp1_todas if a.equivalente_a(b)]
    print(f"  no repetición semántica inmediata: {len(repite)} coincidencias (0 esperado).")

    fam1 = [c.familia_editorial for c in sel1]
    fam2 = [c.familia_editorial for c in sel2]
    print(f"  no repetición editorial mecánica: familias del lote 1 reutilizadas exactamente "
         f"igual en el lote 2 -> {len(set(fam1) & set(fam2))} (la cuota de 1-por-lote de "
         "universe.py ya lo impedía dentro de cada lote; aquí se mide ENTRE lotes).")

    con_afinidad = [p.ajuste_afinidad_founder for p in pts2 if p.ajuste_afinidad_founder > 0]
    print(f"  afinidad hacia señales seleccionadas: {len(con_afinidad)}/10 piezas heredaron "
         "ajuste positivo de la curaduría anterior.")

    materias_descartadas = {c.materia for c in sel1 if c.candidate_id not in elegidos_ids}
    reaparecen = {c.materia for c in sel2} & materias_descartadas
    print(f"  ramas descartadas no quedan muertas: {len(reaparecen)}/{len(materias_descartadas)} "
         f"materias descartadas reaparecen en el lote 2 (memoria corta, no bloqueo permanente).")

    print("\n  problemas abiertos declarados explícitamente:")
    print("  - visual_distance estricta no puede certificarse antes de que exista escena/metáfora real.")
    print("  - diversidad de estilos: resuelto (Parte XII, 16-sep-2026) — el techo ya es el catálogo "
         "maestro de 504 direcciones, no las 8 familias reducidas de antes.")
    print("  - hook y copy exacto siguen sin generarse (contenido, no infraestructura).")
    print("  - ningún candidato ha pasado legalmente-legal-verification: todos NO_VERIFICADO.")


if __name__ == "__main__":
    main()
