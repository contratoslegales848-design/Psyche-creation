"""OBJECT_REGISTRY del ecosistema LegalMente.

Regla de honestidad (CLAUDE.md §2): una mencion en un documento no es una
capacidad implementada. Por eso este registro NO es una lista estatica escrita
a mano: cada objeto declara donde deberia estar, y `resolve_state()` comprueba
el sistema de archivos real en el momento de leerlo. Un objeto que se declara
presente y no existe se degrada a MISSING_ARTIFACT, nunca al reves.

Es el mismo criterio que ya usa `visual/topology.py` para los enlaces: la
afirmacion se verifica al construir la lista, no se promete y se olvida.

Este modulo no publica, no genera arte, no toca claims y no modifica el canon.
"""

from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# --- Vocabulario de estado -------------------------------------------------
# Cerrado, como exige el prompt de integracion §3.2.
CANONICAL = "CANONICAL"
FROZEN = "FROZEN"
AUXILIARY = "AUXILIARY"
PROPOSED = "PROPOSED"
BLOCKED = "BLOCKED"
READY_FOR_HUMAN_REVIEW = "READY_FOR_HUMAN_REVIEW"
# Estados propios de este registro, para no fingir que algo existe:
MISSING_ARTIFACT = "MISSING_ARTIFACT"
EXTERNAL_READ_ONLY = "EXTERNAL_READ_ONLY"
# Distinto de MISSING_ARTIFACT a proposito: el objeto SI existe en el proyecto
# (esta en main), pero no en el arbol de esta rama. Confundir ambos casos
# borraria la diferencia entre "nunca se construyo" y "esta rama esta atrasada".
ABSENT_ON_THIS_BRANCH = "ABSENT_ON_THIS_BRANCH"

DECLARABLE_STATES = frozenset({
    CANONICAL, FROZEN, AUXILIARY, PROPOSED, BLOCKED,
    READY_FOR_HUMAN_REVIEW, MISSING_ARTIFACT, EXTERNAL_READ_ONLY,
    ABSENT_ON_THIS_BRANCH,
})

# Estados terminales: describen una ausencia ya comprobada, asi que
# resolve_state() no puede degradarlos ni promoverlos.
TERMINAL_ABSENT_STATES = frozenset({MISSING_ARTIFACT, ABSENT_ON_THIS_BRANCH})

# Capas del modelo unificado (prompt de integracion §4).
LAYER_ENTRY = "entrada_humana"
LAYER_NAVIGATION = "navegacion"
LAYER_KNOWLEDGE = "conocimiento"
LAYER_EVIDENCE = "evidencia"
LAYER_HELP = "ayuda"
LAYER_PRODUCT = "producto"
LAYER_OPERATION = "operacion"
LAYER_VISUAL = "visual"
LAYER_DISTRIBUTION = "distribucion"
LAYER_GOVERNANCE = "gobernanza"

LAYERS = (
    LAYER_ENTRY, LAYER_NAVIGATION, LAYER_KNOWLEDGE, LAYER_EVIDENCE,
    LAYER_HELP, LAYER_PRODUCT, LAYER_OPERATION, LAYER_VISUAL,
    LAYER_DISTRIBUTION, LAYER_GOVERNANCE,
)

# Repositorios del ecosistema.
REPO_PSYCHE = "psyche-creation"
REPO_WEB = "legalmente-web"
REPO_DRIVE = "google-drive"


