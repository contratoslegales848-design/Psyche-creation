"""Pruebas del puente CONCEPT → CLAIM_ID.

Contra el canon real de `pilot/claim-packets/`, no contra fixtures inventadas,
y con los diez fallos que las instrucciones §6 exigen que fallen cerradamente.
Ningun fallo puede terminar en aprobacion silenciosa.
"""

import sys
import unittest
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ecosystem import concept_claim_bridge as bridge  # noqa: E402


def _binding(**overrides):
    """Vinculo base valido contra el canon real, para mutarlo en cada prueba."""
    base = bridge.ConceptClaimBinding(
        binding_id="TEST-BND",
        concept_id="everyday-life",
        concept_label="Vida cotidiana",
        human_question="¿Que distingue propiedad, posesion y tenencia?",
        claim_id="pieza-01-claim-1",
        packet_file="pieza-01-reales.json",
        declared_layer=bridge.CAPA_B,
        territories=("México", "España", "Argentina"),
        source_ids=("SRC-P01-MX-FED-02",),
        limits=("El detalle varia por pais.",),
        owner="fundador",
        next_action="ninguna",
    )
    return replace(base, **overrides)


class TestCanonReal(unittest.TestCase):
    def test_el_catalogo_lee_los_packets_reales(self):
        catalogo = bridge.available_claim_ids()
        self.assertIn("pieza-01-claim-1", catalogo)
        self.assertIn("pieza-02-claim-1", catalogo)
        # No se replica el canon: cada entrada apunta a su archivo real.
        self.assertEqual(catalogo["pieza-01-claim-1"]["packet_file"],
                         "pieza-01-reales.json")

    def test_un_vinculo_completo_y_aprobado_si_se_verifica(self):
        """Sin esto el contrato solo sabria decir que no. Debe saber decir que si."""
        decision = bridge.evaluate_binding(_binding())
        self.assertEqual(decision.state, bridge.VERIFIED_BINDING)

    def test_existe_al_menos_una_ruta_recorrible_de_punta_a_punta(self):
        """Criterio de finalizacion §10: pregunta -> concepto -> claim ->
        fuente -> territorio -> limite -> ayuda -> estado -> owner -> accion."""
        ruta = bridge.traversable_route("BND-002")
        self.assertIsNotNone(ruta)
        for eslabon in ("pregunta_humana", "concepto", "claim", "fuentes",
                        "territorio", "limites", "ayuda_permitida", "estado",
                        "owner", "siguiente_accion", "publicacion"):
            self.assertIn(eslabon, ruta)
            self.assertTrue(ruta[eslabon], f"eslabon vacio: {eslabon}")
        self.assertEqual(ruta["estado"], bridge.VERIFIED_BINDING)
        self.assertEqual(ruta["publicacion"], "NOT_PUBLISHED")

    def test_ninguna_decision_usa_un_estado_inventado(self):
        for decision in bridge.evaluate_all():
            self.assertIn(decision.state, bridge.BINDING_STATES)

    def test_ningun_vinculo_declara_publicacion(self):
        for binding in bridge.DECLARED_BINDINGS:
            self.assertEqual(binding.publication_state, "NOT_PUBLISHED")


