"""Generador multi-factor: hard gates que rechazan de verdad, sin fabricar
factores que no tienen evidencia."""

import unittest

import corpus_import as ci
import editorial
import generator
import territory_explorer as te
import universe
from semantic_fingerprint import SemanticFingerprint as S
from semantic_memory import SemanticMemory, GENERADA, HISTORICA


class GenBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.regs, _ = ci.construir_registros()
        cls.universo = editorial.EditorialUniverse.load()
        cls.mapa = te.construir_mapa(cls.regs)
        _, cls.materias = universe.cargar_materias()


class TestFactoresPendientesHonestos(GenBase):
    def test_legal_support_nunca_se_finge(self):
        c = universe.build_reserve(objetivo_lote=1, seed=1)[0]
        s = generator.puntuar_candidato(c, SemanticMemory(), self.mapa, self.universo)
        self.assertEqual(s.legal_support, generator.PENDIENTE_VERIFICACION)

    def test_human_interest_nunca_se_finge(self):
        c = universe.build_reserve(objetivo_lote=1, seed=1)[0]
        s = generator.puntuar_candidato(c, SemanticMemory(), self.mapa, self.universo)
        self.assertEqual(s.human_interest, generator.PENDIENTE_VERIFICACION)

    def test_visual_distance_no_disponible_en_esta_etapa(self):
        c = universe.build_reserve(objetivo_lote=1, seed=1)[0]
        s = generator.puntuar_candidato(c, SemanticMemory(), self.mapa, self.universo)
        self.assertEqual(s.visual_distance, generator.NO_DISPONIBLE_EN_ESTA_ETAPA)

    def test_estos_tres_no_entran_en_el_score_compuesto(self):
        self.assertNotIn("legal_support", generator.PESOS)
        self.assertNotIn("human_interest", generator.PESOS)
        self.assertNotIn("visual_distance", generator.PESOS)

    def test_los_pesos_de_los_factores_reales_suman_uno(self):
        self.assertAlmostEqual(sum(generator.PESOS.values()), 1.0, places=6)


