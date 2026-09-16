"""Nucleo agnostico al proveedor.

El dominio de LegalMente NUNCA conoce a OpenAI, Grok, Gemini, Higgsfield, Flux,
Stable Diffusion ni Ideogram. Habla este contrato. Cada adapter traduce en su
propio archivo (mandato §24, §25).

CONTRATO DE SALIDA text-to-image vs. image-edit (Hotfix, 16-sep-2026): un
consumidor externo intentó consumir una petición de LegalMente y la
interpretó como EDIT/RESTORE, exigiendo una imagen de referencia que nunca
se pidió. Causa raíz real: `NormalizedImageRequest` — el ÚNICO lugar del
repositorio donde se construye la petición final hacia un proveedor
(`pipeline.py::generate_visual`, una sola vez) — no declaraba NINGÚN campo
de modo de operación. El prompt en lenguaje natural puede sonar como
"restaurar", "recrear" o "traer de vuelta" sin que eso sea una instrucción
estructural de edición; el modo de generación nunca debe inferirse del
texto creativo. Ver `docs/contrato-generacion-imagenes-legalmente.md`.
"""

from dataclasses import dataclass, field

GENERATION_MODE_TEXT_TO_IMAGE = "TEXT_TO_IMAGE"
GENERATION_MODE_IMAGE_EDIT = "IMAGE_EDIT"
GENERATION_MODES = (GENERATION_MODE_TEXT_TO_IMAGE, GENERATION_MODE_IMAGE_EDIT)

# Estados de entrega de un item de generación (mandato Hotfix §15) — nunca se
# afirma un estado más avanzado del que realmente ocurrió. Sin proveedor real
# conectado (ver docs/auditoria-inteligencia-tematica-2026-09-16.md §3), el
# estado máximo alcanzable hoy es COMPILED.
DELIVERY_COMPILED = "COMPILED"
DELIVERY_SENT_TO_PROVIDER = "SENT_TO_PROVIDER"
DELIVERY_GENERATED = "GENERATED"
DELIVERY_QA_ACCEPTED = "QA_ACCEPTED"
DELIVERY_REJECTED = "REJECTED"
DELIVERY_STATES = (DELIVERY_COMPILED, DELIVERY_SENT_TO_PROVIDER, DELIVERY_GENERATED,
                   DELIVERY_QA_ACCEPTED, DELIVERY_REJECTED)


class ProviderError(RuntimeError):
    pass


@dataclass(frozen=True)
class ProviderCapabilities:
    provider_id: str
    aspect_ratios: tuple = ()
    supports_negative_prompt: bool = False
    supports_reference_image: bool = False
    supports_editing: bool = False
    supports_reliable_text: bool = False
    supports_seed: bool = False
    supports_transparency: bool = False
    max_width: int = 0
    max_height: int = 0


@dataclass(frozen=True)
class NormalizedImageRequest:
    """Peticion en el vocabulario de LegalMente, no en el de un proveedor.

    `generation_mode` es OBLIGATORIO y explícito — nunca se infiere del
    lenguaje del prompt. Por defecto `TEXT_TO_IMAGE`: toda la infraestructura
    real de este repositorio (`pipeline.py::generate_visual`) sólo produce
    piezas nuevas desde cero, nunca edita una imagen existente — no hay
    ningún flujo de edición implementado hoy. Los campos de edición existen
    en el contrato para no romper un flujo IMAGE_EDIT futuro, pero
    `validate_generation_contract()` exige que estén vacíos en TEXT_TO_IMAGE
    y que `source_image` exista siempre en IMAGE_EDIT — nunca se hereda un
    `source_image`/`reference_images` de una generación anterior de forma
    automática.
    """

    content_id: str
    prompt: str
    negative_prompt: str
    width: int
    height: int
    aspect_ratio: str
    seed: int = None
    requires_text_rendering: bool = False
    metadata: dict = field(default_factory=dict)
    generation_mode: str = GENERATION_MODE_TEXT_TO_IMAGE
    source_image: bytes = None
    reference_images: tuple = ()
    edit_instruction: str = None


