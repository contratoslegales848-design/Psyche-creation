#!/usr/bin/env python3
"""Pruebas unitarias para check_pilot_governance.py (control de CI del piloto)."""
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_pilot_governance import check_pilot_governance, main  # noqa: E402

SCRIPT = Path(__file__).resolve().parent / "check_pilot_governance.py"

BASE_CLAIM = {
    "claim_id": "c1",
    "estado": "REQUIERE_INVESTIGACION",
    "revision_humana": {"estado": "PENDIENTE"},
    "gate_arte": "CERRADO",
}

BASE_PIECE = {
    "schema_version": "4.0",
    "piece_id": "PIEZA-TEST",
    "claims": [BASE_CLAIM],
    "gate_global_arte": "CERRADO",
}


class TestCheckPilotGovernance(unittest.TestCase):
    def test_pieza_conforme_sin_problemas(self):
        self.assertEqual(check_pilot_governance(copy.deepcopy(BASE_PIECE)), [])

    def test_schema_version_incorrecta(self):
        piece = copy.deepcopy(BASE_PIECE)
        piece["schema_version"] = "3.0"
        problems = check_pilot_governance(piece)
        self.assertTrue(any("schema_version" in p for p in problems))

    def test_gate_global_abierto_rechazado(self):
        piece = copy.deepcopy(BASE_PIECE)
        piece["gate_global_arte"] = "ABIERTO"
        problems = check_pilot_governance(piece)
        self.assertTrue(any("gate_global_arte" in p for p in problems))

    def test_revision_humana_aprobada_rechazada_en_piloto(self):
        piece = copy.deepcopy(BASE_PIECE)
        piece["claims"][0]["revision_humana"]["estado"] = "APROBADO"
        problems = check_pilot_governance(piece)
        self.assertTrue(any("revision_humana.estado" in p for p in problems))

    def test_gate_arte_de_claim_abierto_rechazado(self):
        piece = copy.deepcopy(BASE_PIECE)
        piece["claims"][0]["gate_arte"] = "ABIERTO"
        problems = check_pilot_governance(piece)
        self.assertTrue(any("gate_arte" in p for p in problems))

    def test_cli_exit_0_para_pieza_conforme(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "pieza.json"
            path.write_text(json.dumps(BASE_PIECE), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(path)],
                capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_cli_exit_1_para_gate_abierto(self):
        with tempfile.TemporaryDirectory() as tmp:
            piece = copy.deepcopy(BASE_PIECE)
            piece["gate_global_arte"] = "ABIERTO"
            path = Path(tmp) / "pieza.json"
            path.write_text(json.dumps(piece), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(path)],
                capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 1)

    def test_cli_exit_1_sin_argumentos(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT)],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 1)

    def test_cli_exit_1_para_json_invalido(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "roto.json"
            path.write_text("{not json", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(path)],
                capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 1)


if __name__ == "__main__":
    unittest.main()
