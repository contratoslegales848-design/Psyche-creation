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

import command_center  # noqa: E402
import inventory  # noqa: E402
import resolver  # noqa: E402
import review_semantics  # noqa: E402


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
            # Ambas piezas: investigacion realmente intentada y bloqueada por
            # acceso a fuentes (confirmado en esta sesion via WebFetch/curl) —
            # sigue siendo trabajo de SISTEMA, nunca escala a HUMAN por si solo.
            self.assertEqual(r.next_executable_action, inventory.ACTION_BLOCKED_BY_SOURCE_ACCESS)
            self.assertEqual(r.owner, inventory.OWNER_SYSTEM)

    def test_pieza01_lee_el_puntero_persistente_vigente(self):
        """review-packet.json (ya corregido) debe reflejar la generacion mas
        reciente, no una generacion anterior stale."""
        filas = {r.piece_id: r for r in inventory.build_readiness()}
        r = filas["PIEZA-01-REALES"]
        self.assertEqual(r.handoff_state, "HANDOFF_EMITIDO")
        self.assertEqual(r.latest_generation_id, "gen-2f2dfb9c6f2f")

    def test_pieza01_con_fakeprovider_no_es_decision_artistica_urgente(self):
        """El punto central del mandato de continuacion: GEN3 usa
        FakeImageProvider, asi que no debe presentarse como si hubiera arte
        real esperando juicio humano."""
        filas = {r.piece_id: r for r in inventory.build_readiness()}
        r = filas["PIEZA-01-REALES"]
        self.assertTrue(r.provider_is_simulated)
        self.assertEqual(r.human_art_review, review_semantics.NOT_ACTIONABLE_UNTIL_REAL_PROVIDER)
        self.assertEqual(r.next_executable_action, inventory.ACTION_WAIT_REAL_PROVIDER)
        self.assertEqual(r.mechanical_qa, "PASS")  # la mecanica SI esta probada.

    def test_inbox_no_incluye_visual_review_para_fakeprovider(self):
        """No se gasta una decision humana en juzgar un placeholder."""
        items = inventory.build_inbox()
        visuales = [i for i in items if i.decision_type == inventory.DECISION_VISUAL_REVIEW]
        self.assertEqual(visuales, [])
        negocio = [i for i in items if i.decision_type == inventory.DECISION_BUSINESS_COST]
        self.assertEqual({i.piece_id for i in negocio}, {"PIEZA-01-REALES"})

    def test_inbox_no_incluye_legal_review_mientras_es_trabajo_de_sistema(self):
        """Punto central del mandato de continuacion V4: mientras la
        investigacion sea trabajo de SISTEMA (VERIFY_SOURCES o
        BLOCKED_BY_SOURCE_ACCESS), NO debe aparecer como decision humana."""
        items = inventory.build_inbox()
        legales = {i.piece_id for i in items if i.decision_type == inventory.DECISION_LEGAL_REVIEW}
        self.assertEqual(legales, set())

    def test_system_queue_incluye_piezas_bloqueadas_por_acceso(self):
        cola = {r.piece_id for r in inventory.system_executable_queue()}
        self.assertEqual({"PIEZA-02-LABORAL", "PIEZA-03-HONOR"} & cola,
                          {"PIEZA-02-LABORAL", "PIEZA-03-HONOR"})

    def test_next_nunca_propone_una_pieza_con_gate_cerrado_antes_que_una_abierta(self):
        filas = inventory.build_readiness()
        abiertas = [r for r in filas if r.art_gate == "ABIERTO"]
        cerradas = [r for r in filas if r.art_gate != "ABIERTO"]
        for a in abiertas:
            for c in cerradas:
                self.assertLess(len(a.blockers), len(c.blockers))

    def test_executable_now_no_incluye_piezas_cerradas(self):
        """El motor 'next' nunca abre gates: solo observa lo ya autorizado."""
        ejecutables = inventory.executable_now()
        self.assertNotIn("PIEZA-02-LABORAL", {r.piece_id for r in ejecutables})
        self.assertNotIn("PIEZA-03-HONOR", {r.piece_id for r in ejecutables})

    def test_command_center_payload_no_recalcula_autoridad(self):
        """El campo art_gate del payload es una lectura, nunca una re-derivacion:
        debe coincidir exactamente con resolver.gate_summary()."""
        real = {f["PIECE_ID"]: f["ART_GATE"] for f in resolver.gate_summary()}
        for fila in inventory.command_center_payload():
            if fila["piece_id"]:
                self.assertEqual(fila["art_gate"], real[fila["piece_id"]])


