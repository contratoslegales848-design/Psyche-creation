#!/usr/bin/env python3
"""Pruebas del inventario materializado.

Qué se protege:

1. **Determinismo.** El inventario es un índice derivado; si regenerarlo diera
   resultados distintos, `check` no podría detectar que está obsoleto y el
   inventario dejaría de ser fiable exactamente cuando más falta hace.
2. **No autoridad.** El inventario nunca inventa un estado: cada campo procede de
   un artefacto. Si el inventario y el artefacto discrepan, el artefacto tiene
   razón, y `check` falla.
3. **Anti-duplicados.** Cinco colisiones deterministas. La paráfrasis NO se
   detecta, y hay una prueba que lo deja escrito para que nadie lo suponga.
4. **Métricas.** Una pieza publicada hace más de siete días y sin medición
   aparece en DUE_FOR_MEASUREMENT.

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
REPO_ROOT = SCRIPTS_DIR.parent
SCRIPT = SCRIPTS_DIR / "inventory.py"
FIXTURES = REPO_ROOT / "inventory" / "fixtures"
CADENA_CONTENT = FIXTURES / "cadena-completa" / "content"
CADENA_RECORDS = FIXTURES / "cadena-completa" / "records"
DUP_CONTENT = FIXTURES / "duplicados" / "content"
DUP_RECORDS = FIXTURES / "duplicados" / "records"

HOY = date(2026, 8, 27)


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


inv = _load(SCRIPT, "inventory")


def construir(content=CADENA_CONTENT, records=CADENA_RECORDS):
    return inv.build(content, records)


def por_id(inventario, content_id):
    for i in inventario["items"]:
        if i["content_id"] == content_id:
            return i
    raise AssertionError(f"{content_id} no está en el inventario")


class TestCadenaCompleta(unittest.TestCase):
    """MATERIA → SUBMATERIA → CONCEPTO → SITUACIÓN → CONTENIDO → PRODUCCIÓN →
    PUBLICACIÓN → MÉTRICAS, con fixtures suficientes para demostrarlo."""

    def setUp(self):
        self.inventario = construir()

    def test_la_taxonomia_editorial_llega_completa_al_inventario(self):
        item = por_id(self.inventario, "LM-DEMO-CIVIL-001")
        self.assertEqual(item["materia"], "Civil")
        self.assertEqual(item["submateria"], "Contratos")
        self.assertEqual(item["concepto"], "Comodato frente a mutuo")
        self.assertTrue(item["situacion_humana"])
        self.assertEqual(item["content_type"], "DIFERENCIA")

    def test_la_cadena_de_estados_se_deriva_de_los_artefactos(self):
        item = por_id(self.inventario, "LM-DEMO-CIVIL-001")
        self.assertEqual(item["source_state"], "CURRENT")
        self.assertEqual(item["verification_state"], "APROBADO")
        self.assertEqual(item["production_state"], "APROBADO_QA")
        self.assertEqual(item["publication_state"], "PUBLICADA")
        self.assertEqual(item["metrics_state"], "MEDIDA")
        self.assertTrue(item["publication_url"].startswith("https://"))
        self.assertEqual(item["measurement_due_at"], "2026-08-08")

    def test_el_territorio_sale_de_las_jurisdicciones_revisadas(self):
        item = por_id(self.inventario, "LM-DEMO-CIVIL-001")
        self.assertEqual(item["territory"], ["Argentina", "España", "México", "Perú"])

    def test_la_capa_jurisdiccional_es_la_del_claim(self):
        item = por_id(self.inventario, "LM-DEMO-CIVIL-001")
        self.assertEqual(item["jurisdiction_layer"], "CAPA_A_TRANSVERSAL")

    def test_la_pieza_no_aplica_conserva_ruta_valida(self):
        """Una cita histórica es publicable sin claim jurídico, y consta como tal."""
        item = por_id(self.inventario, "LM-DEMO-CITA-001")
        self.assertEqual(item["modo_procedencia"], "NO_APLICA")
        self.assertTrue(item["publicable"])
        self.assertEqual(item["source_state"], "NO_APLICA")
        self.assertEqual(item["verification_state"], "NO_APLICA")
        self.assertTrue(item["materia"])

    def test_hay_aprendizaje_asociado_a_la_pieza_medida(self):
        self.assertEqual(por_id(self.inventario, "LM-DEMO-CIVIL-001")["learning_count"], 1)


class TestDeterminismo(unittest.TestCase):

    def test_regenerar_produce_resultado_identico(self):
        """Invariante 4."""
        a, b = construir(), construir()
        self.assertEqual(inv.digest(a), inv.digest(b))
        self.assertEqual(inv.serialize(a), inv.serialize(b))

    def test_no_hay_marca_de_tiempo_en_la_salida(self):
        """Una marca de tiempo haría que `check` fallara siempre."""
        texto = inv.serialize(construir())
        for sospechoso in ("generated_at", "timestamp", "created_at"):
            self.assertNotIn(sospechoso, texto)

    def test_el_inventario_almacenado_no_depende_del_reloj(self):
        """Nada que dependa de la fecha se congela en el índice: si lo hiciera,
        `check` empezaría a fallar solo por el paso del tiempo, sin que ningún
        artefacto hubiera cambiado."""
        estados = {i["metrics_state"] for i in construir()["items"]}
        self.assertNotIn("DUE_FOR_MEASUREMENT", estados)
        self.assertEqual(inv.digest(construir()), inv.digest(construir()))

    def test_el_orden_no_depende_del_orden_del_sistema_de_archivos(self):
        ids = [i["content_id"] for i in construir()["items"]]
        self.assertEqual(ids, sorted(ids))

    def test_check_detecta_un_inventario_obsoleto(self):
        """Vector de red team: inventario stale."""
        with tempfile.TemporaryDirectory() as tmp:
            salida = Path(tmp) / "inventory.json"
            actual = construir()
            salida.write_text(inv.serialize(actual), encoding="utf-8")
            code = inv.main(["check", "--content-dir", str(CADENA_CONTENT),
                             "--records-dir", str(CADENA_RECORDS),
                             "--output", str(salida), "--today", "2026-08-27"])
            self.assertEqual(code, 0)
            # Se manipula el inventario, no los artefactos: el artefacto manda.
            manipulado = copy.deepcopy(actual)
            manipulado["items"][0]["publication_state"] = "PUBLICADA"
            salida.write_text(inv.serialize(manipulado), encoding="utf-8")
            code = inv.main(["check", "--content-dir", str(CADENA_CONTENT),
                             "--records-dir", str(CADENA_RECORDS),
                             "--output", str(salida), "--today", "2026-08-27"])
            self.assertEqual(code, 1, "un inventario que discrepa del artefacto debe fallar")

    def test_el_inventario_del_repositorio_esta_al_dia(self):
        """Invariante 10: lo que ya existe sigue pasando."""
        proc = subprocess.run([sys.executable, str(SCRIPT), "check"],
                              capture_output=True, text=True, cwd=str(REPO_ROOT))
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)


class TestAntiDuplicados(unittest.TestCase):

    def setUp(self):
        self.dups = construir(DUP_CONTENT, DUP_RECORDS)["duplicates"]
        self.tipos = {d["tipo"] for d in self.dups}

    def test_content_id_repetido_se_detecta(self):
        """Invariante 5."""
        self.assertIn("CONTENT_ID_REPETIDO", self.tipos)

    def test_composicion_repetida_se_detecta(self):
        self.assertIn("COMPOSICION_REPETIDA", self.tipos)

    def test_concepto_repetido_se_detecta(self):
        self.assertIn("CONCEPTO_REPETIDO", self.tipos)

    def test_fingerprint_identico_se_detecta(self):
        self.assertIn("FINGERPRINT_IDENTICO", self.tipos)

    def test_publicacion_ya_registrada_se_detecta(self):
        """Invariante 6."""
        inventario = construir()
        a, b = inventario["items"][1], copy.deepcopy(inventario["items"][1])
        b["content_id"] = "LM-OTRO-999"
        b["composition_id"] = "otro"
        b["concepto"] = "otro concepto"
        b["fingerprint"] = "otra frase"
        hallazgos = inv.detect_duplicates([a, b])
        self.assertIn("PUBLICACION_YA_REGISTRADA", {h["tipo"] for h in hallazgos})

    def test_la_cadena_limpia_no_produce_falsos_positivos(self):
        self.assertEqual(construir()["duplicates"], [])

    def test_check_falla_ante_duplicados(self):
        with tempfile.TemporaryDirectory() as tmp:
            salida = Path(tmp) / "inventory.json"
            salida.write_text(inv.serialize(construir(DUP_CONTENT, DUP_RECORDS)), encoding="utf-8")
            code = inv.main(["check", "--content-dir", str(DUP_CONTENT),
                             "--records-dir", str(DUP_RECORDS),
                             "--output", str(salida), "--today", "2026-08-27"])
            self.assertEqual(code, 1)

    def test_la_parafrasis_NO_se_detecta_y_queda_declarado(self):
        """Límite explícito: sin motor semántico, dos formulaciones distintas pasan.

        Esta prueba no celebra el hueco; lo fija por escrito para que nadie
        suponga una cobertura que no existe.
        """
        inventario = construir()
        a = copy.deepcopy(por_id(inventario, "LM-DEMO-CITA-001"))
        b = copy.deepcopy(a)
        b["content_id"] = "LM-DEMO-CITA-002"
        b["composition_id"] = "otra"
        b["concepto"] = "El derecho premia a quien actúa"
        b["fingerprint"] = inv.load_helpers()[2].normalize_fingerprint(
            "Quien no reclama a tiempo acaba perdiendo lo que le corresponde")
        self.assertEqual(inv.detect_duplicates([a, b]), [],
                         "si esto empieza a fallar es que se añadió detección semántica: "
                         "actualiza la documentación que declara el límite")


class TestMetricas(unittest.TestCase):

    def test_pieza_vencida_sin_medicion_aparece_en_due_for_measurement(self):
        """Invariante 8."""
        resultado = inv.query(construir(), "DUE_FOR_MEASUREMENT", HOY)
        ids = [i["content_id"] for i in resultado]
        self.assertEqual(ids, ["LM-DEMO-CIVIL-002"])

    def test_measurement_due_at_se_calcula_a_siete_dias(self):
        """Invariante 7: el dato viene del PublicationRecord, no se recalcula aquí."""
        item = por_id(construir(), "LM-DEMO-CIVIL-002")
        self.assertEqual(item["measurement_due_at"], "2026-08-12")
        self.assertEqual(
            (date.fromisoformat("2026-08-12") - date.fromisoformat("2026-08-05")).days, 7)

    def test_antes_del_vencimiento_no_aparece(self):
        resultado = inv.query(construir(), "DUE_FOR_MEASUREMENT", date(2026, 8, 10))
        self.assertEqual([i["content_id"] for i in resultado], [])

    def test_pieza_ya_medida_no_aparece(self):
        item = por_id(construir(), "LM-DEMO-CIVIL-001")
        self.assertEqual(item["metrics_state"], "MEDIDA")
        vencidas = inv.query(construir(), "DUE_FOR_MEASUREMENT", date(2027, 1, 1))
        self.assertNotIn("LM-DEMO-CIVIL-001", [i["content_id"] for i in vencidas],
                         "una pieza ya medida no vuelve a vencer por el paso del tiempo")

    def test_artefacto_no_publicable_no_aparece_como_publicado(self):
        """Invariante 9: el ejemplo técnico del repositorio no es una publicación."""
        inventario = inv.build(REPO_ROOT / "content", REPO_ROOT / ".claude" / "skills"
                               / "legalmente-legal-verification" / "publication" / "records")
        item = por_id(inventario, "LM-EJEMPLO-TECNICO-001")
        self.assertFalse(item["publicable"])
        self.assertNotEqual(item["publication_state"], "PUBLICADA")
        self.assertEqual(item["metrics_state"], "NO_APLICA")
        self.assertEqual(inv.query(inventario, "PUBLICADAS", HOY), [])


class TestConsultas(unittest.TestCase):

    def test_las_consultas_declaradas_existen(self):
        inventario = construir()
        for nombre in inv.QUERIES:
            with self.subTest(consulta=nombre):
                self.assertIsInstance(inv.query(inventario, nombre, HOY), list)

    def test_consulta_desconocida_falla(self):
        with self.assertRaises(ValueError):
            inv.query(construir(), "LO_QUE_SEA", HOY)

    def test_requiere_revision_fuentes_encuentra_lo_que_debe(self):
        inventario = construir()
        for item in inventario["items"]:
            item["source_state"] = "BLOQUEADO"
        self.assertEqual(len(inv.query(inventario, "REQUIERE_REVISION_FUENTES", HOY)),
                         len(inventario["items"]))


class TestNoAutoridad(unittest.TestCase):
    """El inventario no es fuente de verdad de nada."""

    def test_los_datos_proceden_de_los_artefactos_no_del_inventario(self):
        item = por_id(construir(), "LM-DEMO-CIVIL-001")
        artefacto = json.loads((REPO_ROOT / item["artifact"]).read_text(encoding="utf-8"))
        self.assertEqual(item["content_id"], artefacto["procedencia"]["content_id"])
        self.assertEqual(item["materia"], artefacto["taxonomia"]["materia"])
        self.assertEqual(item["jurisdiction_layer"], artefacto["procedencia"]["jurisdiction_layer"])

    def test_construir_no_modifica_ningun_artefacto(self):
        antes = {p: p.read_bytes() for p in sorted(CADENA_CONTENT.rglob("*.json"))}
        antes.update({p: p.read_bytes() for p in sorted(CADENA_RECORDS.rglob("*.json"))})
        construir()
        for p, contenido in antes.items():
            self.assertEqual(p.read_bytes(), contenido, f"{p} fue modificado")

    def test_la_nota_del_inventario_declara_que_no_es_autoridad(self):
        self.assertIn("No es autoridad", construir()["_nota"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
