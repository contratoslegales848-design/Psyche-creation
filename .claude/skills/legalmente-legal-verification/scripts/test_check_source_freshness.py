#!/usr/bin/env python3
"""Pruebas de la vigencia de fuentes.

Qué se protege: que una fuente derogada, sustituida o sin comprobar deje de
sostener un claim aprobado — **sin tocar el claim**. Escribir el veredicto dentro
del claim packet cambiaría su contenido y, con él, su `contenido_hash_sha256`,
invalidando en silencio una aprobación humana ya firmada. El sistema no modifica
el contenido aprobado: deja de dejarlo avanzar.

Ningún revisor de prueba lleva nombre real (ver SKILL.md).
"""
import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPTS_DIR.parent
SCRIPT = SCRIPTS_DIR / "check-source-freshness.py"
LEDGER_PATH = SKILL_ROOT / "references" / "source-freshness.json"
PACKET_APROBADO = SKILL_ROOT / "publication" / "fixtures" / "claim-packet-aprobado.json"

REVISOR_FICTICIO = "REVISOR_FICTICIO_SOLO_PRUEBA"
HOY = date(2026, 8, 27)


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


csf = _load(SCRIPT, "check_source_freshness")
REGISTRY = csf.load_registry()


def entrada(url="https://www.boe.es/buscar/act.php?id=BOE-A-1889-4763",
            status="CURRENT", source_type="NORMA_OFICIAL", jurisdiction="España",
            registro="boe-es", last_verified="2026-08-25", **over):
    e = {
        "source_id": csf.source_id_for(url),
        "titulo": "Norma de prueba",
        "jurisdiction": jurisdiction,
        "source_type": source_type,
        "canonical_url": url,
        "registro_oficial_id": registro,
        "published_at": None,
        "effective_from": None,
        "effective_to": None,
        "last_verified_at": last_verified,
        "verified_by": REVISOR_FICTICIO if last_verified else None,
        "verification_status": status,
        "supersedes": [],
        "superseded_by": None,
        "review_due_at": csf.expected_review_due(last_verified, source_type) if last_verified else None,
    }
    e.update(over)
    return e


def libro(*entradas):
    return {"ledger_version": "1.0", "sources": list(entradas)}


def claim(url, tipo="NORMA_OFICIAL", gate="ABIERTO"):
    return {
        "claim_id": "c1", "gate_arte": gate,
        "fuentes": [{"id": "f1", "url": url, "tipo_fuente": tipo}],
    }


def evaluar(ledger, claims, today=HOY):
    """Escribe los claims en una pieza temporal y aplica el checker."""
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "pieza.json"
        p.write_text(json.dumps({"piece_id": "p", "claims": claims}, ensure_ascii=False),
                     encoding="utf-8")
        return csf.check_pieces([p], ledger, today)


URL = "https://www.boe.es/buscar/act.php?id=BOE-A-1889-4763"
URL2 = "https://www.boe.es/buscar/pdf/1995/BOE-A-1995-25444-consolidado.pdf"


