"""La superficie profesional no puede convertirse en una fuga.

Dos riesgos propios de esta superficie, que el resto del sistema no cubre:

  1. Que la experiencia profesional del fundador se publique como si fuera
     norma. Una inferencia con vocabulario tecnico sigue siendo una inferencia.
  2. Que un caso real se cuele en el texto. Un nombre, un importe, un numero de
     escritura: material identificable en un repositorio publico.

Sin red. Determinista.
"""

import sys
import unittest
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))

import linkedin as L  # noqa: E402


def _pieza(**extra):
    base = {
        "id": "LM-PRO-001",
        "dominio": "gobierno_corporativo",
        "pregunta_profesional": "Como se documenta que una facultad fue ejercida dentro de su alcance",
        "afirmaciones": [{
            "id": "a1", "categoria": L.FACT,
            "texto": "El acta debe reflejar el alcance de la facultad ejercida.",
            "fuentes": [{"id": "s1"}],
        }],
    }
    base.update(extra)
    return base


class TestClasificacionDeAfirmaciones(unittest.TestCase):
    def test_un_fact_sin_fuente_no_pasa(self):
        r = L.evaluar_afirmacion({"id": "a", "categoria": L.FACT, "texto": "x", "fuentes": []})
        self.assertFalse(r["apta_para_preparar"])
        self.assertTrue(any("sin fuente" in p for p in r["problemas"]))

    def test_derived_knowledge_exige_razonamiento_explicito(self):
        """Sin el razonamiento a la vista, es una inferencia disfrazada."""
        r = L.evaluar_afirmacion({"id": "a", "categoria": L.DERIVED_KNOWLEDGE,
                                  "texto": "x", "fuentes": [{"id": "s"}]})
        self.assertFalse(r["apta_para_preparar"])
        self.assertTrue(any("razonamiento" in p for p in r["problemas"]))

    def test_una_inferencia_no_puede_presentarse_como_regla(self):
        r = L.evaluar_afirmacion({"id": "a", "categoria": L.INFERENCE, "texto": "x",
                                  "presentada_como_regla": True})
        self.assertFalse(r["apta_para_preparar"])
        self.assertTrue(any("presentada como regla" in p for p in r["problemas"]))

    def test_solo_fact_y_derived_pueden_sostener_derecho(self):
        """Las categorías con autoridad se escriben LITERALMENTE aquí, no se
        derivan de la constante del módulo. Derivarlas hacía la prueba
        tautológica: añadir INFERENCE a la constante no rompía nada, que es
        exactamente el cambio más peligroso que se podría hacer."""
        self.assertEqual(set(L.CATEGORIAS_CON_AUTORIDAD), {"FACT", "DERIVED_KNOWLEDGE"})
        con_autoridad = {"FACT", "DERIVED_KNOWLEDGE"}
        for cat in L.CATEGORIAS:
            r = L.evaluar_afirmacion({"id": "a", "categoria": cat, "texto": "x",
                                      "fuentes": [{"id": "s"}], "razonamiento": "r",
                                      "autor_identificable": "Autor, Obra (2020)"})
            with self.subTest(categoria=cat):
                self.assertEqual(r["puede_sostener_derecho"], cat in con_autoridad)

    def test_una_opinion_nunca_es_derecho_aunque_traiga_fuente(self):
        """Adjuntar una fuente a una opinión no la convierte en norma."""
        for cat in (L.INFERENCE, L.EDITORIAL, L.EXTERNAL_RESEARCH):
            r = L.evaluar_afirmacion({"id": "a", "categoria": cat, "texto": "x",
                                      "fuentes": [{"id": "s"}],
                                      "autor_identificable": "Autor, Obra (2020)"})
            with self.subTest(categoria=cat):
                self.assertFalse(r["puede_sostener_derecho"])

    def test_external_research_exige_autor_identificable(self):
        """Una atribucion viral no es una fuente."""
        r = L.evaluar_afirmacion({"id": "a", "categoria": L.EXTERNAL_RESEARCH, "texto": "x"})
        self.assertFalse(r["apta_para_preparar"])

    def test_una_categoria_inventada_se_rechaza(self):
        r = L.evaluar_afirmacion({"id": "a", "categoria": "OPINION_EXPERTA", "texto": "x"})
        self.assertFalse(r["apta_para_preparar"])


