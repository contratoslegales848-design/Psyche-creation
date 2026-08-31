"""Disciplina de rotacion de lotes — reglas mecanicas adaptadas de material de
Drive marcado explicitamente no canonico. Nada aqui verifica ni produce
afirmaciones juridicas."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import rotation  # noqa: E402
from memory import VisualMemoryEntry  # noqa: E402


def entry(**kw):
    base = dict(content_id="c", generation_id="g", visual_family="fam_a",
                scene_type="escena_a", metaphor="metafora_a", camera_angle="picada",
                human_presence="ninguna", materia="civil")
    base.update(kw)
    return VisualMemoryEntry(**base)


class TestVariacionMinima(unittest.TestCase):

    def test_sin_pieza_anterior_siempre_cumple(self):
        r = rotation.verificar_variacion_minima(None, entry())
        self.assertTrue(r.minimo_alcanzado)

    def test_pieza_identica_no_cumple(self):
        a = entry()
        b = entry()
        r = rotation.verificar_variacion_minima(a, b)
        self.assertFalse(r.minimo_alcanzado)
        self.assertEqual(r.ejes_cambiados, set())

    def test_cambiar_3_de_5_ejes_cumple(self):
        a = entry()
        b = entry(visual_family="fam_b", scene_type="escena_b", metaphor="metafora_b")
        r = rotation.verificar_variacion_minima(a, b)
        self.assertTrue(r.minimo_alcanzado)
        self.assertEqual(len(r.ejes_cambiados), 3)

    def test_cambiar_solo_2_de_5_ejes_no_cumple(self):
        a = entry()
        b = entry(visual_family="fam_b", scene_type="escena_b")
        r = rotation.verificar_variacion_minima(a, b)
        self.assertFalse(r.minimo_alcanzado)

    def test_cambio_de_fondo_solamente_no_es_variacion(self):
        """Ataque directo del propio material de Drive: 'no cuenta como
        variacion cambiar unicamente el fondo o el color'. Aqui 'fondo' no es
        ninguno de los 5 ejes reales, asi que cambiarlo (fuera de estos ejes)
        nunca puede, por construccion, hacer que el check pase."""
        a = entry()
        b = entry()  # ejes identicos: un cambio de "fondo" no capturado por
        # ningun eje de AXES_VARIACION_MINIMA no puede aparecer como cambio.
        r = rotation.verificar_variacion_minima(a, b)
        self.assertFalse(r.minimo_alcanzado)

    def test_dato_ausente_en_ambos_no_cuenta_como_cambio(self):
        a = entry(human_presence="")
        b = entry(human_presence="", visual_family="fam_b", scene_type="escena_b", metaphor="m_b")
        r = rotation.verificar_variacion_minima(a, b)
        self.assertNotIn("human_presence", r.ejes_cambiados)


class TestDiversidadDeLote(unittest.TestCase):

    def test_lote_vacio_no_cumple(self):
        r = rotation.assess_batch_diversity([])
        self.assertFalse(r.cumple)

    def test_lote_de_10_todo_identico_no_cumple(self):
        lote = [entry(generation_id=f"g{i}") for i in range(10)]
        r = rotation.assess_batch_diversity(lote)
        self.assertFalse(r.cumple)
        self.assertEqual(r.materias_distintas, 1)
        self.assertEqual(r.familias_distintas, 1)

    def test_lote_de_10_suficientemente_diverso_cumple(self):
        materias = ["civil", "penal", "laboral", "familia", "sucesiones", "inmobiliario"]
        familias = ["fam_a", "fam_b", "fam_c", "fam_d"]
        encuadres = ["picada", "contrapicada", "cenital", "plano medio", "plano general",
                     "plano detalle", "contraluz"]
        lote = [entry(generation_id=f"g{i}", materia=materias[i % len(materias)],
                      visual_family=familias[i % len(familias)],
                      camera_angle=encuadres[i % len(encuadres)]) for i in range(10)]
        r = rotation.assess_batch_diversity(lote)
        self.assertTrue(r.cumple, r.incumplidos)

    def test_minimos_escalan_con_el_tamano_del_lote(self):
        """Un lote de 5 no debe exigir los mismos minimos absolutos que uno
        de 10 — se escala proporcionalmente, nunca se exige sobre datos que
        el lote pequeno no puede tener."""
        r5 = rotation.assess_batch_diversity([entry(generation_id=f"g{i}") for i in range(5)])
        r10 = rotation.assess_batch_diversity([entry(generation_id=f"g{i}") for i in range(10)])
        self.assertLessEqual(r5.minimos["materias"], r10.minimos["materias"])

    def test_materia_ausente_no_se_exige(self):
        """Si ninguna pieza declara materia (taxonomia no disponible), ese
        eje simplemente no se evalua — no se fuerza un incumplimiento sobre
        un dato que nunca existio."""
        lote = [entry(generation_id=f"g{i}", materia="") for i in range(10)]
        r = rotation.assess_batch_diversity(lote)
        self.assertFalse(any("materias" in i for i in r.incumplidos))


if __name__ == "__main__":
    unittest.main()
