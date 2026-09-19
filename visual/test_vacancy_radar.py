"""Radar de temas desde vacantes (Founder, 15-sep-2026): 'siempre se
alimente y se vaya depurando lo menos importante'. Nunca auto-aplica: toda
salida es propuesta, y la depuración exige evidencia acumulada, no una
sola corrida sin señal."""

import json
import tempfile
import unittest
from pathlib import Path

import vacancy_radar as vr


class TestNormalizacion(unittest.TestCase):
    def test_no_descarta_tokens_con_puntuacion(self):
        """A diferencia de memory.normaliza(), texto libre de vacantes reales
        trae siglas con barra ('PLD/FT') que no deben perderse enteras."""
        self.assertIn("pld", vr.normaliza("Oficial de cumplimiento PLD/FT"))
        self.assertIn("ft", vr.normaliza("Oficial de cumplimiento PLD/FT"))

    def test_quita_acentos_y_normaliza_mayusculas(self):
        self.assertEqual(vr.normaliza("Protección DE Datos"), "proteccion de datos")

    def test_vacio_es_vacio(self):
        self.assertEqual(vr.normaliza(""), "")
        self.assertEqual(vr.normaliza(None), "")


class TestClasificacion(unittest.TestCase):
    def test_coincidencia_literal_asigna_materia(self):
        c = vr.clasificar_vacante(vr.VacancyPosting(titulo="Abogado Inmobiliario Transaccional"))
        self.assertIn("inmobiliario", c.materias)
        self.assertIn("inmobiliario", c.palabras_encontradas)

    def test_una_vacante_puede_coincidir_con_varias_materias(self):
        c = vr.clasificar_vacante(vr.VacancyPosting(titulo="Abogado Corporativo / Notarial"))
        self.assertIn("mercantil", c.materias)
        self.assertIn("notarial_registral", c.materias)

    def test_sin_coincidencia_queda_sin_materia_reconocida_nunca_por_defecto(self):
        c = vr.clasificar_vacante(vr.VacancyPosting(titulo="Legal Escalations Specialist"))
        self.assertEqual(c.materias, [])
        self.assertTrue(c.sin_materia_reconocida)

    def test_nunca_asigna_una_materia_sin_palabra_clave_encontrada(self):
        """Invariante: toda materia en `materias` tiene su evidencia en
        `palabras_encontradas` — nunca una asignación 'porque sí'."""
        for texto in ("Abogado Fiscalista", "Oficial de Cumplimiento PLD",
                      "Abogado Inmobiliario", "Legal Assistant remote"):
            c = vr.clasificar_vacante(vr.VacancyPosting(titulo=texto))
            for m in c.materias:
                self.assertTrue(c.palabras_encontradas.get(m))


class TestCoberturaReal(unittest.TestCase):
    def test_cuenta_contra_el_corpus_historico_real(self):
        cobertura = vr.cobertura_real_por_materia()
        # civil es la materia con más piezas reales (CONTRATOS + OBLIGACIONES
        # mapean a civil en corpus_import.TEMA_A_MATERIA): debe ser > 0.
        self.assertGreater(cobertura.get("civil", 0), 0)

    def test_materia_sin_ninguna_pieza_real_no_aparece_o_es_cero(self):
        cobertura = vr.cobertura_real_por_materia()
        self.assertEqual(cobertura.get("notarial_registral", 0), 0)


class TestCandidatosNuevos(unittest.TestCase):
    def test_umbral_exige_al_menos_dos_senales(self):
        postings = [vr.VacancyPosting(titulo="Abogado Fiscalista")]
        result = vr.ejecutar_radar(postings, registros=[])
        self.assertEqual(result.candidatos_nuevos, [])

    def test_con_suficientes_senales_y_baja_cobertura_propone(self):
        postings = [vr.VacancyPosting(titulo="Abogado Fiscalista", url=f"u{i}")
                   for i in range(3)]
        result = vr.ejecutar_radar(postings, registros=[])
        materias = [c.materia for c in result.candidatos_nuevos]
        self.assertIn("fiscal", materias)
        propuesta = next(c for c in result.candidatos_nuevos if c.materia == "fiscal")
        self.assertEqual(propuesta.senales_vacantes, 3)
        self.assertEqual(propuesta.cobertura_real, 0)
        self.assertTrue(propuesta.ejemplos)

    def test_materia_con_cobertura_alta_no_se_propone_aunque_haya_demanda(self):
        class FakeRegistro:
            def __init__(self, materia):
                self.materia = materia
        registros = [FakeRegistro("fiscal") for _ in range(5)]
        postings = [vr.VacancyPosting(titulo="Abogado Fiscalista") for _ in range(4)]
        result = vr.ejecutar_radar(postings, registros=registros)
        self.assertNotIn("fiscal", [c.materia for c in result.candidatos_nuevos])


