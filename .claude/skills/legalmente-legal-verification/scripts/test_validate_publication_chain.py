#!/usr/bin/env python3
"""Pruebas de la cadena post-aprobación (validate-publication-chain.py).

Qué se está protegiendo aquí, en una frase: que **abrir el gate de arte no
autorice publicar**. El gate de arte lo abre una aprobación jurídica humana
firmada sobre el claim packet; la publicación exige, además, una
`PublicationDecision` humana separada y posterior. Esta batería fija esa
separación como invariante ejecutable, no como buena intención documentada.

Invariantes cubiertas (una prueba por invariante, más las de forma):

  1. Un ProductionHandoff exige gate de arte ABIERTO en el claim packet.
  2. El hash aprobado que transporta el handoff debe seguir coincidiendo con
     el hash canónico del claim.
  3. El texto que va a producción debe ser literalmente el aprobado.
  4. La redacción prohibida viaja con el contenido.
  5. No hay publicación sin PublicationDecision humana.
  6. Solo una decisión AUTORIZADA habilita publicar.
  7. Una autorización exige firma completa (decisor, fecha, observaciones).
  8. Una autorización exige QA determinista superado al completo.
  9. No se publica en una plataforma no autorizada por la decisión.
 10. No hay publicación sin Content ID válido.
 11. El recordatorio de medición es published_at + 7 días exactos.
 12. No hay medición sin publicación, ni aprendizaje sin medición.
 13. Los identificadores no se duplican.

Ningún revisor/decisor de prueba lleva nombre real (ver SKILL.md): siempre
REVISOR_FICTICIO_SOLO_PRUEBA.
"""
import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPTS_DIR.parent
SCRIPT = SCRIPTS_DIR / "validate-publication-chain.py"
FIXTURES = SKILL_ROOT / "publication" / "fixtures"
VALIDOS = FIXTURES / "validos"
INVALIDOS = FIXTURES / "invalidos"
PACKET_REL = "publication/fixtures/claim-packet-aprobado.json"

REVISOR_FICTICIO = "REVISOR_FICTICIO_SOLO_PRUEBA"

sys.path.insert(0, str(SCRIPTS_DIR))
import test_validate_claim_packet as tvcp  # noqa: E402

FORBIDDEN_REAL_NAMES = tvcp.FORBIDDEN_REAL_NAMES


def _load(path, name):
    """Importa un script con guiones en el nombre (no es un módulo importable)."""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


vpc = _load(SCRIPT, "validate_publication_chain")
VALIDATOR = vpc.load_validator()


def cadena_valida():
    """Copia mutable de la cadena completa válida de referencia."""
    return json.loads((VALIDOS / "cadena-completa.json").read_text(encoding="utf-8"))


def por_tipo(records, record_type):
    for r in records:
        if r.get("record_type") == record_type:
            return r
    raise AssertionError(f"la cadena de referencia no contiene {record_type}")


def evaluar(records):
    """Valida registros + cadena y devuelve (errores, advertencias)."""
    etiquetados = [(f"mem[{i}]", r) for i, r in enumerate(records)]
    errores, advertencias = [], []
    for label, rec in etiquetados:
        e, w = vpc.validate_record(rec, VALIDATOR, label)
        errores.extend(e)
        advertencias.extend(w)
    ce, cw = vpc.validate_chain(
        [(l, r) for l, r in etiquetados if isinstance(r, dict) and r.get("record_type") in vpc.RECORD_TYPES]
    )
    return errores + ce, advertencias + cw


def ejecutar_script(*paths):
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), *[str(p) for p in paths]],
        capture_output=True,
        text=True,
        cwd=str(SKILL_ROOT),
    )
    return proc


