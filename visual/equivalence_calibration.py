"""Recalibración de la política de dos niveles — Paso 3 del mandato
'CALIBRACIÓN POSITIVA + PRODUCCIÓN REAL' (Founder, 2026-09-14).

Usa:
  - NEGATIVOS: los 18 pares reales del Founder (10 B COEXISTIR + 8 C
    DISTINTA). Ground truth real, no derivado.
  - POSITIVOS: los 8 pares sintéticos base (mutación 'solo_hook' de
    `calibration_positive_set` — el positivo mínimo: mismo núcleo semántico,
    sólo cambia el hook). Marcados SYNTHETIC_CALIBRATION_ONLY; nunca se
    mezclan con corpus real ni se usan como contenido.

Mide `equivalence_policy.nivel_equivalencia()` — el criterio de DOS NIVELES,
no el `equivalente_a()` binario que calibra `calibration.py`. Por eso las
métricas aquí tienen una tercera categoría que `calibration.py` no tiene:
ALERTA_DE_PROXIMIDAD no es acierto ni fallo — es "pedir revisión humana", el
resultado que el Founder pidió que existiera. Se reporta aparte, nunca se
cuenta como bloqueo ni como paso.

Esto PROPONE un `alerta_minimo` recalibrado. No lo activa. Activar sigue
siendo el cambio de una línea descrito en `equivalence_policy.py`, y sigue
sin hacerse aquí.
"""

import statistics
from dataclasses import dataclass, field

import calibration as cal
import calibration_positive_set as cps
import corpus_import
from equivalence_policy import ALERTA_MAXIMO, BLOQUEO, ALERTA_DE_PROXIMIDAD, nivel_equivalencia

CANDIDATOS_ALERTA_MINIMO = (0.05, 0.10, 0.15, 0.20, 0.22, 0.25, 0.28, 0.30, 0.35)


def positivos_sinteticos(mutacion="solo_hook", semillas=None):
    """El positivo mínimo del mandato: mismo núcleo, sólo cambia el hook.
    Las demás mutaciones (Paso 2) ya se validan en la prueba de
    contaminación — no se repiten aquí para no duplicar evidencia."""
    return [(p.base, p.mutado) for p in cps.generar_pares(semillas) if p.mutacion == mutacion]


def negativos_reales(registros=None, path=None):
    if registros is None:
        registros, _ = corpus_import.construir_registros()
    pares, meta = cal.cargar_pares_etiquetados(registros, path)
    negativos = [(a, b) for a, b, etiqueta, _ in pares
                 if cal.BLOQUEO_POR_ETIQUETA.get(etiqueta) is False]
    return negativos, meta


@dataclass
class PuntoRecalibracion:
    alerta_minimo: float = 0.0
    alerta_maximo: float = ALERTA_MAXIMO
    tp: int = 0                 # positivo sintético -> BLOQUEO (acierto duro)
    positivos_en_alerta: int = 0  # positivo sintético -> ALERTA (revisión, no acierto ni fallo)
    fn: int = 0                 # positivo sintético -> NO_RELACIONADO (fallo: se perdió del todo)
    fp: int = 0                 # negativo real -> BLOQUEO (fallo grave: bloqueo autónomo indebido)
    negativos_en_alerta: int = 0  # negativo real -> ALERTA (costo de revisión, no error de bloqueo)
    tn: int = 0                 # negativo real -> NO_RELACIONADO (acierto)
    recall_estricto: float = 0.0
    cobertura_con_revision: float = 0.0
    precision_estricta: float = 0.0
    tasa_alerta_negativos: float = 0.0
    fallos: list = field(default_factory=list)

    def to_dict(self):
        return {"alerta_minimo": self.alerta_minimo, "alerta_maximo": self.alerta_maximo,
                "tp": self.tp, "positivos_en_alerta": self.positivos_en_alerta, "fn": self.fn,
                "fp": self.fp, "negativos_en_alerta": self.negativos_en_alerta, "tn": self.tn,
                "recall_estricto": self.recall_estricto,
                "cobertura_con_revision": self.cobertura_con_revision,
                "precision_estricta": self.precision_estricta,
                "tasa_alerta_negativos": self.tasa_alerta_negativos,
                "fallos": list(self.fallos)}


