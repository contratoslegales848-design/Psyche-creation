"""Inventario real y bandeja de decisiones humanas.

Contra el canon real del repo (como test_resolver.py) mas un mini red-team con
fixtures aislados para los bordes que el canon real no expone hoy.
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import inventory  # noqa: E402
import resolver  # noqa: E402


class TestInventarioReal(unittest.TestCase):
    """Contra el canon real: PIEZA-01-REALES abierta, 02 y 03 cerradas."""

    def test_las_tres_piezas_del_piloto_aparecen(self):
        filas = inventory.build_readiness()
        self.assertEqual({r.piece_id for r in filas},
                          {"PIEZA-01-REALES", "PIEZA-02-LABORAL", "PIEZA-03-HONOR"})

    def test_piezas_requieren_investigacion_bloquean_por_esa_razon(self):
        filas = {r.piece_id: r for r in inventory.build_readiness()}
        for pid in ("PIEZA-02-LABORAL", "PIEZA-03-HONOR"):
            r = filas[pid]
            self.assertEqual(r.canonical_state, "REQUIERE_INVESTIGACION")
            self.assertTrue(any("REQUIERE_INVESTIGACION" in b for b in r.blockers))
            self.assertEqual(r.handoff_state, "SIN_HANDOFF")

    def test_pieza01_lee_el_puntero_persistente_vigente(self):
        """review-packet.json (ya corregido) debe reflejar la generacion mas
        reciente, no una generacion anterior stale."""
        filas = {r.piece_id: r for r in inventory.build_readiness()}
        r = filas["PIEZA-01-REALES"]
        self.assertEqual(r.handoff_state, "HANDOFF_EMITIDO")
        self.assertEqual(r.latest_generation_id, "gen-2f2dfb9c6f2f")
        self.assertEqual(r.human_visual_review_state, "PENDIENTE")

    def test_inbox_incluye_visual_review_pendiente_de_pieza01(self):
        items = inventory.build_inbox()
        visuales = [i for i in items if i.decision_type == inventory.DECISION_VISUAL_REVIEW]
        self.assertEqual(len(visuales), 1)
        self.assertEqual(visuales[0].piece_id, "PIEZA-01-REALES")

    def test_inbox_incluye_legal_review_para_piezas_cerradas(self):
        items = inventory.build_inbox()
        legales = {i.piece_id for i in items if i.decision_type == inventory.DECISION_LEGAL_REVIEW}
        self.assertEqual(legales, {"PIEZA-02-LABORAL", "PIEZA-03-HONOR"})

    def test_next_nunca_propone_una_pieza_con_gate_cerrado_antes_que_una_abierta(self):
        filas = inventory.build_readiness()
        abiertas = [r for r in filas if r.art_gate == "ABIERTO"]
        cerradas = [r for r in filas if r.art_gate != "ABIERTO"]
        # Todas las abiertas tienen menos (o igual) bloqueos que cualquier cerrada,
        # porque el gate cerrado siempre se registra como bloqueo.
        for a in abiertas:
            for c in cerradas:
                self.assertLess(len(a.blockers), len(c.blockers))

    def test_command_center_payload_no_recalcula_autoridad(self):
        """El campo art_gate del payload es una lectura, nunca una re-derivacion:
        debe coincidir exactamente con resolver.gate_summary()."""
        real = {f["PIECE_ID"]: f["ART_GATE"] for f in resolver.gate_summary()}
        for fila in inventory.command_center_payload():
            if fila["piece_id"]:
                self.assertEqual(fila["art_gate"], real[fila["piece_id"]])


class TestRedTeamInventario(unittest.TestCase):
    """Bordes deliberados: inbox vacio, pieza sin generacion, puntero stale."""

    def test_inbox_vacio_no_es_error(self):
        vacio = inventory.build_inbox(readiness=[])
        self.assertEqual(vacio, [])

    def test_pieza_sin_ninguna_generacion_no_revienta(self):
        r = inventory.ContentReadinessRecord(
            piece_id="PIEZA-X", canonical_state="APTO_PARA_NARRATIVA", art_gate="ABIERTO")
        r.handoff_state = "HANDOFF_EMITIDO"
        r.next_action = inventory._next_action_para(r.art_gate, r.handoff_state,
                                                      r.human_visual_review_state, r.canonical_state)
        items = inventory.build_inbox(readiness=[r])
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].decision_type, inventory.DECISION_VISUAL_REVIEW)
        self.assertIn("(ninguna)", items[0].detail)

    def test_puntero_stale_no_engana_al_inventario_una_vez_corregido(self):
        """Si review-packet.json volviera a apuntar a una generacion vieja, el
        inventario reportaria esa generacion vieja como si fuera la vigente:
        no hay forma de detectar staleness sin una fuente independiente de
        'cual es realmente la ultima generacion' (el registro persistente que
        todavia no existe). Este test fija ese comportamiento honesto: el
        inventario CONFIA en el puntero, no lo adivina."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            content_dir = root / "content"
            content_dir.mkdir()
            (content_dir / "pieza-x.json").write_text(json.dumps({
                "procedencia": {"content_id": "LM-PIEZA-X", "piece_id": "PIEZA-X", "modo": "GOBERNADO"}
            }), encoding="utf-8")

            original_repo = inventory.resolver.REPO
            original_content_dir = inventory.resolver.CONTENT_DIR
            original_hr = inventory.HUMAN_REVIEW_DIR
            try:
                inventory.resolver.REPO = root
                inventory.resolver.CONTENT_DIR = content_dir
                inventory.HUMAN_REVIEW_DIR = root / "artifacts" / "human-review"
                hr_dir = inventory.HUMAN_REVIEW_DIR / "LM-PIEZA-X"
                hr_dir.mkdir(parents=True)
                (hr_dir / "review-packet.json").write_text(json.dumps({
                    "generation_id": "gen-viejo", "human_visual_review_state": "APPROVE_VISUAL",
                    "provider": "fake (SIMULATED)",
                }), encoding="utf-8")

                paquete = inventory._review_packet_para("LM-PIEZA-X")
                self.assertEqual(paquete["generation_id"], "gen-viejo")
                self.assertEqual(paquete["human_visual_review_state"], "APPROVE_VISUAL")
            finally:
                inventory.resolver.REPO = original_repo
                inventory.resolver.CONTENT_DIR = original_content_dir
                inventory.HUMAN_REVIEW_DIR = original_hr


if __name__ == "__main__":
    unittest.main()