class TestBaseDeReferencia(unittest.TestCase):
    """La cadena de referencia tiene que ser válida; si no, nada más significa nada."""

    def test_la_cadena_completa_de_referencia_es_valida(self):
        errores, _ = evaluar(cadena_valida())
        self.assertEqual(errores, [], f"la cadena de referencia debería ser válida: {errores}")

    def test_el_claim_packet_de_la_fixture_es_valido_y_tiene_gate_abierto(self):
        packet = json.loads((SKILL_ROOT / PACKET_REL).read_text(encoding="utf-8"))
        errores, _ = VALIDATOR.validate_piece(copy.deepcopy(packet), PACKET_REL)
        self.assertEqual(errores, [], f"el claim packet de la fixture debe validar: {errores}")
        self.assertEqual(packet["gate_global_arte"], "ABIERTO")

    def test_ningun_registro_de_fixture_usa_un_nombre_real(self):
        """SKILL.md: jamás una persona real en material de prueba.

        La lista negra se importa de test_validate_claim_packet — este archivo
        no puede escribir los nombres, o se delataría a sí mismo ante la
        comprobación de higiene de scripts.
        """
        for path in sorted(FIXTURES.rglob("*.json")):
            texto = path.read_text(encoding="utf-8")
            for nombre in FORBIDDEN_REAL_NAMES:
                self.assertNotIn(nombre, texto, f"{path} contiene un nombre real prohibido")


class TestSeparacionGateArteVsPublicacion(unittest.TestCase):
    """El corazón del diseño: producir y publicar son dos permisos distintos."""

    def test_gate_de_arte_abierto_no_basta_para_publicar(self):
        """Handoff válido + publicación, sin ninguna decisión humana → inválido."""
        cadena = cadena_valida()
        handoff = por_tipo(cadena, "ProductionHandoff")
        publicacion = por_tipo(cadena, "PublicationRecord")
        errores, _ = evaluar([handoff, publicacion])
        self.assertTrue(
            any("no corresponde a ninguna PublicationDecision" in e for e in errores),
            f"publicar con solo el gate de arte abierto debe fallar: {errores}",
        )

    def test_handoff_exige_gate_de_arte_abierto(self):
        """Invariante 1: no entra en producción una pieza con el gate cerrado."""
        cadena = cadena_valida()
        handoff = por_tipo(cadena, "ProductionHandoff")
        handoff["claim_packet"] = "fixtures/piezas/pieza-1-comodato-mutuo.json"
        handoff["piece_id"] = "pieza-1-comodato-mutuo"
        handoff["claims"] = [
            {
                "claim_id": "pieza-1-claim-1",
                "approved_claim_hash": "0" * 64,
                "approved_text": "irrelevante",
            }
        ]
        errores, _ = evaluar([handoff])
        self.assertTrue(
            any("gate_global_arte" in e and "ABIERTO" in e for e in errores),
            f"un handoff sobre gate cerrado debe fallar: {errores}",
        )

    def test_solo_una_decision_autorizada_habilita_publicar(self):
        """Invariante 6: RECHAZADA o PENDIENTE no autorizan nada."""
        for estado in ("RECHAZADA", "PENDIENTE"):
            with self.subTest(decision=estado):
                cadena = cadena_valida()
                decision = por_tipo(cadena, "PublicationDecision")
                decision["decision"] = estado
                errores, _ = evaluar(cadena)
                self.assertTrue(
                    any("Solo una decisión AUTORIZADA habilita publicar" in e for e in errores),
                    f"decision={estado} no puede habilitar publicación: {errores}",
                )