def evaluar_alerta_minimo(alerta_minimo, positivos, negativos, alerta_maximo=ALERTA_MAXIMO):
    p = PuntoRecalibracion(alerta_minimo=alerta_minimo, alerta_maximo=alerta_maximo)

    for a, b in positivos:
        v = nivel_equivalencia(a, b, alerta_minimo=alerta_minimo, alerta_maximo=alerta_maximo)
        if v.nivel == BLOQUEO:
            p.tp += 1
        elif v.nivel == ALERTA_DE_PROXIMIDAD:
            p.positivos_en_alerta += 1
        else:
            p.fn += 1
            p.fallos.append(f"FN sintético: {a.content_id}~{b.content_id} "
                             f"era equivalente por diseño y no llegó ni a alerta ({v.nivel}, d={v.distancia}).")

    for a, b in negativos:
        v = nivel_equivalencia(a, b, alerta_minimo=alerta_minimo, alerta_maximo=alerta_maximo)
        if v.nivel == BLOQUEO:
            p.fp += 1
            p.fallos.append(f"FP real: {a.content_id}~{b.content_id} el Founder dijo "
                             f"distinta/coexiste y la política las bloqueó (d={v.distancia}).")
        elif v.nivel == ALERTA_DE_PROXIMIDAD:
            p.negativos_en_alerta += 1
        else:
            p.tn += 1

    n_pos, n_neg = len(positivos), len(negativos)
    p.recall_estricto = round(p.tp / n_pos, 4) if n_pos else 0.0
    p.cobertura_con_revision = round((p.tp + p.positivos_en_alerta) / n_pos, 4) if n_pos else 0.0
    p.precision_estricta = round(p.tp / (p.tp + p.fp), 4) if (p.tp + p.fp) else 0.0
    p.tasa_alerta_negativos = round(p.negativos_en_alerta / n_neg, 4) if n_neg else 0.0
    return p


def distribucion_distancias(pares):
    """Distribución de distancia agregada, sin decidir nada — sólo describir
    dónde cae la evidencia real, para que el Founder vea el mapa antes de
    fijar un corte."""
    valores = []
    for a, b in pares:
        d = a.distancia_semantica(b)
        if d.comparable:
            valores.append(d.valor)
    if not valores:
        return {"n": 0}
    valores.sort()
    return {"n": len(valores), "min": round(valores[0], 4), "max": round(valores[-1], 4),
            "media": round(statistics.mean(valores), 4),
            "mediana": round(statistics.median(valores), 4),
            "valores": [round(v, 4) for v in valores]}


def proponer_cutoff(puntos):
    """Candidato: fp=0 (nunca bloquea autónomamente lo que el Founder marcó
    distinto/coexiste) y, entre esos, el mayor recall_estricto; empate lo
    rompe el alerta_minimo MÁS BAJO. `alerta_minimo` es el borde del
    BLOQUEO duro (d < alerta_minimo con corroboración completa) — subirlo
    ENSANCHA cuánto puede auto-bloquearse, no lo reduce. El mandato del
    Founder es "señal, no bloqueo autónomo": entre dos umbrales con la
    misma evidencia a favor, el más estrecho (más conservador) es el que
    corresponde proponer, dejando lo demás en ALERTA_DE_PROXIMIDAD para
    revisión humana en vez de auto-bloqueo. Ninguno se activa aquí."""
    seguros = [p for p in puntos if p.fp == 0]
    if not seguros:
        return None
    mejor_recall = max(p.recall_estricto for p in seguros)
    candidatos = [p for p in seguros if p.recall_estricto == mejor_recall]
    return min(candidatos, key=lambda p: p.alerta_minimo)


LIMITACION_POSITIVOS = (
    "Los 8 positivos sintéticos ('solo_hook') sólo cambian el hook: todos los "
    "demás campos son literalmente idénticos, así que su distancia agregada "
    "es 0.0 en los ocho. Eso basta para fijar un PISO de recall (si "
    "alerta_minimo no cubre ni siquiera 0.0, el criterio ya falla), pero NO "
    "dice nada sobre dónde está el TECHO seguro de alerta_minimo — para eso "
    "harían falta positivos reales con distancia agregada intermedia (mismo "
    "concepto_nucleo/pregunta_resuelta/relacion pero redactados de forma "
    "distinta en los ejes de texto libre). Por eso el barrido de candidatos "
    "da resultados idénticos entre 0.05 y 0.35: con este set, cualquier "
    "alerta_minimo por encima de 0.0 satisface el piso igual de bien, y el "
    "criterio de desempate manda al más bajo. La propuesta es honesta sobre "
    "esa carencia, no la esconde subiendo el umbral sin evidencia que lo "
    "sostenga.")


def informe_recalibracion(alerta_maximo=ALERTA_MAXIMO, candidatos=CANDIDATOS_ALERTA_MINIMO):
    positivos = positivos_sinteticos()
    negativos, meta = negativos_reales()
    puntos = [evaluar_alerta_minimo(am, positivos, negativos, alerta_maximo) for am in candidatos]
    propuesto = proponer_cutoff(puntos)
    return {
        "estado": "PROPUESTA_NO_ACTIVADA",
        "aviso": "threshold_state: PENDIENTE_SET_POSITIVO en equivalence_policy.py sigue vigente "
                 "hasta decisión expresa del Founder. Este informe PROPONE, no activa.",
        "limitacion_positivos": LIMITACION_POSITIVOS,
        "fuente_negativos": meta,
        "n_positivos_sinteticos": len(positivos),
        "n_negativos_reales": len(negativos),
        "distribucion_distancias_positivos": distribucion_distancias(positivos),
        "distribucion_distancias_negativos": distribucion_distancias(negativos),
        "puntos": [p.to_dict() for p in puntos],
        "cutoff_propuesto": propuesto.to_dict() if propuesto else None,
        "alerta_maximo_vigente": alerta_maximo,
    }


if __name__ == "__main__":
    import json
    print(json.dumps(informe_recalibracion(), indent=2, ensure_ascii=False))
