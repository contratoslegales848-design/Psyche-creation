"""Conjunto de calibración positiva sintética — Founder, 2026-09-14.

Los 18 pares reales del Founder (`corpus/eval-umbral-founder.json`) son TODOS
negativos: 10 B (coexisten) + 8 C (distintas), 0 A (bloquear). Sin un
positivo conocido, RECALL no se puede medir — un umbral que nunca bloquea
nada tendría recall indefinido pero parecería perfecto. Por eso el Founder
ordenó construir `corpus/calibration-positive-set-v1.json`: 8 semillas
DELIBERADAMENTE equivalentes (mismo concepto_nucleo + pregunta_resuelta +
relacion), marcadas `SYNTHETIC_CALIBRATION_ONLY` — nunca corpus histórico,
nunca fuente de contenido real.

PRUEBA DE CONTAMINACIÓN (Paso 2 del mandato): para cada semilla se generan
mutaciones controladas que cambian SÓLO capas expresivas/visuales (hook,
familia editorial, formato, emoción, metáfora, dirección artística) mientras
el núcleo semántico permanece fijo. Si una mutación deja de ser equivalente
bajo `equivalente_a()`, hay CONTAMINACIÓN entre la memoria semántica y las
capas editorial/visual — el canon central de esta reconciliación (el título,
el hook o el estilo nunca deben comprar novedad) se estaría rompiendo.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path

from semantic_fingerprint import SemanticFingerprint

POSITIVE_SET_PATH = Path(__file__).resolve().parent.parent / "corpus" / "calibration-positive-set-v1.json"

# Cada mutación cambia un subconjunto de capas EXPRESIVAS/VISUALES,
# nunca el núcleo semántico (concepto_nucleo/pregunta_resuelta/relacion).
MUTACIONES = {
    "solo_hook": {},  # el propio texto_a/texto_b YA es la mutación de hook
    "hook_y_familia": {"familia_editorial": "checklist", "formato": "listado"},
    "hook_familia_y_emocion": {"familia_editorial": "duda_frecuente",
                               "formato": "pregunta", "emocion": "sorpresa"},
    "mutacion_total_expresiva_y_visual": {
        "familia_editorial": "confusion_habitual", "formato": "historia",
        "emocion": "curiosidad", "metafora": "una puerta entreabierta que nadie cruza",
        "escena": "archivo con luz de tarde", "composicion": "diagonal",
        "camara": "picado corto", "direccion_artistica": "claroscuro_de_museo"},
}


def cargar_semillas(path=None):
    data = json.loads(Path(path or POSITIVE_SET_PATH).read_text(encoding="utf-8"))
    if data.get("estado") != "SYNTHETIC_CALIBRATION_ONLY":
        raise ValueError(
            "el conjunto de calibración positiva debe declararse "
            "SYNTHETIC_CALIBRATION_ONLY explícitamente; no se usa sin esa marca.")
    return data["semillas"], data.get("aviso", "")


def _fingerprint_base(semilla, texto):
    return SemanticFingerprint(
        content_id=f"{semilla['id']}-base", materia=semilla["materia"],
        submateria=semilla["submateria"], concepto_nucleo=semilla["concepto_nucleo"],
        relacion=semilla["relacion"], familia_editorial="mito",
        necesidad=semilla["necesidad"], pregunta_resuelta=semilla["pregunta_resuelta"],
        angulo=semilla["angulo"], contexto_funcional=semilla["contexto_funcional"],
        rol_lector=semilla["rol_lector"], hook=texto, formato="frase")


@dataclass
class ParPositivo:
    semilla_id: str
    mutacion: str
    base: SemanticFingerprint
    mutado: SemanticFingerprint

    def to_dict(self):
        return {"semilla_id": self.semilla_id, "mutacion": self.mutacion,
                "base": self.base.to_dict(), "mutado": self.mutado.to_dict()}


def generar_pares(semillas=None):
    """Un par 'base' (texto_a) por semilla, más una mutación por cada
    entrada de MUTACIONES aplicada sobre 'mutado' (texto_b) — el hook YA
    difiere entre a y b en toda semilla; las mutaciones añaden capas
    adicionales encima de esa diferencia de hook."""
    if semillas is None:
        semillas, _ = cargar_semillas()
    pares = []
    for s in semillas:
        base = _fingerprint_base(s, s["texto_a"])
        for nombre_mut, cambios in MUTACIONES.items():
            mutado = SemanticFingerprint.from_dict(_fingerprint_base(s, s["texto_b"]).to_dict())
            mutado.content_id = f"{s['id']}-{nombre_mut}"
            for campo, valor in cambios.items():
                setattr(mutado, campo, valor)
            pares.append(ParPositivo(s["id"], nombre_mut, base, mutado))
    return pares


@dataclass
class ResultadoContaminacion:
    semilla_id: str
    mutacion: str
    equivalente: bool
    distancia: float
    contaminado: bool   # True si DEBERÍA ser equivalente y dejó de serlo

    def to_dict(self):
        return {"semilla_id": self.semilla_id, "mutacion": self.mutacion,
                "equivalente": self.equivalente, "distancia": self.distancia,
                "contaminado": self.contaminado}


def prueba_de_contaminacion(pares=None, umbral=None):
    """Para cada par, ¿sigue siendo equivalente tras la mutación? Debe serlo
    SIEMPRE — el núcleo semántico nunca cambió. Si deja de serlo, se marca
    `contaminado=True`: la capa expresiva/visual está filtrándose a la
    decisión de novedad semántica."""
    if pares is None:
        pares = generar_pares()
    resultados = []
    for p in pares:
        kw = {"umbral": umbral} if umbral is not None else {}
        equiv = p.base.equivalente_a(p.mutado, **kw)
        d = p.base.distancia_semantica(p.mutado)
        resultados.append(ResultadoContaminacion(
            semilla_id=p.semilla_id, mutacion=p.mutacion, equivalente=equiv,
            distancia=d.valor if d.comparable else None, contaminado=not equiv))
    return resultados


def resumen_contaminacion(resultados=None):
    resultados = resultados if resultados is not None else prueba_de_contaminacion()
    contaminados = [r for r in resultados if r.contaminado]
    por_mutacion = {}
    for r in resultados:
        por_mutacion.setdefault(r.mutacion, {"total": 0, "contaminados": 0})
        por_mutacion[r.mutacion]["total"] += 1
        if r.contaminado:
            por_mutacion[r.mutacion]["contaminados"] += 1
    return {"total": len(resultados), "contaminados": len(contaminados),
            "limpio": len(contaminados) == 0, "por_mutacion": por_mutacion,
            "detalle_contaminados": [r.to_dict() for r in contaminados]}