class TestIntegridadDeLoAprobado(unittest.TestCase):
    """Lo aprobado por un humano no puede mutar camino de producción."""

    def test_hash_incorrecto_en_el_handoff_falla(self):
        """Invariante 2."""
        cadena = cadena_valida()
        handoff = por_tipo(cadena, "ProductionHandoff")
        handoff["claims"][0]["approved_claim_hash"] = "a" * 64
        errores, _ = evaluar([handoff])
        self.assertTrue(
            any("no coincide con el hash canónico" in e for e in errores),
            f"un hash aprobado que no corresponde debe fallar: {errores}",
        )

    def test_hash_con_forma_invalida_falla(self):
        cadena = cadena_valida()
        handoff = por_tipo(cadena, "ProductionHandoff")
        handoff["claims"][0]["approved_claim_hash"] = "no-es-un-hash"
        errores, _ = evaluar([handoff])
        self.assertTrue(
            any("64 hexadecimales" in e for e in errores),
            f"un hash malformado debe fallar: {errores}",
        )

    def test_texto_modificado_tras_la_aprobacion_falla(self):
        """Invariante 3: el texto que va a arte es LITERALMENTE el aprobado."""
        cadena = cadena_valida()
        handoff = por_tipo(cadena, "ProductionHandoff")
        handoff["claims"][0]["approved_text"] += " Siempre y en todo país."
        errores, _ = evaluar([handoff])
        self.assertTrue(
            any("no coincide literalmente" in e.lower() or "NO coincide literalmente" in e for e in errores),
            f"alterar el texto aprobado debe fallar: {errores}",
        )

    def test_la_redaccion_prohibida_debe_viajar_con_el_contenido(self):
        """Invariante 4: la prohibición no se pierde en el traspaso a arte."""
        cadena = cadena_valida()
        handoff = por_tipo(cadena, "ProductionHandoff")
        handoff["redacciones_prohibidas"] = []
        errores, _ = evaluar([handoff])
        self.assertTrue(
            any("redaccion_prohibida" in e for e in errores),
            f"perder la redacción prohibida debe fallar: {errores}",
        )

    def test_claim_inexistente_en_el_packet_falla(self):
        cadena = cadena_valida()
        handoff = por_tipo(cadena, "ProductionHandoff")
        handoff["claims"][0]["claim_id"] = "claim-que-no-existe"
        errores, _ = evaluar([handoff])
        self.assertTrue(
            any("no existe en el claim packet" in e for e in errores),
            f"un claim inexistente debe fallar: {errores}",
        )

    def test_claim_packet_fuera_de_la_skill_falla(self):
        """Fail-closed: no se acepta evidencia de una ruta arbitraria del disco."""
        cadena = cadena_valida()
        handoff = por_tipo(cadena, "ProductionHandoff")
        handoff["claim_packet"] = "../../../etc/passwd"
        errores, _ = evaluar([handoff])
        self.assertTrue(
            any("no resuelve a un archivo real dentro de la skill" in e for e in errores),
            f"una ruta fuera de la skill debe rechazarse: {errores}",
        )


