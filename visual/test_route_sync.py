import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

import pipeline
import route_engine
import route_sync
from brief import VisualPolicy
from providers import FakeImageProvider
from test_visual_pipeline import make_brief

RUTA_PENAL = [
    route_engine.CAT_CAUSA, route_engine.CAT_CONSECUENCIA,
    route_engine.CAT_RESPONSABILIDAD, route_engine.CAT_PRUEBA,
    route_engine.CAT_PROCEDIMIENTO, route_engine.CAT_REPARACION,
]

REPO = Path(__file__).resolve().parent.parent
ARTEFACTO_REAL = json.loads((REPO / "content" / "pieza-01-reales.json").read_text(encoding="utf-8"))


class TestExportLosCatorceCampos(unittest.TestCase):
    """FIXTURE: ruta manual generica, no ligada a contenido real -- prueba
    la ruta de aceptacion Penal -> Delito -> Daño -> Responsabilidad civil
    -> Prueba -> Proceso -> Reparacion pedida explicitamente, marcada como
    fixture (no se presenta como pieza penal real: no existe contenido
    penal real en content/*.json en este repositorio)."""

    def setUp(self):
        self.motor = route_engine.RouteEngine()
        self.filas = self.motor.avanzar_ruta_completa(
            "FIXTURE: ¿qué pasa cuando alguien comete un delito?", "Penal", RUTA_PENAL
        )
        self.rows = route_sync.export_all(self.motor)

    def test_exporta_exactamente_los_14_campos(self):
        for row in self.rows:
            self.assertEqual(set(row.keys()), set(route_sync.CANONICAL_FIELDS))
            self.assertEqual(len(row), 14)

    def test_conserva_el_orden_de_los_nodos(self):
        etiquetas = [r["nodo_actual"] for r in self.rows]
        self.assertEqual(etiquetas, [
            "MATERIA — Penal", "CAUSA — Delito", "CONSECUENCIA — Daño",
            "RESPONSABILIDAD — Responsabilidad civil", "PRUEBA — Prueba",
            "PROCEDIMIENTO — Proceso", "REPARACION — Reparación",
        ])

    def test_siguiente_vinculo_serializado_json_estable(self):
        # En el momento en que se produce la fila RESPONSABILIDAD, ninguna de
        # sus dos aristas (-> PRUEBA, -> DEFENSA) se ha usado todavia: eso
        # ocurre recien en el paso SIGUIENTE de la secuencia.
        fila_responsabilidad = self.rows[3]
        self.assertEqual(
            json.loads(fila_responsabilidad["siguiente_vinculo"]),
            sorted([route_engine.CAT_PRUEBA, route_engine.CAT_DEFENSA]),
        )
        for row in self.rows:
            valor = json.loads(row["siguiente_vinculo"])
            self.assertIsInstance(valor, list)

    def test_ruta_manual_sin_content_id_exporta_vacio_no_inventado(self):
        for row in self.rows:
            self.assertEqual(row["content_id"], "")
            self.assertEqual(row["submateria"], "")
            self.assertEqual(row["concepto"], "")

    def test_estado_verificacion_nunca_se_eleva(self):
        for row in self.rows[1:]:  # fila 0 (MATERIA) no tiene pieza producida todavia
            self.assertEqual(row["estado_verificacion"], "NO_VERIFICADO")


class TestExportContenidoReal(unittest.TestCase):
    """Contenido REAL: LM-PIEZA-01-REALES (materia civil, la unica materia
    con artefacto GOBERNADO real disponible en este repositorio)."""

    def setUp(self):
        self.motor = route_engine.RouteEngine()
        self.ruta_id = self.motor.leer_entrada_desde_artefacto(ARTEFACTO_REAL)
        self.motor.producir_pieza(self.ruta_id)  # un nodo mas alla del inicial
        self.rows = route_sync.export_ruta(self.motor, self.ruta_id)

    def test_conserva_content_id_y_taxonomia_real_en_cada_fila(self):
        for row in self.rows:
            self.assertEqual(row["content_id"], "LM-PIEZA-01-REALES")
            self.assertEqual(row["materia"], "civil")
            self.assertEqual(row["submateria"], "derechos_reales")
            self.assertEqual(row["concepto"], "propiedad_y_posesion")


