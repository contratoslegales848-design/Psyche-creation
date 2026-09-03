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

from ecosystem import (  # noqa: E402
    drive_evidence, gate_matrix, help_protocols, registry, relations, validate,
)


class TestRegistroReal(unittest.TestCase):
    """Contra el repositorio real, no contra fixtures."""

    def test_el_registro_real_no_tiene_hallazgos(self):
        hallazgos = validate.validate()
        self.assertEqual(
            [f"{f.severity} {f.code} {f.object_id}: {f.detail}" for f in hallazgos], [])

    def test_ningun_objeto_declarado_esta_ausente(self):
        """Deriva documental: declarar que algo existe y que no exista."""
        self.assertEqual([o.object_id for o in registry.drifted()], [])

    def test_los_paquetes_auxiliares_si_existen_en_drive(self):
        """CORRECCION de la sesion anterior.

        Se habian declarado MISSING_ARTIFACT tras buscarlos solo con greps
        sobre los repositorios. La busqueda en Drive del 2026-09-03 los
        encontro todos. Esta prueba fija la correccion para que nadie vuelva
        a concluir inexistencia sin haber buscado donde el objeto vive."""
        encontrados = {
            o.object_id for o in registry.ALL_OBJECTS
            if o.resolve_state() == registry.FOUND_AUXILIARY
        }
        for esperado in ("MIS-CONTENT-FACTORY", "MIS-VISUAL-FACTORY",
                         "MIS-EXPANSION-LAB", "MIS-COMMERCIAL-OPS",
                         "MIS-LC1-RELEASE", "MIS-PUBLIC-CLOSURE",
                         "MIS-DEMAND-INTEL", "MIS-LINKEDIN-BANK"):
            self.assertIn(esperado, encontrados)

    def test_existencia_verificada_no_es_contenido_verificado(self):
        """Un ZIP localizado en Drive no es un paquete leido.

        Las instrucciones prohiben descargar o ejecutar artefactos externos de
        forma automatica, asi que todo paquete arrastra el bloqueo de contenido
        no leido en vez de darse por integrado."""
        for obj in registry.ALL_OBJECTS:
            if obj.resolve_state() == registry.FOUND_AUXILIARY:
                self.assertIn("ECO-BLK-DRIVE-CONTENT-UNREAD", obj.blockers,
                              f"{obj.object_id} se da por leido sin estarlo")

    def test_las_tres_fuentes_en_hold_siguen_ausentes_tras_buscarlas(self):
        """§8: no se convierten en verificadas, y la ausencia ya es documentada."""
        ausentes = {a.artifact_id for a in drive_evidence.sources_still_missing()}
        self.assertEqual(ausentes,
                         {"DRV-SRC-AR-LCT", "DRV-SRC-CO-CST", "DRV-SRC-ES-STS"})
        for artifact in drive_evidence.sources_still_missing():
            self.assertIsNone(artifact.drive_id)
            self.assertIn("2026-09-03", artifact.evidence)

    def test_los_protocolos_declaran_de_donde_derivan(self):
        """No puede haber dos objetos que representen lo mismo sin decirlo."""
        self.assertEqual(help_protocols.IDENTITY_RELATION, "DERIVED_FROM")
        origen = drive_evidence.by_id(help_protocols.IDENTITY_TARGET)
        self.assertIsNotNone(origen)
        self.assertEqual(origen.drive_id, help_protocols.IDENTITY_TARGET_DRIVE_ID)
        self.assertTrue(origen.content_verified(),
                        "el original debe haberse leido para poder afirmar el duplicado")

    def test_un_objeto_ausente_jamas_se_promueve(self):
        """resolve_state() puede degradar, nunca ascender."""
        for obj in registry.ALL_OBJECTS:
            if obj.declared_state in registry.TERMINAL_ABSENT_STATES:
                self.assertEqual(obj.resolve_state(), obj.declared_state)

    def test_ningun_objeto_existente_sigue_declarado_ausente(self):
        """Una ausencia no puede sobrevivir a la llegada del archivo.

        PIEZA-04 y la direccion de contenido estuvieron declaradas
        ABSENT_ON_THIS_BRANCH mientras la rama iba por detras de main. La
        convergencia las trajo al arbol, y una declaracion de ausencia que
        sobrevive a eso deja de describir el proyecto: lo contradice. Esta
        prueba falla si vuelve a ocurrir con cualquier objeto.
        """
        contradicciones = [
            o.object_id for o in registry.ALL_OBJECTS
            if o.resolve_state() == registry.STALE_ABSENCE_DECLARATION
        ]
        self.assertEqual(
            contradicciones, [],
            "estos objetos siguen declarados ausentes pero su archivo esta en "
            f"el arbol: {contradicciones}")

    def test_una_ausencia_declarada_nunca_se_promueve_sola_a_canonical(self):
        """El contrapeso de la prueba anterior.

        Corregir una declaracion obsoleta es trabajo de un humano. Si
        resolve_state() ascendiera sola a CANONICAL, el registro se habria
        convertido en una via para conceder estado canonico sin decision.
        """
        falso = replace(registry.ALL_OBJECTS[0],
                        object_id="TMP-STALE",
                        declared_state=registry.ABSENT_ON_THIS_BRANCH,
                        path="ecosystem/registry.py")
        self.assertEqual(falso.resolve_state(), registry.STALE_ABSENCE_DECLARATION)
        self.assertNotEqual(falso.resolve_state(), registry.CANONICAL)

    def test_una_ausencia_real_se_conserva_como_ausencia(self):
        """Y sigue distinguiendose de 'nunca se construyo'."""
        falso = replace(registry.ALL_OBJECTS[0],
                        object_id="TMP-ABSENT",
                        declared_state=registry.ABSENT_ON_THIS_BRANCH,
                        path="ecosystem/no-existe-en-ninguna-rama.py")
        self.assertEqual(falso.resolve_state(), registry.ABSENT_ON_THIS_BRANCH)
        self.assertNotEqual(falso.resolve_state(), registry.MISSING_ARTIFACT)

    def test_el_motor_de_rutas_esta_registrado(self):
        """Un componente no registrado es un componente que nadie echa de menos:
        el route engine llevaba tiempo fuera del registro, y esa invisibilidad
        es la misma que dejo sus pruebas fuera de CI."""
        ids = {o.object_id for o in registry.ALL_OBJECTS}
        for oid in ("PSY-NAV-ROUTE-ENGINE", "PSY-NAV-ROUTE-SYNC", "PSY-KNOW-TOPICS"):
            with self.subTest(objeto=oid):
                self.assertIn(oid, ids)
                self.assertEqual(registry.by_id(oid).resolve_state(), registry.CANONICAL)

    def test_el_hueco_entrada_evidencia_esta_declarado(self):
        """El hueco de integracion mas importante debe ser visible, no implicito."""
        enlaces = relations.ecosystem_links()
        hueco = [
            l for l in enlaces
            if l["source"] == "WEB-NAV-KNOWLEDGE-GRAPH"
            and l["target"] == "PSY-EVID-SKILL-VERIF"
        ]
        self.assertEqual(len(hueco), 1)
        # Parcialmente cerrado: existe contrato con vinculos verificados, pero
        # los concept_id aun se declaran a mano en vez de leerse del grafo web.
        self.assertEqual(hueco[0]["state"], relations.READY_TO_CONNECT)
        self.assertIn("CONCEPT -> CLAIM_ID", hueco[0]["reason"])

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
