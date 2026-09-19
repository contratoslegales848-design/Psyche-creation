"""Mandato Maestro §1-3 (17-sep-2026): capa pedagógica del motor de
conocimiento. Clasificación auditable, ajuste acotado (nunca cuota)."""

import unittest

import editorial
import pedagogia as ped
import universe


class TestClasificacionOrigenPedagogico(unittest.TestCase):
    def setUp(self):
        self.universo = editorial.EditorialUniverse.load()

    def test_clasificacion_cubre_las_65_familias_reales(self):
        """Ninguna familia real del registro queda sin clasificar, y
        ninguna familia en FAMILIAS_NARRATIVA es inventada. 58 originales +
        7 altas reales de la continuación pedagógica (17-sep-2026, segunda
        pasada: clasificacion, elementos, mapa_de_materia,
        institucion_juridica, para_recordar, quiz_juridico,
        relacion_figuras) = 65."""
        nombres = set(self.universo.names())
        self.assertEqual(len(nombres), 65)
        self.assertTrue(ped.FAMILIAS_NARRATIVA.issubset(nombres),
                        ped.FAMILIAS_NARRATIVA - nombres)
        for nombre in nombres:
            origen, razon = ped.clasificar_origen_pedagogico(nombre)
            self.assertIn(origen, (ped.CONOCIMIENTO_JURIDICO, ped.SITUACION_NARRATIVA))
            self.assertTrue(razon)

    def test_las_60_no_narrativas_son_conocimiento(self):
        no_narrativa = set(self.universo.names()) - ped.FAMILIAS_NARRATIVA
        self.assertEqual(len(no_narrativa), 60)
        for nombre in no_narrativa:
            origen, _ = ped.clasificar_origen_pedagogico(nombre)
            self.assertEqual(origen, ped.CONOCIMIENTO_JURIDICO)

    def test_las_5_narrativas_declaradas(self):
        for nombre in ped.FAMILIAS_NARRATIVA:
            origen, _ = ped.clasificar_origen_pedagogico(nombre)
            self.assertEqual(origen, ped.SITUACION_NARRATIVA)

    def test_familia_vacia_lanza_error_explicito(self):
        with self.assertRaises(ped.PedagogiaError):
            ped.clasificar_origen_pedagogico("")

    def test_es_determinista(self):
        self.assertEqual(ped.clasificar_origen_pedagogico("mito"),
                         ped.clasificar_origen_pedagogico("mito"))


class TestObjetivoYTipoDeAprendizaje(unittest.TestCase):
    def setUp(self):
        self.universo = editorial.EditorialUniverse.load()

    def test_objetivo_pedagogico_es_la_funcion_editorial_real(self):
        self.assertEqual(ped.objetivo_pedagogico("concepto", self.universo),
                         self.universo.get("concepto").funcion_editorial)

    def test_todas_las_necesidades_reales_tienen_tipo_de_aprendizaje(self):
        for nec in self.universo.necesidades:
            tipo = ped.tipo_de_aprendizaje(nec)
            self.assertNotEqual(tipo, "SIN_CLASIFICAR", nec)

    def test_necesidad_desconocida_no_se_inventa(self):
        self.assertEqual(ped.tipo_de_aprendizaje("necesidad-inexistente-xyz"), "SIN_CLASIFICAR")


class TestPerfilPedagogico(unittest.TestCase):
    def test_perfil_trae_los_cuatro_campos(self):
        c = universe.TopicCandidate(candidate_id="x", familia_editorial="mito",
                                    necesidad="corregir")
        p = ped.perfil_pedagogico(c)
        self.assertEqual(p.origen, ped.CONOCIMIENTO_JURIDICO)  # "mito" no está en FAMILIAS_NARRATIVA
        self.assertTrue(p.objetivo)
        self.assertTrue(p.tipo_aprendizaje)
        self.assertEqual(p.familia_editorial, "mito")