class TestReviewSemantics(unittest.TestCase):
    def test_fake_provider_nunca_es_actionable(self):
        c = review_semantics.classify({"provider": "fake (SIMULATED)", "human_visual_review_state": "PENDIENTE"})
        self.assertTrue(c.provider_is_simulated)
        self.assertEqual(c.human_art_review, review_semantics.NOT_ACTIONABLE_UNTIL_REAL_PROVIDER)

    def test_provider_real_conserva_el_estado_crudo(self):
        c = review_semantics.classify({"provider": "generic-http-image-v1", "human_visual_review_state": "PENDIENTE"})
        self.assertFalse(c.provider_is_simulated)
        self.assertEqual(c.human_art_review, "PENDIENTE")

    def test_ausencia_de_qa_nunca_se_convierte_en_pass(self):
        c = review_semantics.classify({"provider": "x"})
        self.assertEqual(c.mechanical_qa, review_semantics.NOT_AVAILABLE)
        self.assertEqual(c.copy_qa, review_semantics.NOT_AVAILABLE)

    def test_paquete_ausente_no_revienta(self):
        c = review_semantics.classify(None)
        self.assertEqual(c.human_art_review, review_semantics.NOT_ACTIONABLE_UNTIL_REAL_PROVIDER)


class TestCommandCenterContract(unittest.TestCase):
    def test_envelope_real_es_valido(self):
        env = command_center.build_envelope()
        self.assertEqual(command_center.validate_envelope(env), [])

    def test_version_desconocida_falla_cerrado(self):
        env = command_center.build_envelope()
        env["contract_version"] = "99.0"
        errores = command_center.validate_envelope(env)
        self.assertTrue(errores)
        self.assertIn("desconocida", errores[0])

    def test_content_ausente_se_reporta(self):
        errores = command_center.validate_envelope({"contract_version": command_center.CONTRACT_VERSION})
        self.assertTrue(any("content" in e for e in errores))

    def test_intento_de_escalada_de_autoridad_se_rechaza(self):
        malicioso = {
            "contract_version": command_center.CONTRACT_VERSION,
            "content": [{"content_id": "X", "human_art_review": "APPROVE_VISUAL",
                         "publication_state": "PUBLICADO"}],
            "human_decision_inbox": [],
        }
        errores = command_center.validate_envelope(malicioso)
        self.assertTrue(any("escalada de autoridad" in e for e in errores))

    def test_simulado_nunca_se_marca_live(self):
        env = command_center.build_envelope()
        for fila in env["content"]:
            if fila.get("provider_is_simulated"):
                self.assertEqual(fila["data_freshness"], command_center.FRESHNESS_SIMULATED)
                self.assertNotEqual(fila["data_freshness"], command_center.FRESHNESS_LIVE)


class TestRedTeamInventario(unittest.TestCase):
    """Bordes deliberados: inbox vacio, pieza sin generacion, puntero stale,
    contrato con version desconocida, escalada de autoridad."""

    def test_inbox_vacio_no_es_error(self):
        vacio = inventory.build_inbox(readiness=[])
        self.assertEqual(vacio, [])

    def test_pieza_sin_ninguna_generacion_no_revienta(self):
        r = inventory.ContentReadinessRecord(
            piece_id="PIEZA-X", canonical_state="APTO_PARA_NARRATIVA", art_gate="ABIERTO")
        r.handoff_state = "HANDOFF_EMITIDO"
        clasif = review_semantics.classify(None)
        r.human_art_review = clasif.human_art_review
        r.provider_is_simulated = clasif.provider_is_simulated
        r.next_action = inventory._next_action_para(r.art_gate, r.handoff_state, r.canonical_state, clasif)
        items = inventory.build_inbox(readiness=[r])
        # sin generacion real, clasif ya es NOT_ACTIONABLE (paquete None -> simulado por defecto):
        # la unica fila real es de negocio/costo, nunca una revision visual de la nada.
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].decision_type, inventory.DECISION_BUSINESS_COST)

    def test_pieza_con_arte_real_pendiente_si_genera_visual_review(self):
        """Contraste: con proveedor NO simulado, la fila VISUAL_REVIEW si debe aparecer."""
        r = inventory.ContentReadinessRecord(
            piece_id="PIEZA-Y", canonical_state="APTO_PARA_NARRATIVA", art_gate="ABIERTO")
        r.handoff_state = "HANDOFF_EMITIDO"
        clasif = review_semantics.classify({"provider": "generic-http-image-v1",
                                             "human_visual_review_state": "PENDIENTE"})
        r.human_art_review = clasif.human_art_review
        r.provider_is_simulated = clasif.provider_is_simulated
        items = inventory.build_inbox(readiness=[r])
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].decision_type, inventory.DECISION_VISUAL_REVIEW)

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

    def test_pieza02_no_puede_entrar_a_generacion_visual(self):
        """Ataque #15 del red-team pedido: PIEZA-02 (gate cerrado) intentando
        colarse en generacion visual debe seguir cerrada por gates.py real."""
        import gates
        art = json.loads((resolver.REPO / "content" / "pieza-01-reales.json").read_text())
        proc = dict(art["procedencia"])
        proc["piece_id"] = "PIEZA-02-LABORAL"  # intento de suplantacion
        proc["content_id"] = "LM-PIEZA-02-FALSIFICADA"
        proc["handoff_id"] = ""  # PIEZA-02 no tiene handoff real
        decision = gates.can_enter_visual_generation(proc, handoff=None)
        self.assertFalse(decision.permitido)


if __name__ == "__main__":
    unittest.main()
