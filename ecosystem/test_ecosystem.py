"""Pruebas del ecosistema: estado real + inyeccion de fallos.

Dos mitades deliberadas. La primera fija lo que HOY es cierto del repositorio
(y fallara si alguien lo cambia sin actualizar el registro). La segunda inyecta
fallos a proposito para comprobar que el validador los atrapa en lugar de
aprobar en silencio, que es la regla del prompt de integracion §11.
"""

import sys
import unittest
from dataclasses import replace
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ecosystem import gate_matrix, help_protocols, registry, relations, validate  # noqa: E402


class TestRegistroReal(unittest.TestCase):
    """Contra el repositorio real, no contra fixtures."""

    def test_el_registro_real_no_tiene_hallazgos(self):
        hallazgos = validate.validate()
        self.assertEqual(
            [f"{f.severity} {f.code} {f.object_id}: {f.detail}" for f in hallazgos], [])

    def test_ningun_objeto_declarado_esta_ausente(self):
        """Deriva documental: declarar que algo existe y que no exista."""
        self.assertEqual([o.object_id for o in registry.drifted()], [])

    def test_los_paquetes_nombrados_sin_artefacto_estan_registrados_como_tales(self):
        """El hallazgo central: seis paquetes del §1 no existen.

        No se inventan ni se dan por implementados. Si alguno aparece de
        verdad en el futuro, esta prueba obliga a actualizar el registro."""
        faltantes = {
            o.object_id for o in registry.ALL_OBJECTS
            if o.resolve_state() == registry.MISSING_ARTIFACT
        }
        for esperado in ("MIS-VISUAL-FACTORY", "MIS-EXPANSION-LAB",
                         "MIS-COMMERCIAL-OPS", "MIS-LC1-RELEASE",
                         "MIS-PUBLIC-CLOSURE", "MIS-DEMAND-INTEL",
                         "MIS-LINKEDIN-BANK", "MIS-GOLD-STANDARD"):
            self.assertIn(esperado, faltantes)

    def test_un_objeto_ausente_jamas_se_promueve(self):
        """resolve_state() puede degradar, nunca ascender."""
        for obj in registry.ALL_OBJECTS:
            if obj.declared_state in registry.TERMINAL_ABSENT_STATES:
                self.assertEqual(obj.resolve_state(), obj.declared_state)

    def test_la_rama_atrasada_se_declara_en_lugar_de_confundirse(self):
        """No es lo mismo 'nunca se construyo' que 'esta rama va atrasada'.

        PIEZA-04 y la direccion de contenido existen y estan fusionadas en main;
        aqui no. Registrarlas como MISSING_ARTIFACT borraria esa diferencia y
        haria creer que el proyecto no las tiene."""
        atrasados = {
            o.object_id for o in registry.ALL_OBJECTS
            if o.resolve_state() == registry.ABSENT_ON_THIS_BRANCH
        }
        self.assertEqual(atrasados, {"PSY-EVID-PACKET-04", "PSY-NAV-DIRECCION"})
        for oid in atrasados:
            self.assertIn("ECO-BLK-STALE-BRANCH", registry.by_id(oid).blockers)

    def test_el_hueco_entrada_evidencia_esta_declarado(self):
        """El hueco de integracion mas importante debe ser visible, no implicito."""
        enlaces = relations.ecosystem_links()
        hueco = [
            l for l in enlaces
            if l["source"] == "WEB-NAV-KNOWLEDGE-GRAPH"
            and l["target"] == "PSY-EVID-SKILL-VERIF"
        ]
        self.assertEqual(len(hueco), 1)
        self.assertEqual(hueco[0]["state"], relations.DISCONNECTED)

    def test_el_grafo_heredado_se_consume_de_verdad(self):
        """No se duplica topology.py: se lee en vivo."""
        heredados = relations.inherited_topology()
        self.assertGreater(len(heredados), 5)
        fuentes = {l["source"] for l in heredados}
        self.assertIn("psyche_canon", fuentes)

    def test_hay_huecos_de_integracion_declarados(self):
        self.assertGreater(len(relations.integration_gaps()), 0)


