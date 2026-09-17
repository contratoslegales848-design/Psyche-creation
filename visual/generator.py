"""Generador multi-factor con hard gates — Fase 7.

El mandato pide al menos nueve factores. Este módulo calcula SEIS con
evidencia real y declara TRES como pendientes — nunca los fabrica:

    legal_support     PENDIENTE. Los candidatos combinatorios nacen
                       NO_VERIFICADO (universe.py); la verificación jurídica
                       real ocurre después, en `legalmente-legal-verification`,
                       sobre una pieza concreta, no sobre un candidato
                       abstracto. Fingir un valor aquí falsificaría el gate
                       más importante del sistema.
    human_interest     PENDIENTE. No hay métricas de interacción (0 entradas
                       en todo el histórico — ver docs/arquitectura). Un
                       proxy léxico sobre `pregunta_resuelta` no serviría:
                       ese campo lo produce una PLANTILLA fija
                       ("¿{ángulo} en {tema} cuando alguien necesita
                       {necesidad}?"), así que el texto no varía en nada que
                       distinga interés real. La Fase 10 (Founder Selection
                       Rate) es el camino honesto hacia esta señal.
    visual_distance    NO DISPONIBLE en esta etapa. Un TopicCandidate no
                       lleva plan visual (escena/cámara/metáfora): eso lo
                       decide `brief.py`/`pipeline.py` más adelante, después
                       de la verificación jurídica. Calcularlo aquí sería
                       inventar una escena que nadie ha diseñado todavía.

Los seis restantes, con evidencia real:

    semantic_novelty     — `semantic_memory.SemanticMemory.evaluar` (repetición
                            de CONTENIDO, corpus histórico incluido).
    editorial_diversity  — contribución del candidato a la variedad editorial
                            DEL LOTE que se está construyendo (no de todo el
                            histórico — eso es `editorial_saturation`).
    territory_coverage   — `territory_explorer.score_candidate().opportunity`.
    utility              — `territory_explorer.coherencia()`: ¿la familia
                            editorial sirve de verdad a esta necesidad?
    emotional_fit        — ¿el perfil emocional se derivó con fundamento, o
                            tuvo que degradarse por falta de consecuencia?
    recent_cooldown       — inverso de `editorial_saturation.evaluar()`.

HARD GATES, no penalización blanda — el mandato es explícito: "una pieza
puede ser jurídicamente nueva y aun así ser rechazada por saturación
editorial":

    1. `semantic_memory` bloquea (repetición de contenido)      -> RECHAZO
    2. `editorial_saturation` en nivel ALTO (función sobreusada) -> RECHAZO
    3. cuota de materia del lote agotada ("00 LEER PRIMERO" §3.A: máximo 2 de
       una misma materia en un lote de 10, escalado a `n`)       -> RECHAZO

Ningún factor blando puede compensar un hard gate: un candidato rechazado
tiene `score_compuesto = 0.0` y no participa en el ranking, por alto que
sea cualquier otro factor.

EXPLOTACIÓN DEL GUSTO DEL FOUNDER (Fase 9): `memoria.preferencias()` acumula
un sesgo — positivo en materia/familia/necesidad/ángulo/emoción/rol_lector de
lo PRESELECCIONADO/APROBADO/PUBLICADO, negativo en lo DESCARTADO — que nunca
excluye nada (es sesgo, no filtro; ver `semantic_memory.py`). Este módulo lo
traduce en un ajuste PEQUEÑO y ACOTADO sobre el score compuesto
(`AJUSTE_AAFINIDAD_MAX`), nunca en la ponderación base: en el primer lote,
antes de cualquier curaduría, `preferencias()` está vacío y el ajuste es
exactamente 0 — el sistema no puede explotar un gusto que todavía no conoce.
El acotamiento es la mitad de la EXPLORACIÓN: un ajuste sin techo encerraría
al motor en lo ya premiado, justo lo que el mandato prohíbe.

SEÑAL DE MERCADO REAL (mandato "Fase post-implementación", 16-sep-2026,
Parte VI): mismo patrón exacto que la afinidad del Founder — un ajuste
PEQUEÑO y ACOTADO (`AJUSTE_SENAL_MERCADO_MAX`), nunca la ponderación base,
y exactamente 0.0 sin evidencia. La evidencia es `market_signal.py`
(vacantes reales clasificadas y agrupadas) — `professional_demand` real
sobre conteo observado, nunca una predicción de "viral" o "tendencia": el
mandato lo prohíbe explícitamente ("no confundir 'popular' con 'viral'").
Sin `señales_mercado` (parámetro opcional en todo este módulo), el
comportamiento es idéntico al de antes de esta fase.
"""