class TestAjusteBalancePedagogico(unittest.TestCase):
    def candidato(self, familia):
        return universe.TopicCandidate(candidate_id="x", familia_editorial=familia,
                                       necesidad="entender")

    def test_lote_vacio_es_cero_exacto(self):
        ajuste, razon = ped.ajuste_balance_pedagogico(self.candidato("concepto"), [])
        self.assertEqual(ajuste, 0.0)
        self.assertIn("vacío", razon)

    def test_desactivado_explicitamente_es_cero(self):
        lote = [self.candidato("caso_cotidiano")] * 5
        ajuste, razon = ped.ajuste_balance_pedagogico(
            self.candidato("concepto"), lote, objetivo_conocimiento=None)
        self.assertEqual(ajuste, 0.0)
        self.assertIn("desactivado", razon)

    def test_lote_saturado_de_narrativa_favorece_conocimiento(self):
        """Si el lote parcial ya es 100% narrativa, un candidato de
        conocimiento debe recibir empujón POSITIVO."""
        lote = [self.candidato("caso_cotidiano")] * 5
        ajuste, _ = ped.ajuste_balance_pedagogico(self.candidato("concepto"), lote)
        self.assertGreater(ajuste, 0.0)

    def test_lote_saturado_de_narrativa_penaliza_mas_narrativa(self):
        lote = [self.candidato("caso_cotidiano")] * 5
        ajuste, _ = ped.ajuste_balance_pedagogico(self.candidato("jurista"), lote)
        self.assertLess(ajuste, 0.0)

    def test_lote_saturado_de_conocimiento_favorece_narrativa(self):
        """Simétrico: narrativa nunca se elimina — si el lote va muy cargado
        de conocimiento, narrativa recupera ventaja (mandato §3: 'sigue
        disponible como puerta editorial')."""
        lote = [self.candidato("concepto")] * 9
        ajuste, _ = ped.ajuste_balance_pedagogico(self.candidato("caso_cotidiano"), lote)
        self.assertGreater(ajuste, 0.0)

    def test_lote_ya_en_el_objetivo_exacto_da_ajuste_cero(self):
        lote = ([self.candidato("concepto")] * 7) + ([self.candidato("caso_cotidiano")] * 3)
        ajuste_c, _ = ped.ajuste_balance_pedagogico(self.candidato("definicion_operativa"), lote)
        self.assertEqual(ajuste_c, 0.0)

    def test_ajuste_esta_acotado(self):
        lote = [self.candidato("caso_cotidiano")] * 20
        ajuste, _ = ped.ajuste_balance_pedagogico(self.candidato("concepto"), lote)
        self.assertLessEqual(abs(ajuste), ped.AJUSTE_BALANCE_PEDAGOGICO_MAX)

    def test_objetivo_configurable_no_es_regla_fija(self):
        """Mandato §3: 'hazlo configurable'. En un lote 100% conocimiento,
        un objetivo BAJO (quiere más narrativa: 0.10) debe empujar narrativa
        con más fuerza que un objetivo ALTO (casi conforme con puro
        conocimiento: 0.95, apenas por encima del 100% real) — la magnitud
        del empujón depende del parámetro, no de una constante quemada."""
        lote = [self.candidato("concepto")] * 5
        ajuste_narrativa_obj_bajo, _ = ped.ajuste_balance_pedagogico(
            self.candidato("caso_cotidiano"), lote, objetivo_conocimiento=0.10)
        ajuste_narrativa_obj_alto, _ = ped.ajuste_balance_pedagogico(
            self.candidato("caso_cotidiano"), lote, objetivo_conocimiento=0.95)
        self.assertGreater(ajuste_narrativa_obj_bajo, ajuste_narrativa_obj_alto)

    def test_nunca_excluye_solo_ajusta_score(self):
        """No hay ningún hard gate aquí: la función siempre devuelve un
        float, nunca bloquea_ni_rechaza."""
        lote = [self.candidato("caso_cotidiano")] * 30
        ajuste, _ = ped.ajuste_balance_pedagogico(self.candidato("jurista"), lote)
        self.assertIsInstance(ajuste, float)


class TestNuevasFamiliasContinuacionPedagogica(unittest.TestCase):
    """Continuación ejecutiva — prioridad pedagógica (17-sep-2026, 2ª
    pasada). Las 7 familias nuevas son altas reales, no un banco paralelo:
    deben resolverse igual que cualquier familia del registro."""

    NUEVAS = ("clasificacion", "elementos", "mapa_de_materia",
             "institucion_juridica", "para_recordar", "quiz_juridico",
             "relacion_figuras")

    def setUp(self):
        self.universo = editorial.EditorialUniverse.load()

    def test_las_7_nuevas_estan_en_el_registro_real(self):
        nombres = set(self.universo.names())
        for nueva in self.NUEVAS:
            self.assertIn(nueva, nombres)

    def test_ninguna_nueva_es_narrativa(self):
        """Las 7 nuevas enseñan estructura jurídica (clasificación,
        elementos, mapa de materia, etc.), no narran una situación."""
        for nueva in self.NUEVAS:
            origen, _ = ped.clasificar_origen_pedagogico(nueva)
            self.assertEqual(origen, ped.CONOCIMIENTO_JURIDICO, nueva)

    def test_las_7_nuevas_declaran_afinidad_real(self):
        """Mismo contrato que las 58 originales: nada de necesidades_afines
        o roles_lector_afines vacíos (ver test_territory_explorer)."""
        for nueva in self.NUEVAS:
            fam = self.universo.get(nueva)
            self.assertTrue(fam.necesidades_afines, nueva)
            self.assertTrue(fam.roles_lector_afines, nueva)