@dataclass(frozen=True)
class EcosystemObject:
    """Un objeto del ecosistema con los campos obligatorios del prompt §5.

    `path` es relativo a la raiz de su repositorio. Si `repo` no es
    psyche-creation, no se puede verificar desde aqui y el estado declarado se
    conserva tal cual, marcado como no verificable.
    """

    object_id: str
    label: str
    layer: str
    repo: str
    declared_state: str
    owner: str
    next_action: str
    path: str | None = None
    source_ids: tuple[str, ...] = ()
    claim_ids: tuple[str, ...] = ()
    relations: tuple[str, ...] = ()
    blockers: tuple[str, ...] = ()
    tests: tuple[str, ...] = ()
    notes: str = ""
    # Campos §5 que hoy no aplican a ningun objeto real; se conservan
    # explicitos para que su ausencia sea una afirmacion, no un olvido.
    assets: tuple[str, ...] = ()
    prompts: tuple[str, ...] = ()
    fingerprints: tuple[str, ...] = ()
    handoff: str = "NONE"

    def verifiable(self) -> bool:
        """Solo lo que vive en este repositorio puede comprobarse aqui."""
        return self.repo == REPO_PSYCHE and self.path is not None

    def exists(self) -> bool:
        if not self.verifiable():
            return False
        return (REPO / self.path).exists()

    def resolve_state(self) -> str:
        """Estado real. Fail-closed: lo declarado no puede superar lo verificado.

        Un objeto de este repositorio que declara existir y no existe cae a
        MISSING_ARTIFACT. Nunca ocurre la promocion inversa: este metodo no
        puede convertir un MISSING_ARTIFACT en CANONICAL.
        """
        if self.declared_state in TERMINAL_ABSENT_STATES:
            return self.declared_state
        if not self.verifiable():
            return self.declared_state
        return self.declared_state if self.exists() else MISSING_ARTIFACT


def _obj(**kwargs) -> EcosystemObject:
    return EcosystemObject(**kwargs)


# --- Objetos reales de psyche-creation -------------------------------------

