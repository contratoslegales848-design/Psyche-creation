"""DRIVE_EVIDENCE — qué se buscó en Drive, qué apareció y con qué autoridad.

Este módulo corrige un error real de la sesión anterior. Allí se concluyó
`MISSING_ARTIFACT` para siete paquetes auxiliares basándose únicamente en greps
sobre los repositorios. La búsqueda en Drive demuestra que **todos existen**.
La lección queda codificada aquí: no encontrar algo en un repositorio no es
evidencia de que no exista.

Distinción central que este módulo sostiene: un artefacto puede estar
`FOUND_AUXILIARY` (existe, con ID, fecha y tamaño verificados) y al mismo tiempo
tener su contenido en `ACCESS_GAP`, porque las instrucciones prohíben descargar
o ejecutar artefactos externos de forma automática. Existencia verificada no es
contenido verificado.

Búsqueda ejecutada: 2026-09-03 desde la cuenta de Drive de la sesión, vía CLI autorizado.
Sin escritura en Drive.
"""

from dataclasses import dataclass

# --- Vocabulario de clasificación exigido por las instrucciones §3.6 --------
FOUND_CANONICAL = "FOUND_CANONICAL"
FOUND_AUXILIARY = "FOUND_AUXILIARY"
FOUND_HISTORICAL = "FOUND_HISTORICAL"
ABSENT_ON_THIS_BRANCH = "ABSENT_ON_THIS_BRANCH"
MISSING_ARTIFACT = "MISSING_ARTIFACT"
ACCESS_GAP = "ACCESS_GAP"
BLOCKED_BY_AUTHORIZATION = "BLOCKED_BY_AUTHORIZATION"

CLASSIFICATIONS = frozenset({
    FOUND_CANONICAL, FOUND_AUXILIARY, FOUND_HISTORICAL, ABSENT_ON_THIS_BRANCH,
    MISSING_ARTIFACT, ACCESS_GAP, BLOCKED_BY_AUTHORIZATION,
})

SEARCH_DATE = "2026-09-03"
CONTRIBUTION_FOLDER = "1I8-Mr6DuMuazc1HqfBGcBUmAZKSfFPXi"


@dataclass(frozen=True)
class DriveArtifact:
    """Un artefacto buscado en Drive, con la evidencia de la búsqueda.

    `content_state` es distinto de `classification` a propósito: el primero
    dice si pudimos LEER el contenido, el segundo si el objeto EXISTE.
    """

    artifact_id: str            # identificador lógico dentro del ecosistema
    title: str                  # título literal en Drive
    drive_id: str | None        # ID real de Drive; None si no se encontró
    mime_type: str
    size_bytes: int | None
    modified: str
    classification: str
    authority_level: int        # nivel de la jerarquía del súper prompt §1
    content_state: str          # leído, o ACCESS_GAP
    evidence: str               # cómo se estableció

    def exists(self) -> bool:
        return self.drive_id is not None

    def content_verified(self) -> bool:
        return self.content_state == "READ"


# --- Nivel 1-2: autoridad constitucional y bitácora ------------------------

_CANONICAL: tuple[DriveArtifact, ...] = (
    DriveArtifact(
        artifact_id="DRV-CONSTITUCION",
        title="LegalMente — Constitución y Manual Operativo (LEER PRIMERO)",
        drive_id="11xVy8GvEACrJB5jHnWKbLncuR0Ww-YwbO5EBIcOGgR0",
        mime_type="application/vnd.google-apps.document",
        size_bytes=9852, modified="2026-08-27",
        classification=FOUND_CANONICAL, authority_level=1,
        content_state=ACCESS_GAP,
        evidence="Localizado por título. Autoridad superior de la jerarquía. "
                 "No se leyó su contenido en esta sesión: la tarea no lo exigía "
                 "y no se modificó nada que dependa de él.",
    ),
    DriveArtifact(
        artifact_id="DRV-BITACORA",
        title="LegalMente — Bitácora operativa y decisiones",
        drive_id="1Bpq4FXBVGQZ1LqQ9ieW3MwPXr1QwhI5hqFA8obK_6v8",
        mime_type="application/vnd.google-apps.document",
        size_bytes=16032, modified="2026-09-01",
        classification=FOUND_CANONICAL, authority_level=2,
        content_state=ACCESS_GAP,
        evidence="Localizada por título. Su descripción confirma que el objeto "
                 "canónico de la revisión humana es PIEZA-01-REALES.",
    ),
    DriveArtifact(
        artifact_id="DRV-NEUTRALIDAD",
        title="LegalMente — Decisión Constitucional: Neutralidad Jurisdiccional",
        drive_id="1sFd_NXItyCID2rTQsBDOtep42xKjqTGdjtXyX9QkVro",
        mime_type="application/vnd.google-apps.document",
        size_bytes=11541, modified="2026-08-19",
        classification=FOUND_CANONICAL, authority_level=2,
        content_state=ACCESS_GAP,
        evidence="Citada por la skill de verificación como fuente viva de la "
                 "política de jurisdicción.",
    ),
)

