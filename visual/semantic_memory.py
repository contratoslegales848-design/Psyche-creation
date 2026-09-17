"""Memoria semántica con estados y aprendizaje — P0 del Handoff §4 y §5.

`memory.py` guarda una ventana plana de huellas visuales y puntúa riesgo de
repetición. Le faltan las dos cosas que el fundador pide: (a) comparar por
SIGNIFICADO, no por escena y objeto; (b) distinguir PRODUCIR de APROBAR.

Estados ("00 LEER PRIMERO" §7):

    GENERADA → PRESELECCIONADA → APROBADA → PUBLICADA
    DESCARTADA es independiente.

Fuerza de la señal (Handoff §4):

    APROBADA/PUBLICADA  = señal positiva fuerte  → memoria fuerte
    PRESELECCIONADA     = señal positiva          → memoria fuerte, ventana menor
    GENERADA reciente   = memoria corta           → cooldown
    DESCARTADA reciente = evita repetición inmediata, pero NO prohíbe
                          permanentemente una rama del conocimiento

Esa última regla es la que impide que el sistema se encierre. Está
implementada con la ventana de cooldown MÁS CORTA de todas y, además, con un
bloqueo que sólo alcanza al equivalente semántico exacto: la materia, la
familia y el concepto siguen disponibles por otras puertas. Un descarte es
fatiga de un ángulo, no una rama de conocimiento cancelada.

La memoria NO abre gates y no es fuente jurídica: sólo decide si algo ya se
contó, nunca si es cierto.
"""

import json
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path

from memory import normaliza
from semantic_fingerprint import SemanticFingerprint, mas_similar, UMBRAL_EQUIVALENCIA

SEMANTIC_MEMORY_SCHEMA_VERSION = "1.0"

HISTORICA = "HISTORICA"
GENERADA = "GENERADA"
PRESELECCIONADA = "PRESELECCIONADA"
APROBADA = "APROBADA"
PUBLICADA = "PUBLICADA"
DESCARTADA = "DESCARTADA"

ESTADOS = (HISTORICA, GENERADA, PRESELECCIONADA, APROBADA, PUBLICADA, DESCARTADA)

# Ventana de cooldown por estado, en número de registros recientes.
# El descarte tiene la ventana más corta a propósito (ver docstring).
COOLDOWN = {
    # El corpus histórico es el REGISTRO ACUMULADO de lo ya contado, no
    # producción reciente. Con la ventana de GENERADA (40) el motor sólo veía
    # las últimas 40 de 174 piezas y volvía a "descubrir" las otras 134 como
    # nuevas — exactamente el defecto que esta fase venía a cerrar.
    HISTORICA: 100000,
    PUBLICADA: 200,
    APROBADA: 200,
    PRESELECCIONADA: 100,
    GENERADA: 40,
    DESCARTADA: 20,
}
# HISTORICA NO es memoria fuerte: que algo se produjera en el pasado no
# significa que el Founder lo eligiera. Bloquea la repetición, pero no cuenta
# como señal positiva de preferencia (ver `preferencias`).
MEMORIA_FUERTE = (APROBADA, PUBLICADA, PRESELECCIONADA)


class SemanticMemoryError(ValueError):
    pass


@dataclass
class MemoryEntry:
    fingerprint: dict = field(default_factory=dict)
    estado: str = GENERADA
    lote_id: str = ""
    registrado_en: float = 0.0

    def fp(self):
        return SemanticFingerprint.from_dict(self.fingerprint)

    def to_dict(self):
        return asdict(self)


@dataclass
class Veredicto:
    bloquea: bool = False
    motivo: str = ""
    distancia: float = 1.0
    contra: str = ""
    estado_contra: str = ""

    def to_dict(self):
        return asdict(self)


