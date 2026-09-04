"""El motor de temas no puede convertirse en una vía para publicar sin fuentes.

Dos riesgos, opuestos, y las pruebas cubren los dos:

  1. Que el motor deje pasar lo nacional disfrazado de transversal — la falsa
     universalización que ya ocurrió en el último lote.
  2. Que el propio motor se lea como una autorización, porque produce briefs con
     aspecto de estar listos. Un brief NO abre nada.

Sin red. Determinista.
"""

import json
import sys
import unittest
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))

import brief as B  # noqa: E402
import lote as L  # noqa: E402
import transversality as T  # noqa: E402

# Procedencia que acredita autoridad canonica. Se escribe en las pruebas, nunca
# la produce el loader: ninguna lectura del repositorio puede fabricarla.
PROCEDENCIA_OK = {"drive_file_id": "1FICTICIO", "exportado_en": "2026-09-04",
                  "exportado_por": "fundador"}

CATALOGO = T.cargar_catalogo()
TEMAS = CATALOGO["temas"]
REPO = AQUI.parent.parent


class TestCatalogo(unittest.TestCase):
    def test_hay_temas(self):
        self.assertTrue(TEMAS)

    def test_ids_y_conceptos_unicos(self):
        """Dos temas con el mismo concepto competirían por la misma casilla de la
        taxonomía y uno de los dos no podría producirse nunca."""
        self.assertEqual(len({t["id"] for t in TEMAS}), len(TEMAS))
        self.assertEqual(len({t["concepto"] for t in TEMAS}), len(TEMAS))

    def test_todo_tema_declara_su_hipotesis(self):
        """Sin esa justificación, 'transversal' sería una etiqueta, no un juicio."""
        for t in TEMAS:
            with self.subTest(tema=t["id"]):
                self.assertGreater(len(t["hipotesis_de_transversalidad"]), 40)

    def test_todo_tema_declara_donde_puede_derivar(self):
        """La advertencia dice qué parte del asunto SÍ es nacional. Un tema que no
        lo sabe todavía no está estudiado."""
        for t in TEMAS:
            with self.subTest(tema=t["id"]):
                self.assertTrue(t["advertencia"].strip())
                self.assertIn(t["riesgo_de_deriva_nacional"], T.RIESGOS_VALIDOS)


class TestBarreraDeTransversalidad(unittest.TestCase):
    def test_todo_el_catalogo_pasa_la_barrera(self):
        for d in T.evaluar_catalogo():
            with self.subTest(tema=d["id"]):
                self.assertTrue(d["admisible_como_tema"],
                                f"{d['anclajes_nacionales']} {d['errores_de_forma']}")

    def test_un_tema_que_nombra_un_pais_es_rechazado(self):
        malo = dict(TEMAS[0], id="LM-T-X",
                    pregunta_central="¿Qué dice el derecho en México sobre esto?")
        d = T.evaluar_tema(malo)
        self.assertFalse(d["admisible_como_tema"])
        self.assertTrue(any("país" in m for m in d["anclajes_nacionales"]))

    def test_un_tema_que_cita_una_norma_nacional_es_rechazado(self):
        malo = dict(TEMAS[0], id="LM-T-X",
                    hipotesis_de_transversalidad="Lo regula el Código Civil y basta con eso.")
        d = T.evaluar_tema(malo)
        self.assertFalse(d["admisible_como_tema"])

    def test_un_tema_que_fija_un_plazo_es_rechazado(self):
        """Los plazos son la deriva nacional más frecuente y la más invisible."""
        malo = dict(TEMAS[0], id="LM-T-X",
                    titulo_de_trabajo="La deuda se extingue a los 5 años")
        d = T.evaluar_tema(malo)
        self.assertFalse(d["admisible_como_tema"])
        self.assertTrue(any("plazo" in m for m in d["anclajes_nacionales"]))

    def test_un_tema_con_moneda_es_rechazado(self):
        malo = dict(TEMAS[0], id="LM-T-X",
                    pregunta_central="¿Y si la deuda es de mil euros?")
        self.assertFalse(T.evaluar_tema(malo)["admisible_como_tema"])

    def test_la_deteccion_es_por_palabra_no_por_subcadena(self):
        """'peru' dentro de otra palabra no puede disparar un rechazo: un filtro
        que se dispara solo empuja a desactivarlo."""
        self.assertEqual(T.detectar_anclajes_nacionales("perutenencia superusuario"), [])

    def test_las_tildes_no_permiten_esquivar_el_filtro(self):
        self.assertTrue(T.detectar_anclajes_nacionales("en Mexico"))
        self.assertTrue(T.detectar_anclajes_nacionales("en México"))
        self.assertTrue(T.detectar_anclajes_nacionales("en MÉXICO"))

    def test_la_advertencia_no_penaliza_por_nombrar_lo_nacional(self):
        """La advertencia es justo donde el catálogo debe decir qué varía por
        país. Si el filtro la leyera, premiaría callarlo."""
        texto = T.texto_de_tema({"advertencia": "En España el plazo es de 5 años"})
        self.assertEqual(T.detectar_anclajes_nacionales(texto), [])


