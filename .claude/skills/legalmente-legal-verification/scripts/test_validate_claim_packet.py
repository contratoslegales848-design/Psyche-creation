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
    """Por defecto es una fuente Nivel 1 VÁLIDA contra el registro único
    (boe-es / España): organismo canónico y 'registro_oficial_id' coherentes
    con el hostname por defecto. Cualquier prueba que cambie 'url', 'tipo_fuente'
    o 'jurisdicciones_cubiertas' a algo que ya no sea boe.es/NORMA_OFICIAL/España
    debe también pasar 'registro_oficial_id' (y a menudo 'organismo_autor')
    coherentes, o dejar explícito que se está probando una incoherencia."""
    f = {
        "id": "f1", "tipo_fuente": "NORMA_OFICIAL", "titulo": "Ley X",
        "organismo_autor": "Agencia Estatal BOE", "url": "https://www.boe.es/algo",
        "identificador_bibliografico": None, "fecha_consulta": TODAY,
        "localizador": "art. 1", "jurisdicciones_cubiertas": ["España"],
        "verificacion_fuente": base_verificacion(),
        "registro_oficial_id": "boe-es",
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
        "schema_version": "4.0", "piece_id": "p1", "claims": claims,
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
        f = base_fuente(url="https://mexico.justia.com/x", registro_oficial_id=None)
        self.assertNotEqual(vcp.compute_fuente_nivel(f), vcp.NIVEL_1_CONFIRMADO)
        self.assertEqual(vcp.compute_fuente_nivel(f), vcp.NIVEL_2_DECLARADO_NO_VERIFICADO)

    def test_hostname_real_pero_texto_no_consultado_no_es_nivel_1(self):
        f = base_fuente(verificacion_fuente=base_verificacion(texto=False))
        self.assertNotEqual(vcp.compute_fuente_nivel(f), vcp.NIVEL_1_CONFIRMADO)

    def test_hostname_real_pero_vigencia_no_comprobada_no_es_nivel_1(self):
        f = base_fuente(verificacion_fuente=base_verificacion(vigencia=False))
        self.assertNotEqual(vcp.compute_fuente_nivel(f), vcp.NIVEL_1_CONFIRMADO)

    def test_secundaria_es_nivel_3(self):
        f = base_fuente(tipo_fuente="SECUNDARIA_ESPECIALIZADA", registro_oficial_id=None,
                         verificacion_fuente=base_verificacion(False, False, False))
        self.assertEqual(vcp.compute_fuente_nivel(f), vcp.NIVEL_3_ACADEMICA_SECUNDARIA)

    def test_drive_es_nivel_4(self):
        f = base_fuente(tipo_fuente="DRIVE_INTERNO", registro_oficial_id=None,
                         verificacion_fuente=base_verificacion(False, False, False))
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
            base_fuente(id="f-es", url="https://www.boe.es/x", jurisdicciones_cubiertas=["España"]),
            base_fuente(id="f-mx", url="https://www.diputados.gob.mx/x", jurisdicciones_cubiertas=["México"],
                        organismo_autor="Congreso de la Unión (México)", registro_oficial_id="diputados-gob-mx"),
            base_fuente(id="f-ar", url="https://servicios.infoleg.gob.ar/x", jurisdicciones_cubiertas=["Argentina"],
                        organismo_autor="InfoLEG", registro_oficial_id="infoleg-gob-ar"),
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
        # tipo secundaria: no aplica el cruce hostname<->jurisdicción (eso se
        # prueba aparte en TestHostnameJurisdiccion); aquí lo que se prueba es
        # que jurisdicciones_revisadas no acepta una fuente de otro país.
        f = base_fuente(id="f-mx", tipo_fuente="SECUNDARIA_ESPECIALIZADA", url="https://blog-mx.example.com/x",
                         registro_oficial_id=None,
                         jurisdicciones_cubiertas=["México"], verificacion_fuente=base_verificacion(False, False, False))
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
        fuentes = [
            base_fuente(id="f1", url="https://www.diputados.gob.mx/x", jurisdicciones_cubiertas=["México"],
                        organismo_autor="Congreso de la Unión (México)", registro_oficial_id="diputados-gob-mx"),
            base_fuente(id="f2", tipo_fuente="NORMA_OFICIAL", url="https://www.funcionpublica.gov.co/x",
                        jurisdicciones_cubiertas=["Colombia"], organismo_autor="Función Pública Colombia",
                        registro_oficial_id="funcionpublica-gov-co"),
        ]
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


class TestHostnameJurisdiccion(unittest.TestCase):
    """Fase 1D (Paso 3) + Fase 1D.1 (Paso 6): una fuente oficial nacional no
    puede autoafirmar cobertura de países ajenos a su organismo — ahora
    verificado contra el registro único (references/official-source-registry.json)
    vía 'registro_oficial_id', no contra una jurisdicción suelta."""

    def test_boe_declarando_mexico_es_error(self):
        f = base_fuente(url="https://www.boe.es/x", jurisdicciones_cubiertas=["México"], registro_oficial_id="boe-es")
        errors, _ = vcp.validate_fuente(f, "f")
        self.assertTrue(any("país/ámbito ajeno a lo autorizado" in e for e in errors))

    def test_boe_declarando_cuatro_paises_es_error(self):
        f = base_fuente(url="https://www.boe.es/x", jurisdicciones_cubiertas=["España", "México", "Argentina", "Perú"],
                         registro_oficial_id="boe-es")
        errors, _ = vcp.validate_fuente(f, "f")
        self.assertTrue(any("país/ámbito ajeno a lo autorizado" in e for e in errors))

    def test_diputados_mx_declarando_colombia_es_error(self):
        f = base_fuente(url="https://www.diputados.gob.mx/x", jurisdicciones_cubiertas=["Colombia"],
                         organismo_autor="Congreso de la Unión (México)", registro_oficial_id="diputados-gob-mx")
        errors, _ = vcp.validate_fuente(f, "f")
        self.assertTrue(any("país/ámbito ajeno a lo autorizado" in e for e in errors))

    def test_boe_declarando_solo_espana_es_valido(self):
        f = base_fuente(url="https://www.boe.es/x", jurisdicciones_cubiertas=["España"])
        errors, _ = vcp.validate_fuente(f, "f")
        self.assertEqual(errors, [])

    def test_academica_comparada_varios_paises_no_eleva_a_nivel_1(self):
        """Una fuente académica/secundaria SÍ puede declarar varios países —
        el registro único solo restringe fuentes OFICIALES — pero nunca
        puede alcanzar Nivel 1."""
        f = base_fuente(tipo_fuente="ACADEMICA_IDENTIFICABLE", url="https://revista-academica.edu/x",
                         registro_oficial_id=None,
                         jurisdicciones_cubiertas=["España", "México", "Argentina"],
                         verificacion_fuente=base_verificacion(False, False, False))
        errors, _ = vcp.validate_fuente(f, "f")
        self.assertEqual(errors, [])
        self.assertNotEqual(vcp.compute_fuente_nivel(f), vcp.NIVEL_1_CONFIRMADO)
        self.assertEqual(vcp.compute_fuente_nivel(f), vcp.NIVEL_3_ACADEMICA_SECUNDARIA)

    def test_supranacional_ambito_valido(self):
        f = base_fuente(url="https://eur-lex.europa.eu/x", jurisdicciones_cubiertas=["Unión Europea"],
                         organismo_autor="EUR-Lex", registro_oficial_id="eur-lex-europa-eu")
        errors, _ = vcp.validate_fuente(f, "f")
        self.assertEqual(errors, [])

    def test_supranacional_ambito_invalido(self):
        f = base_fuente(url="https://eur-lex.europa.eu/x", jurisdicciones_cubiertas=["México"],
                         organismo_autor="EUR-Lex", registro_oficial_id="eur-lex-europa-eu")
        errors, _ = vcp.validate_fuente(f, "f")
        self.assertTrue(any("país/ámbito ajeno a lo autorizado" in e for e in errors))

    def test_hostname_desconocido_no_se_cruza(self):
        """Un hostname que no está en el registro único, y una fuente que no
        declara 'registro_oficial_id', falla cerrado por la vía del nivel
        (Nivel 2) con una ADVERTENCIA — no un error estructural duro,
        preservando el comportamiento fail-closed ya establecido en la
        Fase 1D para dominios genuinamente desconocidos."""
        f = base_fuente(url="https://www.algun-ministerio-no-listado.gob.uy/x", jurisdicciones_cubiertas=["Uruguay"],
                         organismo_autor="Ministerio no listado", registro_oficial_id=None)
        errors, warnings = vcp.validate_fuente(f, "f")
        self.assertEqual(errors, [])  # dominio desconocido -> advertencia, no error
        self.assertTrue(warnings)
        self.assertNotEqual(vcp.compute_fuente_nivel(f), vcp.NIVEL_1_CONFIRMADO)


class TestCapaCComparadaCobertura(unittest.TestCase):
    """Fase 1D, Paso 4: cobertura COMPLETA por país en Capa C con varias
    jurisdicciones — no 'alguna fuente cubre alguno de los países'."""

    def _fuente_mx(self):
        return base_fuente(id="f-mx", url="https://www.diputados.gob.mx/x", jurisdicciones_cubiertas=["México"],
                            organismo_autor="Congreso de la Unión (México)", registro_oficial_id="diputados-gob-mx")

    def _fuente_co(self):
        return base_fuente(id="f-co", tipo_fuente="NORMA_OFICIAL",
                            url="https://www.funcionpublica.gov.co/x", jurisdicciones_cubiertas=["Colombia"],
                            organismo_autor="Función Pública Colombia", registro_oficial_id="funcionpublica-gov-co")

    def test_dos_paises_solo_fuente_mexicana_estado_alto_es_error(self):
        c = base_claim(alcance="CAPA_C_NACIONAL", jurisdiccion=["México", "Colombia"],
                        estado="APTO_PARA_NARRATIVA", fuentes=[self._fuente_mx()])
        errors, _, max_estado, _ = vcp.validate_claim(c, "c")
        self.assertTrue(any("excede lo que las fuentes permiten" in e for e in errors))
        self.assertEqual(max_estado, "REQUIERE_INVESTIGACION")

    def test_dos_paises_solo_fuente_colombiana_estado_alto_es_error(self):
        c = base_claim(alcance="CAPA_C_NACIONAL", jurisdiccion=["México", "Colombia"],
                        estado="APTO_PARA_NARRATIVA", fuentes=[self._fuente_co()])
        errors, _, max_estado, _ = vcp.validate_claim(c, "c")
        self.assertTrue(any("excede lo que las fuentes permiten" in e for e in errors))
        self.assertEqual(max_estado, "REQUIERE_INVESTIGACION")

    def test_una_valida_una_no_verificada_estado_alto_es_error(self):
        f_co_no_verificada = self._fuente_co()
        f_co_no_verificada["verificacion_fuente"] = base_verificacion(False, False, False)
        c = base_claim(alcance="CAPA_C_NACIONAL", jurisdiccion=["México", "Colombia"],
                        estado="APTO_PARA_NARRATIVA", fuentes=[self._fuente_mx(), f_co_no_verificada])
        errors, _, max_estado, _ = vcp.validate_claim(c, "c")
        self.assertTrue(any("excede lo que las fuentes permiten" in e for e in errors))
        self.assertEqual(max_estado, "APTO_CON_MATICES")

    def test_una_valida_una_no_verificada_estado_matices_es_valido(self):
        f_co_no_verificada = self._fuente_co()
        f_co_no_verificada["verificacion_fuente"] = base_verificacion(False, False, False)
        c = base_claim(alcance="CAPA_C_NACIONAL", jurisdiccion=["México", "Colombia"],
                        estado="APTO_CON_MATICES", confianza="media", fuentes=[self._fuente_mx(), f_co_no_verificada])
        errors, _, max_estado, _ = vcp.validate_claim(c, "c")
        self.assertEqual(errors, [])

    def test_ambas_fuentes_nivel_1_es_apto_para_narrativa(self):
        c = base_claim(alcance="CAPA_C_NACIONAL", jurisdiccion=["México", "Colombia"],
                        estado="APTO_PARA_NARRATIVA", fuentes=[self._fuente_mx(), self._fuente_co()])
        errors, _, max_estado, _ = vcp.validate_claim(c, "c")
        self.assertEqual(errors, [])
        self.assertEqual(max_estado, "APTO_PARA_NARRATIVA")

    def test_jurisdicciones_duplicadas_es_error(self):
        c = base_claim(alcance="CAPA_C_NACIONAL", jurisdiccion=["México", "México"],
                        estado="REQUIERE_INVESTIGACION", fuentes=[])
        errors, _, _, _ = vcp.validate_claim(c, "c")
        self.assertTrue(any("duplicado" in e for e in errors))

    def test_jurisdiccion_lista_vacia_es_error(self):
        c = base_claim(alcance="CAPA_C_NACIONAL", jurisdiccion=[], estado="REQUIERE_INVESTIGACION", fuentes=[])
        errors, _, _, _ = vcp.validate_claim(c, "c")
        self.assertTrue(any("no puede estar vacía" in e or "'jurisdiccion' debe ser string" in e for e in errors))

    def test_sin_fuentes_todavia_requiere_investigacion_es_valido(self):
        """No es un error declarar honestamente REQUIERE_INVESTIGACION para
        una Capa C con países sin fuentes todavía — el error es solo cuando
        el estado declarado excede lo que las fuentes permiten."""
        c = base_claim(alcance="CAPA_C_NACIONAL", jurisdiccion=["México", "Colombia"],
                        estado="REQUIERE_INVESTIGACION", confianza="baja", fuentes=[])
        errors, _, max_estado, _ = vcp.validate_claim(c, "c")
        self.assertEqual(errors, [])
        self.assertEqual(max_estado, "REQUIERE_INVESTIGACION")


class TestCapaBPaisCoverage(unittest.TestCase):
    """Fase 1E: mismo techo POR PAÍS que ya protegía a Capa C (Fase 1D,
    Paso 4) ahora también protege a CAPA_B_VARIABLE (y a cualquier otro
    alcance con 'jurisdiccion' declarada). Antes, un claim CAPA_B_VARIABLE
    con varios países solo necesitaba UNA fuente Nivel 1 en CUALQUIER país
    para declararse APTO_PARA_NARRATIVA — una fuente mexicana Nivel 1 podía
    'elevar' a España o Argentina sin que esos países tuvieran cobertura
    propia. Reproducido con un paquete sintético fuera de este archivo antes
    de la corrección (ver PR de la corrección); estas pruebas fijan el
    comportamiento correcto de forma permanente."""

    def _fuente_mx_nivel1(self):
        return base_fuente(id="f-mx", url="https://www.diputados.gob.mx/x", jurisdicciones_cubiertas=["México"],
                            organismo_autor="Congreso de la Unión (México)", registro_oficial_id="diputados-gob-mx")

    def _fuente_es_nivel1(self):
        return base_fuente(id="f-es", url="https://www.boe.es/x", jurisdicciones_cubiertas=["España"],
                            organismo_autor="Agencia Estatal BOE", registro_oficial_id="boe-es")

    def _fuente_ar_nivel2(self):
        """Fuente argentina consultada directamente (booleanos en true) pero
        SIN 'registro_oficial_id', con un hostname deliberadamente sintético
        y sin entrada propia en el registro oficial cerrado — nunca alcanza
        Nivel 1 aunque sus tres booleanos de verificación estén en true.
        (Antes de la verificación externa de argentina.gob.ar registrada en
        official-source-registry.json como 'argentina-gob-ar-normativa', este
        fixture usaba precisamente ese hostname como ejemplo de "no
        registrado"; tras esa alta legítima, dejó de serlo, así que aquí se
        usa un hostname distinto que sigue sin tener entrada.)"""
        return base_fuente(id="f-ar", url="https://www.mininterior.gob.ar/normativa/x",
                            jurisdicciones_cubiertas=["Argentina"], organismo_autor="InfoLEG",
                            registro_oficial_id=None)

    # --- 1. México Nivel 1 + España Nivel 1 + Argentina Nivel 2 --------------

    def test_tres_paises_mexico_espana_nivel1_argentina_nivel2_no_puede_ser_apto_para_narrativa(self):
        c = base_claim(
            alcance="CAPA_B_VARIABLE", jurisdiccion=["México", "España", "Argentina"],
            variaciones_materiales="Formulación distinta por país (prueba).",
            estado="APTO_PARA_NARRATIVA",
            fuentes=[self._fuente_mx_nivel1(), self._fuente_es_nivel1(), self._fuente_ar_nivel2()],
        )
        errors, _, max_estado, _ = vcp.validate_claim(c, "c")
        self.assertTrue(any("excede lo que las fuentes permiten" in e for e in errors))
        self.assertEqual(max_estado, "APTO_CON_MATICES")
        self.assertNotEqual(max_estado, "APTO_PARA_NARRATIVA")

    def test_tres_paises_mexico_espana_nivel1_argentina_nivel2_matices_es_valido(self):
        """El mismo escenario, pero declarando el techo real (APTO_CON_MATICES)
        en vez de forzar APTO_PARA_NARRATIVA, es válido sin errores."""
        c = base_claim(
            alcance="CAPA_B_VARIABLE", jurisdiccion=["México", "España", "Argentina"],
            variaciones_materiales="Formulación distinta por país (prueba).",
            estado="APTO_CON_MATICES", confianza="media",
            fuentes=[self._fuente_mx_nivel1(), self._fuente_es_nivel1(), self._fuente_ar_nivel2()],
        )
        errors, _, max_estado, _ = vcp.validate_claim(c, "c")
        self.assertEqual(errors, [])
        self.assertEqual(max_estado, "APTO_CON_MATICES")

    # --- 2. Jurisdicción declarada sin fuente propia -------------------------

    def test_jurisdiccion_declarada_sin_fuente_propia_queda_requiere_investigacion(self):
        c = base_claim(
            alcance="CAPA_B_VARIABLE", jurisdiccion=["México", "España", "Argentina"],
            variaciones_materiales="Formulación distinta por país (prueba).",
            estado="REQUIERE_INVESTIGACION", confianza="baja",
            # Argentina no tiene NINGUNA fuente que la cubra.
            fuentes=[self._fuente_mx_nivel1(), self._fuente_es_nivel1()],
        )
        errors, _, max_estado, _ = vcp.validate_claim(c, "c")
        self.assertEqual(errors, [])
        self.assertEqual(max_estado, "REQUIERE_INVESTIGACION")

    def test_jurisdiccion_declarada_sin_fuente_propia_estado_alto_es_error(self):
        c = base_claim(
            alcance="CAPA_B_VARIABLE", jurisdiccion=["México", "España", "Argentina"],
            variaciones_materiales="Formulación distinta por país (prueba).",
            estado="APTO_PARA_NARRATIVA",
            fuentes=[self._fuente_mx_nivel1(), self._fuente_es_nivel1()],
        )
        errors, _, max_estado, _ = vcp.validate_claim(c, "c")
        self.assertTrue(any("excede lo que las fuentes permiten" in e for e in errors))
        self.assertEqual(max_estado, "REQUIERE_INVESTIGACION")

    # --- 3. Una fuente NO puede cubrir un país que su registro no permite ----

    def test_fuente_mexicana_no_puede_declarar_que_cubre_argentina(self):
        """Una fuente con 'registro_oficial_id' de México (diputados-gob-mx,
        que solo autoriza 'México' en 'jurisdicciones') no puede declarar en
        'jurisdicciones_cubiertas' que también respalda a Argentina — el
        registro hostname→jurisdicción lo rechaza como incoherencia."""
        f_mx_que_dice_cubrir_argentina = base_fuente(
            id="f-mx-falso", url="https://www.diputados.gob.mx/x",
            jurisdicciones_cubiertas=["México", "Argentina"],
            organismo_autor="Congreso de la Unión (México)", registro_oficial_id="diputados-gob-mx",
        )
        errors, _ = vcp.validate_fuente(f_mx_que_dice_cubrir_argentina, "f")
        self.assertTrue(any("jurisdicciones_cubiertas" in e and "ajeno" in e for e in errors))

    def test_fuente_mexicana_con_jurisdicciones_cubiertas_falsas_no_cuenta_para_argentina(self):
        """Aunque una fuente mexicana declarara (incoherentemente)
        'jurisdicciones_cubiertas' incluyendo Argentina, compute_ceiling_by_countries
        de todos modos exige revisar esa incoherencia — el claim entero debe
        fallar con error estructural antes de llegar siquiera a calcular el
        techo, nunca aceptar la cobertura falsa."""
        f_mx_que_dice_cubrir_argentina = base_fuente(
            id="f-mx-falso", url="https://www.diputados.gob.mx/x",
            jurisdicciones_cubiertas=["México", "Argentina"],
            organismo_autor="Congreso de la Unión (México)", registro_oficial_id="diputados-gob-mx",
        )
        c = base_claim(
            alcance="CAPA_B_VARIABLE", jurisdiccion=["México", "Argentina"],
            variaciones_materiales="Formulación distinta por país (prueba).",
            estado="APTO_PARA_NARRATIVA", fuentes=[f_mx_que_dice_cubrir_argentina],
        )
        errors, _, _, _ = vcp.validate_claim(c, "c")
        self.assertTrue(any("ajeno" in e for e in errors))

    # --- 4. Todas las jurisdicciones cubiertas conserva el techo ------------

    def test_tres_paises_todos_nivel1_conserva_apto_para_narrativa(self):
        # Fuente argentina genuinamente Nivel 1: infoleg-gob-ar SÍ tiene
        # entrada propia en el registro oficial cerrado (a diferencia de
        # argentina.gob.ar, que no la tiene) — no se toca el registro, solo
        # se usa una entrada que ya existía antes de este cambio.
        f_ar_nivel1 = base_fuente(id="f-ar-1", url="https://servicios.infoleg.gob.ar/x",
                                   jurisdicciones_cubiertas=["Argentina"],
                                   organismo_autor="InfoLEG",
                                   registro_oficial_id="infoleg-gob-ar")
        c = base_claim(
            alcance="CAPA_B_VARIABLE", jurisdiccion=["México", "España", "Argentina"],
            variaciones_materiales="Formulación distinta por país (prueba).",
            estado="APTO_PARA_NARRATIVA",
            fuentes=[self._fuente_mx_nivel1(), self._fuente_es_nivel1(), f_ar_nivel1],
        )
        errors, _, max_estado, _ = vcp.validate_claim(c, "c")
        self.assertEqual(errors, [])
        self.assertEqual(max_estado, "APTO_PARA_NARRATIVA")

    # --- 5. Aprobación humana no abre el gate si falta cobertura ------------

    def test_aprobacion_humana_no_abre_gate_si_falta_cobertura_de_pais(self):
        c = approved_claim(
            alcance="CAPA_B_VARIABLE", jurisdiccion=["México", "España", "Argentina"],
            variaciones_materiales="Formulación distinta por país (prueba).",
            fuentes=[self._fuente_mx_nivel1(), self._fuente_es_nivel1(), self._fuente_ar_nivel2()],
        )
        # approved_claim() ya deja estado=APTO_PARA_NARRATIVA (heredado de
        # base_claim) y gate_arte=ABIERTO con hash correcto — pero Argentina
        # solo alcanza Nivel 2, así que el techo real es APTO_CON_MATICES.
        errors, _, max_estado, gate = vcp.validate_claim(c, "c")
        self.assertEqual(max_estado, "APTO_CON_MATICES")
        self.assertTrue(any("excede lo que las fuentes permiten" in e for e in errors))
        self.assertEqual(gate, "CERRADO")

    # --- 7 (de la tarea). Lista de tres países ya cubierta arriba -----------
    # (test_tres_paises_mexico_espana_nivel1_argentina_nivel2_no_puede_ser_apto_para_narrativa
    # y test_tres_paises_todos_nivel1_conserva_apto_para_narrativa usan tres
    # países explícitamente.)

    # --- 8. Una sola jurisdicción correctamente sustentada: sin regresión ---

    def test_una_sola_jurisdiccion_capa_b_correctamente_sustentada_sin_regresion(self):
        c = base_claim(
            alcance="CAPA_B_VARIABLE", jurisdiccion="España",
            variaciones_materiales="Variación interna de una sola jurisdicción (prueba).",
            estado="APTO_PARA_NARRATIVA", fuentes=[self._fuente_es_nivel1()],
        )
        errors, _, max_estado, _ = vcp.validate_claim(c, "c")
        self.assertEqual(errors, [])
        self.assertEqual(max_estado, "APTO_PARA_NARRATIVA")

    def test_capa_c_sigue_usando_el_mismo_techo_por_pais_sin_regresion(self):
        """Capa C con dos países y ambos Nivel 1 debe seguir sosteniendo
        APTO_PARA_NARRATIVA exactamente igual que antes de este cambio — la
        protección de Capa C no se reduce."""
        c = base_claim(
            alcance="CAPA_C_NACIONAL", jurisdiccion=["México", "España"],
            estado="APTO_PARA_NARRATIVA",
            fuentes=[self._fuente_mx_nivel1(), self._fuente_es_nivel1()],
        )
        errors, _, max_estado, _ = vcp.validate_claim(c, "c")
        self.assertEqual(errors, [])
        self.assertEqual(max_estado, "APTO_PARA_NARRATIVA")


class TestArgentinaGobArNormativa(unittest.TestCase):
    """Migración segura de fuentes argentinas (2026-08-27): registro
    'argentina-gob-ar-normativa' en official-source-registry.json, restringido
    por hostname ('argentina.gob.ar', exacto + subdominios) + organismo exacto
    ('Argentina.gob.ar — Normativa / Presidencia de la Nación') + tipo_fuente
    (solo NORMA_OFICIAL). El schema no admite path_prefix — deuda técnica
    documentada en la propia entrada del registro, no cubierta por estas
    pruebas de código (no hay mecanismo que probar)."""

    ORGANISMO = "Argentina.gob.ar — Normativa / Presidencia de la Nación"
    URL = "https://www.argentina.gob.ar/normativa/nacional/ley-26994-235975/actualizacion"

    def _fuente_ar(self, **overrides):
        f = base_fuente(
            id="f-ar-normativa", url=self.URL, organismo_autor=self.ORGANISMO,
            jurisdicciones_cubiertas=["Argentina"], registro_oficial_id="argentina-gob-ar-normativa",
        )
        f.update(overrides)
        return f

    # 1. Registro correcto + organismo correcto + NORMA_OFICIAL + tres booleanos true -> Nivel 1.
    def test_registro_organismo_tipo_y_booleanos_correctos_alcanza_nivel_1(self):
        f = self._fuente_ar()
        errors, warnings = vcp.validate_fuente(f, "f")
        self.assertEqual(errors, [])
        self.assertEqual(vcp.compute_fuente_nivel(f), vcp.NIVEL_1_CONFIRMADO)

    # 2. Registro correcto + booleanos false -> Nivel 2 (nunca Nivel 1 solo por el registro).
    def test_registro_correcto_con_booleanos_false_se_queda_en_nivel_2(self):
        f = self._fuente_ar(verificacion_fuente=base_verificacion(origen=False, texto=False, vigencia=False))
        errors, _ = vcp.validate_fuente(f, "f")
        self.assertEqual(errors, [])
        self.assertEqual(vcp.compute_fuente_nivel(f), vcp.NIVEL_2_DECLARADO_NO_VERIFICADO)

    # 3. Organismo incorrecto -> rechazo.
    def test_organismo_incorrecto_rechazado(self):
        f = self._fuente_ar(organismo_autor="InfoLEG")
        errors, _ = vcp.validate_fuente(f, "f")
        self.assertTrue(any("no coincide, tras normalizar, con el organismo canónico" in e for e in errors))

    # 4. Tipo no permitido -> rechazo.
    def test_tipo_fuente_no_permitido_rechazado(self):
        f = self._fuente_ar(tipo_fuente="JURISPRUDENCIA_OFICIAL")
        errors, _ = vcp.validate_fuente(f, "f")
        self.assertTrue(any("no tiene permitido el tipo de fuente" in e for e in errors))

    # 5. ID incorrecto/ausente para hostname registrado -> rechazo.
    def test_registro_oficial_id_ausente_para_hostname_registrado_rechazado(self):
        f = self._fuente_ar(registro_oficial_id=None)
        errors, _ = vcp.validate_fuente(f, "f")
        self.assertTrue(any("corresponde al organismo registrado" in e and "argentina-gob-ar-normativa" in e for e in errors))
        self.assertNotEqual(vcp.compute_fuente_nivel(f), vcp.NIVEL_1_CONFIRMADO)

    def test_registro_oficial_id_incorrecto_para_hostname_registrado_rechazado(self):
        f = self._fuente_ar(registro_oficial_id="boe-es")
        errors, _ = vcp.validate_fuente(f, "f")
        self.assertTrue(any("no corresponde al hostname real de la URL" in e for e in errors))


class TestPilotClaimPacketsReales(unittest.TestCase):
    """Prueba de regresión automatizada (2026-08-27): valida las 3 piezas
    reales del piloto dentro de la propia suite unittest, no solo mediante
    ejecución manual de validate-claim-packet.py — para que un cambio de
    registro (u otro) que rompa alguna de ellas falle la suite
    automáticamente."""

    PILOT_DIR = Path(__file__).resolve().parent.parent / "pilot" / "claim-packets"

    def test_las_tres_piezas_reales_pasan_validacion_estructural(self):
        piezas = sorted(self.PILOT_DIR.glob("*.json"))
        self.assertEqual(len(piezas), 3, f"se esperaban 3 piezas reales, se encontraron {len(piezas)}: {piezas}")
        for path in piezas:
            with self.subTest(pieza=path.name):
                piece = json.loads(path.read_text(encoding="utf-8"))
                errors, _ = vcp.validate_piece(piece, path.name)
                self.assertEqual(errors, [], f"{path.name} no debería tener errores estructurales: {errors}")


class TestHashCompleto(unittest.TestCase):
    """Fase 1D, Paso 5: el hash de aprobación cubre TODO el claim excepto
    revision_humana y gate_arte — cualquier otro cambio lo invalida."""

    def _cambio_invalida(self, mutate_fn):
        c = approved_claim()
        mutate_fn(c)
        errors, _, _, gate = vcp.validate_claim(c, "c")
        self.assertTrue(any("no coincide con el hash recalculado" in e for e in errors), f"no detectó el cambio: {errors}")
        self.assertEqual(gate, "CERRADO")

    def test_cambiar_titulo_de_fuente_invalida(self):
        self._cambio_invalida(lambda c: c["fuentes"][0].__setitem__("titulo", "Título cambiado tras aprobar"))

    def test_cambiar_organismo_autor_invalida(self):
        # Con el registro único, cambiar 'organismo_autor' a un valor que ya
        # no coincide con ningún alias de 'boe-es' dispara PRIMERO el error
        # de coherencia de registro (más específico) — el hash ya ni se
        # llega a comparar porque validate_fuente corta antes. Sigue siendo
        # una detección correcta de la manipulación post-aprobación, solo
        # que por un motivo más preciso que "el hash no coincide".
        c = approved_claim()
        c["fuentes"][0]["organismo_autor"] = "Otro organismo que no está en el registro"
        errors, _, _, gate = vcp.validate_claim(c, "c")
        self.assertTrue(errors)
        self.assertNotEqual(gate, "ABIERTO")

    def test_cambiar_organismo_autor_a_otro_alias_del_mismo_registro_invalida_hash(self):
        """Si el nuevo 'organismo_autor' SÍ es un alias válido del mismo
        'registro_oficial_id' (no dispara el error de coherencia de
        registro), el cambio todavía debe invalidar la aprobación por la vía
        del hash — el contenido aprobado fue uno específico, no 'cualquier
        alias equivalente'."""
        self._cambio_invalida(lambda c: c["fuentes"][0].__setitem__("organismo_autor", "BOE"))

    def test_cambiar_fecha_consulta_invalida(self):
        self._cambio_invalida(lambda c: c["fuentes"][0].__setitem__("fecha_consulta", "2020-01-01"))

    def test_cambiar_tipo_de_claim_invalida(self):
        self._cambio_invalida(lambda c: c.__setitem__("tipo", "cita"))

    def test_cambiar_ubicacion_invalida(self):
        self._cambio_invalida(lambda c: c.__setitem__("ubicacion", "caption"))

    def test_cambiar_confianza_invalida(self):
        self._cambio_invalida(lambda c: c.__setitem__("confianza", "media"))

    def test_cambiar_riesgo_asesoria_invalida(self):
        self._cambio_invalida(lambda c: c.__setitem__("riesgo_asesoria", "alto"))

    def test_cambiar_platform_review_status_invalida(self):
        # Este cambio dispara además review_allows_gate()=False, así que el
        # motivo reportado es la incoherencia de gate, no el mensaje de hash
        # — igual de válido: el punto es que la aprobación deja de sostenerse.
        c = approved_claim()
        c["platform_review"] = base_review(required=True, status="PENDIENTE")
        errors, _, _, gate = vcp.validate_claim(c, "c")
        self.assertTrue(errors)
        self.assertEqual(gate, "CERRADO")

    def test_cambiar_reformulacion_propuesta_invalida(self):
        self._cambio_invalida(lambda c: c.__setitem__("reformulacion_propuesta", {"texto": "algo nuevo tras aprobar", "verificada": False, "nuevo_claim_id": None}))

    def test_url_y_localizador_sin_cambios_hash_estable(self):
        """Control: si NADA cambia, el hash sigue coincidiendo y el gate
        permanece abierto."""
        c = approved_claim()
        errors, _, _, gate = vcp.validate_claim(c, "c")
        self.assertEqual(errors, [])
        self.assertEqual(gate, "ABIERTO")

    def test_cambiar_registro_oficial_id_invalida_hash(self):
        """Fase 1D.1, Paso 5: 'registro_oficial_id' es un campo más de la
        fuente y por tanto forma parte del hash igual que 'titulo' u
        'organismo_autor' — sustituir el organismo aprobado por otro
        (aunque ambos existan en el registro) invalida la aprobación."""
        c = approved_claim()
        c["fuentes"][0]["registro_oficial_id"] = "poderjudicial-es"
        errors, _, _, gate = vcp.validate_claim(c, "c")
        self.assertTrue(errors)
        self.assertNotEqual(gate, "ABIERTO")


class TestRegistroOficialUnico(unittest.TestCase):
    """Fase 1D.1: toda validación de hostname↔organismo↔tipo_fuente↔
    jurisdicción para fuentes oficiales se deriva de UN ÚNICO registro
    (references/official-source-registry.json vía REGISTRY/REGISTRY_BY_ID),
    nunca de listas manuales paralelas. Cubre el checklist completo del
    Paso 7 del encargo de Fase 1D.1."""

    # 1-2. Migración de schema_version a v4.0 -----------------------------

    def test_schema_v4_es_aceptada(self):
        c = base_claim(estado="APTO_PARA_NARRATIVA")
        piece = base_piece([c])
        errors, _ = vcp.validate_piece(piece, "p")
        self.assertEqual(errors, [])

    def test_schema_v3_es_rechazada_con_mensaje_de_migracion(self):
        c = base_claim(estado="APTO_PARA_NARRATIVA")
        piece = base_piece([c], schema_version="3.0")
        errors, _ = vcp.validate_piece(piece, "p")
        self.assertTrue(any("ya NO es una versión vigente" in e and "\"4.0\"" in e for e in errors))

    # 3-6. BOE / Diputados MX: organismo y tipo permitido -----------------

    def test_boe_organismo_mexicano_rechazado(self):
        f = base_fuente(tipo_fuente="JURISPRUDENCIA_OFICIAL", organismo_autor="Suprema Corte de Justicia de México",
                         registro_oficial_id="boe-es")
        errors, _ = vcp.validate_fuente(f, "f")
        self.assertTrue(any("no coincide, tras normalizar, con el organismo canónico" in e for e in errors))

    def test_boe_tipo_incorrecto_rechazado(self):
        f = base_fuente(tipo_fuente="JURISPRUDENCIA_OFICIAL")  # organismo/registro por defecto SÍ son BOE
        errors, _ = vcp.validate_fuente(f, "f")
        self.assertTrue(any("no tiene permitido el tipo de fuente" in e for e in errors))

    def test_boe_todo_correcto_aceptado(self):
        f = base_fuente()  # NORMA_OFICIAL + boe-es + Agencia Estatal BOE + España, todo coherente por defecto
        errors, _ = vcp.validate_fuente(f, "f")
        self.assertEqual(errors, [])
        self.assertEqual(vcp.compute_fuente_nivel(f), vcp.NIVEL_1_CONFIRMADO)

    def test_diputados_mx_organismo_colombiano_rechazado(self):
        f = base_fuente(url="https://www.diputados.gob.mx/x", organismo_autor="Función Pública Colombia",
                         jurisdicciones_cubiertas=["México"], registro_oficial_id="diputados-gob-mx")
        errors, _ = vcp.validate_fuente(f, "f")
        self.assertTrue(any("no coincide, tras normalizar, con el organismo canónico" in e for e in errors))

    # 7-8. registro_oficial_id inexistente / hostname que no coincide -----

    def test_registro_oficial_id_inexistente_rechazado(self):
        f = base_fuente(registro_oficial_id="organismo-que-no-existe")
        errors, _ = vcp.validate_fuente(f, "f")
        self.assertTrue(any("no existe en el registro oficial" in e for e in errors))

    def test_registro_oficial_id_hostname_no_coincide_rechazado(self):
        """registro_oficial_id existe de verdad (diputados-gob-mx), pero la
        URL de la fuente es boe.es — el hostname no resuelve a esa misma
        entrada."""
        f = base_fuente(url="https://www.boe.es/x", registro_oficial_id="diputados-gob-mx",
                         organismo_autor="Congreso de la Unión (México)")
        errors, _ = vcp.validate_fuente(f, "f")
        self.assertTrue(any("no corresponde al hostname real de la URL" in e for e in errors))

    # 9. Alias oficial válido ----------------------------------------------

    def test_alias_oficial_valido_aceptado(self):
        f = base_fuente(organismo_autor="BOE")  # alias, no el nombre canónico
        errors, _ = vcp.validate_fuente(f, "f")
        self.assertEqual(errors, [])

    # 10. Organismo coincidente solo por subcadena ---------------------------

    def test_organismo_subcadena_rechazado(self):
        f = base_fuente(
            tipo_fuente="JURISPRUDENCIA_OFICIAL", url="https://www.scjn.gob.mx/x",
            organismo_autor="Suprema Corte de Justicia de la Nación (México) — Sala Segunda",
            jurisdicciones_cubiertas=["México"], registro_oficial_id="scjn-gob-mx",
        )
        errors, _ = vcp.validate_fuente(f, "f")
        self.assertTrue(any("no coincide, tras normalizar, con el organismo canónico" in e for e in errors))

    # 11. Dominio desconocido no alcanza Nivel 1 ---------------------------

    def test_dominio_desconocido_no_alcanza_nivel_1(self):
        f = base_fuente(url="https://ministerio-no-listado.example/x", registro_oficial_id=None,
                         organismo_autor="Ministerio no listado")
        errors, warnings = vcp.validate_fuente(f, "f")
        self.assertEqual(errors, [])
        self.assertTrue(warnings)
        self.assertNotEqual(vcp.compute_fuente_nivel(f), vcp.NIVEL_1_CONFIRMADO)

    # 12. Hostname específico gana sobre el genérico gob.mx -----------------

    def test_hostname_especifico_gana_sobre_generico(self):
        entry = vcp.match_registry_entry_for_url("https://www.dof.gob.mx/algo", vcp.REGISTRY)
        self.assertIsNotNone(entry)
        self.assertEqual(entry["id"], "dof-gob-mx")

    # 13-14. gob.mx genérico: AUTORIDAD_PUBLICA_OFICIAL sí, NORMA/JURISPRUDENCIA no --

    def test_gobmx_generico_autoridad_publica_aceptado(self):
        f = base_fuente(
            tipo_fuente="AUTORIDAD_PUBLICA_OFICIAL", url="https://www.gob.mx/sat",
            organismo_autor="Gobierno de México", jurisdicciones_cubiertas=["México"],
            registro_oficial_id="gob-mx-generico",
        )
        errors, _ = vcp.validate_fuente(f, "f")
        self.assertEqual(errors, [])

    def test_gobmx_generico_como_norma_rechazado(self):
        f = base_fuente(
            tipo_fuente="NORMA_OFICIAL", url="https://www.gob.mx/sat",
            organismo_autor="Gobierno de México", jurisdicciones_cubiertas=["México"],
            registro_oficial_id="gob-mx-generico",
        )
        errors, _ = vcp.validate_fuente(f, "f")
        self.assertTrue(any("no tiene permitido el tipo de fuente" in e for e in errors))

    # 15. Registro ausente/inválido/duplicado falla cerrado -----------------

    def test_registro_ausente_o_invalido_falla_cerrado(self):
        vacio = vcp.load_official_source_registry(Path("/ruta/que/no/existe/registry.json"))
        self.assertEqual(vacio, {"registry_version": None, "sources": []})

    def test_registro_ids_duplicados_falla_cerrado(self):
        registro_corrupto = {
            "registry_version": "corrupto",
            "sources": [
                {"id": "dup", "hostnames": ["a.example"], "organismo_canonico": "A",
                 "organismo_aliases": [], "jurisdicciones": ["X"],
                 "tipos_fuente_permitidos": ["NORMA_OFICIAL"], "ambito": "NACIONAL"},
                {"id": "dup", "hostnames": ["b.example"], "organismo_canonico": "B",
                 "organismo_aliases": [], "jurisdicciones": ["Y"],
                 "tipos_fuente_permitidos": ["NORMA_OFICIAL"], "ambito": "NACIONAL"},
            ],
        }
        by_id = vcp._build_registry_by_id(registro_corrupto)
        self.assertNotIn("dup", by_id)  # ninguna de las dos entradas duplicadas queda usable

    # 18. Los cierres de Capa C y hash de la Fase 1D siguen funcionando -----

    def test_capa_c_ceiling_sigue_siendo_minimo_entre_paises(self):
        """Confirma que compute_ceiling_by_countries/compute_capa_c_ceiling
        (cierre del Bypass D, Fase 1D) no se rompieron con la migración al
        registro único: un país sin fuente propia sigue topando el techo en
        REQUIERE_INVESTIGACION aunque el otro país tenga una fuente Nivel 1."""
        fuentes = [base_fuente(id="f-mx", url="https://www.diputados.gob.mx/x", jurisdicciones_cubiertas=["México"],
                                organismo_autor="Congreso de la Unión (México)", registro_oficial_id="diputados-gob-mx")]
        ceiling = vcp.compute_capa_c_ceiling(["México", "Colombia"], fuentes)
        self.assertEqual(ceiling, "REQUIERE_INVESTIGACION")


class TestUrlCanonica(unittest.TestCase):
    """Fase 1D.2, Paso 1: una única función canónica (parse_official_url)
    valida y extrae el hostname de una URL — fail-closed ante cualquier
    ambigüedad (barra invertida, userinfo, espacios/control, puerto
    inválido), en vez de reimplementar la normalización WHATWG."""

    # Regresión directa del bypass reportado por Codex ------------------

    def test_bypass_userinfo_con_barra_invertida_rechazado(self):
        """'https://evil.example\\@boe.es/falso': un parser ingenuo (o el
        'urllib.parse' de Python sin este endurecimiento) calcula el host
        como 'boe.es'; un navegador WHATWG lo interpreta como
        'evil.example' (la barra invertida es separador de host en
        esquemas especiales). La ambigüedad en sí misma se rechaza."""
        ok, hostname, reason = vcp.parse_official_url("https://evil.example\\@boe.es/falso")
        self.assertFalse(ok)
        self.assertIsNone(hostname)
        self.assertIn("barra invertida", reason)

    def test_bypass_userinfo_con_barra_invertida_fuente_completa_rechazada(self):
        f = base_fuente(url="https://evil.example\\@boe.es/falso")
        errors, _ = vcp.validate_fuente(f, "f")
        self.assertTrue(any("no es una URL http/https válida" in e for e in errors))

    # Barra invertida en cualquier otra posición -------------------------

    def test_barra_invertida_en_path_rechazada(self):
        ok, hostname, reason = vcp.parse_official_url("https://boe.es/algo\\raro")
        self.assertFalse(ok)
        self.assertIn("barra invertida", reason)

    # Userinfo (sin barra invertida) --------------------------------------

    def test_userinfo_simple_rechazado(self):
        ok, hostname, reason = vcp.parse_official_url("https://usuario:clave@boe.es/x")
        self.assertFalse(ok)
        self.assertIn("userinfo", reason)

    # Puerto inválido -------------------------------------------------------

    def test_puerto_fuera_de_rango_rechazado(self):
        ok, hostname, reason = vcp.parse_official_url("https://boe.es:99999999/x")
        self.assertFalse(ok)
        self.assertIn("puerto", reason)

    def test_puerto_no_numerico_rechazado(self):
        ok, hostname, reason = vcp.parse_official_url("https://boe.es:abc/x")
        self.assertFalse(ok)
        self.assertIn("puerto", reason)

    def test_puerto_valido_aceptado(self):
        ok, hostname, reason = vcp.parse_official_url("https://boe.es:443/x")
        self.assertTrue(ok)
        self.assertEqual(hostname, "boe.es")

    # Espacios y caracteres de control --------------------------------------

    def test_espacio_en_url_rechazado(self):
        ok, hostname, reason = vcp.parse_official_url("https://boe.es/algo con espacio")
        self.assertFalse(ok)
        self.assertIn("espacios", reason)

    def test_caracter_de_control_rechazado(self):
        ok, hostname, reason = vcp.parse_official_url("https://boe.es/algo\x00raro")
        self.assertFalse(ok)
        self.assertIn("espacios o caracteres de control", reason)

    # Esquema --------------------------------------------------------------

    def test_esquema_no_http_rechazado(self):
        ok, hostname, reason = vcp.parse_official_url("ftp://boe.es/x")
        self.assertFalse(ok)
        self.assertIn("esquema", reason)

    # Dominio falso (subcadena / subdominio spoofing) — regresión Fase 1C --

    def test_dominio_falso_boe_es_evil_com_rechazado_por_extract_hostname(self):
        self.assertNotEqual(vcp.extract_hostname("https://boe.es.evil.com/x"), "boe.es")

    def test_dominio_falso_notboe_es_rechazado_por_extract_hostname(self):
        self.assertNotEqual(vcp.extract_hostname("https://notboe.es/x"), "boe.es")

    # URLs legítimas de boe.es — deben seguir aceptándose sin cambios -----

    def test_boe_es_url_legitima_simple_aceptada(self):
        ok, hostname, reason = vcp.parse_official_url("https://www.boe.es/buscar/act.php?id=BOE-A-1889-4763")
        self.assertTrue(ok)
        self.assertEqual(hostname, "www.boe.es")
        self.assertTrue(vcp.hostname_matches_official("https://www.boe.es/buscar/act.php?id=BOE-A-1889-4763"))

    def test_boe_es_url_con_fragmento_y_parametros_aceptada(self):
        ok, hostname, reason = vcp.parse_official_url("https://www.boe.es/eli/es/rd/1889/07/24/(1)/con#a1740")
        self.assertTrue(ok)
        self.assertEqual(hostname, "www.boe.es")

    def test_boe_es_sin_www_aceptada(self):
        ok, hostname, reason = vcp.parse_official_url("https://boe.es/x")
        self.assertTrue(ok)
        self.assertEqual(hostname, "boe.es")

    # Fuente completa con URL legítima sigue alcanzando Nivel 1 -------------

    def test_fuente_boe_url_legitima_sigue_siendo_nivel_1(self):
        f = base_fuente()  # boe.es real, organismo/registro coherentes por defecto
        self.assertEqual(vcp.compute_fuente_nivel(f), vcp.NIVEL_1_CONFIRMADO)


class TestFuenteOficialSinUrl(unittest.TestCase):
    """Fase 1D.2, Paso 2: una fuente oficial sin 'url' (solo
    'identificador_bibliografico') puede ser estructuralmente válida, pero
    nunca alcanza Nivel 1, genera advertencia, y nunca abre el gate —
    incluso si 'registro_oficial_id'/'organismo_autor'/verificación parecen
    completamente coherentes entre sí (el bypass reportado por Codex:
    autoafirmaciones sin ningún hostname real que verificar)."""

    def _fuente_oficial_sin_url(self, **overrides):
        f = base_fuente(
            url=None, identificador_bibliografico="Editorial Aranzadi, edición 2024, ISBN 000-0-00-000000-0",
        )
        f.update(overrides)
        return f

    def test_oficial_sin_url_nunca_es_nivel_1(self):
        f = self._fuente_oficial_sin_url()
        self.assertNotEqual(vcp.compute_fuente_nivel(f), vcp.NIVEL_1_CONFIRMADO)
        self.assertEqual(vcp.compute_fuente_nivel(f), vcp.NIVEL_2_DECLARADO_NO_VERIFICADO)

    def test_oficial_sin_url_genera_advertencia_no_error(self):
        f = self._fuente_oficial_sin_url()
        errors, warnings = vcp.validate_fuente(f, "f")
        self.assertEqual(errors, [])
        self.assertTrue(any("sin 'url'" in w for w in warnings))

    def test_oficial_sin_url_estructuralmente_valida_en_nivel_correspondiente(self):
        """Declarada honestamente APTO_CON_MATICES (no APTO_PARA_NARRATIVA),
        la pieza completa SÍ valida (exit lógico 0 vía validate_claim sin
        errores) — 'estructuralmente válida' no significa 'nunca aceptada'."""
        f = self._fuente_oficial_sin_url()
        c = base_claim(alcance="CAPA_C_NACIONAL", jurisdiccion="España", estado="APTO_CON_MATICES",
                        confianza="media", fuentes=[f])
        errors, _, max_estado, _ = vcp.validate_claim(c, "c")
        self.assertEqual(errors, [])
        self.assertEqual(max_estado, "APTO_CON_MATICES")

    def test_oficial_sin_url_no_puede_declararse_apto_para_narrativa(self):
        f = self._fuente_oficial_sin_url()
        c = base_claim(alcance="CAPA_C_NACIONAL", jurisdiccion="España", estado="APTO_PARA_NARRATIVA", fuentes=[f])
        errors, _, max_estado, _ = vcp.validate_claim(c, "c")
        self.assertTrue(any("excede lo que las fuentes permiten" in e for e in errors))
        self.assertEqual(max_estado, "APTO_CON_MATICES")

    def test_oficial_sin_url_nunca_abre_el_gate(self):
        """Incluso con una 'aprobación' simulada (hash correcto, revisor
        ficticio), el gate no puede abrirse porque el estado 'APTO_PARA_NARRATIVA'
        ya es inalcanzable — se detiene antes de llegar siquiera a evaluar el hash."""
        f = self._fuente_oficial_sin_url()
        c = base_claim(alcance="CAPA_C_NACIONAL", jurisdiccion="España", estado="APTO_PARA_NARRATIVA",
                        fuentes=[f], gate_arte="ABIERTO")
        c["revision_humana"] = {
            "estado": "APROBADO", "revisor": REVISOR_FICTICIO, "fecha": TODAY,
            "observaciones": None, "contenido_hash_sha256": vcp.compute_content_hash(c),
        }
        errors, _, _, gate = vcp.validate_claim(c, "c")
        self.assertTrue(errors)
        self.assertNotEqual(gate, "ABIERTO")

    def test_fuente_academica_fisica_sin_url_sigue_permitida(self):
        """Control: las fuentes NO oficiales (académicas/secundarias/Drive)
        nunca pasaron por 'evaluate_fuente_registry' — su techo (Nivel 3/4)
        es independiente de tener o no 'url', y no cambia en esta fase."""
        f = base_fuente(tipo_fuente="ACADEMICA_IDENTIFICABLE", registro_oficial_id=None,
                         url=None, identificador_bibliografico="Editorial X, 2020, ISBN 111-1-11-111111-1",
                         verificacion_fuente=base_verificacion(False, False, False))
        self.assertEqual(vcp.compute_fuente_nivel(f), vcp.NIVEL_3_ACADEMICA_SECUNDARIA)


if __name__ == "__main__":
    unittest.main()
