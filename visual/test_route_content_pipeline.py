import json
import sys
import unittest
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pipeline
import route_engine
import resolver
from brief import VisualPolicy
from providers import FakeImageProvider
from test_visual_pipeline import make_brief


REPO = Path(__file__).resolve().parent.parent
POLICY = VisualPolicy.load()


class TestRutaDesdeContenidoReal(unittest.TestCase):
    def test_artefacto_real_abre_ruta_y_conserva_content_id(self):
        artefacto = json.loads((REPO / "content" / "pieza-01-reales.json").read_text(encoding="utf-8"))
        motor = route_engine.RouteEngine()
        ruta_id = motor.leer_entrada_desde_artefacto(artefacto)
        fila = motor.ultima_fila(ruta_id)
        self.assertEqual(fila.materia, "civil")
        self.assertEqual(fila.content_id, "LM-PIEZA-01-REALES")
        self.assertEqual(fila.concepto, "propiedad_y_posesion")
        self.assertEqual(fila.nodo_actual_label, "civil")

    def test_content_id_y_concepto_sobreviven_a_cada_nodo_producido(self):
        artefacto = json.loads((REPO / "content" / "pieza-01-reales.json").read_text(encoding="utf-8"))
        motor = route_engine.RouteEngine()
        ruta_id = motor.leer_entrada_desde_artefacto(artefacto)
        fila = motor.producir_pieza(ruta_id)  # avanza un nodo mas alla del inicial
        self.assertEqual(fila.content_id, "LM-PIEZA-01-REALES")
        self.assertEqual(fila.concepto, "propiedad_y_posesion")

    def test_content_id_real_se_transporta_al_pipeline_sin_inventar(self):
        content_id = "LM-PIEZA-01-REALES"
        resolution = resolver.resolve(content_id)
        self.assertTrue(resolution.resolved)
        brief = replace(make_brief(), content_id=content_id)
        provider = FakeImageProvider()
        run = pipeline.generate_visual_from_content_id(
            content_id, brief, POLICY, provider, dry_run=True
        )
        self.assertEqual(run.receipt.content_id, content_id)
        self.assertEqual(run.receipt.procedencia["modo"], "GOBERNADO")
        self.assertEqual(provider.llamadas, 0)


if __name__ == "__main__":
    unittest.main()
