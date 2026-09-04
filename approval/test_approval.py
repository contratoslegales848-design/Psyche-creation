"""La cola no puede convertirse en la puerta trasera de la aprobacion.

Es la tentacion evidente de un modulo que se llama "cola de aprobacion": que
acabe aprobando. Estas pruebas fijan que no hay ningun camino —ni por
conveniencia, ni por silencio, ni por lote— que produzca una aprobacion que un
humano no haya tomado.

Sin red. Determinista.
"""

import sys
import unittest
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))

import cola as Q  # noqa: E402


def _item(**extra):
    base = {
        "id": "LM-X-001",
        "titulo": "Posesion y tenencia",
        "contenido_exacto": "Texto exacto de la pieza.",
        "alcance": "CAPA_C_NACIONAL",
        "fuentes": [{"id": "s1", "verificacion_fuente": {"texto_exacto_consultado": True}}],
    }
    base.update(extra)
    return base


class TestPrepararNoEsAprobar(unittest.TestCase):
    def test_una_solicitud_recien_preparada_no_esta_aprobada(self):
        s = Q.preparar_solicitud("L1", [_item()])
        self.assertEqual(s["estado"], Q.PREPARADA)
        self.assertFalse(s["aprobada"])
        self.assertEqual(s["gate_arte"], "CERRADO")
        self.assertEqual(s["publicacion"], "NOT_PUBLISHED")

    def test_no_existe_ninguna_funcion_que_apruebe(self):
        """Control estructural: si mañana alguien añade `aprobar()`, esta prueba
        lo obliga a justificar por qué."""
        publicas = [n for n in dir(Q) if not n.startswith("_") and callable(getattr(Q, n))]
        for nombre in publicas:
            with self.subTest(funcion=nombre):
                self.assertNotIn("aprobar", nombre.lower())

    def test_sin_decision_no_hay_aprobacion(self):
        s = Q.preparar_solicitud("L1", [_item()])
        r = Q.evaluar_decision(s, None)
        self.assertFalse(r["aplicable"])
        self.assertEqual(r["items_aprobados"], [])

    def test_el_silencio_caduca_en_vez_de_aprobar(self):
        """Lo contrario de auto-aprobar: pasado el plazo, la solicitud muere."""
        s = Q.preparar_solicitud("L1", [_item()])
        self.assertEqual(s["caducidad_dias"], Q.CADUCIDAD_DIAS)
        self.assertIn("El silencio no la aprueba", s["_nota"])


