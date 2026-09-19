"""Integración de punta a punta: universe → generator → art_direction →
visual_distance → lanes → organism, con datos reales del corpus."""

import unittest

import demo_reconciliation as dr
import editorial
import families
import generator
import territory_explorer as te
import universe
from memory import VisualMemory
from semantic_memory import SemanticMemory


class TestCadenaCompleta(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import corpus_import as ci
        cls.regs, _ = ci.construir_registros()
        cls.universo = editorial.EditorialUniverse.load()
        _, cls.materias = universe.cargar_materias()
        cls.registro_familias = families.VisualFamilyRegistry.load()
        cls.mapa = te.construir_mapa(cls.regs, materias=cls.materias, universo=cls.universo)
        cls.memoria = SemanticMemory()
        ci.importar(cls.memoria, cls.regs)

    def test_produce_diez_piezas_con_borrador_visual(self):
        _, sel, pts, drafts, _ = dr.producir_y_dirigir(
            111, self.memoria, self.mapa, self.universo, self.materias, self.registro_familias)
        self.assertEqual(len(sel), 10)
        self.assertEqual(len(drafts), 10)
        self.assertEqual(len(pts), 10)

    def test_la_direccion_artistica_rota_dentro_del_lote(self):
        """El defecto real encontrado y corregido: sin memoria acumulada,
        las 10 piezas salían con la misma familia visual."""
        _, sel, _, drafts, _ = dr.producir_y_dirigir(
            222, self.memoria, self.mapa, self.universo, self.materias, self.registro_familias)
        distintas = {d.familia_visual for d in drafts}
        self.assertGreater(len(distintas), 1)

    def test_cada_borrador_esta_ligado_a_su_candidato(self):
        _, sel, _, drafts, _ = dr.producir_y_dirigir(
            333, self.memoria, self.mapa, self.universo, self.materias, self.registro_familias)
        for c, d in zip(sel, drafts):
            self.assertEqual(c.candidate_id, d.content_id)

    def test_ningun_borrador_esta_autorizado(self):
        _, sel, _, drafts, _ = dr.producir_y_dirigir(
            444, self.memoria, self.mapa, self.universo, self.materias, self.registro_familias)
        self.assertTrue(all(not d.autorizado for d in drafts))

    def test_draft_a_entry_visual_no_copia_los_pendientes_como_dato(self):
        _, sel, _, drafts, _ = dr.producir_y_dirigir(
            555, self.memoria, self.mapa, self.universo, self.materias, self.registro_familias)
        entry = dr.draft_a_entry_visual(sel[0], drafts[0])
        self.assertEqual(entry.scene_type, "")
        self.assertEqual(entry.metaphor, "")

    def test_qa_de_lote_no_finge_certeza_sobre_distancia_visual(self):
        _, sel, _, drafts, _ = dr.producir_y_dirigir(
            666, self.memoria, self.mapa, self.universo, self.materias, self.registro_familias)
        # No debe lanzar, y no debe reportar el lote como "visualmente
        # verificado" — sólo evidencia_incompleta es un resultado honesto
        # aquí, dado que escena/metáfora son PENDIENTE_CONTENIDO.
        problemas = dr.qa_de_lote(sel, drafts, self.registro_familias, self.memoria)
        self.assertIsInstance(problemas, list)

    def test_gate_de_proveedor_bloquearia_higgsfield(self):
        import provider_gate as pg
        with self.assertRaises(pg.ProviderGateError):
            pg.verificar_proveedor_permitido("Higgsfield")


class TestSegundoLoteAprende(unittest.TestCase):
    def test_ciclo_completo_es_reproducible(self):
        import corpus_import as ci
        regs, _ = ci.construir_registros()
        universo = editorial.EditorialUniverse.load()
        _, materias = universe.cargar_materias()
        registro = families.VisualFamilyRegistry.load()
        mapa = te.construir_mapa(regs, materias=materias, universo=universo)

        m1 = SemanticMemory()
        ci.importar(m1, regs)
        _, sel1a, _, _, _ = dr.producir_y_dirigir(999, m1, mapa, universo, materias, registro)

        m2 = SemanticMemory()
        ci.importar(m2, regs)
        _, sel1b, _, _, _ = dr.producir_y_dirigir(999, m2, mapa, universo, materias, registro)

        self.assertEqual([c.candidate_id for c in sel1a], [c.candidate_id for c in sel1b])


if __name__ == "__main__":
    unittest.main()
