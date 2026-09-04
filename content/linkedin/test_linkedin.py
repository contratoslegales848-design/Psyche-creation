"""La superficie profesional alimenta el motor; no lo duplica ni lo relaja.

Tres riesgos propios de esta superficie que ningun otro control cubre:

  1. Que se convierta en un segundo motor de imagen. El motor es `visual/` y ya
     funciona; aqui solo se construye el brief que consume.
  2. Que la experiencia profesional se publique como si fuera norma. Una
     inferencia con vocabulario tecnico sigue siendo una inferencia.
  3. Que un caso real se cuele. El septimo pilar nace de practica documentada, y
     este repositorio es publico.

Sin red. Determinista.
"""

import json
import sys
import unittest
from pathlib import Path

AQUI = Path(__file__).resolve().parent
REPO = AQUI.parent.parent
sys.path.insert(0, str(AQUI))
sys.path.insert(0, str(REPO / "visual"))

import superficie as S  # noqa: E402

DATOS = S.cargar_pilares()

def _tema(i=0, **extra):
    """Un tema del banco con CONTENT_ID, como llegaria desde un artefacto real."""
    t = dict(S.temas(DATOS)[i], content_id="LM-LN-PRUEBA-001")
    t.update(extra)
    return t


ESCENA_OK = {
    "subject": "dos sellos identicos, uno con el mango gastado",
    "environment": "secretaria corporativa al final del dia",
    "camera": "plano detalle cenital",
    "focal_point": "el sello gastado",
    "metaphor": "mismo cargo, facultades distintas",
}


