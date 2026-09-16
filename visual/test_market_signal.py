"""Partes III-VI del mandato "Fase post-implementación" (16-sep-2026):
modelo de señal, extracción granular, demanda profesional real."""

import unittest

import market_signal as ms
from vacancy_radar import VacancyPosting


class TestExtraccionGranular(unittest.TestCase):
    def test_ejemplo_literal_del_mandato_reduccion_de_capital(self):
        conceptos = ms.extraer_conceptos_granulares(
            "revisión de reducción de capital y protección de acreedores", "mercantil")
        self.assertIn("reduccion_de_capital_y_proteccion_de_acreedores", conceptos)

    def test_ejemplo_literal_del_mandato_formalizacion_de_asambleas(self):
        conceptos = ms.extraer_conceptos_granulares(
            "coordinación de asambleas y actas societarias", "mercantil")
        self.assertIn("formalizacion_de_asambleas", conceptos)

    def test_ejemplo_literal_del_mandato_beneficiario_controlador(self):
        conceptos = ms.extraer_conceptos_granulares(
            "actualización de beneficiario controlador ante el SAT", "corporativo_compliance")
        self.assertIn("beneficiario_controlador", conceptos)

    def test_sin_coincidencia_no_inventa_concepto(self):
        conceptos = ms.extraer_conceptos_granulares(
            "abogado corporativo junior con experiencia", "mercantil")
        self.assertEqual(conceptos, [])

    def test_materia_sin_vocabulario_granular_declarado_no_falla(self):
        # 'penal' no tiene entrada en CONCEPTOS_GRANULARES_POR_MATERIA todavía:
        # debe devolver vacío, no lanzar KeyError.
        self.assertEqual(ms.extraer_conceptos_granulares("litigio penal", "penal"), [])

    def test_un_texto_puede_disparar_varios_conceptos_de_la_misma_materia(self):
        conceptos = ms.extraer_conceptos_granulares(
            "revisión de asambleas, poderes y libros corporativos", "mercantil")
        self.assertIn("formalizacion_de_asambleas", conceptos)
        self.assertIn("limites_materiales_de_un_poder", conceptos)
        self.assertIn("actualizacion_de_libros_corporativos", conceptos)


class TestSignalDesdeVacante(unittest.TestCase):
    def test_vacante_sin_concepto_granular_produce_senal_a_nivel_materia(self):
        p = VacancyPosting(titulo="Abogado Corporativo Jr.", url="http://x/1")
        señales = ms.senales_desde_vacante(p)
        self.assertEqual(len(señales), 1)
        self.assertEqual(señales[0].legal_area, "mercantil")
        self.assertEqual(señales[0].subarea, "")
        self.assertEqual(señales[0].normalized_concept, "mercantil")

    def test_vacante_con_concepto_granular_lo_declara_en_subarea(self):
        p = VacancyPosting(titulo="Gerente Fusiones y Adquisiciones Legal", url="http://x/2")
        señales = ms.senales_desde_vacante(p)
        conceptos = {s.normalized_concept for s in señales}
        self.assertIn("fusiones y adquisiciones", conceptos)

    def test_vacante_sin_materia_reconocida_no_produce_senales(self):
        p = VacancyPosting(titulo="Legal Escalations Specialist", url="http://x/3")
        self.assertEqual(ms.senales_desde_vacante(p), [])

    def test_verification_status_nace_no_verificado(self):
        p = VacancyPosting(titulo="Abogado Laboral", url="http://x/4")
        for s in ms.senales_desde_vacante(p):
            self.assertEqual(s.verification_status, ms.NO_VERIFICADO)
            self.assertEqual(s.proxima_accion, ms.PROXIMA_ACCION_VERIFICACION)


class TestDemandaProfesionalReal(unittest.TestCase):
    def test_demanda_es_baja_por_defecto_sin_repeticion(self):
        postings = [VacancyPosting(titulo="Abogado Fiscalista", url="http://x/5")]
        señales = ms.procesar_vacantes(postings)
        self.assertEqual(señales[0].professional_demand, "BAJA")

    def test_demanda_sube_con_frecuencia_real_no_inventada(self):
        postings = [VacancyPosting(titulo="Abogado Corporativo", url=f"http://x/{i}")
                   for i in range(5)]
        señales = ms.procesar_vacantes(postings)
        # 5 apariciones reales del mismo concepto (materia mercantil, sin
        # granularidad) -> ALTA, por encima del umbral, nunca por afirmación
        # de "viral".
        self.assertTrue(all(s.professional_demand == "ALTA" for s in señales))
        self.assertTrue(all(s.frequency == 5 for s in señales))

    def test_nunca_afirma_viralidad_ni_tendencia_futura(self):
        # Regresión directa de la Parte VI: ningún campo del modelo afirma
        # "viral" ni predice el futuro -- professional_demand es un bucket
        # sobre conteo pasado/presente real.
        campos = ms.Signal().to_dict()
        self.assertNotIn("viral", str(campos).lower())
        self.assertNotIn("tendencia_futura", campos)


class TestRecencia(unittest.TestCase):
    def test_fecha_reciente_se_marca_reciente(self):
        from datetime import date
        hoy = date(2026, 9, 16)
        self.assertEqual(ms._recencia_desde_fecha("2026-09-10", hoy=hoy), "RECIENTE")

    def test_fecha_antigua_se_marca_antigua(self):
        from datetime import date
        hoy = date(2026, 9, 16)
        self.assertEqual(ms._recencia_desde_fecha("2025-01-01", hoy=hoy), "ANTIGUA")

    def test_fecha_ausente_o_no_parseable_no_se_asume_reciente(self):
        self.assertEqual(ms._recencia_desde_fecha(""), "NO_DECLARADA")
        self.assertEqual(ms._recencia_desde_fecha("no es una fecha"), "NO_DECLARADA")


class TestAgruparPorConcepto(unittest.TestCase):
    def test_agrupa_sin_duplicar_el_mismo_concepto(self):
        postings = [VacancyPosting(titulo="Abogado Corporativo", url=f"http://x/{i}")
                   for i in range(3)]
        señales = ms.procesar_vacantes(postings)
        filas = ms.agrupar_por_concepto(señales)
        self.assertEqual(len(filas), 1)
        self.assertEqual(filas[0]["frequency"], 3)

    def test_ordena_por_frecuencia_descendente(self):
        postings = ([VacancyPosting(titulo="Abogado Corporativo", url=f"http://x/{i}")
                    for i in range(3)] +
                   [VacancyPosting(titulo="Abogado Fiscalista", url=f"http://y/{i}")
                    for i in range(1)])
        filas = ms.agrupar_por_concepto(ms.procesar_vacantes(postings))
        self.assertGreaterEqual(filas[0]["frequency"], filas[-1]["frequency"])


if __name__ == "__main__":
    unittest.main()