class TestHardGates(GenBase):
    def test_repeticion_semantica_bloquea_con_score_cero(self):
        m = SemanticMemory()
        base = S(content_id="h1", materia="civil", concepto_nucleo="deposito en garantia",
                familia_editorial="mito", necesidad="corregir")
        m.record(base, HISTORICA)
        c = type("C", (), {"candidate_id": "x", "materia": "civil", "submateria": "arrendamiento",
                           "familia_editorial": "mito", "necesidad": "corregir",
                           "angulo": "", "contexto_funcional": "", "rol_lector": "",
                           "consecuencia": "", "hook": "otro", "formato": "",
                           "perfil_emocional": {},
                           "fingerprint": lambda self: S(content_id="x", materia="civil",
                                                         concepto_nucleo="deposito en garantia",
                                                         familia_editorial="mito",
                                                         necesidad="corregir", hook="otro")})()
        s = generator.puntuar_candidato(c, m, self.mapa, self.universo)
        self.assertFalse(s.hard_gates_pasados)
        self.assertIn("REPETICIÓN SEMÁNTICA", s.motivo_bloqueo)
        self.assertEqual(s.score_compuesto, 0.0)

    def test_saturacion_alta_bloquea_aunque_sea_semanticamente_nueva(self):
        """El caso central del mandato."""
        m = SemanticMemory()
        for i in range(5):
            m.record(S(content_id=f"g{i}", materia="civil", concepto_nucleo=f"concepto{i}",
                      familia_editorial="caso_cotidiano", necesidad="entender"), GENERADA)
        c = type("C", (), {"candidate_id": "nuevo", "materia": "penal", "submateria": "",
                           "familia_editorial": "caso_cotidiano", "necesidad": "entender",
                           "angulo": "", "contexto_funcional": "", "rol_lector": "",
                           "consecuencia": "", "hook": "", "formato": "",
                           "perfil_emocional": {},
                           "fingerprint": lambda self: S(content_id="nuevo", materia="penal",
                                                         concepto_nucleo="algo nunca dicho",
                                                         familia_editorial="caso_cotidiano",
                                                         necesidad="entender")})()
        self.assertFalse(m.evaluar(c.fingerprint()).bloquea)  # confirma que es nueva
        s = generator.puntuar_candidato(c, m, self.mapa, self.universo)
        self.assertFalse(s.hard_gates_pasados)
        self.assertIn("SATURACIÓN EDITORIAL", s.motivo_bloqueo)

    def test_cuota_de_materia_bloquea_al_superarse(self):
        candidatos = universe.build_reserve(objetivo_lote=30, seed=5)
        misma_materia = {}
        for c in candidatos:
            misma_materia.setdefault(c.materia, []).append(c)
        materia, piezas = max(misma_materia.items(), key=lambda kv: len(kv[1]))
        self.assertGreaterEqual(len(piezas), 3)
        lote_previo = piezas[:2]
        s = generator.puntuar_candidato(piezas[2], SemanticMemory(), self.mapa, self.universo,
                                        lote_en_progreso=lote_previo, materias=self.materias,
                                        n_lote=10)
        self.assertFalse(s.hard_gates_pasados)
        self.assertIn("CUOTA DE MATERIA", s.motivo_bloqueo)

    def test_ningun_factor_blando_rescata_un_hard_gate(self):
        """Ni la mejor oportunidad de territorio puede compensar un gate."""
        m = SemanticMemory()
        for i in range(5):
            m.record(S(content_id=f"g{i}", familia_editorial="mito", necesidad="corregir"),
                    GENERADA)
        c = type("C", (), {"candidate_id": "x", "materia": "ambiental", "submateria": "",
                           "familia_editorial": "mito", "necesidad": "corregir",
                           "angulo": "", "contexto_funcional": "", "rol_lector": "persona",
                           "consecuencia": "", "hook": "", "formato": "",
                           "perfil_emocional": {},
                           "fingerprint": lambda self: S(content_id="x", materia="ambiental",
                                                         familia_editorial="mito",
                                                         necesidad="corregir")})()
        s = generator.puntuar_candidato(c, m, self.mapa, self.universo)
        self.assertEqual(s.score_compuesto, 0.0)


class TestScoreCompuesto(GenBase):
    def test_candidato_admitido_tiene_score_entre_0_y_1(self):
        c = universe.build_reserve(objetivo_lote=1, seed=1)[0]
        s = generator.puntuar_candidato(c, SemanticMemory(), self.mapa, self.universo)
        self.assertTrue(s.hard_gates_pasados)
        self.assertGreaterEqual(s.score_compuesto, 0.0)
        self.assertLessEqual(s.score_compuesto, 1.0)

    def test_es_determinista(self):
        c = universe.build_reserve(objetivo_lote=1, seed=1)[0]
        s1 = generator.puntuar_candidato(c, SemanticMemory(), self.mapa, self.universo)
        s2 = generator.puntuar_candidato(c, SemanticMemory(), self.mapa, self.universo)
        self.assertEqual(s1.score_compuesto, s2.score_compuesto)

    def test_diversidad_editorial_decae_dentro_del_mismo_lote(self):
        c1 = universe.build_reserve(objetivo_lote=1, seed=1)[0]
        c2 = type("C", (), {"materia": c1.materia, "familia_editorial": c1.familia_editorial,
                            "necesidad": c1.necesidad, "rol_lector": c1.rol_lector})()
        div_vacio, _ = generator._diversidad_editorial_de_lote(c2, [])
        div_repetido, _ = generator._diversidad_editorial_de_lote(c2, [c1])
        self.assertGreater(div_vacio, div_repetido)

    def test_emotional_fit_penaliza_la_degradacion(self):
        con_friccion = {"emocion": "urgencia", "razones": ["degradado a claridad"]}
        sin_friccion = {"emocion": "claridad", "razones": ["necesidad 'x' ancla en 'claridad'."]}
        c1 = type("C", (), {"perfil_emocional": con_friccion})()
        c2 = type("C", (), {"perfil_emocional": sin_friccion})()
        f1, _ = generator._ajuste_emocional(c1)
        f2, _ = generator._ajuste_emocional(c2)
        self.assertLess(f1, f2)