_PSYCHE_OBJECTS: tuple[EcosystemObject, ...] = (
    _obj(
        object_id="PSY-GOV-CLAUDE-MD", label="Reglas operativas del repositorio",
        layer=LAYER_GOVERNANCE, repo=REPO_PSYCHE, path="CLAUDE.md",
        declared_state=CANONICAL, owner="fundador",
        next_action="NONE — vigente",
        relations=("gobierna:PSY-EVID-SKILL-VERIF", "gobierna:PSY-VIS-ENGINE"),
        notes="Autoridad operativa local. No sustituye la Constitucion de Drive.",
    ),
    _obj(
        object_id="PSY-GOV-TECHNICAL-STATE", label="Estado tecnico real",
        layer=LAYER_GOVERNANCE, repo=REPO_PSYCHE, path="docs/TECHNICAL_STATE.md",
        declared_state=CANONICAL, owner="fundador",
        next_action="Actualizar tras esta integracion",
        notes="Semaforo por subsistema con corte 2026-08-27. Es la fuente de "
              "estado vigente; este registro enlaza, no la reescribe.",
    ),
    _obj(
        object_id="PSY-EVID-SKILL-VERIF", label="Skill de verificacion juridica",
        layer=LAYER_EVIDENCE, repo=REPO_PSYCHE,
        path=".claude/skills/legalmente-legal-verification",
        declared_state=CANONICAL, owner="fundador",
        next_action="Depende de PDFs oficiales en HOLD",
        tests=("scripts/test_validate_claim_packet.py",),
        relations=("valida:PSY-EVID-PACKET-01", "valida:PSY-EVID-PACKET-02",
                   "valida:PSY-EVID-PACKET-03", "valida:PSY-EVID-PACKET-04"),
        notes="Esquema v4, fail-closed. Ninguna IA es fuente juridica.",
    ),
    _obj(
        object_id="PSY-EVID-PACKET-01", label="Claim packet PIEZA-01",
        layer=LAYER_EVIDENCE, repo=REPO_PSYCHE,
        path=".claude/skills/legalmente-legal-verification/pilot/claim-packets/pieza-01-reales.json",
        declared_state=FROZEN, owner="fundador",
        next_action="NONE — aprobado y con handoff emitido",
        claim_ids=("pieza-01",), handoff="HO-PIEZA-01-REALES-001",
    ),
    _obj(
        object_id="PSY-EVID-PACKET-02", label="Claim packet PIEZA-02 (laboral, despido)",
        layer=LAYER_EVIDENCE, repo=REPO_PSYCHE,
        path=".claude/skills/legalmente-legal-verification/pilot/claim-packets/pieza-02-laboral.json",
        declared_state=BLOCKED, owner="fundador",
        next_action="Obtener PDFs oficiales AR/CO/ES-STS",
        blockers=("ECO-BLK-SOURCES-HOLD",),
    ),
    _obj(
        object_id="PSY-EVID-PACKET-03", label="Claim packet PIEZA-03 (honor)",
        layer=LAYER_EVIDENCE, repo=REPO_PSYCHE,
        path=".claude/skills/legalmente-legal-verification/pilot/claim-packets/pieza-03-honor.json",
        declared_state=BLOCKED, owner="fundador",
        next_action="Verificacion de fuentes pendiente",
        blockers=("ECO-BLK-SOURCES-HOLD",),
    ),
    _obj(
        object_id="PSY-EVID-PACKET-04", label="Claim packet PIEZA-04 (laboral basico)",
        layer=LAYER_EVIDENCE, repo=REPO_PSYCHE,
        path=".claude/skills/legalmente-legal-verification/pilot/claim-packets/pieza-04-laboral-basico.json",
        declared_state=ABSENT_ON_THIS_BRANCH, owner="fundador",
        next_action="Rebasar esta rama sobre main, o trabajarlo desde main",
        blockers=("ECO-BLK-STALE-BRANCH",),
        notes="Existe y esta fusionado en main (Capa A transversal, "
              "APTO_CON_MATICES, gate de arte CERRADO). No esta en el arbol de "
              "esta rama, que va 27 commits por detras de main.",
    ),
    _obj(
        object_id="PSY-EVID-PROVENANCE", label="Validador de procedencia de contenido",
        layer=LAYER_EVIDENCE, repo=REPO_PSYCHE,
        path="scripts/validate-content-provenance.py",
        declared_state=CANONICAL, owner="sistema",
        next_action="NONE",
        tests=("scripts/test_validate_content_provenance.py",),
    ),
    _obj(
        object_id="PSY-VIS-ENGINE", label="Motor de generacion visual",
        layer=LAYER_VISUAL, repo=REPO_PSYCHE, path="visual",
        declared_state=CANONICAL, owner="sistema",
        next_action="Sin credenciales de proveedor real configuradas",
        blockers=("ECO-BLK-NO-REAL-PROVIDER",),
    ),
    _obj(
        object_id="PSY-GOV-GATES", label="Gates de generacion visual",
        layer=LAYER_GOVERNANCE, repo=REPO_PSYCHE, path="visual/gates.py",
        declared_state=CANONICAL, owner="sistema",
        next_action="NONE",
        notes="Fail-closed: sin handoff aprobado no hay generacion.",
    ),
    _obj(
        object_id="PSY-GOV-TOPOLOGY", label="Topologia del organismo",
        layer=LAYER_GOVERNANCE, repo=REPO_PSYCHE, path="visual/topology.py",
        declared_state=CANONICAL, owner="sistema",
        next_action="NONE",
        notes="Grafo de enlaces ya existente. Este ecosistema lo consume; "
              "no construye un grafo paralelo.",
    ),
    _obj(
        object_id="PSY-OPS-INVENTORY", label="Inventario y bandeja de decisiones humanas",
        layer=LAYER_OPERATION, repo=REPO_PSYCHE, path="visual/inventory.py",
        declared_state=CANONICAL, owner="sistema", next_action="NONE",
        tests=("visual/test_inventory.py",),
    ),
    _obj(
        object_id="PSY-PROD-CONTRACT", label="Canonical Envelope v1 (contrato cross-repo)",
        layer=LAYER_PRODUCT, repo=REPO_PSYCHE, path="contract/canonical_envelope.py",
        declared_state=CANONICAL, owner="sistema",
        next_action="Entregado por patches; falta empujarlo a legalmente-web",
        relations=("consumido_por:WEB-PROD-CONSUMER",),
    ),
    _obj(
        object_id="PSY-PROD-HANDOFF-WEB", label="Paquete de handoff a legalmente-web",
        layer=LAYER_PRODUCT, repo=REPO_PSYCHE, path="handoff/legalmente-web",
        declared_state=READY_FOR_HUMAN_REVIEW, owner="fundador",
        next_action="Sesion con permisos de legallmente-alt para aplicar",
        blockers=("ECO-BLK-NO-WRITE-WEB",),
    ),
    _obj(
        object_id="PSY-NAV-DIRECCION", label="Direccion de contenido: basico antes que complejo",
        layer=LAYER_NAVIGATION, repo=REPO_PSYCHE,
        path="docs/direccion-basico-antes-que-complejo.md",
        declared_state=ABSENT_ON_THIS_BRANCH, owner="fundador",
        next_action="Rebasar esta rama sobre main, o trabajarlo desde main",
        blockers=("ECO-BLK-STALE-BRANCH",),
        notes="CLAUDE.md lo cita como direccion de contenido vigente y existe "
              "en main, pero no en el arbol de esta rama.",
    ),
)