class TestCandidatosADepurar(unittest.TestCase):
    def test_materia_protegida_nunca_se_propone_aunque_no_haya_senal(self):
        result = vr.ejecutar_radar([], registros=[],
                                   historial_previo=[{"senales_por_materia": {}}])
        materias = [c.materia for c in result.candidatos_a_depurar]
        for protegida in vr.MATERIAS_PROTEGIDAS:
            self.assertNotIn(protegida, materias)

    def test_una_sola_corrida_sin_senal_no_basta_para_proponer_depurar(self):
        """Una fotografía no prueba que un tema no importe."""
        result = vr.ejecutar_radar([], registros=[], historial_previo=[])
        self.assertEqual(result.candidatos_a_depurar, [])

    def test_dos_corridas_consecutivas_sin_senal_si_proponen(self):
        historial = [{"senales_por_materia": {}}]
        result = vr.ejecutar_radar([], registros=[], historial_previo=historial)
        materias = [c.materia for c in result.candidatos_a_depurar]
        self.assertIn("transito", materias)
        self.assertIn("ambiental", materias)

    def test_materia_con_cobertura_real_nunca_se_propone_para_depurar(self):
        class FakeRegistro:
            materia = "ambiental"
        result = vr.ejecutar_radar([], registros=[FakeRegistro()],
                                   historial_previo=[{"senales_por_materia": {}}])
        self.assertNotIn("ambiental", [c.materia for c in result.candidatos_a_depurar])

    def test_una_senal_en_la_corrida_actual_retira_del_candidato(self):
        postings = [vr.VacancyPosting(titulo="Abogado ambiental medio ambiente")]
        result = vr.ejecutar_radar(postings, registros=[],
                                   historial_previo=[{"senales_por_materia": {}}])
        self.assertNotIn("ambiental", [c.materia for c in result.candidatos_a_depurar])


class TestPersistenciaAppendOnly(unittest.TestCase):
    def test_registrar_corrida_no_borra_el_historial_previo(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "log.json"
            r1 = vr.ejecutar_radar([vr.VacancyPosting(titulo="Abogado Fiscalista")], registros=[])
            vr.registrar_corrida(r1, path=path)
            r2 = vr.ejecutar_radar([vr.VacancyPosting(titulo="Abogado Inmobiliario")], registros=[])
            vr.registrar_corrida(r2, path=path)
            historial = vr.cargar_historial(path)
            self.assertEqual(len(historial), 2)

    def test_sin_archivo_previo_devuelve_lista_vacia(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(vr.cargar_historial(Path(d) / "no-existe.json"), [])

    def test_el_archivo_es_json_valido_con_schema_version(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "log.json"
            r = vr.ejecutar_radar([], registros=[])
            vr.registrar_corrida(r, path=path)
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertIn("schema_version", data)
            self.assertEqual(len(data["corridas"]), 1)


class TestRenderMarkdown(unittest.TestCase):
    def test_incluye_las_secciones_clave(self):
        postings = [vr.VacancyPosting(titulo="Abogado Fiscalista", url=f"u{i}") for i in range(3)]
        result = vr.ejecutar_radar(postings, registros=[])
        md = vr.render_markdown(result)
        for encabezado in ("Señales por materia", "Candidatos a tema nuevo",
                           "Candidatos a depurar"):
            self.assertIn(encabezado, md)

    def test_nunca_se_cae_con_un_resultado_vacio(self):
        result = vr.ejecutar_radar([], registros=[])
        md = vr.render_markdown(result)
        self.assertIsInstance(md, str)
        self.assertTrue(md)


class TestNuncaModificaElSeedNiElCorpus(unittest.TestCase):
    def test_no_hay_ninguna_escritura_de_archivo_fuera_del_log_dedicado(self):
        """Invariante estructural: este módulo propone, nunca aplica — la
        única llamada de escritura en todo el archivo debe ser la del log
        append-only (`registrar_corrida`), nunca a materias-seed-v1.json,
        al corpus, ni a ningún banco de contenido."""
        import inspect
        fuente = inspect.getsource(vr)
        llamadas_escritura = fuente.count("write_text(")
        self.assertEqual(llamadas_escritura, 1, "debe haber exactamente una escritura de archivo")
        self.assertIn("def registrar_corrida", fuente)

    def test_registrar_corrida_solo_escribe_en_el_log_dedicado(self):
        self.assertTrue(str(vr.LOG_PATH).endswith("radar-vacantes-log.json"))


if __name__ == "__main__":
    unittest.main()
