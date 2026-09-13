"""Calibración de UMBRAL_EQUIVALENCIA contra el corpus histórico real.

El umbral 0.30 se fijó mirando pares sintéticos. Este módulo lo mide.

DOS FUENTES DE VERDAD, deliberadamente separadas porque no valen lo mismo:

1. DERIVADOS CANÓNICOS (positivos duros). Se toma una pieza REAL del corpus y
   se le cambian sólo hook, formato, emoción, metáfora y dirección artística.
   El canon DEFINE eso como el mismo contenido ("dos contenidos semánticamente
   equivalentes no son nuevos porque cambie el título, el hook o el estilo"),
   así que la etiqueta no es un juicio: es la regla. Un umbral que no bloquea
   estos casos está roto por definición.

2. PARES ETIQUETADOS (`corpus/eval-umbral-candidato.json`). Los etiquetó el
   AGENTE leyendo los guiones, no el Founder. Sirven para detectar falsos
   positivos — bloquear cosas legítimamente distintas — pero NO acreditan
   certeza estadística. El fichero lo dice y este módulo lo repite en cada
   informe: no se presenta como ground truth humano.

Los pares MUY_PROXIMO se excluyen del cómputo: son la zona gris donde ni el
agente ni, previsiblemente, el Founder tienen una respuesta única. Contarlos
en un sentido u otro inflaría artificialmente la métrica elegida.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path

import corpus_import
from semantic_fingerprint import SemanticFingerprint

EVAL_PATH = Path(__file__).resolve().parent.parent / "corpus" / "eval-umbral-candidato.json"

BLOQUEAR = ("EQUIVALENTE",)
NO_BLOQUEAR = ("RELACIONADO_DISTINTO", "DISTINTO")
ZONA_GRIS = ("MUY_PROXIMO",)

UMBRALES = (0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50, 0.60)


def derivados_canonicos(registros, cuantos=25):
    """Positivos duros: la misma pieza con otra ropa expresiva y visual."""
    pares = []
    for r in registros[:cuantos]:
        base = r.fingerprint()
        disfraz = SemanticFingerprint.from_dict(base.to_dict())
        disfraz.content_id = base.content_id + "-DISFRAZ"
        disfraz.hook = "Otro titular completamente distinto para la misma pieza"
        disfraz.formato = "historia"
        disfraz.emocion = "sorpresa"
        disfraz.metafora = "una metáfora visual enteramente nueva y sin relación"
        disfraz.direccion_artistica = "estampa ukiyo-e"
        disfraz.escena = "azotea urbana"
        disfraz.camara = "contrapicado"
        disfraz.composicion = "espejo empañado"
        pares.append((base, disfraz))
    return pares


def cargar_pares_etiquetados(registros, path=None):
    p = Path(path or EVAL_PATH)
    if not p.is_file():
        return [], {}
    data = json.loads(p.read_text(encoding="utf-8"))
    por_id = {r.content_id: r for r in registros}
    fuera, pares = [], []
    for par in data.get("pares", []):
        a, b = por_id.get(par["a"]), por_id.get(par["b"])
        if a is None or b is None:
            fuera.append(par)
            continue
        pares.append((a.fingerprint(), b.fingerprint(), par["etiqueta"], par.get("razon", "")))
    meta = {"estado": data.get("estado"), "aviso": data.get("aviso"),
            "pares_no_resueltos": fuera}
    return pares, meta


@dataclass
class PuntoCalibracion:
    umbral: float = 0.0
    tp: int = 0
    fp: int = 0
    fn: int = 0
    tn: int = 0
    precision: float = 0.0
    recall: float = 0.0
    f1: float = 0.0
    fallos: list = field(default_factory=list)

    def to_dict(self):
        return {"umbral": self.umbral, "tp": self.tp, "fp": self.fp, "fn": self.fn,
                "tn": self.tn, "precision": self.precision, "recall": self.recall,
                "f1": self.f1, "fallos": list(self.fallos)}


def evaluar_umbral(umbral, canonicos, etiquetados):
    """TP = bloquea lo que debía bloquear. FP = bloquea lo legítimamente distinto."""
    tp = fp = fn = tn = 0
    fallos = []

    for base, disfraz in canonicos:
        if base.equivalente_a(disfraz, umbral=umbral):
            tp += 1
        else:
            fn += 1
            fallos.append(f"FN canónico: {base.content_id} no reconoce su propio disfraz")

    for a, b, etiqueta, _ in etiquetados:
        if etiqueta in ZONA_GRIS:
            continue
        bloquea = a.equivalente_a(b, umbral=umbral)
        if etiqueta in BLOQUEAR:
            if bloquea:
                tp += 1
            else:
                fn += 1
                fallos.append(f"FN: {a.content_id}~{b.content_id} son la misma pregunta y pasó")
        else:
            if bloquea:
                fp += 1
                fallos.append(f"FP: {a.content_id}~{b.content_id} son distintas y se bloqueó")
            else:
                tn += 1

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return PuntoCalibracion(umbral, tp, fp, fn, tn, round(precision, 4),
                            round(recall, 4), round(f1, 4), fallos)


def barrido(registros=None, umbrales=UMBRALES, path=None):
    if registros is None:
        registros, _ = corpus_import.construir_registros()
    canonicos = derivados_canonicos(registros)
    etiquetados, meta = cargar_pares_etiquetados(registros, path)
    puntos = [evaluar_umbral(u, canonicos, etiquetados) for u in umbrales]
    return puntos, meta, {"canonicos": len(canonicos),
                          "etiquetados_computados": len([e for e in etiquetados
                                                         if e[2] not in ZONA_GRIS]),
                          "zona_gris_excluida": len([e for e in etiquetados
                                                     if e[2] in ZONA_GRIS])}
