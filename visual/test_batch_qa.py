"""El lote se juzga como sistema: diez disfraces no son diez piezas."""

import unittest

import batch_qa
import universe
from semantic_fingerprint import SemanticFingerprint
from semantic_memory import SemanticMemory, APROBADA


def diverso(n=10):
    rep = universe.select_batch(universe.build_reserve(objetivo_lote=n, seed=7), n=n)
    return [c.fingerprint() for c in rep.seleccionados]


def clones(n=10):
    """El caso patológico: la misma sesión con n disfraces."""
    return [SemanticFingerprint(
        content_id=f"c{i}", materia="civil", submateria="arrendamiento",
        concepto_nucleo="deposito en garantia", relacion="dinero retenido",
        familia_editorial="mito", necesidad="corregir",
        pregunta_resuelta="puede el arrendador quedarse el deposito",
        angulo="critico", contexto_funcional="despues_del_dano",
        rol_lector="persona", consecuencia="se pierde dinero",
        hook=f"hook distinto {i}", formato=["frase", "historia"][i % 2],
        emocion="sorpresa", metafora=f"metafora {i}", escena=f"escena {i}",
        composicion=f"composicion {i}", objeto_protagonista=f"objeto {i}",
        material=f"material {i}", camara=f"camara {i}", iluminacion=f"luz {i}",
        direccion_artistica=["oleo_narrativo", "foto_impasto"][i % 2]) for i in range(n)]


class TestVeredicto(unittest.TestCase):
    def test_lote_vacio_se_rechaza(self):
        r = batch_qa.evaluar_lote([])
        self.assertFalse(r.aceptado)
        self.assertEqual(r.total, 0)

    def test_un_lote_diverso_se_acepta(self):
        r = batch_qa.evaluar_lote(diverso(), objetivo=10)
        self.assertTrue(r.aceptado, r.incumplimientos)

    def test_diez_disfraces_se_rechazan(self):
        """El defecto que reporta el fundador, detectado."""
        r = batch_qa.evaluar_lote(clones(), objetivo=10)
        self.assertFalse(r.aceptado)
        self.assertTrue(any("misma sesión" in x for x in r.incumplimientos))

    def test_el_arte_distinto_no_salva_el_lote(self):
        """Cada clon tiene metáfora, escena, composición y estilo distintos."""
        fps = clones()
        self.assertEqual(len({f.direccion_artistica for f in fps}), 2)
        self.assertEqual(len({f.metafora for f in fps}), 10)
        self.assertFalse(batch_qa.evaluar_lote(fps, objetivo=10).aceptado)

    def test_detecta_el_par_mas_proximo(self):
        r = batch_qa.evaluar_lote(clones(), objetivo=10)
        self.assertTrue(r.pares_mas_proximos)
        self.assertEqual(r.pares_mas_proximos[0][0], 0.0)

    def test_rechaza_sobreexplotacion_de_una_materia(self):
        fps = diverso()
        for f in fps[:5]:
            f.materia = "penal"
        r = batch_qa.evaluar_lote(fps, objetivo=10)
        self.assertFalse(r.aceptado)
        self.assertTrue(any("sobreexplotación" in x for x in r.incumplimientos))

    def test_rechaza_el_lote_incompleto(self):
        r = batch_qa.evaluar_lote(diverso()[:6], objetivo=10)
        self.assertFalse(r.aceptado)
        self.assertTrue(any("no se rellena" in x.lower() for x in r.incumplimientos))

    def test_rechaza_sin_rotacion_emocional(self):
        fps = diverso()
        for f in fps:
            f.emocion = "gravedad"
        r = batch_qa.evaluar_lote(fps, objetivo=10)
        self.assertFalse(r.aceptado)
        self.assertTrue(any("emocion" in x for x in r.incumplimientos))

    def test_rechaza_una_sola_familia_editorial(self):
        fps = diverso()
        for f in fps:
            f.familia_editorial = "mito"
        self.assertFalse(batch_qa.evaluar_lote(fps, objetivo=10).aceptado)


class TestAusenciaDeDato(unittest.TestCase):
    def test_sin_datos_no_hay_aprobado(self):
        """Ausencia de evidencia nunca es un PASS."""
        fps = [SemanticFingerprint(content_id=f"c{i}") for i in range(10)]
        r = batch_qa.evaluar_lote(fps, objetivo=10)
        self.assertFalse(r.aceptado)
        self.assertTrue(any("no es un aprobado" in x for x in r.incumplimientos))

    def test_un_eje_sin_declarar_bloquea_el_lote(self):
        """Fail-closed: no se acredita rotación emocional sin emociones."""
        fps = diverso()
        for f in fps:
            f.emocion = ""
        r = batch_qa.evaluar_lote(fps, objetivo=10)
        self.assertFalse(r.aceptado)
        self.assertTrue(any("emocion" in x and "dato ausente" in x
                            for x in r.incumplimientos))


class TestTelemetria(unittest.TestCase):
    def test_expone_las_metricas_del_handoff(self):
        t = batch_qa.evaluar_lote(diverso(), objetivo=10).telemetria
        for metrica in ("selection_rate", "semantic_distance_min", "semantic_distance_media",
                        "topic_repetition", "family_coverage", "matter_coverage",
                        "emotional_rotation", "visual_distance", "style_frequency",
                        "composition_frequency", "cooldown_age", "regeneration_rate"):
            self.assertIn(metrica, t)

    def test_selection_rate_refleja_la_curaduria(self):
        fps = diverso()
        t = batch_qa.evaluar_lote(fps, objetivo=10, seleccionadas=fps[:3]).telemetria
        self.assertEqual(t["selection_rate"], 0.3)

    def test_cobertura_de_un_lote_diverso(self):
        t = batch_qa.evaluar_lote(diverso(), objetivo=10).telemetria
        self.assertGreaterEqual(t["family_coverage"], 0.8)
        self.assertGreaterEqual(t["matter_coverage"], 0.8)

    def test_topic_repetition_maxima_en_clones(self):
        self.assertEqual(batch_qa.evaluar_lote(clones(), objetivo=10).telemetria["topic_repetition"], 1.0)

    def test_topic_repetition_nula_en_lote_diverso(self):
        self.assertEqual(batch_qa.evaluar_lote(diverso(), objetivo=10).telemetria["topic_repetition"], 0.0)

    def test_visual_distance_es_nula_sin_plan_visual(self):
        """Sin plan visual no se finge una distancia visual."""
        self.assertIsNone(batch_qa.evaluar_lote(diverso(), objetivo=10).telemetria["visual_distance"])

    def test_cooldown_age_usa_la_memoria(self):
        m = SemanticMemory()
        fps = diverso()
        m.record(fps[0], APROBADA)
        t = batch_qa.evaluar_lote(fps, objetivo=10, memoria=m).telemetria
        self.assertIsNotNone(t["cooldown_age"])

    def test_regeneration_rate(self):
        t = batch_qa.evaluar_lote(diverso(), objetivo=10, regeneraciones=4).telemetria
        self.assertEqual(t["regeneration_rate"], 0.4)


class TestIntegracionConRotation(unittest.TestCase):
    def test_reutiliza_el_motor_visual_existente(self):
        """No duplica rotation.py: lo invoca."""
        r = batch_qa.evaluar_lote(diverso(), objetivo=10)
        self.assertIn("minimos", r.diversidad_visual)
        self.assertIn("cumple", r.diversidad_visual)

    def test_serializable(self):
        import json
        json.dumps(batch_qa.evaluar_lote(diverso(), objetivo=10).to_dict(), ensure_ascii=False)


if __name__ == "__main__":
    unittest.main()