class TestAltoNivelDesdeContentId(unittest.TestCase):
    """Fase 4: entrada real -> resolver -> ruta -> export, reanudable."""

    def test_avanzar_desde_content_id_resuelve_y_exporta(self):
        motor = route_engine.RouteEngine()
        resolution, filas = route_sync.avanzar_desde_content_id(motor, "LM-PIEZA-01-REALES")
        self.assertTrue(resolution.resolved)
        self.assertEqual(len(filas), 2)  # MATERIA + un nodo producido
        self.assertEqual(filas[-1]["content_id"], "LM-PIEZA-01-REALES")
        self.assertEqual(filas[-1]["materia"], "civil")
        self.assertEqual(filas[-1]["estado_verificacion"], "NO_VERIFICADO")

    def test_llamadas_sucesivas_reanudan_sin_duplicar(self):
        motor = route_engine.RouteEngine()
        _, filas_1 = route_sync.avanzar_desde_content_id(motor, "LM-PIEZA-01-REALES")
        _, filas_2 = route_sync.avanzar_desde_content_id(motor, "LM-PIEZA-01-REALES")
        # la segunda llamada continua la MISMA ruta (mismo ruta_id) y avanza
        # un nodo mas, sin repetir ninguno de los ya producidos.
        self.assertEqual(filas_1[0]["ruta_id"], filas_2[0]["ruta_id"])
        self.assertEqual(len(filas_2), 3)
        nodos = [f["nodo_actual"] for f in filas_2]
        self.assertEqual(len(nodos), len(set(nodos)))
        route_sync.assert_no_duplicate_rows(filas_2)

    def test_content_id_inexistente_no_abre_ruta_ni_gate(self):
        motor = route_engine.RouteEngine()
        with self.assertRaises(ValueError):
            route_sync.avanzar_desde_content_id(motor, "NO-EXISTE-ESTE-ID")
        self.assertEqual(len(motor), 0)


class TestGateEndToEndConContenidoRealNoPublicable(unittest.TestCase):
    """content/ejemplo.json es EJEMPLO_TECNICO real (no un fixture inventado
    por este test): confirma que el pipeline lo cierra end-to-end y nunca
    lo trata como contenido publicable, con 0 llamadas al proveedor."""

    def test_ejemplo_tecnico_real_cierra_el_gate_sin_llamar_al_proveedor(self):
        REPO = Path(__file__).resolve().parent.parent
        content_id = "LM-EJEMPLO-TECNICO-001"
        POLICY = VisualPolicy.load()
        brief = replace(make_brief(), content_id=content_id)
        provider = FakeImageProvider()
        run = pipeline.generate_visual_from_content_id(content_id, brief, POLICY, provider, dry_run=True)
        self.assertEqual(run.receipt.status, "GATE_CERRADO")
        self.assertIn("EJEMPLO_TECNICO", " ".join(run.receipt.motivos))
        self.assertEqual(provider.llamadas, 0)


