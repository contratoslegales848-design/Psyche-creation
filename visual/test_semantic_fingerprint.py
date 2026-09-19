"""La huella semántica debe detectar lo que memory.py no podía: repetición
de SIGNIFICADO bajo ropa distinta."""

import unittest

from semantic_fingerprint import (
    SemanticFingerprint, EJES_SEMANTICOS, EJES_VISUALES, UMBRAL_EQUIVALENCIA,
    mas_similar,
)


def fp(**kw):
    base = dict(materia="civil", submateria="arrendamiento",
                concepto_nucleo="deposito en garantia", relacion="dinero retenido",
                familia_editorial="mito", necesidad="corregir",
                pregunta_resuelta="puede el arrendador quedarse el deposito",
                angulo="critico", contexto_funcional="despues_del_dano",
                rol_lector="persona", consecuencia="se pierde dinero")
    base.update(kw)
    return SemanticFingerprint(**base)


class TestPesos(unittest.TestCase):
    def test_pesos_semanticos_suman_uno(self):
        self.assertAlmostEqual(sum(EJES_SEMANTICOS.values()), 1.0, places=6)

    def test_pesos_visuales_suman_uno(self):
        self.assertAlmostEqual(sum(EJES_VISUALES.values()), 1.0, places=6)

    def test_el_nucleo_domina(self):
        """concepto y familia editorial pesan más que materia sola: cambiar de
        materia no debe bastar para acreditar novedad."""
        self.assertGreater(EJES_SEMANTICOS["concepto_nucleo"], EJES_SEMANTICOS["materia"])
        self.assertGreater(EJES_SEMANTICOS["familia_editorial"], EJES_SEMANTICOS["materia"])

    def test_los_ejes_expresivos_no_entran_en_la_distancia_semantica(self):
        """La regla central del canon, como aserción ejecutable."""
        for eje in ("hook", "formato", "emocion"):
            self.assertNotIn(eje, EJES_SEMANTICOS)


class TestEquivalencia(unittest.TestCase):
    def test_cambiar_hook_no_crea_novedad(self):
        a = fp(content_id="a", hook="Lo que nadie te dice")
        b = fp(content_id="b", hook="La verdad sobre tu depósito")
        self.assertEqual(a.distancia_semantica(b).valor, 0.0)
        self.assertTrue(a.equivalente_a(b))

    def test_cambiar_formato_y_estilo_no_crea_novedad(self):
        a = fp(content_id="a", formato="frase", direccion_artistica="oleo_clasico_institucional")
        b = fp(content_id="b", formato="historia", direccion_artistica="claroscuro_de_museo")
        self.assertTrue(a.equivalente_a(b))

    def test_arte_radicalmente_distinto_no_compra_novedad(self):
        """Distancia visual máxima y distancia semántica nula a la vez: el
        caso exacto que reporta el fundador."""
        a = fp(content_id="a", metafora="llave", escena="oficina", camara="cenital",
               composicion="centrada_axial", objeto_protagonista="llave",
               material="latón", iluminacion="dura", direccion_artistica="oleo_narrativo")
        b = fp(content_id="b", metafora="grieta", escena="patio", camara="picado",
               composicion="diagonal", objeto_protagonista="muro",
               material="hormigón", iluminacion="difusa", direccion_artistica="foto_impasto")
        self.assertEqual(a.distancia_visual(b).valor, 1.0)
        self.assertTrue(a.equivalente_a(b))

    def test_otra_familia_editorial_si_crea_novedad(self):
        """Canon §3: arrendamiento+mito != arrendamiento+checklist."""
        a = fp(content_id="a")
        b = fp(content_id="b", familia_editorial="checklist", necesidad="prepararse",
               pregunta_resuelta="que revisar antes de entregar el deposito",
               angulo="procedimental", contexto_funcional="antes_de_firmar")
        self.assertFalse(a.equivalente_a(b))
        self.assertGreater(a.distancia_semantica(b).valor, UMBRAL_EQUIVALENCIA)

    def test_materias_distintas_son_distintas(self):
        a = fp(content_id="a")
        b = fp(content_id="b", materia="penal", submateria="tipicidad",
               concepto_nucleo="dolo y culpa", familia_editorial="diferencia",
               necesidad="distinguir", pregunta_resuelta="en que se diferencia el dolo",
               relacion="dos figuras cercanas", consecuencia="")
        self.assertGreater(a.distancia_semantica(b).valor, 0.7)


