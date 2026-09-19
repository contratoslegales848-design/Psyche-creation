"""Fases 8, 9 y 10 — lote real, aprendizaje Founder simulado, métricas.

    python3 demo_founder_loop.py        (desde el directorio visual/)

No genera imágenes. No verifica Derecho. No publica. Selecciona candidatos
con el generador multi-factor (Fase 7), contra la memoria histórica real (174
piezas), y simula — SÓLO LA INFRAESTRUCTURA, nunca la decisión del Founder —
un ciclo completo de curaduría y aprendizaje.

HONESTIDAD DECLARADA sobre lo que este lote SÍ y NO puede mostrar: un
TopicCandidate nace de la capa semántica/editorial, antes de verificación
jurídica y antes de plan visual. Por eso HOOK, METÁFORA y DIRECCIÓN ARTÍSTICA
FINAL aparecen como PENDIENTE — inventarlos aquí sería exactamente el defecto
que esta reconciliación viene corrigiendo. COMPOSICIÓN y CÁMARA sí se
muestran: nacen del perfil emocional (Fase de emoción, ya integrada), no se
fabrican para esta demo.
"""

import corpus_enrichment as ce
import corpus_import as ci
import editorial
import editorial_saturation
import founder_metrics as fm
import generator
import organism
import territory_explorer as te
import universe
from semantic_fingerprint import mas_similar
from semantic_memory import SemanticMemory


def linea():
    print("=" * 96)


def seccion(t):
    print("\n" + "=" * 96 + f"\n{t}\n" + "=" * 96)


def mostrar_candidato(i, c, puntuacion, historicas, por_id_enr):
    fp = c.fingerprint()
    vecino, d = mas_similar(fp, historicas)
    h = por_id_enr.get(vecino.content_id) if vecino else None

    print(f"\n  --- CANDIDATO {i} ---")
    print(f"  MATERIA:              {c.materia}")
    print(f"  TEMA (submateria):     {c.submateria}")
    print(f"  HOOK:                  PENDIENTE — el copy se redacta después de la "
          f"verificación jurídica (CLAUDE.md §4).")
    print(f"  FAMILIA EDITORIAL:     {c.familia_editorial}")
    print(f"  NECESIDAD:             {c.necesidad}")
    print(f"  PREGUNTA QUE RESUELVE: {c.pregunta_resuelta}")
    print(f"  CONCEPTO NÚCLEO:       {c.concepto_nucleo}")
    print(f"  EMOCIÓN:               {c.emocion}  (intensidad "
          f"{c.perfil_emocional.get('intensidad', '?')})")
    print(f"  TENSIÓN (relación):    {c.relacion}")
    print(f"  CONSECUENCIA:          {c.consecuencia or '(no declarada por esta familia)'}")
    print(f"  METÁFORA:              PENDIENTE — se decide en brief.py junto con la escena "
          f"real, tras verificación.")
    print(f"  COMPOSICIÓN:           {c.perfil_emocional.get('composicion', '?')}  "
          f"(derivada del perfil emocional)")
    print(f"  CÁMARA (sugerida):     {c.perfil_emocional.get('camara', '?')}")
    print(f"  DIRECCIÓN ARTÍSTICA:   PENDIENTE — biblioteca abierta "
          f"(families.py); se asigna en brief.py.")
    if h and d is not None and d.valor >= 0.999:
        print(f"  VECINO HISTÓRICO:      ninguno con un solo eje en común (distancia "
             f"máxima 1.0). {h.content_id} es sólo el primero de una lista entera "
             "empatada al máximo — no hay precedente parcial real que reportar: "
             "este candidato abre territorio sin ningún antecedente histórico.")
    elif h:
        print(f"  VECINO HISTÓRICO:      {h.content_id} «{h.base.titular}»")
        print(f"  DISTANCIA:             {d.valor}  (umbral de equivalencia 0.25)")
    else:
        print("  VECINO HISTÓRICO:      ninguno comparable.")
    print(f"  TERRITORIO QUE ABRE:   opportunity={puntuacion.territory_coverage} "
          f"| utility={puntuacion.utility} | novelty semántica={puntuacion.semantic_novelty}")
    print(f"  SCORE COMPUESTO:       {puntuacion.score_compuesto}")


