"""Partes VII-VIII del mandato "Fase post-implementación" (16-sep-2026):
clasificación anti-repetición temática y taxonomía editorial derivada."""

import unittest

import topic_classification as tc
from semantic_fingerprint import SemanticFingerprint as S
from semantic_memory import SemanticMemory, GENERADA, PUBLICADA


class Candidato:
    """Doble mínimo de TopicCandidate: sólo lo que estas funciones leen."""

    def __init__(self, **kw):
        defaults = dict(candidate_id="x", materia="", submateria="", familia_editorial="",
                        necesidad="", pregunta_resuelta="", concepto_nucleo="",
                        relacion="", angulo="", contexto_funcional="", rol_lector="",
                        consecuencia="", hook="", formato="", emocion="", profundidad="")
        defaults.update(kw)
        self.__dict__.update(defaults)

    def fingerprint(self):
        return S(content_id=self.candidate_id, materia=self.materia, submateria=self.submateria,
                 concepto_nucleo=self.concepto_nucleo, relacion=self.relacion,
                 familia_editorial=self.familia_editorial, necesidad=self.necesidad,
                 pregunta_resuelta=self.pregunta_resuelta, angulo=self.angulo,
                 contexto_funcional=self.contexto_funcional, rol_lector=self.rol_lector,
                 consecuencia=self.consecuencia, hook=self.hook, formato=self.formato,
                 emocion=self.emocion)


class TestClasificarRepeticion(unittest.TestCase):
    def test_sin_memoria_es_nuevo(self):
        c = Candidato(materia="civil")
        r = tc.clasificar_repeticion(c, None)
        self.assertEqual(r.etiqueta, tc.NUEVO)

    def test_memoria_vacia_es_nuevo(self):
        c = Candidato(materia="civil", concepto_nucleo="algo")
        r = tc.clasificar_repeticion(c, SemanticMemory())
        self.assertEqual(r.etiqueta, tc.NUEVO)

    def test_ejemplo_literal_del_mandato_whatsapp_como_prueba_es_repetido(self):
        """'¿Puede valer un WhatsApp como prueba?' == 'Valor probatorio de
        conversaciones de mensajería' — el ejemplo exacto de la Parte VII."""
        m = SemanticMemory()
        m.record(S(content_id="LM-1", materia="civil",
                   concepto_nucleo="valor probatorio de conversaciones de mensajeria",
                   familia_editorial="concepto", necesidad="entender",
                   pregunta_resuelta="puede valer un whatsapp como prueba"), PUBLICADA)
        c = Candidato(candidate_id="x1", materia="civil",
                     concepto_nucleo="valor probatorio de whatsapp como prueba",
                     familia_editorial="concepto", necesidad="entender",
                     pregunta_resuelta="puede valer un whatsapp como prueba")
        r = tc.clasificar_repeticion(c, m)
        self.assertEqual(r.etiqueta, tc.REPETIDO)
        self.assertEqual(r.contra, "LM-1")

    def test_saturacion_editorial_alta_se_etiqueta_saturado_no_repetido(self):
        m = SemanticMemory()
        for i in range(3):
            m.record(S(content_id=f"g{i}", materia="laboral",
                       familia_editorial="caso_cotidiano", necesidad="entender"), GENERADA)
        c = Candidato(candidate_id="x2", materia="laboral",
                     concepto_nucleo="un asunto laboral genuinamente distinto",
                     familia_editorial="caso_cotidiano", necesidad="entender",
                     pregunta_resuelta="algo que no se ha preguntado antes")
        r = tc.clasificar_repeticion(c, m)
        self.assertEqual(r.etiqueta, tc.SATURADO)

    def test_variante_justificada_cuando_hay_parecido_pero_no_bloquea(self):
        m = SemanticMemory()
        m.record(S(content_id="LM-2", materia="civil", concepto_nucleo="requisitos del contrato",
                   familia_editorial="concepto", necesidad="entender",
                   pregunta_resuelta="que hace valido un contrato"), PUBLICADA)
        # mismo campo semántico (materia+familia+necesidad), pregunta y concepto
        # bastante distintos -> cercano pero no equivalente.
        c = Candidato(candidate_id="x3", materia="civil",
                     concepto_nucleo="efectos de la nulidad contractual",
                     familia_editorial="concepto", necesidad="entender",
                     pregunta_resuelta="que pasa cuando se anula un contrato")
        r = tc.clasificar_repeticion(c, m)
        self.assertIn(r.etiqueta, (tc.VARIANTE_JUSTIFICADA, tc.NUEVO))
        # el punto real del test: si hay evidencia de parecido real sin
        # bloquear, nunca puede leerse como REPETIDO ni SATURADO.
        self.assertNotIn(r.etiqueta, (tc.REPETIDO, tc.SATURADO))

    def test_nuevo_cuando_no_hay_parecido_real(self):
        m = SemanticMemory()
        m.record(S(content_id="LM-3", materia="penal", concepto_nucleo="tipos penales",
                   familia_editorial="concepto", necesidad="entender"), PUBLICADA)
        c = Candidato(candidate_id="x4", materia="ambiental",
                     concepto_nucleo="gestion de residuos peligrosos",
                     familia_editorial="checklist", necesidad="prepararse",
                     pregunta_resuelta="que revisar antes de una auditoria ambiental")
        r = tc.clasificar_repeticion(c, m)
        self.assertEqual(r.etiqueta, tc.NUEVO)