class TestDecisionHumanaDePublicacion(unittest.TestCase):
    """Una autorización a medias no autoriza."""

    def test_autorizacion_exige_firma_completa(self):
        """Invariante 7."""
        for campo, valor, esperado in (
            ("decisor", "   ", "'decisor' identificado no vacío"),
            ("fecha", "27/08/2026", "'fecha' ISO válida"),
            ("observaciones", "", "'observaciones'"),
        ):
            with self.subTest(campo=campo):
                cadena = cadena_valida()
                decision = por_tipo(cadena, "PublicationDecision")
                decision[campo] = valor
                errores, _ = evaluar([decision])
                self.assertTrue(
                    any(esperado in e for e in errores),
                    f"una autorización sin {campo} debe fallar: {errores}",
                )

    def test_autorizacion_exige_advertencia_editorial_verificada(self):
        cadena = cadena_valida()
        decision = por_tipo(cadena, "PublicationDecision")
        decision["advertencia_editorial_verificada"] = False
        errores, _ = evaluar([decision])
        self.assertTrue(
            any("advertencia_editorial_verificada" in e for e in errores),
            f"sin advertencia verificada no se autoriza: {errores}",
        )

    def test_autorizacion_exige_todas_las_comprobaciones_de_qa(self):
        """Invariante 8: cada comprobación determinista, una por una."""
        for check in vpc.REQUIRED_QA_CHECKS:
            with self.subTest(qa=check):
                cadena = cadena_valida()
                decision = por_tipo(cadena, "PublicationDecision")
                decision["qa"][check] = False
                errores, _ = evaluar([decision])
                self.assertTrue(
                    any(check in e for e in errores),
                    f"la comprobación {check} en false debe bloquear la autorización: {errores}",
                )

    def test_autorizacion_sin_qa_declarado_falla(self):
        cadena = cadena_valida()
        decision = por_tipo(cadena, "PublicationDecision")
        decision["qa"] = {}
        errores, _ = evaluar([decision])
        self.assertTrue(
            any("faltan comprobaciones obligatorias" in e for e in errores),
            f"sin QA declarado no se autoriza: {errores}",
        )

    def test_autorizacion_exige_al_menos_una_plataforma(self):
        cadena = cadena_valida()
        decision = por_tipo(cadena, "PublicationDecision")
        decision["plataformas_autorizadas"] = []
        errores, _ = evaluar([decision])
        self.assertTrue(
            any("al menos una plataforma" in e for e in errores),
            f"una autorización sin plataforma debe fallar: {errores}",
        )

    def test_decision_debe_referirse_a_un_handoff_existente(self):
        cadena = cadena_valida()
        decision = por_tipo(cadena, "PublicationDecision")
        decision["handoff_id"] = "HO-QUE-NO-EXISTE"
        errores, _ = evaluar(cadena)
        self.assertTrue(
            any("no corresponde a ningún ProductionHandoff" in e for e in errores),
            f"autorizar sin handoff debe fallar: {errores}",
        )

    def test_una_decision_rechazada_no_exige_firma_completa(self):
        """Rechazar es siempre posible; lo que exige requisitos es autorizar."""
        cadena = cadena_valida()
        decision = por_tipo(cadena, "PublicationDecision")
        decision["decision"] = "RECHAZADA"
        decision["plataformas_autorizadas"] = []
        decision["qa"] = {}
        decision["advertencia_editorial_verificada"] = False
        handoff = por_tipo(cadena, "ProductionHandoff")
        errores, _ = evaluar([handoff, decision])
        self.assertEqual(errores, [], f"un rechazo bien formado debe ser válido: {errores}")


class TestRegistroDePublicacion(unittest.TestCase):

    def test_publicacion_sin_content_id_valido_falla(self):
        """Invariante 10."""
        for valor in ("", "minusculas-no", "con espacio", "AB"):
            with self.subTest(content_id=valor):
                cadena = cadena_valida()
                publicacion = por_tipo(cadena, "PublicationRecord")
                publicacion["content_id"] = valor
                errores, _ = evaluar([publicacion])
                self.assertTrue(
                    any("'content_id' inválido" in e for e in errores),
                    f"content_id {valor!r} debe rechazarse: {errores}",
                )

    def test_publicacion_sin_decision_declarada_falla(self):
        """Invariante 5, a nivel de forma del propio registro."""
        cadena = cadena_valida()
        publicacion = por_tipo(cadena, "PublicationRecord")
        publicacion["publication_decision_id"] = ""
        errores, _ = evaluar([publicacion])
        self.assertTrue(
            any("no se publica sin decisión humana" in e for e in errores),
            f"una publicación sin decisión declarada debe fallar: {errores}",
        )

    def test_publicada_exige_url_real(self):
        for url in ("", "no-es-url", "ftp://example.invalid/x"):
            with self.subTest(url=url):
                cadena = cadena_valida()
                publicacion = por_tipo(cadena, "PublicationRecord")
                publicacion["publication_url"] = url
                errores, _ = evaluar([publicacion])
                self.assertTrue(
                    any("publication_url" in e for e in errores),
                    f"url {url!r} debe rechazarse en una publicación PUBLICADA: {errores}",
                )

    def test_plataforma_no_autorizada_falla(self):
        """Invariante 9."""
        cadena = cadena_valida()
        publicacion = por_tipo(cadena, "PublicationRecord")
        publicacion["platform"] = "una-plataforma-cualquiera"
        errores, _ = evaluar(cadena)
        self.assertTrue(
            any("no está entre las plataformas" in e for e in errores),
            f"publicar fuera de lo autorizado debe fallar: {errores}",
        )

    def test_recordatorio_de_medicion_a_siete_dias_exactos(self):
        """Invariante 11."""
        cadena = cadena_valida()
        publicacion = por_tipo(cadena, "PublicationRecord")
        publicacion["measurement_due_at"] = "2026-09-04"
        errores, _ = evaluar([publicacion])
        self.assertTrue(
            any("measurement_due_at" in e for e in errores),
            f"un recordatorio distinto de +7 días debe fallar: {errores}",
        )

    def test_recordatorio_de_medicion_correcto_no_falla(self):
        cadena = cadena_valida()
        publicacion = por_tipo(cadena, "PublicationRecord")
        publicacion["published_at"] = "2026-12-28"
        publicacion["measurement_due_at"] = "2027-01-04"  # cruza el fin de año
        errores, _ = evaluar([publicacion])
        self.assertFalse(
            any("measurement_due_at" in e for e in errores),
            f"published_at + 7 días debe aceptarse aunque cruce el año: {errores}",
        )


