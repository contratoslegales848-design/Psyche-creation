"""Análisis del corpus: repetición, clusters, territorio sin explorar."""

import unittest

import corpus_analysis as ca
import corpus_import as ci
from semantic_fingerprint import UMBRAL_EQUIVALENCIA


class AnalisisBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.regs, _ = ci.construir_registros()
        cls.perfil = ca.perfil_de_repeticion(cls.regs)


class TestPerfilDeRepeticion(AnalisisBase):
    def test_cubre_los_ejes_que_pide_el_founder(self):
        for eje in ("materia", "familia_editorial", "concepto_nucleo", "metafora",
                    "composicion", "direccion_artistica", "emocion",
                    "materia+familia_editorial"):
            self.assertIn(eje, self.perfil)

    def test_los_unknown_no_se_cuentan_como_una_categoria(self):
        """Contarlos fingiría que 29 piezas comparten una familia editorial."""
        self.assertNotIn(ci.UNKNOWN, self.perfil["familia_editorial"])

    def test_los_unknown_se_informan_aparte(self):
        self.assertGreater(self.perfil["_sin_dato"]["familia_editorial"], 0)
        self.assertEqual(self.perfil["_sin_dato"]["emocion"], 174)

    def test_la_capa_visual_estaba_diversificada(self):
        """174 metáforas distintas: el problema histórico no era el arte."""
        self.assertEqual(len(self.perfil["metafora"]), 174)

    def test_la_capa_editorial_no_lo_estaba(self):
        """La función editorial dominante cubre casi la mitad del catálogo."""
        top = max(self.perfil["familia_editorial"].values())
        self.assertGreater(top / len(self.regs), 0.40)

    def test_ordenado_de_mas_repetido_a_menos(self):
        vals = list(self.perfil["materia"].values())
        self.assertEqual(vals, sorted(vals, reverse=True))


class TestClusters(AnalisisBase):
    def test_al_umbral_de_bloqueo_no_hay_duplicados(self):
        """El banco v3 cumplió: 174 temas realmente distintos."""
        cs = ca.clusters_semanticos(self.regs, umbral=UMBRAL_EQUIVALENCIA)
        self.assertEqual(cs, [])

    def test_a_umbral_de_proximidad_aparecen_vecindades(self):
        cs = ca.clusters_semanticos(self.regs, umbral=0.35)
        self.assertTrue(cs)
        self.assertGreaterEqual(cs[0].tamano, 2)

    def test_los_clusters_se_ordenan_por_tamano(self):
        cs = ca.clusters_semanticos(self.regs, umbral=0.35)
        self.assertEqual([c.tamano for c in cs], sorted([c.tamano for c in cs], reverse=True))

    def test_cada_pieza_aparece_en_un_solo_cluster(self):
        cs = ca.clusters_semanticos(self.regs, umbral=0.35)
        vistos = [cid for c in cs for cid, _ in c.miembros]
        self.assertEqual(len(vistos), len(set(vistos)))

    def test_es_determinista(self):
        a = ca.clusters_semanticos(self.regs, umbral=0.35)
        b = ca.clusters_semanticos(self.regs, umbral=0.35)
        self.assertEqual([c.miembros for c in a], [c.miembros for c in b])

    def test_un_umbral_mas_laxo_agrupa_mas(self):
        self.assertGreaterEqual(
            sum(c.tamano for c in ca.clusters_semanticos(self.regs, umbral=0.45)),
            sum(c.tamano for c in ca.clusters_semanticos(self.regs, umbral=0.30)))

    def test_no_agrupa_sobre_huellas_incomparables(self):
        from semantic_fingerprint import SemanticFingerprint

        class Vacia:
            def __init__(self, i):
                self.content_id, self.guion, self.materia = f"V{i}", "", ""

            def fingerprint(self):
                return SemanticFingerprint(content_id=self.content_id)

        self.assertEqual(ca.clusters_semanticos([Vacia(i) for i in range(5)]), [])


class TestZonasSinExplorar(AnalisisBase):
    def setUp(self):
        self.z = ca.zonas_sin_explorar(self.regs)

    def test_identifica_materias_nunca_tocadas(self):
        self.assertTrue(self.z["materias_del_seed_sin_una_sola_pieza"])

    def test_identifica_familias_nunca_usadas(self):
        """La respuesta a '¿qué puertas no ha abierto LegalMente?'."""
        nunca = self.z["familias_editoriales_nunca_usadas"]
        self.assertGreater(len(nunca), 30)
        for esperada in ("jurista", "etimologia", "doctrina", "caso_historico"):
            self.assertIn(esperada, nunca)

    def test_el_corpus_ya_no_tiene_materias_fuera_del_seed(self):
        """migracion y cultura_y_literatura_juridica se incorporaron al seed
        porque el corpus demostró que existían."""
        self.assertEqual(self.z["materias_del_corpus_fuera_del_seed"], [])

    def test_la_cobertura_combinatoria_es_minima(self):
        producidas = self.z["combinaciones_materia_familia_producidas"]
        posibles = self.z["combinaciones_posibles_sobre_materias_ya_abiertas"]
        self.assertLess(producidas / posibles, 0.15)

    def test_sucesorio_no_aparece_como_virgen(self):
        """Regresión: el banco archivó herencia bajo FAMILIA y sucesorio
        parecía territorio sin explorar cuando tiene 4 piezas."""
        self.assertNotIn("sucesorio", self.z["materias_del_seed_sin_una_sola_pieza"])


if __name__ == "__main__":
    unittest.main()