class TestVeredictoDeFrescura(unittest.TestCase):

    def test_fuente_current_permite_la_ruta_normal(self):
        """Invariante 1."""
        errores, advertencias, resumen = evaluar(libro(entrada()), [claim(URL)])
        self.assertEqual(errores, [], f"{errores}")
        self.assertEqual(resumen[0][1], "CURRENT")

    def test_fuente_superseded_exige_revision(self):
        """Invariante 2 (primera mitad)."""
        vieja = entrada(status="SUPERSEDED", superseded_by=csf.source_id_for(URL2))
        nueva = entrada(url=URL2, supersedes=[csf.source_id_for(URL)])
        errores, _a, resumen = evaluar(libro(vieja, nueva), [claim(URL)])
        self.assertEqual(resumen[0][1], "BLOQUEADO")
        self.assertTrue(any("superseded" in e for e in errores), f"{errores}")

    def test_fuente_repealed_exige_revision(self):
        """Invariante 2 (segunda mitad)."""
        errores, _a, resumen = evaluar(
            libro(entrada(status="REPEALED", effective_to="2026-01-01")), [claim(URL)])
        self.assertEqual(resumen[0][1], "BLOQUEADO")
        self.assertTrue(any("repealed" in e for e in errores), f"{errores}")

    def test_unknown_falla_cerrado_cuando_la_vigencia_es_necesaria(self):
        """Invariante 3: una norma sin vigencia comprobada no sostiene nada."""
        errores, _a, resumen = evaluar(
            libro(entrada(status="UNKNOWN", last_verified=None)),
            [claim(URL, tipo="NORMA_OFICIAL")])
        self.assertEqual(resumen[0][1], "REQUIERE_REVISION")
        self.assertTrue(any("vigencia desconocida" in e for e in errores), f"{errores}")

    def test_unknown_se_tolera_donde_la_vigencia_no_aplica(self):
        """Una sentencia no 'caduca' como una norma: el control no la castiga igual."""
        errores, _a, resumen = evaluar(
            libro(entrada(status="UNKNOWN", last_verified=None,
                          source_type="JURISPRUDENCIA_OFICIAL", registro="poderjudicial-es",
                          url="https://www.poderjudicial.es/search/openDocument/x/1")),
            [claim("https://www.poderjudicial.es/search/openDocument/x/1",
                   tipo="JURISPRUDENCIA_OFICIAL")])
        self.assertEqual(errores, [], f"{errores}")
        self.assertEqual(resumen[0][1], "CURRENT")

    def test_fuente_sin_registrar_exige_revision(self):
        errores, _a, resumen = evaluar(libro(), [claim(URL)])
        self.assertEqual(resumen[0][1], "REQUIERE_REVISION")
        self.assertTrue(any("no está en el libro mayor" in e for e in errores), f"{errores}")

    def test_url_cambiada_deja_de_emparejar(self):
        """Vector de red team: cambiar la URL no hereda la vigencia de la vieja."""
        _e, _a, resumen = evaluar(
            libro(entrada()),
            [claim("https://www.boe.es/buscar/act.php?id=BOE-A-1889-9999")])
        self.assertEqual(resumen[0][1], "REQUIERE_REVISION")

    def test_gate_cerrado_solo_advierte(self):
        """Fail-closed donde hay algo en riesgo; ruido en ninguna parte."""
        errores, advertencias, _r = evaluar(
            libro(entrada(status="REPEALED", effective_to="2026-01-01")),
            [claim(URL, gate="CERRADO")])
        self.assertEqual(errores, [])
        self.assertTrue(advertencias)

    def test_el_veredicto_nunca_se_escribe_en_el_claim(self):
        """La aprobación firmada no se toca: solo deja de poder avanzar."""
        c = claim(URL)
        antes = copy.deepcopy(c)
        csf.claim_freshness(c, {csf.normalize_url(URL): entrada(status="REPEALED")}, HOY)
        self.assertEqual(c, antes)

    def test_review_due_vencido_degrada_a_needs_review(self):
        """El reloj degrada un CURRENT declarado; no lo 'arregla' nadie en silencio."""
        e = entrada(last_verified="2026-01-01")  # +180 días → 2026-06-30
        _err, _a, resumen = evaluar(libro(e), [claim(URL)], today=date(2026, 8, 27))
        self.assertEqual(resumen[0][1], "REQUIERE_REVISION")
        _err2, _a2, resumen2 = evaluar(libro(e), [claim(URL)], today=date(2026, 6, 1))
        self.assertEqual(resumen2[0][1], "CURRENT")