class TestMedicionYAprendizaje(unittest.TestCase):

    def test_medicion_sin_publicacion_falla(self):
        """Invariante 12 (primera mitad)."""
        cadena = cadena_valida()
        medicion = por_tipo(cadena, "MeasurementRecord")
        errores, _ = evaluar([medicion])
        self.assertTrue(
            any("No se miden publicaciones que no constan" in e for e in errores),
            f"medir sin publicación debe fallar: {errores}",
        )

    def test_aprendizaje_sin_medicion_falla(self):
        """Invariante 12 (segunda mitad)."""
        cadena = [r for r in cadena_valida() if r.get("record_type") != "MeasurementRecord"]
        errores, _ = evaluar(cadena)
        self.assertTrue(
            any("sin ningún MeasurementRecord" in e for e in errores),
            f"aprender sin medir debe fallar: {errores}",
        )

    def test_no_se_inventan_metricas(self):
        cadena = cadena_valida()
        medicion = por_tipo(cadena, "MeasurementRecord")
        medicion["metrics"]["metrica_no_declarada"] = 999
        errores, _ = evaluar(cadena)
        self.assertTrue(
            any("no declaradas en 'available_metrics'" in e for e in errores),
            f"una métrica no declarada disponible debe fallar: {errores}",
        )

    def test_metrica_declarada_disponible_pero_ausente_falla(self):
        cadena = cadena_valida()
        medicion = por_tipo(cadena, "MeasurementRecord")
        medicion["available_metrics"].append("retencion")
        errores, _ = evaluar(cadena)
        self.assertTrue(
            any("declaradas disponibles pero ausentes" in e for e in errores),
            f"declarar una métrica y no aportarla debe fallar: {errores}",
        )


