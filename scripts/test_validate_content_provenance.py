#!/usr/bin/env python3
"""Pruebas de la procedencia del contenido renderizable.

Qué se protege: que nada llegue al renderizador como pieza publicable sin un
origen verificable. Antes, `content/*.json` solo validaba forma — cualquier JSON
bien formado se renderizaba, sin ningún claim packet detrás.

Se prueba en las dos direcciones:
  - lo gobernado debe demostrar su procedencia (handoff, hashes, capa jurídica);
  - lo que legítimamente NO lleva claim jurídico (cita histórica, formato de
    marca) conserva una ruta válida, con motivo tipificado y responsable.

Y una frontera que no se cruza: un artefacto de producción válido NO autoriza
publicar. Publicar sigue exigiendo una PublicationDecision humana.

Ningún revisor de prueba lleva nombre real (ver SKILL.md).
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
REPO_ROOT = SCRIPTS_DIR.parent
SCRIPT = SCRIPTS_DIR / "validate-content-provenance.py"
SKILL_ROOT = REPO_ROOT / ".claude" / "skills" / "legalmente-legal-verification"
PACKET_REL = "publication/fixtures/claim-packet-aprobado.json"

REVISOR_FICTICIO = "REVISOR_FICTICIO_SOLO_PRUEBA"


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


vcp = _load(SCRIPT, "validate_content_provenance")
CLAIM_MOD, CHAIN_MOD = vcp.load_validators()

PACKET = json.loads((SKILL_ROOT / PACKET_REL).read_text(encoding="utf-8"))
CLAIM = PACKET["claims"][0]
CLAIM_ID = CLAIM["claim_id"]
CLAIM_HASH = CLAIM["revision_humana"]["contenido_hash_sha256"]
CLAIM_TEXT = CLAIM["texto_exacto"]
CLAIM_LAYER = CLAIM["alcance"]
PROHIBIDA = CLAIM["redaccion_prohibida"]

CONTENT_ID = "LM-PROV-FIXTURE-001"


def handoff(**over):
    r = {
        "record_type": "ProductionHandoff",
        "schema_version": "1.0",
        "handoff_id": "HO-PROV-001",
        "content_id": CONTENT_ID,
        "piece_id": PACKET["piece_id"],
        "claim_packet": PACKET_REL,
        "claims": [
            {
                "claim_id": CLAIM_ID,
                "approved_claim_hash": CLAIM_HASH,
                "approved_text": CLAIM_TEXT,
            }
        ],
        "jurisdiccion": "Panhispánica / comparada",
        "alcance": CLAIM_LAYER,
        "advertencia_editorial": (
            "Contenido educativo de divulgación jurídica comparada. No es asesoría legal."
        ),
        "redacciones_prohibidas": [PROHIBIDA],
        "status": "APROBADO_QA",
        "creado_en": "2026-08-27",
    }
    r.update(over)
    return r


def taxonomia(**over):
    t = {
        "materia": "Civil",
        "submateria": "Contratos",
        "concepto": "Comodato frente a mutuo",
        "situacion_humana": "Prestar algo y no saber qué hay que devolver",
        "content_type": "DIFERENCIA",
    }
    t.update(over)
    return t


def artefacto_gobernado(**proc_over):
    proc = {
        "modo": "GOBERNADO",
        "content_id": CONTENT_ID,
        "publicable": True,
        "handoff_id": "HO-PROV-001",
        "piece_id": PACKET["piece_id"],
        "claims": [{"claim_id": CLAIM_ID, "approved_claim_hash": CLAIM_HASH}],
        "jurisdiction_layer": CLAIM_LAYER,
        "production_status": "APROBADO_QA",
    }
    proc.update(proc_over)
    return {
        "id": "prov-fixture",
        "titulo": "Comodato y mutuo",
        "frase": CLAIM_TEXT,
        "remate": "Derecho civil comparado",
        "marca": "LegalMente",
        "imagen": "assets/images/ejemplo.jpg",
        "audio": None,
        "duracionSegundos": 10,
        "procedencia": proc,
        "taxonomia": taxonomia(),
    }


def artefacto_no_aplica(**proc_over):
    proc = {
        "modo": "NO_APLICA",
        "content_id": "LM-CITA-HISTORICA-001",
        "publicable": True,
        "jurisdiction_layer": "NO_APLICA",
        "motivo_no_aplica": "CITA_HISTORICA",
        "justificacion_no_aplica": (
            "Máxima del derecho romano de dominio histórico: no enuncia una regla "
            "vigente de ningún ordenamiento, por lo que no hay afirmación jurídica "
            "que verificar contra fuente oficial."
        ),
        "autorizado_por": REVISOR_FICTICIO,
        "fecha_autorizacion": "2026-08-27",
    }
    proc.update(proc_over)
    return {
        "id": "cita-historica",
        "titulo": "Dormientibus non succurrit ius",
        "frase": "El derecho no favorece a quien duerme sobre sus derechos",
        "remate": "Máxima del Derecho Romano",
        "marca": "LegalMente",
        "imagen": "assets/images/ejemplo.jpg",
        "audio": None,
        "duracionSegundos": 10,
        "procedencia": proc,
        "taxonomia": taxonomia(materia="Historia del derecho",
                               submateria="Máximas romanas",
                               concepto="Dormientibus non succurrit ius",
                               content_type="MAXIMA"),
    }


class ProvenanceTestCase(unittest.TestCase):
    """Base con un directorio de handoffs aislado, para no tocar los reales."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._records = Path(self._tmp.name) / "records"
        self._records.mkdir()
        self._orig_records = vcp.RECORDS_DIR
        vcp.RECORDS_DIR = self._records
        self.addCleanup(self._restore)

    def _restore(self):
        vcp.RECORDS_DIR = self._orig_records
        self._tmp.cleanup()

    def escribir_handoff(self, rec):
        (self._records / f"{rec['handoff_id']}.json").write_text(
            json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def evaluar(self, artefactos, con_handoff=True):
        if con_handoff:
            self.escribir_handoff(handoff())
        handoffs, errores = vcp.load_handoffs(CHAIN_MOD)
        etiquetados = [(f"mem[{i}]", a) for i, a in enumerate(artefactos)]
        for label, art in etiquetados:
            errores.extend(vcp.validate_artifact(art, label, handoffs, CLAIM_MOD, CHAIN_MOD))
        errores.extend(vcp.validate_duplicates(etiquetados))
        return errores


class TestRutaGobernada(ProvenanceTestCase):

    def test_artefacto_gobernado_completo_es_valido(self):
        """Invariante 10: la cadena válida completa sigue pasando."""
        self.assertEqual(self.evaluar([artefacto_gobernado()]), [])

    def test_pieza_gobernada_sin_handoff_falla(self):
        """Invariante 6."""
        errores = self.evaluar([artefacto_gobernado()], con_handoff=False)
        self.assertTrue(any("no corresponde a ningún ProductionHandoff" in e for e in errores),
                        f"{errores}")

    def test_handoff_invalido_no_da_procedencia(self):
        """Invariante 4: un handoff que no valida no se indexa siquiera."""
        self.escribir_handoff(handoff(claims=[{
            "claim_id": CLAIM_ID,
            "approved_claim_hash": "0" * 64,
            "approved_text": CLAIM_TEXT,
        }]))
        handoffs, errores = vcp.load_handoffs(CHAIN_MOD)
        errores.extend(vcp.validate_artifact(artefacto_gobernado(), "mem[0]",
                                             handoffs, CLAIM_MOD, CHAIN_MOD))
        self.assertTrue(any("NO es válido" in e or "no coincide" in e for e in errores), f"{errores}")

    def test_hash_incoherente_en_el_artefacto_falla(self):
        """Invariante 5."""
        art = artefacto_gobernado()
        art["procedencia"]["claims"][0]["approved_claim_hash"] = "a" * 64
        errores = self.evaluar([art])
        self.assertTrue(any("no coincide con el que transporta el handoff" in e for e in errores),
                        f"{errores}")

    def test_hash_malformado_falla(self):
        art = artefacto_gobernado()
        art["procedencia"]["claims"][0]["approved_claim_hash"] = "no-es-un-hash"
        errores = self.evaluar([art])
        self.assertTrue(any("64 hexadecimales" in e for e in errores), f"{errores}")

    def test_claim_que_no_viaja_en_el_handoff_falla(self):
        art = artefacto_gobernado()
        art["procedencia"]["claims"][0]["claim_id"] = "claim-ajeno"
        errores = self.evaluar([art])
        self.assertTrue(any("no viaja en el handoff" in e for e in errores), f"{errores}")

    def test_capa_jurisdiccional_reetiquetada_falla(self):
        """La jurisdicción no se reetiqueta al pasar a producción."""
        art = artefacto_gobernado(jurisdiction_layer="CAPA_C_NACIONAL")
        errores = self.evaluar([art])
        self.assertTrue(any("no coincide con el alcance del claim" in e for e in errores), f"{errores}")

    def test_content_id_distinto_del_handoff_falla(self):
        art = artefacto_gobernado(content_id="LM-OTRO-ID-999")
        errores = self.evaluar([art])
        self.assertTrue(any("no coincide" in e and "handoff" in e for e in errores), f"{errores}")

    def test_handoff_no_aprobado_por_qa_no_habilita(self):
        self.escribir_handoff(handoff(status="EN_PRODUCCION"))
        handoffs, errores = vcp.load_handoffs(CHAIN_MOD)
        errores.extend(vcp.validate_artifact(artefacto_gobernado(), "mem[0]",
                                             handoffs, CLAIM_MOD, CHAIN_MOD))
        self.assertTrue(any("APROBADO_QA" in e for e in errores), f"{errores}")

    def test_gobernado_sin_taxonomia_falla(self):
        art = artefacto_gobernado()
        del art["taxonomia"]
        errores = self.evaluar([art])
        self.assertTrue(any("taxonomia" in e for e in errores), f"{errores}")


class TestRutaNoAplica(ProvenanceTestCase):
    """Lo que legítimamente no lleva claim jurídico conserva una ruta válida."""

    def test_pieza_no_aplica_legitima_es_valida(self):
        """Invariante 7."""
        self.assertEqual(self.evaluar([artefacto_no_aplica()]), [])

    def test_no_aplica_sin_motivo_tipificado_falla(self):
        errores = self.evaluar([artefacto_no_aplica(motivo_no_aplica="PORQUE_SI")])
        self.assertTrue(any("tipificado" in e for e in errores), f"{errores}")

    def test_no_aplica_sin_responsable_falla(self):
        errores = self.evaluar([artefacto_no_aplica(autorizado_por="")])
        self.assertTrue(any("autorizado_por" in e for e in errores), f"{errores}")

    def test_no_aplica_sin_justificacion_suficiente_falla(self):
        errores = self.evaluar([artefacto_no_aplica(justificacion_no_aplica="No aplica.")])
        self.assertTrue(any("justificacion_no_aplica" in e for e in errores), f"{errores}")

    def test_no_aplica_no_puede_declarar_capa_juridica(self):
        errores = self.evaluar([artefacto_no_aplica(jurisdiction_layer="CAPA_A_TRANSVERSAL")])
        self.assertTrue(any("jurisdiction_layer" in e for e in errores), f"{errores}")


class TestModoYFormaBasica(ProvenanceTestCase):

    def test_artefacto_sin_procedencia_falla(self):
        art = artefacto_gobernado()
        del art["procedencia"]
        errores = self.evaluar([art])
        self.assertTrue(any("falta el objeto 'procedencia'" in e for e in errores), f"{errores}")

    def test_modo_desconocido_falla(self):
        errores = self.evaluar([artefacto_gobernado(modo="LO_QUE_SEA")])
        self.assertTrue(any("'modo' inválido" in e for e in errores), f"{errores}")

    def test_content_id_invalido_falla(self):
        for valor in ("", "minusculas", "con espacio", "AB"):
            with self.subTest(content_id=valor):
                errores = self.evaluar([artefacto_gobernado(content_id=valor)])
                self.assertTrue(any("content_id" in e for e in errores), f"{errores}")

    def test_ejemplo_tecnico_no_puede_ser_publicable(self):
        art = artefacto_gobernado(modo="EJEMPLO_TECNICO", publicable=True)
        errores = self.evaluar([art])
        self.assertTrue(any("EJEMPLO_TECNICO" in e for e in errores), f"{errores}")

    def test_ejemplo_tecnico_no_publicable_es_valido(self):
        art = {
            "id": "ejemplo-tecnico",
            "procedencia": {
                "modo": "EJEMPLO_TECNICO",
                "content_id": "LM-EJEMPLO-999",
                "publicable": False,
                "jurisdiction_layer": "NO_APLICA",
            },
        }
        self.assertEqual(self.evaluar([art]), [])


class TestAntiDuplicados(ProvenanceTestCase):

    def test_content_id_duplicado_falla(self):
        """Invariante 8."""
        errores = self.evaluar([artefacto_gobernado(), artefacto_gobernado()])
        self.assertTrue(any("content_id duplicado" in e for e in errores), f"{errores}")

    def test_misma_frase_con_otro_id_falla(self):
        a = artefacto_no_aplica()
        b = copy.deepcopy(a)
        b["id"] = "cita-historica-2"
        b["procedencia"]["content_id"] = "LM-CITA-HISTORICA-002"
        b["taxonomia"]["concepto"] = "Otro concepto distinto"
        # Misma frase, solo cambian mayúsculas, tildes y signos.
        b["frase"] = "EL DERECHO NO FAVORECE A QUIEN DUERME SOBRE SUS DERECHOS!!!"
        errores = self.evaluar([a, b])
        self.assertTrue(any("es la misma pieza con otro ID" in e for e in errores), f"{errores}")

    def test_misma_casilla_de_taxonomia_falla(self):
        a = artefacto_no_aplica()
        b = copy.deepcopy(a)
        b["id"] = "otra"
        b["procedencia"]["content_id"] = "LM-CITA-HISTORICA-003"
        b["frase"] = "Una formulación completamente distinta de la misma idea."
        errores = self.evaluar([a, b])
        self.assertTrue(any("casilla de taxonomía" in e for e in errores), f"{errores}")

    def test_id_de_composicion_duplicado_falla(self):
        a = artefacto_no_aplica()
        b = copy.deepcopy(a)
        b["procedencia"]["content_id"] = "LM-CITA-HISTORICA-004"
        b["frase"] = "Otra frase distinta."
        b["taxonomia"]["concepto"] = "Otro concepto"
        errores = self.evaluar([a, b])
        self.assertTrue(any("id de composición duplicado" in e for e in errores), f"{errores}")

    def test_la_huella_ignora_tildes_mayusculas_y_signos(self):
        self.assertEqual(
            vcp.normalize_fingerprint("¿Prescripción, o CADUCIDAD?"),
            vcp.normalize_fingerprint("prescripcion o caducidad"),
        )

    def test_la_huella_no_confunde_textos_distintos(self):
        self.assertNotEqual(
            vcp.normalize_fingerprint("El comodato se devuelve idéntico."),
            vcp.normalize_fingerprint("El mutuo se devuelve equivalente."),
        )


class TestFronteraConLaPublicacion(ProvenanceTestCase):
    """Un artefacto de producción válido NO autoriza publicar."""

    def test_produccion_valida_no_autoriza_publicacion(self):
        """Invariante 9."""
        self.assertEqual(self.evaluar([artefacto_gobernado()]), [],
                         "el artefacto de producción es válido...")
        # ...y sin embargo publicar sigue exigiendo decisión humana.
        publicacion = {
            "record_type": "PublicationRecord",
            "schema_version": "1.0",
            "content_id": CONTENT_ID,
            "piece_id": PACKET["piece_id"],
            "platform": "instagram",
            "format": "carrusel",
            "publication_url": "https://example.invalid/p/1",
            "published_at": "2026-08-27",
            "publication_decision_id": "PD-QUE-NO-EXISTE",
            "asset_version": "v1",
            "status": "PUBLICADA",
            "measurement_due_at": "2026-09-03",
        }
        registros = [("mem[0]", handoff()), ("mem[1]", publicacion)]
        errores, _ = CHAIN_MOD.validate_chain(registros)
        self.assertTrue(
            any("PUBLICAR SIN DECISIÓN HUMANA ES INVÁLIDO" in e for e in errores),
            f"un artefacto de producción válido no puede habilitar publicación: {errores}",
        )


class TestContenidoRealDelRepositorio(unittest.TestCase):

    def test_el_contenido_del_repositorio_declara_procedencia(self):
        proc = subprocess.run(
            [sys.executable, str(SCRIPT)], capture_output=True, text=True, cwd=str(REPO_ROOT)
        )
        self.assertEqual(proc.returncode, 0, f"{proc.stdout}{proc.stderr}")
        self.assertIn("PROCEDENCIA VÁLIDA", proc.stdout)

    def test_ningun_contenido_publicable_carece_de_handoff(self):
        for path in sorted((REPO_ROOT / "content").glob("*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            proc = data.get("procedencia") or {}
            if proc.get("modo") == "GOBERNADO":
                with self.subTest(archivo=path.name):
                    self.assertTrue(proc.get("handoff_id"),
                                    f"{path.name} es GOBERNADO y no declara handoff_id")

    def test_la_salida_recuerda_que_producir_no_es_publicar(self):
        proc = subprocess.run(
            [sys.executable, str(SCRIPT)], capture_output=True, text=True, cwd=str(REPO_ROOT)
        )
        self.assertIn("habilita PRODUCIR, no publicar", proc.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