# --- Nivel 5: los siete paquetes auxiliares --------------------------------
# CORRECCIÓN: la sesión anterior los declaró MISSING_ARTIFACT. Existen.

def _package(artifact_id: str, title: str, drive_id: str, size: int) -> DriveArtifact:
    return DriveArtifact(
        artifact_id=artifact_id, title=title, drive_id=drive_id,
        mime_type="application/zip", size_bytes=size, modified="2026-09-03",
        classification=FOUND_AUXILIARY, authority_level=5,
        content_state=ACCESS_GAP,
        evidence=f"Encontrado en la carpeta {CONTRIBUTION_FOLDER} el {SEARCH_DATE}, "
                 "con su .sha256 acompañante. Contenido NO verificado: las "
                 "instrucciones prohíben descargar o ejecutar artefactos "
                 "externos de forma automática.",
    )


_PACKAGES: tuple[DriveArtifact, ...] = (
    _package("DRV-CONTENT-FACTORY", "LEGALMENTE_CONTENT_FACTORY_V1.zip",
             "1uNgeBTXxDxy9pPRQxs75d9YAMYRDo1Kf", 142868),
    _package("DRV-VISUAL-FACTORY", "LEGALMENTE_VISUAL_FACTORY_V1.zip",
             "12q4732yQ1HDvw4r1lEVabGrG2O9BKnc-", 124547274),
    _package("DRV-EXPANSION-LAB", "LEGALMENTE_EXPANSION_BUSINESS_LAUNCH_LAB_V1.zip",
             "1b-AwtjFLi4u1xD4Tj_l6iGuy80cUeRH3", 110266),
    _package("DRV-COMMERCIAL-OPS", "LEGALMENTE_COMMERCIAL_LAUNCH_OPERATIONS_FACTORY_V1.zip",
             "1Nl35JS4UAZpaCIac7rP2tOAbZDX_nRTX", 35622),
    _package("DRV-LC1-RELEASE", "LEGALMENTE_LC1_RELEASE_ASSEMBLY_DRY_RUN_FACTORY_V1.zip",
             "13lt8LdL6PyEp0lIaUXlpkGuUF5VfBuAY", 34036),
    _package("DRV-PUBLIC-CLOSURE", "LEGALMENTE_PUBLIC_LAUNCH_CLOSURE_FACTORY_V1.zip",
             "1r_55-ApsfRO8I2dzcqurBZUmA-NyMf9Q", 41285),
    _package("DRV-DEMAND-INTEL", "LEGALMENTE_DEMAND_GROWTH_ACQUISITION_INTELLIGENCE_V1.zip",
             "1VY9AcbVa-KZk3xA4yKtGCzo71EXwd5Or", 136573),
)

# --- Nivel 6: LinkedIn y aportación de Raymundo ----------------------------

_LINKEDIN: tuple[DriveArtifact, ...] = (
    DriveArtifact(
        artifact_id="DRV-LINKEDIN-STRATEGY",
        title="LegalMente Artefacto 05 LinkedIn Strategy",
        drive_id="1GWyYAZ2T7x__I-FqmRsDrbaEC7IXloo2Ycq3tcWc_I0",
        mime_type="application/vnd.google-apps.document",
        size_bytes=12025, modified="2026-09-03",
        classification=FOUND_AUXILIARY, authority_level=6,
        content_state=ACCESS_GAP,
        evidence="Existe como documento. No es autorización de publicación.",
    ),
    DriveArtifact(
        artifact_id="DRV-RAYMUNDO-CONTRIB",
        title="LEGALMENTE_RAYMUNDO_LINKEDIN_HELP_CONTRIBUTION_V1.zip",
        drive_id="10ZbpPNWAyPVXRx6nI6lCpZ7z54O--4Wd",
        mime_type="application/zip", size_bytes=8359, modified="2026-09-03",
        classification=FOUND_AUXILIARY, authority_level=6,
        content_state=ACCESS_GAP,
        evidence="Paquete comprimido. Su README suelto sí se leyó y declara "
                 "estado AUXILIARY_CONTRIBUTION_READY_FOR_FOUNDER_REVIEW.",
    ),
    DriveArtifact(
        artifact_id="DRV-FIVE-HELP-PROTOCOLS",
        title="02_five_help_protocols.md",
        drive_id="17HeKx9FqZrvqwMDTOarjUtuzqvtYeOUf",
        mime_type="text/markdown", size_bytes=920, modified="2026-09-03",
        classification=FOUND_AUXILIARY, authority_level=6,
        content_state="READ",
        evidence="LEÍDO. Contiene los cinco protocolos: antes de comprar tierra, "
                 "de predio matriz a lote, quién debe intervenir, marketing/"
                 "autorización/contrato, y cuándo detenerse. Es el ORIGINAL del "
                 "que ecosystem/help_protocols.py resultó ser un duplicado no "
                 "intencionado.",
    ),
    DriveArtifact(
        artifact_id="DRV-RAYMUNDO-README",
        title="README.md (Raymundo LinkedIn + Help Contribution V1)",
        drive_id="1D5vfwRd-ko-wNa24uWWkgR0RD6t0_pP5",
        mime_type="text/markdown", size_bytes=673, modified="2026-09-03",
        classification=FOUND_AUXILIARY, authority_level=6,
        content_state="READ",
        evidence="LEÍDO. Declara AUXILIARY / CONTRIBUTION / NON-CANONICAL y "
                 "que no autoriza publicación, asesoría, DM, cobro ni PII.",
    ),
)