class TestElLoteAbarataLaDecisionSinDiluirla(unittest.TestCase):
    def test_una_sola_decision_cubre_varios_items(self):
        """El objetivo del modulo: que aprobar diez cueste una decision, no diez."""
        items = [_item(id=f"LM-X-{i:03d}") for i in range(10)]
        s = Q.preparar_solicitud("L1", items)
        self.assertEqual(len(s["items_listos"]), 10)
        decision = {
            "decision": "APROBADA", "decidida_por": "fundador", "fecha": "2026-09-04",
            "contenido_hashes": [i["contenido_hash"] for i in s["items_listos"]],
        }
        r = Q.evaluar_decision(s, decision)
        self.assertTrue(r["aplicable"], r["problemas"])
        self.assertEqual(len(r["items_aprobados"]), 10)

    def test_la_decision_no_alcanza_a_contenido_que_cambio_despues(self):
        """El control central. Aprobar un lote no es firmar en blanco: si el
        texto cambia, la decision deja de valer para ese item."""
        s = Q.preparar_solicitud("L1", [_item(id="a"), _item(id="b")])
        decision = {
            "decision": "APROBADA", "decidida_por": "fundador", "fecha": "2026-09-04",
            "contenido_hashes": [s["items_listos"][0]["contenido_hash"]],
        }
        r = Q.evaluar_decision(s, decision)
        self.assertFalse(r["aplicable"])
        self.assertTrue(any("cambiaron desde que se reviso" in p for p in r["problemas"]))
        self.assertEqual(r["estado"], Q.CADUCADA)

    def test_una_decision_sobre_contenido_ajeno_se_rechaza(self):
        s = Q.preparar_solicitud("L1", [_item()])
        decision = {"decision": "APROBADA", "decidida_por": "fundador",
                    "fecha": "2026-09-04", "contenido_hashes": ["0" * 64]}
        r = Q.evaluar_decision(s, decision)
        self.assertFalse(r["aplicable"])
        self.assertTrue(any("no esta en esta solicitud" in p for p in r["problemas"]))

    def test_una_decision_sin_autor_no_vale(self):
        s = Q.preparar_solicitud("L1", [_item()])
        r = Q.evaluar_decision(s, {
            "decision": "APROBADA", "fecha": "2026-09-04",
            "contenido_hashes": [s["items_listos"][0]["contenido_hash"]]})
        self.assertFalse(r["aplicable"])
        self.assertTrue(any("quien la tomo" in p for p in r["problemas"]))

    def test_un_tipo_de_decision_inventado_se_rechaza(self):
        s = Q.preparar_solicitud("L1", [_item()])
        r = Q.evaluar_decision(s, {
            "decision": "APROBADA_TACITAMENTE", "decidida_por": "x", "fecha": "y",
            "contenido_hashes": [s["items_listos"][0]["contenido_hash"]]})
        self.assertFalse(r["aplicable"])

    def test_una_decision_rechazada_no_aprueba_nada(self):
        s = Q.preparar_solicitud("L1", [_item()])
        r = Q.evaluar_decision(s, {
            "decision": "RECHAZADA", "decidida_por": "fundador", "fecha": "2026-09-04",
            "contenido_hashes": [s["items_listos"][0]["contenido_hash"]]})
        self.assertTrue(r["aplicable"])
        self.assertEqual(r["items_aprobados"], [])

    def test_ni_siquiera_aprobada_abre_el_gate(self):
        """Aprobar habilita PRODUCIR el arte. Abrir el gate y publicar son pasos
        posteriores con sus propias reglas."""
        s = Q.preparar_solicitud("L1", [_item()])
        r = Q.evaluar_decision(s, {
            "decision": "APROBADA", "decidida_por": "fundador", "fecha": "2026-09-04",
            "contenido_hashes": [s["items_listos"][0]["contenido_hash"]]})
        self.assertEqual(r["gate_arte"], "CERRADO")
        self.assertEqual(r["publicacion"], "NOT_PUBLISHED")


class TestNoMolestarAntesDeTiempo(unittest.TestCase):
    """Preguntar antes de tiempo gasta la atencion del fundador en algo que el
    agente todavia podia resolver solo."""

    def test_un_item_sin_contenido_no_llega_a_una_persona(self):
        s = Q.preparar_solicitud("L1", [_item(contenido_exacto="")])
        self.assertEqual(s["estado"], Q.INCOMPLETA)
        self.assertEqual(s["items_listos"], [])

    def test_un_item_con_fuentes_sin_leer_no_llega_a_una_persona(self):
        s = Q.preparar_solicitud("L1", [_item(fuentes=[
            {"id": "s1", "verificacion_fuente": {"texto_exacto_consultado": False}}])])
        self.assertEqual(s["estado"], Q.INCOMPLETA)
        self.assertTrue(any("sin texto leido" in f
                            for f in s["items_incompletos"][0]["falta_para_decidir"]))

    def test_un_alcance_sin_determinar_bloquea_la_pregunta(self):
        s = Q.preparar_solicitud("L1", [_item(alcance="NO_DETERMINADO")])
        self.assertEqual(s["estado"], Q.INCOMPLETA)

    def test_el_resumen_separa_lo_humano_de_lo_que_falta_al_agente(self):
        listo = Q.preparar_solicitud("L1", [_item()])
        pendiente = Q.preparar_solicitud("L2", [_item(id="z", contenido_exacto="")])
        r = Q.resumen([listo, pendiente])
        self.assertEqual(r["items_esperando_decision_humana"], 1)
        self.assertEqual(r["items_que_todavia_puede_avanzar_el_agente"], 1)
        self.assertEqual(r["decisiones_humanas_necesarias"], 1)


class TestHash(unittest.TestCase):
    def test_el_hash_es_estable_y_no_depende_del_orden_de_claves(self):
        a = Q.hash_de_contenido({"x": 1, "y": 2})
        b = Q.hash_de_contenido({"y": 2, "x": 1})
        self.assertEqual(a, b)

    def test_una_coma_cambia_el_hash(self):
        a = Q.hash_de_contenido({"t": "El plazo corre desde la entrega"})
        b = Q.hash_de_contenido({"t": "El plazo corre desde la entrega."})
        self.assertNotEqual(a, b)


if __name__ == "__main__":
    unittest.main()
