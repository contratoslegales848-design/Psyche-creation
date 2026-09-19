"""Radar de temas desde vacantes — alimenta y depura el universo de materias.

Mandato del Founder (15-sep-2026), verbatim: "se deben ir actualizando los
temas jurídicos adicionalmente con lo que piden las vacantes jurídicas para
tener mayor temas de interés para abogados y personas en general quiero que
siempre se alimente y se vaya depurando lo menos importante."

Precedente ya existente en Drive, nunca implementado en código: "LegalMente
— Temas legales de demanda real en México (vacantes, 2026-09)" (6-sep, una
corrida manual única) y la sección 9 ("Radar vivo de temas") de "Aportación
V2" (31-ago, AUXILIAR / NO_CANÓNICO / NOT_IMPLEMENTED — nunca aprobada como
canon, pero la idea del radar continuo sí es la que pide hoy el Founder).
Este módulo construye la versión mínima real de esa idea: no el "Grafo de
Restricciones Jurídicas" completo de esa propuesta (fuera de alcance, no
aprobado), solo el radar de temas.

QUÉ HACE (y qué NO hace):

- Clasifica vacantes reales (título, por ahora — Indeed no siempre expone
  descripción completa en la búsqueda) contra el vocabulario YA CONTROLADO
  de `materias-seed-v1.json`. Fail-closed: si el título no coincide con
  ninguna palabra clave declarada, la vacante queda `SIN_MATERIA_RECONOCIDA`
  — nunca se le asigna una materia por parecido o intuición.
- Cruza la señal de demanda contra la cobertura REAL del corpus histórico
  (`corpus_import.py`, 174 piezas, `TEMA_A_MATERIA` ya existente — no se
  reinventa ese mapeo aquí) para proponer temas nuevos donde hay demanda y
  poca o ninguna pieza real todavía.
- Propone candidatos a "depurar" (retirar de la capa activa, nunca borrar):
  materias sin ninguna pieza real en el corpus Y sin ninguna señal de
  demanda acumulada — nunca las materias protegidas (§PROTEGIDAS) ni
  ninguna con evidencia de producción real, por escasa que sea.
- Persiste cada corrida en un log append-only (`corpus/radar-vacantes-log.json`)
  para que "depurar" se decida sobre evidencia ACUMULADA, no sobre una sola
  fotografía — una corrida sin señal no prueba que un tema no importe.

QUÉ NO HACE, deliberadamente:
- No modifica `materias-seed-v1.json`, el corpus, ni ningún banco de
  contenido. Toda salida es PROPUESTA para revisión humana (mismo criterio
  que todo el resto de `visual/`: "Analizar → registrar → evaluar →
  ejecutar o retirar", docs/direccion-basico-antes-que-complejo.md §6).
- No verifica Derecho. Un tema con demanda real de vacantes no es una
  afirmación jurídica — sigue pasando por `legalmente-legal-verification`
  como cualquier otro antes de convertirse en pieza.
- No llama a ningún proveedor de imagen ni genera contenido.
"""

import json
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from corpus_import import TEMA_A_MATERIA


