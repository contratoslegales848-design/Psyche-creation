"""El reporte de bloqueo no puede convertirse en un atajo de publicacion.

La utilidad del reporte es decir por que un packet NO puede producir copy. El
riesgo es el contrario: que alguien lo lea como si autorizara algo. Estas
pruebas fijan que mientras el gate este cerrado, la lista de salidas permitidas
sea vacia, y que el reporte no invente motivos ni pierda claims por el camino.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import report_blocked_packets as rbp  # noqa: E402


class TestReporteDeBloqueo(unittest.TestCase):
    def setUp(self):
        self.reporte = rbp.analizar()

    def test_hay_claims_que_reportar(self):
        self.assertTrue(self.reporte, "no se encontro ningun claim packet")

    def test_ningun_claim_con_gate_cerrado_permite_salidas_de_autoridad(self):
        """El control central: gate cerrado => cero copy, cero prompt, cero handshake."""
        for r in self.reporte:
            if r["gate_global"] == "ABIERTO":
                continue
            with self.subTest(claim=r["claim_id"]):
                self.assertEqual(r["salidas_permitidas"], [])
                self.assertEqual(set(r["salidas_bloqueadas"]), set(rbp.SALIDAS_DE_AUTORIDAD))

    def test_todo_claim_bloqueado_declara_al_menos_un_motivo(self):
        """Un bloqueo sin motivo es indistinguible de un fallo del reporte."""
        for r in self.reporte:
            if not r["salidas_bloqueadas"]:
                continue
            with self.subTest(claim=r["claim_id"]):
                self.assertTrue(r["motivos_de_bloqueo"])

    def test_el_reporte_siempre_declara_not_published(self):
        for r in self.reporte:
            self.assertEqual(r["publicacion"], "NOT_PUBLISHED")

    def test_no_pierde_ni_duplica_claims(self):
        import json
        esperados = []
        for ruta in sorted(rbp.PACKETS_DIR.glob("*.json")):
            datos = json.loads(ruta.read_text(encoding="utf-8"))
            esperados.extend(c["claim_id"] for c in datos["claims"])
        reportados = [r["claim_id"] for r in self.reporte]
        self.assertEqual(sorted(reportados), sorted(esperados))
        self.assertEqual(len(reportados), len(set(reportados)))

    def test_una_revision_pendiente_siempre_aparece_como_motivo(self):
        for r in self.reporte:
            if r["gate_global"] == "ABIERTO":
                continue
            with self.subTest(claim=r["claim_id"]):
                self.assertTrue(any("revision humana" in m for m in r["motivos_de_bloqueo"]))

    def test_un_alcance_sin_determinar_se_reporta_como_motivo_propio(self):
        for r in self.reporte:
            if r["alcance"] != "NO_DETERMINADO":
                continue
            with self.subTest(claim=r["claim_id"]):
                self.assertTrue(any("alcance sin determinar" in m for m in r["motivos_de_bloqueo"]))

    def test_el_reporte_no_escribe_nada(self):
        """Es de solo lectura: analizar() no debe tocar los packets."""
        antes = {p: p.read_bytes() for p in rbp.PACKETS_DIR.glob("*.json")}
        rbp.analizar()
        for p, contenido in antes.items():
            self.assertEqual(p.read_bytes(), contenido, f"{p.name} fue modificado")


if __name__ == "__main__":
    unittest.main()