class TestDimensionDeFamilia(unittest.TestCase):
    def setUp(self):
        self.universo = editorial.EditorialUniverse.load()

    def test_todas_las_65_familias_tienen_dimension_clasificada(self):
        """Mandato §1/§8: 'conocimiento primero' exige poder leer, de cada
        familia real, qué dimensión de conocimiento enseña."""
        for nombre in self.universo.names():
            dim = ped.dimension_de_familia(nombre)
            self.assertNotEqual(dim, "SIN_CLASIFICAR", nombre)
            self.assertIn(dim, ped.DIMENSIONES_CONOCIMIENTO)

    def test_familia_desconocida_no_se_inventa(self):
        self.assertEqual(ped.dimension_de_familia("familia-inexistente-xyz"), "SIN_CLASIFICAR")

    def test_clasificacion_se_distingue_de_una_definicion(self):
        """Propiedad del mandato §12: 'la clasificación se distingue de una
        definición'. Son familias reales distintas, con dimensión distinta."""
        self.assertNotEqual(ped.dimension_de_familia("clasificacion"),
                            ped.dimension_de_familia("definicion_operativa"))

    def test_diferencia_ab_se_distingue_de_un_caso_humano(self):
        """Propiedad del mandato §12: 'la diferencia A/B se distingue de un
        caso humano'. 'diferencia' es CONOCIMIENTO_JURIDICO (dimensión
        RELACION_CON_OTRAS_FIGURAS); 'caso_cotidiano' es SITUACION_NARRATIVA
        — ejes distintos, nunca la misma clasificación."""
        origen_diferencia, _ = ped.clasificar_origen_pedagogico("diferencia")
        origen_caso, _ = ped.clasificar_origen_pedagogico("caso_cotidiano")
        self.assertEqual(origen_diferencia, ped.CONOCIMIENTO_JURIDICO)
        self.assertEqual(origen_caso, ped.SITUACION_NARRATIVA)
        self.assertNotEqual(origen_diferencia, origen_caso)


class TestCubreDimensionesDistintas(unittest.TestCase):
    """Mandato §4: 'un concepto puede generar una ruta' — la memoria debe
    poder distinguir una ruta real (ángulos distintos) de una repetición del
    mismo ángulo con distinto envoltorio."""

    def candidato(self, familia, concepto="prescripcion"):
        return universe.TopicCandidate(candidate_id=f"x-{familia}", familia_editorial=familia,
                                       necesidad="entender", concepto_nucleo=concepto)

    def test_una_ruta_real_sobre_prescripcion_cubre_varios_angulos(self):
        """Ejemplo del mandato §4: qué es / diferencia con caducidad /
        elementos — tres familias reales, mismo concepto_nucleo, tres
        dimensiones de conocimiento distintas."""
        ruta = [self.candidato("concepto"), self.candidato("diferencia"),
               self.candidato("elementos")]
        self.assertTrue(ped.cubre_dimensiones_distintas(ruta))

    def test_repetir_el_mismo_angulo_no_cuenta_como_ruta(self):
        repetido = [self.candidato("concepto"), self.candidato("concepto")]
        self.assertFalse(ped.cubre_dimensiones_distintas(repetido))

    def test_un_solo_candidato_nunca_es_ruta(self):
        self.assertFalse(ped.cubre_dimensiones_distintas([self.candidato("concepto")]))

    def test_lista_vacia_no_es_ruta(self):
        self.assertFalse(ped.cubre_dimensiones_distintas([]))


