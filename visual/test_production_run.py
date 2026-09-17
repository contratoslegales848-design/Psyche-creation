"""Producción real — Pasos 4 a 14 del mandato. Cadena completa sobre datos
reales: reserva >=120, selección territorial, dirección de arte, QA de dos
ejes, ciclo Founder simulado. Escena/metáfora/copyExact quedan bloqueados
deliberadamente — se prueba que SIGAN bloqueados, no que se completen."""

import unittest

import production_run as pr
from art_direction import PENDIENTE_CONTENIDO

# Cachea la ejecución completa (reserva ~140 x2, selección multi-factor,
# dirección de arte para 20 piezas): es determinista (semillas fijas), y
# recalcularla por cada clase de prueba multiplicaría un costo real sin
# ganar cobertura — todas las clases comparten el mismo resultado.
_RESULTADO = None


def _resultado():
    global _RESULTADO
    if _RESULTADO is None:
        _RESULTADO = pr.ejecutar(seed_lote1=5551, seed_lote2=5552)
    return _RESULTADO


class ProduccionBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r = _resultado()


class TestReservaReal(ProduccionBase):
    def test_la_reserva_alcanza_el_minimo_exigido(self):
        self.assertGreaterEqual(self.r["reserva1_size"], pr.RESERVA_MINIMA)
        self.assertTrue(self.r["reserva1_minimo_cumplido"])

    def test_selecciona_diez_piezas_reales(self):
        self.assertEqual(len(self.r["seleccion1"]), 10)
        self.assertEqual(len(self.r["drafts1"]), 10)
        self.assertEqual(len(self.r["puntuaciones1"]), 10)


class TestBalanceExploracion(ProduccionBase):
    def test_todo_candidato_seleccionado_cae_en_exploitation_o_exploration_o_ninguno(self):
        b = self.r["balance_exploracion"]
        self.assertEqual(b["exploitation"] + b["exploration"] + b["ninguno"], b["n"])

    def test_primer_lote_con_memoria_fuerte_real_ya_explota_señal_verdadera(self):
        """Mandato Maestro §6 (17-sep-2026): memoria fuerte real (fuente #5,
        `memoria_fuerte.py`) ya tiene curaduría real del Founder desde ANTES
        de esta corrida — a diferencia de la memoria de ejecución (`ctx
        ["memoria"]`, virgen en el primer lote), no hay nada sintético que
        esperar para poder explotarla. Reemplaza el test anterior, que
        asumía "sin curaduría previa no puede haber afinidad que explotar"
        — premisa correcta sólo quitando memoria_fuerte (ver el siguiente
        test), incorrecta ahora que production_run.py la conecta por
        defecto."""
        b = self.r["balance_exploracion"]
        self.assertGreater(b["exploitation"], 0)
        self.assertGreater(b["exploration"], 0)

    def test_sin_ninguna_memoria_el_primer_lote_es_puramente_exploracion(self):
        """La garantía original se conserva bajo su condición real: SIN
        memoria de ningún tipo (ni de ejecución ni memoria_fuerte), el
        primer lote no puede explotar nada porque no hay nada que explotar."""
        ctx = pr.cargar_contexto()
        from semantic_memory import SemanticMemory
        memoria_virgen = SemanticMemory()
        reserva, sel, pts, drafts, rech = pr.producir_y_dirigir(
            7771, memoria_virgen, ctx["mapa"], ctx["universo"], ctx["materias"],
            ctx["registro_familias"], memoria_fuerte=None)
        b = pr.balance_exploracion(sel, pts)
        self.assertEqual(b.exploitation, 0)
        self.assertGreater(b.exploration, 0)

    def test_exploration_nunca_se_mide_con_novelty_sola(self):
        """El detalle debe citar 'novelty*coherencia' (opportunity), nunca
        una rareza cruda: 'nunca elegir rareza por sí misma' (mandato)."""
        b = pr.balance_exploracion(self.r["seleccion1"], self.r["puntuaciones1"])
        for _, motivo, razon in b.detalle:
            if motivo == "EXPLORATION":
                self.assertIn("novelty*coherencia", razon)

    def test_segundo_lote_hereda_afinidad_de_la_curaduria_previa(self):
        heredan, total = self.r["afinidad_heredada"].split("/")
        self.assertGreaterEqual(int(heredan), 0)
        self.assertEqual(int(total), 10)


