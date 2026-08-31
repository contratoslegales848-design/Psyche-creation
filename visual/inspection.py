"""QA semantica: contrato explicito + heuristicas honestas sobre pixels.

Distincion deliberada:

- HEURISTICA = una medida real sobre los pixels (luminancia, contraste,
  dominancia calida). Es cierta, y es poco. Puede pedir revision humana.
- COMPRENSION VISUAL = saber si hay un collage, si la marca esta bien integrada,
  si una mano tiene seis dedos. NO existe en este repositorio. No se finge.

Por eso el inspector por defecto es NOOP y devuelve NOT_EVALUATED.
"""

import struct
import zlib
from dataclasses import dataclass, field

PASS = "PASS"
FAIL = "FAIL"
NEEDS_HUMAN_REVIEW = "NEEDS_HUMAN_REVIEW"
NOT_EVALUATED = "NOT_EVALUATED"

# Umbrales de las heuristicas. Conservadores: prefieren pedir revision a rechazar.
LUMINANCIA_BAJA = 0.18
NEAR_BLACK = 0.06
RATIO_NEAR_BLACK_ALTO = 0.72
CONTRASTE_BAJO = 0.10
SEPIA_RATIO = 0.55


@dataclass
class SemanticReport:
    state: str = NOT_EVALUATED
    inspector: str = "noop"
    reason_codes: list = field(default_factory=list)
    metrics: dict = field(default_factory=dict)
    notes: list = field(default_factory=list)


class SemanticVisualInspector:
    """Interfaz. Toda implementacion futura (vision real) cumple esto."""

    id = "abstract"

    def inspect(self, image_bytes, expectations=None):
        raise NotImplementedError


class NoopSemanticInspector(SemanticVisualInspector):
    """Por defecto. No mira nada y lo dice."""

    id = "noop"

    def inspect(self, image_bytes, expectations=None):
        return SemanticReport(
            state=NOT_EVALUATED, inspector=self.id,
            notes=["no hay inspector semantico real disponible en este repositorio."])


class HeuristicSemanticInspector(SemanticVisualInspector):
    """Mide lo medible. No afirma entender la imagen."""

    id = "heuristic"

    def inspect(self, image_bytes, expectations=None):
        px = decode_png_rgb(image_bytes)
        if px is None:
            return SemanticReport(
                state=NOT_EVALUATED, inspector=self.id,
                notes=["PNG no decodificable por el decodificador minimo; sin medida."])

        m = pixel_metrics(px)
        codes = []
        if m["avg_luminance"] < LUMINANCIA_BAJA:
            codes.append("DARKNESS_RISK")
        if m["near_black_ratio"] > RATIO_NEAR_BLACK_ALTO:
            codes.append("DARKNESS_RISK")
        if m["contrast"] < CONTRASTE_BAJO:
            codes.append("LOW_CONTRAST_RISK")
        if m["warm_dominance"] > SEPIA_RATIO:
            codes.append("SEPIA_DOMINANCE_RISK")

        codes = sorted(set(codes))
        # Una heuristica NUNCA rechaza sola: escala a humano.
        state = NEEDS_HUMAN_REVIEW if codes else PASS
        return SemanticReport(state=state, inspector=self.id, reason_codes=codes, metrics=m,
                              notes=["heuristicas sobre pixels; no equivalen a comprension visual."])


class FakeSemanticInspector(SemanticVisualInspector):
    """Solo para pruebas: devuelve el estado que se le pida."""

    id = "fake"

    def __init__(self, state=PASS, reason_codes=()):
        self._state, self._codes = state, list(reason_codes)

    def inspect(self, image_bytes, expectations=None):
        return SemanticReport(state=self._state, inspector=self.id,
                              reason_codes=list(self._codes),
                              notes=["inspector de laboratorio, sin valor probatorio."])


# --- decodificador PNG minimo (los 5 filtros), sin dependencias ---

def decode_png_rgb(data):
    """Devuelve lista de (r,g,b) o None si no se puede decodificar con certeza."""
    try:
        if not data or not data.startswith(b"\x89PNG\r\n\x1a\n"):
            return None
        pos, w, h, bitd, ct, idat = 8, 0, 0, 0, 0, b""
        while pos + 8 <= len(data):
            ln = struct.unpack(">I", data[pos:pos + 4])[0]
            tipo = data[pos + 4:pos + 8]
            cuerpo = data[pos + 8:pos + 8 + ln]
            if tipo == b"IHDR":
                w, h, bitd, ct = struct.unpack(">IIBB", cuerpo[:10])
            elif tipo == b"IDAT":
                idat += cuerpo
            elif tipo == b"IEND":
                break
            pos += 12 + ln
        if not idat or bitd != 8 or ct not in (2, 6) or w <= 0 or h <= 0:
            return None   # solo RGB/RGBA de 8 bits; lo demas: sin medida, no adivinar
        canales = 3 if ct == 2 else 4
        raw = zlib.decompress(idat)
        stride = w * canales
        out, prev = [], bytearray(stride)
        i = 0
        for _ in range(h):
            if i >= len(raw):
                return None
            f = raw[i]; i += 1
            linea = bytearray(raw[i:i + stride]); i += stride
            if len(linea) < stride:
                return None
            for x in range(stride):
                a = linea[x - canales] if x >= canales else 0
                b = prev[x]
                c = prev[x - canales] if x >= canales else 0
                if f == 1:
                    linea[x] = (linea[x] + a) & 0xFF
                elif f == 2:
                    linea[x] = (linea[x] + b) & 0xFF
                elif f == 3:
                    linea[x] = (linea[x] + (a + b) // 2) & 0xFF
                elif f == 4:
                    p = a + b - c
                    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                    pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                    linea[x] = (linea[x] + pr) & 0xFF
                elif f != 0:
                    return None
            for x in range(0, stride, canales):
                out.append((linea[x], linea[x + 1], linea[x + 2]))
            prev = linea
        return out or None
    except Exception:
        return None


def pixel_metrics(pixels):
    n = len(pixels)
    lum = [(0.2126 * r + 0.7152 * g + 0.0722 * b) / 255.0 for r, g, b in pixels]
    avg = sum(lum) / n
    near_black = sum(1 for l in lum if l < NEAR_BLACK) / n
    lo, hi = min(lum), max(lum)
    warm = sum(1 for r, g, b in pixels if r > b + 18 and g > b + 8) / n
    return {
        "pixels_muestreados": n,
        "avg_luminance": round(avg, 4),
        "near_black_ratio": round(near_black, 4),
        "contrast": round(hi - lo, 4),
        "warm_dominance": round(warm, 4),
    }
