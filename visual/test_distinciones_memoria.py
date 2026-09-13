"""Las cinco distinciones que la memoria debe saber hacer (mandato §8).

    MISMO TEMA                      -> bloquear
    MISMO TEMA + NUEVA FUNCIÓN ÚTIL -> dejar pasar
    NUEVO ÁNGULO                    -> dejar pasar
    NUEVA PREGUNTA                  -> dejar pasar
    NUEVO CONOCIMIENTO              -> dejar pasar

Y la regla que las sostiene: ningún campo suelto puede dominar. Cambiar sólo
familia_editorial, hook, estilo, emoción o metáfora NO convierte una pregunta
jurídica repetida en contenido nuevo — pero un cambio real de FUNCIÓN (familia
+ necesidad + pregunta + ángulo) sí, porque entonces sirve a otra persona en
otro momento.
"""

import unittest

from semantic_fingerprint import SemanticFingerprint, EJES_SEMANTICOS, UMBRAL_EQUIVALENCIA


def pieza(**kw):
    base = dict(
        content_id="base", materia="civil", submateria="arrendamiento",
        concepto_nucleo="deposito en garantia del arrendamiento",
        relacion="dinero retenido al terminar", familia_editorial="mito",
        necesidad="corregir",
        pregunta_resuelta="puede el arrendador quedarse el deposito sin justificar",
        angulo="critico", contexto_funcional="despues_del_dano",
        rol_lector="persona", consecuencia="se pierde dinero",
        hook="Lo que nadie te dice", formato="frase", emocion="sorpresa",
        metafora="una llave que ya no abre", escena="patio de vecindad",
        direccion_artistica="oleo_narrativo")
    base.update(kw)
    return SemanticFingerprint(**base)


class TestNingunCampoDomina(unittest.TestCase):
    def test_ningun_eje_supera_un_cuarto_del_peso(self):
        """Si un solo campo pesara más, cambiarlo bastaría para comprar novedad."""
        for eje, peso in EJES_SEMANTICOS.items():
            self.assertLessEqual(peso, 0.25, eje)

    def test_cambiar_solo_el_hook_no_crea_novedad(self):
        self.assertTrue(pieza().equivalente_a(pieza(hook="Otro titular por completo")))

    def test_cambiar_solo_el_estilo_no_crea_novedad(self):
        self.assertTrue(pieza().equivalente_a(
            pieza(direccion_artistica="estampa ukiyo-e", escena="azotea urbana")))

    def test_cambiar_solo_la_emocion_no_crea_novedad(self):
        self.assertTrue(pieza().equivalente_a(pieza(emocion="gravedad")))

    def test_cambiar_solo_la_metafora_no_crea_novedad(self):
        self.assertTrue(pieza().equivalente_a(pieza(metafora="un muro con una grieta")))

    def test_cambiar_solo_la_familia_editorial_no_crea_novedad(self):
        """Regla explícita del mandato: la etiqueta editorial por sí sola no
        convierte una pregunta repetida en contenido nuevo."""
        self.assertTrue(pieza().equivalente_a(pieza(familia_editorial="checklist")))

    def test_cambiarlo_todo_menos_el_nucleo_sigue_sin_crear_novedad(self):
        disfraz = pieza(hook="otro", formato="historia", emocion="alivio",
                        metafora="otra", direccion_artistica="foto_impasto",
                        escena="cocina familiar", camara="cenital")
        self.assertTrue(pieza().equivalente_a(disfraz))


class TestLasCincoDistinciones(unittest.TestCase):
    def test_mismo_tema_se_bloquea(self):
        self.assertTrue(pieza().equivalente_a(pieza(content_id="otra", hook="x")))

    def test_mismo_tema_con_nueva_funcion_util_pasa(self):
        """El caso que el mandato pide NO bloquear: arrendamiento + mito
        frente a arrendamiento + checklist, resolviendo necesidades distintas."""
        checklist = pieza(
            content_id="checklist", familia_editorial="checklist",
            necesidad="prepararse", angulo="procedimental",
            contexto_funcional="antes_de_firmar",
            pregunta_resuelta="que revisar y fotografiar antes de entregar el deposito")
        self.assertFalse(pieza().equivalente_a(checklist))

    def test_nuevo_angulo_pasa(self):
        otro = pieza(content_id="hist", angulo="historico",
                     familia_editorial="historia_del_derecho", necesidad="recordar",
                     pregunta_resuelta="de donde viene la figura del deposito en garantia",
                     contexto_funcional="aprendizaje")
        self.assertFalse(pieza().equivalente_a(otro))

    def test_nueva_pregunta_pasa(self):
        otra = pieza(content_id="plazo", familia_editorial="plazo_prescripcion",
                     necesidad="actuar", angulo="procedimental",
                     pregunta_resuelta="cuanto tiempo hay para reclamar el deposito",
                     concepto_nucleo="plazo para reclamar el deposito",
                     contexto_funcional="despues_del_dano")
        self.assertFalse(pieza().equivalente_a(otra))

    def test_nuevo_conocimiento_pasa(self):
        otro = pieza(content_id="nuevo", materia="procesal", submateria="prueba",
                     concepto_nucleo="carga de la prueba sobre el estado del inmueble",
                     familia_editorial="carga_de_la_prueba", necesidad="distinguir",
                     angulo="probatorio",
                     pregunta_resuelta="a quien toca probar el estado en que se entrego",
                     relacion="quien debe acreditar")
        self.assertFalse(pieza().equivalente_a(otro))


class TestGradacion(unittest.TestCase):
    def test_la_distancia_crece_con_el_cambio_real_de_funcion(self):
        d_hook = pieza().distancia_semantica(pieza(hook="otro")).valor
        d_fam = pieza().distancia_semantica(pieza(familia_editorial="checklist")).valor
        d_fun = pieza().distancia_semantica(pieza(
            familia_editorial="checklist", necesidad="prepararse",
            angulo="procedimental", contexto_funcional="antes_de_firmar",
            pregunta_resuelta="que revisar antes de entregar")).valor
        self.assertLess(d_hook, d_fam)
        self.assertLess(d_fam, d_fun)
        self.assertLess(d_fam, UMBRAL_EQUIVALENCIA)
        self.assertGreater(d_fun, UMBRAL_EQUIVALENCIA)

    def test_el_umbral_cae_entre_ambos_casos(self):
        """Es lo que hace utilizable el umbral: separa 'otra etiqueta' de
        'otra función'."""
        solo_etiqueta = pieza().distancia_semantica(
            pieza(familia_editorial="checklist")).valor
        funcion_real = pieza().distancia_semantica(pieza(
            familia_editorial="checklist", necesidad="prepararse",
            angulo="procedimental", contexto_funcional="antes_de_firmar",
            pregunta_resuelta="que revisar antes de entregar")).valor
        self.assertTrue(solo_etiqueta < UMBRAL_EQUIVALENCIA < funcion_real)


if __name__ == "__main__":
    unittest.main()
