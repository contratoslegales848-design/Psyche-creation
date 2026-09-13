"""La emoción debe DERIVARSE, rotar con sentido y no poder fabricar alarma."""

import unittest

import emotion
from brief import VisualBrief


class TestCatalogo(unittest.TestCase):
    def test_cada_emocion_declara_su_direccion_de_arte(self):
        """Una emoción sin traducción visual sería decoración."""
        for nombre, d in emotion.EMOCIONES.items():
            for campo in ("intensidad", "escala", "composicion", "camara", "luz",
                          "textura", "ritmo", "narrativa"):
                self.assertTrue(str(d.get(campo, "")).strip(),
                                f"{nombre} no declara {campo}")

    def test_las_tablas_estan_normalizadas(self):
        """normaliza() convierte '_' en espacio: si las claves no se
        normalizan, ninguna familia con guion bajo casa jamás."""
        for clave in emotion._AJUSTE_NORM:
            self.assertNotIn("_", clave)
        for clave in emotion._BASE_NORM:
            self.assertNotIn("_", clave)

    def test_familias_con_guion_bajo_si_resuelven(self):
        for fam, esperada in (("plazo_prescripcion", "urgencia"),
                              ("senal_de_alerta", "inquietud"),
                              ("historia_del_derecho", "asombro"),
                              ("lenguaje_juridico_explicado", "claridad")):
            p = emotion.derivar(necesidad="entender", familia_editorial=fam,
                                consecuencia="una consecuencia real")
            self.assertEqual(p.emocion, esperada, fam)

    def test_sin_caracteres_fuera_del_alfabeto_latino(self):
        """Regresión: un typo coló caracteres cirílicos en una cadena."""
        for d in emotion.EMOCIONES.values():
            for v in d.values():
                for c in str(v):
                    self.assertLess(ord(c), 0x370, f"carácter no latino en {v!r}")


class TestDerivacion(unittest.TestCase):
    def test_es_determinista(self):
        kw = dict(necesidad="prevenir", familia_editorial="riesgo", consecuencia="multa")
        self.assertEqual(emotion.derivar(**kw).emocion, emotion.derivar(**kw).emocion)

    def test_la_necesidad_ancla(self):
        p = emotion.derivar(necesidad="reflexionar")
        self.assertEqual(p.emocion, "reflexion")
        self.assertTrue(any("necesidad" in r for r in p.razones))

    def test_la_familia_editorial_ajusta(self):
        p = emotion.derivar(necesidad="entender", familia_editorial="rareza_juridica")
        self.assertEqual(p.emocion, "asombro")
        self.assertTrue(any("familia editorial" in r for r in p.razones))

    def test_sin_entradas_no_inventa_emocion(self):
        """El canon prohíbe la emoción decorativa: sin origen, no hay emoción."""
        p = emotion.derivar()
        self.assertEqual(p.emocion, "")
        self.assertEqual(p.intensidad, 0)
        self.assertTrue(p.razones)

    def test_siempre_explica_por_que(self):
        p = emotion.derivar(necesidad="actuar", consecuencia="se pierde el plazo")
        self.assertTrue(p.razones)


class TestNoFabricarAlarma(unittest.TestCase):
    def test_urgencia_exige_consecuencia_declarada(self):
        con = emotion.derivar(necesidad="actuar", consecuencia="caduca el derecho")
        sin = emotion.derivar(necesidad="actuar", consecuencia="")
        self.assertEqual(con.emocion, "urgencia")
        self.assertNotEqual(sin.emocion, "urgencia")
        self.assertTrue(any("no se fabrica alarma" in r.lower() for r in sin.razones))

    def test_indignacion_exige_consecuencia(self):
        p = emotion.derivar(necesidad="reclamar", consecuencia="")
        self.assertNotEqual(p.emocion, "indignacion_contenida")

    def test_ninguna_emocion_intensa_sobrevive_sin_consecuencia(self):
        for nec in emotion.BASE_POR_NECESIDAD:
            p = emotion.derivar(necesidad=nec, consecuencia="")
            if p.emocion:
                self.assertLess(p.intensidad, emotion.INTENSIDAD_EXIGE_CONSECUENCIA,
                                f"{nec} produjo {p.emocion} sin consecuencia")

    def test_la_rotacion_respeta_la_misma_regla(self):
        """Rotar no puede ser una puerta trasera hacia la alarma inventada."""
        evitar = ["claridad", "reflexion", "curiosidad", "confianza", "empatia", "alivio"]
        p = emotion.derivar(necesidad="entender", consecuencia="", evitar=evitar)
        self.assertLess(p.intensidad, emotion.INTENSIDAD_EXIGE_CONSECUENCIA)


