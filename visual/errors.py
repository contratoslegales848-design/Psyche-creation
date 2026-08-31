"""Taxonomia de errores del pipeline visual.

Errores especificos en vez de genericos: el que los captura sabe QUE fallo y
puede decidir si reintentar, bloquear o escalar a humano.
"""


class VisualError(Exception):
    """Raiz de todo error del subsistema visual."""


class VisualGateClosedError(VisualError):
    """El gate de arte no autoriza producir. Nunca se reintenta automaticamente."""


class VisualInputInvalidError(VisualError):
    """El input canonico no es legible o esta incompleto. Fail-closed."""


class VisualPolicyViolationError(VisualError):
    """El brief contradice la politica visual vigente."""


class ProviderCapabilityError(VisualError):
    """El proveedor no puede atender la peticion sin degradar una regla esencial."""


class ProviderExecutionError(VisualError):
    """El proveedor fallo al ejecutar (red, 5xx, timeout, rate limit)."""


class AssetIntegrityError(VisualError):
    """El asset no coincide con lo pedido o esta corrupto."""


class ReceiptIntegrityError(VisualError):
    """Un receipt no es coherente consigo mismo ni con el asset que dice describir."""


class DuplicateGenerationError(VisualError):
    """Se intento repetir una generacion ya realizada sin intencion explicita."""


class VisualQAError(VisualError):
    """El QA estructural rechazo el asset."""


class StoragePathError(VisualError):
    """Ruta de almacenamiento insegura o fuera de la raiz permitida."""