# --- Objetos de legalmente-web (lectura externa, sin escritura) -------------

_WEB_OBJECTS: tuple[EcosystemObject, ...] = (
    _obj(
        object_id="WEB-NAV-KNOWLEDGE-GRAPH", label="Grafo de conocimiento (mundos, rutas, conceptos)",
        layer=LAYER_NAVIGATION, repo=REPO_WEB, path="src/lib/knowledge-graph",
        declared_state=EXTERNAL_READ_ONLY, owner="fundador",
        next_action="Conectar con la capa de evidencia de Psyche",
        blockers=("ECO-BLK-ENTRY-EVIDENCE-GAP",),
        notes="Aqui viven HUMAN_CONDUCT, rutas y conceptos. Es la capa de "
              "entrada del ecosistema, y hoy no conoce los claim packets.",
    ),
    _obj(
        object_id="WEB-HELP-BEFORE-SIGNING", label="Antes de firmar (herramienta sin PII)",
        layer=LAYER_HELP, repo=REPO_WEB, path="src/lib/legal-core/before-signing.ts",
        declared_state=EXTERNAL_READ_ONLY, owner="fundador",
        next_action="NONE — con prueba de privacidad propia",
        notes="Unico protocolo de ayuda realmente implementado del ecosistema.",
    ),
    _obj(
        object_id="WEB-VIS-ROTATION", label="Motor de rotacion visual",
        layer=LAYER_VISUAL, repo=REPO_WEB, path="scripts/visual-rotation-engine.mjs",
        declared_state=EXTERNAL_READ_ONLY, owner="fundador", next_action="NONE",
    ),
    _obj(
        object_id="WEB-KNOW-COMPOSITION", label="Contrato de composicion de contenido",
        layer=LAYER_KNOWLEDGE, repo=REPO_WEB, path="src/lib/content-composition",
        declared_state=PROPOSED, owner="fundador",
        next_action="Aplicar patch en sesion con permisos de legallmente-alt",
        blockers=("ECO-BLK-NO-WRITE-WEB",),
        notes="Construido y probado localmente (14 pruebas). Entregado por "
              "patch; no esta en ninguna rama remota.",
    ),
    _obj(
        object_id="WEB-PROD-CONSUMER", label="Consumidor estricto del Canonical Envelope",
        layer=LAYER_PRODUCT, repo=REPO_WEB, path=None,
        declared_state=PROPOSED, owner="fundador",
        next_action="Aplicar la serie de patches de handoff/",
        blockers=("ECO-BLK-NO-WRITE-WEB",),
    ),
)

