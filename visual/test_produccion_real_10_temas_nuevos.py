"""Parte XIII del mandato "Fase post-implementación" (16-sep-2026): prueba
real de producción con candidatos del motor editorial real (no una lista
redactada para la ocasión), corrida como regresión ejecutable."""

import unittest
from pathlib import Path

import demo_produccion_real_10_temas_nuevos as dp


class TestProduccionReal10TemasNuevos(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        (cls.resultados, cls.reporte_lote_visual, cls.intentos, cls.mezcla,
         cls.rechazados, cls.señales) = dp.ejecutar()

    def test_hay_diez_piezas(self):
        self.assertEqual(len(self.resultados), 10)

    def test_los_candidatos_vienen_del_motor_real_no_de_una_lista_escrita(self):
        """Cada resultado trae un TopicCandidate real de universe.py, con
        todos los ejes del motor combinatorio poblados -- no un dict a mano."""
        import universe
        for r in self.resultados:
            self.assertIsInstance(r["candidato"], universe.TopicCandidate)
            self.assertTrue(r["candidato"].concepto_nucleo)
            self.assertTrue(r["candidato"].pregunta_resuelta)

    def test_al_menos_un_candidato_trae_senal_de_mercado_real(self):
        """Prueba de que market_signal.py realmente influyó en esta corrida
        -- no basta con que exista el mecanismo, tiene que haberse activado."""
        con_senal = [r for r in self.resultados if r["puntuacion"].ajuste_senal_mercado > 0]
        self.assertTrue(con_senal, "ningún candidato de esta corrida recibió señal de mercado real")

    def test_qa_de_huella_visual_es_aceptado(self):
        self.assertTrue(self.reporte_lote_visual.aceptado, self.reporte_lote_visual.incumplimientos)

    def test_ninguna_pieza_esta_clasificada_como_repetida_o_saturada(self):
        """Contra 174 piezas históricas reales -- si el motor produjera un
        tema ya contado, esto lo atraparía."""
        import topic_classification as tc
        for r in self.resultados:
            self.assertNotIn(r["clasif_repeticion"].etiqueta, (tc.REPETIDO, tc.SATURADO),
                             f"{r['candidato'].candidate_id}: {r['clasif_repeticion'].motivo}")

    def test_cada_pieza_tiene_prompt_compilado_con_la_metafora_autorada(self):
        for r in self.resultados:
            self.assertIn(r["direccion"]["metaphor"], r["compilado"].positive_prompt)

    def test_cada_pieza_tiene_taxonomia_no_vacia(self):
        for r in self.resultados:
            self.assertTrue(r["etiqueta_taxonomia"])

    def test_es_reproducible_con_la_misma_semilla(self):
        resultados2, *_ = dp.ejecutar()
        ids1 = [r["candidato"].candidate_id for r in self.resultados]
        ids2 = [r["candidato"].candidate_id for r in resultados2]
        self.assertEqual(ids1, ids2)

    def test_el_reporte_escrito_contiene_las_diez_piezas(self):
        destino = (Path(__file__).resolve().parent.parent / "docs" /
                  "prueba-real-produccion-10-temas-2026-09-16.md")
        self.assertTrue(destino.is_file(), "correr demo_produccion_real_10_temas_nuevos.py primero")
        contenido = destino.read_text(encoding="utf-8")
        for r in self.resultados:
            self.assertIn(r["candidato"].candidate_id, contenido)


if __name__ == "__main__":
    unittest.main()