class TestUnicidadYForma(unittest.TestCase):

    def test_handoff_id_duplicado_falla(self):
        """Invariante 13."""
        cadena = cadena_valida()
        handoff = por_tipo(cadena, "ProductionHandoff")
        errores, _ = evaluar([handoff, copy.deepcopy(handoff)])
        self.assertTrue(
            any("handoff_id duplicado" in e for e in errores),
            f"dos handoffs con el mismo id deben fallar: {errores}",
        )

    def test_decision_id_duplicado_falla(self):
        cadena = cadena_valida()
        decision = por_tipo(cadena, "PublicationDecision")
        errores, _ = evaluar([decision, copy.deepcopy(decision)])
        self.assertTrue(
            any("decision_id duplicado" in e for e in errores),
            f"dos decisiones con el mismo id deben fallar: {errores}",
        )

    def test_publicacion_duplicada_en_la_misma_plataforma_falla(self):
        cadena = cadena_valida()
        publicacion = por_tipo(cadena, "PublicationRecord")
        errores, _ = evaluar([publicacion, copy.deepcopy(publicacion)])
        self.assertTrue(
            any("publicación duplicada" in e for e in errores),
            f"registrar dos veces la misma pieza en la misma plataforma debe fallar: {errores}",
        )

    def test_record_type_desconocido_falla(self):
        errores, _ = evaluar([{"record_type": "Publicar", "schema_version": "1.0"}])
        self.assertTrue(
            any("'record_type' inválido" in e for e in errores),
            f"un record_type inventado debe rechazarse: {errores}",
        )

    def test_schema_version_incorrecta_falla(self):
        cadena = cadena_valida()
        handoff = por_tipo(cadena, "ProductionHandoff")
        handoff["schema_version"] = "0.9"
        errores, _ = evaluar([handoff])
        self.assertTrue(
            any("schema_version" in e for e in errores),
            f"una schema_version distinta debe rechazarse: {errores}",
        )

    def test_campos_obligatorios_ausentes_fallan(self):
        cadena = cadena_valida()
        for tipo in ("ProductionHandoff", "PublicationDecision", "PublicationRecord",
                     "MeasurementRecord", "Learning"):
            registro = por_tipo(cadena_valida(), tipo)
            for campo in list(registro.keys()):
                if campo in ("record_type", "schema_version"):
                    continue
                with self.subTest(tipo=tipo, campo=campo):
                    mutilado = copy.deepcopy(registro)
                    del mutilado[campo]
                    errores, _ = evaluar([mutilado])
                    self.assertTrue(
                        any(f"'{campo}'" in e for e in errores),
                        f"quitar {campo} de {tipo} debe producir un error: {errores}",
                    )


class TestFixturesEnDisco(unittest.TestCase):
    """Las fixtures del repositorio deben comportarse como dicen sus carpetas."""

    def test_hay_fixturas_en_ambas_carpetas(self):
        self.assertTrue(list(VALIDOS.glob("*.json")), "no hay fixtures válidas")
        self.assertTrue(list(INVALIDOS.glob("*.json")), "no hay fixtures inválidas")

    def test_todas_las_fixtures_validas_pasan(self):
        for path in sorted(VALIDOS.glob("*.json")):
            with self.subTest(fixture=path.name):
                proc = ejecutar_script(path)
                self.assertEqual(proc.returncode, 0, f"{path.name} debía pasar:\n{proc.stdout}{proc.stderr}")

    def test_todas_las_fixtures_invalidas_son_rechazadas(self):
        for path in sorted(INVALIDOS.glob("*.json")):
            with self.subTest(fixture=path.name):
                proc = ejecutar_script(path)
                self.assertEqual(proc.returncode, 1, f"{path.name} debía ser rechazada:\n{proc.stdout}{proc.stderr}")
                self.assertIn("[CADENA INVÁLIDA]", proc.stdout)


class TestCLI(unittest.TestCase):

    def test_sin_argumentos_devuelve_error(self):
        proc = ejecutar_script()
        self.assertEqual(proc.returncode, 1)

    def test_archivo_ilegible_devuelve_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            roto = Path(tmp) / "roto.json"
            roto.write_text("{esto no es json", encoding="utf-8")
            proc = ejecutar_script(roto)
            self.assertEqual(proc.returncode, 1)
            self.assertIn("no se pudo leer/parsear", proc.stdout)

    def test_la_salida_recuerda_la_separacion_de_permisos(self):
        proc = ejecutar_script(VALIDOS / "cadena-completa.json")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("habilita producción", proc.stdout)
        self.assertIn("AUTORIZADA habilita publicar", proc.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
