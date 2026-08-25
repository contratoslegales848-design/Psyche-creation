#!/usr/bin/env python3
"""Pruebas unitarias (stdlib unittest) del validador legalmente-legal-verification
(esquema v3).

Uso:
    python3 -m unittest test_validate_claim_packet -v
    (desde dentro de scripts/)
"""

import importlib.util
import json
import re
import sys
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parent / "validate-claim-packet.py"
spec = importlib.util.spec_from_file_location("validate_claim_packet", MODULE_PATH)
vcp = importlib.util.module_from_spec(spec)
sys.modules["validate_claim_packet"] = vcp
spec.loader.exec_module(vcp)

SKILL_ROOT = Path(__file__).resolve().parent.parent
TODAY = "2026-08-25"

# Identificadores de revisor que SÍ pueden aparecer en pruebas — nunca un
# nombre real. Ver Fase 1C, Paso 2 y Paso 10.12.
REVISOR_FICTICIO = "REVISOR_FICTICIO_SOLO_PRUEBA"
FORBIDDEN_REAL_NAMES = ["Raymundo Acevedo", "Raymundo"]


def base_verificacion(origen=True, texto=True, vigencia=True):
    return {
        "origen_oficial_confirmado": origen, "texto_exacto_consultado": texto,
        "vigencia_comprobada": vigencia,
        "fecha_comprobacion": TODAY if (texto or vigencia) else None,
        "metodo_o_evidencia": "Lectura directa del BOE" if texto else None,
        "observaciones": None,
    }


def base_fuente(**overrides):
    f = {
        "id": "f1", "tipo_fuente": "NORMA_OFICIAL", "titulo": "Ley X",
        "organismo_autor": "Autoridad X", "url": "https://www.boe.es/algo",
        "identificador_bibliografico": None, "fecha_consulta": TODAY,
        "localizador": "art. 1", "jurisdicciones_cubiertas": ["España"],
        "verificacion_fuente": base_verificacion(),
    }
    f.update(overrides)
    return f


def base_review(required=False, status="NO_APLICA"):
    return {"required": required, "status": status, "revisor": None, "fecha": None, "observaciones": None}


def base_revision_humana(estado="PENDIENTE", revisor=None, fecha=None, contenido_hash=None):
    return {"estado": estado, "revisor": revisor, "fecha": fecha, "observaciones": None, "contenido_hash_sha256": contenido_hash}


def base_claim(**overrides):
    c = {
        "claim_id": "c1", "texto_exacto": "Afirmación de prueba.", "ubicacion": "titulo",
        "tipo": "regla", "alcance": "NO_APLICA",
        "jurisdiccion": None, "nucleo_transversal": None, "variaciones_materiales": None,
        "jurisdicciones_revisadas": None, "diferencias_buscadas": None,
        "contraejemplos_encontrados": None, "justificacion_suficiencia_comparada": None,
        "fuentes": [base_fuente()],
        "confianza": "alta", "riesgo_falsa_universalizacion": "bajo", "riesgo_asesoria": "ninguno",
        "platform_review": base_review(), "confidentiality_review": base_review(),
        "estado": "APTO_PARA_NARRATIVA",
        "revision_humana": base_revision_humana(),
        "gate_arte": "CERRADO",
        "reformulacion_propuesta": {"texto": None, "verificada": False, "nuevo_claim_id": None},
        "redaccion_prohibida": None, "notas": None,
    }
    c.update(overrides)
    return c


def approved_claim(**overrides):
    """Claim con revisión humana APROBADA y hash correcto — SOLO usa el
    identificador ficticio de prueba, nunca un nombre real."""
    c = base_claim(**overrides)
    c["revision_humana"] = base_revision_humana("APROBADO", revisor=REVISOR_FICTICIO, fecha=TODAY)
    c["revision_humana"]["contenido_hash_sha256"] = vcp.compute_content_hash(c)
    c["gate_arte"] = "ABIERTO"
    return c


def base_piece(claims, **overrides):
    estados = [c["estado"] for c in claims]
    p = {
        "schema_version": "3.0", "piece_id": "p1", "claims": claims,
        "estado_agregado": vcp.compute_estado_agregado(estados),
        "revisiones_pendientes": sorted(vcp.compute_revisiones_pendientes(claims)),
        "gate_global_arte": "CERRADO",
    }
    p.update(overrides)
    return p


