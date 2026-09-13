"""Registro editorial y generación combinatoria de candidatos."""

import unittest

import editorial
import universe
from lanes import LEGALMENTE_GENERAL


class TestRegistroEditorial(unittest.TestCase):
    def setUp(self):
        self.u = editorial.EditorialUniverse.load()

    def test_carga_la_semilla_canonica(self):
        self.assertTrue(self.u.version)
        self.assertGreaterEqual(len(self.u), 50)

    def test_toda_familia_declara_su_funcion(self):
        for n in self.u.names():
            self.assertTrue(self.u.get(n).funcion_editorial.strip(), n)

    def test_familia_desconocida_no_se_infiere(self):
        with self.assertRaises(editorial.EditorialError):
            self.u.get("familia_que_nadie_declaro")

    def test_el_registro_es_abierto(self):
        """Canon §11: las listas son semilla, no techo."""
        antes = len(self.u)
        self.u.register_familia(editorial.FamiliaEditorial(
            nombre="nueva_puerta", funcion_editorial="probar el alta",
            tension_tipica="t"))
        self.assertEqual(len(self.u), antes + 1)
        self.assertEqual(self.u.get("nueva_puerta").funcion_editorial, "probar el alta")

    def test_rechaza_duplicado_exacto(self):
        with self.assertRaises(editorial.EditorialError):
            self.u.register_familia(editorial.FamiliaEditorial(
                nombre=self.u.names()[0], funcion_editorial="x", tension_tipica="y"))

    def test_rechaza_familia_sin_funcion(self):
        with self.assertRaises(editorial.EditorialError):
            self.u.register_familia(editorial.FamiliaEditorial(
                nombre="sin_funcion", funcion_editorial="  ", tension_tipica="y"))

    def test_declara_las_familias_que_exige_el_founder(self):
        """Handoff §3: deben aparecer de forma natural, no excepcional."""
        nombres = set(self.u.names())
        for exigida in ("mito", "diferencia", "checklist", "historia_del_derecho",
                        "jurista", "criminalistica_forense", "medicina_legal",
                        "etimologia", "rareza_juridica", "negociacion",
                        "conciliacion_mediacion", "reparacion", "prevencion",
                        "cumplimiento_compliance", "maxima_aforismo", "duda_frecuente",
                        "asesoria_orientacion", "costumbre_juridica", "prueba",
                        "documento_clave", "proceso", "error_frecuente", "obligacion",
                        "derecho", "requisito", "prohibicion"):
            self.assertIn(exigida, nombres)

    def test_afinidades(self):
        self.assertIn("checklist", self.u.familias_para_necesidad("prepararse"))
        self.assertTrue(self.u.familias_para_rol("profesional"))

    def test_ejes_auxiliares_presentes(self):
        for eje in (self.u.necesidades, self.u.roles_lector, self.u.angulos,
                    self.u.contextos_funcionales, self.u.profundidades,
                    self.u.formatos_editoriales):
            self.assertTrue(eje)


class TestSemillaMaterias(unittest.TestCase):
    def test_carga(self):
        v, m = universe.cargar_materias()
        self.assertTrue(v)
        self.assertGreaterEqual(len(m), 20)

    def test_toda_materia_tiene_submaterias_y_cuota(self):
        _, m = universe.cargar_materias()
        for nombre, d in m.items():
            self.assertTrue(d["submaterias"], nombre)
            self.assertGreaterEqual(d["cuota_max_por_lote_10"], 1, nombre)

    def test_digital_tiene_cuota_de_uno(self):
        """'00 LEER PRIMERO' §3.A: digital/datos máximo 1 de 10."""
        _, m = universe.cargar_materias()
        self.assertEqual(m["digital_datos"]["cuota_max_por_lote_10"], 1)

    def test_no_sobrerrepresenta_las_zonas_faciles(self):
        _, m = universe.cargar_materias()
        for facil in ("penal", "civil", "digital_datos"):
            self.assertLessEqual(m[facil]["cuota_max_por_lote_10"], 2)


