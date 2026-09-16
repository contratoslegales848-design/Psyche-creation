"""Etiquetas de reporte sobre motores ya existentes — Partes VII y VIII del
mandato "Fase post-implementación" (Founder, 16-sep-2026).

Ninguna de las dos funciones de este módulo construye un motor nuevo: las
dos leen el veredicto de mecanismos que ya existen y calibrados
(`semantic_memory.py`, `editorial_saturation.py`) o campos que un
`TopicCandidate` ya trae (`materia`, `profundidad`, `familia_editorial`) y
los traducen al vocabulario de reporte que el mandato pide. Es la misma
disciplina que el resto de `visual/`: adaptar, no duplicar.
"""

from dataclasses import dataclass

from memory import normaliza

# --- Parte VII: clasificación anti-repetición temática ---------------------

NUEVO = "NUEVO"
VARIANTE_JUSTIFICADA = "VARIANTE JUSTIFICADA"
REPETIDO = "REPETIDO"
SATURADO = "SATURADO"

# Por debajo de este umbral (pero por encima del umbral de equivalencia que
# ya bloquea, `semantic_fingerprint.UMBRAL_EQUIVALENCIA`), dos piezas tocan
# el mismo tema desde un ángulo distinto — el caso que el propio
# `semantic_fingerprint.py` documenta como LEGÍTIMO ("mismo tema + nueva
# función útil no es repetición"), no una copia. Más allá de este umbral,
# no hay evidencia de parecido suficiente para llamarlo variante: es NUEVO.
UMBRAL_VARIANTE_JUSTIFICADA = 0.50


@dataclass
class ClasificacionTematica:
    etiqueta: str
    motivo: str
    distancia_semantica: float = 1.0
    contra: str = ""

    def to_dict(self):
        from dataclasses import asdict
        return asdict(self)


def clasificar_repeticion(candidato, memoria, umbral_variante=UMBRAL_VARIANTE_JUSTIFICADA):
    """NUEVO / VARIANTE JUSTIFICADA / REPETIDO / SATURADO — en ese orden de
    prioridad: un candidato bloqueado por repetición semántica es REPETIDO
    aunque también estuviera saturado (la razón exacta importa para quien
    lee el reporte); SATURADO sólo se evalúa cuando la repetición semántica
    ya lo dejó pasar."""
    import editorial_saturation

    if memoria is None:
        return ClasificacionTematica(
            NUEVO, "sin memoria con qué comparar: no se puede afirmar repetición.", 1.0)

    fp = candidato.fingerprint()
    veredicto = memoria.evaluar(fp)
    if veredicto.bloquea:
        return ClasificacionTematica(REPETIDO, veredicto.motivo, veredicto.distancia,
                                     veredicto.contra)

    saturacion = editorial_saturation.evaluar(
        getattr(candidato, "familia_editorial", ""), getattr(candidato, "necesidad", ""), memoria)
    if saturacion.bloquea:
        return ClasificacionTematica(SATURADO, "; ".join(saturacion.razones), veredicto.distancia)

    if veredicto.distancia < umbral_variante:
        return ClasificacionTematica(
            VARIANTE_JUSTIFICADA,
            f"toca un tema cercano (distancia {veredicto.distancia}) sin ser equivalente "
            f"ni saturado: {veredicto.motivo}",
            veredicto.distancia, veredicto.contra)

    return ClasificacionTematica(NUEVO, veredicto.motivo, veredicto.distancia)


# --- Parte VIII: taxonomía editorial derivada -------------------------------
# No sustituye a `editorial-universe-v1.json` (58 familias, la taxonomía
# REAL del sistema) ni a `materias-seed-v1.json` (26 materias): traduce esos
# dos ejes ya existentes, más `profundidad` (base/media/alta, ya en
# `TopicCandidate`), a las 23 etiquetas de reporte que pide el mandato. El
# mandato mismo autoriza esto explícitamente: "no limitar el sistema a esta
# lista si ya existe una taxonomía más completa".

# Materias con nombre directo en la lista del mandato. Prioridad sobre el
# fallback por profundidad: si la materia ya tiene una etiqueta sustantiva
# clara, esa gana.
MATERIA_A_ETIQUETA = {
    "mercantil": "MERCANTIL", "corporativo_compliance": "COMPLIANCE",
    "civil": "CONTRACTUAL", "inmobiliario": "INMOBILIARIO", "laboral": "LABORAL",
    "penal": "PENAL", "familiar": "FAMILIAR", "administrativo": "ADMINISTRATIVO",
    "fiscal": "FISCAL", "salud_medico_legal": "SALUD / RESPONSABILIDAD PROFESIONAL",
    "digital_datos": "DIGITAL / DATOS / TECNOLOGÍA", "procesal": "PROCESAL",
    "criminalistica_forense": "FORENSE", "historia_del_derecho": "HISTÓRICO",
    "ambiental": "REGULATORIO",
}

