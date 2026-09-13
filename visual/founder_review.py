"""Revisión Founder del umbral — Fase 1.

`corpus/eval-umbral-candidato.json` lo etiquetó el agente. No es ground truth.
Este módulo lo convierte en una hoja de revisión legible y luego incorpora las
decisiones reales del Founder SIN destruir el conjunto original: escribe un
fichero nuevo (`corpus/eval-umbral-founder.json`) con trazabilidad completa —
AGENT_LABEL, FOUNDER_LABEL, FECHA, CAMBIO y la razón si se da una.

Interfaz deliberadamente mínima: cuatro letras.

    A — MISMA IDEA / DEBE BLOQUEARSE
    B — RELACIONADAS PERO PUEDEN COEXISTIR
    C — CLARAMENTE DISTINTAS
    D — NO HAY INFORMACIÓN SUFICIENTE

El Founder contesta con líneas "1A", "2B", ... — nada más. `parsear_respuestas`
no exige justificación; `razones` es opcional y por par.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import corpus_import as ci
from corpus_enrichment import enriquecer

CORPUS_DIR = Path(__file__).resolve().parent.parent / "corpus"
EVAL_PATH = CORPUS_DIR / "eval-umbral-candidato.json"
FOUNDER_EVAL_PATH = CORPUS_DIR / "eval-umbral-founder.json"

OPCIONES = {
    "A": "BLOQUEAR",
    "B": "COEXISTIR",
    "C": "DISTINTA",
    "D": "SIN_INFO",
}

# A qué le corresponde cada opción Founder en el vocabulario interno de
# equivalencia (usado por calibration.py). B y D no fijan una postura fuerte:
# B dice explícitamente "coexisten" (no equivalentes) y D dice "no lo sé" — no
# se traduce D a un valor de calibración, se excluye del cómputo igual que la
# zona gris del conjunto del agente.
MAPEA_A_BLOQUEO = {"A": True, "B": False, "C": False, "D": None}

# Bucket del agente contra el que se compara la decisión Founder para saber si
# CONFIRMA o CORRIGE. AGENTE_BLOQUEA sólo para EQUIVALENTE; todo lo demás no.
_AGENTE_BLOQUEA = {"EQUIVALENTE": True, "MUY_PROXIMO": None,
                   "RELACIONADO_DISTINTO": False, "DISTINTO": False}


def _cargar_eval(path=None):
    return json.loads(Path(path or EVAL_PATH).read_text(encoding="utf-8"))


def _por_id(enriquecidos):
    return {e.content_id: e for e in enriquecidos}


def generar_hoja_revision(path=None, registros=None):
    """Texto plano, listo para pegar en el chat. Cada par muestra los
    campos reales — no el resumen que el agente escribió — para que la
    decisión del Founder se apoye en el dato, no en mi lectura de él."""
    data = _cargar_eval(path)
    if registros is None:
        registros, _ = ci.construir_registros()
    enr = _por_id(enriquecer(registros))

    lineas = []
    lineas.append("REVISIÓN FOUNDER DEL UMBRAL DE EQUIVALENCIA")
    lineas.append(f"{len(data['pares'])} pares. Para cada uno, una letra:")
    lineas.append("  A — MISMA IDEA / DEBE BLOQUEARSE")
    lineas.append("  B — RELACIONADAS PERO PUEDEN COEXISTIR")
    lineas.append("  C — CLARAMENTE DISTINTAS")
    lineas.append("  D — NO HAY INFORMACIÓN SUFICIENTE")
    lineas.append("Responde con líneas \"1A\", \"2B\", ... — nada más hace falta.")
    lineas.append("")

    for i, par in enumerate(data["pares"], 1):
        a, b = enr.get(par["a"]), enr.get(par["b"])
        if a is None or b is None:
            lineas.append(f"PAR #{i} — {par['a']}/{par['b']}: no encontrado en el corpus.")
            continue
        lineas.append(f"PAR #{i}")
        lineas.append(f"  PIEZA A: {a.content_id} — «{a.base.titular}»")
        lineas.append(f"  PIEZA B: {b.content_id} — «{b.base.titular}»")
        lineas.append(f"  Materia:            {a.base.materia:<28} / {b.base.materia}")
        lineas.append(f"  Concepto:           {a.concepto_nucleo_enriquecido[:36]!r:<30} "
                      f"/ {b.concepto_nucleo_enriquecido[:36]!r}")
        lineas.append(f"  Familia editorial:  {a.base.familia_editorial:<28} "
                      f"/ {b.base.familia_editorial}")
        preg_a = a.pregunta_resuelta_enriquecida or "(sin evidencia suficiente)"
        preg_b = b.pregunta_resuelta_enriquecida or "(sin evidencia suficiente)"
        lineas.append(f"  Pregunta resuelta:  {preg_a[:40]}")
        lineas.append(f"                      {preg_b[:40]}")
        lineas.append(f"  Necesidad:          {a.base.necesidad:<28} / {b.base.necesidad}")
        d = a.base.fingerprint().distancia_semantica(b.base.fingerprint())
        lineas.append(f"  Distancia calculada: {d.valor if d.comparable else 'no comparable'}")
        if a.content_id == "LM-026" and b.content_id == "LM-027":
            lineas.append("  AVISO: la etiqueta original del agente para este par se basó en "
                          "el slug ('depositos-...'), no en el titular real. El titular de "
                          "LM-026 es sobre anticipo/arras/pena, no sobre depósito. Revísalo "
                          "con eso en cuenta.")
        lineas.append("")
    return "\n".join(lineas)


def parsear_respuestas(texto):
    """'1A' o '1 A - por que...' -> {1: ('A', 'por que...')}. Tolera espacios,
    minúsculas y un separador opcional antes de la razón."""
    import re
    respuestas = {}
    for linea in texto.strip().splitlines():
        m = re.match(r"^\s*(\d+)\s*[\.\)]?\s*([A-Da-d])\b\s*[-:]?\s*(.*)$", linea)
        if not m:
            continue
        num, letra, razon = int(m.group(1)), m.group(2).upper(), m.group(3).strip()
        respuestas[num] = (letra, razon)
    return respuestas


@dataclass
class InformeIncorporacion:
    total_pares: int = 0
    respondidos: int = 0
    sin_responder: list = field(default_factory=list)
    confirma_agente: int = 0
    corrige_agente: int = 0
    sin_comparar: int = 0
    salida: str = ""

    def to_dict(self):
        return {"total_pares": self.total_pares, "respondidos": self.respondidos,
                "sin_responder": list(self.sin_responder),
                "confirma_agente": self.confirma_agente,
                "corrige_agente": self.corrige_agente,
                "sin_comparar": self.sin_comparar, "salida": self.salida}


def incorporar_decisiones(respuestas, eval_path=None, salida_path=None, fecha=None):
    """Escribe `corpus/eval-umbral-founder.json`. NUNCA toca el original.

    `respuestas` es lo que devuelve `parsear_respuestas`: {num: (letra, razon)}.
    """
    data = _cargar_eval(eval_path)
    fecha = fecha or datetime.now(timezone.utc).isoformat()
    pares_out = []
    confirma = corrige = sin_comparar = 0
    sin_responder = []

    for i, par in enumerate(data["pares"], 1):
        agent_label = par["etiqueta"]
        letra, razon = respuestas.get(i, (None, ""))
        if letra is None:
            sin_responder.append(i)
            entrada = {"par_id": i, "a": par["a"], "b": par["b"],
                      "agent_label": agent_label, "founder_label": None,
                      "founder_label_mapped": None, "founder_razon": "",
                      "fecha": fecha, "cambio": "SIN_DECISION"}
            pares_out.append(entrada)
            continue

        founder_mapeado = OPCIONES[letra]
        agente_bloquea = _AGENTE_BLOQUEA.get(agent_label)
        founder_bloquea = MAPEA_A_BLOQUEO[letra]
        if founder_bloquea is None or agente_bloquea is None:
            cambio = "SIN_COMPARAR"
            sin_comparar += 1
        elif founder_bloquea == agente_bloquea:
            cambio = "CONFIRMA_AGENTE"
            confirma += 1
        else:
            cambio = "CORRIGE_AGENTE"
            corrige += 1

        pares_out.append({
            "par_id": i, "a": par["a"], "b": par["b"],
            "agent_label": agent_label, "founder_label": letra,
            "founder_label_mapped": founder_mapeado,
            "founder_razon": razon or par.get("razon", ""),
            "fecha": fecha, "cambio": cambio,
        })

    salida = {
        "schema_version": "1.0",
        "estado": "GROUND_TRUTH_FOUNDER" if not sin_responder else "GROUND_TRUTH_FOUNDER_PARCIAL",
        "fuente_original": str(eval_path or EVAL_PATH),
        "fecha_incorporacion": fecha,
        "opciones": OPCIONES,
        "pares": pares_out,
    }
    out = Path(salida_path or FOUNDER_EVAL_PATH)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(salida, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return InformeIncorporacion(
        total_pares=len(data["pares"]), respondidos=len(data["pares"]) - len(sin_responder),
        sin_responder=sin_responder, confirma_agente=confirma, corrige_agente=corrige,
        sin_comparar=sin_comparar, salida=str(out))