class TestRolYRotacion(unittest.TestCase):
    def test_el_profesional_atempera(self):
        p = emotion.derivar(necesidad="actuar", consecuencia="caduca", rol_lector="profesional")
        self.assertEqual(p.emocion, "tension")
        self.assertTrue(any("atempera" in r for r in p.razones))

    def test_rota_cuando_la_emocion_esta_reciente(self):
        base = emotion.derivar(necesidad="entender")
        rotada = emotion.derivar(necesidad="entender", evitar=[base.emocion])
        self.assertNotEqual(rotada.emocion, base.emocion)
        self.assertTrue(any("rota a" in r for r in rotada.razones))

    def test_la_rotacion_no_es_azar(self):
        kw = dict(necesidad="entender", evitar=["claridad"])
        self.assertEqual(emotion.derivar(**kw).emocion, emotion.derivar(**kw).emocion)

    def test_conserva_la_emocion_si_no_hay_alternativa_coherente(self):
        todas = [e for e in emotion.EMOCIONES if e != "claridad"]
        p = emotion.derivar(necesidad="entender", evitar=todas + ["claridad"])
        self.assertTrue(p.emocion)
        self.assertTrue(any("no hay alternativa" in r for r in p.razones))


class TestAplicarABrief(unittest.TestCase):
    def brief(self):
        return VisualBrief(content_id="c1", formato="reel_9_16",
                           visual_family="oleo_narrativo", subject="s",
                           environment="e", camera="frontal", focal_point="f")

    def test_modifica_la_direccion_de_arte(self):
        p = emotion.derivar(necesidad="actuar", consecuencia="caduca el plazo")
        nuevo, cambios = emotion.aplicar_a_brief(self.brief(), p)
        self.assertEqual(nuevo.camera, p.camara)
        self.assertEqual(nuevo.key_light, p.luz)
        self.assertIn("camera", cambios)

    def test_no_muta_el_brief_original(self):
        b = self.brief()
        p = emotion.derivar(necesidad="actuar", consecuencia="caduca")
        emotion.aplicar_a_brief(b, p)
        self.assertEqual(b.camera, "frontal")

    def test_no_toca_el_canon(self):
        b = self.brief()
        p = emotion.derivar(necesidad="actuar", consecuencia="caduca")
        nuevo, _ = emotion.aplicar_a_brief(b, p)
        self.assertEqual(nuevo.content_id, b.content_id)
        self.assertEqual(nuevo.formato, b.formato)
        self.assertEqual(nuevo.tiene_carga_juridica, b.tiene_carga_juridica)

    def test_el_brief_resultante_sigue_siendo_valido(self):
        from brief import VisualPolicy
        pol = VisualPolicy.load()
        b = self.brief()
        b.acento_frio_objeto = "placa de acero azulado"
        b.marca_superficie = sorted(pol.data["marca"]["superficies_permitidas"])[0]
        b.formato = sorted(pol.data["formatos"])[0]
        b.visual_family = pol.familias[0]
        self.assertEqual(b.validate(pol), [])
        p = emotion.derivar(necesidad="actuar", consecuencia="caduca")
        nuevo, _ = emotion.aplicar_a_brief(b, p)
        self.assertEqual(nuevo.validate(pol), [])

    def test_sin_perfil_no_cambia_nada(self):
        b = self.brief()
        nuevo, cambios = emotion.aplicar_a_brief(b, emotion.EmotionalProfile())
        self.assertEqual(cambios, {})
        self.assertIs(nuevo, b)


if __name__ == "__main__":
    unittest.main()