class TestCoberturaReal(unittest.TestCase):
    """La prosa limpia no basta: lo que cuenta son las fuentes."""

    def setUp(self):
        self.reg = T.cargar_registro()

    def test_el_registro_se_carga(self):
        self.assertGreaterEqual(len(self.reg), 26)

    def test_una_sola_jurisdiccion_no_sostiene_capa_a(self):
        claim = {"claim_id": "x", "alcance": "CAPA_A_TRANSVERSAL",
                 "fuentes": [{"id": "f1", "registro_oficial_id": "dof-gob-mx"}]}
        r = T.evaluar_cobertura_de_claim(claim, self.reg)
        self.assertFalse(r["cobertura_comparada_suficiente"])
        self.assertEqual(r["sostenible_por_la_evidencia"], "CAPA_C_NACIONAL")
        self.assertEqual(r["riesgo_falsa_universalizacion"], "alto")
        self.assertTrue(any("falsa universalización" in p for p in r["problemas"]))

    def test_tres_jurisdicciones_si_la_sostienen(self):
        claim = {"claim_id": "x", "alcance": "CAPA_A_TRANSVERSAL", "fuentes": [
            {"id": "f1", "registro_oficial_id": "dof-gob-mx"},
            {"id": "f2", "registro_oficial_id": "boe-es"},
            {"id": "f3", "registro_oficial_id": "infoleg-gob-ar"}]}
        r = T.evaluar_cobertura_de_claim(claim, self.reg)
        self.assertTrue(r["cobertura_comparada_suficiente"])
        self.assertEqual(len(r["paises_cubiertos_por_fuentes"]), 3)

    def test_una_fuente_supranacional_no_suma_jurisdiccion_nacional(self):
        """Si sumara, un solo tratado convertiría en transversal cualquier cosa."""
        claim = {"claim_id": "x", "alcance": "CAPA_A_TRANSVERSAL", "fuentes": [
            {"id": "f1", "registro_oficial_id": "dof-gob-mx"},
            {"id": "f2", "registro_oficial_id": "eur-lex-europa-eu"},
            {"id": "f3", "registro_oficial_id": "corteidh-or-cr"}]}
        r = T.evaluar_cobertura_de_claim(claim, self.reg)
        self.assertEqual(r["paises_cubiertos_por_fuentes"], ["mexico"])
        self.assertFalse(r["cobertura_comparada_suficiente"])

    def test_una_fuente_sin_registro_no_cubre_nada(self):
        claim = {"claim_id": "x", "alcance": "CAPA_A_TRANSVERSAL",
                 "fuentes": [{"id": "f1", "registro_oficial_id": None}]}
        r = T.evaluar_cobertura_de_claim(claim, self.reg)
        self.assertEqual(r["paises_cubiertos_por_fuentes"], [])

    def test_un_registro_ausente_deja_la_cobertura_en_cero(self):
        """Fail-closed: sin registro, ninguna fuente cubre nada."""
        self.assertEqual(T.cargar_registro(AQUI / "no-existe.json"), {})

    def test_ningun_packet_real_declara_capa_a_sin_sostenerla(self):
        """Prueba de realidad sobre los claim packets que existen hoy: ninguno
        puede declararse transversal sin tres jurisdicciones con fuente propia."""
        packets = sorted((REPO / "content" / "claim-packets").glob("*.json"))
        if not packets:
            self.skipTest("no hay claim packets en esta rama")
        for ruta in packets:
            datos = json.loads(ruta.read_text(encoding="utf-8"))
            for claim in datos.get("claims", []):
                r = T.evaluar_cobertura_de_claim(claim, self.reg)
                if r["alcance_declarado"] != "CAPA_A_TRANSVERSAL":
                    continue
                with self.subTest(claim=r["claim_id"]):
                    self.assertTrue(
                        r["cobertura_comparada_suficiente"],
                        f"{r['claim_id']} se declara transversal con "
                        f"{r['paises_cubiertos_por_fuentes']}")