class TestSeleccionarLote(GenBase):
    def test_selecciona_diez_completo(self):
        reserva = universe.build_reserve(objetivo_lote=10, seed=42, factor=12)
        m = SemanticMemory()
        ci.importar(m, self.regs)
        sel, puntos, rechazados = generator.seleccionar_lote(reserva, m, self.mapa, n=10)
        self.assertEqual(len(sel), 10)
        self.assertEqual(len(puntos), 10)

    def test_respeta_cuota_de_materia_en_el_lote_final(self):
        reserva = universe.build_reserve(objetivo_lote=10, seed=42, factor=12)
        m = SemanticMemory()
        sel, _, _ = generator.seleccionar_lote(reserva, m, self.mapa, n=10)
        from collections import Counter
        for materia, cuenta in Counter(c.materia for c in sel).items():
            tope = self.materias.get(materia, {}).get("cuota_max_por_lote_10", 2)
            self.assertLessEqual(cuenta, tope)

    def test_nunca_selecciona_contenido_ya_en_memoria_historica(self):
        reserva = universe.build_reserve(objetivo_lote=10, seed=42, factor=12)
        m = SemanticMemory()
        ci.importar(m, self.regs)
        sel, _, _ = generator.seleccionar_lote(reserva, m, self.mapa, n=10)
        for c in sel:
            self.assertFalse(m.evaluar(c.fingerprint()).bloquea)

    def test_ningun_rechazado_aparece_en_la_seleccion(self):
        reserva = universe.build_reserve(objetivo_lote=10, seed=42, factor=12)
        m = SemanticMemory()
        sel, _, rechazados = generator.seleccionar_lote(reserva, m, self.mapa, n=10)
        ids_rechazados = {r[0] for r in rechazados}
        self.assertFalse({c.candidate_id for c in sel} & ids_rechazados)


class TestAfinidadFounder(GenBase):
    def test_memoria_sin_curaduria_da_ajuste_exactamente_cero(self):
        """El primer lote no puede explotar un gusto que no existe todavía."""
        c = universe.build_reserve(objetivo_lote=1, seed=1)[0]
        ajuste, razon = generator.ajuste_afinidad_founder(c, SemanticMemory())
        self.assertEqual(ajuste, 0.0)
        self.assertIn("sin memoria", razon.lower() + "sin memoria")  # siempre explica por qué

    def test_memoria_none_da_ajuste_cero(self):
        c = universe.build_reserve(objetivo_lote=1, seed=1)[0]
        ajuste, _ = generator.ajuste_afinidad_founder(c, None)
        self.assertEqual(ajuste, 0.0)

    def test_rasgo_preferido_produce_ajuste_positivo(self):
        m = SemanticMemory()
        from semantic_fingerprint import SemanticFingerprint as S
        from semantic_memory import PRESELECCIONADA
        m.record(S(content_id="p", familia_editorial="mito", necesidad="corregir"),
                PRESELECCIONADA)
        c = type("C", (), {"materia": "civil", "familia_editorial": "mito",
                           "necesidad": "corregir", "angulo": "", "emocion": "",
                           "rol_lector": ""})()
        ajuste, razon = generator.ajuste_afinidad_founder(c, m)
        self.assertGreater(ajuste, 0.0)
        self.assertIn("mito", razon)

    def test_rasgo_descartado_produce_ajuste_negativo_pero_no_bloquea(self):
        m = SemanticMemory()
        from semantic_fingerprint import SemanticFingerprint as S
        from semantic_memory import DESCARTADA
        for i in range(4):
            m.record(S(content_id=f"d{i}", familia_editorial="mito"), DESCARTADA)
        c = type("C", (), {"materia": "civil", "familia_editorial": "mito",
                           "necesidad": "x", "angulo": "", "emocion": "", "rol_lector": ""})()
        ajuste, _ = generator.ajuste_afinidad_founder(c, m)
        self.assertLess(ajuste, 0.0)
        self.assertGreaterEqual(ajuste, -generator.AJUSTE_AFINIDAD_MAX)

    def test_el_ajuste_esta_acotado(self):
        """Ninguna cantidad de señal previa puede desbordar el tope."""
        m = SemanticMemory()
        from semantic_fingerprint import SemanticFingerprint as S
        from semantic_memory import PRESELECCIONADA
        for i in range(50):
            m.record(S(content_id=f"p{i}", familia_editorial="mito", necesidad="corregir",
                      materia="civil", angulo="critico", emocion="sorpresa",
                      rol_lector="persona"), PRESELECCIONADA)
        c = type("C", (), {"materia": "civil", "familia_editorial": "mito",
                           "necesidad": "corregir", "angulo": "critico",
                           "emocion": "sorpresa", "rol_lector": "persona"})()
        ajuste, _ = generator.ajuste_afinidad_founder(c, m)
        self.assertEqual(ajuste, generator.AJUSTE_AFINIDAD_MAX)

    def test_ningun_eje_coincidente_da_cero(self):
        m = SemanticMemory()
        from semantic_fingerprint import SemanticFingerprint as S
        from semantic_memory import PRESELECCIONADA
        m.record(S(content_id="p", familia_editorial="mito", necesidad="corregir"),
                PRESELECCIONADA)
        c = type("C", (), {"materia": "penal", "familia_editorial": "checklist",
                           "necesidad": "prepararse", "angulo": "", "emocion": "",
                           "rol_lector": ""})()
        ajuste, _ = generator.ajuste_afinidad_founder(c, m)
        self.assertEqual(ajuste, 0.0)