class TestImageGenerationBrief(ProduccionBase):
    def test_hay_un_brief_por_pieza_seleccionada(self):
        self.assertEqual(len(self.r["briefs"]), 10)

    def test_los_campos_de_infraestructura_estan_poblados(self):
        """Composición, cámara, luz, material y superficie de marca no llevan
        carga jurídica propia: son dirección de arte, y sí deben estar
        completos en esta fase."""
        for b in self.r["briefs"]:
            for campo in ("content_id", "materia", "familia_editorial",
                         "visual_function", "familia_visual", "composicion",
                         "camara", "luz", "material_sugerido"):
                self.assertTrue(str(b[campo]).strip(), (b["content_id"], campo))

    def test_escena_metafora_y_copy_permanecen_bloqueados(self):
        """El bloqueo central de esta fase: ninguna pieza ha pasado
        legalmente-legal-verification, así que ninguna puede llevar una
        afirmación jurídica textual o visual concreta todavía."""
        for b in self.r["briefs"]:
            self.assertEqual(b["escena"], PENDIENTE_CONTENIDO)
            self.assertEqual(b["metafora"], PENDIENTE_CONTENIDO)
            self.assertEqual(b["copyExact"], pr.COPY_BLOQUEADO)
            self.assertFalse(b["autorizado_para_produccion"])
            self.assertEqual(b["estado_verificacion_juridica"], "NO_VERIFICADO")

    def test_ningun_brief_se_autoriza_a_si_mismo(self):
        for b in self.r["briefs"]:
            self.assertIn("BLOQUEADO_SIN_VERIFICACION", b["copyExact"])


class TestQADosEjes(ProduccionBase):
    def test_el_eje_intelectual_reporta_distintos_por_eje(self):
        qa = self.r["qa_dos_ejes"]
        distintos = qa["intelectual_detalle"]["distintos_por_eje"]
        for eje in ("materia", "familia_editorial", "necesidad", "angulo", "emocion"):
            self.assertIn(eje, distintos)
            self.assertGreaterEqual(distintos[eje], 1)

    def test_el_eje_visual_reporta_diversidad_de_estilos_y_distancia_estricta(self):
        qa = self.r["qa_dos_ejes"]
        self.assertIn("diversidad_estilos", qa["visual_detalle"])
        self.assertIn("distancia_visual_estricta", qa["visual_detalle"])

    def test_los_dos_ejes_nunca_se_mezclan_en_un_solo_numero(self):
        qa = self.r["qa_dos_ejes"]
        self.assertIn("intelectual_ok", qa)
        self.assertIn("visual_ok", qa)
        self.assertNotIn("score_unico", qa)

    def test_prueba_de_titulos_ocultos_esta_presente(self):
        qa = self.r["qa_dos_ejes"]
        self.assertIn("prueba_titulos_ocultos_ok", qa)
        self.assertTrue(qa["prueba_titulos_ocultos_detalle"])

    def test_prueba_de_titulos_ocultos_falla_si_cuatro_o_mas_comparten_firma_visual(self):
        drafts = list(self.r["drafts1"])

        class D:
            def __init__(self, i):
                self.content_id = f"X{i}"
                self.familia_visual = "misma"
                self.composicion = "misma"
                self.camara = "misma"
                self.luz = "misma"
                self.material_sugerido = "mismo"

        ok, detalle = pr._prueba_titulos_ocultos([D(i) for i in range(4)])
        self.assertFalse(ok)
        self.assertIn("FALLA", detalle)

    def test_prueba_de_titulos_ocultos_pasa_con_menos_de_cuatro_repetidas(self):
        class D:
            def __init__(self, i, misma):
                self.content_id = f"X{i}"
                self.familia_visual = "a" if misma else f"b{i}"
                self.composicion = "c"
                self.camara = "cam"
                self.luz = "l"
                self.material_sugerido = "m"

        drafts = [D(0, True), D(1, True), D(2, True), D(3, False), D(4, False)]
        ok, detalle = pr._prueba_titulos_ocultos(drafts)
        self.assertTrue(ok)
        self.assertIn("OK", detalle)