class TestBriefNoAutorizaNada(unittest.TestCase):
    def setUp(self):
        self.briefs = B.construir_todos()

    def test_hay_un_brief_por_tema(self):
        self.assertEqual(len(self.briefs), len(TEMAS))

    def test_ningun_brief_abre_gate_ni_aprueba(self):
        """El control central de este módulo."""
        for b in self.briefs:
            with self.subTest(tema=b["tema_id"]):
                self.assertEqual(b["gate_arte"], "CERRADO")
                self.assertEqual(b["estado_juridico"], "REQUIERE_INVESTIGACION")
                self.assertEqual(b["revision_humana"], "PENDIENTE")
                self.assertEqual(b["publicacion"], "NOT_PUBLISHED")

    def test_el_copy_se_entrega_vacio(self):
        """Un copy prerrellenado sería una afirmación sin fuente disfrazada de
        plantilla. Solo el cierre jurisdiccional viene escrito, porque no afirma
        nada: advierte."""
        for b in self.briefs:
            with self.subTest(tema=b["tema_id"]):
                for hueco in ("apertura", "explicacion", "por_que_importa",
                              "en_la_practica", "remate"):
                    self.assertEqual(b["copy"][hueco], "")
                self.assertIn("variar", b["copy"]["cierre_jurisdiccional"])

    def test_ningun_brief_contiene_un_ancla_nacional(self):
        """El brief se serializa entero y se vuelve a pasar por el filtro: si el
        motor introdujera un país por su cuenta, aquí se vería."""
        for b in self.briefs:
            texto = json.dumps({k: v for k, v in b.items()
                                if k != "pendiente_antes_de_producir"},
                               ensure_ascii=False)
            with self.subTest(tema=b["tema_id"]):
                self.assertEqual(T.detectar_anclajes_nacionales(texto), [])

    def test_la_familia_visual_existe_en_el_registro_del_repositorio(self):
        fams = set(B.cargar_familias())
        for b in self.briefs:
            with self.subTest(tema=b["tema_id"]):
                self.assertIn(b["imagen"]["familia_visual"], fams)

    def test_la_animacion_respeta_el_arco_y_las_invariantes(self):
        for b in self.briefs:
            with self.subTest(tema=b["tema_id"]):
                self.assertEqual(tuple(b["animacion"]["arco"]), B.ARCO_ANIMACION)
                self.assertTrue(b["animacion"]["micro_evento"])
                self.assertIn("no borrar", b["animacion"]["propuesta_de_prompt_NO_EJECUTABLE"])
                self.assertTrue(any("texto montado no se borra" in i
                                    for i in b["animacion"]["invariantes"]))

    def test_el_micro_evento_corresponde_al_formato(self):
        for b in self.briefs:
            with self.subTest(tema=b["tema_id"]):
                self.assertIn(b["animacion"]["micro_evento"],
                              B.MICROEVENTOS[b["formato_editorial"]])

    def test_la_marca_nunca_es_marca_de_agua(self):
        for b in self.briefs:
            with self.subTest(tema=b["tema_id"]):
                self.assertIn("flotante", b["imagen"]["marca"]["prohibido"])
                self.assertIn(b["imagen"]["marca"]["superficie_sugerida"],
                              B.SUPERFICIES_DE_MARCA)

    def test_el_formato_sale_de_la_politica_y_es_de_una_sola_escena(self):
        """El formato ya NO es 9:16 fijo: lo elige la forma editorial, porque
        un listado numerado y una maxima de una linea no necesitan el mismo
        alto ni los recorta igual el feed.

        Lo que sigue siendo invariante, y es lo que esta prueba protege: las
        dimensiones vienen de la politica visual real (no escritas a mano en
        este modulo, que era el defecto anterior) y la escena es una sola,
        nunca collage."""
        formatos = B.cargar_formatos()
        for b in self.briefs:
            with self.subTest(tema=b["tema_id"]):
                nombre = b["imagen"]["formato"]
                self.assertIn(nombre, formatos, "el formato tiene que existir en la politica")
                declarado = formatos[nombre]
                self.assertEqual(b["imagen"]["aspecto"], declarado["aspect_ratio"])
                self.assertEqual((b["imagen"]["ancho"], b["imagen"]["alto"]),
                                 (declarado["width"], declarado["height"]))
                self.assertIn("collage", b["imagen"]["escena"])

    def test_el_lote_no_usa_un_solo_formato(self):
        """El motivo del cambio: 24 candidatos con el mismo formato producen
        un feed uniforme. Si alguien vuelve a fijarlo, esto lo detecta."""
        usados = {b["imagen"]["formato"] for b in self.briefs}
        self.assertGreater(len(usados), 1, f"el lote entero salio en un solo formato: {usados}")

    def test_una_forma_editorial_sin_mapear_no_inventa_dimensiones(self):
        """Cae al formato por defecto declarado, nunca a un tamano inventado."""
        nombre, dims = B.formato_para("FORMA_QUE_NO_EXISTE")
        self.assertEqual(nombre, B.FORMATO_POR_DEFECTO)
        self.assertEqual(dims["ancho"], B.cargar_formatos()[B.FORMATO_POR_DEFECTO]["width"])

    def test_un_formato_mapeado_pero_ausente_de_la_politica_falla_claro(self):
        """Silenciarlo serviria un formato que nadie eligio."""
        with self.assertRaises(KeyError):
            B.formato_para("LISTADO", formatos={"OTRO": {"aspect_ratio": "1:1",
                                                         "width": 1, "height": 1}})

    def test_un_tema_no_transversal_no_recibe_brief(self):
        """Producir arte para un tema que habrá que reclasificar es gasto tirado."""
        malo = dict(TEMAS[0], id="LM-T-X",
                    titulo_de_trabajo="Lo que dice la ley en Colombia")
        r = B.construir_brief(malo)
        self.assertIsNone(r["brief"])
        self.assertFalse(r["dictamen"]["admisible_como_tema"])

    def test_el_motor_es_determinista(self):
        """Dos ejecuciones idénticas producen el mismo brief: si no, el brief no
        sería auditable contra lo que se aprobó."""
        self.assertEqual(json.dumps(self.briefs, ensure_ascii=False, sort_keys=True),
                         json.dumps(B.construir_todos(), ensure_ascii=False, sort_keys=True))

    def test_el_motor_no_escribe_nada(self):
        antes = CATALOGO
        B.construir_todos()
        self.assertEqual(T.cargar_catalogo(), antes)