from dataclasses import dataclass, field

import editorial
import editorial_saturation
import pedagogia
import territory_explorer as te
from memory import normaliza

PENDIENTE_VERIFICACION = "PENDIENTE_VERIFICACION"
NO_DISPONIBLE_EN_ESTA_ETAPA = "NO_DISPONIBLE_EN_ESTA_ETAPA"

# Pesos sobre los SEIS factores con evidencia real. Suman 1.0. legal_support,
# human_interest y visual_distance quedan fuera del promedio por diseño: no
# tienen valor numérico que ponderar, y tratarlos como 0 los penalizaría
# como si fueran un defecto en vez de una etapa que aún no ha llegado.
PESOS = {
    "semantic_novelty": 0.30,
    "editorial_diversity": 0.15,
    "territory_coverage": 0.20,
    "utility": 0.15,
    "emotional_fit": 0.10,
    "recent_cooldown": 0.10,
}

# Ejes sobre los que se lee la preferencia acumulada del Founder — mismos
# ejes que registra `semantic_memory.preferencias()`.
EJES_AFINIDAD = ("materia", "familia_editorial", "necesidad", "angulo", "emocion", "rol_lector")
AJUSTE_AFINIDAD_MAX = 0.12
AJUSTE_AFINIDAD_ESCALA = 0.03

# Señal de mercado real (Parte VI, 16-sep-2026): ajuste acotado por
# demanda profesional observada (vacantes reales), a nivel de MATERIA —
# `market_signal.py` no siempre resuelve un concepto más fino que eso (el
# título de una vacante real casi nunca lo declara), y este ajuste no finge
# una precisión que la fuente no tiene.
AJUSTE_SENAL_MERCADO_MAX = 0.08
PESO_DEMANDA = {"ALTA": 1.0, "MEDIA": 0.5, "BAJA": 0.0}


@dataclass
class CandidateScore:
    candidate_id: str = ""
    hard_gates_pasados: bool = True
    motivo_bloqueo: str = ""
    legal_support: str = PENDIENTE_VERIFICACION
    semantic_novelty: float = 0.0
    editorial_diversity: float = 0.0
    territory_coverage: float = 0.0
    human_interest: str = PENDIENTE_VERIFICACION
    utility: float = 0.0
    emotional_fit: float = 0.0
    visual_distance: str = NO_DISPONIBLE_EN_ESTA_ETAPA
    recent_cooldown: float = 0.0
    ajuste_afinidad_founder: float = 0.0
    ajuste_senal_mercado: float = 0.0
    ajuste_balance_pedagogico: float = 0.0
    score_compuesto: float = 0.0
    explicacion: list = field(default_factory=list)

    def to_dict(self):
        return {"candidate_id": self.candidate_id,
                "hard_gates_pasados": self.hard_gates_pasados,
                "motivo_bloqueo": self.motivo_bloqueo,
                "legal_support": self.legal_support,
                "semantic_novelty": self.semantic_novelty,
                "editorial_diversity": self.editorial_diversity,
                "territory_coverage": self.territory_coverage,
                "human_interest": self.human_interest,
                "utility": self.utility, "emotional_fit": self.emotional_fit,
                "visual_distance": self.visual_distance,
                "recent_cooldown": self.recent_cooldown,
                "ajuste_afinidad_founder": self.ajuste_afinidad_founder,
                "ajuste_senal_mercado": self.ajuste_senal_mercado,
                "score_compuesto": self.score_compuesto,
                "explicacion": list(self.explicacion)}


def _diversidad_editorial_de_lote(candidato, lote_en_progreso):
    """1.0 si la familia editorial de `candidato` no aparece todavía en el
    lote que se está construyendo; decae si se repite. Es intra-lote — el
    eje que `universe.select_batch` ya impone como cuota dura de "no repetir
    familia"; aquí se expone como SCORE continuo para poder rankear, no sólo
    admitir/rechazar."""
    if not lote_en_progreso:
        return 1.0, "primer candidato del lote: diversidad máxima por definición."
    fam = normaliza(getattr(candidato, "familia_editorial", ""))
    usos = sum(1 for c in lote_en_progreso
              if normaliza(getattr(c, "familia_editorial", "")) == fam)
    if usos == 0:
        return 1.0, "familia editorial aún no usada en este lote."
    valor = max(0.0, 1.0 - 0.5 * usos)
    return valor, f"familia editorial ya usada {usos} vez/veces en este mismo lote."