class TestFallosObligatorios(unittest.TestCase):
    """Los diez casos del §6. Cada uno debe cerrar, nunca aprobar."""

    def _state(self, **overrides):
        return bridge.evaluate_binding(_binding(**overrides)).state

    def test_concept_id_ausente(self):
        self.assertEqual(self._state(concept_id="  "), bridge.REJECTED)

    def test_claim_id_ausente(self):
        self.assertEqual(self._state(claim_id=""), bridge.REJECTED)

    def test_claim_no_encontrado_en_el_canon_local(self):
        """Pendiente, no rechazado: el claim podria existir en otra rama."""
        decision = bridge.evaluate_binding(_binding(claim_id="pieza-99-claim-1"))
        self.assertEqual(decision.state, bridge.PENDING_BINDING)
        self.assertIn("no existe en el canon local", decision.reasons[0])

    def test_fuente_ausente_del_claim_real(self):
        """Una fuente inventada no puede colarse en un vinculo."""
        decision = bridge.evaluate_binding(_binding(source_ids=("SRC-NO-EXISTE",)))
        self.assertEqual(decision.state, bridge.REJECTED)
        self.assertIn("Fuentes ausentes", decision.reasons[0])

    def test_sin_ninguna_fuente_declarada(self):
        self.assertEqual(self._state(source_ids=()), bridge.REVIEW_REQUIRED)

    def test_territorio_ausente_en_un_claim_nacional(self):
        decision = bridge.evaluate_binding(_binding(
            claim_id="pieza-02-claim-1", packet_file="pieza-02-laboral.json",
            declared_layer=bridge.CAPA_C, territories=(),
            source_ids=(), limits=("x",)))
        self.assertEqual(decision.state, bridge.REJECTED)
        self.assertIn("exige territorio", decision.reasons[-1])

    def test_falsa_universalizacion(self):
        """Declarar transversal un claim nacional es el error mas caro."""
        decision = bridge.evaluate_binding(_binding(
            claim_id="pieza-02-claim-1", packet_file="pieza-02-laboral.json",
            declared_layer=bridge.CAPA_A))
        self.assertEqual(decision.state, bridge.REJECTED)
        self.assertIn("falsa universalización", decision.reasons[-1])

    def test_estado_de_verificacion_incompatible(self):
        """Un claim en REQUIERE_INVESTIGACION no sostiene ningun vinculo."""
        decision = bridge.evaluate_binding(_binding(
            claim_id="pieza-03-claim-1", packet_file="pieza-03-honor.json",
            declared_layer=bridge.CAPA_C, territories=("México",),
            source_ids=(), limits=("x",)))
        self.assertEqual(decision.state, bridge.ACCESS_GAP)
        self.assertIn("REQUIERE_INVESTIGACION", decision.reasons[-1])

    def test_duplicacion_semantica_sin_alias_ni_derived(self):
        """Declarar una relacion de identidad sin nombrar el origen se rechaza."""
        decision = bridge.evaluate_binding(
            _binding(identity_relation=bridge.DERIVED_FROM, identity_target="NONE"))
        self.assertEqual(decision.state, bridge.REJECTED)
        self.assertIn("exige nombrar el objeto de origen", decision.reasons[0])

    def test_relacion_de_identidad_inventada(self):
        decision = bridge.evaluate_binding(
            _binding(identity_relation="ES_LO_MISMO_QUE", identity_target="X"))
        self.assertEqual(decision.state, bridge.REJECTED)

    def test_publicacion_activada_por_error(self):
        """El fallo mas peligroso: un vinculo que se declara publicado."""
        decision = bridge.evaluate_binding(_binding(publication_state="PUBLICADO"))
        self.assertEqual(decision.state, bridge.REJECTED)
        self.assertTrue(any("jamás abre publicación" in r for r in decision.reasons))

    def test_owner_ausente(self):
        self.assertEqual(self._state(owner=""), bridge.REJECTED)

    def test_siguiente_accion_ausente(self):
        self.assertEqual(self._state(next_action="   "), bridge.REJECTED)

    def test_packet_equivocado_pide_revision(self):
        self.assertEqual(self._state(packet_file="pieza-03-honor.json"),
                         bridge.REVIEW_REQUIRED)

    def test_sin_acceso_al_canon_nada_se_aprueba(self):
        """Acceso inexistente al canon: el vinculo queda pendiente, no aprobado.

        Cubre el caso 'acceso a Drive inexistente o no autorizado' del §6: si la
        fuente de verdad no esta disponible, el contrato no puede concluir nada."""
        decision = bridge.evaluate_binding(_binding(), catalogo={})
        self.assertEqual(decision.state, bridge.PENDING_BINDING)
        self.assertNotEqual(decision.state, bridge.VERIFIED_BINDING)


if __name__ == "__main__":
    unittest.main()
