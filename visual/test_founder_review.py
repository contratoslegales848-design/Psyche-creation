"""La hoja de revisión Founder y la incorporación trazable de sus decisiones."""

import json
import tempfile
import unittest
from pathlib import Path

import founder_review as fr
import corpus_import as ci


class TestHojaDeRevision(unittest.TestCase):
    def setUp(self):
        self.hoja = fr.generar_hoja_revision()

    def test_incluye_los_18_pares(self):
        self.assertEqual(self.hoja.count("PAR #"), 18)

    def test_incluye_las_cuatro_opciones(self):
        for opcion in ("A — MISMA IDEA", "B — RELACIONADAS", "C — CLARAMENTE",
                       "D — NO HAY INFORMACIÓN"):
            self.assertIn(opcion, self.hoja)

    def test_muestra_distancia_calculada_por_par(self):
        self.assertGreaterEqual(self.hoja.count("Distancia calculada:"), 17)

    def test_no_exige_json_al_founder(self):
        self.assertNotIn("{", self.hoja.split("PAR #1")[0])

    def test_avisa_del_error_propio_en_lm026_lm027(self):
        """El agente etiquetó ese par mirando el slug, no el titular real."""
        self.assertIn("AVISO", self.hoja)
        self.assertIn("anticipo/arras/pena", self.hoja)


class TestParseo(unittest.TestCase):
    def test_formato_simple(self):
        r = fr.parsear_respuestas("1A\n2B\n3C\n4D")
        self.assertEqual(r[1], ("A", ""))
        self.assertEqual(r[2], ("B", ""))
        self.assertEqual(r[4], ("D", ""))

    def test_tolera_espacios_y_minusculas(self):
        r = fr.parsear_respuestas("1 a\n 2  b ")
        self.assertEqual(r[1][0], "A")
        self.assertEqual(r[2][0], "B")

    def test_admite_razon_opcional(self):
        r = fr.parsear_respuestas("1A - porque son la misma pregunta")
        self.assertEqual(r[1], ("A", "porque son la misma pregunta"))

    def test_ignora_lineas_irrelevantes(self):
        r = fr.parsear_respuestas("hola\n1A\nesto no cuenta\n2B")
        self.assertEqual(set(r), {1, 2})

    def test_respuestas_parciales(self):
        r = fr.parsear_respuestas("1A\n5C")
        self.assertEqual(set(r), {1, 5})


class TestIncorporacion(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.salida = Path(self.tmp.name) / "founder.json"

    def tearDown(self):
        self.tmp.cleanup()

    def test_no_toca_el_fichero_original(self):
        original_antes = Path(fr.EVAL_PATH).read_text(encoding="utf-8")
        fr.incorporar_decisiones({1: ("A", "")}, salida_path=self.salida)
        original_despues = Path(fr.EVAL_PATH).read_text(encoding="utf-8")
        self.assertEqual(original_antes, original_despues)

    def test_escribe_un_fichero_nuevo(self):
        fr.incorporar_decisiones({1: ("A", "")}, salida_path=self.salida)
        self.assertTrue(self.salida.is_file())

    def test_trazabilidad_completa_por_par(self):
        fr.incorporar_decisiones({1: ("B", "coexisten de verdad")}, salida_path=self.salida)
        data = json.loads(self.salida.read_text(encoding="utf-8"))
        par1 = data["pares"][0]
        for campo in ("agent_label", "founder_label", "founder_label_mapped",
                     "fecha", "cambio", "founder_razon"):
            self.assertIn(campo, par1)
        self.assertEqual(par1["founder_label"], "B")
        self.assertEqual(par1["founder_label_mapped"], "COEXISTIR")
        self.assertEqual(par1["founder_razon"], "coexisten de verdad")

    def test_pares_sin_responder_quedan_marcados(self):
        rep = fr.incorporar_decisiones({1: ("A", "")}, salida_path=self.salida)
        self.assertEqual(rep.respondidos, 1)
        self.assertEqual(len(rep.sin_responder), 17)
        data = json.loads(self.salida.read_text(encoding="utf-8"))
        self.assertEqual(data["pares"][1]["cambio"], "SIN_DECISION")

    def test_confirma_vs_corrige(self):
        # Par #1 es EQUIVALENTE según el agente. Founder dice A (bloquear) -> confirma.
        respuestas = {1: ("A", "")}
        rep = fr.incorporar_decisiones(respuestas, salida_path=self.salida)
        self.assertEqual(rep.confirma_agente, 1)
        self.assertEqual(rep.corrige_agente, 0)

    def test_corrige_cuando_el_founder_discrepa(self):
        # Par #1 es EQUIVALENTE según el agente. Founder dice C (distinta) -> corrige.
        rep = fr.incorporar_decisiones({1: ("C", "")}, salida_path=self.salida)
        self.assertEqual(rep.corrige_agente, 1)

    def test_estado_completo_cuando_no_faltan_respuestas(self):
        data_original = json.loads(Path(fr.EVAL_PATH).read_text(encoding="utf-8"))
        n = len(data_original["pares"])
        respuestas = {i: ("C", "") for i in range(1, n + 1)}
        fr.incorporar_decisiones(respuestas, salida_path=self.salida)
        data = json.loads(self.salida.read_text(encoding="utf-8"))
        self.assertEqual(data["estado"], "GROUND_TRUTH_FOUNDER")

    def test_estado_parcial_si_faltan_respuestas(self):
        fr.incorporar_decisiones({1: ("A", "")}, salida_path=self.salida)
        data = json.loads(self.salida.read_text(encoding="utf-8"))
        self.assertEqual(data["estado"], "GROUND_TRUTH_FOUNDER_PARCIAL")

    def test_reejecutar_con_nuevas_respuestas_no_acumula_pares_duplicados(self):
        fr.incorporar_decisiones({1: ("A", "")}, salida_path=self.salida)
        fr.incorporar_decisiones({1: ("A", ""), 2: ("B", "")}, salida_path=self.salida)
        data = json.loads(self.salida.read_text(encoding="utf-8"))
        original = json.loads(Path(fr.EVAL_PATH).read_text(encoding="utf-8"))
        self.assertEqual(len(data["pares"]), len(original["pares"]))


class TestIntegracionConCalibracion(unittest.TestCase):
    def test_calibration_usa_el_fichero_founder_si_existe(self):
        import calibration as cal
        with tempfile.TemporaryDirectory() as d:
            salida = Path(d) / "eval-umbral-founder.json"
            n = len(json.loads(Path(fr.EVAL_PATH).read_text(encoding="utf-8"))["pares"])
            fr.incorporar_decisiones({i: ("C", "") for i in range(1, n + 1)},
                                     salida_path=salida)
            regs, _ = ci.construir_registros()
            pares, meta = cal.cargar_pares_etiquetados(regs, path=salida)
            self.assertTrue(pares)
            for _, _, etiqueta, _ in pares:
                self.assertEqual(etiqueta, "DISTINTA")


if __name__ == "__main__":
    unittest.main()
