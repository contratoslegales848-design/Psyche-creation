"""El corpus histórico debe migrar sin inventar y sin duplicarse."""

import unittest

import corpus_import as ci
from semantic_memory import SemanticMemory, GENERADA, APROBADA, HISTORICA


class CorpusBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.regs, cls.errores = ci.construir_registros()


class TestFuente(CorpusBase):
    def test_las_174_piezas_se_parsean(self):
        self.assertEqual(len(self.regs), 174)

    def test_sin_errores_de_parseo(self):
        self.assertEqual(self.errores, [])

    def test_los_dos_documentos_se_validan_cruzadamente(self):
        """174 en el doc 1 y 174 en el doc 2, unidos por slug sin huérfanos."""
        crudos, errores = ci.cargar_fuente()
        self.assertEqual(len(crudos), 174)
        self.assertEqual(errores, [])

    def test_identificadores_unicos(self):
        ids = [r.content_id for r in self.regs]
        self.assertEqual(len(ids), len(set(ids)))

    def test_slugs_unicos(self):
        slugs = [r.guion for r in self.regs]
        self.assertEqual(len(slugs), len(set(slugs)))

    def test_todo_registro_declara_procedencia(self):
        for r in self.regs:
            self.assertTrue(r.fuente)
            self.assertTrue(r.fecha)
            self.assertTrue(r.content_id.startswith("LM-"))

    def test_campos_literales_llegan_completos(self):
        """Hook, metáfora y ejes visuales son texto literal del documento."""
        for r in self.regs:
            for campo in ("hook", "metafora", "direccion_artistica", "escena",
                          "camara", "composicion", "material", "objeto_protagonista"):
                self.assertTrue(str(getattr(r, campo)).strip(), f"{r.content_id}:{campo}")


class TestNoInventar(CorpusBase):
    def test_los_ejes_que_nadie_declaro_quedan_unknown(self):
        """El corpus es anterior a estos ejes: inventarlos contaminaría la
        memoria con puertas editoriales que nunca se abrieron."""
        for r in self.regs:
            for campo in ("angulo", "contexto_funcional", "rol_lector",
                          "consecuencia", "pregunta_resuelta", "emocion"):
                self.assertEqual(getattr(r, campo), ci.UNKNOWN, f"{r.content_id}:{campo}")

    def test_toda_inferencia_declara_su_confianza(self):
        for r in self.regs:
            self.assertTrue(r.confianza_extraccion)
            for campo, nivel in r.confianza_extraccion.items():
                self.assertIn(nivel, (ci.ALTA, ci.MEDIA, ci.BAJA, ci.NINGUNA))

    def test_un_campo_sin_evidencia_declara_confianza_ninguna(self):
        for r in self.regs:
            if r.familia_editorial == ci.UNKNOWN:
                self.assertEqual(r.confianza_extraccion["familia_editorial"], ci.NINGUNA)

    def test_la_necesidad_no_es_mas_fiable_que_la_familia_de_la_que_deriva(self):
        niveles = {ci.NINGUNA: 0, ci.BAJA: 1, ci.MEDIA: 2, ci.ALTA: 3}
        for r in self.regs:
            self.assertLessEqual(niveles[r.confianza_extraccion["necesidad"]],
                                 niveles[r.confianza_extraccion["familia_editorial"]],
                                 r.content_id)

    def test_unknown_no_viaja_a_la_huella_como_valor(self):
        """'UNKNOWN' literal haría que dos piezas sin dato pareciesen coincidir."""
        for r in self.regs:
            for v in r.fingerprint().to_dict().values():
                self.assertNotEqual(v, ci.UNKNOWN)

    def test_hay_familias_sin_clasificar(self):
        """Si todo quedara clasificado, sería señal de que se está forzando."""
        self.assertTrue([r for r in self.regs if r.familia_editorial == ci.UNKNOWN])


class TestClasificacionRetroactiva(unittest.TestCase):
    def test_marcador_explicito_da_confianza_alta(self):
        for slug, esperada in (("mito-contrato-sin-papel", "mito"),
                               ("concepto-buena-fe", "concepto"),
                               ("diferencia-perito-testigo", "diferencia"),
                               ("pasos-antes-de-firmar", "primeros_pasos"),
                               ("listado-derechos-al-firmar-contrato-trabajo", "checklist"),
                               ("tecnicismo-corpus-delicti", "lenguaje_juridico_explicado"),
                               ("cita-el-proceso-kafka", "maxima_aforismo")):
            fam, conf = ci.clasificar_familia_editorial(slug)
            self.assertEqual(fam, esperada, slug)
            self.assertEqual(conf, ci.ALTA, slug)

    def test_marcador_tras_linkedin_tambien_cuenta(self):
        fam, conf = ci.clasificar_familia_editorial("linkedin-mito-due-diligence-rapida")
        self.assertEqual(fam, "mito")
        self.assertEqual(conf, ci.ALTA)

    def test_patron_vs_es_una_diferencia(self):
        fam, conf = ci.clasificar_familia_editorial("depositos-vs-fianzas")
        self.assertEqual(fam, "diferencia")
        self.assertEqual(conf, ci.MEDIA)

    def test_forma_narrativa_da_confianza_baja(self):
        fam, conf = ci.clasificar_familia_editorial("el-acto-que-nadie-notifico")
        self.assertEqual(fam, "caso_cotidiano")
        self.assertEqual(conf, ci.BAJA)

    def test_sin_evidencia_devuelve_unknown(self):
        fam, conf = ci.clasificar_familia_editorial("anatomia-de-una-firma")
        self.assertEqual(fam, ci.UNKNOWN)
        self.assertEqual(conf, ci.NINGUNA)

    def test_es_determinista(self):
        for slug in ("mito-contrato-sin-papel", "el-acto-que-nadie-notifico", "xyz"):
            self.assertEqual(ci.clasificar_familia_editorial(slug),
                             ci.clasificar_familia_editorial(slug))


