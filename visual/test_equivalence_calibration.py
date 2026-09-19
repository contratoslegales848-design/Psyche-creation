"""Recalibración de la política de dos niveles — Paso 3 del mandato."""

import unittest

import equivalence_calibration as rc
from equivalence_policy import BLOQUEO


class TestFuentesDeDatos(unittest.TestCase):
    def test_ocho_positivos_sinteticos_minimos(self):
        self.assertEqual(len(rc.positivos_sinteticos()), 8)

    def test_dieciocho_negativos_reales_del_founder(self):
        negativos, meta = rc.negativos_reales()
        self.assertEqual(len(negativos), 18)
        self.assertEqual(meta["fuente_etiquetas"], "FOUNDER")

    def test_los_positivos_no_se_mezclan_con_los_negativos(self):
        positivos = {a.content_id for a, _ in rc.positivos_sinteticos()}
        negativos, _ = rc.negativos_reales()
        negativos_ids = {a.content_id for a, _ in negativos} | {b.content_id for _, b in negativos}
        self.assertEqual(positivos & negativos_ids, set())


class TestEvaluarAlertaMinimo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.positivos = rc.positivos_sinteticos()
        cls.negativos, _ = rc.negativos_reales()

    def test_recall_estricto_perfecto_en_el_positivo_minimo(self):
        """Los 8 positivos 'solo_hook' son idénticos salvo el hook: distancia
        0.0, corroboración completa por construcción. Cualquier alerta_minimo
        > 0 debe bloquearlos todos."""
        p = rc.evaluar_alerta_minimo(0.25, self.positivos, self.negativos)
        self.assertEqual(p.tp, 8)
        self.assertEqual(p.fn, 0)
        self.assertEqual(p.recall_estricto, 1.0)

    def test_cero_falsos_positivos_sobre_negativos_reales_del_founder(self):
        """Ningún par que el Founder marcó B/C debe auto-bloquearse: son el
        ground truth negativo real, no un derivado."""
        for alerta_minimo in rc.CANDIDATOS_ALERTA_MINIMO:
            p = rc.evaluar_alerta_minimo(alerta_minimo, self.positivos, self.negativos)
            self.assertEqual(p.fp, 0, alerta_minimo)
            self.assertEqual(p.precision_estricta, 1.0, alerta_minimo)

    def test_alerta_minimo_cero_no_bloquea_nada(self):
        p = rc.evaluar_alerta_minimo(0.0, self.positivos, self.negativos)
        self.assertEqual(p.tp, 0)
        self.assertGreater(p.positivos_en_alerta + p.fn, 0)

    def test_cobertura_con_revision_nunca_es_menor_que_recall_estricto(self):
        for alerta_minimo in rc.CANDIDATOS_ALERTA_MINIMO:
            p = rc.evaluar_alerta_minimo(alerta_minimo, self.positivos, self.negativos)
            self.assertGreaterEqual(p.cobertura_con_revision, p.recall_estricto, alerta_minimo)

    def test_negativos_en_alerta_es_costo_de_revision_no_de_bloqueo(self):
        """Un negativo en ALERTA_DE_PROXIMIDAD no es un falso positivo: pide
        revisión humana, no se descarta ni se bloquea solo."""
        p = rc.evaluar_alerta_minimo(0.28, self.positivos, self.negativos)
        self.assertGreater(p.negativos_en_alerta, 0)
        self.assertEqual(p.fp, 0)


class TestPropuestaDeCutoff(unittest.TestCase):
    def test_propone_el_alerta_minimo_mas_bajo_entre_los_de_mejor_recall(self):
        """Entre umbrales empatados en recall y con fp=0, el más CONSERVADOR
        (más bajo, ensancha menos el bloqueo duro) es el que se propone —
        nunca el más laxo, coherente con 'señal, no bloqueo autónomo'."""
        informe = rc.informe_recalibracion()
        propuesto = informe["cutoff_propuesto"]
        self.assertIsNotNone(propuesto)
        mismos_recall = [p for p in informe["puntos"]
                         if p["fp"] == 0 and p["recall_estricto"] == propuesto["recall_estricto"]]
        self.assertEqual(propuesto["alerta_minimo"], min(p["alerta_minimo"] for p in mismos_recall))

    def test_ningun_punto_propuesto_tiene_falsos_positivos(self):
        informe = rc.informe_recalibracion()
        self.assertEqual(informe["cutoff_propuesto"]["fp"], 0)


class TestInformeNoSeActiva(unittest.TestCase):
    def test_el_informe_se_declara_propuesta_no_activada(self):
        informe = rc.informe_recalibracion()
        self.assertEqual(informe["estado"], "PROPUESTA_NO_ACTIVADA")
        self.assertIn("no activa", informe["aviso"].lower())

    def test_documenta_la_limitacion_del_positivo_minimo(self):
        informe = rc.informe_recalibracion()
        self.assertIn("techo", informe["limitacion_positivos"].lower())

    def test_reporta_distribucion_de_distancias_de_ambos_lados(self):
        informe = rc.informe_recalibracion()
        self.assertEqual(informe["distribucion_distancias_positivos"]["n"], 8)
        self.assertEqual(informe["distribucion_distancias_negativos"]["n"], 18)

    def test_es_determinista(self):
        a = rc.informe_recalibracion()
        b = rc.informe_recalibracion()
        self.assertEqual(a["puntos"], b["puntos"])
        self.assertEqual(a["cutoff_propuesto"], b["cutoff_propuesto"])


if __name__ == "__main__":
    unittest.main()
