"""Saturación editorial: un score DISTINTO de la repetición semántica."""

import unittest

import editorial_saturation as es
from semantic_fingerprint import SemanticFingerprint as S
from semantic_memory import SemanticMemory, GENERADA, HISTORICA, DESCARTADA


def entrada(fam="caso_cotidiano", nec="entender"):
    return S(familia_editorial=fam, necesidad=nec)


class TestSaturacion(unittest.TestCase):
    def test_memoria_vacia_no_satura(self):
        a = es.evaluar("mito", "corregir", SemanticMemory())
        self.assertEqual(a.nivel, "BAJO")
        self.assertFalse(a.bloquea)

    def test_familia_repetida_satura(self):
        m = SemanticMemory()
        for i in range(5):
            m.record(entrada(), GENERADA)
        a = es.evaluar("caso_cotidiano", "distinguir", m)
        self.assertEqual(a.nivel, "ALTO")
        self.assertTrue(a.bloquea)

    def test_familia_nueva_no_satura_aunque_otra_este_saturada(self):
        m = SemanticMemory()
        for i in range(5):
            m.record(entrada(), GENERADA)
        a = es.evaluar("etimologia", "recordar", m)
        self.assertEqual(a.nivel, "BAJO")

    def test_historica_no_cuenta_para_saturacion(self):
        """El corpus (48% caso_cotidiano) no puede prohibir esa familia para
        siempre: HISTORICA queda fuera de la ventana reciente."""
        m = SemanticMemory()
        for i in range(50):
            m.record(entrada(), HISTORICA)
        a = es.evaluar("caso_cotidiano", "entender", m)
        self.assertEqual(a.nivel, "BAJO")
        self.assertEqual(a.ocurrencias_familia, 0)

    def test_descartada_no_cuenta_para_saturacion(self):
        """Un rechazo del Founder no es 'hemos insistido demasiado'."""
        m = SemanticMemory()
        for i in range(5):
            m.record(entrada(), DESCARTADA)
        a = es.evaluar("caso_cotidiano", "entender", m)
        self.assertEqual(a.ocurrencias_familia, 0)


class TestIndependenciaDeLaRepeticionSemantica(unittest.TestCase):
    def test_pieza_semanticamente_nueva_puede_saturar(self):
        """El caso central del mandato: jurídicamente nueva, saturada igual."""
        m = SemanticMemory()
        for i in range(5):
            m.record(S(content_id=f"h{i}", materia="civil", concepto_nucleo=f"concepto{i}",
                      familia_editorial="caso_cotidiano", necesidad="entender"), GENERADA)
        nueva = S(content_id="nueva", materia="penal", concepto_nucleo="algo completamente distinto",
                 familia_editorial="caso_cotidiano", necesidad="entender")
        veredicto_semantico = m.evaluar(nueva)
        self.assertFalse(veredicto_semantico.bloquea, "debería ser semánticamente nueva")
        sat = es.evaluar("caso_cotidiano", "entender", m)
        self.assertTrue(sat.bloquea, "pero debería estar saturada editorialmente")

    def test_pieza_semanticamente_repetida_puede_no_estar_saturada(self):
        """Y al revés: el score de saturación no repite el trabajo de memoria."""
        m = SemanticMemory()
        m.record(S(content_id="a", materia="civil", concepto_nucleo="deposito",
                  familia_editorial="mito", necesidad="corregir"), GENERADA)
        sat = es.evaluar("mito", "corregir", m)
        self.assertFalse(sat.bloquea)


class TestDistribucion(unittest.TestCase):
    def test_distribucion_reciente_cuenta_por_eje(self):
        m = SemanticMemory()
        for _ in range(3):
            m.record(entrada("mito"), GENERADA)
        for _ in range(2):
            m.record(entrada("checklist"), GENERADA)
        dist = es.distribucion_reciente(m)
        self.assertEqual(dist["mito"], 3)
        self.assertEqual(dist["checklist"], 2)

    def test_distribucion_ignora_historica(self):
        m = SemanticMemory()
        m.record(entrada("mito"), HISTORICA)
        self.assertEqual(es.distribucion_reciente(m), {})


if __name__ == "__main__":
    unittest.main()