def _ajuste_emocional(candidato):
    """¿El perfil emocional tiene fundamento, o tuvo que degradarse?
    (ver emotion.py: intensidades altas sin consecuencia declarada se
    degradan — eso es correcto, pero un perfil degradado encaja peor que
    uno derivado sin fricción)."""
    perfil = getattr(candidato, "perfil_emocional", None) or {}
    emocion = perfil.get("emocion", "")
    razones = perfil.get("razones", [])
    if not emocion:
        return 0.0, "sin emoción derivable: necesidad y familia no bastaron."
    if any("degradado" in r or "no se fabrica alarma" in r for r in razones):
        return 0.6, f"emoción {emocion!r} derivada, pero tuvo que degradarse "\
                    "por falta de consecuencia declarada."
    return 1.0, f"emoción {emocion!r} derivada sin fricción de necesidad+familia."


def ajuste_afinidad_founder(candidato, memoria, memoria_fuerte=None):
    """Traduce `memoria.preferencias()` en un empujón pequeño y acotado.

    Suma el peso acumulado (positivo = elegido antes, negativo = descartado
    antes) en los ejes del candidato, lo escala y lo recorta a
    [-AJUSTE_AFINIDAD_MAX, +AJUSTE_AFINIDAD_MAX]. Vacío -> 0.0 exacto: el
    primer lote, antes de cualquier curaduría, no tiene nada que explotar.

    `memoria_fuerte` (Mandato Maestro §6, 17-sep-2026 — fuente #5 real del
    Contrato v4, ver `memoria_fuerte.py`) es OPCIONAL y, si se da, suma su
    propia `preferencias()` a la misma acumulación ANTES de recortar: la
    selección temática debe poder aprender de lo que el Founder ya aprobó/
    publicó de verdad, no sólo de la curaduría simulada de esta corrida —
    "aprender ≠ copiar" (mandato): el recorte sigue siendo el mismo
    `AJUSTE_AFINIDAD_MAX` de siempre, nunca se amplía el techo de
    influencia por tener dos fuentes en vez de una.
    """
    if memoria is None and memoria_fuerte is None:
        return 0.0, "sin memoria: no hay preferencia que explotar."
    acumulado, detalle = 0.0, []
    for memo, etiqueta in ((memoria, "corrida"), (memoria_fuerte, "memoria fuerte real")):
        if memo is None:
            continue
        pref = memo.preferencias()
        for eje in EJES_AFINIDAD:
            valor = normaliza(getattr(candidato, eje, "") or "")
            peso = pref.get(eje, {}).get(valor, 0.0) if valor else 0.0
            if peso:
                acumulado += peso
                detalle.append(f"{eje}={valor!r} pesa {peso:+.2f} en preferencias de {etiqueta}.")
    ajuste = max(-AJUSTE_AFINIDAD_MAX, min(AJUSTE_AFINIDAD_MAX, acumulado * AJUSTE_AFINIDAD_ESCALA))
    razon = "; ".join(detalle) if detalle else "sin señal previa en los ejes de este candidato."
    return round(ajuste, 4), razon


def ajuste_senal_mercado(candidato, señales_mercado):
    """Traduce la demanda profesional real (`market_signal.agrupar_por_concepto`)
    en un ajuste pequeño y acotado, igual patrón que `ajuste_afinidad_founder`.

    Empareja por MATERIA (`legal_area`), no por concepto granular: la
    mayoría de señales reales observadas hoy sólo resuelven a ese nivel
    (ver `market_signal.py`), y emparejar por un concepto más fino que el
    dato real sostiene sería fabricar precisión. Sin señales -> 0.0 exacto.
    """
    if not señales_mercado:
        return 0.0, "sin señales de mercado para esta corrida."
    mat = normaliza(getattr(candidato, "materia", "") or "")
    fila = next((f for f in señales_mercado if normaliza(f.get("legal_area", "")) == mat), None)
    if fila is None:
        return 0.0, f"ninguna señal de mercado reciente coincide con la materia {candidato.materia!r}."
    peso = PESO_DEMANDA.get(fila.get("professional_demand", ""), 0.0)
    ajuste = round(AJUSTE_SENAL_MERCADO_MAX * peso, 4)
    razon = (f"demanda profesional {fila.get('professional_demand')} en materia "
            f"{candidato.materia!r} ({fila.get('frequency')} señal(es) real(es) de mercado): "
            f"ajuste +{ajuste}.")
    return ajuste, razon


