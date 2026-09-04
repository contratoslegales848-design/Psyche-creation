"""El motor de imagen no puede generar arte de un claim sin verificar.

El riesgo que cubren estas pruebas no es tecnico, es de gobernanza. El dia que
haya creditos, la tentacion sera generar; y un proveedor que genera en cuanto
puede pagar habria convertido el presupuesto en una autorizacion.

Tambien fijan la honestidad del estado: sin creditos y sin despachador, el
proveedor dice que NO genero, en vez de devolver un resultado vacio que parezca
un fallo transitorio.

Sin red. Determinista.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from providers.base import NormalizedImageRequest, ProviderError  # noqa: E402
from providers.higgsfield import (  # noqa: E402
    GATE_CERRADO, MODELO_POR_DEFECTO, MODELOS, PENDIENTE_DE_DESPACHO, SIN_CREDITOS,
    EstadoDeCuenta, HiggsfieldProvider, modelo_recomendado_para,
)


def _req(**extra):
    base = dict(content_id="LM-TEST", prompt="escena editorial sobria",
                negative_prompt="texto deformado", width=1080, height=1920,
                aspect_ratio="9:16", seed=None, requires_text_rendering=True,
                metadata={})
    base.update(extra)
    return NormalizedImageRequest(**base)


def _despachador_ok(payload):
    return {"image_bytes": b"PNGDATA", "width": 1080, "height": 1920,
            "mime_type": "image/png", "url": "https://ejemplo/imagen.png"}


class TestElGateManda(unittest.TestCase):
    def test_con_el_gate_cerrado_no_se_genera_ni_se_prepara(self):
        """El control central: ni siquiera se construye la peticion."""
        r = HiggsfieldProvider().generate(_req())
        self.assertFalse(r.ok)
        self.assertEqual(r.error, GATE_CERRADO)
        self.assertEqual(r.raw_meta["payload"], {})

    def test_el_gate_cerrado_manda_incluso_con_creditos_y_despachador(self):
        """Tener presupuesto no es una razon para generar."""
        p = HiggsfieldProvider(cuenta=EstadoDeCuenta(creditos=9999, plan="pro"),
                               despachador=_despachador_ok)
        r = p.generate(_req(), gate_arte="CERRADO")
        self.assertFalse(r.ok)
        self.assertEqual(r.error, GATE_CERRADO)

    def test_el_gate_por_defecto_esta_cerrado(self):
        """Un proveedor al que se le olvide preguntarlo no genera nada."""
        p = HiggsfieldProvider(cuenta=EstadoDeCuenta(creditos=100),
                               despachador=_despachador_ok)
        self.assertFalse(p.generate(_req()).ok)


class TestEstadoRealDeLaCuenta(unittest.TestCase):
    def test_sin_creditos_lo_dice_en_vez_de_fingir_un_fallo(self):
        p = HiggsfieldProvider(cuenta=EstadoDeCuenta(creditos=0, plan="free"))
        r = p.generate(_req(), gate_arte="ABIERTO")
        self.assertFalse(r.ok)
        self.assertEqual(r.error, SIN_CREDITOS)
        self.assertTrue(any("falta presupuesto, no codigo" in n
                            for n in r.raw_meta["notas"]))

    def test_sin_creditos_la_peticion_ya_queda_preparada(self):
        """Que no haya presupuesto no debe costar trabajo de mas manana."""
        p = HiggsfieldProvider(cuenta=EstadoDeCuenta(creditos=0))
        r = p.generate(_req(), gate_arte="ABIERTO")
        self.assertEqual(r.raw_meta["payload"]["aspect_ratio"], "9:16")
        self.assertEqual(r.raw_meta["payload"]["model"], MODELO_POR_DEFECTO)

    def test_la_via_gratuita_tambien_habilita(self):
        p = HiggsfieldProvider(cuenta=EstadoDeCuenta(creditos=0, unlim_disponible=True))
        r = p.generate(_req(), gate_arte="ABIERTO")
        self.assertEqual(r.error, PENDIENTE_DE_DESPACHO)

    def test_con_creditos_y_sin_despachador_no_inventa_una_imagen(self):
        p = HiggsfieldProvider(cuenta=EstadoDeCuenta(creditos=100))
        r = p.generate(_req(), gate_arte="ABIERTO")
        self.assertFalse(r.ok)
        self.assertEqual(r.error, PENDIENTE_DE_DESPACHO)
        self.assertEqual(r.image_bytes, b"")

    def test_despachada_devuelve_la_imagen_real(self):
        p = HiggsfieldProvider(cuenta=EstadoDeCuenta(creditos=100),
                               despachador=_despachador_ok)
        r = p.generate(_req(), gate_arte="ABIERTO")
        self.assertTrue(r.ok)
        self.assertEqual(r.image_bytes, b"PNGDATA")
        self.assertEqual((r.width, r.height), (1080, 1920))

    def test_un_despachador_vacio_no_se_toma_por_exito(self):
        p = HiggsfieldProvider(cuenta=EstadoDeCuenta(creditos=100),
                               despachador=lambda payload: None)
        r = p.generate(_req(), gate_arte="ABIERTO")
        self.assertFalse(r.ok)
        self.assertEqual(r.error, "PROVIDER_EMPTY_RESULT")


class TestCatalogoVerificado(unittest.TestCase):
    def test_un_modelo_fuera_del_catalogo_se_rechaza(self):
        """El catalogo se verifico contra la API; no se amplia de memoria."""
        with self.assertRaises(ProviderError):
            HiggsfieldProvider(modelo="modelo_que_suena_bien")

    def test_todos_los_modelos_declaran_por_que_estan(self):
        for mid, m in MODELOS.items():
            with self.subTest(modelo=mid):
                self.assertTrue(m["_por_que"])
                self.assertTrue(m["aspect_ratios"])

    def test_el_modelo_por_defecto_renderiza_texto_fiable(self):
        """LegalMente monta texto juridico exacto: un modelo que deforma letras
        no sirve por muy bueno que sea el fondo."""
        self.assertTrue(MODELOS[MODELO_POR_DEFECTO]["texto_fiable"])
        self.assertIn("9:16", MODELOS[MODELO_POR_DEFECTO]["aspect_ratios"])

    def test_la_recomendacion_depende_de_si_lleva_texto_montado(self):
        con = modelo_recomendado_para(True)
        sin = modelo_recomendado_para(False)
        self.assertTrue(MODELOS[con]["texto_fiable"])
        self.assertNotEqual(con, sin)

    def test_las_capacidades_salen_del_catalogo_no_de_una_lista_paralela(self):
        for mid in MODELOS:
            p = HiggsfieldProvider(modelo=mid)
            with self.subTest(modelo=mid):
                caps = p.capabilities()
                self.assertEqual(tuple(caps.aspect_ratios), MODELOS[mid]["aspect_ratios"])
                self.assertEqual(caps.supports_reliable_text, MODELOS[mid]["texto_fiable"])


if __name__ == "__main__":
    unittest.main()
