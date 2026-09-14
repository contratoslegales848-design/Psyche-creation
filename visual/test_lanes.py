"""Tres carriles, un solo cerebro jurídico, memorias editoriales separadas."""

import unittest

import lanes
import universe
from semantic_memory import APROBADA
from semantic_fingerprint import SemanticFingerprint


def candidato(**kw):
    base = dict(candidate_id="C1", materia="laboral", submateria="jornada",
                familia_editorial="proceso", necesidad="entender", rol_lector="persona",
                angulo="procedimental", contexto_funcional="vida_cotidiana",
                profundidad="media", formato="proceso", concepto_nucleo="jornada",
                relacion="r", pregunta_resuelta="p")
    base.update(kw)
    return universe.TopicCandidate(**base)


class TestConfiguracion(unittest.TestCase):
    def test_los_tres_carriles_existen(self):
        self.assertEqual(set(lanes.CARRILES),
                         {lanes.LEGALMENTE_GENERAL, lanes.LINKEDIN_LEGALMENTE,
                          lanes.LINKEDIN_FOUNDER})

    def test_carril_desconocido_falla(self):
        with self.assertRaises(lanes.LaneError):
            lanes.get("INSTAGRAM_SECRETO")

    def test_formatos_canonicos(self):
        self.assertEqual(lanes.get(lanes.LEGALMENTE_GENERAL).formato_visual, "9:16")
        self.assertEqual(lanes.get(lanes.LINKEDIN_LEGALMENTE).formato_visual, "4:5")
        self.assertEqual(lanes.get(lanes.LINKEDIN_FOUNDER).formato_visual, "4:5")

    def test_el_carril_general_no_restringe_familias(self):
        """Exploración amplia: el universo entero disponible."""
        cfg = lanes.get(lanes.LEGALMENTE_GENERAL)
        self.assertFalse(cfg.familias_permitidas)
        self.assertTrue(cfg.admite_familia("cualquier_familia_nueva"))


class TestCarrilGeneral(unittest.TestCase):
    def test_admite_toda_la_reserva(self):
        for c in universe.build_reserve(objetivo_lote=10, seed=4):
            self.assertTrue(lanes.validar_candidato(c, lanes.LEGALMENTE_GENERAL).admitido)


class TestCarrilInstitucional(unittest.TestCase):
    def test_admite_familia_profesional(self):
        v = lanes.validar_candidato(candidato(familia_editorial="cumplimiento_compliance",
                                              materia="corporativo_compliance"),
                                    lanes.LINKEDIN_LEGALMENTE)
        self.assertTrue(v.admitido, v.motivos)

    def test_rechaza_familia_no_profesional(self):
        v = lanes.validar_candidato(candidato(familia_editorial="etimologia"),
                                    lanes.LINKEDIN_LEGALMENTE)
        self.assertFalse(v.admitido)
        self.assertTrue(any("familia editorial" in m for m in v.motivos))

    def test_rechaza_materia_fuera_del_carril(self):
        v = lanes.validar_candidato(candidato(materia="historia_del_derecho"),
                                    lanes.LINKEDIN_LEGALMENTE)
        self.assertFalse(v.admitido)

    def test_no_restringe_la_variedad_visual(self):
        """'No hacerlo visualmente aburrido': la restricción es editorial."""
        cfg = lanes.get(lanes.LINKEDIN_LEGALMENTE)
        self.assertTrue(cfg.familias_permitidas)
        for campo in vars(cfg):
            self.assertNotIn("visual_family", campo)

    def test_cubre_las_areas_que_pide_el_handoff(self):
        for area in ("contrato_bajo_lupa", "cumplimiento_compliance", "riesgo",
                     "prueba", "evidencia_digital", "herramienta_practica", "proceso"):
            self.assertIn(area, lanes.FAMILIAS_LINKEDIN_LEGALMENTE)
        for mat in ("corporativo_compliance", "inmobiliario", "laboral", "penal", "mercantil"):
            self.assertIn(mat, lanes.MATERIAS_LINKEDIN_LEGALMENTE)

    def test_la_reserva_produce_candidatos_admisibles(self):
        r = universe.build_reserve(objetivo_lote=10, seed=3)
        admitidos = [c for c in r if lanes.validar_candidato(c, lanes.LINKEDIN_LEGALMENTE).admitido]
        self.assertGreater(len(admitidos), 0)