class TestHostnameMatching(unittest.TestCase):
    def test_dominio_exacto_valido(self):
        self.assertTrue(vcp.hostname_matches_official("https://boe.es/x"))

    def test_subdominio_real_valido(self):
        self.assertTrue(vcp.hostname_matches_official("https://www.boe.es/x"))

    def test_subcadena_boe_es_evil_com_invalida(self):
        self.assertFalse(vcp.hostname_matches_official("https://boe.es.evil.com/x"))

    def test_prefijo_notboe_es_invalido(self):
        self.assertFalse(vcp.hostname_matches_official("https://notboe.es/x"))

    def test_dominio_privado_justia_invalido(self):
        self.assertFalse(vcp.hostname_matches_official("https://mexico.justia.com/x"))

    def test_sin_url_invalido(self):
        self.assertFalse(vcp.hostname_matches_official(None))


class TestFuenteNivelFailClosed(unittest.TestCase):
    def test_oficial_confirmada_hostname_real_es_nivel_1(self):
        f = base_fuente()
        self.assertEqual(vcp.compute_fuente_nivel(f), vcp.NIVEL_1_CONFIRMADO)

    def test_origen_confirmado_true_pero_hostname_falso_no_es_nivel_1(self):
        """Bypass A: el booleano autoafirmado NUNCA basta solo — hace falta
        que el hostname real coincida con la lista cerrada."""
        f = base_fuente(url="https://mexico.justia.com/x")
        self.assertNotEqual(vcp.compute_fuente_nivel(f), vcp.NIVEL_1_CONFIRMADO)
        self.assertEqual(vcp.compute_fuente_nivel(f), vcp.NIVEL_2_DECLARADO_NO_VERIFICADO)

    def test_hostname_real_pero_texto_no_consultado_no_es_nivel_1(self):
        f = base_fuente(verificacion_fuente=base_verificacion(texto=False))
        self.assertNotEqual(vcp.compute_fuente_nivel(f), vcp.NIVEL_1_CONFIRMADO)

    def test_hostname_real_pero_vigencia_no_comprobada_no_es_nivel_1(self):
        f = base_fuente(verificacion_fuente=base_verificacion(vigencia=False))
        self.assertNotEqual(vcp.compute_fuente_nivel(f), vcp.NIVEL_1_CONFIRMADO)

    def test_secundaria_es_nivel_3(self):
        f = base_fuente(tipo_fuente="SECUNDARIA_ESPECIALIZADA", verificacion_fuente=base_verificacion(False, False, False))
        self.assertEqual(vcp.compute_fuente_nivel(f), vcp.NIVEL_3_ACADEMICA_SECUNDARIA)

    def test_drive_es_nivel_4(self):
        f = base_fuente(tipo_fuente="DRIVE_INTERNO", verificacion_fuente=base_verificacion(False, False, False))
        self.assertEqual(vcp.compute_fuente_nivel(f), vcp.NIVEL_4_DRIVE)