class TestRefinamientoDeMateria(CorpusBase):
    def test_sucesiones_no_quedan_sepultadas_bajo_familia(self):
        """El banco archivó herencia y testamento en FAMILIA; sin refinar,
        'sucesorio' parecería territorio virgen y no lo es."""
        sucesorio = [r for r in self.regs if r.materia == "sucesorio"]
        self.assertGreaterEqual(len(sucesorio), 4)
        for r in sucesorio:
            self.assertEqual(r.confianza_extraccion["materia"], ci.MEDIA)

    def test_el_refinamiento_no_toca_lo_que_ya_estaba_bien(self):
        m, conf = ci.refinar_materia("penal-mito-detenido-es-culpable", "penal")
        self.assertEqual(m, "penal")
        self.assertEqual(conf, ci.ALTA)


class TestMigracionIdempotente(CorpusBase):
    def test_primera_migracion_importa_todo(self):
        m = SemanticMemory()
        rep = ci.importar(m, self.regs)
        self.assertEqual(rep.importados, 174)
        self.assertEqual(rep.ya_presentes, 0)
        self.assertEqual(len(m), 174)

    def test_re_ejecutarla_no_duplica(self):
        m = SemanticMemory()
        ci.importar(m, self.regs)
        rep = ci.importar(m, self.regs)
        self.assertEqual(rep.importados, 0)
        self.assertEqual(rep.ya_presentes, 174)
        self.assertEqual(len(m), 174)

    def test_tres_ejecuciones_siguen_dando_174(self):
        m = SemanticMemory()
        for _ in range(3):
            ci.importar(m, self.regs)
        self.assertEqual(len(m), 174)

    def test_se_importa_como_historica_no_como_aprobada(self):
        """Producir no es aprobar: el corpus no trae señal de curaduría."""
        m = SemanticMemory()
        ci.importar(m, self.regs)
        self.assertEqual(len(m.entries(HISTORICA)), 174)
        self.assertEqual(m.entries(APROBADA), [])
        self.assertEqual(m.entries(GENERADA), [])

    def test_todo_el_corpus_es_visible_no_solo_las_ultimas(self):
        """Con la ventana de memoria corta sólo se veían 40 de 174, y el motor
        volvía a descubrir las otras 134 como si fueran nuevas."""
        m = SemanticMemory()
        ci.importar(m, self.regs)
        for r in (self.regs[0], self.regs[80], self.regs[-1]):
            self.assertTrue(m.evaluar(r.fingerprint()).bloquea, r.content_id)

    def test_el_corpus_no_cuenta_como_gusto_del_founder(self):
        """Producirlo en el pasado no significa que el Founder lo eligiera."""
        m = SemanticMemory()
        ci.importar(m, self.regs)
        pref = m.preferencias()["familia_editorial"]
        self.assertEqual(pref, {})

    def test_el_reporte_informa_campos_faltantes(self):
        m = SemanticMemory()
        rep = ci.importar(m, self.regs)
        self.assertIn("emocion", rep.campos_faltantes)
        self.assertEqual(rep.campos_faltantes["emocion"], 174)

    def test_no_hay_duplicados_exactos_de_slug(self):
        m = SemanticMemory()
        self.assertEqual(ci.importar(m, self.regs).duplicados_exactos, [])


class TestMemoriaHistoricaEnUso(CorpusBase):
    def test_un_disfraz_de_pieza_historica_queda_bloqueado(self):
        """Lo que el motor no podía hacer antes: reconocer que ya lo contó."""
        m = SemanticMemory()
        ci.importar(m, self.regs)
        base = self.regs[0].fingerprint()
        from semantic_fingerprint import SemanticFingerprint
        disfraz = SemanticFingerprint.from_dict(base.to_dict())
        disfraz.content_id = "NUEVO"
        disfraz.hook = "un titular completamente distinto"
        disfraz.metafora = "otra metáfora sin relación"
        disfraz.direccion_artistica = "estampa ukiyo-e"
        self.assertTrue(m.evaluar(disfraz).bloquea)


if __name__ == "__main__":
    unittest.main()