class TestNoSobreafirmar(unittest.TestCase):
    """Las pruebas que impiden que el motor prometa mas de lo que demuestra."""

    def test_ausencia_de_pais_no_equivale_a_capa_a(self):
        """El error central corregido: un texto sin topónimos no dice nada sobre
        el derecho de ningún país. Cuatro de las diez piezas del último lote
        estaban escritas sin un solo país y describían el de uno solo."""
        d = T.evaluar_tema(TEMAS[0])
        self.assertTrue(d["admisible_como_tema"])
        self.assertEqual(d["demostrado_por_el_filtro"], T.NO_EXPLICIT_NATIONAL_ANCHOR)
        self.assertEqual(d["capa_jurisdiccional"], "NO_DETERMINADO")
        # La capa solo puede aparecer dentro del propio descargo, nunca como
        # valor de un campo: eso seria concederla.
        valores = [v for k, v in d.items() if not k.startswith("_")]
        self.assertNotIn("CAPA_A_TRANSVERSAL", json.dumps(valores, ensure_ascii=False))
        self.assertIn("CAPA_A_TRANSVERSAL", d["_no_demostrado"])

    def test_todo_candidato_sale_como_topic_candidate(self):
        """El motor emite el primer escalón y no puede conceder ninguno de los
        otros tres."""
        for d in T.evaluar_catalogo():
            with self.subTest(tema=d["id"]):
                self.assertEqual(d["estado_epistemico"], T.TOPIC_CANDIDATE)
                self.assertNotEqual(d["estado_epistemico"], T.VERIFIED_CLAIM)
                self.assertNotEqual(d["estado_epistemico"], T.HUMAN_APPROVED_CONTENT)

    def test_las_justificaciones_son_hipotesis_no_hechos(self):
        """'Es común a toda la tradición civil' es una proposición jurídica sobre
        más de veinte ordenamientos. Puede sostenerse como hipótesis; no puede
        afirmarse sin haber leído ninguno."""
        for t_ in TEMAS:
            with self.subTest(tema=t_["id"]):
                self.assertEqual(t_["estado_epistemico"], "LEGAL_HYPOTHESIS")
                self.assertEqual(t_["evidencia_por_jurisdiccion"], [])

    def test_tres_paises_no_se_describen_como_toda_la_comunidad(self):
        """Tres jurisdicciones demuestran cobertura comparada de esas tres. Hay
        más de veinte ordenamientos hispanohablantes."""
        reg = T.cargar_registro()
        claim = {"claim_id": "x", "alcance": "CAPA_A_TRANSVERSAL", "fuentes": [
            {"id": "f1", "registro_oficial_id": "dof-gob-mx"},
            {"id": "f2", "registro_oficial_id": "boe-es"},
            {"id": "f3", "registro_oficial_id": "infoleg-gob-ar"}]}
        r = T.evaluar_cobertura_de_claim(claim, reg)
        self.assertTrue(r["cobertura_comparada_suficiente"])
        self.assertFalse(r["es_universalidad_panhispanica"])
        self.assertEqual(sorted(r["cobertura_comparada_de"]),
                         ["argentina", "espana", "mexico"])
        self.assertIn("No se extrapola", r["_nota_alcance"])

    def test_ningun_estado_tecnico_abre_aprobacion_arte_ni_publicacion(self):
        briefs = B.construir_todos()
        for b in briefs:
            with self.subTest(tema=b["tema_id"]):
                self.assertEqual(b["gate_arte"], "CERRADO")
                self.assertEqual(b["revision_humana"], "PENDIENTE")
                self.assertEqual(b["publicacion"], "NOT_PUBLISHED")
                texto = json.dumps(b, ensure_ascii=False)
                for prohibido in ("APROBADO", "APPROVED", "AUTORIZAD", "PUBLICABLE"):
                    self.assertNotIn(prohibido, texto.upper())