class TestCarrilFounder(unittest.TestCase):
    def test_sin_hecho_verificable_se_bloquea(self):
        """Handoff §9.B: nunca inventar experiencia. Ejecutable, no advertencia."""
        v = lanes.validar_candidato(candidato(), lanes.LINKEDIN_FOUNDER)
        self.assertFalse(v.admitido)
        self.assertTrue(any("NO inventa" in m for m in v.motivos))

    def test_con_hecho_completo_se_admite(self):
        pf = lanes.ProfileFact("Abogado en ejercicio", "perfil profesional público",
                               "Raymundo Acevedo")
        self.assertTrue(lanes.validar_candidato(candidato(), lanes.LINKEDIN_FOUNDER, pf).admitido)

    def test_hecho_sin_fuente_se_bloquea(self):
        pf = lanes.ProfileFact("Dirigí una operación", "", "Raymundo Acevedo")
        v = lanes.validar_candidato(candidato(), lanes.LINKEDIN_FOUNDER, pf)
        self.assertFalse(v.admitido)
        self.assertTrue(any("fuente" in m for m in v.motivos))

    def test_hecho_sin_verificador_se_bloquea(self):
        pf = lanes.ProfileFact("Dirigí una operación", "documento interno", "")
        self.assertFalse(lanes.validar_candidato(candidato(), lanes.LINKEDIN_FOUNDER, pf).admitido)

    def test_el_profile_fact_no_lo_genera_el_sistema(self):
        """No existe ninguna fábrica automática de hechos del fundador."""
        self.assertFalse([n for n in dir(lanes)
                          if "generar" in n.lower() or "inventar" in n.lower()])


class TestMemoriasSeparadas(unittest.TestCase):
    def test_una_memoria_por_carril(self):
        m = lanes.LaneMemories()
        self.assertEqual(set(m.resumen()), set(lanes.CARRILES))

    def test_linkedin_no_quema_el_carril_general(self):
        """Memorias parcialmente independientes: mismo cerebro jurídico,
        distinta fatiga editorial."""
        m = lanes.LaneMemories()
        fp = SemanticFingerprint(content_id="x", materia="laboral", submateria="jornada",
                                 concepto_nucleo="jornada", familia_editorial="proceso",
                                 necesidad="entender", pregunta_resuelta="p", angulo="a")
        m[lanes.LINKEDIN_LEGALMENTE].record(fp, APROBADA)
        self.assertTrue(m[lanes.LINKEDIN_LEGALMENTE].evaluar(fp).bloquea)
        self.assertFalse(m[lanes.LEGALMENTE_GENERAL].evaluar(fp).bloquea)

    def test_carril_desconocido_falla_al_acceder(self):
        with self.assertRaises(lanes.LaneError):
            lanes.LaneMemories()["TIKTOK"]


class TestRatioOperativo(unittest.TestCase):
    """Fase de reconciliación con legalmente-web: LinkedIn LegalMente exige
    75% de escenas operativas en lotes de 4+ (channel-strategy.ts,
    LINKEDIN_OPERATIONAL_STRATEGIES)."""

    def test_no_se_aplica_con_menos_de_cuatro(self):
        candidatos = [candidato(familia_editorial="mito") for _ in range(3)]
        ok, motivo = lanes.verificar_ratio_operativo(candidatos, lanes.LINKEDIN_LEGALMENTE)
        self.assertTrue(ok)
        self.assertEqual(motivo, "")

    def test_no_se_aplica_fuera_del_carril_institucional(self):
        candidatos = [candidato(familia_editorial="mito") for _ in range(6)]
        ok, _ = lanes.verificar_ratio_operativo(candidatos, lanes.LEGALMENTE_GENERAL)
        self.assertTrue(ok)

    def test_lote_todo_metaforico_falla(self):
        candidatos = [candidato(familia_editorial="mito") for _ in range(5)]
        ok, motivo = lanes.verificar_ratio_operativo(candidatos, lanes.LINKEDIN_LEGALMENTE)
        self.assertFalse(ok)
        self.assertIn("75%", motivo)

    def test_lote_mayormente_operativo_pasa(self):
        candidatos = ([candidato(familia_editorial="proceso") for _ in range(3)] +
                      [candidato(familia_editorial="checklist")] +
                      [candidato(familia_editorial="mito")])
        ok, _ = lanes.verificar_ratio_operativo(candidatos, lanes.LINKEDIN_LEGALMENTE)
        self.assertTrue(ok)

    def test_escena_operativa_reconoce_familias_de_proceso_y_evidencia(self):
        for fam in ("proceso", "documento_clave", "carga_de_la_prueba", "cumplimiento_compliance"):
            self.assertTrue(lanes.escena_operativa(fam), fam)

    def test_escena_operativa_no_marca_familias_metaforicas(self):
        for fam in ("mito", "maxima_aforismo", "rareza_juridica"):
            self.assertFalse(lanes.escena_operativa(fam), fam)


if __name__ == "__main__":
    unittest.main()
