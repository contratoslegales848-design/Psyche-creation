#!/usr/bin/env python3
"""Pruebas unitarias (stdlib unittest) del validador legalmente-legal-verification.

Uso:
    python3 -m unittest scripts.test_validate_claim_packet -v
    (o, desde dentro de scripts/): python3 test_validate_claim_packet.py -v

Complementa, no sustituye, la ejecución del validador sobre los fixtures
reales de fixtures/piezas/ y fixtures/negativos/.
"""

import importlib.util
import sys
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parent / "validate-claim-packet.py"
spec = importlib.util.spec_from_file_location("validate_claim_packet", MODULE_PATH)
vcp = importlib.util.module_from_spec(spec)
sys.modules["validate_claim_packet"] = vcp
spec.loader.exec_module(vcp)


def base_fuente(**overrides):
    f = {
        "id": "f1", "tipo_fuente": "NORMA_OFICIAL", "titulo": "Ley X",
        "organismo_autor": "Autoridad X", "url": "https://www.boe.es/algo",
        "identificador_bibliografico": None, "fecha_consulta": "2026-08-25",
        "localizador": "art. 1", "dominio_oficial_confirmado": True,
    }
    f.update(overrides)
    return f


def base_claim(**overrides):
    c = {
        "claim_id": "c1", "texto_exacto": "Afirmación de prueba.", "ubicacion": "titulo",
        "tipo": "regla", "alcance": "NO_APLICA",
        "jurisdiccion": None, "nucleo_transversal": None, "variaciones_materiales": None,
        "jurisdicciones_revisadas": None, "diferencias_buscadas": None,
        "contraejemplos_encontrados": None, "justificacion_suficiencia_comparada": None,
        "fuentes": [base_fuente()],
        "confianza": "alta", "riesgo_falsa_universalizacion": "bajo", "riesgo_asesoria": "ninguno",
        "platform_review_required": False, "confidentiality_review_required": False,
        "estado": "APTO_PARA_NARRATIVA",
        "revision_humana": {"estado": "PENDIENTE", "revisor": None, "fecha": None, "observaciones": None},
        "gate_arte": "CERRADO",
        "reformulacion_propuesta": {"texto": None, "verificada": False, "nuevo_claim_id": None},
        "redaccion_prohibida": None, "notas": None,
    }
    c.update(overrides)
    return c


def base_piece(claims, **overrides):
    estados = [c["estado"] for c in claims]
    p = {
        "schema_version": "2.0", "piece_id": "p1", "claims": claims,
        "estado_agregado": vcp.compute_estado_agregado(estados),
        "revisiones_pendientes": sorted(vcp.compute_revisiones_pendientes(claims)),
        "gate_global_arte": "CERRADO",
    }
    p.update(overrides)
    return p


class TestFuenteNivel(unittest.TestCase):
    def test_norma_oficial_confirmada_es_nivel_1(self):
        self.assertEqual(vcp.compute_fuente_nivel(base_fuente()), vcp.NIVEL_1_CONFIRMADO)

    def test_norma_oficial_no_confirmada_es_nivel_2(self):
        f = base_fuente(dominio_oficial_confirmado=False)
        self.assertEqual(vcp.compute_fuente_nivel(f), vcp.NIVEL_2_DECLARADO_NO_VERIFICADO)

    def test_secundaria_es_nivel_3(self):
        f = base_fuente(tipo_fuente="SECUNDARIA_ESPECIALIZADA", dominio_oficial_confirmado=False)
        self.assertEqual(vcp.compute_fuente_nivel(f), vcp.NIVEL_3_ACADEMICA_SECUNDARIA)

    def test_drive_es_nivel_4(self):
        f = base_fuente(tipo_fuente="DRIVE_INTERNO", dominio_oficial_confirmado=False)
        self.assertEqual(vcp.compute_fuente_nivel(f), vcp.NIVEL_4_DRIVE)