class TestDiversidadEditorial(unittest.TestCase):
    def test_un_lote_de_diez_identico_en_forma_falla(self):
        lote = [{"forma_editorial": "MITO", "concepto": f"c{i}", "angulo": "a",
                 "situacion_humana": "s", "utilidad": "u"} for i in range(10)]
        r = L.evaluar_diversidad(lote)
        self.assertFalse(r["diverso"])
        self.assertTrue(any("formas editoriales distintas" in p for p in r["problemas"]))
        self.assertTrue(any("aparece 10 veces" in p for p in r["problemas"]))

    def test_un_lote_con_cinco_formas_y_maximo_dos_repeticiones_pasa(self):
        formas = ["MITO", "MITO", "DIFERENCIAS", "DIFERENCIAS", "CONCEPTO",
                  "CONCEPTO", "APRENDIZAJE", "APRENDIZAJE", "PREGUNTA_COMUN",
                  "ERROR_FRECUENTE"]
        lote = [{"forma_editorial": f, "concepto": f"c{i}", "angulo": f"a{i}",
                 "situacion_humana": f"s{i}", "utilidad": f"u{i}"}
                for i, f in enumerate(formas)]
        r = L.evaluar_diversidad(lote)
        self.assertTrue(r["diverso"], r["problemas"])
        self.assertGreaterEqual(r["formas_distintas"], L.MINIMO_FORMAS_DISTINTAS)

    def test_cambiar_solo_la_forma_no_convierte_lo_repetido_en_nuevo(self):
        """Dos piezas que coinciden en concepto, ángulo, situación y utilidad son
        la misma pieza con otra ropa, aunque cambie el formato."""
        lote = [{"forma_editorial": "MITO", "concepto": "c", "angulo": "a",
                 "situacion_humana": "s", "utilidad": "u"},
                {"forma_editorial": "CONCEPTO", "concepto": "c", "angulo": "a",
                 "situacion_humana": "s", "utilidad": "u"}]
        r = L.evaluar_diversidad(lote)
        self.assertFalse(r["diverso"])
        self.assertTrue(any("misma pieza con otra ropa" in p for p in r["problemas"]))

    def test_organizar_un_lote_no_aprueba_nada(self):
        r = L.evaluar_diversidad([{"forma_editorial": "MITO", "concepto": "c",
                                   "angulo": "a", "situacion_humana": "s",
                                   "utilidad": "u"}])
        self.assertFalse(r["aprueba_claims"])
        self.assertFalse(r["abre_gate"])
        self.assertFalse(r["autoriza_publicacion"])

    def test_el_catalogo_puede_producir_un_lote_diverso(self):
        """Prueba de realidad: si el pozo no da para cinco formas, la regla es
        decorativa. Con doce DIFERENCIAS de veinticuatro no daba."""
        from collections import Counter
        formas = Counter(t["forma_editorial"] for t in TEMAS)
        self.assertGreaterEqual(len(formas), L.MINIMO_FORMAS_DISTINTAS)
        self.assertGreaterEqual(sum(1 for n in formas.values() if n >= 1),
                                L.MINIMO_FORMAS_DISTINTAS)

    def test_la_forma_editorial_real_llega_a_la_taxonomia(self):
        """Fijar todos los briefs como content_type='concepto' borraba la única
        señal que permite ver que un lote está repitiendo formato."""
        vistos = set()
        for b in B.construir_todos():
            with self.subTest(tema=b["tema_id"]):
                self.assertEqual(b["taxonomia"]["content_type"], b["formato_editorial"])
                self.assertTrue(b["taxonomia"]["angulo"])
                self.assertTrue(b["taxonomia"]["utilidad"])
            vistos.add(b["taxonomia"]["content_type"])
        self.assertGreater(len(vistos), 1, "todos los briefs comparten content_type")


class TestOrdenDelPipeline(unittest.TestCase):
    def test_la_ficha_no_es_ejecutable(self):
        """Un prompt con aspecto de listo, junto a un gate cerrado, es una
        invitación a saltárselo."""
        for b in B.construir_todos():
            with self.subTest(tema=b["tema_id"]):
                self.assertFalse(b["ejecutable"])
                self.assertEqual(b["etapa_del_pipeline"], "candidato")
                self.assertIn("gate_de_arte", b["etapas_pendientes_antes_del_arte"])
                self.assertNotIn("prompt", b["animacion"])

    def test_el_gate_de_arte_va_despues_de_la_revision_humana(self):
        i = B.PIPELINE.index("revision_humana")
        j = B.PIPELINE.index("gate_de_arte")
        k = B.PIPELINE.index("autorizacion_humana_de_publicacion")
        self.assertLess(i, j)
        self.assertLess(j, k)
        self.assertEqual(B.PIPELINE[-1], "autorizacion_humana_de_publicacion")


class TestMemoriaAntiRepeticion(unittest.TestCase):
    def test_el_inventario_real_se_consulta(self):
        _inv, estado, _det = L.cargar_inventario()
        self.assertEqual(estado, L.INVENTARIO_REPO_COMPLETO)

    def test_sin_inventario_no_se_declara_novedad(self):
        """La respuesta honesta cuando no se pudo comprobar no es 'es nuevo'."""
        r = L.evaluar_novedad({"id": "X", "concepto": "loquesea"},
                              inventario=[], estado_inventario=L.INVENTARIO_INCOMPLETO)
        self.assertFalse(r["puede_declararse_nuevo_globalmente"])
        self.assertEqual(r["estado_inventario"], L.INVENTARIO_INCOMPLETO)

    def test_un_concepto_ya_ocupado_no_es_nuevo(self):
        inv = [{"origen": "content/pieza-01-reales.json", "concepto": "propiedad_y_posesion",
                "situacion_humana": "", "angulo": "", "utilidad": "", "conexion_juridica": ""}]
        r = L.evaluar_novedad({"id": "X", "concepto": "propiedad_y_posesion"},
                              inventario=inv, estado_inventario=L.INVENTARIO_CANONICO,
                              procedencia_canonica=PROCEDENCIA_OK)
        self.assertEqual(r["veredicto"], "REPETICION")
        self.assertFalse(r["puede_declararse_nuevo_globalmente"])

    def test_ids_distintos_entre_si_no_bastan(self):
        """Comprobar que los ids del lote nuevo son distintos ENTRE SÍ no
        demuestra nada sobre lo ya producido."""
        inv, estado, _ = L.cargar_inventario()
        resultados = [L.evaluar_novedad(t_, inv, estado) for t_ in TEMAS]
        self.assertTrue(all("estado_inventario" in r for r in resultados))
        self.assertTrue(all(r["motivo"] for r in resultados))