class TestReportarMezclaEditorial(unittest.TestCase):
    def test_mezcla_equilibrada_no_produce_avisos(self):
        candidatos = ([Candidato(profundidad="base") for _ in range(4)] +
                     [Candidato(profundidad="media") for _ in range(4)] +
                     [Candidato(profundidad="alta") for _ in range(2)])
        r = tc.reportar_mezcla_editorial(candidatos)
        self.assertEqual(r["avisos"], [])

    def test_mezcla_desequilibrada_produce_aviso_informativo_no_bloqueo(self):
        candidatos = [Candidato(profundidad="base") for _ in range(10)]
        r = tc.reportar_mezcla_editorial(candidatos)
        self.assertTrue(r["avisos"])
        self.assertEqual(r["conteo_por_profundidad"]["base"], 10)
        # nunca un veredicto de aprobado/rechazado -- solo un dict informativo.
        self.assertNotIn("aceptado", r)
        self.assertNotIn("bloquea", r)

    def test_escala_a_lotes_de_otro_tamano(self):
        candidatos = [Candidato(profundidad="base") for _ in range(2)]
        r = tc.reportar_mezcla_editorial(candidatos)
        self.assertEqual(r["total"], 2)

    def test_lote_vacio_no_falla(self):
        r = tc.reportar_mezcla_editorial([])
        self.assertEqual(r["total"], 0)


class TestClasificarTaxonomia(unittest.TestCase):
    def test_materia_con_etiqueta_directa(self):
        c = Candidato(materia="mercantil", familia_editorial="concepto", profundidad="media")
        etiqueta, _ = tc.clasificar_taxonomia(c)
        self.assertEqual(etiqueta, "MERCANTIL")

    def test_familia_editorial_de_funcion_domina_sobre_materia(self):
        c = Candidato(materia="mercantil", familia_editorial="historia_del_derecho",
                      profundidad="base")
        etiqueta, _ = tc.clasificar_taxonomia(c)
        self.assertEqual(etiqueta, "HISTÓRICO")

    def test_muy_especializado_requiere_familia_tecnica_y_profundidad_alta(self):
        c = Candidato(materia="cultura_y_literatura_juridica",
                     familia_editorial="lenguaje_juridico_explicado", profundidad="alta")
        etiqueta, _ = tc.clasificar_taxonomia(c)
        self.assertEqual(etiqueta, "MUY ESPECIALIZADO")

    def test_familia_tecnica_sin_profundidad_alta_no_es_muy_especializado(self):
        c = Candidato(materia="cultura_y_literatura_juridica",
                     familia_editorial="lenguaje_juridico_explicado", profundidad="base")
        etiqueta, _ = tc.clasificar_taxonomia(c)
        self.assertNotEqual(etiqueta, "MUY ESPECIALIZADO")

    def test_fallback_por_profundidad_sin_materia_reconocida(self):
        c = Candidato(materia="consumo", familia_editorial="checklist", profundidad="base")
        etiqueta, _ = tc.clasificar_taxonomia(c)
        self.assertEqual(etiqueta, "GENERAL CON SUSTANCIA")

    def test_sin_ningun_dato_reconocible_es_otros(self):
        c = Candidato(materia="", familia_editorial="", profundidad="")
        etiqueta, _ = tc.clasificar_taxonomia(c)
        self.assertEqual(etiqueta, "OTROS")

    def test_es_determinista(self):
        c = Candidato(materia="inmobiliario", familia_editorial="checklist", profundidad="media")
        a, _ = tc.clasificar_taxonomia(c)
        b, _ = tc.clasificar_taxonomia(c)
        self.assertEqual(a, b)


if __name__ == "__main__":
    unittest.main()