def validate_generation_contract(request):
    """Invariante fail-fast del contrato de salida (Hotfix, 16-sep-2026).

    Nunca intenta adivinar ni corrige en silencio: cada violación es un
    problema explícito en la lista devuelta. Lista vacía = contrato válido.
    Quien llama decide qué hacer con los problemas (en este repositorio,
    `pipeline.py` los convierte en un receipt `CONTRATO_GENERACION_INVALIDO`
    y nunca contacta al proveedor).
    """
    problemas = []
    modo = request.generation_mode
    if modo not in GENERATION_MODES:
        problemas.append(
            f"generation_mode desconocido: {modo!r}. Válidos: {list(GENERATION_MODES)}.")
        return problemas
    if modo == GENERATION_MODE_TEXT_TO_IMAGE:
        if request.source_image:
            problemas.append(
                "TEXT_TO_IMAGE no debe llevar source_image — así no puede confundirse "
                "con una edición. Si esta pieza necesita editar una imagen existente, "
                "el modo correcto es IMAGE_EDIT.")
        if request.edit_instruction:
            problemas.append("TEXT_TO_IMAGE no debe llevar edit_instruction.")
    elif modo == GENERATION_MODE_IMAGE_EDIT:
        if not request.source_image:
            problemas.append(
                "IMAGE_EDIT exige source_image explícito. No se infiere ni se hereda "
                "automáticamente de una generación anterior de la misma sesión o lote.")
    return problemas


@dataclass
class GenerationResult:
    provider_id: str
    model: str
    ok: bool
    image_bytes: bytes = b""
    width: int = 0
    height: int = 0
    mime_type: str = ""
    seed: int = None
    error: str = ""
    raw_meta: dict = field(default_factory=dict)


class ImageProvider:
    """Interfaz que todo adapter implementa. Sin estado compartido."""

    id = "abstract"

    def capabilities(self):
        raise NotImplementedError

    def generate(self, request):
        raise NotImplementedError


def negotiate(request, capabilities):
    """Negociacion de capacidades. Devuelve lista de incompatibilidades.

    Vacia = el proveedor puede atender la peticion. No degrada la peticion en
    silencio: prefiere rechazar a entregar algo distinto de lo pedido.
    """
    problemas = []
    if request.generation_mode == GENERATION_MODE_IMAGE_EDIT and not capabilities.supports_editing:
        problemas.append(
            f"{capabilities.provider_id}: no soporta IMAGE_EDIT — la petición exige editar "
            "una imagen existente y este proveedor sólo genera desde cero.")
    if capabilities.aspect_ratios and request.aspect_ratio not in capabilities.aspect_ratios:
        problemas.append(
            f"{capabilities.provider_id}: no soporta aspect ratio {request.aspect_ratio!r} "
            f"(soporta {list(capabilities.aspect_ratios)})."
        )
    if request.negative_prompt and not capabilities.supports_negative_prompt:
        problemas.append(
            f"{capabilities.provider_id}: no soporta negative prompt, y el brief declara "
            f"{len(request.negative_prompt.split(', '))} restricciones negativas que se perderian."
        )
    if request.seed is not None and not capabilities.supports_seed:
        problemas.append(f"{capabilities.provider_id}: no soporta seed; la generacion no seria reproducible.")
    if request.requires_text_rendering and not capabilities.supports_reliable_text:
        problemas.append(
            f"{capabilities.provider_id}: no tiene capacidad de texto demostrada y la peticion exige "
            "texto renderizado por el generador."
        )
    if capabilities.max_width and request.width > capabilities.max_width:
        problemas.append(f"{capabilities.provider_id}: ancho {request.width} > maximo {capabilities.max_width}.")
    if capabilities.max_height and request.height > capabilities.max_height:
        problemas.append(f"{capabilities.provider_id}: alto {request.height} > maximo {capabilities.max_height}.")
    return problemas
