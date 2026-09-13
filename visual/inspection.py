"""QA semantica: contrato explicito + heuristicas honestas sobre pixels.

Distincion deliberada:

- HEURISTICA = una medida real sobre los pixels (luminancia, contraste,
  dominancia calida). Es cierta, y es poco. Puede pedir revision humana.
- COMPRENSION VISUAL = saber si hay un collage, si la marca esta bien integrada,
  si una mano tiene seis dedos. NO existe en este repositorio. No se finge.

Por eso el inspector por defecto es NOOP y devuelve NOT_EVALUATED.

`ArtDetailInspector` (añadido con la politica 1.2) sigue siendo heuristica, pero
mide lo que la politica visual declara PROHIBIDO o EXIGIDO y hasta ahora nadie
comprobaba sobre los pixels: negros empastados ("negros sin detalle"), pieza
excesivamente oscura, dominancia sepia, ausencia del acento frio que la marca
exige como objeto fisico, deriva de la paleta institucional y rango tonal plano.
Sigue sin entender la imagen y sigue sin rechazar sola: escala a revision humana.
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


class ArtDetailInspector(SemanticVisualInspector):
    """Detalle artistico medible sobre los pixels, contra la politica vigente.

    Usa Pillow (ya es dependencia del compositor, ADR 0003), asi que tambien lee
    JPEG y cualquier modo de color, a diferencia del decodificador minimo de
    `HeuristicSemanticInspector`. Submuestrea a `lado` px: el juicio es de
    distribucion de color y tono, no de nitidez, y muestrear entero seria pagar
    segundos por ninguna informacion adicional.

    Nunca rechaza. Devuelve PASS o NEEDS_HUMAN_REVIEW.
    """

    id = "art_detail"

    def __init__(self, policy=None, lado=160):
        if policy is None:
            from brief import VisualPolicy
            policy = VisualPolicy.load()
        self.policy = policy
        self.lado = int(lado)
        paleta = policy.data.get("paleta", {})
        self._anclas = [hex_a_rgb(h) for tonos in (paleta.get("requerida") or {}).values()
                        for h in tonos]
        self._anclas = [a for a in self._anclas if a]
        self._frias = [hex_a_rgb(h) for h in (paleta.get("requerida") or {}).get("azul_petroleo", [])]
        self._frias = [a for a in self._frias if a]
        self._umbrales = paleta.get("adherencia") or {}

    def inspect(self, image_bytes, expectations=None):
        try:
            from PIL import Image
            import io
            img = Image.open(io.BytesIO(image_bytes))
            img.load()
            img = img.convert("RGB")
        except Exception as exc:
            return SemanticReport(
                state=NOT_EVALUATED, inspector=self.id,
                notes=[f"asset no legible como imagen: {exc}. Sin medida, no se inventa una."])

        lado = max(8, self.lado)
        muestra = img.copy()
        muestra.thumbnail((lado, lado))
        px = muestra.load()
        pixels = [px[x, y] for y in range(muestra.height) for x in range(muestra.width)]
        m = pixel_metrics(pixels)
        m.update(art_metrics(pixels, self._anclas, self._frias,
                             int(self._umbrales.get("tolerancia_rgb", 64))))

        codes = []
        if m["avg_luminance"] < LUMINANCIA_BAJA:
            codes.append("DARKNESS_RISK")
        if m["near_black_ratio"] > RATIO_NEAR_BLACK_ALTO:
            codes.append("DARKNESS_RISK")
        if m["contrast"] < CONTRASTE_BAJO:
            codes.append("LOW_CONTRAST_RISK")
        if m["warm_dominance"] > SEPIA_RATIO:
            codes.append("SEPIA_DOMINANCE_RISK")
        # "negros sin detalle" esta PROHIBIDO por la politica de paleta: no es una
        # preferencia, es una regla, y hasta ahora no se medía.
        if m["clipped_black_ratio"] > float(self._umbrales.get("negro_empastado_maximo", 0.12)):
            codes.append("BLACK_CLIPPING_RISK")
        if m["clipped_white_ratio"] > 0.02:
            codes.append("HIGHLIGHT_CLIPPING_RISK")
        # La marca exige que el acento frio venga de un objeto fisico real: si no
        # hay un solo pixel frio, ese objeto no llego a la imagen.
        if m["cold_accent_ratio"] < float(self._umbrales.get("acento_frio_minimo_pixeles", 0.005)):
            codes.append("COLD_ACCENT_ABSENT")
        if m["palette_adherence"] < float(self._umbrales.get("minimo_pixeles_en_paleta", 0.35)):
            codes.append("PALETTE_DRIFT_RISK")
        if m["tonal_spread"] < 0.25:
            codes.append("FLAT_TONAL_RANGE_RISK")

        codes = sorted(set(codes))
        return SemanticReport(
            state=NEEDS_HUMAN_REVIEW if codes else PASS, inspector=self.id,
            reason_codes=codes, metrics=m,
            notes=["medidas de color y tono contra la politica visual vigente; no equivalen a "
                   "comprension visual y nunca rechazan solas."])


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


def hex_a_rgb(valor):
    v = str(valor or "").strip().lstrip("#")
    if len(v) != 6:
        return None
    try:
        return tuple(int(v[i:i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        return None


def _distancia(a, b):
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2) ** 0.5


def art_metrics(pixels, anclas_paleta=(), anclas_frias=(), tolerancia=64):
    """Medidas de detalle artistico. Todas comprobables a mano sobre la imagen."""
    n = len(pixels)
    lum = sorted((0.2126 * r + 0.7152 * g + 0.0722 * b) / 255.0 for r, g, b in pixels)
    p05 = lum[int(0.05 * (n - 1))]
    p95 = lum[int(0.95 * (n - 1))]
    clipped_black = sum(1 for r, g, b in pixels if max(r, g, b) <= 6) / n
    clipped_white = sum(1 for r, g, b in pixels if min(r, g, b) >= 250) / n
    frio = sum(1 for r, g, b in pixels if b > r + 10 and b > g + 5) / n
    if anclas_paleta:
        en_paleta = sum(1 for p in pixels
                        if min(_distancia(p, a) for a in anclas_paleta) <= tolerancia) / n
    else:
        en_paleta = 0.0
    if anclas_frias:
        frio_paleta = sum(1 for p in pixels
                          if min(_distancia(p, a) for a in anclas_frias) <= tolerancia * 1.5) / n
    else:
        frio_paleta = 0.0
    return {
        "clipped_black_ratio": round(clipped_black, 4),
        "clipped_white_ratio": round(clipped_white, 4),
        "cold_accent_ratio": round(max(frio, frio_paleta), 4),
        "cold_accent_en_paleta": round(frio_paleta, 4),
        "palette_adherence": round(en_paleta, 4),
        "tonal_spread": round(p95 - p05, 4),
    }


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
