"""Fixtures del contrato versionado del Command Center (mandato de
continuacion §6): valid, unknown version, unknown state, simulated provider,
blocked content, no metrics, publication absent, authority escalation."""

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import command_center  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "command_center"


def _cargar(nombre):
    return json.loads((FIXTURES / nombre).read_text(encoding="utf-8"))


class TestCommandCenterFixtures(unittest.TestCase):

    def test_valid_no_tiene_errores(self):
        self.assertEqual(command_center.validate_envelope(_cargar("valid.json")), [])

    def test_unknown_version_falla_cerrado(self):
        errores = command_center.validate_envelope(_cargar("unknown_version.json"))
        self.assertTrue(errores)
        self.assertIn("desconocida", errores[0])

    def test_unknown_state_se_reporta(self):
        errores = command_center.validate_envelope(_cargar("unknown_state.json"))
        self.assertTrue(any("fuera del vocabulario cerrado" in e for e in errores))

    def test_simulated_provider_no_es_error_pero_esta_marcado(self):
        env = _cargar("simulated_provider.json")
        self.assertEqual(command_center.validate_envelope(env), [])
        self.assertEqual(env["content"][0]["data_freshness"], command_center.FRESHNESS_SIMULATED)

    def test_blocked_content_no_es_error(self):
        self.assertEqual(command_center.validate_envelope(_cargar("blocked_content.json")), [])

    def test_no_metrics_nunca_es_error_measurement_ausente_es_honesto(self):
        env = _cargar("no_metrics.json")
        self.assertEqual(command_center.validate_envelope(env), [])
        self.assertEqual(env["content"][0]["measurement_state"], "NO_MEDIDO")

    def test_publication_absent_no_es_error(self):
        self.assertEqual(command_center.validate_envelope(_cargar("publication_absent.json")), [])

    def test_authority_escalation_attempt_se_rechaza(self):
        errores = command_center.validate_envelope(_cargar("authority_escalation_attempt.json"))
        self.assertTrue(any("escalada de autoridad" in e for e in errores))


if __name__ == "__main__":
    unittest.main()
