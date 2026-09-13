"""Carriles de publicación — P1 del Handoff §9.

"LinkedIn forma parte del mismo organismo pero conserva carriles propios."

Tres espacios, UN SOLO cerebro jurídico, memorias editoriales PARCIALMENTE
independientes:

    LEGALMENTE_GENERAL   — exploración amplia, 9:16, máx 1 de 10 en digital.
    LINKEDIN_LEGALMENTE  — profesional/institucional, 4:5, familias de valor
                           profesional. "No hacerlo visualmente aburrido":
                           la cuota de rotación visual NO se relaja aquí.
    LINKEDIN_FOUNDER     — voz profesional humana de Raymundo.

"Parcialmente independientes" está implementado literalmente: cada carril
tiene su propia memoria de repetición (que un tema salga en LinkedIn no lo
quema para el carril general), pero todos comparten la misma verificación
jurídica y el mismo universo editorial. No hay un segundo cerebro.

REGLA FAIL-CLOSED DEL CARRIL FOUNDER: "no inventar cargos, casos, resultados
ni experiencia" (Handoff §9.B). Aquí eso no es una advertencia en un
documento: `validar_candidato` RECHAZA cualquier candidato del carril Founder
que no traiga un hecho profesional verificable declarado y atribuido. Sin
hecho, no hay pieza. El sistema no puede inventar una trayectoria porque no
se le permite producir sin una.
"""

from dataclasses import dataclass, field

from memory import normaliza

LANE_SCHEMA_VERSION = "1.0"

LEGALMENTE_GENERAL = "LEGALMENTE_GENERAL"
LINKEDIN_LEGALMENTE = "LINKEDIN_LEGALMENTE"
LINKEDIN_FOUNDER = "LINKEDIN_FOUNDER"

CARRILES = (LEGALMENTE_GENERAL, LINKEDIN_LEGALMENTE, LINKEDIN_FOUNDER)

# Familias de valor profesional para el carril institucional (Handoff §9.A:
# "procesos, contratos, corporativo, inmobiliario, laboral, penal aplicado,
# compliance, riesgo, evidencia, herramientas").
FAMILIAS_LINKEDIN_LEGALMENTE = {
    "proceso", "etapa_procesal", "prueba", "carga_de_la_prueba", "evidencia_digital",
    "contrato_bajo_lupa", "clausula_bajo_lupa", "documento_clave", "requisito",
    "cumplimiento_compliance", "riesgo", "responsabilidad", "obligacion",
    "herramienta_practica", "checklist", "negociacion", "conciliacion_mediacion",
    "actualizacion_normativa", "interpretacion", "comparacion_sistemas",
    "excepcion", "plazo_prescripcion", "senal_de_alerta", "prevencion",
    "autoridad_competente", "incumplimiento", "doctrina", "pregunta_avanzada",
}

MATERIAS_LINKEDIN_LEGALMENTE = {
    "corporativo_compliance", "mercantil", "laboral", "inmobiliario", "procesal",
    "penal", "civil", "fiscal", "administrativo", "digital_datos",
    "propiedad_intelectual", "internacional_privado", "notarial_registral",
    "seguridad_social", "consumo", "ambiental",
}


class LaneError(ValueError):
    pass


@dataclass
class LaneConfig:
    nombre: str
    formato_visual: str
    rol_lector_preferente: str
    familias_permitidas: frozenset = frozenset()
    materias_permitidas: frozenset = frozenset()
    exige_hecho_verificable: bool = False
    nota: str = ""

    def admite_familia(self, familia):
        return not self.familias_permitidas or familia in self.familias_permitidas

    def admite_materia(self, materia):
        return not self.materias_permitidas or materia in self.materias_permitidas


CONFIG = {
    LEGALMENTE_GENERAL: LaneConfig(
        nombre=LEGALMENTE_GENERAL, formato_visual="9:16", rol_lector_preferente="persona",
        nota="Exploración amplia y aleatoria controlada. Sin restricción de familia: "
             "el universo entero está disponible."),
    LINKEDIN_LEGALMENTE: LaneConfig(
        nombre=LINKEDIN_LEGALMENTE, formato_visual="4:5", rol_lector_preferente="profesional",
        familias_permitidas=frozenset(FAMILIAS_LINKEDIN_LEGALMENTE),
        materias_permitidas=frozenset(MATERIAS_LINKEDIN_LEGALMENTE),
        nota="Profesional e institucional. La restricción es de FAMILIA y MATERIA, "
             "nunca de variedad visual: 'no hacerlo visualmente aburrido'."),
    LINKEDIN_FOUNDER: LaneConfig(
        nombre=LINKEDIN_FOUNDER, formato_visual="4:5", rol_lector_preferente="profesional",
        exige_hecho_verificable=True,
        nota="Criterio profesional humano. Sólo hechos y experiencia verificables: "
             "sin ProfileFact atribuido, el candidato se bloquea."),
}


@dataclass
class ProfileFact:
    """Hecho profesional verificable del fundador. No lo genera el sistema."""

    hecho: str
    fuente: str = ""          # dónde consta (perfil público, documento, registro)
    verificado_por: str = ""  # persona identificada que lo confirmó

    def valido(self):
        return all(str(x or "").strip() for x in (self.hecho, self.fuente, self.verificado_por))


@dataclass
class LaneVerdict:
    admitido: bool = False
    carril: str = ""
    motivos: list = field(default_factory=list)

    def to_dict(self):
        return {"admitido": self.admitido, "carril": self.carril,
                "motivos": list(self.motivos)}


def get(carril):
    cfg = CONFIG.get(carril)
    if cfg is None:
        raise LaneError(f"carril desconocido: {carril!r}. Conocidos: {list(CARRILES)}")
    return cfg


def validar_candidato(candidato, carril, profile_fact=None):
    """¿Puede este candidato salir por este carril?"""
    cfg = get(carril)
    motivos = []

    if not cfg.admite_familia(candidato.familia_editorial):
        motivos.append(
            f"familia editorial {candidato.familia_editorial!r} fuera del carril "
            f"{carril}: no aporta valor profesional institucional.")
    if not cfg.admite_materia(candidato.materia):
        motivos.append(f"materia {candidato.materia!r} fuera del carril {carril}.")

    if cfg.exige_hecho_verificable:
        if profile_fact is None:
            motivos.append(
                "carril Founder sin ProfileFact: no se publica experiencia que nadie "
                "declaró. El sistema NO inventa cargos, casos ni resultados.")
        elif not profile_fact.valido():
            faltan = [c for c in ("hecho", "fuente", "verificado_por")
                      if not str(getattr(profile_fact, c, "") or "").strip()]
            motivos.append(
                f"ProfileFact incompleto (falta: {faltan}). Un hecho sin fuente ni "
                "persona que lo verifique no es experiencia verificable.")

    return LaneVerdict(not motivos, carril, motivos or ["admitido en el carril."])


class LaneMemories:
    """Una memoria semántica por carril. Independientes por diseño.

    Que un tema salga en LinkedIn NO debe quemarlo para el carril general: son
    públicos distintos, profundidades distintas y funciones editoriales
    distintas. Comparten el cerebro jurídico, no la fatiga editorial.
    """

    def __init__(self, fabrica=None):
        from semantic_memory import SemanticMemory
        fabrica = fabrica or SemanticMemory
        self._memorias = {c: fabrica() for c in CARRILES}

    def __getitem__(self, carril):
        get(carril)
        return self._memorias[carril]

    def carriles(self):
        return list(CARRILES)

    def resumen(self):
        return {c: len(m) for c, m in self._memorias.items()}
