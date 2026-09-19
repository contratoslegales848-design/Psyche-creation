"""Prueba de generación real del banco maestro (entregable explícito del
mandato "Revisa y mejora el generador de imágenes", 19-sep-2026): confirma
con datos reales -- no fabricados -- que el motor combinatorio real produce
temas variados y no repetidos, y que ENTREGADO efectivamente bloquea una
segunda corrida.

Ejecutar: `cd visual && python3 demo_banco_maestro.py`
"""

import json
import tempfile
from pathlib import Path

import banco_maestro as bm


def linea(t=""):
    print("-" * 70 if not t else f"\n=== {t} ===")


def main():
    linea("1. Corrida real contra el historial completo (174 + 16 piezas reales)")
    with tempfile.TemporaryDirectory() as d:
        banco_path = Path(d) / "banco-maestro-demo.json"

        # Se captura el historial ANTES de la corrida -- comparar los
        # entregados contra un historial que ya los incluye a ellos mismos
        # (tras persistir) sería una tautología, no una prueba.
        historial_previo = bm.cargar_memoria_historial_completo(banco_path)

        r1 = bm.construir_banco(objetivo=80, seed=9200, factor_reserva=3,
                                banco_previo_path=banco_path, persistir=True)
        print(f"objetivo: {r1.objetivo}")
        print(f"reserva total generada: {r1.reserva_total}")
        print(f"ENTREGADOS (utilizados): {len(r1.entregados)}")
        print(f"DISPONIBLES (validados, listos para la próxima corrida): {len(r1.disponibles)}")
        print(f"BLOQUEADOS (repetían historial real): {len(r1.bloqueados)}")
        print(f"distribución por categoría del Founder: "
             f"{json.dumps(r1.distribucion_categoria, ensure_ascii=False)}")
        print(f"distribución por materia: {len(r1.distribucion_materia)} materias distintas")

        linea("2. Prueba de NO repetición dentro del banco (requisito 5)")
        fps = [c.fingerprint() for c in r1.entregados]
        pares_equivalentes = [(a.content_id, b.content_id)
                              for i, a in enumerate(fps) for b in fps[i + 1:]
                              if a.equivalente_a(b)]
        print(f"pares semánticamente equivalentes entre los {len(fps)} entregados: "
             f"{len(pares_equivalentes)} (esperado: 0)")
        assert not pares_equivalentes, "el banco entregó duplicados internos"

        linea("3. Prueba de NO repetición contra el historial completo (requisito 3)")
        bloqueados_por_historial = 0
        for c in r1.entregados:
            v = historial_previo.evaluar(c.fingerprint())
            if v.bloquea:
                bloqueados_por_historial += 1
        print(f"entregados que en realidad repetían el historial: "
             f"{bloqueados_por_historial} (esperado: 0)")
        assert bloqueados_por_historial == 0

        linea("4. Exportación — 'Excel maestro actualizado' (entregable)")
        rutas = bm.exportar_banco(r1, excel_path=Path(d) / "banco-maestro-demo.xlsx",
                                  csv_path=Path(d) / "banco-maestro-demo.csv")
        for k, v in rutas.items():
            print(f"{k}: {v} ({Path(v).stat().st_size} bytes)")

        linea("5. Segunda corrida — prueba de que ENTREGADO bloquea el futuro (requisito 4)")
        r2 = bm.construir_banco(objetivo=80, seed=9200, factor_reserva=3,
                                banco_previo_path=banco_path, persistir=True)
        ids1 = {c.candidate_id for c in r1.entregados}
        ids2 = {c.candidate_id for c in r2.entregados}
        print(f"solapamiento de candidate_id entre corrida 1 y 2: {len(ids1 & ids2)} "
             f"(esperado: 0 — los IDs de la corrida 2 nunca coinciden con los de la 1)")
        fps2 = [c.fingerprint() for c in r2.entregados]
        equivalentes_entre_corridas = [(a.content_id, b.content_id)
                                       for a in fps2 for b in fps
                                       if a.equivalente_a(b)]
        print(f"equivalentes semánticos entre corrida 1 y corrida 2: "
             f"{len(equivalentes_entre_corridas)} (esperado: 0)")
        assert not equivalentes_entre_corridas

        citan_entregado = [m for _, m in r2.bloqueados if "ya ENTREGADO" in m]
        print(f"bloqueados en la corrida 2 que citan ENTREGADO de la corrida 1: "
             f"{len(citan_entregado)}")
        if citan_entregado:
            print(f"  ejemplo: {citan_entregado[0]}")

    linea("RESULTADO")
    print("El motor real produce temas variados (9 categorías, "
         f"{len(r1.distribucion_materia)} materias), sin duplicados internos, sin repetir "
         "el historial completo, y ENTREGADO bloquea correctamente una segunda corrida "
         "sobre la misma semilla. Ningún candidato queda verificado jurídicamente: todos "
         "permanecen NO_VERIFICADO con proxima_accion='legalmente-legal-verification' "
         "(CLAUDE.md §4). NO MERGE. NO DEPLOY. NO PUBLICAR.")


if __name__ == "__main__":
    main()