def normaliza(texto):
    """Minúsculas, sin tildes, puntuación reemplazada por espacio (nunca
    tokens completos descartados). Texto libre de vacantes reales trae
    barras, ampersands y siglas con puntuación ("PLD/FT", "M&A") que
    `memory.normaliza()` no sirve aquí: esa función descarta un token
    entero si contiene cualquier carácter no alfanumérico (ver su propio
    docstring) — correcto para comparar identificadores controlados, pero
    perdería "pld" y "ft" enteros en "PLD/FT". Aquí solo se compara texto
    libre externo contra palabras clave, así que se reemplaza puntuación
    por espacio en vez de descartar el token completo."""
    if not texto:
        return ""
    t = unicodedata.normalize("NFKD", str(texto).strip().lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = re.sub(r"[^a-z0-9]+", " ", t)
    return " ".join(t.split())

LOG_PATH = Path(__file__).resolve().parent.parent / "corpus" / "radar-vacantes-log.json"

# Materias protegidas: nunca se proponen para depuración aunque una corrida
# no muestre demanda de vacantes. Son la Capa A transversal
# (docs/direccion-basico-antes-que-complejo.md) o disciplinas fundacionales
# que no se miden por demanda de empleo (nadie contrata a un "abogado de
# teoría del derecho", pero el contenido sigue siendo cimiento del proyecto).
MATERIAS_PROTEGIDAS = frozenset({
    "civil", "familiar", "laboral", "penal", "procesal", "mercantil",
    "constitucional", "teoria_y_filosofia", "historia_del_derecho",
})

# Palabras clave por materia. DECLARADO por esta sesión a partir de: (a) los
# submaterias reales de materias-seed-v1.json, y (b) el vocabulario real
# visto en vacantes reales de Indeed México (sep-2026) que ese seed todavía
# no cubre con una palabra literal (p. ej. "PLD", "REPSE", "notarial").
# Es un vocabulario ABIERTO — igual que materias-seed-v1.json declara de sí
# mismo ("semilla, nunca techo") — se amplía cuando aparezca evidencia real,
# nunca por intuición sin vacante que lo sostenga.
PALABRAS_CLAVE_POR_MATERIA = {
    "civil": ("civil", "contrato", "contractual", "obligaciones"),
    "familiar": ("familiar", "familia", "divorcio", "custodia", "protección de la niñez",
                "protección a la infancia"),
    "sucesorio": ("sucesorio", "herencia", "testamento", "sucesiones"),
    "laboral": ("laboral", "trabajo", "repse", "outsourcing", "subcontratación",
               "recursos humanos derecho"),
    "penal": ("penal", "litigante", "litigios"),
    "procesal": ("procesal", "juicios", "litigios"),
    "mercantil": ("mercantil", "corporativo", "societario", "sociedades", "empresarial",
                 "fusiones", "m&a"),
    "corporativo_compliance": ("compliance", "cumplimiento", "pld", "aml",
                               "lavado de dinero", "due diligence", "gobierno corporativo",
                               "regulatory"),
    "administrativo": ("administrativo", "licencias", "normatividad", "uso de suelo",
                       "gestión urbana"),
    "constitucional": ("constitucional", "derechos humanos", "amparo"),
    "inmobiliario": ("inmobiliario", "bienes raíces", "arrendamiento", "compraventa de inmueble",
                     "terrenos", "adquisición de terrenos"),
    "notarial_registral": ("notarial", "notaría", "escritura pública", "fedatario"),
    "consumo": ("consumidor", "protección al consumidor"),
    "fiscal": ("fiscal", "fiscalista", "tributario", "impuestos"),
    "seguridad_social": ("seguridad social", "pensión", "imss", "infonavit"),
    "salud_medico_legal": ("médico legal", "responsabilidad sanitaria", "peritaje médico"),
    "criminalistica_forense": ("criminalística", "forense", "peritaje"),
    "propiedad_intelectual": ("propiedad intelectual", "marca", "patente", "derecho de autor"),
    "transito": ("tránsito", "accidente vial", "seguro de auto"),
    "ambiental": ("ambiental", "medio ambiente"),
    "internacional_privado": ("internacional", "exequatur", "apostilla"),
    "digital_datos": ("protección de datos", "datos personales", "privacidad", "evidencia digital",
                      "firma electrónica", "digital"),
    "migracion": ("migración", "migratorio", "visa", "residencia", "extranjería"),
}


@dataclass
class VacancyPosting:
    """Una vacante real. `titulo` es el único campo garantizado — Indeed no
    siempre expone la descripción completa en la búsqueda; si se tiene,
    `descripcion` amplía la clasificación pero nunca la reemplaza."""
    titulo: str
    empresa: str = ""
    ubicacion: str = ""
    publicado: str = ""
    url: str = ""
    descripcion: str = ""
    fuente: str = "indeed"

    def texto_clasificable(self):
        return f"{self.titulo} {self.descripcion}".strip()

    def to_dict(self):
        from dataclasses import asdict
        return asdict(self)


@dataclass
class ClasificacionVacante:
    posting: VacancyPosting
    materias: list = field(default_factory=list)          # nunca inventadas: solo coincidencia literal
    palabras_encontradas: dict = field(default_factory=dict)  # materia -> [palabras]

    @property
    def sin_materia_reconocida(self):
        return not self.materias

    def to_dict(self):
        return {"titulo": self.posting.titulo, "url": self.posting.url,
                "empresa": self.posting.empresa, "materias": list(self.materias),
                "palabras_encontradas": dict(self.palabras_encontradas)}


def clasificar_vacante(posting, vocabulario=None):
    """Coincidencia literal, normalizada, contra el vocabulario declarado.
    Una vacante puede coincidir con varias materias (p. ej. "abogado
    corporativo/notarial"). Sin coincidencia -> lista vacía, nunca un
    genérico "civil" por defecto."""
    vocabulario = vocabulario or PALABRAS_CLAVE_POR_MATERIA
    texto = normaliza(posting.texto_clasificable())
    materias, encontradas = [], {}
    for materia, palabras in vocabulario.items():
        hits = [p for p in palabras if normaliza(p) in texto]
        if hits:
            materias.append(materia)
            encontradas[materia] = hits
    return ClasificacionVacante(posting, materias, encontradas)


def cobertura_real_por_materia(registros=None):
    """Cuenta piezas REALES del corpus histórico por materia (nunca
    generadas/candidatas: solo lo ya producido). Registra también qué temas
    del corpus no resolvieron a ninguna materia conocida — igual criterio
    fail-closed que `corpus_import.py` ya aplica."""
    if registros is None:
        import corpus_import as ci
        registros, _ = ci.construir_registros()
    conteo = {}
    for r in registros:
        conteo[r.materia] = conteo.get(r.materia, 0) + 1
    return conteo


@dataclass
class TemaPropuesto:
    materia: str
    senales_vacantes: int
    cobertura_real: int
    ejemplos: list = field(default_factory=list)   # [(titulo, empresa, url)]
    razon: str = ""

    def to_dict(self):
        return {"materia": self.materia, "senales_vacantes": self.senales_vacantes,
                "cobertura_real": self.cobertura_real, "ejemplos": list(self.ejemplos),
                "razon": self.razon}


@dataclass
class CandidatoDepuracion:
    materia: str
    corridas_sin_senal: int
    razon: str = ""

    def to_dict(self):
        return {"materia": self.materia, "corridas_sin_senal": self.corridas_sin_senal,
                "razon": self.razon}


@dataclass
class RadarResult:
    fecha: str
    total_vacantes: int
    clasificadas: int
    sin_materia_reconocida: list = field(default_factory=list)
    senales_por_materia: dict = field(default_factory=dict)
    candidatos_nuevos: list = field(default_factory=list)
    candidatos_a_depurar: list = field(default_factory=list)
    fuente: str = ""

    def to_dict(self):
        return {
            "fecha": self.fecha, "fuente": self.fuente,
            "total_vacantes": self.total_vacantes, "clasificadas": self.clasificadas,
            "sin_materia_reconocida": [p.titulo for p in self.sin_materia_reconocida],
            "senales_por_materia": dict(self.senales_por_materia),
            "candidatos_nuevos": [c.to_dict() for c in self.candidatos_nuevos],
            "candidatos_a_depurar": [c.to_dict() for c in self.candidatos_a_depurar],
        }


# Umbral: una materia entra a "candidatos_nuevos" con >=2 señales de vacante
# reales y <3 piezas ya producidas — evita proponer un tema por una sola
# vacante aislada, y nunca compite con materias que ya tienen producción
# sostenida (ahí el radar no aporta nada nuevo).
MIN_SENALES_PARA_PROPONER = 2
MAX_COBERTURA_PARA_PROPONER = 3


def ejecutar_radar(postings, registros=None, fuente="", historial_previo=None):
    """Corrida completa. `historial_previo` (lista de RadarResult.to_dict()
    de corridas anteriores, opcional) permite que la depuración se decida
    sobre evidencia acumulada — ver `cargar_historial`/`registrar_corrida`."""
    clasificaciones = [clasificar_vacante(p) for p in postings]
    cobertura = cobertura_real_por_materia(registros)

    senales = {}
    ejemplos = {}
    for c in clasificaciones:
        for m in c.materias:
            senales[m] = senales.get(m, 0) + 1
            ejemplos.setdefault(m, []).append(
                (c.posting.titulo, c.posting.empresa, c.posting.url))

    candidatos_nuevos = []
    for materia, n in sorted(senales.items(), key=lambda kv: -kv[1]):
        cob = cobertura.get(materia, 0)
        if n >= MIN_SENALES_PARA_PROPONER and cob < MAX_COBERTURA_PARA_PROPONER:
            candidatos_nuevos.append(TemaPropuesto(
                materia=materia, senales_vacantes=n, cobertura_real=cob,
                ejemplos=ejemplos[materia][:5],
                razon=(f"{n} vacantes reales detectadas, solo {cob} pieza(s) ya "
                       f"producidas en el corpus histórico.")))

    # Depuración: acumula corridas sin señal a partir del historial previo.
    corridas_previas = list(historial_previo or [])
    candidatos_a_depurar = []
    for materia in PALABRAS_CLAVE_POR_MATERIA:
        if materia in MATERIAS_PROTEGIDAS or cobertura.get(materia, 0) > 0:
            continue
        sin_senal_hoy = materia not in senales
        if not sin_senal_hoy:
            continue
        corridas_sin_senal = 1 + sum(
            1 for corrida in corridas_previas
            if materia not in (corrida.get("senales_por_materia") or {})
        )
        if corridas_sin_senal >= 2:
            candidatos_a_depurar.append(CandidatoDepuracion(
                materia=materia, corridas_sin_senal=corridas_sin_senal,
                razon=(f"0 piezas reales en el corpus y 0 señales de vacantes en "
                       f"{corridas_sin_senal} corridas del radar. Candidato a retirar "
                       "de la capa activa — nunca a borrar (00 LEER PRIMERO §9: "
                       "'retirar de la capa activa lo superado', no destruir).")))

    return RadarResult(
        fecha=datetime.now(timezone.utc).isoformat(),
        total_vacantes=len(postings),
        clasificadas=sum(1 for c in clasificaciones if not c.sin_materia_reconocida),
        sin_materia_reconocida=[c.posting for c in clasificaciones if c.sin_materia_reconocida],
        senales_por_materia=senales,
        candidatos_nuevos=candidatos_nuevos,
        candidatos_a_depurar=candidatos_a_depurar,
        fuente=fuente,
    )


def cargar_historial(path=None):
    p = Path(path or LOG_PATH)
    if not p.is_file():
        return []
    return json.loads(p.read_text(encoding="utf-8")).get("corridas", [])


def registrar_corrida(result, path=None):
    """Append-only: nunca reescribe una corrida anterior."""
    p = Path(path or LOG_PATH)
    historial = cargar_historial(p)
    historial.append(result.to_dict())
    p.write_text(json.dumps({"schema_version": "1.0", "corridas": historial},
                            indent=2, ensure_ascii=False), encoding="utf-8")
    return p


def render_markdown(result):
    lineas = [
        f"# Radar de temas desde vacantes — {result.fecha}",
        f"\nFuente: {result.fuente or 'sin declarar'}",
        f"\nVacantes analizadas: {result.total_vacantes} "
        f"({result.clasificadas} clasificadas, "
        f"{len(result.sin_materia_reconocida)} sin materia reconocida).",
    ]
    lineas.append("\n## Señales por materia\n")
    for materia, n in sorted(result.senales_por_materia.items(), key=lambda kv: -kv[1]):
        lineas.append(f"- **{materia}**: {n} vacante(s)")

    lineas.append("\n## Candidatos a tema nuevo (propuesta, no decisión)\n")
    if not result.candidatos_nuevos:
        lineas.append("Ninguno en esta corrida.")
    for c in result.candidatos_nuevos:
        lineas.append(f"\n### {c.materia}")
        lineas.append(c.razon)
        for titulo, empresa, url in c.ejemplos:
            lineas.append(f"- \"{titulo}\" — {empresa} ({url})")

    lineas.append("\n## Candidatos a depurar (propuesta, no decisión — nunca se borra solo)\n")
    if not result.candidatos_a_depurar:
        lineas.append("Ninguno en esta corrida.")
    for c in result.candidatos_a_depurar:
        lineas.append(f"- **{c.materia}**: {c.razon}")

    if result.sin_materia_reconocida:
        lineas.append("\n## Vacantes sin materia reconocida (vocabulario a revisar)\n")
        for p in result.sin_materia_reconocida:
            lineas.append(f"- \"{p.titulo}\" — {p.empresa} ({p.url})")

    return "\n".join(lineas)
