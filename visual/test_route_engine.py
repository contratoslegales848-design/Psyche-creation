import json
import tempfile
import unittest
from pathlib import Path

from route_engine import (
    CAT_CAUSA,
    CAT_CONSECUENCIA,
    CAT_DEFENSA,
    CAT_MATERIA,
    CAT_PROCEDIMIENTO,
    CAT_PRUEBA,
    CAT_REPARACION,
    CAT_RESPONSABILIDAD,
    RouteEngine,
)

RUTA_PENAL = [
    CAT_CAUSA,           # Delito
    CAT_CONSECUENCIA,    # Daño
    CAT_RESPONSABILIDAD, # Responsabilidad civil
    CAT_PRUEBA,          # Prueba
    CAT_PROCEDIMIENTO,   # Proceso
    CAT_REPARACION,      # Reparación
]

ETIQUETAS_ESPERADAS = [
    "Penal", "Delito", "Daño", "Responsabilidad civil", "Prueba", "Proceso", "Reparación",
]


class TestRutaPenalDeAceptacion(unittest.TestCase):
    """La ruta exacta pedida como prueba de aceptacion del motor:
    Penal -> Delito -> Daño -> Responsabilidad civil -> Prueba -> Proceso -> Reparación."""

    def setUp(self):
        self.motor = RouteEngine()
        self.filas = self.motor.avanzar_ruta_completa(
            "¿Qué pasa cuando alguien comete un delito?", "Penal", RUTA_PENAL
        )

    def test_siete_nodos_en_el_orden_pedido(self):
        self.assertEqual(len(self.filas), 7)
        self.assertEqual([f.nodo_actual_label for f in self.filas], ETIQUETAS_ESPERADAS)

    def test_no_repite_ni_pierde_continuidad(self):
        ruta_id = self.filas[0].ruta_id
        ok, problemas = self.motor.valida_continuidad(ruta_id)
        self.assertTrue(ok, problemas)

    def test_cada_pieza_producida_esta_marcada_no_verificada(self):
        for fila in self.filas[1:]:  # la fila 0 es MATERIA, sin pieza producida todavia
            self.assertIsNotNone(fila.pieza_producida)
            self.assertEqual(fila.pieza_producida["estado_verificacion"], "NO_VERIFICADO")
            self.assertIn("legal", fila.pieza_producida["copy_borrador"].lower() + fila.pieza_producida["prompt_borrador"].lower())

    def test_ultima_fila_registra_vinculo_pendiente_no_ruta_completa(self):
        # La ruta pedida se detiene en Reparacion aunque Prevencion siga
        # disponible: se agoto la SECUENCIA pedida, no el grafo completo.
        ultima = self.filas[-1]
        self.assertEqual(ultima.nodo_actual_label, "Reparación")
        self.assertEqual(ultima.proxima_accion, "VERIFY_SOURCES")
        self.assertIn("PREVENCION", ultima.siguiente_vinculo)

    def test_matriz_tiene_los_campos_pedidos(self):
        fila = self.filas[1].to_dict()
        for campo in [
            "ruta_id", "content_id", "nodo_anterior", "nodo_actual", "siguiente_vinculo",
            "materia", "concepto", "formato", "estado", "fuente", "jurisdiccion",
            "verificacion", "pieza_producida", "proxima_accion",
        ]:
            self.assertIn(campo, fila)


class TestEvitarDesperdicio(unittest.TestCase):
    def test_no_repite_la_misma_arista_dentro_de_una_ruta(self):
        motor = RouteEngine()
        ruta_id = motor.leer_entrada("tema x", "Penal")
        motor.producir_pieza(ruta_id, categoria_elegida=CAT_CAUSA)
        with self.assertRaises(ValueError):
            # MATERIA->CAUSA ya se uso; no es una conexion "no explotada".
            motor.crear_vinculo(ruta_id, categoria_elegida=CAT_CAUSA)

    def test_conexion_no_explotada_permanece_disponible_para_otra_eleccion(self):
        motor = RouteEngine()
        ruta_id = motor.leer_entrada("tema y", "Penal")
        motor.producir_pieza(ruta_id, categoria_elegida=CAT_CAUSA)
        motor.producir_pieza(ruta_id, categoria_elegida=CAT_CONSECUENCIA)
        fila = motor.producir_pieza(ruta_id, categoria_elegida=CAT_RESPONSABILIDAD)
        # RESPONSABILIDAD abre dos conexiones (PRUEBA, DEFENSA); ninguna se usa aun.
        self.assertEqual(set(fila.siguiente_vinculo), {CAT_PRUEBA, CAT_DEFENSA})

    def test_ruta_agotada_desde_un_nodo_no_crea_fila_duplicada(self):
        motor = RouteEngine()
        ruta_id = motor.leer_entrada("tema z", "Penal")
        # PREVENCION es una hoja sin salidas en el grafo.
        motor.avanzar_ruta_completa("tema z", "Penal")  # explora natural hasta agotar
        n_filas_antes = len(motor.filas_de(ruta_id))
        ultima = motor.producir_pieza(ruta_id)
        self.assertEqual(len(motor.filas_de(ruta_id)), n_filas_antes)
        self.assertEqual(ultima.estado, "RUTA_COMPLETA")


class TestContinuidadYPersistencia(unittest.TestCase):
    def test_misma_entrada_y_materia_no_duplica_la_ruta(self):
        motor = RouteEngine()
        ruta_id_1 = motor.leer_entrada("mismo tema", "Civil")
        ruta_id_2 = motor.leer_entrada("mismo tema", "Civil")
        self.assertEqual(ruta_id_1, ruta_id_2)
        self.assertEqual(len(motor.filas_de(ruta_id_1)), 1)

    def test_entrada_vacia_falla(self):
        motor = RouteEngine()
        with self.assertRaises(ValueError):
            motor.leer_entrada("   ", "Civil")

    def test_persistencia_roundtrip(self):
        motor = RouteEngine()
        motor.avanzar_ruta_completa("ruta persistente", "Laboral", [CAT_CAUSA, CAT_CONSECUENCIA])
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "rutas.json"
            motor.save(path)
            recargado = RouteEngine.load(path)
        ruta_id = motor._filas[0].ruta_id
        self.assertEqual(
            [f.to_dict() for f in motor.filas_de(ruta_id)],
            [f.to_dict() for f in recargado.filas_de(ruta_id)],
        )

    def test_version_de_esquema_desconocida_se_ignora_fail_closed(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "rutas.json"
            path.write_text(json.dumps({"schema_version": "999.0", "filas": [{"x": 1}]}), encoding="utf-8")
            motor = RouteEngine.load(path)
        self.assertEqual(len(motor), 0)

    def test_ruta_natural_sin_secuencia_explicita_termina_en_prevencion(self):
        motor = RouteEngine()
        filas = motor.avanzar_ruta_completa("exploracion abierta", "Civil")
        self.assertEqual(filas[-1].nodo_actual, "PREVENCION")
        self.assertEqual(filas[-1].proxima_accion, "RUTA_COMPLETA")
        ok, problemas = motor.valida_continuidad(filas[0].ruta_id)
        self.assertTrue(ok, problemas)


if __name__ == "__main__":
    unittest.main()
