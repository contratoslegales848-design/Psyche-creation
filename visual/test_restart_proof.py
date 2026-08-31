"""Prueba de recuperacion: cerrar el proceso y reabrirlo no debe hacer que
LegalMente olvide quien es. Usa un directorio temporal CONTROLADO por el
propio test (nunca /tmp implicito de otras pasadas), pero simula un restart
real: se instancian objetos NUEVOS de AssetRegistry/VisualMemory apuntando a
la MISMA raiz en disco, sin reusar ningun objeto Python del "proceso anterior".
"""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import feedback as feedback_mod  # noqa: E402
import pipeline  # noqa: E402
import registry as registry_mod  # noqa: E402
import runtime_config  # noqa: E402
from brief import VisualPolicy  # noqa: E402
from providers import FakeImageProvider  # noqa: E402
from test_visual_pipeline import HANDOFF, PROC, make_brief  # noqa: E402

POLICY = VisualPolicy.load()


class TestRestartProof(unittest.TestCase):

    def test_registro_persistente_sobrevive_a_un_restart_simulado(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "runtime-persistente"

            # --- "proceso 1": crea el registro y GEN1 ---
            reg1 = registry_mod.AssetRegistry(root)
            run1 = pipeline.generate_visual(
                PROC, make_brief(), POLICY, FakeImageProvider(), handoff=HANDOFF, registry=reg1)
            self.assertEqual(run1.receipt.status, "PENDIENTE_REVISION_HUMANA")
            gen1_id = run1.receipt.generation_id
            canonical_hash_gen1 = run1.receipt.content_hash

            # --- "cierre del proceso": se destruye toda referencia Python ---
            del reg1

            # --- "proceso 2": instancia NUEVA apuntando a la MISMA raiz en disco ---
            reg2 = registry_mod.AssetRegistry(root)
            historial = reg2.generations_for(PROC["content_id"])
            self.assertEqual(len(historial), 1)
            self.assertEqual(historial[0]["generation_id"], gen1_id)

            recuperado = reg2.get_generation(PROC["content_id"], gen1_id)
            self.assertIsNotNone(recuperado)
            self.assertEqual(recuperado["content_hash"], canonical_hash_gen1)

            # --- regenera GEN2 sobre el registro "recien reabierto", a partir
            # del run ORIGINAL (previous_run solo aporta .receipt.generation_id,
            # que es identico a lo que reg2 acaba de recuperar de disco) ---
            brief_revisado, cambios = feedback_mod.apply_feedback(make_brief(), ["TOO_DARK"])
            run2 = pipeline.regenerate(
                run1, brief_revisado, POLICY, FakeImageProvider(), PROC,
                ["TOO_DARK"], cambios, handoff=HANDOFF, registry=reg2)
            self.assertEqual(run2.receipt.status, "PENDIENTE_REVISION_HUMANA")
            self.assertEqual(run2.receipt.parent_generation_id, gen1_id)
            self.assertNotEqual(run2.receipt.generation_id, gen1_id)  # nunca duplica la anterior
            self.assertEqual(run2.receipt.content_hash, canonical_hash_gen1)  # canon intacto

            # --- "proceso 3": otro restart mas, verifica lineage completo desde disco ---
            reg3 = registry_mod.AssetRegistry(root)
            historial_final = reg3.generations_for(PROC["content_id"])
            self.assertEqual(len(historial_final), 2)
            ids = {g["generation_id"] for g in historial_final}
            self.assertEqual(ids, {gen1_id, run2.receipt.generation_id})
            gen2_en_disco = reg3.get_generation(PROC["content_id"], run2.receipt.generation_id)
            self.assertEqual(gen2_en_disco["parent_generation_id"], gen1_id)

    def test_default_registry_root_nunca_es_tmp_por_defecto(self):
        root = runtime_config.default_registry_root()
        self.assertNotIn("/tmp/", str(root) + "/")


if __name__ == "__main__":
    unittest.main()
