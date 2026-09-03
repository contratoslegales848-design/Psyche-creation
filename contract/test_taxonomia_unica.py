"""Los enums del contrato y del validador no pueden derivar por separado.

Por qué existe este archivo. Las capas jurisdiccionales estaban declaradas a
mano en tres sitios: el validador canónico (Python, en la skill), el contrato
cross-repo (este paquete) y `knowledge-pilot` en legalmente-web (TypeScript).
Tres copias, ninguna atada a las otras. Y ya habían derivado: el validador
admite `NO_DETERMINADO` y las otras dos copias no.

La deriva no era cosmética. `NO_DETERMINADO` es el estado de un claim cuyo
alcance todavía no se ha establecido — el de las cuatro piezas declaradas
panhispánicas con fuentes de un solo país. Al no caber en el sobre canónico, la
única forma de exportarlas era reetiquetarlas a `NO_APLICA`, que sí cabía y
suena inofensivo. Significan cosas opuestas: «no sabemos qué territorio cubre»
frente a «no hay territorio que determinar». Convertir la primera en la segunda
pierde la duda por el camino.

Estas pruebas no pueden alcanzar el repositorio de TypeScript, y no lo fingen:
comprueban las dos copias Python, que son las que este repositorio posee, y
dejan constancia explícita de la tercera para que quien toque el contrato sepa
que existe.

Sin red. Determinista.
"""

import importlib.util
import unittest
from pathlib import Path

import canonical_envelope as C

REPO = Path(__file__).resolve().parent.parent
VALIDADOR = (REPO / ".claude" / "skills" / "legalmente-legal-verification"
             / "scripts" / "validate-claim-packet.py")


def _cargar_validador():
    """El validador se llama con guiones; no es importable por nombre."""
    spec = importlib.util.spec_from_file_location("validate_claim_packet", VALIDADOR)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


V = _cargar_validador()


class TestTaxonomiaUnica(unittest.TestCase):
    def test_las_capas_jurisdiccionales_coinciden_exactamente(self):
        """No 'compatibles', no 'un subconjunto': idénticas.

        Un subconjunto sería igual de peligroso: es exactamente la situación de
        la que venimos, y el sobre acabaría rechazando estados canónicos
        legítimos o invitando a reetiquetarlos.
        """
        self.assertEqual(
            C.JURISDICTION_LAYERS, V.VALID_ALCANCE,
            "el contrato y el validador declaran capas distintas — "
            f"solo en el contrato: {C.JURISDICTION_LAYERS - V.VALID_ALCANCE}; "
            f"solo en el validador: {V.VALID_ALCANCE - C.JURISDICTION_LAYERS}")

    def test_no_determinado_esta_en_ambos(self):
        """El caso concreto que provocó esta prueba."""
        self.assertIn("NO_DETERMINADO", C.JURISDICTION_LAYERS)
        self.assertIn("NO_DETERMINADO", V.VALID_ALCANCE)

    def test_los_estados_de_gate_coinciden(self):
        self.assertEqual(C.LEGAL_GATE_STATES, V.VALID_GATE)

    def test_los_estados_de_claim_del_contrato_existen_en_el_validador(self):
        """Aquí sí cabe una relación de subconjunto, y por una razón: el sobre
        añade 'PENDIENTE' como estado de transporte, que no es un estado
        jurídico del claim. Lo que NO puede pasar es que el contrato invente un
        estado jurídico que el canon no reconoce."""
        inventados = C.CLAIM_STATES - V.VALID_ESTADO - {"PENDIENTE"}
        self.assertEqual(inventados, set(),
                         f"el contrato declara estados que el canon no conoce: {inventados}")


class TestNoDeterminadoNoAbreNada(unittest.TestCase):
    """Admitir la capa no puede haber sido una puerta."""

    def _sobre(self, **extra):
        base = {
            "schema_version": C.ENVELOPE_SCHEMA_VERSION,
            "content_id": "LM-TEST-001",
            "claim_state": "REQUIERE_INVESTIGACION",
            "source_state": "PENDIENTE",
            "legal_gate_state": "CERRADO",
            "jurisdiction_layer": "NO_DETERMINADO",
            "territories": [],
            "claims": [],
            "provenance": {"sources": [{"id": "s1"}]},
            "art_eligibility": "NO_ELEGIBLE",
            "emitted_at": "2026-09-03T00:00:00Z",
        }
        base.update(extra)
        return base

    def test_un_alcance_sin_determinar_cabe_en_el_sobre(self):
        """El objetivo de la corrección: exportar la duda sin disfrazarla."""
        errores = C.validate_envelope(self._sobre())
        capas = [e for e in errores if "jurisdiction_layer" in e]
        self.assertEqual(capas, [], f"NO_DETERMINADO sigue sin caber: {errores}")

    def test_pero_nunca_con_el_gate_abierto(self):
        errores = C.validate_envelope(self._sobre(legal_gate_state="ABIERTO"))
        self.assertTrue(any("no se puede abrir el gate" in e for e in errores), errores)

    def test_ni_con_arte_elegible(self):
        errores = C.validate_envelope(self._sobre(art_eligibility="ELEGIBLE"))
        self.assertTrue(any("art_eligibility" in e for e in errores), errores)

    def test_no_aplica_sigue_siendo_un_estado_distinto(self):
        """La confusión que se quiere impedir: los dos son válidos y NO son
        intercambiables. 'NO_APLICA' sí puede acompañar a un gate abierto —una
        cita histórica, un formato de gobernanza— y 'NO_DETERMINADO' nunca."""
        errores = C.validate_envelope(
            self._sobre(jurisdiction_layer="NO_APLICA", legal_gate_state="ABIERTO"))
        self.assertEqual([e for e in errores if "no se puede abrir el gate" in e], [])


class TestLaTerceraCopiaQuedaDeclarada(unittest.TestCase):
    """La copia de TypeScript vive en otro repositorio y en otra cuenta.

    Esta prueba no puede comprobarla. Lo que sí puede es dejar constancia de que
    existe, para que nadie toque el contrato creyendo que solo hay dos copias.
    """

    TERCERA_COPIA = "legalmente-web · src/lib/knowledge-pilot/index.ts · jurisdictionLayer"

    def test_el_contrato_documenta_donde_esta_la_copia_que_no_podemos_probar(self):
        fuente = (Path(__file__).resolve().parent / "canonical_envelope.py").read_text(
            encoding="utf-8")
        self.assertIn("validate-claim-packet.py", fuente,
                      "el contrato debe decir de dónde derivan sus capas")

    def test_esta_prueba_nombra_la_copia_pendiente(self):
        self.assertIn("knowledge-pilot", self.TERCERA_COPIA)


if __name__ == "__main__":
    unittest.main()
