"""Memoria histórica de LegalMente — informe y prueba de regresión.

    python3 demo_corpus.py        (desde el directorio visual/)

Importa el corpus real (174 piezas), mide los sesgos históricos, agrupa por
significado, calibra el umbral y demuestra que un lote nuevo no reformula el
pasado. No genera arte, no gasta créditos, no publica y no verifica Derecho.
"""

import calibration
import corpus_analysis as ca
import corpus_import as ci
import organism
import universe
from semantic_fingerprint import UMBRAL_EQUIVALENCIA, mas_similar
from semantic_memory import SemanticMemory, GENERADA


def seccion(t):
    print("\n" + "=" * 94 + f"\n{t}\n" + "=" * 94)


def main():
    regs, errores = ci.construir_registros()
    por_id = {r.content_id: r for r in regs}

    seccion("A. CORPUS ENCONTRADO E IMPORTADO")
    memoria = SemanticMemory()
    rep = ci.importar(memoria, regs)
    print(f"  piezas en la fuente ........ {rep.total_fuente}")
    print(f"  importadas ................. {rep.importados}")
    print(f"  errores de parseo .......... {len(rep.errores)}")
    print(f"  duplicados exactos de slug . {len(rep.duplicados_exactos)}")
    rep2 = ci.importar(memoria, regs)
    print(f"  re-ejecución (idempotencia)  importadas={rep2.importados}, "
          f"ya presentes={rep2.ya_presentes}, memoria={len(memoria)}")
    completas = sum(1 for r in regs
                    if ci.NINGUNA not in r.confianza_extraccion.values())
    print(f"  huellas completas .......... {completas}")
    print(f"  huellas parciales .......... {len(regs) - completas}")
    print("  confianza por campo:", rep.confianza)
    print("  campos sin evidencia:", dict(list(rep.campos_faltantes.items())[:6]))

    seccion("B. SESGOS HISTÓRICOS MEDIDOS")
    perfil = ca.perfil_de_repeticion(regs)
    for eje, n in (("materia", 6), ("familia_editorial", 6), ("escena", 4),
                   ("composicion", 4), ("direccion_artistica", 4)):
        print(f"  {eje}:")
        for v, c in list(perfil[eje].items())[:n]:
            print(f"     {c:>4}  ({c * 100 // len(regs):>2}%)  {v[:70]}")
    print(f"  metáforas distintas ........ {len(perfil['metafora'])} de {len(regs)}")

    seccion("C. CLUSTERS SEMÁNTICOS (misma pregunta con títulos distintos)")
    cs = ca.clusters_semanticos(regs, umbral=UMBRAL_EQUIVALENCIA)
    print(f"  Al umbral de BLOQUEO ({UMBRAL_EQUIVALENCIA}): {len(cs)} clusters, "
          f"{sum(c.tamano for c in cs)} piezas.")
    print("  Es decir: el banco v3 cumplió lo que prometía — 174 temas realmente")
    print("  distintos. NO hay 10 ni 20 piezas que sean la misma pregunta jurídica.")
    print()
    print("  Vista de PROXIMIDAD (umbral 0.35, solo para revision humana — no bloquea):")
    prox = ca.clusters_semanticos(regs, umbral=0.35)
    print(f"  {len(prox)} grupos, {sum(c.tamano for c in prox)} piezas vecinas.")
    for c in prox[:4]:
        print(f"\n  -- {c.tamano} piezas | distancia media {c.distancia_media} | {c.materia}")
        for cid, g in c.miembros:
            print(f"       {cid}  {g}")

    seccion("D. ZONAS DEL DERECHO SIN EXPLORAR")
    z = ca.zonas_sin_explorar(regs)
    print(f"  materias sin una sola pieza ({len(z['materias_del_seed_sin_una_sola_pieza'])}):")
    print(f"     {z['materias_del_seed_sin_una_sola_pieza']}")
    print(f"\n  familias editoriales nunca usadas: "
          f"{len(z['familias_editoriales_nunca_usadas'])} de 58")
    print(f"     {z['familias_editoriales_nunca_usadas'][:18]}")
    print(f"\n  combinaciones materia x familia producidas: "
          f"{z['combinaciones_materia_familia_producidas']} de "
          f"{z['combinaciones_posibles_sobre_materias_ya_abiertas']} posibles")

    seccion("E. CALIBRACIÓN DEL UMBRAL CONTRA EL CORPUS REAL")
    puntos, meta, conteo = calibration.barrido(regs)
    print(f"  positivos canónicos: {conteo['canonicos']} | pares etiquetados: "
          f"{conteo['etiquetados_computados']} | zona gris excluida: {conteo['zona_gris_excluida']}")
    print(f"\n  {'umbral':>7}{'TP':>5}{'FP':>5}{'FN':>5}{'TN':>5}{'precision':>11}{'recall':>9}{'F1':>9}")
    for p in puntos:
        marca = "  <- vigente" if abs(p.umbral - UMBRAL_EQUIVALENCIA) < 1e-9 else ""
        print(f"  {p.umbral:>7}{p.tp:>5}{p.fp:>5}{p.fn:>5}{p.tn:>5}"
              f"{p.precision:>11}{p.recall:>9}{p.f1:>9}{marca}")
    print(f"\n  AVISO: {meta.get('estado')}")
    print("  Las etiquetas las puso el agente, no el Founder. No es certeza estadística.")

    seccion("F. PRUEBA DE REGRESIÓN: LOTE NUEVO CONTRA 174 PIEZAS HISTÓRICAS")
    reserva = universe.build_reserve(objetivo_lote=10, seed=777, factor=12)
    print(f"  reserva generada: {len(reserva)} candidatos")
    sel = universe.select_batch(reserva, n=10, memoria=memoria)
    print(f"  seleccionados: {len(sel.seleccionados)} | descartados por memoria: "
          f"{len(sel.descartados)}")
    historicas = [r.fingerprint() for r in regs]
    for i, c in enumerate(sel.seleccionados, 1):
        fp = c.fingerprint()
        vecino, d = mas_similar(fp, historicas)
        h = por_id.get(vecino.content_id) if vecino else None
        print(f"\n  {i}. {c.materia} / {c.familia_editorial}")
        print(f"     necesidad={c.necesidad}  ángulo={c.angulo}  emoción={c.emocion}")
        print(f"     pregunta: {c.pregunta_resuelta[:82]}")
        if h:
            print(f"     vecino histórico más cercano: {h.content_id} «{h.titular[:46]}»")
            print(f"       distancia semántica {d.valor}  (umbral {UMBRAL_EQUIVALENCIA})")
            print(f"       NO es repetición: {_porque(c, h)}")

    seccion("G. PRUEBA FOUNDER: ¿APARECEN FAMILIAS DISTINTAS SIN PEDIRLAS?")
    lote = organism.producir_lote("founder-test", n=10, seed=4242,
                                  memoria=memoria, factor_reserva=12)
    print(f"  estado: {lote.estado} | intentos: {lote.intentos} | "
          f"reserva: {lote.reserva_total}")
    print(f"  {'MATERIA':<32}{'FAMILIA EDITORIAL':<26}{'NECESIDAD':<13}{'EMOCIÓN'}")
    for c in lote.candidatos:
        print(f"  {c.materia[:31]:<32}{c.familia_editorial[:25]:<26}"
              f"{c.necesidad:<13}{c.emocion}")
    fams = {c.familia_editorial for c in lote.candidatos}
    historicas_fam = {r.familia_editorial for r in regs
                      if r.familia_editorial != ci.UNKNOWN}
    print(f"\n  familias distintas: {len(fams)}/10")
    print(f"  familias que el corpus histórico NUNCA usó: "
          f"{len(fams - historicas_fam)}/10 -> {sorted(fams - historicas_fam)}")
    print("\n  LÍMITE: todos los candidatos siguen NO_VERIFICADO. Este motor "
          "selecciona;\n  no verifica Derecho ni autoriza publicación.")


def _porque(candidato, historica):
    """Justificación legible. Un eje que la pieza histórica dejó en UNKNOWN no
    prueba diferencia: se declara como tal en vez de presentarlo como razón."""
    razones, sin_dato = [], []
    for etiqueta, nuevo, viejo in (
            ("materia", candidato.materia, historica.materia),
            ("función editorial", candidato.familia_editorial, historica.familia_editorial),
            ("necesidad", candidato.necesidad, historica.necesidad)):
        if viejo == ci.UNKNOWN:
            sin_dato.append(etiqueta)
        elif nuevo != viejo:
            razones.append(f"otra {etiqueta} (histórica: {viejo})")
    texto = "; ".join(razones) or "difiere sólo en ejes secundarios"
    if sin_dato:
        texto += f" [la pieza histórica no declara {', '.join(sin_dato)}]"
    return texto


if __name__ == "__main__":
    main()
