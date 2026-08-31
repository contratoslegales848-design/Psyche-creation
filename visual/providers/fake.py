"""FakeImageProvider — proveedor de laboratorio.

Existe para ejercitar el pipeline completo en CI sin credenciales, sin red y sin
gastar un credito. Produce archivos REALES (PNG valido; JPEG con cabecera
valida) de las dimensiones pedidas, y simula deterministicamente los fallos que
un proveedor real comete.

Limite declarado: el JPEG que emite tiene cabecera correcta (magic, SOF0 con
dimensiones reales) pero su scan no es una imagen decodificable. Sirve para
probar MIME, extension, dimensiones, checksum y corrupcion — no para mirarlo.
"""

import hashlib
import struct
import zlib

from .base import ImageProvider, ProviderCapabilities, GenerationResult

MODOS = (
    "success",
    "provider_failure",
    "timeout",
    "rate_limit",
    "empty_result",
    "zero_byte",
    "corrupt_response",
    "bad_mime",
    "wrong_dimensions",
    "duplicate_asset",
    "bad_metadata",
)


def png_bytes(width, height, rgb):
    """PNG solido valido, escrito a mano para no depender de Pillow."""
    def chunk(tipo, data):
        c = tipo + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    fila = b"\x00" + bytes(rgb) * width
    idat = zlib.compress(fila * height, 9)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat) + chunk(b"IEND", b"")


def jpeg_bytes(width, height):
    """JPEG de cabecera valida: SOI + APP0/JFIF + SOF0(dims reales) + EOI."""
    soi = b"\xff\xd8"
    app0 = b"\xff\xe0" + struct.pack(">H", 16) + b"JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
    sof0 = (b"\xff\xc0" + struct.pack(">H", 17) + b"\x08"
            + struct.pack(">HH", height, width)
            + b"\x03\x01\x11\x00\x02\x11\x01\x03\x11\x01")
    return soi + app0 + sof0 + b"\xff\xd9"


class FakeImageProvider(ImageProvider):
    id = "fake"

    def __init__(self, modo="success", model="fake-v1", supports_reliable_text=False,
                 aspect_ratios=("9:16", "4:5"), fmt="png", fail_on=()):
        if modo not in MODOS:
            raise ValueError(f"modo de simulacion desconocido: {modo!r} (uno de {list(MODOS)})")
        self.modo = modo
        self.model = model
        self._aspect_ratios = tuple(aspect_ratios)
        self._texto = supports_reliable_text
        self.fmt = fmt
        # fail_on: content_ids que deben fallar (fallo parcial de lote).
        self.fail_on = set(fail_on)
        self.llamadas = 0
        self.llamadas_por_content = {}

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
        self.llamadas_por_content[request.content_id] = \
            self.llamadas_por_content.get(request.content_id, 0) + 1
        base = dict(provider_id=self.id, model=self.model, seed=request.seed)

        modo = "provider_failure" if request.content_id in self.fail_on else self.modo

        if modo == "provider_failure":
            return GenerationResult(ok=False, error="el proveedor devolvio 500", **base)
        if modo == "timeout":
            return GenerationResult(ok=False, error="timeout de la peticion al proveedor", **base)
        if modo == "rate_limit":
            return GenerationResult(ok=False, error="429 rate limit del proveedor", **base)
        if modo == "empty_result":
            return GenerationResult(ok=True, image_bytes=b"", width=request.width,
                                    height=request.height, mime_type="image/png", **base)
        if modo == "zero_byte":
            return GenerationResult(ok=True, image_bytes=b"", width=0, height=0,
                                    mime_type="image/png", **base)
        if modo == "corrupt_response":
            return GenerationResult(ok=True, image_bytes=b"no-soy-un-png",
                                    width=request.width, height=request.height,
                                    mime_type="image/png", **base)
        if modo == "bad_mime":
            # Extension/MIME que no concuerda con los bytes entregados.
            return GenerationResult(ok=True, image_bytes=png_bytes(8, 8, (43, 27, 23)),
                                    width=request.width, height=request.height,
                                    mime_type="image/jpeg", **base)
        if modo == "bad_metadata":
            return GenerationResult(ok=True, image_bytes=png_bytes(8, 8, (43, 27, 23)),
                                    width=0, height=0, mime_type="", **base)

        w, h = request.width, request.height
        if modo == "wrong_dimensions":
            w, h = h, w

        if self.fmt == "jpeg":
            data, mime = jpeg_bytes(8, 8), "image/jpeg"
        elif modo == "duplicate_asset":
            data, mime = png_bytes(8, 8, (128, 128, 128)), "image/png"
        else:
            tono = hashlib.sha256(request.prompt.encode("utf-8")).digest()[:3]
            data, mime = png_bytes(8, 8, tuple(tono)), "image/png"

        return GenerationResult(ok=True, image_bytes=data, width=w, height=h,
                                mime_type=mime, **base)