class TestLosTemasVienenDeDrive(unittest.TestCase):
    def test_hay_siete_pilares_con_temas(self):
        self.assertEqual(len(DATOS["pilares"]), 7)
        self.assertTrue(all(p["temas"] for p in DATOS["pilares"]))

    def test_cada_pilar_declara_audiencia_promesa_y_formato(self):
        """Un pilar sin audiencia ni promesa no orienta nada: seria una etiqueta."""
        for p in DATOS["pilares"]:
            with self.subTest(pilar=p["id"]):
                for campo in ("audiencia", "promesa", "formato_editorial",
                              "familia_visual_sugerida"):
                    self.assertTrue(str(p.get(campo, "")).strip(), campo)

    def test_se_declara_la_procedencia_y_su_clasificacion(self):
        """El cuerpo de la estrategia es PROPUESTA/HIPOTESIS en Drive y la
        ampliacion de experiencia es HECHO DOCUMENTADO. Colapsar esa diferencia
        convertiria una hipotesis editorial en un hecho."""
        self.assertIn("Artefacto 05", DATOS["_procedencia"])
        self.assertIn("PROPUESTA / HIPÓTESIS", DATOS["_clasificacion_de_la_fuente"])
        self.assertIn("HECHO DOCUMENTADO", DATOS["_clasificacion_de_la_fuente"])

    def test_el_banco_no_es_una_autorizacion(self):
        self.assertIn("no abre gates", DATOS["_lo_que_este_archivo_no_es"])

    def test_los_ids_de_pilar_son_unicos(self):
        ids = [p["id"] for p in DATOS["pilares"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_ningun_tema_se_repite_entre_pilares(self):
        t = [x["tema"] for x in S.temas(DATOS)]
        self.assertEqual(len(t), len(set(t)))


class TestConfidencialidad(unittest.TestCase):
    """El riesgo propio del septimo pilar: nace de practica real."""

    def test_el_banco_no_contiene_nombres_de_proyecto_ni_clientes(self):
        """El control mas importante de este archivo. Drive cita proyectos reales
        por su nombre; este repositorio es publico y no los recibe."""
        crudo = (AQUI / "pilares-v1.json").read_text(encoding="utf-8")
        datos = json.loads(crudo)
        for p in datos["pilares"]:
            for tema in p["temas"]:
                with self.subTest(tema=tema[:48]):
                    self.assertEqual(S.detectar_material_identificable(tema), [])

    def test_la_deteccion_es_por_patron_y_no_por_lista_literal(self):
        """Una lista de proyectos reales obligaria a escribir esos nombres aqui,
        que es exactamente lo que hay que evitar."""
        self.assertIn("no por lista literal", DATOS["regla_de_privacidad"]["_nota"])
        # Un nombre inventado que nunca aparecio en Drive tambien se detecta.
        self.assertTrue(S.detectar_material_identificable(
            "El caso de Residencial Poniente lo llevaba el area juridica."))

    def test_detecta_importes_escrituras_notarias_y_contacto(self):
        casos = [
            "se pactaron $2,500,000 de pena convencional",
            "una pena de 3 millones",
            "consta en la escritura 44.812",
            "expediente: 214/2024-B",
            "ante la notaria 15 del estado",
            "escribir a alguien@ejemplo.com",
            "llamar al +52 55 1234 5678",
        ]
        for c in casos:
            with self.subTest(caso=c):
                self.assertTrue(S.detectar_material_identificable(c))

    def test_detecta_una_clausula_textual_larga(self):
        texto = "«" + "El proveedor se obliga de manera irrevocable y solidaria " * 3 + "»"
        self.assertTrue(S.detectar_material_identificable(texto))

    def test_un_patron_anonimizado_pasa(self):
        """La experiencia SI se puede usar: como patron, sin caso reconocible."""
        self.assertEqual(S.detectar_material_identificable(
            "Un patron frecuente: la facultad se otorga amplia y se ejerce estrecha, "
            "y el acta no recoge cual de las dos ocurrio."), [])

    def test_el_control_automatico_no_se_declara_suficiente(self):
        r = S.evaluar_pieza(_pieza(), DATOS)
        self.assertEqual(r["revision_confidencialidad"], "PENDIENTE")
        self.assertIn("no lo eliminan", r["_nota"])


class TestClasificacionDeAfirmaciones(unittest.TestCase):
    def test_solo_fact_y_derived_pueden_sostener_derecho(self):
        """Las categorias con autoridad se escriben LITERALMENTE aqui, no se
        derivan de la constante del modulo: derivarlas haria la prueba
        tautologica y anadir INFERENCE no rompería nada."""
        self.assertEqual(set(S.CATEGORIAS_CON_AUTORIDAD), {"FACT", "DERIVED_KNOWLEDGE"})
        for cat in S.CATEGORIAS:
            r = S.evaluar_afirmacion({"id": "a", "categoria": cat, "texto": "x",
                                      "fuentes": [{"id": "s"}], "razonamiento": "r",
                                      "autor_identificable": "Autor, Obra (2020)"})
            with self.subTest(categoria=cat):
                self.assertEqual(r["puede_sostener_derecho"],
                                 cat in ("FACT", "DERIVED_KNOWLEDGE"))

    def test_un_fact_sin_fuente_no_pasa(self):
        r = S.evaluar_afirmacion({"id": "a", "categoria": S.FACT, "texto": "x", "fuentes": []})
        self.assertFalse(r["apta_para_preparar"])

    def test_derived_knowledge_exige_razonamiento_explicito(self):
        """Sin el razonamiento a la vista es una inferencia disfrazada."""
        r = S.evaluar_afirmacion({"id": "a", "categoria": S.DERIVED_KNOWLEDGE,
                                  "texto": "x", "fuentes": [{"id": "s"}]})
        self.assertFalse(r["apta_para_preparar"])

    def test_una_opinion_no_puede_presentarse_como_regla(self):
        r = S.evaluar_afirmacion({"id": "a", "categoria": S.INFERENCE, "texto": "x",
                                  "presentada_como_regla": True})
        self.assertFalse(r["apta_para_preparar"])


class TestPuenteAlMotorExistente(unittest.TestCase):
    """No hay motor nuevo: se construye el brief que `visual/` ya consume."""

    def test_el_brief_usa_el_formato_que_la_politica_ya_declaraba(self):
        from brief import VisualPolicy
        br = S.construir_brief(_tema(), ESCENA_OK, DATOS)
        self.assertEqual(br.formato, "SOCIAL_4_5")
        self.assertEqual(VisualPolicy.load().formato(br.formato)["aspect_ratio"], "4:5")

    def test_todas_las_familias_sugeridas_existen_en_el_motor(self):
        """La superficie no declara familias propias: si inventara una, el
        compilador la rechazaria en produccion y no aqui."""
        from families import VisualFamilyRegistry
        disponibles = set(VisualFamilyRegistry.load().names())
        for p in DATOS["pilares"]:
            with self.subTest(pilar=p["id"]):
                self.assertIn(p["familia_visual_sugerida"], disponibles)

    def test_una_familia_inventada_se_rechaza(self):
        tema = _tema(familia_visual="art_deco_neon")
        with self.assertRaises(ValueError):
            S.construir_brief(tema, ESCENA_OK, DATOS)

    def test_una_escena_sin_dirigir_se_rechaza(self):
        """Una escena por plantilla produce piezas intercambiables."""
        for falta in ESCENA_OK:
            escena = dict(ESCENA_OK, **{falta: ""})
            with self.subTest(sin=falta), self.assertRaises(ValueError):
                S.construir_brief(_tema(), escena, DATOS)

    def test_el_brief_no_fija_negative_space(self):
        """Lo deriva el pipeline del texto real; escribirlo aqui lo pisaria."""
        br = S.construir_brief(_tema(), ESCENA_OK, DATOS)
        self.assertEqual(br.negative_space, "")

    def test_el_brief_compila_en_el_motor_real(self):
        """La prueba de que el cableado es real y no una promesa."""
        from compiler import compile_request
        from brief import VisualPolicy
        from families import VisualFamilyRegistry
        from providers.fake import FakeImageProvider
        import dataclasses
        br = S.construir_brief(_tema(), ESCENA_OK, DATOS)
        fams = VisualFamilyRegistry.load()
        c = compile_request(br, VisualPolicy.load(), family=fams.get(br.visual_family),
                            capabilities=FakeImageProvider().capabilities())
        d = dataclasses.asdict(c)
        self.assertEqual(d["requested_aspect_ratio"], "4:5")
        self.assertEqual(tuple(d["requested_dimensions"]), (1080, 1350))
        self.assertEqual(d["text_mode"], "POST_COMPOSITE")
        self.assertIn(ESCENA_OK["metaphor"], d["positive_prompt"])


class TestIdentidadPropiaYPolitica(unittest.TestCase):
    def test_una_pieza_sin_pregunta_profesional_no_esta_lista(self):
        r = S.evaluar_pieza(_pieza(pregunta_profesional=""), DATOS)
        self.assertFalse(r["lista_para_revision_humana"])

    def test_el_mismo_post_con_corbata_se_rechaza(self):
        r = S.evaluar_pieza(_pieza(equivalente_publico="LM-T-001"), DATOS)
        self.assertFalse(r["lista_para_revision_humana"])
        self.assertTrue(any("con corbata" in p for p in r["problemas"]))

    def test_declarando_que_anade_si_pasa(self):
        r = S.evaluar_pieza(_pieza(
            equivalente_publico="LM-T-001",
            que_anade_sobre_el_publico="el publico explica la figura; aqui se "
                                       "documenta como se acredita su ejercicio"), DATOS)
        self.assertTrue(r["lista_para_revision_humana"], r["problemas"])

    def test_el_cta_por_defecto_no_abre_consultas(self):
        """Hasta que exista preflight operativo, LinkedIn construye autoridad."""
        self.assertEqual(S.cta_para("", DATOS), "SIN_CTA")
        self.assertEqual(S.cta_para("ANALISIS_DE_AUTORIDAD", DATOS), "SIN_CTA")
        self.assertEqual(S.cta_para("CHECKLIST_EDUCATIVO", DATOS), "SOFT_CTA")
        self.assertIn("PREFLIGHT", S.cta_para("PRODUCTO", DATOS))

    def test_un_pilar_desconocido_se_rechaza(self):
        r = S.evaluar_pieza(_pieza(pilar_id="LN-P99-INVENTADO"), DATOS)
        self.assertFalse(r["lista_para_revision_humana"])


class TestNoRelajaNingunControl(unittest.TestCase):
    def test_ninguna_pieza_abre_gate_ni_publica(self):
        for extra in ({}, {"pilar_id": "LN-P7-OPERACIONES-INMOBILIARIAS"}, {"afirmaciones": []}):
            r = S.evaluar_pieza(_pieza(**extra), DATOS)
            with self.subTest(extra=extra):
                self.assertEqual(r["gate_arte"], "CERRADO")
                self.assertEqual(r["revision_humana"], "PENDIENTE")
                self.assertEqual(r["publicacion"], "NOT_PUBLISHED")
                self.assertEqual(r["estado_juridico"], "REQUIERE_INVESTIGACION")

    def test_lista_para_revision_no_significa_aprobada(self):
        r = S.evaluar_pieza(_pieza(), DATOS)
        self.assertTrue(r["lista_para_revision_humana"])
        self.assertEqual(r["revision_humana"], "PENDIENTE")

    def test_el_gate_del_motor_sigue_cerrando_una_pieza_sin_handoff(self):
        """Comprobacion contra el motor real: una pieza de LinkedIn necesita la
        misma cadena que una publica. EJEMPLO_TECNICO nunca genera."""
        import gates
        d = gates.can_enter_visual_generation(
            {"modo": "EJEMPLO_TECNICO", "content_id": "LM-LN-X", "publicable": False},
            None)
        self.assertFalse(d.permitido)


def _pieza(**extra):
    base = {
        "id": "LM-LN-001",
        "pilar_id": "LN-P2-REPRESENTACION",
        "tipo_de_pieza": "ANALISIS_DE_AUTORIDAD",
        "pregunta_profesional": "Como se acredita que quien firmo podia obligar a la sociedad",
        "afirmaciones": [{
            "id": "a1", "categoria": S.FACT,
            "texto": "El acta debe reflejar el alcance de la facultad ejercida.",
            "fuentes": [{"id": "s1"}],
        }],
    }
    base.update(extra)
    return base


if __name__ == "__main__":
    unittest.main()