class TestConfidencialidad(unittest.TestCase):
    """El hueco que la auditoria anterior dejo registrado y sin cerrar."""

    def test_detecta_un_importe(self):
        self.assertTrue(L.detectar_material_identificable("se pactaron $2,500,000 de pena"))
        self.assertTrue(L.detectar_material_identificable("una pena de 3 millones"))

    def test_detecta_un_numero_de_escritura(self):
        self.assertTrue(L.detectar_material_identificable("consta en la escritura 44.812"))
        self.assertTrue(L.detectar_material_identificable("expediente: 214/2024-B"))

    def test_detecta_correo_y_telefono(self):
        self.assertTrue(L.detectar_material_identificable("escribir a alguien@ejemplo.com"))
        self.assertTrue(L.detectar_material_identificable("llamar al +52 55 1234 5678"))

    def test_detecta_una_clausula_textual_larga(self):
        texto = '«' + "El proveedor se obliga de manera irrevocable y solidaria " * 3 + '»'
        self.assertTrue(L.detectar_material_identificable(texto))

    def test_detecta_un_nombre_propio(self):
        self.assertTrue(L.detectar_material_identificable(
            "El caso lo llevaba Ricardo Fuentes en la operacion."))

    def test_un_patron_anonimizado_pasa(self):
        """La experiencia SI se puede usar: como patron, sin caso reconocible."""
        texto = ("Un patron frecuente: la facultad se otorga amplia y se ejerce "
                 "estrecha, y el acta no recoge cual de las dos ocurrio.")
        self.assertEqual(L.detectar_material_identificable(texto), [])

    def test_el_control_automatico_no_se_declara_suficiente(self):
        r = L.evaluar_pieza(_pieza())
        self.assertEqual(r["revision_confidencialidad"], "PENDIENTE")
        self.assertIn("no lo elimina", r["_nota"])


class TestIdentidadPropia(unittest.TestCase):
    def test_una_pieza_sin_pregunta_profesional_no_esta_lista(self):
        r = L.evaluar_pieza(_pieza(pregunta_profesional=""))
        self.assertFalse(r["lista_para_revision_humana"])

    def test_el_mismo_post_con_corbata_se_rechaza(self):
        """Declarar un equivalente publico obliga a decir que anade."""
        r = L.evaluar_pieza(_pieza(equivalente_publico="LM-T-001"))
        self.assertFalse(r["lista_para_revision_humana"])
        self.assertTrue(any("con corbata" in p for p in r["problemas"]))

    def test_declarando_que_anade_si_pasa(self):
        r = L.evaluar_pieza(_pieza(
            equivalente_publico="LM-T-001",
            que_anade_sobre_el_publico="el publico explica la figura; aqui se "
                                       "documenta como se acredita su ejercicio"))
        self.assertTrue(r["lista_para_revision_humana"], r["problemas"])

    def test_el_dominio_debe_estar_en_el_vocabulario(self):
        r = L.evaluar_pieza(_pieza(dominio="growth_hacking"))
        self.assertFalse(r["lista_para_revision_humana"])


class TestInvariantes(unittest.TestCase):
    def test_ninguna_pieza_abre_gate_ni_publica(self):
        for pieza in (_pieza(), _pieza(dominio="cobranza"), _pieza(afirmaciones=[])):
            r = L.evaluar_pieza(pieza)
            with self.subTest(pieza=r["id"]):
                self.assertEqual(r["gate_arte"], "CERRADO")
                self.assertEqual(r["revision_humana"], "PENDIENTE")
                self.assertEqual(r["publicacion"], "NOT_PUBLISHED")
                self.assertEqual(r["estado_juridico"], "REQUIERE_INVESTIGACION")

    def test_lista_para_revision_no_significa_aprobada(self):
        r = L.evaluar_pieza(_pieza())
        self.assertTrue(r["lista_para_revision_humana"])
        self.assertEqual(r["revision_humana"], "PENDIENTE")


if __name__ == "__main__":
    unittest.main()