class TestCicloOperativoCompleto(unittest.TestCase):
    """El ciclo de 14 pasos, en una sola llamada (route_sync.ejecutar_ciclo_operativo)."""

    def test_sin_brief_se_detiene_despues_del_paso_7_sin_inventar_direccion_de_arte(self):
        motor = route_engine.RouteEngine()
        resultado = route_sync.ejecutar_ciclo_operativo(motor, "LM-PIEZA-01-REALES")
        self.assertFalse(resultado.visual_intentado)
        self.assertEqual(resultado.visual_status, "")
        self.assertTrue(resultado.continuidad_ok, resultado.problemas_continuidad)
        self.assertEqual(resultado.fila_exportada["estado_verificacion"], "NO_VERIFICADO")
        self.assertIn(resultado.proxima_accion, ("VERIFY_SOURCES", "RUTA_COMPLETA", "ABRIR_VINCULO"))

    def test_con_brief_y_gate_abierto_se_detiene_en_dry_run_sin_llamar_proveedor(self):
        motor = route_engine.RouteEngine()
        POLICY = VisualPolicy.load()
        provider = FakeImageProvider()
        brief = replace(make_brief(), content_id="LM-PIEZA-01-REALES")
        resultado = route_sync.ejecutar_ciclo_operativo(
            motor, "LM-PIEZA-01-REALES", brief=brief, policy=POLICY, provider=provider, dry_run=True,
        )
        self.assertTrue(resultado.visual_intentado)
        self.assertEqual(resultado.visual_error, "")
        self.assertIn(resultado.visual_status, ("DRY_RUN", "GATE_CERRADO"))
        self.assertEqual(provider.llamadas, 0)
        self.assertTrue(resultado.continuidad_ok, resultado.problemas_continuidad)
        # el vinculo visual de la fila producida (MATERIA->CAUSA) llega al prompt.
        self.assertTrue(resultado.fila.vinculo_visual)

    def test_pieza_nunca_se_marca_verificada_pase_lo_que_pase_en_el_paso_visual(self):
        motor = route_engine.RouteEngine()
        POLICY = VisualPolicy.load()
        provider = FakeImageProvider()
        brief = replace(make_brief(), content_id="LM-PIEZA-01-REALES")
        resultado = route_sync.ejecutar_ciclo_operativo(
            motor, "LM-PIEZA-01-REALES", brief=brief, policy=POLICY, provider=provider, dry_run=True,
        )
        # ninguna funcion auxiliar (ciclo, pipeline de conveniencia, export) puede
        # elevar la autoridad juridica de la pieza -- sigue NO_VERIFICADO siempre.
        self.assertEqual(resultado.fila_exportada["estado_verificacion"], "NO_VERIFICADO")
        self.assertEqual(resultado.fila.pieza_producida["estado_verificacion"], "NO_VERIFICADO")

    def test_error_del_pipeline_no_deja_la_matriz_en_estado_ambiguo(self):
        class ProveedorRoto:
            def generate(self, *a, **kw):
                raise RuntimeError("proveedor caido")

            def capabilities(self):
                from providers import FakeImageProvider
                return FakeImageProvider().capabilities()

        motor = route_engine.RouteEngine()
        POLICY = VisualPolicy.load()
        brief = replace(make_brief(), content_id="LM-PIEZA-01-REALES")
        resultado = route_sync.ejecutar_ciclo_operativo(
            motor, "LM-PIEZA-01-REALES", brief=brief, policy=POLICY, provider=ProveedorRoto(),
            dry_run=False,
        )
        # la ruta ya avanzo (paso 3-7) ANTES del intento visual: un proveedor
        # roto no borra ni corrompe esa parte, solo se reporta el error.
        self.assertTrue(resultado.continuidad_ok, resultado.problemas_continuidad)
        self.assertNotEqual(resultado.visual_error, "")
        self.assertIn("REVISAR_ERROR_VISUAL", resultado.proxima_accion)
        self.assertEqual(len(motor.filas_de(resultado.fila.ruta_id)), 2)  # MATERIA + el nodo producido

    def test_content_id_inexistente_falla_seguro_sin_tocar_la_matriz(self):
        motor = route_engine.RouteEngine()
        with self.assertRaises(ValueError):
            route_sync.ejecutar_ciclo_operativo(motor, "NO-EXISTE-ESTE-ID")
        self.assertEqual(len(motor), 0)

    def test_dos_ciclos_sucesivos_avanzan_sin_duplicar(self):
        motor = route_engine.RouteEngine()
        r1 = route_sync.ejecutar_ciclo_operativo(motor, "LM-PIEZA-01-REALES")
        r2 = route_sync.ejecutar_ciclo_operativo(motor, "LM-PIEZA-01-REALES")
        self.assertEqual(r1.fila.ruta_id, r2.fila.ruta_id)
        self.assertNotEqual(r1.fila.nodo_actual, r2.fila.nodo_actual)
        self.assertTrue(r2.continuidad_ok, r2.problemas_continuidad)
        route_sync.assert_no_duplicate_rows(route_sync.export_ruta(motor, r1.fila.ruta_id))


