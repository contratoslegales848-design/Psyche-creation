"""Política de equivalencia del Founder (decisión 2026-09-14) — PROPUESTA.

Decisión explícita, tras revisar los 18 pares reales:

    "semantic_distance es señal, NO bloqueo autónomo."

    0.28–0.40: ALERTA_DE_PROXIMIDAD → revisar diferencia semántica/editorial/
    visual → NO descartar automáticamente.

    Un bloqueo necesita evidencia fuerte de equivalencia en concepto_nucleo +
    pregunta_resuelta + relacion (o predicado equivalente demostrado).

    threshold_state: PENDIENTE_SET_POSITIVO

Esto es un cambio de fondo: antes, una sola distancia agregada por debajo de
`UMBRAL_EQUIVALENCIA` bastaba para bloquear (`semantic_fingerprint.
equivalente_a`). El Founder pide un criterio de DOS NIVELES — la distancia
agregada nunca decide sola un bloqueo; decide si algo entra en zona de
revisión, y el bloqueo real exige que los TRES campos núcleo coincidan (o
sean casi idénticos) de forma independiente, no sólo que el promedio
ponderado caiga bajo un umbral.

ESTADO: **PROPUESTA, NO ACTIVADA.** `semantic_memory.evaluar()` y los hard
gates de `generator.py` siguen usando `equivalente_a()` (el criterio
anterior) como gate de producción — el mandato es explícito: "PROPONER
cutoff. NO activarlo automáticamente." Este módulo calcula el criterio
nuevo, lo calibra contra evidencia real (18 negativos Founder + positivos
sintéticos) y lo deja listo para activarse cuando el Founder lo decida.
Activar significa: sustituir la llamada a `equivalente_a()` en
`semantic_memory.SemanticMemory.evaluar()` por `nivel_equivalencia()` de
este módulo — un cambio de una línea, deliberadamente no hecho aquí.
"""

from dataclasses import dataclass, field

from memory import normaliza
from semantic_fingerprint import SemanticFingerprint

ALERTA_MINIMO = 0.28
ALERTA_MAXIMO = 0.40

BLOQUEO = "BLOQUEO"
ALERTA_DE_PROXIMIDAD = "ALERTA_DE_PROXIMIDAD"
NO_RELACIONADO = "NO_RELACIONADO"

# Los tres campos núcleo que el Founder exige corroborar. relacion actúa como
# el "legal_relation o predicado equivalente" del mandato: es el campo de
# SemanticFingerprint más cercano a esa noción (la relación jurídica que
# conecta el concepto con su consecuencia).
CAMPOS_CORROBORACION = ("concepto_nucleo", "pregunta_resuelta", "relacion")

# Umbral de similitud POR CAMPO para considerar que corrobora (no exige
# igualdad exacta: mismo criterio de texto libre que ya usa
# semantic_fingerprint para estos campos).
SIMILITUD_CORROBORACION_MINIMA = 0.7


@dataclass
class VerdictoEquivalencia:
    nivel: str = NO_RELACIONADO
    distancia: float = 1.0
    comparable: bool = False
    campos_corroborados: list = field(default_factory=list)
    campos_sin_corroborar: list = field(default_factory=list)
    razon: str = ""

    @property
    def bloquea(self):
        return self.nivel == BLOQUEO

    @property
    def requiere_revision_humana(self):
        return self.nivel == ALERTA_DE_PROXIMIDAD

    def to_dict(self):
        return {"nivel": self.nivel, "distancia": self.distancia,
                "comparable": self.comparable, "bloquea": self.bloquea,
                "requiere_revision_humana": self.requiere_revision_humana,
                "campos_corroborados": list(self.campos_corroborados),
                "campos_sin_corroborar": list(self.campos_sin_corroborar),
                "razon": self.razon}


def _corrobora_campo(a, b, campo):
    from semantic_fingerprint import _similitud, EJES_TEXTO_LIBRE
    va, vb = getattr(a, campo, ""), getattr(b, campo, "")
    s = _similitud(va, vb, campo in EJES_TEXTO_LIBRE)
    return s is not None and s >= SIMILITUD_CORROBORACION_MINIMA


def nivel_equivalencia(a, b, alerta_minimo=ALERTA_MINIMO, alerta_maximo=ALERTA_MAXIMO):
    """Los dos niveles del Founder. La distancia agregada sitúa la zona; la
    corroboración de los 3 campos núcleo decide si de verdad bloquea."""
    d = a.distancia_semantica(b)
    if not d.comparable:
        return VerdictoEquivalencia(NO_RELACIONADO, d.valor, False, [], [],
                                    "sin evidencia comparable: no hay ejes en común.")

    corroborados = [c for c in CAMPOS_CORROBORACION if _corrobora_campo(a, b, c)]
    sin_corroborar = [c for c in CAMPOS_CORROBORACION if c not in corroborados]
    corroboracion_completa = len(corroborados) == len(CAMPOS_CORROBORACION)

    if d.valor < alerta_minimo and corroboracion_completa:
        return VerdictoEquivalencia(
            BLOQUEO, d.valor, True, corroborados, sin_corroborar,
            f"distancia {d.valor} < {alerta_minimo} Y los 3 campos núcleo "
            "(concepto_nucleo, pregunta_resuelta, relacion) corroboran equivalencia.")

    if d.valor < alerta_minimo and not corroboracion_completa:
        return VerdictoEquivalencia(
            ALERTA_DE_PROXIMIDAD, d.valor, True, corroborados, sin_corroborar,
            f"distancia {d.valor} < {alerta_minimo} pero falta corroborar "
            f"{sin_corroborar}: distancia agregada baja NO basta para bloquear "
            "sin evidencia fuerte en los 3 campos núcleo.")

    if alerta_minimo <= d.valor <= alerta_maximo:
        return VerdictoEquivalencia(
            ALERTA_DE_PROXIMIDAD, d.valor, True, corroborados, sin_corroborar,
            f"distancia {d.valor} en zona [{alerta_minimo}, {alerta_maximo}]: "
            "revisar semántica/editorial/visualmente, nunca descartar automáticamente.")

    return VerdictoEquivalencia(
        NO_RELACIONADO, d.valor, True, corroborados, sin_corroborar,
        f"distancia {d.valor} > {alerta_maximo}: sin relación relevante.")