class TestCandidatos(unittest.TestCase):
    def test_nace_sin_verificar(self):
        """CLAUDE.md §4: combinar etiquetas no produce verdad jurídica."""
        for c in universe.build_reserve(objetivo_lote=5, seed=1):
            self.assertEqual(c.estado_verificacion, universe.NO_VERIFICADO)
            self.assertEqual(c.proxima_accion, universe.ACCION_VERIFICACION)

    def test_es_reproducible_con_seed(self):
        a = universe.build_reserve(objetivo_lote=10, seed=42)
        b = universe.build_reserve(objetivo_lote=10, seed=42)
        self.assertEqual([c.to_dict() for c in a], [c.to_dict() for c in b])

    def test_seeds_distintas_dan_reservas_distintas(self):
        a = universe.build_reserve(objetivo_lote=10, seed=1)
        b = universe.build_reserve(objetivo_lote=10, seed=2)
        self.assertNotEqual([c.candidate_id + c.materia + c.familia_editorial for c in a],
                            [c.candidate_id + c.materia + c.familia_editorial for c in b])

    def test_la_reserva_respeta_el_minimo_canonico(self):
        """Reserva mínima de 40 candidatos para un lote de 10."""
        self.assertGreaterEqual(len(universe.build_reserve(objetivo_lote=10, seed=1)), 40)

    def test_la_reserva_cubre_muchas_materias(self):
        r = universe.build_reserve(objetivo_lote=10, seed=5)
        self.assertGreaterEqual(len({c.materia for c in r}), 15)

    def test_la_reserva_cubre_muchas_familias(self):
        r = universe.build_reserve(objetivo_lote=10, seed=5)
        self.assertGreaterEqual(len({c.familia_editorial for c in r}), 15)

    def test_la_coherencia_necesidad_familia_se_respeta(self):
        u = editorial.EditorialUniverse.load()
        for c in universe.build_reserve(objetivo_lote=20, seed=9):
            afines = u.get(c.familia_editorial).necesidades_afines
            if afines:
                self.assertIn(c.necesidad, afines, c.familia_editorial)

    def test_la_consecuencia_solo_aparece_donde_la_familia_la_implica(self):
        """Si se inventara para todas, dispararía urgencia sobre piezas que
        no la sostienen."""
        r = universe.build_reserve(objetivo_lote=30, seed=11)
        con = {c.familia_editorial for c in r if c.consecuencia}
        sin = {c.familia_editorial for c in r if not c.consecuencia}
        self.assertTrue(con)
        self.assertTrue(sin)
        self.assertFalse(con & sin)

    def test_todo_candidato_lleva_perfil_emocional(self):
        for c in universe.build_reserve(objetivo_lote=10, seed=3):
            self.assertIn("emocion", c.perfil_emocional)
            self.assertTrue(c.perfil_emocional.get("razones"))

    def test_produce_una_huella_semantica(self):
        c = universe.build_reserve(objetivo_lote=3, seed=1)[0]
        fp = c.fingerprint()
        self.assertEqual(fp.content_id, c.candidate_id)
        self.assertEqual(fp.materia, c.materia)
        self.assertEqual(fp.familia_editorial, c.familia_editorial)

    def test_la_huella_del_candidato_no_finge_datos_visuales(self):
        """Todavía no hay plan visual: inventarlo sería fabricar evidencia."""
        fp = universe.build_reserve(objetivo_lote=3, seed=1)[0].fingerprint()
        for eje in ("metafora", "escena", "composicion", "direccion_artistica"):
            self.assertEqual(getattr(fp, eje), "")


class TestSeleccion(unittest.TestCase):
    def lote(self, seed=7, n=10):
        return universe.select_batch(universe.build_reserve(objetivo_lote=n, seed=seed), n=n)

    def test_selecciona_el_lote_completo(self):
        rep = self.lote()
        self.assertTrue(rep.completo)
        self.assertEqual(len(rep.seleccionados), 10)

    def test_respeta_el_tope_por_materia(self):
        _, materias = universe.cargar_materias()
        for seed in (1, 2, 3, 7, 13):
            rep = self.lote(seed)
            frec = {}
            for c in rep.seleccionados:
                frec[c.materia] = frec.get(c.materia, 0) + 1
            for mat, cuenta in frec.items():
                self.assertLessEqual(cuenta, materias[mat]["cuota_max_por_lote_10"],
                                     f"seed={seed} materia={mat}")

    def test_no_repite_familia_editorial(self):
        for seed in (1, 2, 3, 7, 13):
            fams = [c.familia_editorial for c in self.lote(seed).seleccionados]
            self.assertEqual(len(fams), len(set(fams)), f"seed={seed}")

    def test_limita_la_repeticion_emocional(self):
        for seed in (1, 2, 3, 7, 13):
            emos = {}
            for c in self.lote(seed).seleccionados:
                if c.emocion:
                    emos[c.emocion] = emos.get(c.emocion, 0) + 1
            for e, n in emos.items():
                self.assertLessEqual(n, universe.MAX_POR_EMOCION_POR_10, f"seed={seed} {e}")

    def test_no_rellena_con_candidatos_debiles(self):
        """Reserva mínima: debe devolver menos y declararlo, nunca rellenar."""
        pequena = universe.build_reserve(objetivo_lote=10, seed=1)[:3]
        rep = universe.select_batch(pequena, n=10)
        self.assertLess(len(rep.seleccionados), 10)
        self.assertFalse(rep.completo)
        self.assertTrue(any("NO se rellena" in a for a in rep.avisos))

    def test_avisa_si_la_reserva_es_insuficiente(self):
        rep = universe.select_batch(universe.build_reserve(objetivo_lote=10, seed=1)[:12], n=10)
        self.assertTrue(any("por debajo del mínimo" in a for a in rep.avisos))

    def test_es_reproducible(self):
        a = [c.candidate_id for c in self.lote(7).seleccionados]
        b = [c.candidate_id for c in self.lote(7).seleccionados]
        self.assertEqual(a, b)


if __name__ == "__main__":
    unittest.main()