class TestGates(unittest.TestCase):
    def test_ningun_gate_automatico_autoriza_publicar(self):
        self.assertEqual(gate_matrix.chaining_violations(), ())

    def test_existe_al_menos_un_gate_humano(self):
        self.assertGreater(len(gate_matrix.human_gates()), 0)

    def test_la_autorizacion_de_publicacion_no_esta_implementada_en_codigo(self):
        """Es una regla, no una carencia: ningun codigo debe poder publicar."""
        gate = next(g for g in gate_matrix.GATE_MATRIX
                    if g.gate_id == "GATE-PUBLICATION-HUMAN")
        self.assertFalse(gate.exists)
        self.assertEqual(gate.decided_by, gate_matrix.HUMAN)

    def test_todos_los_gates_son_fail_closed(self):
        for gate in gate_matrix.GATE_MATRIX:
            self.assertTrue(gate.fail_closed, gate.gate_id)


class TestProtocolosDeAyuda(unittest.TestCase):
    def test_los_cinco_protocolos_existen(self):
        ids = {p.protocol_id for p in help_protocols.HELP_PROTOCOLS}
        self.assertEqual(ids, {"HELP-001", "HELP-002", "HELP-003", "HELP-004", "HELP-005"})

    def test_todos_tienen_condicion_de_parada(self):
        self.assertEqual(help_protocols.protocols_without_stop_condition(), ())

    def test_ninguno_lleva_claim_ni_copy_exacto(self):
        """Un protocolo con claim exigiria fuente, territorio y vigencia."""
        self.assertEqual(help_protocols.protocols_bearing_claims(), ())

    def test_todos_nacen_propuestos(self):
        for protocol in help_protocols.HELP_PROTOCOLS:
            self.assertEqual(protocol.state, help_protocols.PROPOSED)