# --- Fuentes jurídicas: el estado NO cambia --------------------------------

_SOURCES: tuple[DriveArtifact, ...] = (
    DriveArtifact(
        artifact_id="DRV-SRC-MX-LFT", title="SOURCE_MX_LFT.pdf",
        drive_id="1Q1cBHS8jhrWzIwbvjrHvYT6Nd6YBopiU",
        mime_type="application/pdf", size_bytes=4225835, modified="2026-09-02",
        classification=FOUND_CANONICAL, authority_level=2,
        content_state=ACCESS_GAP,
        evidence="Depositado en la carpeta MX. VERIFIED según el receipt humano "
                 "del 2026-09-02, no según este módulo. Su articulado sigue sin "
                 "leerse: no hay EXACT_COPY derivable todavía.",
    ),
    DriveArtifact(
        artifact_id="DRV-SRC-ES-ET", title="SOURCE_ES_ET.pdf",
        drive_id="1QJQK8HZTJk6_hr6foJZOVCpKWV1wrJE-",
        mime_type="application/pdf", size_bytes=695761, modified="2026-09-02",
        classification=FOUND_CANONICAL, authority_level=2,
        content_state=ACCESS_GAP,
        evidence="Depositado en la carpeta ES. VERIFIED según el receipt humano.",
    ),
    DriveArtifact(
        artifact_id="DRV-SRC-AR-LCT", title="SOURCE_AR_LCT.pdf (buscado)",
        drive_id=None, mime_type="application/pdf", size_bytes=None,
        modified="N/A", classification=MISSING_ARTIFACT, authority_level=2,
        content_state=ACCESS_GAP,
        evidence=f"Búsqueda del {SEARCH_DATE} por título LCT y SOURCE_: sin "
                 "resultado. La carpeta AR sigue vacía. Permanece en HOLD.",
    ),
    DriveArtifact(
        artifact_id="DRV-SRC-CO-CST", title="SOURCE_CO_CST.pdf (buscado)",
        drive_id=None, mime_type="application/pdf", size_bytes=None,
        modified="N/A", classification=MISSING_ARTIFACT, authority_level=2,
        content_state=ACCESS_GAP,
        evidence=f"Búsqueda del {SEARCH_DATE} por título CST y SOURCE_: sin "
                 "resultado. La carpeta CO sigue vacía. Permanece en HOLD.",
    ),
    DriveArtifact(
        artifact_id="DRV-SRC-ES-STS", title="SOURCE_ES_STS_6207_2012.pdf (buscado)",
        drive_id=None, mime_type="application/pdf", size_bytes=None,
        modified="N/A", classification=MISSING_ARTIFACT, authority_level=2,
        content_state=ACCESS_GAP,
        evidence=f"Búsqueda del {SEARCH_DATE} por título STS y SOURCE_: sin "
                 "resultado. El enlace oficial sigue tras CAPTCHA, que no se "
                 "resuelve ni se elude. Permanece en HOLD.",
    ),
)

ALL_ARTIFACTS: tuple[DriveArtifact, ...] = (
    _CANONICAL + _PACKAGES + _LINKEDIN + _SOURCES
)


def by_id(artifact_id: str) -> DriveArtifact | None:
    for artifact in ALL_ARTIFACTS:
        if artifact.artifact_id == artifact_id:
            return artifact
    return None


def by_classification(classification: str) -> tuple[DriveArtifact, ...]:
    return tuple(a for a in ALL_ARTIFACTS if a.classification == classification)


def sources_still_missing() -> tuple[DriveArtifact, ...]:
    """Las tres fuentes en HOLD, confirmadas ausentes por búsqueda."""
    return tuple(
        a for a in _SOURCES if a.classification == MISSING_ARTIFACT
    )


def corrected_from_previous_session() -> tuple[DriveArtifact, ...]:
    """Los objetos cuya clasificación anterior era errónea.

    Se conserva explícito para que la corrección sea auditable y no se
    pierda como un cambio silencioso de estado."""
    return _PACKAGES + (by_id("DRV-LINKEDIN-STRATEGY"), by_id("DRV-RAYMUNDO-CONTRIB"))
