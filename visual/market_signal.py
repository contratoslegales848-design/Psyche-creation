"""Señal de mercado — Partes III-VI del mandato "Fase post-implementación:
prueba real de producción + inteligencia temática" (Founder, 16-sep-2026).

Extiende `vacancy_radar.py` (15-sep-2026), no lo duplica: reutiliza
`VacancyPosting`, `clasificar_vacante`, `PALABRAS_CLAVE_POR_MATERIA` y
`normaliza` tal cual. Lo que faltaba, y esto añade:

1. Un modelo de SEÑAL genérico (`Signal`) — el mandato pide que una vacante
   sea una entre varias fuentes posibles (publicaciones institucionales,
   criterios judiciales, reformas...); `VacancyPosting` es específico de
   vacantes, `Signal` es la envoltura fuente-agnóstica que las demás fuentes
   podrán compartir sin reinventar campos, cuando existan.
2. EXTRACCIÓN GRANULAR (Parte V): el radar existente clasifica a nivel de
   MATERIA (26 valores posibles) — el propio mandato da el ejemplo exacto
   de por qué eso no basta: "abogado corporativo" no debe producir
   "hablemos de derecho corporativo", debe producir "reducción de capital y
   protección de acreedores", "límites materiales de un poder", etc. Este
   módulo añade un segundo vocabulario controlado, más fino que materia,
   para extraer esos conceptos — fail-closed: sin coincidencia literal, no
   hay concepto granular, nunca se inventa uno.
3. `professional_demand` real (Parte VI): un bucket determinista sobre la
   frecuencia real observada — nunca una afirmación de "viral" o
   "tendencia" sin evidencia (Parte VI del mandato lo prohíbe
   explícitamente: "No confundir 'popular' con 'viral'").

Una señal NUNCA es autoridad jurídica (Parte XI del mandato, ya el mismo
principio que `universe.py` aplica a `TopicCandidate`): `verification_status`
nace siempre en `NO_VERIFICADO` y la siguiente acción declarada es
`legalmente-legal-verification`, igual que cualquier candidato.
"""

from dataclasses import dataclass, field
from datetime import date, datetime

from vacancy_radar import PALABRAS_CLAVE_POR_MATERIA, VacancyPosting, clasificar_vacante, normaliza

NO_VERIFICADO = "NO_VERIFICADO"
PROXIMA_ACCION_VERIFICACION = "legalmente-legal-verification"

# --- Parte V: vocabulario granular, más fino que materia ------------------
# Cada entrada es un concepto jurídico ESPECÍFICO (no una materia entera),
# con las palabras clave literales que lo delatan en un título/descripción
# real de vacante. Semilla real, nunca techo — mismo criterio que
# `PALABRAS_CLAVE_POR_MATERIA` de vacancy_radar.py: se amplía con evidencia,
# nunca por intuición. Cubre primero la materia que el propio mandato usa
# como ejemplo (mercantil/corporativo) con los 5 conceptos que cita
# literalmente, y añade el resto de materias con demanda real observada en
# el radar del 15-sep y del 16-sep (mercantil, corporativo_compliance,
# laboral, propiedad_intelectual).
CONCEPTOS_GRANULARES_POR_MATERIA = {
    "mercantil": {
        "reduccion_de_capital_y_proteccion_de_acreedores": (
            "reduccion de capital", "reduccion capital"),
        "formalizacion_de_asambleas": ("asamblea", "asambleas"),
        "limites_materiales_de_un_poder": ("poder", "poderes", "apoderado"),
        "actualizacion_de_libros_corporativos": ("libro corporativo", "libros corporativos",
                                                 "libro societario"),
        "fusiones_y_adquisiciones": ("fusion", "fusiones", "adquisicion", "adquisiciones",
                                     "m&a", "f&a"),
        "constitucion_y_transformacion_de_sociedades": ("constitucion de sociedad",
                                                         "transformacion de sociedad",
                                                         "sofom", "sociedad anonima"),
    },
    "corporativo_compliance": {
        "beneficiario_controlador": ("beneficiario controlador",),
        "prevencion_de_lavado_de_dinero": ("pld", "lavado de dinero", "aml",
                                          "prevencion de lavado"),
        "due_diligence_previo_a_operacion": ("due diligence",),
        "gobierno_corporativo": ("gobierno corporativo",),
    },
    "laboral": {
        "subcontratacion_especializada_repse": ("repse", "outsourcing", "subcontratacion"),
        "terminacion_de_la_relacion_laboral": ("despido", "renuncia", "rescision",
                                              "terminacion laboral"),
    },
    "propiedad_intelectual": {
        "registro_y_defensa_de_marca": ("marca", "marcas"),
        "proteccion_de_patentes": ("patente", "patentes"),
    },
    "digital_datos": {
        "aviso_de_privacidad_y_consentimiento": ("aviso de privacidad", "consentimiento",
                                                  "proteccion de datos"),
        "transferencia_internacional_de_datos": ("transferencia internacional de datos",
                                                  "transferencia de datos"),
    },
    "inmobiliario": {
        "debida_diligencia_inmobiliaria": ("due diligence inmobiliario",
                                           "debida diligencia inmobiliaria"),
        "constitucion_de_gravamenes": ("gravamen", "hipoteca", "fideicomiso"),
    },
}