class TestMaxEstadoPorFuentes(unittest.TestCase):
    def test_sin_fuentes_requiere_investigacion(self):
        self.assertEqual(vcp.compute_max_estado_por_fuentes([]), "REQUIERE_INVESTIGACION")

    def test_solo_drive_requiere_investigacion(self):
        fuentes = [base_fuente(tipo_fuente="DRIVE_INTERNO", dominio_oficial_confirmado=False)]
        self.assertEqual(vcp.compute_max_estado_por_fuentes(fuentes), "REQUIERE_INVESTIGACION")

    def test_oficial_confirmada_permite_narrativa(self):
        self.assertEqual(vcp.compute_max_estado_por_fuentes([base_fuente()]), "APTO_PARA_NARRATIVA")

    def test_oficial_no_confirmada_topa_en_matices(self):
        fuentes = [base_fuente(dominio_oficial_confirmado=False)]
        self.assertEqual(vcp.compute_max_estado_por_fuentes(fuentes), "APTO_CON_MATICES")

    def test_secundaria_topa_en_matices(self):
        fuentes = [base_fuente(tipo_fuente="SECUNDARIA_ESPECIALIZADA", dominio_oficial_confirmado=False)]
        self.assertEqual(vcp.compute_max_estado_por_fuentes(fuentes), "APTO_CON_MATICES")


class TestClaimGate(unittest.TestCase):
    def test_gate_cerrado_si_no_apto_para_narrativa(self):
        c = base_claim(estado="APTO_CON_MATICES")
        self.assertEqual(vcp.compute_claim_gate(c, c["estado"]), "CERRADO")

    def test_gate_cerrado_si_revision_pendiente(self):
        c = base_claim(estado="APTO_PARA_NARRATIVA")
        self.assertEqual(vcp.compute_claim_gate(c, c["estado"]), "CERRADO")

    def test_gate_abierto_si_todo_en_orden(self):
        c = base_claim(estado="APTO_PARA_NARRATIVA",
                        revision_humana={"estado": "APROBADO", "revisor": "R", "fecha": "2026-08-25", "observaciones": None})
        self.assertEqual(vcp.compute_claim_gate(c, c["estado"]), "ABIERTO")

    def test_gate_cerrado_si_platform_review_pendiente(self):
        c = base_claim(estado="APTO_PARA_NARRATIVA", platform_review_required=True,
                        revision_humana={"estado": "APROBADO", "revisor": "R", "fecha": "2026-08-25", "observaciones": None})
        self.assertEqual(vcp.compute_claim_gate(c, c["estado"]), "CERRADO")

    def test_gate_cerrado_si_confidentiality_review_pendiente(self):
        c = base_claim(estado="APTO_PARA_NARRATIVA", confidentiality_review_required=True,
                        revision_humana={"estado": "APROBADO", "revisor": "R", "fecha": "2026-08-25", "observaciones": None})
        self.assertEqual(vcp.compute_claim_gate(c, c["estado"]), "CERRADO")


class TestEstadoAgregado(unittest.TestCase):
    def test_uno_bloqueado_bloquea_toda_la_pieza(self):
        estados = ["APTO_PARA_NARRATIVA", "BLOQUEADO", "APTO_PARA_NARRATIVA"]
        self.assertEqual(vcp.compute_estado_agregado(estados), "BLOQUEADO")

    def test_uno_requiere_investigacion_frena_la_pieza(self):
        estados = ["APTO_PARA_NARRATIVA"] * 9 + ["REQUIERE_INVESTIGACION"]
        self.assertEqual(vcp.compute_estado_agregado(estados), "REQUIERE_INVESTIGACION")

    def test_todos_aptos_para_narrativa(self):
        estados = ["APTO_PARA_NARRATIVA"] * 10
        self.assertEqual(vcp.compute_estado_agregado(estados), "APTO_PARA_NARRATIVA")

    def test_matices_frena_narrativa_plena(self):
        estados = ["APTO_PARA_NARRATIVA", "APTO_CON_MATICES"]
        self.assertEqual(vcp.compute_estado_agregado(estados), "APTO_CON_MATICES")