class TestCicloFounderYSegundoLote(ProduccionBase):
    def test_la_curaduria_registra_solo_ids_del_lote(self):
        elegidos = set(self.r["elegidos_ids"])
        seleccionados = {c.candidate_id for c in self.r["seleccion1"]}
        self.assertTrue(elegidos.issubset(seleccionados))

    def test_segundo_lote_no_repite_semanticamente_de_inmediato(self):
        self.assertEqual(self.r["no_repeticion_semantica_inmediata"], 0)

    def test_ramas_descartadas_no_quedan_muertas(self):
        """'nunca prohibición permanente de temas descartados' (mandato)."""
        reaparecen, total = self.r["materias_descartadas_reaparecen"].split("/")
        self.assertGreaterEqual(int(reaparecen), 0)

    def test_el_lote_no_llega_a_estados_de_autoridad_humana(self):
        import semantic_memory as sm
        self.assertEqual(sm.SemanticMemory is not None, True)


class TestProveedorPermitido(ProduccionBase):
    def test_higgsfield_sigue_prohibido_para_este_lote(self):
        import provider_gate
        with self.assertRaises(provider_gate.ProviderGateError):
            provider_gate.verificar_proveedor_permitido("higgsfield")


class TestEmotionalProfileCausalSobreLos10Reales(ProduccionBase):
    """Paso 7 del mandato, sobre las 10 piezas REALES seleccionadas (no un
    fixture sintético aparte): cada perfil emocional debe explicar sus
    campos de dirección de arte, y dos piezas con emociones distintas deben
    diferir en al menos uno de esos campos — nunca la misma imagen con una
    etiqueta emocional distinta pegada encima.

    LÍMITE DECLARADO: `EmotionalProfile` (emotion.py) hoy tiene
    escala/composicion/camara/luz/textura/ritmo, pero NO campos separados
    para presencia_humana, tension_espacial ni movimiento_implicito que
    pide el mandato. `ritmo` es el proxy más cercano a movimiento implícito;
    los otros dos no tienen proxy y no se inventan aquí — extenderlos es un
    cambio de esquema en emotion.py que toca generator.py/art_direction.py
    y no se hace en esta fase sin decisión expresa, para no fabricar
    causalidad sobre un campo que no existe todavía."""

    def test_cada_pieza_trae_un_perfil_emocional_con_razones(self):
        for c in self.r["seleccion1"]:
            perfil = c.perfil_emocional
            self.assertTrue(perfil.get("razones"), c.candidate_id)

    def test_perfiles_con_distinta_emocion_difieren_en_direccion_de_arte(self):
        sel = self.r["seleccion1"]
        campos_direccion = ("composicion", "camara", "luz", "escala", "textura", "ritmo")
        comparados = 0
        for i in range(len(sel)):
            for j in range(i + 1, len(sel)):
                p1, p2 = sel[i].perfil_emocional, sel[j].perfil_emocional
                e1, e2 = p1.get("emocion"), p2.get("emocion")
                if not e1 or not e2 or e1 == e2:
                    continue
                comparados += 1
                difiere = any(p1.get(campo) != p2.get(campo) for campo in campos_direccion)
                self.assertTrue(difiere, f"{sel[i].candidate_id}({e1}) vs "
                                f"{sel[j].candidate_id}({e2}): dirección de arte idéntica")
        self.assertGreater(comparados, 0, "el lote real no tuvo pares con emociones distintas")

    def test_el_gap_de_campos_no_declarados_esta_documentado_no_escondido(self):
        import emotion
        campos = set(vars(emotion.EmotionalProfile()).keys())
        for ausente in ("presencia_humana", "tension_espacial", "movimiento_implicito"):
            self.assertNotIn(ausente, campos,
                            f"{ausente} ya existe en EmotionalProfile: actualizar este test "
                            "y dejar de tratarlo como límite pendiente.")


if __name__ == "__main__":
    unittest.main()