def extraer_conceptos_granulares(texto, materia, vocabulario=None):
    """Coincidencia literal normalizada, igual criterio fail-closed que
    `vacancy_radar.clasificar_vacante`: sin coincidencia, lista vacía —
    nunca se inventa un concepto para una materia que no lo declara."""
    vocabulario = vocabulario or CONCEPTOS_GRANULARES_POR_MATERIA
    conceptos_materia = vocabulario.get(materia, {})
    t = normaliza(texto)
    encontrados = []
    for concepto, palabras in conceptos_materia.items():
        if any(normaliza(p) in t for p in palabras):
            encontrados.append(concepto)
    return encontrados


# --- Parte IV: modelo de señal genérico ------------------------------------

@dataclass
class Signal:
    """Envoltura fuente-agnóstica. Campos mínimos que pide la Parte IV del
    mandato, adaptados a lo que este repositorio puede poblar HOY con
    evidencia real (nunca con un valor inventado sólo para llenar el
    campo — un campo sin evidencia queda vacío, no se rellena)."""

    source_type: str = "vacante"
    source_reference: str = ""          # URL de la vacante real
    date_detected: str = ""             # fecha de publicación de la fuente, si se declara
    jurisdiction: str = ""              # no se infiere del país del anuncio: solo si la fuente lo declara
    industry: str = ""                  # empresa/sector, cuando el dato existe
    legal_area: str = ""                # = materia (vocabulario ya controlado de vacancy_radar)
    subarea: str = ""                   # = concepto granular (vocabulario de este módulo)
    raw_signal: str = ""                # texto literal capturado, para auditar la clasificación
    normalized_concept: str = ""        # subarea en forma legible, o legal_area si no hay subarea
    frequency: int = 1                  # veces que este concepto/materia aparece en la corrida
    recency: str = "NO_DECLARADA"       # "RECIENTE" | "MODERADA" | "ANTIGUA" | NO_DECLARADA
    risk_dimension: str = ""            # PENDIENTE deliberado — ver módulo docstring
    professional_demand: str = "BAJA"   # BAJA | MEDIA | ALTA — bucket determinista de `frequency`
    public_relevance: str = "PENDIENTE_VERIFICACION"
    editorial_potential: str = "PENDIENTE_VERIFICACION"
    verification_status: str = NO_VERIFICADO
    proxima_accion: str = PROXIMA_ACCION_VERIFICACION

    def to_dict(self):
        from dataclasses import asdict
        return asdict(self)


# Umbrales de demanda profesional. Deterministas, sobre CONTEO REAL de
# apariciones en la corrida — nunca una predicción de tendencia futura
# (Parte VI: "no confundir 'popular' con 'viral'. No afirmar que algo será
# viralizable"). BAJA es el default de `Signal`: sólo se sube con evidencia.
UMBRAL_DEMANDA_MEDIA = 2
UMBRAL_DEMANDA_ALTA = 4


