"""Preflight de proveedor real, y preparacion de la peticion — sin ejecutarla.

No inventa un vendor: no hay SDK ni credencial de ningun proveedor de imagen
instalados en este entorno (verificado: `pip list`, variables de entorno). Lo
unico honesto que existe hoy es `providers.HttpImageProvider`, generico. Este
modulo construye un `HttpProviderConfig` de ejemplo (perfil, no vendor real) y
usa el compilador YA existente (`compiler.compile_request`) para producir la
peticion normalizada completa de PIEZA-01 — nunca la envia.

Nunca imprime ni registra un valor de credencial: solo si la variable de
entorno declarada existe (booleano).
"""

import os
from dataclasses import dataclass, field

from providers.http_provider import HttpProviderConfig

# Perfil de ejemplo: NO es un vendor real, es la forma minima que cualquier
# API HTTP de imagen compatible necesitaria. auth_env es deliberadamente
# generico — un despliegue real reemplaza esto por su propio perfil.
DEFAULT_PROFILE = HttpProviderConfig(
    provider_id="generic-http-image-v1",
    endpoint=os.environ.get("LEGALMENTE_IMAGE_PROVIDER_ENDPOINT", ""),
    api_key_env="LEGALMENTE_IMAGE_PROVIDER_API_KEY",
    aspect_ratios=("9:16",),
)

READY = "READY"
MISSING_CREDENTIALS = "MISSING_CREDENTIALS"
INVALID_CONFIG = "INVALID_CONFIG"
UNSUPPORTED_CAPABILITY = "UNSUPPORTED_CAPABILITY"


@dataclass
class PreflightResult:
    provider_id: str
    status: str
    auth_present: bool = False
    endpoint_configured: bool = False
    capabilities: dict = field(default_factory=dict)
    blocking_reason: str = ""
    live_allowed: bool = False  # nunca True por defecto; requiere --live explicito en el caller

    def to_dict(self):
        return {
            "provider_id": self.provider_id,
            "status": self.status,
            "auth_present": self.auth_present,
            "endpoint_configured": self.endpoint_configured,
            "capabilities": dict(self.capabilities),
            "blocking_reason": self.blocking_reason,
            "live_allowed": self.live_allowed,
        }


def preflight(config=None):
    """Comprueba si el proveedor podria ejecutarse, sin ejecutarlo jamas.

    auth_present es un booleano: si la variable de entorno declarada por el
    perfil existe. El valor de la credencial nunca se lee para nada mas que
    esta comprobacion, y nunca se devuelve.
    """
    cfg = config or DEFAULT_PROFILE
    auth_present = bool(os.environ.get(cfg.api_key_env)) if cfg.api_key_env else False
    endpoint_configured = bool(cfg.endpoint)

    caps = {
        "aspect_ratios": list(cfg.aspect_ratios),
        "supports_negative_prompt": cfg.supports_negative_prompt,
        "supports_seed": cfg.supports_seed,
        "supports_reference_image": cfg.supports_reference_image,
        "max_width": cfg.max_width,
        "max_height": cfg.max_height,
    }

    if not endpoint_configured:
        return PreflightResult(cfg.provider_id, INVALID_CONFIG, auth_present, endpoint_configured,
                                caps, "endpoint no configurado (LEGALMENTE_IMAGE_PROVIDER_ENDPOINT ausente).")
    if not auth_present:
        return PreflightResult(cfg.provider_id, MISSING_CREDENTIALS, auth_present, endpoint_configured,
                                caps, f"credencial ausente: variable de entorno {cfg.api_key_env!r} no definida.")
    return PreflightResult(cfg.provider_id, READY, auth_present, endpoint_configured, caps, "")


def build_pieza01_request(brief, policy, family, capabilities):
    """Peticion normalizada COMPLETA para PIEZA-01, lista para inspeccionar.

    Reusa compiler.compile_request tal cual — no reimplementa compilacion de
    prompt. requires_paid_execution es siempre True: no existe proveedor
    gratuito registrado en este sistema.
    """
    import compiler as compiler_mod

    compiled = compiler_mod.compile_request(brief, policy, family=family, capabilities=capabilities)
    return {
        "content_id": brief.content_id,
        "provider_id": capabilities.provider_id if capabilities else DEFAULT_PROFILE.provider_id,
        "model_id": None,
        "compiled_prompt": compiled.positive_prompt,
        "negative_constraints": list(compiled.negative_constraints),
        "aspect_ratio": compiled.requested_aspect_ratio,
        "dimensions": list(compiled.requested_dimensions),
        "seed": compiled.provider_parameters.get("seed"),
        "reference_inputs": [],
        "request_hash": compiled.request_hash(),
        "estimated_cost": "UNKNOWN",
        "requires_paid_execution": True,
        "live_execution_attempted": False,
        "generator_writes_exact_copy": False,
        "generator_writes_legalmente": False,
    }
