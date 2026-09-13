"""Enriquecimiento progresivo de concepto_nucleo y pregunta_resuelta — Fase 5.

Es el déficit principal de la memoria histórica: `corpus_import.py` deja
`pregunta_resuelta` en UNKNOWN para las 174 piezas y `concepto_nucleo` como el
slug con guiones cambiados por espacios (confianza MEDIA plana, sin matices).
Este módulo es una segunda pasada ADITIVA — nunca sustituye ni muta
`corpus_import.py` — que intenta mejorar ambos campos con evidencia real.

VOCABULARIO DE CONFIANZA (exacto, pedido por el Founder — deliberadamente
distinto del ALTA/MEDIA/BAJA/NINGUNA de `corpus_import.py`, que clasifica
materia/familia, un eje distinto):

    DECLARADO       — el propio corpus lo declaró explícitamente (nunca ocurre
                       en este corpus: nadie declaró estos campos en 2026-09.
                       El nivel existe para corpus futuros que sí lo declaren).
    INFERIDO_ALTO   — evidencia estructural fuerte (el titular ES la pregunta,
                       o el slug lleva el prefijo editorial que la delimita).
    INFERIDO_MEDIO  — patrón léxico reconocible, reconstruido por plantilla.
    INFERIDO_BAJO   — sin patrón: se deriva del slug en bruto, es la opción
                       más débil que no es "no sé nada".
    UNKNOWN         — sin evidencia. No se inventa.

REGLA CENTRAL DEL FOUNDER: "los niveles bajos NO deben actuar como verdad
fuerte para bloquear". Por eso este módulo expone DOS huellas distintas para
el mismo registro enriquecido:

    fingerprint_completo()     — usa todo lo enriquecido, cualquier confianza.
                                  Para explorar territorio y medir novedad: ahí
                                  más señal ayuda aunque sea incierta, porque
                                  el riesgo de una exploración de más es bajo.
    fingerprint_conservador()  — sólo usa concepto_nucleo/pregunta_resuelta
                                  cuando su confianza es DECLARADO,
                                  INFERIDO_ALTO o INFERIDO_MEDIO. Con
                                  INFERIDO_BAJO o UNKNOWN, el campo viaja vacío
                                  (evidencia ausente, nunca coincidencia
                                  falsa). Para bloquear repetición: ahí una
                                  huella débil que bloquee por error cuesta
                                  contenido legítimo.

No verifica Derecho. No inventa evidencia donde no la hay.
"""

import re
from dataclasses import dataclass, field, asdict

from semantic_fingerprint import SemanticFingerprint

DECLARADO = "DECLARADO"
INFERIDO_ALTO = "INFERIDO_ALTO"
INFERIDO_MEDIO = "INFERIDO_MEDIO"
INFERIDO_BAJO = "INFERIDO_BAJO"
UNKNOWN = "UNKNOWN"

NIVELES = (DECLARADO, INFERIDO_ALTO, INFERIDO_MEDIO, INFERIDO_BAJO, UNKNOWN)
_RANGO = {n: i for i, n in enumerate(reversed(NIVELES))}  # UNKNOWN=0 ... DECLARADO=4

# Confianza mínima para que el campo cuente como evidencia FUERTE (bloqueo).
# Ver docstring del módulo: INFERIDO_BAJO y UNKNOWN no bloquean.
MINIMO_PARA_BLOQUEAR = INFERIDO_MEDIO

# Prefijos editoriales explícitos ya reconocidos por corpus_import. Cuando el
# slug los lleva, el resto del slug delimita el concepto con precisión: es
# evidencia estructural fuerte, no una conjetura.
_PREFIJOS_DELIMITAN_CONCEPTO = (
    "mito", "concepto", "diferencia", "comparacion", "tecnicismo",
    "consejo", "listado", "consecuencia", "pregunta",
)