def _cuota_materia(materia, n, materias):
    base = materias.get(materia, {}).get("cuota_max_por_lote_10", 2)
    return max(1, round(base * n / 10.0))


def puntuar_candidato(candidato, memoria, mapa_territorio, universo=None,
                      lote_en_progreso=(), materias=None, n_lote=10,
                      señales_mercado=None, objetivo_conocimiento=pedagogia.OBJETIVO_CONOCIMIENTO_DEFAULT,
                      memoria_fuerte=None):
    """Puntúa un candidato. Aplica los hard gates ANTES de calcular el resto:
    un candidato rechazado no necesita un ranking, necesita un motivo."""
    import universe as uni
    universo = universo or editorial.EditorialUniverse.load()
    if materias is None:
        _, materias = uni.cargar_materias()
    explicacion = []

    usos_materia = sum(1 for c in lote_en_progreso
                       if normaliza(c.materia) == normaliza(candidato.materia))
    if usos_materia >= _cuota_materia(candidato.materia, n_lote, materias):
        return CandidateScore(
            candidate_id=candidato.candidate_id, hard_gates_pasados=False,
            motivo_bloqueo=(f"CUOTA DE MATERIA: {candidato.materia!r} ya alcanzó su "
                            f"tope de {_cuota_materia(candidato.materia, n_lote, materias)} "
                            f"para un lote de {n_lote} (00 LEER PRIMERO §3.A)."),
            score_compuesto=0.0)

    fp = candidato.fingerprint()
    veredicto = memoria.evaluar(fp) if memoria is not None else None
    saturacion = (editorial_saturation.evaluar(candidato.familia_editorial,
                                               candidato.necesidad, memoria)
                 if memoria is not None else None)

    if veredicto is not None and veredicto.bloquea:
        return CandidateScore(candidate_id=candidato.candidate_id,
                              hard_gates_pasados=False,
                              motivo_bloqueo=f"REPETICIÓN SEMÁNTICA: {veredicto.motivo}",
                              score_compuesto=0.0, explicacion=[veredicto.motivo])
    if saturacion is not None and saturacion.bloquea:
        return CandidateScore(candidate_id=candidato.candidate_id,
                              hard_gates_pasados=False,
                              motivo_bloqueo=f"SATURACIÓN EDITORIAL: {'; '.join(saturacion.razones)}",
                              score_compuesto=0.0, explicacion=list(saturacion.razones))

    semantic_novelty = round(veredicto.distancia, 4) if veredicto is not None else 1.0
    explicacion.append(f"novedad semántica: {semantic_novelty} "
                       f"({'sin memoria con qué comparar' if veredicto is None else veredicto.motivo}).")

    diversidad, razon_div = _diversidad_editorial_de_lote(candidato, lote_en_progreso)
    explicacion.append(razon_div)

    territorio = te.score_candidate(candidato, mapa_territorio, universo)
    explicacion.extend(territorio.explicacion)

    valor_utilidad, razon_utilidad = te.coherencia(
        candidato.familia_editorial, candidato.necesidad,
        getattr(candidato, "rol_lector", ""), universo)
    explicacion.append(razon_utilidad)

    emocional, razon_emo = _ajuste_emocional(candidato)
    explicacion.append(razon_emo)

    cooldown = 1.0 - (saturacion.score / 100.0) if saturacion is not None else 1.0
    if saturacion is not None:
        explicacion.extend(saturacion.razones)

    factores = {
        "semantic_novelty": semantic_novelty, "editorial_diversity": diversidad,
        "territory_coverage": territorio.opportunity, "utility": valor_utilidad,
        "emotional_fit": emocional, "recent_cooldown": cooldown,
    }
    score_base = sum(PESOS[k] * v for k, v in factores.items())

    afinidad, razon_afinidad = ajuste_afinidad_founder(candidato, memoria, memoria_fuerte=memoria_fuerte)
    explicacion.append(f"afinidad Founder (explotación acotada): {afinidad:+.4f} — {razon_afinidad}")

    senal_mercado, razon_senal = ajuste_senal_mercado(candidato, señales_mercado)
    explicacion.append(f"señal de mercado (acotada): {senal_mercado:+.4f} — {razon_senal}")

    balance_pedagogico, razon_pedagogica = pedagogia.ajuste_balance_pedagogico(
        candidato, lote_en_progreso, objetivo_conocimiento=objetivo_conocimiento)
    explicacion.append(f"balance pedagógico (acotado, no cuota): {balance_pedagogico:+.4f} — "
                       f"{razon_pedagogica}")

    score_compuesto = round(max(0.0, min(
        1.0, score_base + afinidad + senal_mercado + balance_pedagogico)), 4)

    return CandidateScore(
        candidate_id=candidato.candidate_id, hard_gates_pasados=True,
        semantic_novelty=semantic_novelty, editorial_diversity=diversidad,
        territory_coverage=territorio.opportunity, utility=valor_utilidad,
        emotional_fit=emocional, recent_cooldown=cooldown,
        ajuste_afinidad_founder=afinidad, ajuste_senal_mercado=senal_mercado,
        ajuste_balance_pedagogico=balance_pedagogico,
        score_compuesto=score_compuesto, explicacion=explicacion)