# --- Objetos nombrados por el prompt que NO tienen artefacto ---------------
# Registrados, no inventados. Su ausencia es el hallazgo, no un hueco a rellenar.

def _missing(object_id: str, label: str, layer: str, note: str) -> EcosystemObject:
    return _obj(
        object_id=object_id, label=label, layer=layer, repo=REPO_DRIVE, path=None,
        declared_state=MISSING_ARTIFACT, owner="fundador",
        next_action="Localizar el artefacto en Drive o declararlo inexistente",
        blockers=("ECO-BLK-NAMED-NOT-BUILT",), notes=note,
    )


_MISSING_OBJECTS: tuple[EcosystemObject, ...] = (
    _missing("MIS-CONTENT-FACTORY", "Content Factory V1", LAYER_KNOWLEDGE,
             "Cero artefactos. Solo existe vocabulario de etapas en "
             "visual/topology.py:content_factory_topology(), que es una lectura "
             "de lo real, no una fabrica."),
    _missing("MIS-VISUAL-FACTORY", "Visual Factory V1", LAYER_VISUAL,
             "Cero coincidencias en ambos repositorios."),
    _missing("MIS-EXPANSION-LAB", "Expansion Business Launch Lab V1", LAYER_DISTRIBUTION,
             "Cero coincidencias en ambos repositorios."),
    _missing("MIS-COMMERCIAL-OPS", "Commercial & Launch Operations Factory V1", LAYER_OPERATION,
             "Cero coincidencias en ambos repositorios."),
    _missing("MIS-LC1-RELEASE", "LC1 Release Assembly V1", LAYER_OPERATION,
             "Cero coincidencias en ambos repositorios."),
    _missing("MIS-PUBLIC-CLOSURE", "Public Launch Closure Factory V1", LAYER_GOVERNANCE,
             "Cero coincidencias en ambos repositorios."),
    _missing("MIS-DEMAND-INTEL", "Demand / Growth Intelligence V1", LAYER_DISTRIBUTION,
             "Cero coincidencias en ambos repositorios."),
    _missing("MIS-LINKEDIN-BANK", "LinkedIn Strategy / banco de experiencia de Raymundo",
             LAYER_DISTRIBUTION,
             "'Raymundo' aparece en el repositorio unicamente como aprobador "
             "humano en decisiones y claim packets. 'LinkedIn' aparece una vez, "
             "de paso. No existe banco editorial alguno."),
    _missing("MIS-RC0", "RC0", LAYER_GOVERNANCE,
             "Nombrado como intocable por el prompt, pero sin artefacto "
             "identificable en este repositorio."),
    _missing("MIS-GOLD-STANDARD", "Gold Standard visual", LAYER_VISUAL,
             "Nombrado como condicion para generar arte nuevo. Sin artefacto: "
             "por tanto la condicion no puede darse por cumplida."),
)

ALL_OBJECTS: tuple[EcosystemObject, ...] = _PSYCHE_OBJECTS + _WEB_OBJECTS + _MISSING_OBJECTS


def by_id(object_id: str) -> EcosystemObject | None:
    for obj in ALL_OBJECTS:
        if obj.object_id == object_id:
            return obj
    return None


def by_layer(layer: str) -> tuple[EcosystemObject, ...]:
    return tuple(obj for obj in ALL_OBJECTS if obj.layer == layer)


def resolved_registry() -> tuple[tuple[EcosystemObject, str], ...]:
    """Cada objeto con su estado REAL, no el declarado."""
    return tuple((obj, obj.resolve_state()) for obj in ALL_OBJECTS)


def drifted() -> tuple[EcosystemObject, ...]:
    """Objetos que declaran existir y no existen. Deberia estar vacio."""
    return tuple(
        obj for obj in ALL_OBJECTS
        if obj.declared_state not in TERMINAL_ABSENT_STATES
        and obj.resolve_state() == MISSING_ARTIFACT
    )