def _concepto_desde_slug_sin_prefijo(slug):
    partes = slug.split("-")
    if partes and partes[0] in _PREFIJOS_DELIMITAN_CONCEPTO:
        resto = partes[1:]
        return " ".join(resto).strip()
    if partes[:1] == ["linkedin"] and len(partes) > 1 and partes[1] in _PREFIJOS_DELIMITAN_CONCEPTO:
        return " ".join(partes[2:]).strip()
    return ""


# Plantillas de reconstrucción de pregunta por patrón léxico del slug. Cada
# plantilla es una paráfrasis MECÁNICA del propio slug, no una afirmación
# jurídica nueva: reordena palabras que ya estaban, no añade hechos.
_PATRONES_PREGUNTA = (
    (re.compile(r"^diferencia-(.+)$"), lambda m: f"¿en qué se diferencian {m.group(1).replace('-', ' ')}?"),
    (re.compile(r"^comparacion-(.+)$"), lambda m: f"¿cómo se compara {m.group(1).replace('-', ' ')}?"),
    (re.compile(r"^mito-(.+)$"), lambda m: f"¿es verdad que {m.group(1).replace('-', ' ')}?"),
    (re.compile(r"^(?:consejo|listado)-(.+)$"), lambda m: f"¿qué hacer sobre {m.group(1).replace('-', ' ')}?"),
    (re.compile(r"^pasos-(.+)$"), lambda m: f"¿cuáles son los pasos para {m.group(1).replace('-', ' ')}?"),
    (re.compile(r"^pregunta-(.+)$"), lambda m: f"¿{m.group(1).replace('-', ' ')}?"),
)


def _pregunta_desde_slug_narrativo(slug):
    """'el-X-que-Y' -> '¿qué pasa cuando X Y?'. Reformulación mecánica de la
    propia frase, no una inferencia jurídica nueva."""
    m = re.match(r"^(?:el|la|los|las|un|una)-(.+)-que-(.+)$", slug)
    if not m:
        return ""
    sujeto = m.group(1).replace("-", " ")
    predicado = m.group(2).replace("-", " ")
    return f"¿qué pasa cuando {sujeto} {predicado}?"


@dataclass
class RegistroEnriquecido:
    """Envoltorio aditivo: el registro original intacto + los dos campos
    enriquecidos, cada uno con su propia confianza."""

    base: object
    concepto_nucleo_enriquecido: str = ""
    concepto_confianza: str = UNKNOWN
    pregunta_resuelta_enriquecida: str = ""
    pregunta_confianza: str = UNKNOWN
    razon_concepto: str = ""
    razon_pregunta: str = ""

    @property
    def content_id(self):
        return self.base.content_id

    @property
    def guion(self):
        return self.base.guion

    def to_dict(self):
        d = self.base.to_dict()
        d["concepto_nucleo_enriquecido"] = self.concepto_nucleo_enriquecido
        d["concepto_confianza"] = self.concepto_confianza
        d["pregunta_resuelta_enriquecida"] = self.pregunta_resuelta_enriquecida
        d["pregunta_confianza"] = self.pregunta_confianza
        return d

    def fingerprint_completo(self):
        """Toda la señal enriquecida, sin filtrar por confianza. Para
        exploración de territorio y medición de novedad: más señal ayuda
        aunque sea incierta, y el coste de una exploración de más es bajo."""
        fp = self.base.fingerprint()
        return SemanticFingerprint(**{
            **fp.to_dict(),
            "concepto_nucleo": self.concepto_nucleo_enriquecido or fp.concepto_nucleo,
            "pregunta_resuelta": self.pregunta_resuelta_enriquecida or fp.pregunta_resuelta,
        })

    def fingerprint_conservador(self):
        """Sólo cuenta la evidencia enriquecida cuando su confianza alcanza
        INFERIDO_MEDIO o más. Por debajo, el campo viaja vacío: una huella
        débil no puede bloquear contenido legítimo."""
        fp = self.base.fingerprint()
        concepto = (self.concepto_nucleo_enriquecido
                    if _RANGO[self.concepto_confianza] >= _RANGO[MINIMO_PARA_BLOQUEAR]
                    else "")
        pregunta = (self.pregunta_resuelta_enriquecida
                    if _RANGO[self.pregunta_confianza] >= _RANGO[MINIMO_PARA_BLOQUEAR]
                    else "")
        return SemanticFingerprint(**{
            **fp.to_dict(),
            "concepto_nucleo": concepto or fp.concepto_nucleo,
            "pregunta_resuelta": pregunta,
        })


