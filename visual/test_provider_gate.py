"""Gate de proveedores prohibidos: fail-closed, sin fallback silencioso."""

import unittest

import provider_gate as pg


class TestProveedorProhibido(unittest.TestCase):
    def test_detecta_higgsfield_exacto(self):
        self.assertEqual(pg.proveedor_prohibido("Higgsfield"), "higgsfield")

    def test_detecta_variantes_de_escritura(self):
        for variante in ("Higgsfield API v3", "higgs-field.ai", "HIGGS_FIELD",
                         "  higgsfield  ", "HiggsField Studio"):
            self.assertTrue(pg.proveedor_prohibido(variante), variante)

    def test_no_marca_proveedores_legitimos(self):
        for legitimo in ("generic-http-image-v1", "openai", "stability-ai", ""):
            self.assertEqual(pg.proveedor_prohibido(legitimo), "")

    def test_busca_tambien_en_el_modelo(self):
        self.assertTrue(pg.proveedor_prohibido("proveedor-generico", modelo="higgsfield-v2"))


class TestVerificacionFailClosed(unittest.TestCase):
    def test_proveedor_prohibido_lanza(self):
        with self.assertRaises(pg.ProviderGateError):
            pg.verificar_proveedor_permitido("Higgsfield")

    def test_el_error_no_sugiere_fallback_automatico(self):
        try:
            pg.verificar_proveedor_permitido("higgsfield")
        except pg.ProviderGateError as e:
            self.assertIn("Sin fallback silencioso", str(e))
        else:
            self.fail("debía lanzar ProviderGateError")

    def test_proveedor_permitido_devuelve_true(self):
        self.assertTrue(pg.verificar_proveedor_permitido("generic-http-image-v1"))

    def test_vacio_no_se_confunde_con_prohibido(self):
        self.assertTrue(pg.verificar_proveedor_permitido(""))


if __name__ == "__main__":
    unittest.main()
