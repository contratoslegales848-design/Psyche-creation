"""Contrato de payload hacia Drive y verificacion de lectura de vuelta.

Los pasos 8-9 del ciclo operativo (escribir las 14 columnas en una hoja y
releerlas para confirmar que nada se perdio) se venian haciendo a mano,
fuera del repositorio: el payload y el readback reales existian solo como
artefactos sueltos de una sesion. Estas pruebas fijan ese contrato en
codigo, sin red y sin escribir en ningun servicio externo.
"""

import json
import unittest
from pathlib import Path

import route_engine
import route_sync

REPO = Path(__file__).resolve().parent.parent


def _motor_con_ruta_real():
    motor = route_engine.RouteEngine()
    resolution, ruta_id = route_engine.abrir_ruta_desde_content_id(motor, "LM-PIEZA-01-REALES")
    for cat in (route_engine.CAT_CAUSA, route_engine.CAT_CONSECUENCIA,
                route_engine.CAT_RESPONSABILIDAD, route_engine.CAT_PRUEBA,
                route_engine.CAT_PROCEDIMIENTO, route_engine.CAT_REPARACION):
        motor.producir_pieza(ruta_id, categoria_elegida=cat, formato="RUTA_EJECUTIVA")
    return motor, ruta_id


class TestSheetValues(unittest.TestCase):
    def test_primera_fila_es_el_encabezado_canonico_exacto(self):
        motor, ruta_id = _motor_con_ruta_real()
        rows = route_sync.export_ruta(motor, ruta_id)
        values = route_sync.build_sheet_values(rows)
        self.assertEqual(values[0], route_sync.CANONICAL_FIELDS)
        self.assertEqual(len(values[0]), 14)

    def test_una_fila_por_nodo_en_el_orden_de_la_ruta(self):
        motor, ruta_id = _motor_con_ruta_real()
        rows = route_sync.export_ruta(motor, ruta_id)
        values = route_sync.build_sheet_values(rows)
        self.assertEqual(len(values), len(rows) + 1)  # + encabezado
        # cada fila conserva su orden y su ancho exacto
        for fila in values[1:]:
            self.assertEqual(len(fila), 14)
        self.assertEqual([f[0] for f in values[1:]], [r["ruta_id"] for r in rows])

    def test_celdas_ausentes_van_vacias_nunca_None(self):
        # una ruta manual no tiene content_id ni taxonomia: se exporta "" ,
        # nunca None (Sheets escribiria "None" como texto literal).
        motor = route_engine.RouteEngine()
        motor.avanzar_ruta_completa("ruta manual", "Civil", [route_engine.CAT_CAUSA])
        values = route_sync.build_sheet_values(route_sync.export_all(motor))
        for fila in values[1:]:
            for celda in fila:
                self.assertIsInstance(celda, str)


class TestDrivePayload(unittest.TestCase):
    def test_payload_declara_esquema_campos_conteo_y_firma(self):
        motor, ruta_id = _motor_con_ruta_real()
        rows = route_sync.export_ruta(motor, ruta_id)
        payload = route_sync.build_drive_payload(rows)
        self.assertEqual(payload["schema_version"], route_sync.DRIVE_PAYLOAD_SCHEMA_VERSION)
        self.assertEqual(payload["fields"], route_sync.CANONICAL_FIELDS)
        self.assertEqual(payload["row_count"], len(rows))
        self.assertEqual(payload["content_sha256"], route_sync.rows_signature(rows))
        self.assertEqual(len(payload["content_sha256"]), 64)  # SHA-256 real, no un texto cualquiera

    def test_values_del_payload_son_solo_datos_sin_encabezado(self):
        motor, ruta_id = _motor_con_ruta_real()
        rows = route_sync.export_ruta(motor, ruta_id)
        payload = route_sync.build_drive_payload(rows)
        self.assertEqual(len(payload["values"]), len(rows))
        self.assertNotIn(route_sync.CANONICAL_FIELDS, payload["values"])

    def test_rango_a1_se_deriva_del_tamano_real(self):
        motor, ruta_id = _motor_con_ruta_real()
        rows = route_sync.export_ruta(motor, ruta_id)
        payload = route_sync.build_drive_payload(rows)
        # 14 columnas -> N ; 7 filas + encabezado -> 8
        self.assertEqual(payload["range_a1"], f"A1:N{len(rows) + 1}")

    def test_payload_es_determinista(self):
        motor, ruta_id = _motor_con_ruta_real()
        rows = route_sync.export_ruta(motor, ruta_id)
        self.assertEqual(route_sync.build_drive_payload(rows),
                         route_sync.build_drive_payload(rows))

    def test_payload_rechaza_filas_duplicadas(self):
        fila = route_sync.export_row(
            route_engine.RouteMatrixRow(ruta_id="R1", nodo_actual="CAUSA", nodo_actual_label="X"))
        with self.assertRaises(ValueError):
            route_sync.build_drive_payload([fila, dict(fila)])


