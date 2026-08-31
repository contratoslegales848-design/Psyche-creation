"""QA estructural del asset generado.

Deliberadamente estructural, no estetico: comprueba lo que un programa puede
comprobar con certeza (formato, dimensiones, integridad, unicidad). El juicio
visual y la identidad de marca los aprueba un humano — el QA automatico nunca
los sustituye (CLAUDE.md §6, mandato §4).
"""

import hashlib
import struct
from dataclasses import dataclass, field

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


@dataclass
class QAReport:
    passed: bool = False
    asset_sha256: str = ""
    width: int = 0
    height: int = 0
    problemas: list = field(default_factory=list)
    avisos: list = field(default_factory=list)


def _png_size(data):
    """(w, h) leidos del IHDR real, no de lo que el proveedor dice."""
    if len(data) < 24 or not data.startswith(PNG_MAGIC) or data[12:16] != b"IHDR":
        return None
    return struct.unpack(">II", data[16:24])


def structural_qa(result, parametros, known_hashes=()):
    """Valida el resultado bruto contra lo que se pidio."""
    rep = QAReport()

    if result is None or not result.ok:
        rep.problemas.append(f"generacion fallida: {getattr(result, 'error', 'sin resultado')}")
        return rep

    data = result.image_bytes or b""
    if not data:
        rep.problemas.append("el proveedor devolvio un asset vacio.")
        return rep

    rep.asset_sha256 = hashlib.sha256(data).hexdigest()

    if result.mime_type != "image/png":
        rep.problemas.append(f"mime_type inesperado: {result.mime_type!r} (se esperaba image/png).")

    real = _png_size(data)
    if real is None:
        rep.problemas.append("el asset no es un PNG legible: cabecera corrupta.")
    else:
        rep.width, rep.height = real
        # Las dimensiones DECLARADAS por el proveedor son las que se comparan con
        # lo pedido; el PNG real solo tiene que ser coherente consigo mismo.
        if result.width <= 0 or result.height <= 0:
            rep.problemas.append(
                f"metadata invalida: el proveedor declara {result.width}x{result.height}."
            )
        else:
            pedido_ar = parametros.get("aspect_ratio")
            dec_ar = _ratio(result.width, result.height)
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
            f"asset duplicado: sha256 {rep.asset_sha256[:12]}... ya existe en el registro."
        )

    rep.passed = not rep.problemas
    return rep


def _ratio(w, h):
    from math import gcd
    if w <= 0 or h <= 0:
        return "0:0"
    g = gcd(w, h)
    return f"{w // g}:{h // g}"
