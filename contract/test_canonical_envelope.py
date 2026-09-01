"""Contract tests del Canonical Envelope v1.

Estas pruebas son las que legalmente-web debe poder ejecutar contra las mismas
fixtures versionadas. Sin acoplamiento en tiempo de ejecucion entre repos: solo
esquema + fixtures.
"""

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from canonical_envelope import (  # noqa: E402
    ContractViolation, consume, validate_envelope, WEB_MUST_NOT,
)

FIX = Path(__file__).resolve().parent / "fixtures"


def load(name):
    return json.loads((FIX / f"{name}.json").read_text(encoding="utf-8"))


class TestContrato(unittest.TestCase):
    def test_version_conocida_se_acepta(self):
        self.assertEqual(validate_envelope(load("valid_ready")), [])
        self.assertTrue(consume(load("valid_ready")))

    def test_version_desconocida_se_rechaza(self):
        with self.assertRaises(ContractViolation):
            consume(load("unknown_version"))

    def test_estado_desconocido_se_rechaza(self):
        with self.assertRaises(ContractViolation):
            consume(load("unknown_state"))

    def test_provenance_ausente_se_rechaza(self):
        with self.assertRaises(ContractViolation):
            consume(load("missing_provenance"))

    def test_claim_bloqueado_no_puede_volverse_aprobado(self):
        env = load("blocked_claim")
        self.assertEqual(validate_envelope(env), [])       # es valido...
        self.assertEqual(env["claim_state"], "BLOQUEADO")  # ...y sigue bloqueado
        self.assertEqual(env["art_eligibility"], "NO_ELEGIBLE")

    def test_escalamiento_de_autoridad_imposible(self):
        """Un envelope que se autodeclara elegible con claim bloqueado es rechazado."""
        with self.assertRaises(ContractViolation):
            consume(load("authority_escalation_attempt"))

    def test_territorio_no_cubierto_sigue_no_cubierto(self):
        env = load("unsupported_territory")
        self.assertEqual(env["territories"], [])
        self.assertEqual(env["art_eligibility"], "NO_ELEGIBLE")

    def test_fuente_pendiente_no_habilita_arte(self):
        env = load("source_pending")
        self.assertEqual(env["source_state"], "PENDIENTE")
        self.assertEqual(env["legal_gate_state"], "CERRADO")

    def test_campos_opcionales_nuevos_son_tolerados(self):
        """Compatibilidad hacia adelante: un campo extra no rompe al consumidor."""
        env = dict(load("valid_ready"), campo_futuro="algo", otro=123)
        self.assertEqual(validate_envelope(env), [])

    def test_envelope_ausente(self):
        for malo in (None, [], "texto", 42):
            self.assertTrue(validate_envelope(malo))

    def test_lista_de_prohibiciones_del_consumidor(self):
        for prohibido in ("approve_claim", "open_legal_gate", "change_canonical_hash"):
            self.assertIn(prohibido, WEB_MUST_NOT)

    def test_todas_las_fixtures_son_json_valido(self):
        archivos = sorted(FIX.glob("*.json"))
        self.assertGreaterEqual(len(archivos), 8)
        for f in archivos:
            json.loads(f.read_text(encoding="utf-8"))


class TestTransporte(unittest.TestCase):
    """Metadatos de transporte para trazabilidad cross-repo (portados de PR #27)."""

    def test_fixtures_declaran_emisor_y_digest(self):
        env = load("valid_ready")
        self.assertEqual(env["source_system"], "Psyche-creation")
        self.assertTrue(env["source_revision"])
        self.assertRegex(env["provenance_digest"], r"^[0-9a-f]{64}$")

    def test_digest_con_forma_invalida_se_rechaza(self):
        """Un digest malformado aparenta trazabilidad: es peor que no tenerlo."""
        with self.assertRaises(ContractViolation):
            consume(load("bad_provenance_digest"))

    def test_emisor_no_autorizado_se_rechaza(self):
        env = dict(load("valid_ready"), source_system="otro-sistema")
        self.assertTrue(validate_envelope(env))

    def test_transporte_ausente_no_rompe_la_v1(self):
        """Los metadatos son aditivos: su ausencia no invalida un envelope v1."""
        env = {k: v for k, v in load("valid_ready").items()
               if k not in ("source_system", "source_revision", "provenance_digest")}
        self.assertEqual(validate_envelope(env), [])

    def test_el_estado_canonico_nunca_es_opaco(self):
        """Contraste con PR #27, que aceptaba cualquier string como canonicalStatus.

        Aquí un estado desconocido —incluido 'APPROVED', que suena a autoridad—
        se rechaza. Un adapter que transporta estados opacos no puede impedir
        que uno forjado lo atraviese.
        """
        for falso in ("APPROVED", "LIVE", "PUBLISHABLE", "SUPER_APTO"):
            env = dict(load("valid_ready"), claim_state=falso)
            self.assertTrue(validate_envelope(env), f"{falso} no debe aceptarse")


if __name__ == "__main__":
    unittest.main(verbosity=2)
