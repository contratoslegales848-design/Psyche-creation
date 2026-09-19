"""Regresión — 15-sep-2026: 'las imágenes finales no llevan texto ni
respetan el formato'. Bloquea que el compositor real vuelva a producir un
resultado sin texto o con dimensiones distintas a las del canal pedido."""

import unittest

import demo_composicion_formato as demo


class TestComposicionRespetaTextoYFormato(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.resultados = demo.generar_ejemplo()

    def test_los_tres_canales_componen_sin_problemas(self):
        for nombre, (r, problemas) in self.resultados.items():
            self.assertEqual(problemas, [], nombre)
            self.assertEqual(r.state, "COMPOSED", nombre)

    def test_cada_canal_produce_las_dimensiones_exactas_pedidas(self):
        for nombre, (w, h, _) in demo.CANALES.items():
            r, _ = self.resultados[nombre]
            self.assertEqual((r.width, r.height), (w, h), nombre)

    def test_el_compuesto_nunca_es_identico_al_fondo_bruto(self):
        """Si coincidieran, el compositor no habría dibujado nada — exactamente
        el síntoma reportado: un fondo publicado como si fuera la pieza final."""
        for nombre, (r, _) in self.resultados.items():
            self.assertNotEqual(r.composed_sha256, r.raw_sha256, nombre)

    def test_el_texto_exacto_se_preserva_sin_parafrasear(self):
        from composition import build_typography_plan
        typo = build_typography_plan(demo.COPY_EJEMPLO, demo.AUTOR, 1080, 1920,
                                     content_type="concepto")
        self.assertEqual(typo.rendered_text(), demo.COPY_EJEMPLO)


if __name__ == "__main__":
    unittest.main()