class TestBloqueosSemanticosCorregidos(unittest.TestCase):
    """Las seis comprobaciones que el fundador exigió tras revertir el desvío."""

    def setUp(self):
        self.reg = T.cargar_registro()

    # --- 1 y 2: reutilizar un concepto NO es repetirlo ---------------------
    def test_mismo_concepto_con_aportacion_distinta_puede_ramificarse(self):
        """Una materia se construye volviendo sobre el mismo concepto desde otro
        sitio. Prohibirlo habría hecho el motor inservible."""
        inv = [{"origen": "content/a.json", "concepto": "posesion",
                "angulo": "separar figuras", "situacion_humana": "lleva anios ahi",
                "utilidad": "evitar confusion", "conexion_juridica": "usucapion"}]
        candidato = {"id": "X", "concepto": "posesion",
                     "angulo": "que prueba la posesion",
                     "situacion_humana": "lleva anios ahi",
                     "utilidad": "evitar confusion", "conexion_juridica": "usucapion"}
        r = L.evaluar_novedad(candidato, inv, L.INVENTARIO_CANONICO, PROCEDENCIA_OK)
        self.assertEqual(r["veredicto"], "RAMIFICACION")
        self.assertTrue(r["puede_declararse_nuevo_globalmente"])
        self.assertIn("angulo", r["ramifica_sobre"][0]["aporta_en"])

    def test_misma_combinacion_sustantiva_se_detecta_como_repeticion(self):
        base = {"concepto": "posesion", "angulo": "a", "situacion_humana": "s",
                "utilidad": "u", "conexion_juridica": "c"}
        inv = [dict(base, origen="content/a.json")]
        r = L.evaluar_novedad(dict(base, id="X"), inv, L.INVENTARIO_CANONICO, PROCEDENCIA_OK)
        self.assertEqual(r["veredicto"], "REPETICION")
        self.assertFalse(r["puede_declararse_nuevo_globalmente"])

    def test_cambiar_solo_la_forma_editorial_no_evita_la_repeticion(self):
        """La forma y el soporte NO son dimensiones sustantivas: incluirlas
        habría dado coartada para repetir cambiando de envase."""
        base = {"concepto": "posesion", "angulo": "a", "situacion_humana": "s",
                "utilidad": "u", "conexion_juridica": "c"}
        inv = [dict(base, origen="content/a.json", forma_editorial="MITO")]
        r = L.evaluar_novedad(dict(base, id="X", forma_editorial="CARRUSEL"),
                              inv, L.INVENTARIO_CANONICO, PROCEDENCIA_OK)
        self.assertEqual(r["veredicto"], "REPETICION")

    def test_un_campo_vacio_no_cuenta_como_aportacion(self):
        """Omitir no es aportar."""
        inv = [{"origen": "a", "concepto": "c", "angulo": "algo",
                "situacion_humana": "s", "utilidad": "u", "conexion_juridica": "cj"}]
        r = L.evaluar_novedad({"id": "X", "concepto": "c", "angulo": "",
                               "situacion_humana": "s", "utilidad": "u",
                               "conexion_juridica": "cj"},
                              inv, L.INVENTARIO_CANONICO, PROCEDENCIA_OK)
        self.assertEqual(r["veredicto"], "SIN_APORTACION_DEMOSTRABLE")

    # --- 3: alcance de la comprobación ------------------------------------
    def test_un_inventario_local_parcial_no_declara_novedad_global(self):
        r = L.evaluar_novedad({"id": "X", "concepto": "loquesea"},
                              [], L.INVENTARIO_LOCAL)
        self.assertEqual(r["veredicto"], "NO_ENCONTRADO_EN_EL_REPOSITORIO")
        self.assertFalse(r["puede_declararse_nuevo_globalmente"])
        self.assertIn("solo el repositorio", r["alcance_de_la_comprobacion"])
        self.assertIn("Drive NO se ha consultado", r["alcance_de_la_comprobacion"])

    def test_un_inventario_incompleto_tampoco(self):
        r = L.evaluar_novedad({"id": "X", "concepto": "loquesea"},
                              [], L.INVENTARIO_INCOMPLETO)
        self.assertFalse(r["puede_declararse_nuevo_globalmente"])

    def test_los_tres_estados_de_inventario_son_distintos(self):
        self.assertEqual(len({L.INVENTARIO_LOCAL, L.INVENTARIO_REPO_COMPLETO,
                              L.INVENTARIO_CANONICO, L.INVENTARIO_INCOMPLETO}), 4)
        self.assertEqual(L.ESTADOS_QUE_PERMITEN_NOVEDAD_GLOBAL, (L.INVENTARIO_CANONICO,))

    # --- 4: tres jurisdicciones NO producen Capa A -------------------------
    def test_tres_jurisdicciones_no_producen_capa_a_automaticamente(self):
        """El bloqueo real: el código devolvía literalmente CAPA_A_TRANSVERSAL
        con tres países, aunque la documentación dijera lo contrario."""
        claim = {"claim_id": "x", "alcance": "CAPA_A_TRANSVERSAL", "fuentes": [
            {"id": "f1", "registro_oficial_id": "dof-gob-mx"},
            {"id": "f2", "registro_oficial_id": "boe-es"},
            {"id": "f3", "registro_oficial_id": "infoleg-gob-ar"}]}
        r = T.evaluar_cobertura_de_claim(claim, self.reg)
        self.assertEqual(r["sostenible_por_la_evidencia"], T.COBERTURA_COMPARADA_VERIFICADA)
        self.assertNotEqual(r["sostenible_por_la_evidencia"], "CAPA_A_TRANSVERSAL")
        self.assertFalse(r["es_universalidad_panhispanica"])

    def test_ninguna_salida_del_modulo_emite_una_capa_jurisdiccional(self):
        """Ni con cobertura verificada. La capa la declara el packet, no esto."""
        claim = {"claim_id": "x", "alcance": "CAPA_A_TRANSVERSAL", "fuentes": [
            {"id": f"f{i}", "registro_oficial_id": rid} for i, rid in enumerate(
                ["dof-gob-mx", "boe-es", "infoleg-gob-ar", "bcn-cl"])]}
        r = T.evaluar_cobertura_de_claim(claim, self.reg)
        valores = {k: v for k, v in r.items()
                   if not k.startswith("_") and k != "alcance_declarado"}
        self.assertNotIn("CAPA_A_TRANSVERSAL", json.dumps(valores, ensure_ascii=False))

    def test_la_constante_ya_no_promete_capa_a_en_su_nombre(self):
        self.assertFalse(hasattr(T, "MINIMO_JURISDICCIONES_CAPA_A"))
        self.assertEqual(T.MINIMO_JURISDICCIONES_COMPARADAS, 3)

    # --- 5: el documento operativo, sin universalizaciones -----------------
    def test_el_documento_operativo_no_universaliza_instituciones_positivas(self):
        """Patria potestad, prescripción, contrato y hecho ilícito penal son
        instituciones de derecho positivo: su contenido lo fija cada legislador.
        Afirmarlas idénticas en veinte ordenamientos es falsa universalización."""
        doc = (REPO / "docs" / "direccion-basico-antes-que-complejo.md").read_text(
            encoding="utf-8")
        # Las frases solo pueden sobrevivir DENTRO de la corrección que las cita.
        for frase in ("son esencialmente los mismos en",
                      "no cambian sustancialmente entre"):
            with self.subTest(frase=frase):
                for linea in doc.split("\n"):
                    if frase in linea:
                        self.assertTrue(
                            "«" in linea or "»" in linea,
                            f"universalización viva fuera de una cita: {linea!r}")

    def test_el_documento_declara_que_son_instituciones_de_derecho_positivo(self):
        doc = (REPO / "docs" / "direccion-basico-antes-que-complejo.md").read_text(
            encoding="utf-8")
        self.assertIn("instituciones de derecho\n   positivo", doc.replace("**", ""))

    # --- 6: ningún estado técnico abre nada -------------------------------
    def test_ningun_estado_tecnico_abre_aprobacion_arte_ni_publicacion(self):
        for b in B.construir_todos():
            with self.subTest(tema=b["tema_id"]):
                self.assertEqual(b["gate_arte"], "CERRADO")
                self.assertEqual(b["revision_humana"], "PENDIENTE")
                self.assertEqual(b["publicacion"], "NOT_PUBLISHED")
                self.assertFalse(b["ejecutable"])
        r = L.evaluar_diversidad([{"forma_editorial": "MITO", "concepto": "c"}])
        self.assertFalse(r["aprueba_claims"])
        self.assertFalse(r["abre_gate"])
        self.assertFalse(r["autoriza_publicacion"])

    def test_content_type_declara_su_alcance_real(self):
        """No afirma alimentar memoria persistente, porque no lo hace:
        visual/memory.py registra materia y concepto, no content_type."""
        for b in B.construir_todos():
            with self.subTest(tema=b["tema_id"]):
                alcance = b["taxonomia"]["_alcance_de_content_type"]
                self.assertIn("NO alimenta memoria persistente", alcance)