class TestValidateFuente(unittest.TestCase):
    def test_fuente_valida_sin_errores(self):
        errors, warnings = vcp.validate_fuente(base_fuente(), "f")
        self.assertEqual(errors, [])

    def test_tipo_fuente_invalido_es_error(self):
        errors, _ = vcp.validate_fuente(base_fuente(tipo_fuente="INVENTADO"), "f")
        self.assertTrue(any("tipo_fuente" in e for e in errors))

    def test_sin_url_ni_identificador_es_error(self):
        errors, _ = vcp.validate_fuente(base_fuente(url=None, identificador_bibliografico=None), "f")
        self.assertTrue(any("identificador_bibliografico" in e for e in errors))

    def test_identificador_bibliografico_sin_url_es_valido(self):
        errors, _ = vcp.validate_fuente(base_fuente(url=None, identificador_bibliografico="ISBN 000-0"), "f")
        self.assertEqual(errors, [])

    def test_url_no_http_es_error(self):
        errors, _ = vcp.validate_fuente(base_fuente(url="ftp://example.com/x"), "f")
        self.assertTrue(any("URL" in e for e in errors))

    def test_dominio_no_oficial_genera_advertencia_no_error(self):
        f = base_fuente(url="https://mexico.justia.com/algo", dominio_oficial_confirmado=True)
        errors, warnings = vcp.validate_fuente(f, "f")
        self.assertEqual(errors, [])
        self.assertTrue(warnings)


class TestValidateClaimCapaA(unittest.TestCase):
    def test_capa_a_sin_justificacion_es_error(self):
        c = base_claim(alcance="CAPA_A_TRANSVERSAL")
        errors, _, _, _ = vcp.validate_claim(c, "c")
        self.assertTrue(any("justificación comparada" in e for e in errors))

    def test_capa_a_con_dos_jurisdicciones_es_error(self):
        c = base_claim(
            alcance="CAPA_A_TRANSVERSAL",
            jurisdicciones_revisadas=[{"pais": "España", "fuente_ids": ["f1"]}, {"pais": "México", "fuente_ids": ["f1"]}],
            diferencias_buscadas="x", contraejemplos_encontrados="x", justificacion_suficiencia_comparada="x",
        )
        errors, _, _, _ = vcp.validate_claim(c, "c")
        self.assertTrue(any("al menos 3" in e for e in errors))

    def test_capa_a_con_pais_duplicado_es_error(self):
        c = base_claim(
            alcance="CAPA_A_TRANSVERSAL",
            jurisdicciones_revisadas=[
                {"pais": "España", "fuente_ids": ["f1"]},
                {"pais": " españa ", "fuente_ids": ["f1"]},
                {"pais": "México", "fuente_ids": ["f1"]},
            ],
            diferencias_buscadas="x", contraejemplos_encontrados="x", justificacion_suficiencia_comparada="x",
        )
        errors, _, _, _ = vcp.validate_claim(c, "c")
        self.assertTrue(any("duplicado" in e for e in errors))

    def test_capa_a_con_jurisdiccion_sin_fuente_es_error(self):
        c = base_claim(
            alcance="CAPA_A_TRANSVERSAL",
            jurisdicciones_revisadas=[
                {"pais": "España", "fuente_ids": ["f1"]},
                {"pais": "México", "fuente_ids": []},
                {"pais": "Argentina", "fuente_ids": ["f1"]},
            ],
            diferencias_buscadas="x", contraejemplos_encontrados="x", justificacion_suficiencia_comparada="x",
        )
        errors, _, _, _ = vcp.validate_claim(c, "c")
        self.assertTrue(any("fuente_ids" in e for e in errors))

    def test_capa_a_completa_y_valida_pasa(self):
        c = base_claim(
            alcance="CAPA_A_TRANSVERSAL", estado="APTO_PARA_NARRATIVA",
            fuentes=[base_fuente(id="f1"), base_fuente(id="f2"), base_fuente(id="f3")],
            jurisdicciones_revisadas=[
                {"pais": "España", "fuente_ids": ["f1"]},
                {"pais": "México", "fuente_ids": ["f2"]},
                {"pais": "Argentina", "fuente_ids": ["f3"]},
            ],
            diferencias_buscadas="x", contraejemplos_encontrados="ninguno", justificacion_suficiencia_comparada="x",
        )
        errors, _, max_estado, gate = vcp.validate_claim(c, "c")
        self.assertEqual(errors, [])
        self.assertEqual(max_estado, "APTO_PARA_NARRATIVA")