class TestInyeccionDeFallos(unittest.TestCase):
    """§11: cada fallo debe terminar en HOLD, REJECT, FIX_REQUIRED o
    REVIEW_REQUIRED. Nunca en una aprobacion silenciosa."""

    def _base(self):
        return registry.EcosystemObject(
            object_id="TEST-OBJ", label="objeto de prueba",
            layer=registry.LAYER_EVIDENCE, repo=registry.REPO_PSYCHE,
            path="CLAUDE.md", declared_state=registry.CANONICAL,
            owner="fundador", next_action="ninguna",
        )

    def _codigos(self, objetos):
        return {f.code for f in validate.validate(objetos)}

    def test_objeto_declarado_pero_ausente_produce_hold(self):
        roto = replace(self._base(), path="docs/ARCHIVO-QUE-NO-EXISTE.md")
        hallazgos = validate.validate([roto])
        drift = [f for f in hallazgos if f.code == "DECLARED_BUT_ABSENT"]
        self.assertEqual(len(drift), 1)
        self.assertEqual(drift[0].severity, validate.HOLD)

    def test_id_duplicado_produce_reject(self):
        base = self._base()
        hallazgos = validate.validate([base, base])
        dup = [f for f in hallazgos if f.code == "DUPLICATE_OBJECT_ID"]
        self.assertEqual(len(dup), 1)
        self.assertEqual(dup[0].severity, validate.REJECT)

    def test_owner_ausente_produce_fix_required(self):
        sin_owner = replace(self._base(), owner="   ")
        hallazgos = [f for f in validate.validate([sin_owner]) if f.code == "MISSING_OWNER"]
        self.assertEqual(len(hallazgos), 1)
        self.assertEqual(hallazgos[0].severity, validate.FIX_REQUIRED)

    def test_siguiente_accion_ausente_produce_fix_required(self):
        sin_accion = replace(self._base(), next_action="")
        self.assertIn("MISSING_NEXT_ACTION", self._codigos([sin_accion]))

    def test_estado_fuera_del_vocabulario_produce_reject(self):
        inventado = replace(self._base(), declared_state="APROBADO_POR_LA_IA")
        hallazgos = [f for f in validate.validate([inventado]) if f.code == "UNKNOWN_STATE"]
        self.assertEqual(len(hallazgos), 1)
        self.assertEqual(hallazgos[0].severity, validate.REJECT)

    def test_capa_inventada_produce_reject(self):
        self.assertIn("UNKNOWN_LAYER", self._codigos([replace(self._base(), layer="marketing")]))

    def test_token_de_publicacion_produce_reject(self):
        """El fallo mas peligroso: un flag de publicacion activado por error."""
        peligroso = replace(self._base(), notes="listo, PUBLICATION_AUTHORIZED")
        hallazgos = [f for f in validate.validate([peligroso])
                     if f.code == "FORBIDDEN_PUBLICATION_TOKEN"]
        self.assertEqual(len(hallazgos), 1)
        self.assertEqual(hallazgos[0].severity, validate.REJECT)

    def test_canonical_con_bloqueos_pide_revision(self):
        bloqueado = replace(self._base(), object_id="TEST-BLOQ",
                            blockers=("ECO-BLK-ALGO",))
        hallazgos = [f for f in validate.validate([bloqueado])
                     if f.code == "BLOCKED_YET_CANONICAL"]
        self.assertEqual(len(hallazgos), 1)
        self.assertEqual(hallazgos[0].severity, validate.REVIEW_REQUIRED)

    def test_protocolo_sin_parada_produce_reject(self):
        roto = replace(help_protocols.HELP_PROTOCOLS[0], stop_conditions=())
        with mock.patch.object(help_protocols, "HELP_PROTOCOLS", (roto,)):
            hallazgos = [f for f in validate.validate() if f.code == "HELP_WITHOUT_STOP"]
            self.assertEqual(len(hallazgos), 1)
            self.assertEqual(hallazgos[0].severity, validate.REJECT)

    def test_protocolo_con_claim_produce_hold(self):
        con_claim = replace(help_protocols.HELP_PROTOCOLS[0], claim_ids=("claim-x",))
        with mock.patch.object(help_protocols, "HELP_PROTOCOLS", (con_claim,)):
            hallazgos = [f for f in validate.validate() if f.code == "HELP_BEARS_CLAIM"]
            self.assertEqual(len(hallazgos), 1)
            self.assertEqual(hallazgos[0].severity, validate.HOLD)

    def test_gate_automatico_que_publica_produce_reject(self):
        malicioso = gate_matrix.Gate(
            gate_id="GATE-MALO", label="atajo", implemented_in="ninguno",
            decided_by=gate_matrix.AUTOMATIC, authorizes="Publicar.",
            does_not_authorize="", fail_closed=True, exists=False)
        with mock.patch.object(gate_matrix, "GATE_MATRIX",
                               gate_matrix.GATE_MATRIX + (malicioso,)):
            hallazgos = [f for f in validate.validate() if f.code == "GATE_CHAINING"]
            self.assertTrue(hallazgos)
            self.assertEqual(hallazgos[0].severity, validate.REJECT)

    def test_relacion_colgante_produce_fix_required(self):
        colgante = [{"source": "NO-EXISTE-A", "target": "NO-EXISTE-B",
                     "state": relations.CONNECTED, "reason": "inventada"}]
        with mock.patch.object(relations, "ecosystem_links", return_value=colgante):
            hallazgos = [f for f in validate.validate() if f.code == "DANGLING_RELATION"]
            self.assertEqual(len(hallazgos), 2)
            self.assertEqual(hallazgos[0].severity, validate.FIX_REQUIRED)

    def test_ningun_hallazgo_usa_una_severidad_inventada(self):
        roto = replace(self._base(), path="no-existe", owner="", declared_state="RARO")
        for finding in validate.validate([roto]):
            self.assertIn(finding.severity, validate.SEVERITIES)


class TestResumen(unittest.TestCase):
    def test_el_resumen_declara_not_published(self):
        self.assertEqual(validate.summary()["estado_publicacion"], "NOT_PUBLISHED")

    def test_el_resumen_cuenta_objetos_reales(self):
        resumen = validate.summary()
        self.assertEqual(resumen["objetos_totales"], len(registry.ALL_OBJECTS))
        self.assertEqual(resumen["hallazgos"], 0)


if __name__ == "__main__":
    unittest.main()
