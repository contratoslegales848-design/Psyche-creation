"""Nucleo agnostico al proveedor.

El dominio de LegalMente NUNCA conoce a OpenAI, Grok, Gemini, Higgsfield, Flux,
Stable Diffusion ni Ideogram. Habla este contrato. Cada adapter traduce en su
propio archivo (mandato §24, §25).
"""

from dataclasses import dataclass, field


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
    """Peticion en el vocabulario de LegalMente, no en el de un proveedor."""

    content_id: str
    prompt: str
    negative_prompt: str
    width: int
    height: int
    aspect_ratio: str
    seed: int = None
    requires_text_rendering: bool = False
    metadata: dict = field(default_factory=dict)


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
