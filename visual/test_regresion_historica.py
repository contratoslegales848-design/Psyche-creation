"""Prueba de regresión contra las 174 piezas reales.

No basta con que un lote nuevo sea diverso entre sí: no puede ser una
reformulación de lo que LegalMente ya contó.
"""

import unittest

import batch_qa
import corpus_import as ci
import organism
import universe
from semantic_fingerprint import mas_similar, UMBRAL_EQUIVALENCIA
from semantic_memory import SemanticMemory, HISTORICA


class ConMemoriaHistorica(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.regs, _ = ci.construir_registros()
        cls.memoria = SemanticMemory()
        ci.importar(cls.memoria, cls.regs)
        cls.historicas = [r.fingerprint() for r in cls.regs]
        cls.reserva = universe.build_reserve(objetivo_lote=10, seed=777, factor=12)
        cls.seleccion = universe.select_batch(cls.reserva, n=10, memoria=cls.memoria)


class TestReserva(ConMemoriaHistorica):
    def test_la_reserva_supera_los_cien_candidatos(self):
        self.assertGreaterEqual(len(self.reserva), 100)

    def test_la_reserva_es_heterogenea(self):
        self.assertGreaterEqual(len({c.materia for c in self.reserva}), 20)
        self.assertGreaterEqual(len({c.familia_editorial for c in self.reserva}), 30)


class TestLoteContraHistoria(ConMemoriaHistorica):
    def test_se_selecciona_el_lote_completo(self):
        self.assertEqual(len(self.seleccion.seleccionados), 10)
        self.assertTrue(self.seleccion.completo)

    def test_ninguna_pieza_repite_el_corpus_historico(self):
        for c in self.seleccion.seleccionados:
            fp = c.fingerprint()
            for h in self.historicas:
                self.assertFalse(fp.equivalente_a(h),
                                 f"{c.candidate_id} reformula {h.content_id}")

    def test_ninguna_pieza_queda_bloqueada_por_la_memoria(self):
        for c in self.seleccion.seleccionados:
            v = self.memoria.evaluar(c.fingerprint())
            self.assertFalse(v.bloquea, f"{c.candidate_id}: {v.motivo}")

    def test_cada_pieza_tiene_un_vecino_historico_identificable(self):
        """Poder nombrar el vecino más cercano es lo que permite justificar
        que NO es repetición, en vez de afirmarlo."""
        for c in self.seleccion.seleccionados:
            vecino, d = mas_similar(c.fingerprint(), self.historicas)
            self.assertIsNotNone(vecino, c.candidate_id)
            self.assertGreater(d.valor, UMBRAL_EQUIVALENCIA)

    def test_el_lote_pasa_el_qa_de_sistema(self):
        qa = batch_qa.evaluar_lote([c.fingerprint() for c in self.seleccion.seleccionados],
                                   objetivo=10, memoria=self.memoria)
        self.assertTrue(qa.aceptado, qa.incumplimientos)


class TestPruebaFounder(ConMemoriaHistorica):
    """10 piezas LegalMente General: ¿emergen familias distintas sin pedirlas?"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.lote = organism.producir_lote("founder-test", n=10, seed=4242,
                                          memoria=SemanticMemory(
                                              [e for e in cls.memoria.entries()]),
                                          factor_reserva=12)

    def test_el_lote_llega_a_curation_ready(self):
        self.assertTrue(self.lote.listo, self.lote.qa.get("incumplimientos"))

    def test_diez_familias_editoriales_distintas(self):
        fams = {c.familia_editorial for c in self.lote.candidatos}
        self.assertEqual(len(fams), 10)

    def test_no_son_diez_conceptos_ni_diez_definiciones(self):
        for repetida in ("concepto", "definicion_operativa", "asesoria_orientacion"):
            cuenta = sum(1 for c in self.lote.candidatos
                         if c.familia_editorial == repetida)
            self.assertLessEqual(cuenta, 1, repetida)

    def test_no_se_sobreexplota_contratos_penal_ni_digital(self):
        """Las zonas fáciles no pueden dominar sólo por tener más datos."""
        for zona in ("civil", "penal", "digital_datos"):
            cuenta = sum(1 for c in self.lote.candidatos if c.materia == zona)
            self.assertLessEqual(cuenta, 2, zona)

    def test_emergen_familias_que_el_corpus_nunca_uso(self):
        """La prueba de que descubre territorio, no sólo evita repetirse."""
        historicas = {r.familia_editorial for r in self.regs
                      if r.familia_editorial != ci.UNKNOWN}
        nuevas = {c.familia_editorial for c in self.lote.candidatos} - historicas
        self.assertGreaterEqual(len(nuevas), 5, f"sólo {len(nuevas)} familias nuevas")

    def test_hay_rotacion_emocional(self):
        emos = {c.emocion for c in self.lote.candidatos if c.emocion}
        self.assertGreaterEqual(len(emos), 4)

    def test_el_lote_es_reproducible(self):
        otro = organism.producir_lote("founder-test", n=10, seed=4242,
                                      memoria=SemanticMemory(
                                          [e for e in self.memoria.entries()]),
                                      factor_reserva=12)
        self.assertEqual([c.candidate_id for c in otro.candidatos],
                         [c.candidate_id for c in self.lote.candidatos])


if __name__ == "__main__":
    unittest.main()