class TestAprendizajeConcreto(unittest.TestCase):
    """Mandato §7: '¿la persona aprendió algo jurídico concreto? Si NO:
    REWORK.' — proxy estructural, nunca evalúa contenido real."""

    def test_pieza_con_concepto_y_señal_pasa(self):
        c = universe.TopicCandidate(candidate_id="x", concepto_nucleo="prescripcion",
                                    pregunta_resuelta="cuándo empieza el cómputo")
        aprende, razon = ped.aprendizaje_concreto(c)
        self.assertTrue(aprende)
        self.assertTrue(razon)

    def test_pieza_sin_concepto_nucleo_es_rework(self):
        c = universe.TopicCandidate(candidate_id="x", concepto_nucleo="")
        aprende, razon = ped.aprendizaje_concreto(c)
        self.assertFalse(aprende)
        self.assertIn("concepto_nucleo", razon)

    def test_pieza_comercial_sin_senal_de_enseñanza_es_rework(self):
        """Caso adversarial del mandato §7: una pieza que 'parece anuncio'
        — hook llamativo, sin concepto_nucleo ni señal de enseñanza — debe
        marcarse para REWORK, aunque tenga familia narrativa disponible."""
        c = universe.TopicCandidate(candidate_id="x", familia_editorial="caso_cotidiano",
                                    concepto_nucleo="", hook="¡Esto te puede pasar a ti!")
        aprende, _ = ped.aprendizaje_concreto(c)
        self.assertFalse(aprende)

    def test_concepto_sin_ninguna_señal_tambien_es_rework(self):
        c = universe.TopicCandidate(candidate_id="x", concepto_nucleo="prescripcion")
        aprende, razon = ped.aprendizaje_concreto(c)
        self.assertFalse(aprende)
        self.assertIn("sustancia", razon)

    def test_consecuencia_sola_ya_basta_como_señal(self):
        c = universe.TopicCandidate(candidate_id="x", concepto_nucleo="prescripcion",
                                    consecuencia="se pierde la acción")
        aprende, _ = ped.aprendizaje_concreto(c)
        self.assertTrue(aprende)

    def test_relacion_sola_ya_basta_como_señal(self):
        c = universe.TopicCandidate(candidate_id="x", concepto_nucleo="prescripcion",
                                    relacion="caducidad")
        aprende, _ = ped.aprendizaje_concreto(c)
        self.assertTrue(aprende)


class TestFormatoSugerido(unittest.TestCase):
    """Mandato §6: profundidad adaptativa — sugerencia, nunca obligación;
    'si no cabe, nunca elimines relaciones importantes: selecciona otro
    formato o divide la enseñanza'."""

    def test_formato_es_del_vocabulario_real(self):
        universo = editorial.EditorialUniverse.load()
        for prof in universo.profundidades:
            formato, razon = ped.formato_sugerido(prof)
            self.assertIn(formato, universo.formatos_editoriales)
            self.assertTrue(razon)

    def test_muchas_dimensiones_prefiere_secuenciar_no_comprimir(self):
        """Un tema complejo (muchas dimensiones disponibles) en profundidad
        no-alta debe preferir un formato que secuencie (proceso) en vez de
        comprimir todo en una frase o concepto único — nunca 'eliminar
        relaciones importantes' por falta de espacio."""
        formato_simple, _ = ped.formato_sugerido("base", n_dimensiones_disponibles=1)
        formato_complejo, _ = ped.formato_sugerido("base", n_dimensiones_disponibles=5)
        self.assertNotEqual(formato_simple, formato_complejo)
        self.assertEqual(formato_complejo, "proceso")

    def test_profundidad_desconocida_cae_a_media_no_revienta(self):
        formato, _ = ped.formato_sugerido("profundidad-inexistente")
        self.assertIn(formato, ped.FORMATOS_POR_PROFUNDIDAD["media"])


class TestHistoriasHumanasDisponiblesSinDominar(unittest.TestCase):
    """Mandato §12: 'las historias humanas siguen disponibles pero no
    dominan'. FAMILIAS_NARRATIVA sigue siendo una puerta editorial real
    (no se vació al añadir las 7 familias de conocimiento nuevas), y el
    balance sigue favoreciendo narrativa cuando el lote se satura de
    conocimiento (regresión ya cubierta en TestAjusteBalancePedagogico;
    aquí se verifica que la puerta narrativa sigue abierta con las 65
    familias reales)."""

    def test_narrativa_sigue_siendo_subconjunto_no_vacio_de_las_65(self):
        universo = editorial.EditorialUniverse.load()
        self.assertTrue(ped.FAMILIAS_NARRATIVA)
        self.assertTrue(ped.FAMILIAS_NARRATIVA.issubset(set(universo.names())))

    def test_narrativa_no_crecio_ni_se_redujo_con_las_altas_nuevas(self):
        """Las 7 familias nuevas son todas CONOCIMIENTO_JURIDICO (ver
        TestNuevasFamiliasContinuacionPedagogica) — la puerta narrativa
        sigue teniendo exactamente el mismo tamaño de antes, nunca se cerró
        ni se disolvió entre las nuevas."""
        self.assertEqual(len(ped.FAMILIAS_NARRATIVA), 5)


if __name__ == "__main__":
    unittest.main()
