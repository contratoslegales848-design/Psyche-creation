"""QA estructural del asset generado.

Deliberadamente estructural, no estetico: comprueba lo que un programa puede
comprobar con certeza (existencia, tamaño, MIME real frente al declarado,
dimensiones, integridad, unicidad, coherencia de identificadores). El juicio
visual y la identidad de marca los aprueba un humano.
"""

import hashlib
import struct
from dataclasses import dataclass, field
from math import gcd

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
JPEG_MAGIC = b"\xff\xd8"


@dataclass
class QAReport:
    passed: bool = False
    asset_sha256: str = ""
    width: int = 0
    height: int = 0
    detected_mime: str = ""
    problemas: list = field(default_factory=list)
    avisos: list = field(default_factory=list)

    def to_dict(self):
        return {"passed": self.passed, "asset_sha256": self.asset_sha256,
                "width": self.width, "height": self.height,
                "detected_mime": self.detected_mime,
                "problemas": list(self.problemas), "avisos": list(self.avisos)}


def sniff(data):
    """MIME REAL segun los bytes, no segun lo que diga el proveedor."""
    if data.startswith(PNG_MAGIC):
        return "image/png"
    if data.startswith(JPEG_MAGIC):
        return "image/jpeg"
    return ""


def _png_size(data):
    if len(data) < 24 or not data.startswith(PNG_MAGIC) or data[12:16] != b"IHDR":
        return None
    return struct.unpack(">II", data[16:24])


def _jpeg_size(data):
    """Recorre los segmentos hasta el SOF. Sin adivinar."""
    i = 2
    while i + 9 < len(data):
        if data[i] != 0xFF:
            return None
        marker = data[i + 1]
        if marker in (0xD8, 0xD9):
            i += 2
            continue
        ln = struct.unpack(">H", data[i + 2:i + 4])[0]
        if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
            h, w = struct.unpack(">HH", data[i + 5:i + 9])
            return (w, h)
        i += 2 + ln
    return None


def real_dimensions(data):
    m = sniff(data)
    if m == "image/png":
        return _png_size(data)
    if m == "image/jpeg":
        return _jpeg_size(data)
    return None


def ratio(w, h):
    if w <= 0 or h <= 0:
        return "0:0"
    g = gcd(w, h)
    return f"{w // g}:{h // g}"


def structural_qa(result, parametros, known_hashes=(), receipt=None):
    """Valida el resultado bruto contra lo que se pidio."""
    rep = QAReport()

    if result is None or not result.ok:
        rep.problemas.append(f"generacion fallida: {getattr(result, 'error', 'sin resultado')}")
        return rep

    data = result.image_bytes or b""
    if not data:
        rep.problemas.append("el proveedor devolvio un asset vacio (cero bytes).")
        return rep

    rep.asset_sha256 = hashlib.sha256(data).hexdigest()
    rep.detected_mime = sniff(data)

    if not rep.detected_mime:
        rep.problemas.append("los bytes no corresponden a ningun formato de imagen reconocido.")
    elif result.mime_type and result.mime_type != rep.detected_mime:
        rep.problemas.append(
            f"MIME declarado {result.mime_type!r} no coincide con los bytes reales "
            f"({rep.detected_mime!r})."
        )

    real = real_dimensions(data)
    if real is None:
        if rep.detected_mime:
            rep.problemas.append(f"cabecera {rep.detected_mime} ilegible: no se pueden leer dimensiones.")
    else:
        rep.width, rep.height = real

    if result.width <= 0 or result.height <= 0:
        rep.problemas.append(f"metadata invalida: el proveedor declara {result.width}x{result.height}.")
    else:
        pedido_ar = parametros.get("aspect_ratio")
        dec_ar = ratio(result.width, result.height)
        if pedido_ar and dec_ar != pedido_ar:
            rep.problemas.append(
                f"aspect ratio entregado {dec_ar} != pedido {pedido_ar} "
                f"({result.width}x{result.height} frente a "
                f"{parametros.get('width')}x{parametros.get('height')})."
            )
        if (result.width, result.height) != (parametros.get("width"), parametros.get("height")):
            rep.avisos.append(
                f"dimensiones {result.width}x{result.height} distintas de las pedidas "
                f"{parametros.get('width')}x{parametros.get('height')}."
            )

    if rep.asset_sha256 in set(known_hashes):
        rep.problemas.append(
            f"asset duplicado: sha256 {rep.asset_sha256[:12]}... ya existe en el registro.")

    # Coherencia de identificadores contra el receipt que dice describirlo.
    if receipt is not None:
        if getattr(receipt, "content_id", None) and parametros.get("content_id") \
                and receipt.content_id != parametros["content_id"]:
            rep.problemas.append("el receipt apunta a un CONTENT_ID distinto del generado.")
        if getattr(receipt, "asset_sha256", "") and receipt.asset_sha256 != rep.asset_sha256:
            rep.problemas.append("asset hash mismatch entre receipt y asset.")

    rep.passed = not rep.problemas
    return rep