def _demanda_desde_frecuencia(frecuencia):
    if frecuencia >= UMBRAL_DEMANDA_ALTA:
        return "ALTA"
    if frecuencia >= UMBRAL_DEMANDA_MEDIA:
        return "MEDIA"
    return "BAJA"


# Frescura por antigüedad de publicación. Determinista sobre fecha real
# declarada — "NO_DECLARADA" cuando la fuente no trae fecha parseable
# (nunca se asume "reciente" sin evidencia).
DIAS_RECIENTE = 14
DIAS_MODERADA = 60


def _recencia_desde_fecha(fecha_str, hoy=None):
    if not fecha_str:
        return "NO_DECLARADA"
    try:
        publicado = date.fromisoformat(str(fecha_str)[:10])
    except ValueError:
        return "NO_DECLARADA"
    hoy = hoy or date.today()
    dias = (hoy - publicado).days
    if dias < 0:
        return "NO_DECLARADA"
    if dias <= DIAS_RECIENTE:
        return "RECIENTE"
    if dias <= DIAS_MODERADA:
        return "MODERADA"
    return "ANTIGUA"


def senales_desde_vacante(posting, vocabulario_granular=None, hoy=None):
    """Una VacancyPosting real -> 0..N Signal (una por materia×concepto
    granular encontrado; si una materia coincide sin concepto granular
    conocido todavía, una Signal con subarea vacía — la granularidad
    faltante se declara, no se disfraza de materia como si fuera lo mismo
    que pide el mandato)."""
    clasificacion = clasificar_vacante(posting)
    texto = posting.texto_clasificable()
    señales = []
    for materia in clasificacion.materias:
        conceptos = extraer_conceptos_granulares(texto, materia, vocabulario_granular)
        if not conceptos:
            señales.append(Signal(
                source_reference=posting.url, date_detected=posting.publicado,
                industry=posting.empresa, legal_area=materia, subarea="",
                raw_signal=posting.titulo, normalized_concept=materia,
                recency=_recencia_desde_fecha(posting.publicado, hoy)))
            continue
        for concepto in conceptos:
            señales.append(Signal(
                source_reference=posting.url, date_detected=posting.publicado,
                industry=posting.empresa, legal_area=materia, subarea=concepto,
                raw_signal=posting.titulo,
                normalized_concept=concepto.replace("_", " "),
                recency=_recencia_desde_fecha(posting.publicado, hoy)))
    return señales


def procesar_vacantes(postings, vocabulario_granular=None, hoy=None):
    """Corrida completa: todas las señales de un conjunto de vacantes, con
    `frequency`/`professional_demand` calculados sobre el CONJUNTO real
    (no por señal aislada) y agregados por `normalized_concept`."""
    todas = []
    for p in postings:
        todas.extend(senales_desde_vacante(p, vocabulario_granular, hoy))

    conteo = {}
    for s in todas:
        conteo[s.normalized_concept] = conteo.get(s.normalized_concept, 0) + 1

    for s in todas:
        s.frequency = conteo[s.normalized_concept]
        s.professional_demand = _demanda_desde_frecuencia(s.frequency)
    return todas


def agrupar_por_concepto(señales):
    """Una fila por concepto (granular si existe, materia si no), para
    reporte — nunca una fila por señal individual (eso duplicaría el mismo
    concepto tantas veces como vacantes lo mencionen)."""
    grupos = {}
    for s in señales:
        grupos.setdefault(s.normalized_concept, []).append(s)
    filas = []
    for concepto, grupo in grupos.items():
        primero = grupo[0]
        filas.append({
            "normalized_concept": concepto, "legal_area": primero.legal_area,
            "subarea": primero.subarea, "frequency": primero.frequency,
            "professional_demand": primero.professional_demand,
            "ejemplos": [(s.raw_signal, s.industry, s.source_reference) for s in grupo[:5]],
        })
    filas.sort(key=lambda f: (-f["frequency"], f["normalized_concept"]))
    return filas
