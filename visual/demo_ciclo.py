"""Demostración ejecutable del ciclo del organismo.

    python3 demo_ciclo.py        (desde el directorio visual/)

Produce la evidencia que pide el Handoff §16: reserva amplia → lote de 10 →
curaduría 3/7 → segundo lote que aprende sin encerrarse. No genera arte, no
gasta créditos, no publica nada y no verifica Derecho: imprime el estado real
del motor de selección.
"""

import organism
from memory import normaliza
from semantic_memory import SemanticMemory, DESCARTADA, PRESELECCIONADA


def tabla(batch):
    print(f"  {'#':<3}{'MATERIA':<24}{'FAMILIA EDITORIAL':<24}{'NECESIDAD':<13}"
          f"{'ÁNGULO':<15}{'EMOCIÓN':<12}")
    for i, c in enumerate(batch.candidatos, 1):
        print(f"  {i:<3}{c.materia:<24}{c.familia_editorial:<24}{c.necesidad:<13}"
              f"{c.angulo:<15}{c.emocion:<12}")


def telemetria(batch):
    t = batch.qa["telemetria"]
    print(f"  veredicto QA .............. {batch.qa['veredicto']}")
    print(f"  distancia semántica mín ... {t['semantic_distance_min']}")
    print(f"  distancia semántica media . {t['semantic_distance_media']}")
    print(f"  topic_repetition .......... {t['topic_repetition']}")
    print(f"  matter_coverage ........... {t['matter_coverage']}")
    print(f"  family_coverage ........... {t['family_coverage']}")
    print(f"  emotional_rotation ........ {t['emotional_rotation']}")
    print(f"  regeneration_rate ......... {t['regeneration_rate']}")
    print(f"  reserva evaluada .......... {batch.reserva_total} candidatos")
    print(f"  intentos hasta pasar QA ... {batch.intentos}")


def main():
    memoria = SemanticMemory()

    print("=" * 92)
    print("LOTE 1 — generado sin autorización previa (Handoff §5)")
    print("=" * 92)
    lote1 = organism.producir_lote("lote-1", n=10, seed=100, memoria=memoria)
    tabla(lote1)
    print()
    telemetria(lote1)
    print(f"  estado entregado .......... {lote1.estado}")

    elegidos = [lote1.candidatos[i].candidate_id for i in (0, 3, 7)]
    print()
    print("=" * 92)
    print("CURADURÍA DEL FOUNDER — conserva 3, descarta 7")
    print("=" * 92)
    resumen = organism.registrar_curaduria(lote1, elegidos, memoria)
    for c in lote1.candidatos:
        marca = "CONSERVADA" if c.candidate_id in set(elegidos) else "descartada"
        print(f"  {marca:<12}{c.materia:<24}{c.familia_editorial}")
    print(f"\n  selection_rate = {resumen['selection_rate']}  "
          f"(KPI crítico de producción)")

    print()
    print("=" * 92)
    print("LOTE 2 — después de aprender de esas señales")
    print("=" * 92)
    lote2 = organism.producir_lote("lote-2", n=10, seed=200, memoria=memoria)
    tabla(lote2)
    print()
    telemetria(lote2)

    print()
    print("=" * 92)
    print("PRUEBA: ¿aprendió sin encerrarse ni repetir?")
    print("=" * 92)

    repeticiones = [(a.content_id, b.content_id)
                    for a in lote2.fingerprints() for b in lote1.fingerprints()
                    if a.equivalente_a(b)]
    print(f"  piezas del lote 2 semánticamente equivalentes al lote 1 ... {len(repeticiones)}")

    descartadas_mat = {e.fingerprint["materia"] for e in memoria.entries(DESCARTADA)}
    por_materia = {}
    for e in memoria.entries(DESCARTADA):
        por_materia.setdefault(e.fingerprint["materia"], set()).add(
            e.fingerprint["familia_editorial"])
    vuelven = [c for c in lote2.candidatos if c.materia in descartadas_mat]
    otra_puerta = [c for c in vuelven if c.familia_editorial not in por_materia[c.materia]]
    print(f"  materias descartadas que reaparecen ....................... "
          f"{len({c.materia for c in vuelven})} de {len(descartadas_mat)}")
    print(f"  ...y lo hacen por OTRA familia editorial .................. {len(otra_puerta)}")
    for c in otra_puerta[:5]:
        antes = sorted(por_materia[c.materia])
        print(f"      {c.materia}: descartada como {antes} -> vuelve como "
              f"'{c.familia_editorial}'")

    preseleccionadas = {normaliza(e.fingerprint["familia_editorial"])
                        for e in memoria.entries(PRESELECCIONADA)}
    familias2 = {normaliza(c.familia_editorial) for c in lote2.candidatos}
    print(f"\n  familias del lote 2 que NO estaban preseleccionadas ....... "
          f"{len(familias2 - preseleccionadas)} de {len(familias2)}")
    print("  (si fueran 0, el sistema se estaría encerrando en lo ya premiado)")

    print()
    print("  LÍMITE: todos los candidatos siguen NO_VERIFICADO. Este motor "
          "selecciona y\n  diversifica; NO verifica Derecho ni autoriza publicación.")


if __name__ == "__main__":
    main()