def enriquecer_concepto(registro):
    """(texto, confianza, razón). Nunca inventa: cada nivel exige su propia
    evidencia estructural, no una intuición del agente."""
    slug = (registro.guion or "").lower()

    delimitado = _concepto_desde_slug_sin_prefijo(slug)
    if delimitado:
        return delimitado, INFERIDO_ALTO, (
            f"prefijo editorial {slug.split('-')[0]!r} delimita el resto del slug "
            "como el concepto exacto.")

    titular = (registro.titular or "").strip()
    if titular and len(titular.split()) <= 5 and not titular.endswith("?"):
        # Titular corto sin forma interrogativa: probable frase nominal, un
        # candidato razonable a nombre de concepto, pero no tan seguro como un
        # prefijo explícito.
        return titular.lower(), INFERIDO_MEDIO, (
            "titular corto y no interrogativo: probable frase nominal del concepto.")

    if slug:
        return slug.replace("-", " "), INFERIDO_BAJO, (
            "sin prefijo ni titular útil: se deriva el slug en bruto, la opción más débil.")

    return "", UNKNOWN, "sin slug ni titular: no hay de dónde derivar el concepto."


def enriquecer_pregunta(registro):
    """(texto, confianza, razón)."""
    titular = (registro.titular or "").strip()
    if titular.endswith("?"):
        return titular, INFERIDO_ALTO, "el titular está formulado literalmente como pregunta."

    slug = (registro.guion or "").lower()
    for patron, plantilla in _PATRONES_PREGUNTA:
        m = patron.match(slug)
        if m:
            return plantilla(m), INFERIDO_MEDIO, (
                f"patrón léxico {patron.pattern!r} reconstruye la pregunta por plantilla.")

    narrativa = _pregunta_desde_slug_narrativo(slug)
    if narrativa:
        return narrativa, INFERIDO_BAJO, (
            "forma narrativa 'el-X-que-Y' reformulada mecánicamente como pregunta; "
            "no hay marcador editorial que la respalde.")

    return "", UNKNOWN, "sin patrón reconocible: no se inventa una pregunta."


def enriquecer(registros):
    """Segunda pasada aditiva sobre una lista de RegistroHistorico.

    No muta los registros originales — nunca fue el mandato — y no vuelve a
    tocar corpus_import.py: el enriquecimiento vive aparte precisamente para
    poder mejorarse, probarse o revertirse sin arriesgar la migración base.
    """
    enriquecidos = []
    for r in registros:
        concepto, c_conf, c_razon = enriquecer_concepto(r)
        pregunta, p_conf, p_razon = enriquecer_pregunta(r)
        enriquecidos.append(RegistroEnriquecido(
            base=r, concepto_nucleo_enriquecido=concepto, concepto_confianza=c_conf,
            razon_concepto=c_razon, pregunta_resuelta_enriquecida=pregunta,
            pregunta_confianza=p_conf, razon_pregunta=p_razon))
    return enriquecidos


@dataclass
class ReporteEnriquecimiento:
    total: int = 0
    concepto_por_nivel: dict = field(default_factory=dict)
    pregunta_por_nivel: dict = field(default_factory=dict)

    def to_dict(self):
        return asdict(self)


def reporte(enriquecidos):
    def contar(attr):
        out = {n: 0 for n in NIVELES}
        for e in enriquecidos:
            out[getattr(e, attr)] += 1
        return out
    return ReporteEnriquecimiento(
        total=len(enriquecidos),
        concepto_por_nivel=contar("concepto_confianza"),
        pregunta_por_nivel=contar("pregunta_confianza"))