class SemanticMemory:
    """Memoria persistible en JSON. Sin base de datos, igual que memory.py."""

    def __init__(self, entries=(), umbral=UMBRAL_EQUIVALENCIA):
        self._entries = list(entries)     # más reciente primero
        self.umbral = float(umbral)

    def __len__(self):
        return len(self._entries)

    def record(self, fingerprint, estado=GENERADA, lote_id=""):
        if estado not in ESTADOS:
            raise SemanticMemoryError(
                f"estado desconocido: {estado!r}. Conocidos: {list(ESTADOS)}")
        self._entries.insert(0, MemoryEntry(
            fingerprint=fingerprint.to_dict(), estado=estado, lote_id=lote_id,
            registrado_en=time.time()))
        return self._entries[0]

    def entries(self, estado=None):
        return [e for e in self._entries if estado is None or e.estado == estado]

    def promover(self, content_id, estado):
        """Cambia el estado de una huella ya registrada (curaduría posterior).

        Producir no es aprobar: por eso la promoción es un acto separado y
        explícito, nunca un efecto secundario de haber generado la pieza.
        """
        if estado not in ESTADOS:
            raise SemanticMemoryError(f"estado desconocido: {estado!r}")
        tocados = 0
        for e in self._entries:
            if e.fingerprint.get("content_id") == content_id:
                e.estado = estado
                tocados += 1
        if not tocados:
            raise SemanticMemoryError(
                f"no hay huella registrada con content_id={content_id!r}: "
                "no se promueve lo que nunca se generó.")
        return tocados

    # --- la decisión ---
    def evaluar(self, fingerprint):
        """¿Este candidato repite algo que ya vive en la memoria?"""
        if not self._entries:
            return Veredicto(False, "memoria vacía: nada con que comparar.", 1.0)

        peor = Veredicto(False, "ningún registro reciente es semánticamente equivalente.", 1.0)
        for estado in (PUBLICADA, APROBADA, PRESELECCIONADA, HISTORICA,
                       GENERADA, DESCARTADA):
            ventana = [e for e in self._entries if e.estado == estado][:COOLDOWN[estado]]
            if not ventana:
                continue
            _, d = mas_similar(fingerprint, [e.fp() for e in ventana])
            if d is None:
                continue
            if d.valor < self.umbral:
                contra = next((e for e in ventana
                               if fingerprint.distancia_semantica(e.fp()).valor == d.valor), None)
                cid = contra.fingerprint.get("content_id", "?") if contra else "?"
                if estado == DESCARTADA:
                    motivo = (
                        f"equivalente a {cid!r}, descartada hace poco (distancia {d.valor}). "
                        f"Cooldown corto de {COOLDOWN[DESCARTADA]} registros: la materia, la "
                        "familia editorial y el concepto siguen disponibles por otro ángulo — "
                        "sólo se evita repetir este mismo enfoque de inmediato.")
                elif estado == HISTORICA:
                    motivo = (f"equivalente a {cid!r}, que LegalMente YA CONTÓ "
                              f"(corpus histórico, distancia {d.valor}). No es una "
                              "señal de gusto del Founder: es memoria de lo producido.")
                elif estado in MEMORIA_FUERTE:
                    motivo = (f"equivalente a {cid!r}, ya en memoria fuerte como {estado} "
                              f"(distancia {d.valor}). Señal positiva: ya se contó bien.")
                else:
                    motivo = (f"equivalente a {cid!r}, generada recientemente "
                              f"(distancia {d.valor}). Memoria corta.")
                return Veredicto(True, motivo, d.valor, cid, estado)
            if d.valor < peor.distancia:
                peor = Veredicto(False, f"lo más parecido está a distancia {d.valor} "
                                        f"(umbral {self.umbral}).", d.valor)
        return peor

    def evaluar_visual_fuerte(self, fingerprint):
        """¿La dirección visual del candidato repite la puesta en escena de
        una pieza ya en memoria fuerte (APROBADA/PUBLICADA/PRESELECCIONADA)?

        Distinto de `evaluar()`: `evaluar()` mide equivalencia de TEMA
        (`distancia_semantica()`, EJES_SEMANTICOS) — nunca tocó los ejes
        visuales. Este método mide equivalencia de PUESTA EN ESCENA
        (`distancia_visual()`, EJES_VISUALES) y sólo contra memoria fuerte:
        memoria corta/histórica de estilo ya la cubre `visual_fingerprint.py`
        (cooldown de huella reciente del catálogo maestro), que no es una
        señal "positiva" — mezclarla aquí confundiría "ya se generó" con
        "el Founder ya lo aprobó".

        Extensión añadida por la incorporación de la fuente #5 (memoria
        fuerte real, ver `memoria_fuerte.py`) — additiva, no cambia el
        comportamiento de `evaluar()`.
        """
        fuertes = [e for e in self._entries if e.estado in MEMORIA_FUERTE]
        if not fuertes:
            return Veredicto(False, "memoria fuerte vacía: nada con que comparar.", 1.0)

        peor = Veredicto(False, "ninguna pieza de memoria fuerte es visualmente equivalente.", 1.0)
        for e in fuertes:
            d = fingerprint.distancia_visual(e.fp())
            if not d.comparable:
                continue
            if d.valor < self.umbral:
                cid = e.fingerprint.get("content_id", "?")
                motivo = (f"repite arquitectura/escena/objeto de marca de {cid!r}, ya en "
                          f"memoria fuerte como {e.estado} (distancia visual {d.valor}).")
                return Veredicto(True, motivo, d.valor, cid, e.estado)
            if d.valor < peor.distancia:
                peor = Veredicto(False, f"lo más parecido en memoria fuerte está a distancia "
                                        f"visual {d.valor} (umbral {self.umbral}).", d.valor)
        return peor

    # --- aprendizaje desde la curaduría del fundador -----------------------
    def registrar_seleccion(self, seleccionados, descartados, lote_id=""):
        """La selección humana es FEEDBACK, no permiso previo (Handoff §5).

        Se registra después de producir: el sistema ya generó el lote, el
        fundador conserva unas y descarta otras, y eso alimenta la memoria.
        """
        for fp in seleccionados:
            self.record(fp, PRESELECCIONADA, lote_id)
        for fp in descartados:
            self.record(fp, DESCARTADA, lote_id)
        return {"preseleccionadas": len(seleccionados), "descartadas": len(descartados),
                "lote_id": lote_id,
                "selection_rate": round(len(seleccionados) /
                                        max(1, len(seleccionados) + len(descartados)), 4)}

    def preferencias(self):
        """Qué ejes prefiere el fundador, leído de sus decisiones reales.

        Devuelve un SESGO, no un filtro. Se usa como bonificación de desempate
        en la selección: nunca excluye una rama. Si excluyera, el sistema se
        encerraría en lo ya premiado — justo lo contrario del mandato.
        """
        pref = {}
        for eje in ("materia", "familia_editorial", "necesidad", "angulo", "emocion", "rol_lector"):
            acum = {}
            for e in self._entries:
                valor = normaliza(e.fingerprint.get(eje, ""))
                if not valor:
                    continue
                if e.estado in MEMORIA_FUERTE:
                    acum[valor] = acum.get(valor, 0.0) + 1.0
                elif e.estado == DESCARTADA:
                    acum[valor] = acum.get(valor, 0.0) - 0.5
            pref[eje] = acum
        return pref

    # --- persistencia ---
    def save(self, path):
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(
            {"schema_version": SEMANTIC_MEMORY_SCHEMA_VERSION, "umbral": self.umbral,
             "entries": [e.to_dict() for e in self._entries]},
            ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return p

    @classmethod
    def load(cls, path, umbral=UMBRAL_EQUIVALENCIA):
        p = Path(path)
        if not p.is_file():
            return cls(umbral=umbral)
        data = json.loads(p.read_text(encoding="utf-8"))
        if data.get("schema_version") != SEMANTIC_MEMORY_SCHEMA_VERSION:
            # Misma disciplina que memory.py: perder memoria degrada la
            # variedad, pero malinterpretarla corrompe todas las decisiones.
            return cls(umbral=umbral)
        return cls([MemoryEntry(**e) for e in data.get("entries", [])],
                   umbral=data.get("umbral", umbral))
