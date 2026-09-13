"""Territory Explorer: novedad, cobertura y oportunidad — nunca rareza por rareza."""

import unittest

import corpus_import as ci
import editorial
import territory_explorer as te


class MapaBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.regs, _ = ci.construir_registros()
        cls.mapa = te.construir_mapa(cls.regs)
        cls.universo = editorial.EditorialUniverse.load()


class Cand:
    def __init__(self, materia, familia, necesidad="", rol_lector=""):
        self.materia, self.familia_editorial = materia, familia
        self.necesidad, self.rol_lector = necesidad, rol_lector


class TestMapa(MapaBase):
    def test_cuenta_celdas_reales(self):
        self.assertEqual(self.mapa.celdas_tocadas, 77)

    def test_coverage_es_fraccion_de_celdas_posibles(self):
        self.assertAlmostEqual(self.mapa.coverage,
                               self.mapa.celdas_tocadas / self.mapa.celdas_posibles, places=4)

    def test_coverage_bajo_confirma_el_hallazgo_previo(self):
        self.assertLess(self.mapa.coverage, 0.10)

    def test_marginales_cubren_los_ejes_secundarios(self):
        for eje in te.EJES_MARGINALES:
            self.assertIn(eje, self.mapa.marginales)

    def test_unknown_no_contamina_el_mapa(self):
        for (mat, fam) in self.mapa.celdas:
            self.assertNotEqual(mat, "unknown")
            self.assertNotEqual(fam, "unknown")


class TestNovelty(MapaBase):
    def test_celda_nunca_tocada_tiene_novelty_maxima(self):
        s = te.score_candidate(Cand("ambiental", "prevencion"), self.mapa, self.universo)
        self.assertEqual(s.novelty, 1.0)

    def test_celda_muy_tocada_tiene_novelty_baja(self):
        # civil es la materia más repetida del corpus (28 piezas).
        frecuentes = [k for k, v in self.mapa.celdas.items() if v == max(self.mapa.celdas.values())]
        mat, fam = frecuentes[0]
        s = te.score_candidate(Cand(mat, fam), self.mapa, self.universo)
        self.assertEqual(s.novelty, 0.0)

    def test_materia_o_familia_ausente_no_se_puntua(self):
        s = te.score_candidate(Cand("", ""), self.mapa, self.universo)
        self.assertEqual(s.opportunity, 0.0)
        self.assertTrue(s.explicacion)


class TestCoherenciaYOportunidad(MapaBase):
    def test_afinidad_que_encaja_da_coherencia_maxima(self):
        s = te.score_candidate(Cand("ambiental", "prevencion", "prevenir", "persona"),
                               self.mapa, self.universo)
        self.assertEqual(s.coherencia, te.COHERENCIA_CON_AFINIDAD_QUE_ENCAJA)

    def test_afinidad_que_no_encaja_penaliza(self):
        s = te.score_candidate(Cand("ambiental", "prevencion", "recordar", "persona"),
                               self.mapa, self.universo)
        self.assertEqual(s.coherencia, te.COHERENCIA_CON_AFINIDAD_QUE_NO_ENCAJA)

    def test_novedad_sin_utilidad_no_gana_a_novedad_con_utilidad(self):
        """El principio central de la fase: 'novedad sin utilidad no es calidad'."""
        coherente = te.score_candidate(
            Cand("ambiental", "prevencion", "prevenir", "persona"), self.mapa, self.universo)
        incoherente = te.score_candidate(
            Cand("ambiental", "prevencion", "recordar", "persona"), self.mapa, self.universo)
        self.assertEqual(coherente.novelty, incoherente.novelty)  # mismo hueco
        self.assertGreater(coherente.opportunity, incoherente.opportunity)

    def test_coherencia_es_multiplicador_no_bonus_aditivo(self):
        s = te.score_candidate(Cand("ambiental", "prevencion", "recordar", "persona"),
                               self.mapa, self.universo)
        self.assertAlmostEqual(s.opportunity, round(s.novelty * s.coherencia, 4))

    def test_familia_inexistente_es_neutral_no_un_error(self):
        """Puntuar territorio nunca debe reventar por una familia que aún no
        está en el registro: se trata como sin evidencia, no como excepción."""
        s = te.score_candidate(Cand("ambiental", "familia_que_no_existe_todavia",
                                    "entender", "persona"), self.mapa, self.universo)
        self.assertEqual(s.coherencia, te.COHERENCIA_SIN_AFINIDAD_DECLARADA)

    def test_todas_las_58_familias_declaran_afinidad(self):
        """Hallazgo de esta fase: el seed no dejó ninguna familia sin
        necesidades_afines ni roles_lector_afines — la rama 'neutral por falta
        de afinidad declarada' del código cubre familias futuras, no las
        actuales."""
        sin_afinidad = [n for n in self.universo.names()
                        if not self.universo.get(n).necesidades_afines
                        and not self.universo.get(n).roles_lector_afines]
        self.assertEqual(sin_afinidad, [])


class TestTopOportunidades(MapaBase):
    def test_devuelve_n_filas(self):
        self.assertEqual(len(te.top_oportunidades(self.mapa, self.universo, n=15)), 15)

    def test_ordenado_por_oportunidad_descendente(self):
        filas = te.top_oportunidades(self.mapa, self.universo, n=30)
        valores = [f[0] for f in filas]
        self.assertEqual(valores, sorted(valores, reverse=True))

    def test_no_penaliza_por_falta_de_necesidad_especificada(self):
        """El ranking recorre materia×familia SOLO: no debe castigar a las
        familias con afinidades declaradas sólo porque aún no se eligió
        necesidad (bug real encontrado y corregido en esta fase)."""
        filas = te.top_oportunidades(self.mapa, self.universo, n=50)
        valores = {round(f[0], 3) for f in filas}
        # Antes del fix, toda familia CON afinidades declaradas caía a 0.4*novelty
        # aunque estuviera totalmente vacía; el fix la deja en 0.7*novelty como
        # las que no declaran afinidad, hasta que se elige necesidad/rol.
        self.assertIn(round(1.0 * 0.7, 3), valores)

    def test_incluye_materias_sin_ninguna_pieza(self):
        """Territorio virgen (6 materias sin pieza) debe poder aparecer:
        el mandato no restringe a materias ya abiertas."""
        _, materias = ci.construir_registros()[0], None
        import universe as uni
        _, materias = uni.cargar_materias()
        virgen = "ambiental"
        filas = te.top_oportunidades(self.mapa, self.universo, materias=materias, n=2000)
        self.assertTrue(any(f[1] == virgen for f in filas))


if __name__ == "__main__":
    unittest.main()
