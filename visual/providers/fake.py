"""FakeImageProvider — proveedor de laboratorio.

Existe para que el pipeline completo se pueda ejercitar en CI sin credenciales,
sin red y sin gastar un solo credito (mandato §4 y §26). Produce un PNG minimo
real, de las dimensiones pedidas, y sabe simular fallos.
"""

import hashlib
import struct
import zlib

from .base import (
    ImageProvider, ProviderCapabilities, GenerationResult,
)

# Modos de fallo simulables.
MODOS = (
    "success",
    "provider_failure",
    "timeout",
    "wrong_dimensions",
    "corrupt_response",
    "duplicate_asset",
    "bad_metadata",
)


def _png(width, height, rgb):
    """PNG solido valido, escrito a mano para no depender de Pillow."""
    def chunk(tipo, data):
        c = tipo + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    fila = b"\x00" + bytes(rgb) * width
    idat = zlib.compress(fila * height, 9)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat) + chunk(b"IEND", b"")


class FakeImageProvider(ImageProvider):
    id = "fake"

    def __init__(self, modo="success", model="fake-v1", supports_reliable_text=False,
                 aspect_ratios=("9:16", "4:5")):
        if modo not in MODOS:
            raise ValueError(f"modo de simulacion desconocido: {modo!r} (uno de {list(MODOS)})")
        self.modo = modo
        self.model = model
        self._aspect_ratios = tuple(aspect_ratios)
        self._texto = supports_reliable_text
        self.llamadas = 0

    def capabilities(self):
        return ProviderCapabilities(
            provider_id=self.id,
            aspect_ratios=self._aspect_ratios,
            supports_negative_prompt=True,
            supports_reference_image=False,
            supports_editing=False,
            supports_reliable_text=self._texto,
            supports_seed=True,
            supports_transparency=False,
            max_width=4096,
            max_height=4096,
        )

    def generate(self, request):
        self.llamadas += 1
        base = dict(provider_id=self.id, model=self.model, seed=request.seed)

        if self.modo == "provider_failure":
            return GenerationResult(ok=False, error="el proveedor devolvio 500", **base)
        if self.modo == "timeout":
            return GenerationResult(ok=False, error="timeout de la peticion al proveedor", **base)
        if self.modo == "corrupt_response":
            return GenerationResult(
                ok=True, image_bytes=b"no-soy-un-png", width=request.width,
                height=request.height, mime_type="image/png", **base
            )
        if self.modo == "bad_metadata":
            return GenerationResult(
                ok=True, image_bytes=_png(8, 8, (43, 27, 23)), width=0, height=0,
                mime_type="", **base
            )

        w, h = (request.width, request.height)
        if self.modo == "wrong_dimensions":
            w, h = h, w  # devuelve la orientacion cambiada

        if self.modo == "duplicate_asset":
            # ignora el prompt: siempre el mismo pixel -> mismo hash
            data = _png(8, 8, (128, 128, 128))
        else:
            tono = hashlib.sha256(request.prompt.encode("utf-8")).digest()[:3]
            data = _png(8, 8, tuple(tono))

        return GenerationResult(
            ok=True, image_bytes=data, width=w, height=h, mime_type="image/png", **base
        )