class TestCapaAJurisdiccionFuente(unittest.TestCase):
    def _claim_una_fuente_cuatro_paises(self):
        f = base_fuente(id="f-es", jurisdicciones_cubiertas=["España"])
        return base_claim(
            alcance="CAPA_A_TRANSVERSAL", fuentes=[f],
            jurisdicciones_revisadas=[
                {"pais": "España", "fuente_ids": ["f-es"]}, {"pais": "México", "fuente_ids": ["f-es"]},
                {"pais": "Argentina", "fuente_ids": ["f-es"]}, {"pais": "Perú", "fuente_ids": ["f-es"]},
            ],
            diferencias_buscadas="x", contraejemplos_encontrados="ninguno", justificacion_suficiencia_comparada="x",
        )

    def test_bypass_b_una_fuente_cuatro_paises_es_error(self):
        c = self._claim_una_fuente_cuatro_paises()
        errors, _, _, _ = vcp.validate_claim(c, "c")
        self.assertTrue(any("no cubre esta jurisdicción" in e for e in errors))

    def test_fuente_con_jurisdiccion_correcta_por_pais_es_valida(self):
        fuentes = [
            base_fuente(id="f-es", jurisdicciones_cubiertas=["España"]),
            base_fuente(id="f-mx", jurisdicciones_cubiertas=["México"]),
            base_fuente(id="f-ar", jurisdicciones_cubiertas=["Argentina"]),
        ]
        c = base_claim(
            alcance="CAPA_A_TRANSVERSAL", fuentes=fuentes,
            jurisdicciones_revisadas=[
                {"pais": "España", "fuente_ids": ["f-es"]}, {"pais": "México", "fuente_ids": ["f-mx"]},
                {"pais": "Argentina", "fuente_ids": ["f-ar"]},
            ],
            diferencias_buscadas="x", contraejemplos_encontrados="ninguno", justificacion_suficiencia_comparada="x",
        )
        errors, _, max_estado, _ = vcp.validate_claim(c, "c")
        self.assertEqual(errors, [])
        self.assertEqual(max_estado, "APTO_PARA_NARRATIVA")

    def test_una_nivel_1_y_tres_sin_verificar_topa_en_el_pais_mas_debil(self):
        """'Una fuente Nivel 1 confirmada + tres sin verificar no puede
        sostener APTO_PARA_NARRATIVA para toda la comparación' — el techo de
        Capa A es el mínimo entre las 4 jurisdicciones, no el máximo."""
        fuentes = [
            base_fuente(id="f-es", jurisdicciones_cubiertas=["España"]),  # Nivel 1 real
            base_fuente(id="f-mx", jurisdicciones_cubiertas=["México"], verificacion_fuente=base_verificacion(False, False, False)),
            base_fuente(id="f-ar", jurisdicciones_cubiertas=["Argentina"], verificacion_fuente=base_verificacion(False, False, False)),
            base_fuente(id="f-pe", jurisdicciones_cubiertas=["Perú"], verificacion_fuente=base_verificacion(False, False, False)),
        ]
        c = base_claim(
            alcance="CAPA_A_TRANSVERSAL", fuentes=fuentes,
            jurisdicciones_revisadas=[
                {"pais": "España", "fuente_ids": ["f-es"]}, {"pais": "México", "fuente_ids": ["f-mx"]},
                {"pais": "Argentina", "fuente_ids": ["f-ar"]}, {"pais": "Perú", "fuente_ids": ["f-pe"]},
            ],
            diferencias_buscadas="x", contraejemplos_encontrados="ninguno", justificacion_suficiencia_comparada="x",
        )
        fuentes_by_id = {f["id"]: f for f in fuentes}
        ceiling = vcp.compute_capa_a_ceiling(c, fuentes_by_id)
        self.assertEqual(ceiling, "APTO_CON_MATICES")

    def test_tres_fuente_ids_del_mismo_pais_no_cubren_los_otros(self):
        f = base_fuente(id="f-mx", jurisdicciones_cubiertas=["México"])
        c = base_claim(
            alcance="CAPA_A_TRANSVERSAL", fuentes=[f],
            jurisdicciones_revisadas=[
                {"pais": "México", "fuente_ids": ["f-mx"]}, {"pais": "España", "fuente_ids": ["f-mx"]},
                {"pais": "Argentina", "fuente_ids": ["f-mx"]},
            ],
            diferencias_buscadas="x", contraejemplos_encontrados="ninguno", justificacion_suficiencia_comparada="x",
        )
        errors, _, _, _ = vcp.validate_claim(c, "c")
        self.assertTrue(any("no cubre esta jurisdicción" in e for e in errors))


class TestTiposEstrictos(unittest.TestCase):
    def test_jurisdiccion_entero_es_error(self):
        f = base_fuente(jurisdicciones_cubiertas=["México"])
        c = base_claim(alcance="CAPA_C_NACIONAL", jurisdiccion=123, estado="APTO_CON_MATICES", fuentes=[f])
        errors, _, _, _ = vcp.validate_claim(c, "c")
        self.assertTrue(any("'jurisdiccion' debe ser string" in e for e in errors))

    def test_variaciones_materiales_entero_es_error(self):
        c = base_claim(alcance="CAPA_B_VARIABLE", variaciones_materiales=123, estado="REQUIERE_INVESTIGACION", fuentes=[])
        errors, _, _, _ = vcp.validate_claim(c, "c")
        self.assertTrue(any("'variaciones_materiales' debe ser string" in e for e in errors))

    def test_jurisdiccion_lista_de_strings_es_valida(self):
        fuentes = [base_fuente(id="f1", jurisdicciones_cubiertas=["México"]), base_fuente(id="f2", jurisdicciones_cubiertas=["Colombia"])]
        c = base_claim(alcance="CAPA_C_NACIONAL", jurisdiccion=["México", "Colombia"], estado="APTO_CON_MATICES", fuentes=fuentes)
        errors, _, _, _ = vcp.validate_claim(c, "c")
        self.assertEqual(errors, [])