class TestAutoridadDelInventario(unittest.TestCase):
    """El inventario del repositorio no es el inventario de publicaciones.

    CLAUDE.md §2 situa el inventario de publicaciones y la matriz de contenido en
    Google Drive. El loader de este modulo lee `content/`, `claim-packets/` y
    `visual/inventory.py`: las tres son locales. Llamar canonico a eso era
    apropiarse de una autoridad que vive en otro sitio, y producia exactamente la
    afirmacion que hay que evitar — 24 candidatos declarados nuevos sin haber
    mirado nunca lo publicado.
    """

    def test_importar_visual_inventory_no_vuelve_canonico_el_inventario(self):
        """El fallo concreto: bastaba con que el import funcionara."""
        inv, estado, det = L.cargar_inventario()
        self.assertTrue(det["fuentes"]["inventario_produccion"],
                        "esta prueba exige que el import SI funcione")
        self.assertEqual(estado, L.INVENTARIO_REPO_COMPLETO)
        self.assertNotEqual(estado, L.INVENTARIO_CANONICO)

    def test_el_loader_nunca_puede_devolver_el_estado_canonico(self):
        """No es una omision: este modulo no lee Drive."""
        _inv, estado, _det = L.cargar_inventario()
        self.assertNotIn(estado, L.ESTADOS_QUE_PERMITEN_NOVEDAD_GLOBAL)

    def test_el_loader_declara_lo_que_no_consulto(self):
        _inv, _estado, det = L.cargar_inventario()
        self.assertEqual(det["alcance"], "solo este repositorio")
        self.assertIn("Drive", det["no_consultado"])

    def test_ningun_candidato_real_se_declara_nuevo_globalmente(self):
        """La ejecucion real: 0 de 24, no 24 de 24."""
        inv, estado, _ = L.cargar_inventario()
        for tema in TEMAS:
            r = L.evaluar_novedad(tema, inv, estado)
            with self.subTest(tema=tema["id"]):
                self.assertFalse(r["puede_declararse_nuevo_globalmente"])
                self.assertIn("Drive", r["alcance_de_la_comprobacion"])

    def test_no_encontrado_en_el_repositorio_no_dice_no_publicado(self):
        inv, estado, _ = L.cargar_inventario()
        r = L.evaluar_novedad({"id": "X", "concepto": "concepto_inexistente_xyz"},
                              inv, estado)
        self.assertEqual(r["veredicto"], "NO_ENCONTRADO_EN_EL_REPOSITORIO")
        self.assertIn("no se haya publicado ya fuera del repositorio", r["motivo"])

    # --- el trabajo local sigue sirviendo --------------------------------
    def test_una_coincidencia_local_se_sigue_detectando(self):
        base = {"concepto": "posesion", "angulo": "a", "situacion_humana": "s",
                "utilidad": "u", "conexion_juridica": "c"}
        r = L.evaluar_novedad(dict(base, id="X"),
                              [dict(base, origen="content/a.json")],
                              L.INVENTARIO_REPO_COMPLETO)
        self.assertEqual(r["veredicto"], "REPETICION")

    def test_una_ramificacion_local_se_identifica_pero_no_es_novedad_global(self):
        """Sigue siendo util saberlo; lo que no se puede es extrapolarlo."""
        inv = [{"origen": "content/a.json", "concepto": "posesion", "angulo": "a",
                "situacion_humana": "s", "utilidad": "u", "conexion_juridica": "c"}]
        r = L.evaluar_novedad({"id": "X", "concepto": "posesion", "angulo": "otro",
                               "situacion_humana": "s", "utilidad": "u",
                               "conexion_juridica": "c"},
                              inv, L.INVENTARIO_REPO_COMPLETO)
        self.assertEqual(r["veredicto"], "RAMIFICACION")
        self.assertFalse(r["puede_declararse_nuevo_globalmente"])

    # --- la unica via hacia lo global ------------------------------------
    def test_solo_un_inventario_canonico_acreditado_habilita_lo_global(self):
        r = L.evaluar_novedad({"id": "X", "concepto": "libre"}, [],
                              L.INVENTARIO_CANONICO, PROCEDENCIA_OK)
        self.assertTrue(r["puede_declararse_nuevo_globalmente"])
        self.assertEqual(r["degradacion_de_autoridad"], [])

    def test_la_etiqueta_canonica_sin_procedencia_se_degrada(self):
        """Etiquetar no es acreditar: sin origen declarado, no hay autoridad."""
        r = L.evaluar_novedad({"id": "X", "concepto": "libre"}, [],
                              L.INVENTARIO_CANONICO, None)
        self.assertFalse(r["puede_declararse_nuevo_globalmente"])
        self.assertEqual(r["estado_inventario"], L.INVENTARIO_REPO_COMPLETO)
        self.assertTrue(r["degradacion_de_autoridad"])

    def test_una_procedencia_incompleta_tambien_se_degrada(self):
        for falta in L.CAMPOS_DE_AUTORIDAD_CANONICA:
            proc = {c: "x" for c in L.CAMPOS_DE_AUTORIDAD_CANONICA if c != falta}
            with self.subTest(sin=falta):
                r = L.evaluar_novedad({"id": "X", "concepto": "libre"}, [],
                                      L.INVENTARIO_CANONICO, proc)
                self.assertFalse(r["puede_declararse_nuevo_globalmente"])

    def test_ningun_estado_de_inventario_abre_gate_arte_ni_publicacion(self):
        for estado in (L.INVENTARIO_LOCAL, L.INVENTARIO_REPO_COMPLETO,
                       L.INVENTARIO_CANONICO, L.INVENTARIO_INCOMPLETO):
            r = L.evaluar_novedad({"id": "X", "concepto": "c"}, [], estado,
                                  PROCEDENCIA_OK)
            with self.subTest(estado=estado):
                texto = json.dumps(r, ensure_ascii=False).upper()
                for prohibido in ("APROBAD", "GATE_ARTE\": \"ABIERTO",
                                  "PUBLICADA", "AUTORIZAD"):
                    self.assertNotIn(prohibido, texto)


if __name__ == "__main__":
    unittest.main()