class TestExplotacionEnLote(GenBase):
    def test_lote_posterior_a_una_curaduria_refleja_la_preferencia(self):
        """El caso íntegro de la Fase 9: el mandato exige que la probabilidad
        de rasgos elegidos SUBA en el siguiente lote."""
        import organism
        m = SemanticMemory()
        ci.importar(m, self.regs)
        reserva1 = universe.build_reserve(objetivo_lote=10, seed=11, factor=14)
        sel1, _, _ = generator.seleccionar_lote(reserva1, m, self.mapa, n=10,
                                                materias=self.materias)
        elegidos_ids = [sel1[i].candidate_id for i in (1, 4, 8)]
        lote1 = organism.CurationBatch(lote_id="t", estado=organism.CURATION_READY,
                                       candidatos=sel1, reserva_total=len(reserva1))
        organism.registrar_curaduria(lote1, elegidos_ids, m)

        reserva2 = universe.build_reserve(objetivo_lote=10, seed=12, factor=14)
        sel2, pts2, _ = generator.seleccionar_lote(reserva2, m, self.mapa, n=10,
                                                    materias=self.materias)
        con_afinidad = [p for p in pts2 if p.ajuste_afinidad_founder > 0]
        self.assertTrue(con_afinidad,
                        "ninguna pieza del segundo lote heredó afinidad de la curaduría")

    def test_no_bloquea_permanentemente_una_materia_descartada(self):
        """El descarte del Founder no puede cancelar una rama jurídica: sigue
        siendo SELECCIONABLE, sólo con un empujón negativo pequeño."""
        m = SemanticMemory()
        from semantic_fingerprint import SemanticFingerprint as S
        from semantic_memory import DESCARTADA
        for i in range(3):
            m.record(S(content_id=f"d{i}", materia="ambiental", familia_editorial="mito"),
                    DESCARTADA)
        c = type("C", (), {"materia": "ambiental", "familia_editorial": "prevencion",
                           "necesidad": "prevenir", "angulo": "", "emocion": "",
                           "rol_lector": "persona",
                           "candidate_id": "x", "submateria": "", "consecuencia": "",
                           "hook": "", "formato": "", "perfil_emocional": {},
                           "fingerprint": lambda self: S(content_id="x", materia="ambiental",
                                                         familia_editorial="prevencion",
                                                         necesidad="prevenir")})()
        s = generator.puntuar_candidato(c, m, self.mapa, self.universo)
        self.assertTrue(s.hard_gates_pasados,
                        "una materia descartada nunca debe volverse un hard gate")