def metricas_de_lote(candidatos, fingerprints, mapa):
    materias = {c.materia for c in candidatos}
    familias = {c.familia_editorial for c in candidatos}
    emociones = {c.emocion for c in candidatos if c.emocion}
    pares = []
    for i in range(len(fingerprints)):
        for j in range(i + 1, len(fingerprints)):
            d = fingerprints[i].distancia_semantica(fingerprints[j])
            if d.comparable:
                pares.append(d.valor)
    d_min = min(pares) if pares else None
    territorio_nuevo = sum(1 for c in candidatos
                           if mapa.celdas.get((c.materia.lower(), c.familia_editorial.lower()), 0) == 0)
    return {"cobertura_materias": len(materias), "cobertura_familias": len(familias),
            "rotacion_emocional": len(emociones), "distancia_semantica_minima": d_min,
            "abren_territorio_nuevo": territorio_nuevo}


def main():
    regs, _ = ci.construir_registros()
    enr = ce.enriquecer(regs)
    por_id_enr = {e.content_id: e for e in enr}
    # fingerprint_completo(), no la huella cruda: usa el enriquecimiento de la
    # Fase 5 (concepto_nucleo/pregunta_resuelta mejorados) para que "vecino
    # histórico más cercano" sea una búsqueda real, no una comparación contra
    # datos que la migración base dejó en UNKNOWN.
    historicas = [e.fingerprint_completo() for e in enr]

    universo = editorial.EditorialUniverse.load()
    _, materias = universe.cargar_materias()
    mapa = te.construir_mapa(regs, materias=materias, universo=universo)

    memoria = SemanticMemory()
    ci.importar(memoria, regs)

    seccion("FASE 8 — LOTE REAL DE 10 CANDIDATOS (generador multi-factor)")
    reserva = universe.build_reserve(objetivo_lote=10, seed=2026, factor=14)
    print(f"  reserva: {len(reserva)} candidatos")
    seleccion, puntuaciones, rechazados = generator.seleccionar_lote(
        reserva, memoria, mapa, universo=universo, n=10, materias=materias)
    print(f"  seleccionados: {len(seleccion)} | rechazados en el camino: {len(rechazados)}")
    if rechazados:
        print("  motivos de rechazo (muestra):")
        for cid, motivo in rechazados[:3]:
            print(f"    {cid}: {motivo[:100]}")

    for i, (c, p) in enumerate(zip(seleccion, puntuaciones), 1):
        mostrar_candidato(i, c, p, historicas, por_id_enr)

    fps = [c.fingerprint() for c in seleccion]
    m = metricas_de_lote(seleccion, fps, mapa)
    seccion("MÉTRICAS DEL LOTE (Fase 8, cierre)")
    print(f"  cobertura de materias ........ {m['cobertura_materias']}/10")
    print(f"  cobertura de familias ........ {m['cobertura_familias']}/10")
    print(f"  rotación emocional ........... {m['rotacion_emocional']} emociones distintas")
    print(f"  distancia semántica mínima ... {m['distancia_semantica_minima']}")
    print(f"  distancia visual .............. NO DISPONIBLE (sin plan visual en esta etapa)")
    print(f"  piezas que abren territorio nuevo (celda materia×familia nunca "
          f"producida): {m['abren_territorio_nuevo']}/10")

    # --- FASE 9: aprendizaje Founder (simulado: sólo la infraestructura) ---
    seccion("FASE 9 — INFRAESTRUCTURA DE APRENDIZAJE (decisión simulada, no real)")
    elegidos_idx = (1, 4, 8)   # posiciones 2, 5, 9 en numeración humana (1-indexada)
    elegidos_ids = [seleccion[i].candidate_id for i in elegidos_idx]
    print(f"  ME QUEDO CON (simulado): {[i+1 for i in elegidos_idx]} "
         f"-> {elegidos_ids}")
    print(f"  DESCARTO (simulado): {[i+1 for i in range(10) if i not in elegidos_idx]}")

    lote1 = organism.CurationBatch(lote_id="fase8", estado=organism.CURATION_READY,
                                   candidatos=seleccion, reserva_total=len(reserva))
    resumen = organism.registrar_curaduria(lote1, elegidos_ids, memoria)
    print(f"\n  selection_rate de este lote: {resumen['selection_rate']}")

    print("\n  Produciendo LOTE 2 — debe recordar, evitar repetición inmediata de los")
    print("  descartes, NO cancelar sus ramas jurídicas, y favorecer sin encerrarse "
         "en el gusto reciente...")
    reserva2 = universe.build_reserve(objetivo_lote=10, seed=2027, factor=14)
    sel2, pts2, rech2 = generator.seleccionar_lote(reserva2, memoria, mapa, universo=universo,
                                                   n=10, materias=materias)
    print(f"  lote 2: {len(sel2)}/10 seleccionados")

    fp1_elegidos = [c.fingerprint() for c in seleccion if c.candidate_id in elegidos_ids]
    fp1_descartados = [c.fingerprint() for c in seleccion if c.candidate_id not in elegidos_ids]
    familias_elegidas = {c.familia_editorial for c in seleccion if c.candidate_id in elegidos_ids}
    familias_descartadas = {c.familia_editorial for c in seleccion
                            if c.candidate_id not in elegidos_ids}

    repite_algo = [(a.content_id, b.content_id) for a in [c.fingerprint() for c in sel2]
                  for b in fp1_elegidos + fp1_descartados if a.equivalente_a(b)]
    print(f"\n  piezas del lote 2 que repiten semánticamente el lote 1: {len(repite_algo)}")

    materias_descartadas = {c.materia for c in seleccion if c.candidate_id not in elegidos_ids}
    reaparecen = {c.materia for c in sel2} & materias_descartadas
    print(f"  materias descartadas que reaparecen en el lote 2: {len(reaparecen)} "
         f"de {len(materias_descartadas)} -> {sorted(reaparecen)}")

    # EXPLOTACIÓN real: cuántas piezas del lote 2 recibieron un ajuste de
    # afinidad positivo (materia, familia, necesidad, ángulo, emoción o rol
    # coinciden con lo que el Founder acaba de preseleccionar). Contar sólo
    # coincidencias de FAMILIA sería demasiado estrecho — el mandato pide
    # "funciones/características", plural, y el ajuste ya las cubre todas.
    con_afinidad = [(c.candidate_id, p.ajuste_afinidad_founder)
                    for c, p in zip(sel2, pts2) if p.ajuste_afinidad_founder > 0]
    print(f"\n  EXPLOTACIÓN — piezas del lote 2 con afinidad positiva heredada de la "
         f"curaduría: {len(con_afinidad)}/10")
    for cid, aj in con_afinidad[:4]:
        print(f"    {cid}: ajuste +{aj}")

    fams2 = {c.familia_editorial for c in sel2}
    print(f"\n  EXPLORACIÓN — familias del lote 2 que ni siquiera aparecieron en el "
         f"lote 1: {len(fams2 - {c.familia_editorial for c in seleccion})}/10")
    print("  (con afinidad Y exploración a la vez: el ajuste está acotado a "
         f"±{generator.AJUSTE_AFINIDAD_MAX} precisamente para no encerrar la selección "
         "en una sola familia — sigue rotando y sigue respetando la cuota por materia.)")

    # --- FASE 10: métricas Founder ---
    seccion("FASE 10 — FOUNDER SELECTION RATE (con tamaño de muestra visible)")
    rep = fm.informe(memoria, ejes=list(fm.EJES_DISPONIBLES) + list(fm.EJES_PENDIENTES))
    print(f"  tasa global: {rep.tasa_global}  (sobre {rep.total_decididas} decisiones)")
    for a in rep.avisos:
        print(f"  AVISO: {a}")
    for eje, filas in rep.por_eje.items():
        print(f"\n  selection_rate por {eje}:")
        for f in filas[:6]:
            marca = "" if f.muestra_suficiente else "  (muestra insuficiente)"
            print(f"    {f.valor:<26} tasa={f.tasa}  n={f.total_decididas}{marca}")

    print("\n  LÍMITE: con una sola curaduría simulada, TODAS las muestras son "
         "pequeñas por diseño.\n  Esta fase demuestra la INFRAESTRUCTURA, no produce "
         "todavía una conclusión fiable.")


if __name__ == "__main__":
    main()