class TestVerificacionFuente(unittest.TestCase):
    def test_texto_no_vacio_requerido_si_vigencia_true(self):
        v = base_verificacion()
        v["fecha_comprobacion"] = None
        errors = vcp.validate_verificacion_fuente(v, "f")
        self.assertTrue(any("vigencia_comprobada" in e for e in errors))

    def test_metodo_requerido_si_texto_consultado_true(self):
        v = base_verificacion()
        v["metodo_o_evidencia"] = None
        errors = vcp.validate_verificacion_fuente(v, "f")
        self.assertTrue(any("metodo_o_evidencia" in e for e in errors))

    def test_verificacion_completa_no_errores(self):
        self.assertEqual(vcp.validate_verificacion_fuente(base_verificacion(), "f"), [])


class TestGateYHash(unittest.TestCase):
    def test_gate_cerrado_por_defecto(self):
        c = base_claim(estado="APTO_PARA_NARRATIVA")
        errors, _, _, gate = vcp.validate_claim(c, "c")
        self.assertEqual(gate, "CERRADO")

    def test_gate_abierto_con_hash_correcto(self):
        c = approved_claim()
        errors, _, _, gate = vcp.validate_claim(c, "c")
        self.assertEqual(errors, [])
        self.assertEqual(gate, "ABIERTO")

    def test_aprobacion_invalida_si_contenido_cambia_despues(self):
        c = approved_claim()
        c["texto_exacto"] = "Texto cambiado después de aprobar."
        errors, _, _, gate = vcp.validate_claim(c, "c")
        self.assertTrue(any("no coincide con el hash recalculado" in e for e in errors))

    def test_gate_declarado_abierto_sin_aprobacion_es_error(self):
        c = base_claim(estado="APTO_PARA_NARRATIVA", gate_arte="ABIERTO")
        errors, _, _, _ = vcp.validate_claim(c, "c")
        self.assertTrue(any("gate_arte" in e for e in errors))

    def test_platform_review_pendiente_cierra_el_gate(self):
        c = approved_claim(platform_review=base_review(required=True, status="PENDIENTE"))
        c["gate_arte"] = "ABIERTO"
        errors, _, _, gate = vcp.validate_claim(c, "c")
        self.assertEqual(gate, "CERRADO")
        self.assertTrue(errors)

    def test_confidentiality_review_rechazada_cierra_el_gate(self):
        c = approved_claim(confidentiality_review=base_review(required=True, status="RECHAZADO"))
        c["gate_arte"] = "ABIERTO"
        errors, _, _, gate = vcp.validate_claim(c, "c")
        self.assertEqual(gate, "CERRADO")


class TestReviewObject(unittest.TestCase):
    def test_required_false_status_no_aplica_es_valido(self):
        errors = vcp.validate_review_object(base_review(False, "NO_APLICA"), "c", "platform_review")
        self.assertEqual(errors, [])

    def test_required_false_status_pendiente_es_error(self):
        errors = vcp.validate_review_object(base_review(False, "PENDIENTE"), "c", "platform_review")
        self.assertTrue(errors)

    def test_required_true_status_no_aplica_es_error(self):
        errors = vcp.validate_review_object(base_review(True, "NO_APLICA"), "c", "platform_review")
        self.assertTrue(errors)

    def test_required_true_aprobado_sin_revisor_es_error(self):
        r = base_review(True, "APROBADO")
        errors = vcp.validate_review_object(r, "c", "platform_review")
        self.assertTrue(errors)


