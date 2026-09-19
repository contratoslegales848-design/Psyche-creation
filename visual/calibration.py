"""Calibración de UMBRAL_EQUIVALENCIA contra el corpus histórico real.

El umbral 0.30 se fijó mirando pares sintéticos. Este módulo lo mide.

DOS FUENTES DE VERDAD, deliberadamente separadas porque no valen lo mismo:

1. DERIVADOS CANÓNICOS (positivos duros). Se toma una pieza REAL del corpus y
   se le cambian sólo hook, formato, emoción, metáfora y dirección artística.
   El canon DEFINE eso como el mismo contenido ("dos contenidos semánticamente
   equivalentes no son nuevos porque cambie el título, el hook o el estilo"),
   así que la etiqueta no es un juicio: es la regla. Un umbral que no bloquea
   estos casos está roto por definición.

2. PARES ETIQUETADOS. Dos posibles ficheros, en orden de preferencia:

   `corpus/eval-umbral-founder.json`   — GROUND TRUTH real. Lo produce
       `founder_review.incorporar_decisiones()` a partir de las respuestas
       que el Founder da a la hoja de `founder_review.generar_hoja_revision()`.
       Si existe, este módulo lo usa y lo dice en el informe.
   `corpus/eval-umbral-candidato.json` — lo etiquetó el AGENTE leyendo los
       guiones, no el Founder. Sirve de respaldo mientras no exista el
       fichero Founder. NO acredita certeza estadística, y cada informe lo
       repite explícitamente.

Los pares en zona gris (MUY_PROXIMO del agente; SIN_INFO o sin responder del
Founder) se excluyen del cómputo: ni el agente ni el Founder tienen ahí una
respuesta única, y contarlos en un sentido u otro inflaría la métrica.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path

import corpus_import
from semantic_fingerprint import SemanticFingerprint

_CORPUS_DIR = Path(__file__).resolve().parent.parent / "corpus"
EVAL_PATH = _CORPUS_DIR / "eval-umbral-candidato.json"
FOUNDER_EVAL_PATH = _CORPUS_DIR / "eval-umbral-founder.json"

# Traduce CUALQUIERA de los dos vocabularios (el del agente y el que usa
# founder_review) a una sola pregunta: ¿este par DEBE bloquearse? None marca
# zona gris — se excluye, nunca se cuenta en ningún sentido.
BLOQUEO_POR_ETIQUETA = {
    # vocabulario del agente
    "EQUIVALENTE": True, "MUY_PROXIMO": None,
    "RELACIONADO_DISTINTO": False, "DISTINTO": False,
    # vocabulario Founder (founder_label_mapped)
    "BLOQUEAR": True, "COEXISTIR": False, "DISTINTA": False, "SIN_INFO": None,
}

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


def _etiqueta_de(par):
    """Un par del fichero Founder trae 'founder_label_mapped'; uno del agente
    trae 'etiqueta'. Sin decisión Founder (SIN_DECISION) se trata como zona
    gris: no hay con qué evaluar ese par todavía."""
    if "founder_label_mapped" in par:
        return par.get("founder_label_mapped") or "SIN_INFO"
    return par.get("etiqueta")


def cargar_pares_etiquetados(registros, path=None):
    """Prefiere el fichero Founder si `path` no se especifica y existe."""
    fuente = "AGENTE"
    p = Path(path) if path else None
    if p is None:
        if FOUNDER_EVAL_PATH.is_file():
            p, fuente = FOUNDER_EVAL_PATH, "FOUNDER"
        else:
            p = EVAL_PATH
    elif p == FOUNDER_EVAL_PATH:
        fuente = "FOUNDER"

    if not p.is_file():
        return [], {"fuente_etiquetas": fuente, "encontrado": False}

    data = json.loads(p.read_text(encoding="utf-8"))
    por_id = {r.content_id: r for r in registros}
    fuera, pares = [], []
    for par in data.get("pares", []):
        a, b = por_id.get(par["a"]), por_id.get(par["b"])
        if a is None or b is None:
            fuera.append(par)
            continue
        etiqueta = _etiqueta_de(par)
        razon = par.get("founder_razon") or par.get("razon", "")
        pares.append((a.fingerprint(), b.fingerprint(), etiqueta, razon))
    meta = {"fuente_etiquetas": fuente, "encontrado": True, "ruta": str(p),
            "estado": data.get("estado"), "aviso": data.get("aviso"),
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
        debe_bloquear = BLOQUEO_POR_ETIQUETA.get(etiqueta)
        if debe_bloquear is None:
            continue                         # zona gris: no se cuenta en ningún sentido
        bloquea = a.equivalente_a(b, umbral=umbral)
        if debe_bloquear:
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
    en_zona_gris = [e for e in etiquetados if BLOQUEO_POR_ETIQUETA.get(e[2]) is None]
    return puntos, meta, {"canonicos": len(canonicos),
                          "etiquetados_computados": len(etiquetados) - len(en_zona_gris),
                          "zona_gris_excluida": len(en_zona_gris)}
