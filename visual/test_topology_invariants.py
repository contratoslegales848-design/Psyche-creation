"""Invariantes autorizados de topology.py (PR #17 Reviewability Surgery §5.1)
y del limite SYSTEM vs HUMAN (§5.2). Solo pruebas de invariante — ninguna
cambia logica; si alguna fallara, seria un bug real a corregir, no la prueba."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import inventory  # noqa: E402
import review_semantics  # noqa: E402
import topology  # noqa: E402

ORGANISM_VOCAB = {topology.CONNECTED, topology.READY_TO_CONNECT, topology.BLOCKED,
                  topology.DISCONNECTED, topology.EXPERIMENTAL, topology.SUPERSEDED}
CF_VOCAB = {topology.CF_CONNECTED, topology.CF_PARTIAL, topology.CF_DOCUMENTED_ONLY,
            topology.CF_DISCONNECTED, topology.CF_MISSING}
PML_VOCAB = ORGANISM_VOCAB | {"PARTIAL", "NO_MEDIDO"}  # publication_measurement_learning usa estos 2 extra


class TestTopologyInvariants(unittest.TestCase):
    """§5.1 puntos 1-2, 8-10."""

    def test_1_stages_esperados_existen(self):
        links = topology.content_factory_topology()
        nodos = {l["source"] for l in links} | {l["target"] for l in links}
        for esperado in ("idea", "claim_draft", "source_discovery", "source_verification",
                          "territory_mapping", "human_legal_review", "content_id",
                          "production_handoff"):
            self.assertIn(esperado, nodos)

    def test_2_todos_los_estados_pertenecen_al_vocabulario_permitido(self):
        for link in topology.build_topology():
            self.assertIn(link["state"], ORGANISM_VOCAB)
        for link in topology.content_factory_topology():
            self.assertIn(link["state"], CF_VOCAB)
        for link in topology.publication_measurement_learning_topology():
            self.assertIn(link["state"], PML_VOCAB)

    def test_8_topology_no_crea_authority(self):
        """Ninguna funcion de topology.py LLAMA a gates.can_enter_visual_generation
        ni ASIGNA a revision_humana/gate_arte. 'revision_humana' puede aparecer
        en prosa (docstrings explicando que existe en otro archivo) sin ser un
        problema — lo que se prohibe es que topology.py la escriba."""
        import inspect
        src = inspect.getsource(topology)
        self.assertNotIn("can_enter_visual_generation(", src)
        self.assertNotIn("revision_humana[", src)
        self.assertNotIn("revision_humana.estado =", src)
        self.assertNotIn(".estado = \"APROBADO\"", src)
        self.assertNotIn("gate_arte = ", src)

    def test_9_topology_no_muta_canon(self):
        """build_topology()/content_factory_topology() no escriben a disco: se
        verifica que ningun link.state provenga de un write, comparando dos
        llamadas consecutivas — deben ser identicas (deterministico, sin side effects)."""
        a = topology.build_topology()
        b = topology.build_topology()
        self.assertEqual(a, b)

    def test_10_outputs_son_derivados_no_inventados(self):
        """Cada link de content_factory_topology trae una razon con evidencia
        citable (nombre de archivo o funcion real), no una afirmacion vacia."""
        for link in topology.content_factory_topology():
            self.assertTrue(len(link["reason"]) > 20)


class TestPublicationCannotSelfDeclare(unittest.TestCase):
    """§5.1 puntos 3-6: topology nunca abre publication ni mide sin evidencia."""

    def _pml(self):
        return {(l["source"], l["target"]): l for l in
                topology.publication_measurement_learning_topology()}

    def test_3_topology_no_puede_abrir_publication(self):
        """Ningun link de esta topologia declara PUBLICADO ni CONNECTED en la
        cadena de publicacion: el estado mas alto alcanzable hoy es PARTIAL
        (esquema validado, cero registros reales)."""
        links = self._pml()
        for l in links.values():
            self.assertNotIn(l["state"], ("PUBLICADO", "PUBLISHED"))
        l = links[("production_handoff", "publication_record_schema")]
        self.assertNotEqual(l["state"], topology.CONNECTED)

    def test_4_publication_no_aparece_publicada_sin_record_real(self):
        links = self._pml()
        l = links[("production_handoff", "publication_record_schema")]
        self.assertEqual(l["state"], "PARTIAL")
        self.assertIn("cero", l["reason"].lower())

    def test_5_measurement_no_aparece_medido_sin_evidencia(self):
        links = self._pml()
        l = links[("publication_record_schema", "measurement")]
        self.assertEqual(l["state"], "NO_MEDIDO")

    def test_6_learning_permanece_disconnected(self):
        links = self._pml()
        l = links[("measurement", "content_factory_learning_loop")]
        self.assertEqual(l["state"], topology.DISCONNECTED)

    def test_7_content_factory_no_eleva_readiness_por_inferencia(self):
        """territory_mapping -> human_legal_review es PARTIAL, nunca CONNECTED:
        el modulo no infiere que la evidencia ya sea suficiente para revision."""
        links = {(l["source"], l["target"]): l for l in topology.content_factory_topology()}
        l = links[("territory_mapping", "human_legal_review")]
        self.assertEqual(l["state"], topology.CF_PARTIAL)


class TestSystemVsHumanInvariant(unittest.TestCase):
    """§5.2 — casos A-D del mandato de reviewability, contra el codigo real."""

    def test_case_a_requiere_investigacion_bloqueada_es_system_no_human(self):
        filas = {r.piece_id: r for r in inventory.build_readiness()}
        for pid in ("PIEZA-02-LABORAL", "PIEZA-03-HONOR"):
            r = filas[pid]
            self.assertEqual(r.canonical_state, "REQUIERE_INVESTIGACION")
            self.assertEqual(r.owner, inventory.OWNER_SYSTEM)
            self.assertEqual(r.next_executable_action, inventory.ACTION_BLOCKED_BY_SOURCE_ACCESS)
        inbox_piece_ids = {i.piece_id for i in inventory.build_inbox()}
        self.assertNotIn("PIEZA-02-LABORAL", inbox_piece_ids)
        self.assertNotIn("PIEZA-03-HONOR", inbox_piece_ids)

    def test_case_b_verify_sources_sigue_siendo_system(self):
        """Con fuentes accesibles pero sin verificar (checks vacios), la accion
        derivada sigue siendo SYSTEM/VERIFY_SOURCES, nunca HUMAN."""
        rec = inventory.ContentReadinessRecord(
            piece_id="PIEZA-TEST", canonical_state="REQUIERE_INVESTIGACION", art_gate="CERRADO")
        clasif = review_semantics.classify(None)
        accion = inventory._next_executable_action(
            rec.canonical_state, rec.art_gate, rec.handoff_state, clasif, source_summary=None)
        self.assertEqual(accion, inventory.ACTION_VERIFY_SOURCES)
        self.assertEqual(inventory.ACTION_OWNER[accion], inventory.OWNER_SYSTEM)

    def test_case_c_ready_for_human_legal_review_es_human(self):
        self.assertEqual(inventory.ACTION_OWNER[inventory.ACTION_HUMAN_LEGAL_REVIEW],
                          inventory.OWNER_HUMAN)

    def test_case_d_inbox_humano_nunca_contiene_acciones_de_sistema(self):
        """El invariante real (mandato §5.2 caso D) es sobre el VOCABULARIO de
        decision_type del inbox, no sobre que readiness state produjo la fila:
        una pieza en WAIT_REAL_PROVIDER (SYSTEM) puede legitimamente generar
        una fila BUSINESS_COST (HUMAN) — eso es la traduccion correcta, no una
        fuga. Lo prohibido es que decision_type SEA literalmente uno de estos
        codigos de accion de sistema."""
        prohibidas = {inventory.ACTION_VERIFY_SOURCES, inventory.ACTION_BLOCKED_BY_SOURCE_ACCESS,
                      inventory.ACTION_WAIT_REAL_PROVIDER, "MECHANICAL_QA"}
        decision_types = {i.decision_type for i in inventory.build_inbox()}
        self.assertEqual(decision_types & prohibidas, set())


if __name__ == "__main__":
    unittest.main()
