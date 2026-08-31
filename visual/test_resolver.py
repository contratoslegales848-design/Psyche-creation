"""Resolucion de CONTENT_ID contra el canon real, y limites de la memoria visual.

Deliberadamente pequeño: el valor de esta fase esta en el recorrido real, no en
inflar el numero de pruebas.
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pipeline  # noqa: E402
import resolver  # noqa: E402
from brief import VisualPolicy  # noqa: E402
from memory import VisualMemory, VisualMemoryEntry  # noqa: E402
from providers import FakeImageProvider  # noqa: E402
from test_visual_pipeline import HANDOFF, PROC, make_brief  # noqa: E402

POLICY = VisualPolicy.load()


class TestResolucionReal(unittest.TestCase):
    """Contra el canon real del repositorio, no contra fixtures."""

    def test_lista_content_ids_reales(self):
        ids = resolver.list_content_ids()
        self.assertTrue(ids, "el repositorio debe declarar al menos un CONTENT_ID")
        self.assertTrue(all(len(t) == 3 for t in ids))

    def test_gate_summary_no_reinterpreta_estados(self):
        filas = resolver.gate_summary()
        self.assertEqual(len(filas), 3)
        for f in filas:
            # VISUAL_READY jamas dice SI mientras el gate canonico este cerrado.
            if f["ART_GATE"] != "ABIERTO":
                self.assertEqual(f["VISUAL_READY"], "NO")

    def test_ejemplo_tecnico_se_marca_como_fixture(self):
        r = resolver.resolve("LM-EJEMPLO-TECNICO-001")
        self.assertTrue(r.resolved)
        self.assertEqual(r.origin, resolver.TEST_FIXTURE)
        self.assertFalse(r.production_ready)
        self.assertTrue(any("EJEMPLO_TECNICO" in b for b in r.blocking))

    def test_content_id_inexistente_no_inventa_nada(self):
        r = resolver.resolve("LM-NO-EXISTE-999")
        self.assertFalse(r.resolved)
        self.assertIsNone(r.artefacto)
        self.assertIsNone(r.handoff)
        self.assertTrue(r.blocking)

    def test_gobernado_sin_handoff_declara_el_bloqueo(self):
        with tempfile.TemporaryDirectory() as d:
            art = {"id": "x", "frase": "f", "remate": "r",
                   "procedencia": {"modo": "GOBERNADO", "content_id": "LM-G-1",
                                   "publicable": True, "jurisdiction_layer": "CAPA_A_TRANSVERSAL",
                                   "handoff_id": "HO-404", "piece_id": "P-404",
                                   "claims": [{"claim_id": "c", "approved_claim_hash": "a" * 64}]}}
            Path(d, "a.json").write_text(json.dumps(art), encoding="utf-8")
            r = resolver.resolve("LM-G-1", content_dir=d, packets_dir=d, records_dir=d)
            self.assertTrue(r.resolved)
            self.assertFalse(r.production_ready)
            self.assertTrue(any("HO-404" in b for b in r.blocking))
            self.assertTrue(any("claim packet" in b for b in r.blocking))

    def test_el_pipeline_bloquea_el_contenido_real_no_publicable(self):
        """Recorrido real: resolver -> pipeline. Debe cerrar sin llamar al proveedor."""
        r = resolver.resolve("LM-EJEMPLO-TECNICO-001")
        prov = FakeImageProvider()
        run = pipeline.generate_visual(r.artefacto["procedencia"], make_brief(), POLICY,
                                       prov, handoff=r.handoff)
        self.assertEqual(run.receipt.status, "GATE_CERRADO")
        self.assertEqual(prov.llamadas, 0)
        self.assertEqual(run.asset_bytes, b"")


class TestMemoriaNoDecideAutoridad(unittest.TestCase):
    """§35 — la memoria visual solo afecta variables visuales."""

    def test_memoria_no_altera_canon_del_receipt(self):
        mem = VisualMemory()
        for i in range(3):
            mem.record(VisualMemoryEntry(content_id="otro", generation_id=f"g{i}",
                                         scene_type="despacho en penumbra al amanecer",
                                         main_subject="un escritorio de nogal con un contrato cerrado",
                                         camera_angle="35mm, ligeramente picada"))
        sin = pipeline.generate_visual(PROC, make_brief(), POLICY, FakeImageProvider(), HANDOFF)
        con = pipeline.generate_visual(PROC, make_brief(), POLICY, FakeImageProvider(), HANDOFF,
                                       memory=mem)

        # La memoria SI cambia la peticion visual...
        self.assertGreater(con.plan.repetition_score, 0)
        self.assertEqual(sin.plan.repetition_score, 0)
        # ...y NO cambia nada canonico.
        self.assertEqual(sin.receipt.content_id, con.receipt.content_id)
        self.assertEqual(sin.receipt.content_hash, con.receipt.content_hash)
        self.assertEqual(sin.receipt.procedencia, con.receipt.procedencia)

    def test_memoria_no_puede_abrir_un_gate(self):
        mem = VisualMemory()
        run = pipeline.generate_visual(PROC, make_brief(), POLICY, FakeImageProvider(),
                                       handoff=None, memory=mem)
        self.assertEqual(run.receipt.status, "GATE_CERRADO")

    def test_memoria_no_toca_exact_copy(self):
        mem = VisualMemory()
        mem.record(VisualMemoryEntry(content_id="o", generation_id="g",
                                     main_subject="un escritorio de nogal con un contrato cerrado"))
        frase = "El derecho no favorece a quien duerme sobre sus derechos"
        run = pipeline.generate_visual(PROC, make_brief(), POLICY, FakeImageProvider(), HANDOFF,
                                       memory=mem, exact_copy=frase, content_type="maxima")
        self.assertEqual(run.typography_plan.rendered_text(), frase)


if __name__ == "__main__":
    unittest.main(verbosity=2)