class TestValidateClaimAlcanceEspecial(unittest.TestCase):
    def test_no_determinado_con_bloqueado_es_error(self):
        c = base_claim(alcance="NO_DETERMINADO", estado="BLOQUEADO", fuentes=[])
        errors, _, _, _ = vcp.validate_claim(c, "c")
        self.assertTrue(any("NO_DETERMINADO" in e for e in errors))

    def test_no_determinado_con_requiere_investigacion_es_valido(self):
        c = base_claim(alcance="NO_DETERMINADO", estado="REQUIERE_INVESTIGACION", fuentes=[])
        errors, _, _, _ = vcp.validate_claim(c, "c")
        self.assertEqual(errors, [])

    def test_no_aplica_con_bloqueado_es_valido(self):
        c = base_claim(alcance="NO_APLICA", estado="BLOQUEADO", fuentes=[])
        errors, _, _, _ = vcp.validate_claim(c, "c")
        self.assertEqual(errors, [])


class TestValidateClaimEstadoVsFuentes(unittest.TestCase):
    def test_apto_narrativa_con_solo_secundaria_es_error(self):
        c = base_claim(alcance="NO_APLICA", estado="APTO_PARA_NARRATIVA",
                        fuentes=[base_fuente(tipo_fuente="SECUNDARIA_ESPECIALIZADA", dominio_oficial_confirmado=False)])
        errors, _, _, _ = vcp.validate_claim(c, "c")
        self.assertTrue(any("excede lo que las fuentes permiten" in e for e in errors))

    def test_apto_narrativa_con_oficial_confirmada_es_valido(self):
        c = base_claim(alcance="NO_APLICA", estado="APTO_PARA_NARRATIVA", fuentes=[base_fuente()])
        errors, _, _, _ = vcp.validate_claim(c, "c")
        self.assertEqual(errors, [])

    def test_confianza_baja_en_estado_apto_es_error(self):
        c = base_claim(alcance="NO_APLICA", estado="APTO_CON_MATICES", confianza="baja",
                        fuentes=[base_fuente(dominio_oficial_confirmado=False)])
        errors, _, _, _ = vcp.validate_claim(c, "c")
        self.assertTrue(any("confianza" in e for e in errors))


class TestValidateClaimGateDeclarado(unittest.TestCase):
    def test_gate_abierto_declarado_sin_aprobacion_es_error(self):
        c = base_claim(alcance="NO_APLICA", estado="APTO_PARA_NARRATIVA", gate_arte="ABIERTO")
        errors, _, _, _ = vcp.validate_claim(c, "c")
        self.assertTrue(any("gate_arte" in e for e in errors))

    def test_gate_cerrado_declarado_correctamente_es_valido(self):
        c = base_claim(alcance="NO_APLICA", estado="APTO_PARA_NARRATIVA", gate_arte="CERRADO")
        errors, _, _, _ = vcp.validate_claim(c, "c")
        self.assertEqual(errors, [])

    def test_gate_abierto_con_todo_en_regla_es_valido(self):
        c = base_claim(alcance="NO_APLICA", estado="APTO_PARA_NARRATIVA", gate_arte="ABIERTO",
                        revision_humana={"estado": "APROBADO", "revisor": "R", "fecha": "2026-08-25", "observaciones": None})
        errors, _, _, _ = vcp.validate_claim(c, "c")
        self.assertEqual(errors, [])