class TestVerifyReadback(unittest.TestCase):
    def test_lectura_identica_valida(self):
        motor, ruta_id = _motor_con_ruta_real()
        rows = route_sync.export_ruta(motor, ruta_id)
        leido = route_sync.build_sheet_values(rows)  # simula lo que Sheets devuelve
        resultado = route_sync.verify_readback(leido, rows)
        self.assertTrue(resultado.ok, resultado.problemas)
        self.assertEqual(resultado.problemas, [])

    def test_una_celda_alterada_falla_e_indica_la_fila(self):
        motor, ruta_id = _motor_con_ruta_real()
        rows = route_sync.export_ruta(motor, ruta_id)
        leido = route_sync.build_sheet_values(rows)
        leido[3] = list(leido[3])
        leido[3][12] = "APROBADO"  # nadie puede elevar estado_verificacion por la via de la hoja
        resultado = route_sync.verify_readback(leido, rows)
        self.assertFalse(resultado.ok)
        self.assertTrue(any("fila 2" in p for p in resultado.problemas), resultado.problemas)

    def test_encabezado_distinto_falla(self):
        motor, ruta_id = _motor_con_ruta_real()
        rows = route_sync.export_ruta(motor, ruta_id)
        leido = route_sync.build_sheet_values(rows)
        leido[0] = ["otra_cosa"] + list(leido[0][1:])
        resultado = route_sync.verify_readback(leido, rows)
        self.assertFalse(resultado.ok)
        self.assertTrue(any("encabezado" in p for p in resultado.problemas), resultado.problemas)

    def test_faltan_filas_falla(self):
        motor, ruta_id = _motor_con_ruta_real()
        rows = route_sync.export_ruta(motor, ruta_id)
        leido = route_sync.build_sheet_values(rows)[:-1]  # se perdio la ultima fila
        resultado = route_sync.verify_readback(leido, rows)
        self.assertFalse(resultado.ok)

    def test_lectura_vacia_falla_cerrado(self):
        motor, ruta_id = _motor_con_ruta_real()
        rows = route_sync.export_ruta(motor, ruta_id)
        resultado = route_sync.verify_readback([], rows)
        self.assertFalse(resultado.ok)


class TestFormatoCompatibleConLaSincronizacionReal(unittest.TestCase):
    """El formato que Drive ya aceptó en la sincronización verificada.

    Solo se comprueba la FORMA (encabezado exacto, ancho, tipos), nunca las
    etiquetas concretas de los nodos: el vocabulario de navegación puede
    cambiar por decisión editorial (hay un PR abierto que lo hace) y este
    contrato no debe quedar acoplado a él.
    """

    FIXTURE = REPO / "visual" / "fixtures" / "route_engine" / "drive-readback-real.json"

    def test_el_encabezado_real_coincide_con_el_contrato_actual(self):
        readback = json.loads(self.FIXTURE.read_text(encoding="utf-8"))
        self.assertEqual(readback["values"][0], route_sync.CANONICAL_FIELDS)

    def test_todas_las_filas_reales_tienen_ancho_14(self):
        readback = json.loads(self.FIXTURE.read_text(encoding="utf-8"))
        for fila in readback["values"]:
            self.assertEqual(len(fila), 14)

    def test_ninguna_fila_real_declara_verificacion_elevada(self):
        readback = json.loads(self.FIXTURE.read_text(encoding="utf-8"))
        idx = route_sync.CANONICAL_FIELDS.index("estado_verificacion")
        for fila in readback["values"][1:]:
            self.assertEqual(fila[idx], "NO_VERIFICADO")


if __name__ == "__main__":
    unittest.main()