class TestReformulacion(unittest.TestCase):
    def test_verificada_sin_nuevo_claim_id_es_error(self):
        c = base_claim(reformulacion_propuesta={"texto": "algo nuevo", "verificada": True, "nuevo_claim_id": None})
        errors, _, _, _ = vcp.validate_claim(c, "c")
        self.assertTrue(any("reformulacion_propuesta" in e for e in errors))

    def test_no_verificada_es_valida(self):
        c = base_claim(reformulacion_propuesta={"texto": "algo nuevo", "verificada": False, "nuevo_claim_id": None})
        errors, _, _, _ = vcp.validate_claim(c, "c")
        self.assertEqual(errors, [])


class TestEstadoAgregadoYPieza(unittest.TestCase):
    def test_uno_bloqueado_bloquea_toda_la_pieza(self):
        estados = ["APTO_PARA_NARRATIVA", "BLOQUEADO", "APTO_PARA_NARRATIVA"]
        self.assertEqual(vcp.compute_estado_agregado(estados), "BLOQUEADO")

    def test_pieza_valida_pasa(self):
        c = base_claim(estado="APTO_PARA_NARRATIVA")
        piece = base_piece([c])
        errors, _ = vcp.validate_piece(piece, "p")
        self.assertEqual(errors, [])

    def test_gate_global_abierto_sin_aprobacion_es_error(self):
        c = base_claim(estado="APTO_PARA_NARRATIVA")
        piece = base_piece([c], gate_global_arte="ABIERTO")
        errors, _ = vcp.validate_piece(piece, "p")
        self.assertTrue(any("gate_global_arte" in e for e in errors))

    def test_gate_global_abierto_con_aprobacion_real_es_valido(self):
        c = approved_claim()
        piece = base_piece([c], estado_agregado="APTO_PARA_NARRATIVA", revisiones_pendientes=[], gate_global_arte="ABIERTO")
        errors, _ = vcp.validate_piece(piece, "p")
        self.assertEqual(errors, [])

    def test_nueve_aptos_uno_pendiente_no_puede_declararse_abierta(self):
        aprobados = [approved_claim(claim_id=f"c{i}") for i in range(1, 10)]
        pendiente = base_claim(claim_id="c10", estado="REQUIERE_INVESTIGACION", fuentes=[])
        claims = aprobados + [pendiente]
        piece = base_piece(claims, estado_agregado="APTO_PARA_NARRATIVA", revisiones_pendientes=[], gate_global_arte="ABIERTO")
        errors, _ = vcp.validate_piece(piece, "p")
        self.assertTrue(errors)

    def test_claim_id_duplicado_es_error(self):
        c1 = base_claim(claim_id="dup")
        c2 = base_claim(claim_id="dup")
        piece = base_piece([c1, c2])
        errors, _ = vcp.validate_piece(piece, "p")
        self.assertTrue(any("duplicado" in e for e in errors))

    def test_schema_version_incorrecta_es_error(self):
        c = base_claim()
        piece = base_piece([c], schema_version="2.0")
        errors, _ = vcp.validate_piece(piece, "p")
        self.assertTrue(any("schema_version" in e for e in errors))


class TestHigieneRepositorio(unittest.TestCase):
    """No es una prueba del validador (que no puede autenticar personas) sino
    del repositorio: ningún fixture debe contener el nombre real del fundador.
    Ver Fase 1C, Paso 2 y Paso 10.12."""

    def test_no_nombres_reales_en_fixtures(self):
        fixtures_dir = SKILL_ROOT / "fixtures"
        offenders = []
        for path in fixtures_dir.rglob("*.json"):
            text = path.read_text(encoding="utf-8", errors="replace")
            for name in FORBIDDEN_REAL_NAMES:
                if name in text:
                    offenders.append((str(path), name))
        self.assertEqual(offenders, [], f"Nombres reales encontrados en fixtures: {offenders}")

    def test_no_nombres_reales_en_referencias_ni_skill(self):
        for path in [SKILL_ROOT / "SKILL.md", *sorted((SKILL_ROOT / "references").glob("*.md"))]:
            text = path.read_text(encoding="utf-8", errors="replace")
            for name in FORBIDDEN_REAL_NAMES:
                self.assertNotIn(name, text, f"Nombre real {name!r} encontrado en {path}")


if __name__ == "__main__":
    unittest.main()