class TestReformulacion(unittest.TestCase):
    def test_verificada_sin_nuevo_claim_id_es_error(self):
        c = base_claim(reformulacion_propuesta={"texto": "algo nuevo", "verificada": True, "nuevo_claim_id": None})
        errors, _, _, _ = vcp.validate_claim(c, "c")
        self.assertTrue(any("reformulacion_propuesta" in e for e in errors))

    def test_no_verificada_sin_nuevo_claim_id_es_valido(self):
        c = base_claim(reformulacion_propuesta={"texto": "algo nuevo", "verificada": False, "nuevo_claim_id": None})
        errors, _, _, _ = vcp.validate_claim(c, "c")
        self.assertEqual(errors, [])


class TestValidatePiece(unittest.TestCase):
    def test_pieza_valida_pasa(self):
        c = base_claim(alcance="NO_APLICA", estado="APTO_PARA_NARRATIVA")
        piece = base_piece([c])
        errors, warnings = vcp.validate_piece(piece, "p")
        self.assertEqual(errors, [])

    def test_estado_agregado_incorrecto_es_error(self):
        c = base_claim(alcance="NO_APLICA", estado="APTO_PARA_NARRATIVA")
        piece = base_piece([c], estado_agregado="BLOQUEADO")
        errors, _ = vcp.validate_piece(piece, "p")
        self.assertTrue(any("estado_agregado" in e for e in errors))

    def test_gate_global_abierto_sin_condiciones_es_error(self):
        c = base_claim(alcance="NO_APLICA", estado="APTO_PARA_NARRATIVA")  # gate_arte CERRADO
        piece = base_piece([c], gate_global_arte="ABIERTO")
        errors, _ = vcp.validate_piece(piece, "p")
        self.assertTrue(any("gate_global_arte" in e for e in errors))

    def test_gate_global_abierto_con_todo_aprobado_es_valido(self):
        c = base_claim(
            alcance="NO_APLICA", estado="APTO_PARA_NARRATIVA", gate_arte="ABIERTO",
            revision_humana={"estado": "APROBADO", "revisor": "R", "fecha": "2026-08-25", "observaciones": None},
        )
        piece = base_piece([c], gate_global_arte="ABIERTO")
        errors, _ = vcp.validate_piece(piece, "p")
        self.assertEqual(errors, [])

    def test_nueve_aptos_uno_pendiente_no_puede_declararse_apto(self):
        aprobados = [
            base_claim(
                claim_id=f"c{i}", alcance="NO_APLICA", estado="APTO_PARA_NARRATIVA", gate_arte="ABIERTO",
                revision_humana={"estado": "APROBADO", "revisor": "R", "fecha": "2026-08-25", "observaciones": None},
            )
            for i in range(1, 10)
        ]
        pendiente = base_claim(claim_id="c10", alcance="NO_APLICA", estado="REQUIERE_INVESTIGACION", fuentes=[])
        claims = aprobados + [pendiente]
        piece = base_piece(claims, estado_agregado="APTO_PARA_NARRATIVA", revisiones_pendientes=[], gate_global_arte="ABIERTO")
        errors, _ = vcp.validate_piece(piece, "p")
        self.assertTrue(errors)
        self.assertTrue(any("REQUIERE_INVESTIGACION" in e for e in errors))

    def test_claim_id_duplicado_es_error(self):
        c1 = base_claim(claim_id="dup")
        c2 = base_claim(claim_id="dup")
        piece = base_piece([c1, c2])
        errors, _ = vcp.validate_piece(piece, "p")
        self.assertTrue(any("duplicado" in e for e in errors))

    def test_schema_version_incorrecta_es_error(self):
        c = base_claim()
        piece = base_piece([c], schema_version="1.0")
        errors, _ = vcp.validate_piece(piece, "p")
        self.assertTrue(any("schema_version" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