# Familias editoriales que señalan FUNCIÓN por encima de materia — una
# pieza de "doctrina" o "historia_del_derecho" (familia, no materia) es
# DOCTRINAL/HISTÓRICO con independencia de qué materia sustantiva toque.
# Prioridad máxima: la función editorial es más específica que la materia.
FAMILIA_A_ETIQUETA = {
    "doctrina": "DOCTRINAL", "historia_del_derecho": "HISTÓRICO",
    "caso_historico": "HISTÓRICO", "jurista": "HISTÓRICO",
    "etapa_procesal": "PROCESAL", "proceso": "PROCESAL",
}

PROFUNDIDAD_A_ETIQUETA_GENERICA = {
    "base": "GENERAL CON SUSTANCIA", "media": "INTERMEDIO", "alta": "ESPECIALIZADO",
}

# Familias que, en profundidad alta, son MUY especializadas de verdad
# (léxico técnico o doctrina densa) — no cualquier pieza de profundidad
# alta merece el nivel máximo, sólo las que ya declaran esa función.
FAMILIAS_MUY_ESPECIALIZADAS = frozenset({
    "lenguaje_juridico_explicado", "etimologia", "doctrina", "pregunta_avanzada",
})



# --- Parte IX: mezcla editorial (informativa, nunca cuota dura) -----------
# El mandato es explícito: "NO conviertas esos números en una cárcel
# matemática". `universe.select_batch()` ya impone las cuotas DURAS reales
# (materia, familia editorial, emoción — ver universe.py); esto sólo
# reporta la proporción por profundidad para que quien lea el lote la vea,
# nunca rechaza ni regenera nada por sí solo.
RANGO_SUGERIDO_POR_10 = {"base": (3, 4), "media": (3, 4), "alta": (2, 3)}


def reportar_mezcla_editorial(candidatos):
    """Conteo real por profundidad + una nota textual si la mezcla se aleja
    del rango sugerido — nunca un veredicto de aprobado/rechazado."""
    n = len(candidatos)
    conteo = {"base": 0, "media": 0, "alta": 0, "otra": 0}
    for c in candidatos:
        p = normaliza(getattr(c, "profundidad", "") or "")
        if p in conteo:
            conteo[p] += 1
        else:
            conteo["otra"] += 1

    escala = n / 10.0
    avisos = []
    for nivel, (lo, hi) in RANGO_SUGERIDO_POR_10.items():
        lo_e, hi_e = round(lo * escala), round(hi * escala)
        real = conteo[nivel]
        if real < lo_e or real > hi_e:
            avisos.append(
                f"profundidad {nivel!r}: {real}/{n} piezas, fuera del rango sugerido "
                f"{lo_e}-{hi_e} para un lote de {n} — informativo, no bloquea.")
    return {"total": n, "conteo_por_profundidad": conteo, "avisos": avisos}


def clasificar_taxonomia(candidato):
    """Devuelve (etiqueta, razon). Determinista: misma entrada, misma
    salida. Nunca inventa una etiqueta para datos ausentes — con materia y
    familia vacías, cae a OTROS."""
    materia = normaliza(getattr(candidato, "materia", "") or "")
    familia = normaliza(getattr(candidato, "familia_editorial", "") or "")
    profundidad = normaliza(getattr(candidato, "profundidad", "") or "")

    for clave, etiqueta in FAMILIA_A_ETIQUETA.items():
        if normaliza(clave) == familia:
            return etiqueta, f"familia editorial {candidato.familia_editorial!r} determina la etiqueta."

    if familia in {normaliza(f) for f in FAMILIAS_MUY_ESPECIALIZADAS} and profundidad == "alta":
        return ("MUY ESPECIALIZADO",
                f"familia {candidato.familia_editorial!r} en profundidad alta: técnica densa.")

    for clave, etiqueta in MATERIA_A_ETIQUETA.items():
        if normaliza(clave) == materia:
            return etiqueta, f"materia {candidato.materia!r} determina la etiqueta."

    if profundidad in PROFUNDIDAD_A_ETIQUETA_GENERICA:
        return (PROFUNDIDAD_A_ETIQUETA_GENERICA[profundidad],
                f"sin materia con etiqueta directa; profundidad {candidato.profundidad!r} "
                "determina el nivel genérico.")

    return "OTROS", "sin materia, familia editorial funcional ni profundidad reconocibles."