def seleccionar_lote(candidatos, memoria, mapa_territorio, universo=None, n=10,
                     materias=None, señales_mercado=None,
                     objetivo_conocimiento=pedagogia.OBJETIVO_CONOCIMIENTO_DEFAULT,
                     memoria_fuerte=None):
    """Selecciona iterativamente: puntúa contra el lote parcial (para que
    `editorial_diversity` y `ajuste_balance_pedagogico` reaccionen a lo ya
    elegido), toma el mejor superviviente de los hard gates, repite. Nunca
    rellena con un candidato rechazado aunque falten piezas para llegar a
    `n`.

    `objetivo_conocimiento` (mandato Maestro §3, 17-sep-2026): proporción
    orientativa de candidatos CONOCIMIENTO_JURIDICO vs SITUACION_NARRATIVA
    (`pedagogia.py`) — 0.70 por defecto, nunca una cuota dura: pásese
    `None` para desactivar el ajuste, o cualquier otro valor por lote.

    `memoria_fuerte` (mandato Maestro §6, 17-sep-2026 — fuente #5 real,
    `memoria_fuerte.py`) es opcional: si se da, `ajuste_afinidad_founder()`
    también aprende de ella para la selección temática, con el mismo techo
    acotado de siempre — ver ese docstring.
    """
    import universe as uni
    universo = universo or editorial.EditorialUniverse.load()
    if materias is None:
        _, materias = uni.cargar_materias()
    restantes = list(candidatos)
    seleccion, puntuaciones, rechazados = [], [], []

    while len(seleccion) < n and restantes:
        mejor, mejor_score = None, None
        for c in restantes:
            s = puntuar_candidato(c, memoria, mapa_territorio, universo, seleccion,
                                  materias=materias, n_lote=n, señales_mercado=señales_mercado,
                                  objetivo_conocimiento=objetivo_conocimiento,
                                  memoria_fuerte=memoria_fuerte)
            if not s.hard_gates_pasados:
                rechazados.append((c.candidate_id, s.motivo_bloqueo))
                continue
            # Desempate por afinidad Founder + señal de mercado + balance
            # pedagógico. En territorio muy virgen (la fase inicial real:
            # pocas celdas materia×familia tocadas) es normal que muchos
            # candidatos empaten en score_compuesto=1.0 — novelty,
            # territorio y utilidad ya tocan el techo por sí solos.
            # Comparar sólo `score_compuesto` (recortado a [0,1] para que
            # sea legible) dejaría los tres ajustes invisibles justo cuando
            # más importan. `clave` usa el valor SIN recortar como
            # desempate, nunca como criterio principal.
            clave = (s.score_compuesto,
                    s.score_compuesto + s.ajuste_afinidad_founder + s.ajuste_senal_mercado
                    + s.ajuste_balance_pedagogico)
            mejor_clave = ((mejor_score.score_compuesto,
                           mejor_score.score_compuesto + mejor_score.ajuste_afinidad_founder
                           + mejor_score.ajuste_senal_mercado
                           + mejor_score.ajuste_balance_pedagogico)
                          if mejor_score is not None else None)
            if mejor_clave is None or clave > mejor_clave:
                mejor, mejor_score = c, s
        if mejor is None:
            break
        seleccion.append(mejor)
        puntuaciones.append(mejor_score)
        restantes.remove(mejor)
        restantes = [c for c in restantes
                    if c.candidate_id not in {r[0] for r in rechazados}]

    return seleccion, puntuaciones, rechazados
