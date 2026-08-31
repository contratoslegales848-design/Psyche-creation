"""Preflight de proveedor real y peticion preparada para PIEZA-01 — nunca ejecutada."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import provider_preflight  # noqa: E402
import topology  # noqa: E402


class TestProviderPreflight(unittest.TestCase):

    def test_sin_endpoint_configurado_cierra_por_invalid_config(self):
        r = provider_preflight.preflight()
        # En este entorno no hay LEGALMENTE_IMAGE_PROVIDER_ENDPOINT configurado.
        self.assertIn(r.status, (provider_preflight.INVALID_CONFIG, provider_preflight.MISSING_CREDENTIALS))
        self.assertFalse(r.live_allowed)

    def test_preflight_nunca_expone_el_valor_de_la_credencial(self):
        r = provider_preflight.preflight()
        serializado = str(r.to_dict())
        self.assertNotIn("Bearer", serializado)

    def test_ready_requiere_endpoint_y_credencial(self):
        from providers.http_provider import HttpProviderConfig
        cfg = HttpProviderConfig(provider_id="x", endpoint="https://example.invalid",
                                  api_key_env="__LEGALMENTE_TEST_KEY_NO_EXISTE__")
        r = provider_preflight.preflight(cfg)
        self.assertEqual(r.status, provider_preflight.MISSING_CREDENTIALS)

    def test_ready_cuando_endpoint_y_credencial_presentes(self):
        import os
        from providers.http_provider import HttpProviderConfig
        os.environ["__LEGALMENTE_TEST_KEY_TMP__"] = "no-es-una-credencial-real"
        try:
            cfg = HttpProviderConfig(provider_id="x", endpoint="https://example.invalid",
                                      api_key_env="__LEGALMENTE_TEST_KEY_TMP__")
            r = provider_preflight.preflight(cfg)
            self.assertEqual(r.status, provider_preflight.READY)
        finally:
            del os.environ["__LEGALMENTE_TEST_KEY_TMP__"]


class TestProviderRequestPieza01(unittest.TestCase):

    def test_peticion_preparada_nunca_ejecuta_red(self):
        import cli
        from brief import VisualPolicy
        from families import VisualFamilyRegistry
        policy = VisualPolicy.load()
        fams = VisualFamilyRegistry.load()
        brief = cli.gen3_brief_pieza01(policy, fams)
        from providers.base import ProviderCapabilities
        caps = ProviderCapabilities(provider_id="generic-http-image-v1", aspect_ratios=("9:16",))
        req = provider_preflight.build_pieza01_request(brief, policy, fams.get(brief.visual_family), caps)
        self.assertFalse(req["live_execution_attempted"])
        self.assertTrue(req["requires_paid_execution"])
        self.assertEqual(req["estimated_cost"], "UNKNOWN")
        self.assertFalse(req["generator_writes_legalmente"])
        self.assertFalse(req["generator_writes_exact_copy"])

    def test_incorpora_el_feedback_real_de_gen3(self):
        """La metafora llave/umbral solo existe si GEN3 realmente la aplico
        (review-packet-gen-2f2dfb9c6f2f.json); no se inventa aqui."""
        import cli
        from brief import VisualPolicy
        from families import VisualFamilyRegistry
        policy = VisualPolicy.load()
        fams = VisualFamilyRegistry.load()
        brief = cli.gen3_brief_pieza01(policy, fams)
        self.assertIn("llave", brief.metaphor.lower())
        self.assertIn("imagen de stock", brief.negative_constraints)


class TestTopology(unittest.TestCase):

    def test_vocabulario_cerrado(self):
        cerrado = {topology.CONNECTED, topology.READY_TO_CONNECT, topology.BLOCKED,
                   topology.DISCONNECTED, topology.EXPERIMENTAL, topology.SUPERSEDED}
        for link in topology.build_topology():
            self.assertIn(link["state"], cerrado)

    def test_fake_provider_siempre_experimental(self):
        links = {(l["source"], l["target"]): l["state"] for l in topology.build_topology()}
        self.assertEqual(links[("visual_pipeline", "fake_image_provider")], topology.EXPERIMENTAL)

    def test_legal_approval_nunca_conectada_a_visual_review(self):
        links = {(l["source"], l["target"]): l["state"] for l in topology.build_topology()}
        self.assertEqual(links[("human_legal_approval", "human_visual_review")], topology.DISCONNECTED)


if __name__ == "__main__":
    unittest.main()