class TestCoherenciaDelLibroMayor(unittest.TestCase):

    def _errores(self, ledger, today=None):
        return csf.validate_ledger(ledger, REGISTRY, today)[0]

    def test_el_libro_mayor_real_es_coherente(self):
        """Invariante 10: lo que ya existe sigue pasando."""
        self.assertEqual(self._errores(csf.load_ledger()), [])

    def test_source_id_debe_derivarse_de_la_url(self):
        e = entrada()
        e["source_id"] = "SRC-000000000000"
        self.assertTrue(any("no se deriva de su 'canonical_url'" in x
                            for x in self._errores(libro(e))))

    def test_url_canonica_duplicada_es_error(self):
        """Dos entradas para la misma fuente crearían dos verdades sobre su vigencia."""
        self.assertTrue(any("duplicada" in x for x in self._errores(libro(entrada(), entrada()))))

    def test_current_exige_responsable_y_fecha(self):
        for campo in ("verified_by", "last_verified_at"):
            with self.subTest(campo=campo):
                e = entrada()
                e[campo] = None
                if campo == "last_verified_at":
                    e["review_due_at"] = None
                self.assertTrue(any(campo in x for x in self._errores(libro(e))))

    def test_current_con_fecha_de_fin_es_contradictorio(self):
        self.assertTrue(any("effective_to" in x
                            for x in self._errores(libro(entrada(effective_to="2026-01-01")))))

    def test_superseded_exige_destino(self):
        self.assertTrue(any("superseded_by" in x
                            for x in self._errores(libro(entrada(status="SUPERSEDED")))))

    def test_enlace_de_sustitucion_asimetrico_es_error(self):
        vieja = entrada(status="SUPERSEDED", superseded_by=csf.source_id_for(URL2))
        nueva = entrada(url=URL2)  # no declara supersedes
        self.assertTrue(any("asimétrico" in x for x in self._errores(libro(vieja, nueva))))

    def test_ciclo_de_sustitucion_es_error(self):
        a = entrada(status="SUPERSEDED", superseded_by=csf.source_id_for(URL2),
                    supersedes=[csf.source_id_for(URL2)])
        b = entrada(url=URL2, status="SUPERSEDED", superseded_by=csf.source_id_for(URL),
                    supersedes=[csf.source_id_for(URL)])
        self.assertTrue(any("cíclica" in x for x in self._errores(libro(a, b))))

    def test_review_due_debe_ser_last_verified_mas_la_ventana(self):
        e = entrada()
        e["review_due_at"] = "2099-01-01"
        self.assertTrue(any("review_due_at" in x for x in self._errores(libro(e))))

    def test_hostname_que_no_pertenece_al_organismo_es_error(self):
        """Se compara por frontera real de subdominio, nunca por subcadena."""
        e = entrada(url="https://boe.es.evil.com/x")
        self.assertTrue(any("no pertenece al organismo" in x for x in self._errores(libro(e))))

    def test_pais_incorrecto_para_el_organismo_es_error(self):
        """Vector de red team: una fuente española declarada de otro país."""
        e = entrada(jurisdiction="Colombia")
        self.assertTrue(any("no está entre las" in x for x in self._errores(libro(e))))

    def test_tipo_no_permitido_para_el_organismo_es_error(self):
        e = entrada(source_type="JURISPRUDENCIA_OFICIAL")
        self.assertTrue(any("no permitido" in x for x in self._errores(libro(e))))

    def test_registro_inexistente_es_error(self):
        e = entrada(registro="organismo-que-no-existe")
        self.assertTrue(any("no existe en el registro" in x for x in self._errores(libro(e))))


class TestNormalizacionDeUrl(unittest.TestCase):

    def test_esquema_host_y_barra_final_se_normalizan(self):
        self.assertEqual(csf.normalize_url("HTTPS://WWW.BOE.ES/a/b/"),
                         csf.normalize_url("https://www.boe.es/a/b"))

    def test_el_fragmento_se_conserva(self):
        """SPIJ (Perú) identifica la norma concreta en el fragmento."""
        a = "https://spij.minjus.gob.pe/spij-ext-web/#/detallenorma/H1000921"
        b = "https://spij.minjus.gob.pe/spij-ext-web/#/detallenorma/H9999999"
        self.assertNotEqual(csf.normalize_url(a), csf.normalize_url(b))

    def test_el_query_se_conserva(self):
        a = "https://www.boe.es/buscar/act.php?id=BOE-A-1889-4763"
        b = "https://www.boe.es/buscar/act.php?id=BOE-A-1995-25444"
        self.assertNotEqual(csf.normalize_url(a), csf.normalize_url(b))


class TestCLI(unittest.TestCase):

    def _run(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), *args],
                              capture_output=True, text=True, cwd=str(SKILL_ROOT))

    def test_solo_libro_mayor_pasa(self):
        proc = self._run("--solo-libro-mayor")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_los_paquetes_del_piloto_no_producen_error(self):
        """Invariante 10: gates cerrados → advertencias, nunca errores."""
        piloto = sorted((SKILL_ROOT / "pilot" / "claim-packets").glob("*.json"))
        proc = self._run("--today", "2026-08-27", *[str(p) for p in piloto])
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_el_paquete_aprobado_esta_current(self):
        proc = self._run("--today", "2026-08-27", str(PACKET_APROBADO))
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("1/1 claim(s) con veredicto CURRENT", proc.stdout)

    def test_la_salida_recuerda_que_la_actualizacion_es_research_separado(self):
        proc = self._run("--solo-libro-mayor")
        self.assertIn("operación de research separada", proc.stdout)
        self.assertIn("nunca modifica un claim packet", proc.stdout)

    def test_el_script_no_importa_red(self):
        """El validador jurídico no tiene red por diseño; este tampoco."""
        fuente = SCRIPT.read_text(encoding="utf-8")
        for prohibido in ("import requests", "urllib.request", "http.client", "socket"):
            self.assertNotIn(prohibido, fuente,
                             f"{prohibido} introduciría red en una validación que debe ser offline")


if __name__ == "__main__":
    unittest.main(verbosity=2)
