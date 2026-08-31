"""Generalizacion del motor de memoria a multiples materias (orden expresa del
fundador, alcance acotado a solo el motor — sin poblar materias nuevas).

Invariante central: la COMBINACION (materia, concepto) se penaliza si se
repite reciente; ni la materia ni el concepto quedan vedados por separado.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pipeline  # noqa: E402
from memory import VisualMemory, VisualMemoryEntry, PESO_MATERIA_CONCEPTO  # noqa: E402
from test_visual_pipeline import make_brief  # noqa: E402


def entry(materia="", concepto="", gid="g", subject="sujeto neutro", scene="escena neutra"):
    return VisualMemoryEntry(content_id="c", generation_id=gid, main_subject=subject,
                              scene_type=scene, materia=materia, concepto=concepto)


class TestCombinacionMateriaConcepto(unittest.TestCase):

    def test_repetir_la_misma_combinacion_penaliza(self):
        mem = VisualMemory()
        mem.record(entry(materia="civil", concepto="posesion", gid="g1"))
        eval_ = mem.assess(entry(materia="civil", concepto="posesion", gid="g2"))
        self.assertGreaterEqual(eval_.score, PESO_MATERIA_CONCEPTO)
        self.assertTrue(any("combinacion materia+concepto" in r for r in eval_.razones))

    def test_misma_materia_otro_concepto_no_penaliza_ese_eje(self):
        mem = VisualMemory()
        mem.record(entry(materia="civil", concepto="posesion", gid="g1"))
        eval_ = mem.assess(entry(materia="civil", concepto="prescripcion", gid="g2"))
        self.assertFalse(any("combinacion materia+concepto" in r for r in eval_.razones))

    def test_mismo_concepto_otra_materia_no_penaliza_ese_eje(self):
        mem = VisualMemory()
        mem.record(entry(materia="civil", concepto="prueba", gid="g1"))
        eval_ = mem.assess(entry(materia="penal", concepto="prueba", gid="g2"))
        self.assertFalse(any("combinacion materia+concepto" in r for r in eval_.razones))

    def test_sin_taxonomia_declarada_no_participa_del_eje(self):
        mem = VisualMemory()
        mem.record(entry(materia="", concepto="", gid="g1"))
        eval_ = mem.assess(entry(materia="", concepto="", gid="g2"))
        self.assertFalse(any("combinacion materia+concepto" in r for r in eval_.razones))

    def test_familia_visual_compartida_nunca_penaliza_pese_a_taxonomia_igual(self):
        """Invariante preexistente (no tocado): reusar la MISMA familia visual
        deliberadamente no es repeticion, sin importar la taxonomia."""
        mem = VisualMemory()
        e1 = entry(materia="civil", concepto="posesion", gid="g1")
        e1.visual_family = "basalt_and_gold_leaf"
        mem.record(e1)
        e2 = entry(materia="penal", concepto="dolo", gid="g2")
        e2.visual_family = "basalt_and_gold_leaf"
        eval_ = mem.assess(e2)
        self.assertFalse(any("familia" in r.lower() for r in eval_.razones))

    def test_combinacion_normaliza_mayusculas_y_acentos(self):
        mem = VisualMemory()
        mem.record(entry(materia="Civil", concepto="Posesión", gid="g1"))
        eval_ = mem.assess(entry(materia="CIVIL", concepto="posesion", gid="g2"))
        self.assertTrue(any("combinacion materia+concepto" in r for r in eval_.razones))


class TestPipelineThreadsTaxonomia(unittest.TestCase):
    """El motor solo transporta taxonomia real recibida — nunca la infiere."""

    def test_entry_desde_brief_sin_taxonomia_queda_vacia(self):
        e = pipeline._entry_desde_brief("c1", make_brief(), "g1")
        self.assertEqual(e.materia, "")
        self.assertEqual(e.concepto, "")

    def test_entry_desde_brief_transporta_taxonomia_real(self):
        tax = {"materia": "civil", "submateria": "derechos_reales",
               "concepto": "propiedad_y_posesion", "situacion_humana": "x", "content_type": "concepto"}
        e = pipeline._entry_desde_brief("c1", make_brief(), "g1", taxonomia=tax)
        self.assertEqual(e.materia, "civil")
        self.assertEqual(e.concepto, "propiedad_y_posesion")

    def test_taxonomia_ausente_o_none_no_revienta(self):
        e = pipeline._entry_desde_brief("c1", make_brief(), "g1", taxonomia=None)
        self.assertEqual(e.materia, "")


if __name__ == "__main__":
    unittest.main()
