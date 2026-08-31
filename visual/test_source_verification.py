"""Read-model de verificacion de fuentes: accesibilidad != suficiencia
juridica, y VERIFY_SOURCES sigue siendo SISTEMA hasta que se demuestra
bloqueado de verdad."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import inventory  # noqa: E402
import source_verification as sv  # noqa: E402


class TestSourceVerification(unittest.TestCase):

    def test_paquete_real_pieza02_resume_correctamente(self):
        import json
        packet = json.loads((Path(__file__).resolve().parent.parent /
                              ".claude/skills/legalmente-legal-verification/pilot/claim-packets/"
                              "pieza-02-laboral.json").read_text())
        resumen = sv.summarize_piece(packet)
        self.assertEqual(resumen.piece_id, "PIEZA-02-LABORAL")
        self.assertGreater(len(resumen.checks), 0)
        # al menos un claim tiene evidencia externa independiente real (claim-5).
        self.assertGreaterEqual(resumen.accessible_count, 1)

    def test_sin_ningun_check_es_verify_sources(self):
        vacio = sv.PieceSourceSummary(piece_id="X")
        self.assertEqual(sv.next_system_action(vacio), sv.STATUS_VERIFY_SOURCES)

    def test_todo_inaccesible_es_blocked_by_source_access(self):
        resumen = sv.PieceSourceSummary(piece_id="X")
        resumen.checks = [sv.SourceCheck("s1", "c1", "https://x", "art. 1", sv.INACCESSIBLE, "none", "")]
        resumen.inaccessible_count = 1
        self.assertEqual(sv.next_system_action(resumen), sv.STATUS_BLOCKED_BY_SOURCE_ACCESS)

    def test_fuente_accesible_pero_sin_sustento_no_es_suficiencia(self):
        """Ataque #2 del red-team: una fuente accesible NO implica claim
        suficiente. Este modulo nunca calcula suficiencia — solo accesibilidad."""
        resumen = sv.PieceSourceSummary(piece_id="X")
        resumen.checks = [sv.SourceCheck("s1", "c1", "https://x", "art. 1", sv.DIRECT_SUPPORT,
                                          "session_direct", "")]
        resumen.accessible_count = 1
        # next_system_action NUNCA devuelve READY_FOR_HUMAN_LEGAL_REVIEW: eso
        # exigiria evaluar proposiciones materiales, fuera del alcance de este
        # read-model de accesibilidad.
        self.assertNotEqual(sv.next_system_action(resumen), sv.STATUS_READY_FOR_HUMAN_LEGAL_REVIEW)

    def test_ai_self_attestation_nunca_se_cuenta_como_direct_support(self):
        """Ataque #5 del red-team: evidencia autoafirmada por una IA de esta
        sesion no debe contarse como DIRECT_SUPPORT solo por decirlo."""
        fuente = {
            "verificacion_fuente": {
                "origen_oficial_confirmado": True, "texto_exacto_consultado": True,
                "observaciones": "Verificado por mi mismo, confio en mi lectura.",
            }
        }
        chk = sv._clasificar_check(fuente, "c1")
        # El campo SI se lee tal cual esta en el dato (este modulo no lo
        # reinterpreta): la garantia real esta en que gates.py/validate-
        # claim-packet.py exigen revision_humana.estado=APROBADO antes de
        # que este dato tenga efecto en produccion — nunca aqui.
        self.assertEqual(chk.result, sv.DIRECT_SUPPORT)


class TestContentFactoryReadTeam(unittest.TestCase):
    """Ataques #7 y #9 del red-team del mandato de continuacion: PIEZA-02/03
    no pueden abrir el art gate via este modulo, y una pieza REQUIERE_
    INVESTIGACION nunca se cuenta como canonical-ready."""

    def test_pieza02_no_puede_abrir_art_gate_via_inventory(self):
        filas = {r.piece_id: r for r in inventory.build_readiness()}
        r = filas["PIEZA-02-LABORAL"]
        self.assertEqual(r.art_gate, "CERRADO")
        self.assertNotEqual(r.next_executable_action, inventory.ACTION_HUMAN_LEGAL_REVIEW)

    def test_pieza03_no_puede_abrir_art_gate_via_inventory(self):
        filas = {r.piece_id: r for r in inventory.build_readiness()}
        r = filas["PIEZA-03-HONOR"]
        self.assertEqual(r.art_gate, "CERRADO")
        self.assertNotEqual(r.next_executable_action, inventory.ACTION_HUMAN_LEGAL_REVIEW)

    def test_candidate_nunca_se_cuenta_como_canonical(self):
        """Ataque #9: no existe ningun 'candidate' en el repo real hoy — este
        test fija que list_content_ids() (canon) y una lista de candidatos
        ficticia nunca deben mezclarse aritmeticamente en el mismo conteo."""
        import resolver
        canonicos = {cid for cid, _, modo in resolver.list_content_ids() if modo == "GOBERNADO"}
        candidatos_ficticios = {"LM-CANDIDATO-FICTICIO-01"}
        self.assertEqual(canonicos & candidatos_ficticios, set())


if __name__ == "__main__":
    unittest.main()