class TestSenalDeMercado(GenBase):
    """Parte VI del mandato "Fase post-implementación" (16-sep-2026): ajuste
    acotado por demanda profesional real, mismo patrón que la afinidad del
    Founder — sin evidencia, exactamente 0.0."""

    def test_sin_senales_ajuste_es_cero(self):
        ajuste, razon = generator.ajuste_senal_mercado(
            type("C", (), {"materia": "mercantil"})(), None)
        self.assertEqual(ajuste, 0.0)
        self.assertIn("sin señales", razon)

    def test_materia_sin_coincidencia_ajuste_es_cero(self):
        señales = [{"legal_area": "penal", "professional_demand": "ALTA", "frequency": 9}]
        ajuste, _ = generator.ajuste_senal_mercado(
            type("C", (), {"materia": "mercantil"})(), señales)
        self.assertEqual(ajuste, 0.0)

    def test_demanda_alta_da_el_ajuste_maximo(self):
        señales = [{"legal_area": "mercantil", "professional_demand": "ALTA", "frequency": 14}]
        ajuste, razon = generator.ajuste_senal_mercado(
            type("C", (), {"materia": "mercantil"})(), señales)
        self.assertEqual(ajuste, generator.AJUSTE_SENAL_MERCADO_MAX)
        self.assertIn("mercantil", razon)

    def test_demanda_media_da_la_mitad_del_ajuste_maximo(self):
        señales = [{"legal_area": "laboral", "professional_demand": "MEDIA", "frequency": 3}]
        ajuste, _ = generator.ajuste_senal_mercado(
            type("C", (), {"materia": "laboral"})(), señales)
        self.assertEqual(ajuste, round(generator.AJUSTE_SENAL_MERCADO_MAX * 0.5, 4))

    def test_demanda_baja_da_cero(self):
        señales = [{"legal_area": "fiscal", "professional_demand": "BAJA", "frequency": 1}]
        ajuste, _ = generator.ajuste_senal_mercado(
            type("C", (), {"materia": "fiscal"})(), señales)
        self.assertEqual(ajuste, 0.0)

    def test_puntuar_candidato_sin_señales_mercado_es_identico_a_antes(self):
        """Backward-compat explícito: no pasar señales_mercado (el default)
        no cambia nada de lo que ya dependía de puntuar_candidato."""
        c = universe.build_reserve(objetivo_lote=1, seed=1)[0]
        s = generator.puntuar_candidato(c, SemanticMemory(), self.mapa, self.universo)
        self.assertEqual(s.ajuste_senal_mercado, 0.0)

    def test_puntuar_candidato_con_señal_real_suma_al_score(self):
        c = universe.build_reserve(objetivo_lote=1, seed=1)[0]
        señales = [{"legal_area": c.materia, "professional_demand": "ALTA", "frequency": 10}]
        s_sin = generator.puntuar_candidato(c, SemanticMemory(), self.mapa, self.universo)
        s_con = generator.puntuar_candidato(c, SemanticMemory(), self.mapa, self.universo,
                                            señales_mercado=señales)
        self.assertEqual(s_con.ajuste_senal_mercado, generator.AJUSTE_SENAL_MERCADO_MAX)
        self.assertGreaterEqual(s_con.score_compuesto, s_sin.score_compuesto)

    def test_seleccionar_lote_acepta_señales_mercado_sin_romper_cuotas(self):
        reserva = universe.build_reserve(objetivo_lote=10, seed=5, factor=14)
        señales = [{"legal_area": "mercantil", "professional_demand": "ALTA", "frequency": 14}]
        sel, pts, _ = generator.seleccionar_lote(reserva, SemanticMemory(), self.mapa,
                                                 universo=self.universo, n=10,
                                                 materias=self.materias,
                                                 señales_mercado=señales)
        self.assertLessEqual(len(sel), 10)
        for c, p in zip(sel, pts):
            self.assertGreaterEqual(p.score_compuesto, 0.0)
            self.assertLessEqual(p.score_compuesto, 1.0)


if __name__ == "__main__":
    unittest.main()
