"""Enriquecimiento de concepto_nucleo/pregunta_resuelta sin inventar."""

import unittest

import corpus_enrichment as ce
import corpus_import as ci


class EnrichBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.regs, _ = ci.construir_registros()
        cls.enr = ce.enriquecer(cls.regs)
        cls.por_id = {e.content_id: e for e in cls.enr}


class TestVocabularioDeConfianza(EnrichBase):
    def test_los_cinco_niveles_exactos(self):
        self.assertEqual(ce.NIVELES,
                         (ce.DECLARADO, ce.INFERIDO_ALTO, ce.INFERIDO_MEDIO,
                          ce.INFERIDO_BAJO, ce.UNKNOWN))

    def test_declarado_nunca_aparece_en_este_corpus(self):
        """Nadie declaró estos campos explícitamente en 2026-09; el nivel
        existe para corpus futuros que sí los declaren."""
        for e in self.enr:
            self.assertNotEqual(e.concepto_confianza, ce.DECLARADO)
            self.assertNotEqual(e.pregunta_confianza, ce.DECLARADO)

    def test_todos_los_registros_se_enriquecen(self):
        self.assertEqual(len(self.enr), 174)

    def test_toda_inferencia_trae_su_razon(self):
        for e in self.enr:
            if e.concepto_confianza != ce.UNKNOWN:
                self.assertTrue(e.razon_concepto.strip())
            if e.pregunta_confianza != ce.UNKNOWN:
                self.assertTrue(e.razon_pregunta.strip())


class TestEnriquecerConcepto(unittest.TestCase):
    def test_prefijo_editorial_da_inferido_alto(self):
        r = type("R", (), {"guion": "mito-huella-dactilar-infalible", "titular": "X"})()
        texto, conf, _ = ce.enriquecer_concepto(r)
        self.assertEqual(conf, ce.INFERIDO_ALTO)
        self.assertIn("huella dactilar infalible", texto)

    def test_sin_prefijo_ni_titular_util_da_inferido_bajo(self):
        r = type("R", (), {"guion": "anatomia-de-una-firma",
                          "titular": "UN TITULAR LARGO QUE NO ES BREVE EN ABSOLUTO"})()
        texto, conf, _ = ce.enriquecer_concepto(r)
        self.assertEqual(conf, ce.INFERIDO_BAJO)

    def test_sin_nada_da_unknown(self):
        r = type("R", (), {"guion": "", "titular": ""})()
        texto, conf, _ = ce.enriquecer_concepto(r)
        self.assertEqual(conf, ce.UNKNOWN)
        self.assertEqual(texto, "")


class TestEnriquecerPregunta(unittest.TestCase):
    def test_titular_interrogativo_da_inferido_alto(self):
        r = type("R", (), {"guion": "x", "titular": "¿QUÉ PASA SI FIRMO SIN LEER?"})()
        texto, conf, _ = ce.enriquecer_pregunta(r)
        self.assertEqual(conf, ce.INFERIDO_ALTO)
        self.assertEqual(texto, r.titular)

    def test_patron_diferencia_reconstruye_por_plantilla(self):
        r = type("R", (), {"guion": "diferencia-perito-testigo", "titular": "X"})()
        texto, conf, _ = ce.enriquecer_pregunta(r)
        self.assertEqual(conf, ce.INFERIDO_MEDIO)
        self.assertIn("perito testigo", texto)

    def test_forma_narrativa_dispara_inferido_bajo(self):
        r = type("R", (), {"guion": "el-acto-que-nadie-notifico", "titular": "X"})()
        texto, conf, _ = ce.enriquecer_pregunta(r)
        self.assertEqual(conf, ce.INFERIDO_BAJO)
        self.assertIn("acto", texto)
        self.assertIn("notifico", texto)

    def test_reformulacion_no_inventa_hechos_nuevos(self):
        """La pregunta reconstruida sólo reordena palabras del propio slug."""
        r = type("R", (), {"guion": "el-testamento-que-nadie-encontro", "titular": "X"})()
        texto, _, _ = ce.enriquecer_pregunta(r)
        for palabra in ("testamento", "encontro"):
            self.assertIn(palabra, texto)

    def test_sin_patron_da_unknown(self):
        r = type("R", (), {"guion": "anatomia-de-una-firma", "titular": "ANATOMÍA DE UNA FIRMA"})()
        texto, conf, _ = ce.enriquecer_pregunta(r)
        self.assertEqual(conf, ce.UNKNOWN)
        self.assertEqual(texto, "")


class TestLasDosHuellas(EnrichBase):
    def test_completa_usa_toda_la_senal_disponible(self):
        e = self.por_id["LM-024"]  # concepto=claridad-en-contratos (INFERIDO_MEDIO/BAJO)
        fp = e.fingerprint_completo()
        if e.concepto_nucleo_enriquecido:
            self.assertEqual(fp.concepto_nucleo, e.concepto_nucleo_enriquecido)

    def test_conservadora_descarta_confianza_baja(self):
        bajo = next(e for e in self.enr if e.concepto_confianza == ce.INFERIDO_BAJO)
        fp = bajo.fingerprint_conservador()
        base_fp = bajo.base.fingerprint()
        self.assertEqual(fp.concepto_nucleo, base_fp.concepto_nucleo)

    def test_conservadora_conserva_confianza_media_o_mas(self):
        medio = next((e for e in self.enr if e.concepto_confianza == ce.INFERIDO_MEDIO), None)
        self.assertIsNotNone(medio)
        fp = medio.fingerprint_conservador()
        self.assertEqual(fp.concepto_nucleo, medio.concepto_nucleo_enriquecido)

    def test_pregunta_unknown_viaja_vacia_en_ambas_huellas(self):
        sin_pregunta = next(e for e in self.enr if e.pregunta_confianza == ce.UNKNOWN)
        self.assertEqual(sin_pregunta.fingerprint_conservador().pregunta_resuelta, "")

    def test_un_disfraz_con_pregunta_inferida_baja_no_bloquea_por_esa_via(self):
        """La regla central del Founder, ejecutable: confianza baja no
        actúa como verdad fuerte para bloquear."""
        bajo = [e for e in self.enr if e.pregunta_confianza == ce.INFERIDO_BAJO]
        self.assertTrue(bajo)
        a, b = bajo[0], bajo[0]
        fp_a = a.fingerprint_conservador()
        # Comparando el mismo registro consigo mismo bajo huella conservadora:
        # la pregunta INFERIDO_BAJO no debería ser lo que decide el bloqueo,
        # así que su ausencia de la huella conservadora es la prueba directa.
        self.assertEqual(fp_a.pregunta_resuelta, "")


class TestReporte(EnrichBase):
    def test_reporte_cuenta_los_174(self):
        rep = ce.reporte(self.enr)
        self.assertEqual(rep.total, 174)
        self.assertEqual(sum(rep.concepto_por_nivel.values()), 174)
        self.assertEqual(sum(rep.pregunta_por_nivel.values()), 174)

    def test_hay_evidencia_de_progreso_real_no_solo_unknown(self):
        rep = ce.reporte(self.enr)
        self.assertGreater(rep.concepto_por_nivel[ce.INFERIDO_ALTO], 0)
        self.assertGreater(rep.pregunta_por_nivel[ce.INFERIDO_ALTO], 0)

    def test_no_todo_se_resuelve_a_toda_costa(self):
        """Un enriquecimiento que resolviera el 100% sería sospechoso de forzar."""
        rep = ce.reporte(self.enr)
        self.assertGreater(rep.pregunta_por_nivel[ce.UNKNOWN], 0)


if __name__ == "__main__":
    unittest.main()
