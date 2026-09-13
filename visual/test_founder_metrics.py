"""Founder Selection Rate: la métrica y la disciplina de no sobreinterpretarla."""

import unittest

import founder_metrics as fm
import organism
from semantic_memory import SemanticMemory


class TestTasaGlobal(unittest.TestCase):
    def test_memoria_vacia_no_da_tasa(self):
        self.assertIsNone(fm.tasa_global(SemanticMemory()))

    def test_tres_de_diez(self):
        m = SemanticMemory()
        lote = organism.producir_lote("t", n=10, seed=1, memoria=m)
        organism.registrar_curaduria(lote, [lote.candidatos[i].candidate_id for i in (0, 3, 7)], m)
        self.assertEqual(fm.tasa_global(m), 0.3)

    def test_generada_sola_no_cuenta_para_la_tasa(self):
        """Sin curaduría, no hay decisión: la tasa no puede calcularse."""
        m = SemanticMemory()
        organism.producir_lote("t", n=10, seed=1, memoria=m)
        self.assertIsNone(fm.tasa_global(m))


class TestTasaPorEje(unittest.TestCase):
    def setUp(self):
        self.m = SemanticMemory()
        self.lote = organism.producir_lote("t", n=10, seed=2, memoria=self.m)
        organism.registrar_curaduria(
            self.lote, [self.lote.candidatos[i].candidate_id for i in (0, 3, 7)], self.m)

    def test_cada_fila_expone_su_tamano_de_muestra(self):
        filas = fm.tasa_por_eje(self.m, "materia")
        for f in filas:
            self.assertEqual(f.total_decididas, f.preseleccionadas + f.descartadas)

    def test_muestra_pequena_se_marca_explicitamente(self):
        filas = fm.tasa_por_eje(self.m, "materia")
        self.assertTrue(any(not f.muestra_suficiente for f in filas))

    def test_la_tasa_no_se_oculta_aunque_la_muestra_sea_pequena(self):
        """El mandato pide no CONCLUIR de muestras pequeñas, no OCULTARLAS."""
        filas = fm.tasa_por_eje(self.m, "materia")
        for f in filas:
            self.assertIsNotNone(f.tasa)

    def test_ordenado_por_tamano_de_muestra_descendente(self):
        filas = fm.tasa_por_eje(self.m, "necesidad")
        tamanos = [f.total_decididas for f in filas]
        self.assertEqual(tamanos, sorted(tamanos, reverse=True))


class TestInforme(unittest.TestCase):
    def setUp(self):
        self.m = SemanticMemory()
        self.lote = organism.producir_lote("t", n=10, seed=3, memoria=self.m)
        organism.registrar_curaduria(
            self.lote, [self.lote.candidatos[i].candidate_id for i in (1, 4, 6)], self.m)

    def test_cubre_los_ejes_pedidos_por_el_founder(self):
        rep = fm.informe(self.m)
        for eje in ("materia", "familia_editorial", "necesidad", "emocion"):
            self.assertIn(eje, rep.por_eje)

    def test_avisa_de_ejes_sin_datos_en_vez_de_fabricarlos(self):
        rep = fm.informe(self.m, ejes=list(fm.EJES_DISPONIBLES) + list(fm.EJES_PENDIENTES))
        self.assertIn("direccion_artistica", rep.ejes_sin_datos)
        self.assertIn("hook", rep.ejes_sin_datos)
        self.assertTrue(any("direccion_artistica" in a for a in rep.avisos))

    def test_direccion_artistica_no_aparece_como_eje_con_datos_falsos(self):
        rep = fm.informe(self.m, ejes=list(fm.EJES_DISPONIBLES) + list(fm.EJES_PENDIENTES))
        self.assertNotIn("direccion_artistica", rep.por_eje)

    def test_avisa_si_la_muestra_global_es_pequena(self):
        m = SemanticMemory()
        from semantic_fingerprint import SemanticFingerprint as S
        from semantic_memory import PRESELECCIONADA, DESCARTADA
        m.record(S(content_id="a", materia="civil"), PRESELECCIONADA)
        m.record(S(content_id="b", materia="civil"), DESCARTADA)
        rep = fm.informe(m)
        self.assertTrue(any("informativa, no concluyente" in a for a in rep.avisos))

    def test_no_avisa_de_muestra_pequena_cuando_no_la_hay(self):
        """Con muchas decisiones repetidas del mismo valor, deja de avisar
        para ese valor concreto."""
        m = SemanticMemory()
        from semantic_fingerprint import SemanticFingerprint as S
        from semantic_memory import PRESELECCIONADA, DESCARTADA
        for i in range(6):
            m.record(S(content_id=f"s{i}", materia="civil"), PRESELECCIONADA)
        for i in range(6):
            m.record(S(content_id=f"d{i}", materia="civil"), DESCARTADA)
        filas = fm.tasa_por_eje(m, "materia")
        self.assertTrue(filas[0].muestra_suficiente)


if __name__ == "__main__":
    unittest.main()
