"""Mandato Maestro §1-3 (17-sep-2026): capa pedagógica del motor de
conocimiento. Clasificación auditable, ajuste acotado (nunca cuota)."""

import unittest

import editorial
import pedagogia as ped
import universe


class TestClasificacionOrigenPedagogico(unittest.TestCase):
    def setUp(self):
        self.universo = editorial.EditorialUniverse.load()

    def test_clasificacion_cubre_las_58_familias_reales(self):
        """Ninguna familia real del registro queda sin clasificar, y
        ninguna familia en FAMILIAS_NARRATIVA es inventada."""
        nombres = set(self.universo.names())
        self.assertEqual(len(nombres), 58)
        self.assertTrue(ped.FAMILIAS_NARRATIVA.issubset(nombres),
                        ped.FAMILIAS_NARRATIVA - nombres)
        for nombre in nombres:
            origen, razon = ped.clasificar_origen_pedagogico(nombre)
            self.assertIn(origen, (ped.CONOCIMIENTO_JURIDICO, ped.SITUACION_NARRATIVA))
            self.assertTrue(razon)

    def test_las_53_no_narrativas_son_conocimiento(self):
        no_narrativa = set(self.universo.names()) - ped.FAMILIAS_NARRATIVA
        self.assertEqual(len(no_narrativa), 53)
        for nombre in no_narrativa:
            origen, _ = ped.clasificar_origen_pedagogico(nombre)
            self.assertEqual(origen, ped.CONOCIMIENTO_JURIDICO)

    def test_las_5_narrativas_declaradas(self):
        for nombre in ped.FAMILIAS_NARRATIVA:
            origen, _ = ped.clasificar_origen_pedagogico(nombre)
            self.assertEqual(origen, ped.SITUACION_NARRATIVA)

    def test_familia_vacia_lanza_error_explicito(self):
        with self.assertRaises(ped.PedagogiaError):
            ped.clasificar_origen_pedagogico("")

    def test_es_determinista(self):
        self.assertEqual(ped.clasificar_origen_pedagogico("mito"),
                         ped.clasificar_origen_pedagogico("mito"))


class TestObjetivoYTipoDeAprendizaje(unittest.TestCase):
    def setUp(self):
        self.universo = editorial.EditorialUniverse.load()

    def test_objetivo_pedagogico_es_la_funcion_editorial_real(self):
        self.assertEqual(ped.objetivo_pedagogico("concepto", self.universo),
                         self.universo.get("concepto").funcion_editorial)

    def test_todas_las_necesidades_reales_tienen_tipo_de_aprendizaje(self):
        for nec in self.universo.necesidades:
            tipo = ped.tipo_de_aprendizaje(nec)
            self.assertNotEqual(tipo, "SIN_CLASIFICAR", nec)

    def test_necesidad_desconocida_no_se_inventa(self):
        self.assertEqual(ped.tipo_de_aprendizaje("necesidad-inexistente-xyz"), "SIN_CLASIFICAR")


class TestPerfilPedagogico(unittest.TestCase):
    def test_perfil_trae_los_cuatro_campos(self):
        c = universe.TopicCandidate(candidate_id="x", familia_editorial="mito",
                                    necesidad="corregir")
        p = ped.perfil_pedagogico(c)
        self.assertEqual(p.origen, ped.CONOCIMIENTO_JURIDICO)  # "mito" no está en FAMILIAS_NARRATIVA
        self.assertTrue(p.objetivo)
        self.assertTrue(p.tipo_aprendizaje)
        self.assertEqual(p.familia_editorial, "mito")


class TestAjusteBalancePedagogico(unittest.TestCase):
    def candidato(self, familia):
        return universe.TopicCandidate(candidate_id="x", familia_editorial=familia,
                                       necesidad="entender")

    def test_lote_vacio_es_cero_exacto(self):
        ajuste, razon = ped.ajuste_balance_pedagogico(self.candidato("concepto"), [])
        self.assertEqual(ajuste, 0.0)
        self.assertIn("vacío", razon)

    def test_desactivado_explicitamente_es_cero(self):
        lote = [self.candidato("caso_cotidiano")] * 5
        ajuste, razon = ped.ajuste_balance_pedagogico(
            self.candidato("concepto"), lote, objetivo_conocimiento=None)
        self.assertEqual(ajuste, 0.0)
        self.assertIn("desactivado", razon)

    def test_lote_saturado_de_narrativa_favorece_conocimiento(self):
        """Si el lote parcial ya es 100% narrativa, un candidato de
        conocimiento debe recibir empujón POSITIVO."""
        lote = [self.candidato("caso_cotidiano")] * 5
        ajuste, _ = ped.ajuste_balance_pedagogico(self.candidato("concepto"), lote)
        self.assertGreater(ajuste, 0.0)

    def test_lote_saturado_de_narrativa_penaliza_mas_narrativa(self):
        lote = [self.candidato("caso_cotidiano")] * 5
        ajuste, _ = ped.ajuste_balance_pedagogico(self.candidato("jurista"), lote)
        self.assertLess(ajuste, 0.0)

    def test_lote_saturado_de_conocimiento_favorece_narrativa(self):
        """Simétrico: narrativa nunca se elimina — si el lote va muy cargado
        de conocimiento, narrativa recupera ventaja (mandato §3: 'sigue
        disponible como puerta editorial')."""
        lote = [self.candidato("concepto")] * 9
        ajuste, _ = ped.ajuste_balance_pedagogico(self.candidato("caso_cotidiano"), lote)
        self.assertGreater(ajuste, 0.0)

    def test_lote_ya_en_el_objetivo_exacto_da_ajuste_cero(self):
        lote = ([self.candidato("concepto")] * 7) + ([self.candidato("caso_cotidiano")] * 3)
        ajuste_c, _ = ped.ajuste_balance_pedagogico(self.candidato("definicion_operativa"), lote)
        self.assertEqual(ajuste_c, 0.0)

    def test_ajuste_esta_acotado(self):
        lote = [self.candidato("caso_cotidiano")] * 20
        ajuste, _ = ped.ajuste_balance_pedagogico(self.candidato("concepto"), lote)
        self.assertLessEqual(abs(ajuste), ped.AJUSTE_BALANCE_PEDAGOGICO_MAX)

    def test_objetivo_configurable_no_es_regla_fija(self):
        """Mandato §3: 'hazlo configurable'. En un lote 100% conocimiento,
        un objetivo BAJO (quiere más narrativa: 0.10) debe empujar narrativa
        con más fuerza que un objetivo ALTO (casi conforme con puro
        conocimiento: 0.95, apenas por encima del 100% real) — la magnitud
        del empujón depende del parámetro, no de una constante quemada."""
        lote = [self.candidato("concepto")] * 5
        ajuste_narrativa_obj_bajo, _ = ped.ajuste_balance_pedagogico(
            self.candidato("caso_cotidiano"), lote, objetivo_conocimiento=0.10)
        ajuste_narrativa_obj_alto, _ = ped.ajuste_balance_pedagogico(
            self.candidato("caso_cotidiano"), lote, objetivo_conocimiento=0.95)
        self.assertGreater(ajuste_narrativa_obj_bajo, ajuste_narrativa_obj_alto)

    def test_nunca_excluye_solo_ajusta_score(self):
        """No hay ningún hard gate aquí: la función siempre devuelve un
        float, nunca bloquea_ni_rechaza."""
        lote = [self.candidato("caso_cotidiano")] * 30
        ajuste, _ = ped.ajuste_balance_pedagogico(self.candidato("jurista"), lote)
        self.assertIsInstance(ajuste, float)


if __name__ == "__main__":
    unittest.main()