class TestAusenciaDeDato(unittest.TestCase):
    def test_huellas_vacias_no_son_comparables(self):
        """Sin evidencia, no se afirma ni identidad ni diferencia."""
        d = SemanticFingerprint().distancia_semantica(SemanticFingerprint())
        self.assertFalse(d.comparable)
        self.assertEqual(d.ejes_evaluados, 0)

    def test_vacia_nunca_es_equivalente(self):
        self.assertFalse(SemanticFingerprint().equivalente_a(SemanticFingerprint()))

    def test_un_lado_declara_y_el_otro_no_cuenta_como_distinto(self):
        a = SemanticFingerprint(materia="civil")
        b = SemanticFingerprint(materia="")
        d = a.distancia_semantica(b)
        self.assertTrue(d.comparable)
        self.assertEqual(d.valor, 1.0)

    def test_un_eje_ausente_no_diluye_la_señal(self):
        """Renormalización: comparar 3 ejes iguales da 0.0, no 0.7."""
        a = SemanticFingerprint(materia="civil", familia_editorial="mito", necesidad="corregir")
        b = SemanticFingerprint(materia="civil", familia_editorial="mito", necesidad="corregir")
        d = a.distancia_semantica(b)
        self.assertEqual(d.valor, 0.0)
        self.assertEqual(d.ejes_evaluados, 3)


class TestTextoLibre(unittest.TestCase):
    def test_solapamiento_parcial_en_concepto(self):
        """'usucapión' vs 'usucapión y prescripción adquisitiva': el mismo
        tema escrito distinto no debe dar distancia máxima."""
        a = SemanticFingerprint(concepto_nucleo="usucapion")
        b = SemanticFingerprint(concepto_nucleo="usucapion y prescripcion adquisitiva")
        d = a.distancia_semantica(b)
        self.assertGreater(d.valor, 0.0)
        self.assertLess(d.valor, 1.0)

    def test_vocabulario_cerrado_es_binario(self):
        a = SemanticFingerprint(materia="civil")
        b = SemanticFingerprint(materia="civil mercantil")
        self.assertEqual(a.distancia_semantica(b).valor, 1.0)


class TestPuenteVisual(unittest.TestCase):
    def test_produce_una_entrada_de_memoria_visual_usable(self):
        """El puente que impide que esto sea un sistema paralelo."""
        import memory
        e = fp(content_id="x", metafora="llave", escena="oficina",
               objeto_protagonista="llave", camara="cenital").visual_entry(generation_id="g1")
        self.assertIsInstance(e, memory.VisualMemoryEntry)
        self.assertEqual(e.content_id, "x")
        self.assertEqual(e.metaphor, "llave")
        self.assertEqual(e.materia, "civil")

    def test_la_memoria_visual_existente_sigue_puntuando(self):
        import memory
        e = fp(content_id="x", escena="oficina", objeto_protagonista="llave").visual_entry()
        m = memory.VisualMemory([e])
        self.assertGreater(m.assess(e).score, 0)


class TestMasSimilar(unittest.TestCase):
    def test_encuentra_el_mas_cercano(self):
        a = fp(content_id="a")
        casi = fp(content_id="casi", hook="otro")
        lejos = fp(content_id="lejos", materia="penal", concepto_nucleo="dolo",
                   familia_editorial="diferencia", necesidad="distinguir",
                   pregunta_resuelta="que distingue el dolo", submateria="tipicidad")
        encontrado, d = mas_similar(a, [lejos, casi])
        self.assertEqual(encontrado.content_id, "casi")
        self.assertEqual(d.valor, 0.0)

    def test_poblacion_incomparable_devuelve_nada(self):
        encontrado, d = mas_similar(SemanticFingerprint(), [SemanticFingerprint()])
        self.assertIsNone(encontrado)
        self.assertIsNone(d)


class TestSerializacion(unittest.TestCase):
    def test_ida_y_vuelta(self):
        a = fp(content_id="a", emocion="urgencia")
        self.assertEqual(SemanticFingerprint.from_dict(a.to_dict()), a)

    def test_ignora_campos_desconocidos(self):
        d = fp(content_id="a").to_dict()
        d["campo_inventado"] = "x"
        self.assertEqual(SemanticFingerprint.from_dict(d).content_id, "a")

    def test_declara_los_22_campos_del_handoff(self):
        campos = set(SemanticFingerprint.__dataclass_fields__)
        exigidos = {
            "materia", "submateria", "concepto_nucleo", "relacion", "familia_editorial",
            "necesidad", "pregunta_resuelta", "angulo", "contexto_funcional",
            "rol_lector", "consecuencia", "hook", "formato", "metafora", "escena",
            "composicion", "objeto_protagonista", "material", "camara", "iluminacion",
            "direccion_artistica", "emocion",
        }
        self.assertEqual(exigidos - campos, set())


if __name__ == "__main__":
    unittest.main()
