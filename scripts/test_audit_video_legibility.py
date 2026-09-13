"""Pruebas de la medida de legibilidad del video.

Sin renderizar nada: el render de Remotion se prueba renderizando, y eso ya se
hizo a mano. Lo que se prueba aquí es la parte que puede equivocarse en silencio
— qué píxeles cuenta como trazo, qué contraste les asigna y cuándo declara que
el texto se sale de la zona segura — con fotogramas sintéticos donde la
respuesta correcta se conoce de antemano.
"""

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "visual"))

from PIL import Image  # noqa: E402

from brief import VisualPolicy  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "audit_video_legibility", REPO / "scripts" / "audit-video-legibility.py")
audit = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(audit)

POLICY = VisualPolicy.load()
MARFIL = (252, 250, 242)
LATON = (197, 160, 89)
NOGAL = (30, 20, 18)


def fotogramas(directorio, fondo, caja, color=MARFIL, sombra=False):
    """Par (con texto, sin texto) sintético: un bloque de color sobre un fondo.

    Con `sombra=True` se añade un halo oscuro alrededor del bloque, como el
    `textShadow` real: la medida no debe contarlo como trazo.
    """
    sin = Image.new("RGB", (1080, 1920), fondo)
    con = sin.copy()
    x0, y0, x1, y1 = caja
    if sombra:
        for x in range(max(0, x0 - 6), min(1080, x1 + 6)):
            for y in range(max(0, y0 - 6), min(1920, y1 + 6)):
                con.putpixel((x, y), tuple(int(c * 0.4) for c in fondo))
    for x in range(x0, x1):
        for y in range(y0, y1):
            con.putpixel((x, y), color)
    a, b = Path(directorio) / "con.png", Path(directorio) / "sin.png"
    con.save(a)
    sin.save(b)
    return a, b


class TestMedidaDeTrazo(unittest.TestCase):
    def medir(self, fondo, caja=(100, 400, 500, 500), color=MARFIL, sombra=False):
        with tempfile.TemporaryDirectory() as d:
            a, b = fotogramas(d, fondo, caja, color, sombra)
            return audit.medir(a, b, [MARFIL, LATON], 4.5, 7.0)

    def test_marfil_sobre_nogal_contrasta_de_sobra(self):
        m = self.medir(NOGAL)
        self.assertGreater(m["contraste_minimo"], 7.0)
        self.assertEqual(m["fraccion_bajo_minimo"], 0.0)

    def test_marfil_sobre_fondo_claro_no_llega_al_minimo(self):
        m = self.medir((245, 243, 236))
        self.assertLess(m["contraste_minimo"], 4.5)
        self.assertEqual(m["fraccion_bajo_minimo"], 1.0)

    def test_la_sombra_de_texto_no_se_cuenta_como_trazo(self):
        """Contar el halo maquillaría la medida: el halo siempre 'contrasta'."""
        caja = (100, 400, 500, 500)
        sin_halo = self.medir(NOGAL, caja)
        con_halo = self.medir(NOGAL, caja, sombra=True)
        self.assertEqual(sin_halo["pixeles_de_trazo"], con_halo["pixeles_de_trazo"])

    def test_la_caja_del_texto_es_la_del_trazo(self):
        m = self.medir(NOGAL, (120, 300, 900, 1600))
        self.assertEqual(m["caja_del_texto"], [120, 300, 899, 1599])

    def test_fondo_sin_texto_no_devuelve_medida(self):
        with tempfile.TemporaryDirectory() as d:
            sin = Image.new("RGB", (64, 64), NOGAL)
            a, b = Path(d) / "a.png", Path(d) / "b.png"
            sin.save(a)
            sin.save(b)
            self.assertIsNone(audit.medir(a, b, [MARFIL, LATON], 4.5, 7.0))


class TestGeometria(unittest.TestCase):
    """La zona segura sale de la política: si el texto se sale, se dice."""

    def caja_dentro(self, caja):
        (sx, sy, sw, sh), _ = audit.safe_area_para(1080, 1920, POLICY)
        h = audit.TOLERANCIA_BORDE_PX
        x0, y0, x1, y1 = caja
        return (x0 >= sx - h and y0 >= sy - h and x1 <= sx + sw + h and y1 <= sy + sh + h)

    def test_el_encuadre_anterior_del_video_se_habria_detectado(self):
        """Padding de 130 px arriba: el título caía en la franja recortada."""
        self.assertFalse(self.caja_dentro([79, 130, 998, 1830]))

    def test_el_encuadre_actual_pasa(self):
        self.assertTrue(self.caja_dentro([79, 306, 998, 1631]))

    def test_la_holgura_no_tapa_un_desbordamiento_real(self):
        self.assertTrue(self.caja_dentro([80, 289, 1000, 1631]))     # antialias
        self.assertFalse(self.caja_dentro([80, 270, 1000, 1631]))    # 20 px fuera


if __name__ == "__main__":
    unittest.main()