class TestIdempotencia(unittest.TestCase):
    def test_segunda_sincronizacion_no_duplica_filas(self):
        motor = route_engine.RouteEngine()
        motor.avanzar_ruta_completa("tema idempotente", "Civil", [route_engine.CAT_CAUSA])
        primero = route_sync.export_all(motor)
        segundo = route_sync.export_all(motor)
        self.assertEqual(primero, segundo)
        self.assertEqual(route_sync.rows_signature(primero), route_sync.rows_signature(segundo))
        route_sync.assert_no_duplicate_rows(primero)

    def test_producir_una_fila_nueva_cambia_la_firma(self):
        motor = route_engine.RouteEngine()
        motor.leer_entrada("tema cambia", "Civil")
        firma_1 = route_sync.rows_signature(route_sync.export_all(motor))
        ruta_id = motor._filas[0].ruta_id
        motor.producir_pieza(ruta_id, categoria_elegida=route_engine.CAT_CAUSA)
        firma_2 = route_sync.rows_signature(route_sync.export_all(motor))
        self.assertNotEqual(firma_1, firma_2)

    def test_filas_duplicadas_detectadas(self):
        fila = route_sync.export_row(
            route_engine.RouteMatrixRow(ruta_id="R1", nodo_actual="CAUSA", nodo_actual_label="X")
        )
        with self.assertRaises(ValueError):
            route_sync.assert_no_duplicate_rows([fila, dict(fila)])


class TestReciboYPersistencia(unittest.TestCase):
    def test_receipt_roundtrip(self):
        motor = route_engine.RouteEngine()
        motor.avanzar_ruta_completa("tema recibo", "Laboral", [route_engine.CAT_CAUSA])
        rows = route_sync.export_all(motor)
        receipt = route_sync.build_receipt(rows)
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "sync-receipt.json"
            route_sync.write_receipt(receipt, path)
            recargado = route_sync.load_receipt(path)
        self.assertEqual(recargado.row_count, receipt.row_count)
        self.assertEqual(recargado.content_sha256, receipt.content_sha256)
        self.assertEqual(recargado.rows, receipt.rows)

    def test_esquema_desconocido_falla_seguro(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "sync-receipt.json"
            path.write_text(json.dumps({"schema_version": "999.0", "fields": [], "rows": []}), encoding="utf-8")
            with self.assertRaises(route_sync.UnknownSyncSchema):
                route_sync.load_receipt(path)

    def test_campos_desconocidos_falla_seguro(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "sync-receipt.json"
            payload = {
                "schema_version": route_sync.SYNC_SCHEMA_VERSION,
                "fields": ["ruta_id", "otro_campo"],
                "row_count": 0, "content_sha256": "x", "rows": [],
            }
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaises(route_sync.UnknownSyncSchema):
                route_sync.load_receipt(path)

    def test_sync_is_noop_detecta_no_cambios_y_cambios(self):
        motor = route_engine.RouteEngine()
        motor.avanzar_ruta_completa("tema noop", "Civil", [route_engine.CAT_CAUSA])
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "sync-receipt.json"
            self.assertFalse(route_sync.sync_is_noop(motor, path))  # sin recibo previo
            route_sync.write_receipt(route_sync.build_receipt(route_sync.export_all(motor)), path)
            self.assertTrue(route_sync.sync_is_noop(motor, path))  # mismo estado
            motor.producir_pieza(motor._filas[0].ruta_id, categoria_elegida=route_engine.CAT_CONSECUENCIA)
            self.assertFalse(route_sync.sync_is_noop(motor, path))  # estado cambio


class TestToCsv(unittest.TestCase):
    def test_csv_tiene_encabezado_exacto_y_una_fila_por_nodo(self):
        motor = route_engine.RouteEngine()
        motor.avanzar_ruta_completa("tema csv", "Civil", [route_engine.CAT_CAUSA])
        rows = route_sync.export_all(motor)
        texto = route_sync.to_csv_text(rows)
        lineas = texto.strip("\n").split("\n")
        encabezado = lineas[0].split(",")
        self.assertEqual(encabezado, route_sync.CANONICAL_FIELDS)
        self.assertEqual(len(lineas) - 1, len(rows))


if __name__ == "__main__":
    unittest.main()
