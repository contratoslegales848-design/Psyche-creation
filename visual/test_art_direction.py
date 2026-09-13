"""Pruebas del detalle artistico: auditoria, tipografia aprobada y medidas reales.

Sin red, sin credenciales, sin creditos. Lo que se prueba aqui es exactamente lo
que antes no fallaba nunca y arruinaba la pieza igual: recursos quemados en la
propia escena, dos escuelas en un prompt, cuerpo de texto por debajo del escalon
aprobado, texto sobre la marca, texto sin contraste real contra su fondo.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import art_direction  # noqa: E402
import composition  # noqa: E402
import compositor  # noqa: E402
import inspection  # noqa: E402
import pipeline  # noqa: E402
import rotation  # noqa: E402
from brief import VisualPolicy  # noqa: E402
from compiler import compile_request  # noqa: E402
from families import VisualFamilyRegistry  # noqa: E402
from memory import VisualMemory, VisualMemoryEntry  # noqa: E402
from providers import FakeImageProvider  # noqa: E402
from providers.fake import png_bytes  # noqa: E402
from test_visual_pipeline import HANDOFF, PROC, make_brief  # noqa: E402

POLICY = VisualPolicy.load()
FAMS = VisualFamilyRegistry.load()
FRASE = "El derecho no favorece a quien duerme sobre sus derechos"
AUTOR = "Maxima del Derecho Romano"
BRAND = composition.build_brand_plan(POLICY, "sello de lacre").to_dict()


def auditar(**kw):
    return art_direction.auditar_brief(make_brief(**kw), POLICY,
                                       family=FAMS.get(kw.get("visual_family",
                                                               "claroscuro_de_museo")))


def codigos(rep):
    return {h.codigo for h in rep.hallazgos}


class TestPoliticaTranscribeLaSkill(unittest.TestCase):
    """La politica es la unica fuente ejecutable; si pierde un parametro, el
    codigo deja de comprobar arte sin que nadie se entere."""

    def test_declara_los_parametros_tipograficos(self):
        tip = POLICY.data["tipografia"]
        for clave in ("zona_segura_declarada", "escalones_principal", "max_lineas",
                      "contraste_minimo", "colores_por_rol"):
            self.assertIn(clave, tip)
        self.assertEqual(tip["max_lineas"], 6)
        self.assertEqual(tip["contraste_minimo"], 4.5)

    def test_banco_de_escuelas_sin_solapes(self):
        a = {art_direction.normaliza(x) for x in POLICY.data["escuelas"]["carril_a"]}
        b = {art_direction.normaliza(x) for x in POLICY.data["escuelas"]["carril_b"]}
        self.assertTrue(a and b)
        self.assertFalse(a & b, "una escuela no puede estar en los dos carriles")

    def test_toda_familia_de_la_politica_existe_en_el_registro(self):
        for nombre in POLICY.familias:
            self.assertIn(nombre, FAMS.names())

    def test_colores_de_rol_salen_de_la_paleta(self):
        requerida = POLICY.data["paleta"]["requerida"]
        for rol in ("QUOTE", "AUTHOR"):
            color = composition.color_de_rol(rol, POLICY)
            self.assertTrue(any(color in tonos for tonos in requerida.values()),
                            f"{rol} usa un color fuera de la paleta institucional")


class TestRecursosQuemados(unittest.TestCase):
    def test_balanza_en_la_escena_bloquea(self):
        rep = auditar(subject="una balanza de bronce sobre una mesa")
        self.assertIn("RECURSO_QUEMADO_EN_LA_ESCENA", codigos(rep))
        self.assertFalse(rep.sin_bloqueos)

    def test_el_negativo_no_salva_una_escena_que_pide_el_recurso(self):
        """El prompt negativo prohibe la balanza mientras el positivo la pide:
        el generador obedece al positivo. Por eso se bloquea antes."""
        b = make_brief(subject="una balanza de bronce sobre una mesa")
        req = compile_request(b, POLICY, family=FAMS.get(b.visual_family))
        self.assertIn("balanza de la justicia", req.negative_constraints)
        self.assertIn("balanza", req.positive_prompt)
        self.assertTrue(art_direction.auditar_brief(b, POLICY).bloqueos)

    def test_recurso_dudoso_escala_a_revision_no_a_bloqueo(self):
        rep = auditar(subject="un pergamino sobre la mesa")
        self.assertIn("RECURSO_GASTADO_DUDOSO", codigos(rep))
        self.assertTrue(rep.sin_bloqueos)

    def test_escena_limpia_no_inventa_hallazgos(self):
        rep = auditar(subject="una llave de hierro sobre un umbral de piedra",
                      escuela="claroscuro rembrandtiano",
                      mecanismo_revelacion="la luz rasante revela la talla del umbral",
                      environment="umbral de una casa al amanecer")
        self.assertNotIn("RECURSO_QUEMADO_EN_LA_ESCENA", codigos(rep))
        self.assertNotIn("ENTORNO_JURIDICO_GASTADO", codigos(rep))
        self.assertTrue(rep.sin_bloqueos)


class TestUnaEscuelaPorPieza(unittest.TestCase):
    def test_dos_escuelas_invalidan_el_brief(self):
        b = make_brief(escuela="tenebrismo caravaggista, atmosfera disuelta de turner")
        errores = b.validate(POLICY)
        self.assertTrue(any("UNA escuela" in e for e in errores))

    def test_escuela_fuera_del_banco(self):
        b = make_brief(escuela="realismo magico de sobremesa")
        self.assertTrue(any("fuera del banco" in e for e in b.validate(POLICY)))

    def test_sin_escuela_no_se_supone_cumplido(self):
        rep = auditar()
        self.assertIn("ESCUELA_NO_DECLARADA", codigos(rep))
        self.assertIn("rotacion de escuela", rep.no_comprobable)

    def test_escuela_repetida_dentro_de_la_ventana(self):
        recientes = [VisualMemoryEntry("c1", "g1", escuela="Claroscuro Rembrandtiano")]
        rep = art_direction.auditar_brief(
            make_brief(escuela="claroscuro rembrandtiano"), POLICY,
            memoria_reciente=recientes)
        self.assertIn("ESCUELA_REPETIDA_EN_VENTANA", codigos(rep))

    def test_fuera_de_la_ventana_ya_no_penaliza(self):
        recientes = [VisualMemoryEntry("c", f"g{i}", escuela="otra escuela") for i in range(5)]
        recientes.append(VisualMemoryEntry("c", "g9", escuela="claroscuro rembrandtiano"))
        rep = art_direction.auditar_brief(
            make_brief(escuela="claroscuro rembrandtiano"), POLICY,
            memoria_reciente=recientes)
        self.assertNotIn("ESCUELA_REPETIDA_EN_VENTANA", codigos(rep))

    def test_carriles_mezclados(self):
        # "documental de calle" es carril B; oleo_narrativo es familia de carril A.
        rep = art_direction.auditar_brief(
            make_brief(visual_family="oleo_narrativo", escuela="documental de calle"),
            POLICY, family=FAMS.get("oleo_narrativo"))
        self.assertIn("CARRILES_MEZCLADOS", codigos(rep))

    def test_la_escuela_entra_en_el_prompt_una_sola_vez(self):
        b = make_brief(escuela="vitral gotico")
        req = compile_request(b, POLICY, family=FAMS.get(b.visual_family))
        self.assertEqual(req.positive_prompt.lower().count("vitral gotico"), 1)
        self.assertIn("sin mezclar referentes", req.positive_prompt)


class TestDireccionDeArteRestante(unittest.TestCase):
    def test_mecanismo_de_revelacion_ausente(self):
        self.assertIn("SIN_MECANISMO_DE_REVELACION", codigos(auditar()))

    def test_mecanismo_declarado_llega_al_prompt(self):
        b = make_brief(mecanismo_revelacion="la tinta que se seca y cambia de tono")
        req = compile_request(b, POLICY, family=FAMS.get(b.visual_family))
        self.assertIn("Mecanismo de revelacion: la tinta que se seca", req.positive_prompt)

    def test_entorno_juridico_gastado_es_aviso(self):
        rep = auditar(environment="despacho en penumbra al amanecer")
        self.assertIn("ENTORNO_JURIDICO_GASTADO", codigos(rep))
        self.assertTrue(rep.sin_bloqueos)

    def test_presencia_humana_sin_justificar_bloquea(self):
        rep = auditar(subject="un rostro completo iluminado de lado")
        self.assertIn("PRESENCIA_HUMANA_SIN_JUSTIFICAR", codigos(rep))

    def test_presencia_humana_justificada_no_bloquea(self):
        rep = auditar(subject="un rostro completo iluminado de lado",
                      justificacion_presencia_humana="retrato de autor historico aprobado")
        self.assertNotIn("PRESENCIA_HUMANA_SIN_JUSTIFICAR", codigos(rep))

    def test_superficie_de_marca_repetida(self):
        recientes = [VisualMemoryEntry("c", "g", brand_surface="sello de lacre")]
        rep = art_direction.auditar_brief(make_brief(), POLICY, memoria_reciente=recientes)
        self.assertIn("SUPERFICIE_DE_MARCA_REPETIDA", codigos(rep))

    def test_el_detalle_de_la_familia_llega_al_prompt(self):
        f = FAMS.get("claroscuro_de_museo")
        req = compile_request(make_brief(), POLICY, family=f)
        self.assertIn(f.depth_of_field, req.positive_prompt)
        self.assertIn(f.surface_finish, req.positive_prompt)
        self.assertIn(f.imperfection_signature[0], req.positive_prompt)


class TestTipografiaAprobada(unittest.TestCase):
    def test_zona_segura_real_del_feed(self):
        p = composition.build_typography_plan(FRASE, AUTOR, 1080, 1920, "maxima")
        self.assertEqual(p.safe_area, (80, 290, 920, 1340))
        self.assertEqual(p.safe_area_origen, "politica")

    def test_formato_sin_medida_lo_declara(self):
        p = composition.build_typography_plan(FRASE, AUTOR, 1080, 1350, "maxima")
        self.assertEqual(p.safe_area_origen, "ratio_por_defecto")
        self.assertIn("ZONA_SEGURA_NO_MEDIDA",
                      codigos(art_direction.auditar_tipografia(p, POLICY)))

    def test_cuerpo_respeta_el_escalon_aprobado(self):
        corta = composition.build_typography_plan("Nadie da lo que no tiene", "", 1080, 1920)
        self.assertGreaterEqual(corta.blocks[0].size_px, 68)
        self.assertLessEqual(corta.blocks[0].size_px, 96)
        media = composition.build_typography_plan("palabra " * 15, "", 1080, 1920)
        self.assertGreaterEqual(media.blocks[0].size_px, 60)

    def test_el_cuerpo_principal_nunca_cae_a_tamaño_de_pie_de_foto(self):
        largo = composition.build_typography_plan("palabra " * 80, "", 1080, 1920)
        self.assertGreaterEqual(largo.blocks[0].size_px, 60)
        self.assertIn("COPIA_FUERA_DE_TABLA",
                      codigos(art_direction.auditar_tipografia(largo, POLICY)))

    def test_maximo_de_lineas_se_señala(self):
        p = composition.build_typography_plan("palabra " * 80, "", 1080, 1920)
        self.assertIn("EXCEDE_MAXIMO_DE_LINEAS", codigos(art_direction.auditar_tipografia(p, POLICY)))

    def test_sin_huerfana_cuando_hay_reparto_posible(self):
        p = composition.build_typography_plan(FRASE, AUTOR, 1080, 1920, "maxima")
        self.assertFalse(composition.es_huerfana(p.blocks[0].lines))

    def test_el_reparto_jamas_toca_el_texto(self):
        p = composition.build_typography_plan(FRASE, AUTOR, 1080, 1920, "maxima")
        self.assertEqual(p.rendered_text(), FRASE)
        composition.assert_exact_copy_preserved(FRASE, p)

    def test_area_de_texto_dentro_de_la_banda_visible(self):
        p = composition.build_typography_plan(FRASE, AUTOR, 1080, 1920, "maxima")
        vis = composition.zona_visible_tras_recorte(1080, 1920, POLICY)
        sx, sy, sw, sh = p.safe_area
        self.assertGreaterEqual(sy, vis[1])
        self.assertLessEqual(sy + sh, vis[3])

    def test_cada_bloque_lleva_color_de_paleta_y_piso_propio(self):
        p = composition.build_typography_plan(FRASE, AUTOR, 1080, 1920, "maxima")
        quote, autor = p.blocks[0], p.blocks[1]
        self.assertEqual(quote.color_hex, "#FCFAF2")
        self.assertEqual(autor.color_hex, "#C5A059")
        self.assertGreater(quote.min_size_px, autor.min_size_px)


class TestContrasteYMarcaEnElCompositor(unittest.TestCase):
    def plan(self, texto=FRASE):
        return composition.build_typography_plan(texto, AUTOR, 1080, 1920, "maxima")

    def test_texto_claro_sobre_fondo_claro_pide_revision(self):
        claro = png_bytes(1080, 1920, (245, 243, 236))
        r = compositor.compose(claro, self.plan(), BRAND,
                               compositor.ReservedSurface(120, 1700, 500, 90))
        self.assertIn("TEXT_CONTRAST_BELOW_MINIMUM", r.reason_codes)
        self.assertTrue(any("caja opaca" in w for w in r.warnings))

    def test_texto_claro_sobre_fondo_oscuro_pasa(self):
        r = compositor.compose(png_bytes(1080, 1920, (30, 20, 18)), self.plan(), BRAND,
                               compositor.ReservedSurface(120, 1600, 500, 70))
        self.assertNotIn("TEXT_CONTRAST_BELOW_MINIMUM", r.reason_codes)
        self.assertGreater(r.text_contrast["QUOTE"]["min"], 4.5)

    def test_texto_sobre_la_superficie_de_marca_se_declara(self):
        """La marca es un objeto de la escena: escribir encima la destruye."""
        dentro = compositor.ReservedSurface(100, 400, 500, 90)
        r = compositor.compose(png_bytes(1080, 1920, (30, 20, 18)), self.plan(), BRAND, dentro)
        self.assertIn("TEXT_OVER_BRAND_SURFACE", r.reason_codes)
        self.assertEqual(
            art_direction.auditar_composicion(r, POLICY).bloqueos[0].codigo,
            "TEXT_OVER_BRAND_SURFACE")

    def test_marca_sin_contraste_sobre_su_superficie(self):
        laton = png_bytes(1080, 1920, (197, 160, 89))
        r = compositor.compose(laton, self.plan(), BRAND,
                               compositor.ReservedSurface(120, 1600, 500, 70))
        self.assertIn("BRAND_CONTRAST_BELOW_MINIMUM", r.reason_codes)
        self.assertEqual(r.state, compositor.NEEDS_HUMAN_REVIEW)

    def test_marca_fuera_de_la_banda_visible(self):
        r = compositor.compose(png_bytes(1080, 1920, (30, 20, 18)), self.plan(), BRAND,
                               compositor.ReservedSurface(120, 1700, 500, 90))
        self.assertIn("BRAND_SURFACE_OUTSIDE_VISIBLE_AREA", r.reason_codes)

    def test_la_marca_se_graba_no_se_pega(self):
        plano = dict(BRAND, engraved=False)
        raw = png_bytes(1080, 1920, (30, 20, 18))
        s = compositor.ReservedSurface(120, 1600, 500, 70)
        grabado = compositor.compose(raw, self.plan(), BRAND, s)
        pegado = compositor.compose(raw, self.plan(), plano, s)
        self.assertNotEqual(grabado.composed_sha256, pegado.composed_sha256)
        self.assertTrue(grabado.brand_applied and pegado.brand_applied)

    def test_el_grabado_sigue_siendo_determinista(self):
        raw, s = png_bytes(1080, 1920, (30, 20, 18)), compositor.ReservedSurface(120, 1600, 500, 70)
        a = compositor.compose(raw, self.plan(), BRAND, s)
        b = compositor.compose(raw, self.plan(), BRAND, s)
        self.assertEqual(a.composed_sha256, b.composed_sha256)

    def test_contraste_wcag_conocido(self):
        """Blanco sobre negro es 21:1. Si esta cuenta cambia, todo lo demas miente."""
        self.assertAlmostEqual(compositor.ratio_contraste((255, 255, 255), (0, 0, 0)), 21.0, places=1)
        self.assertAlmostEqual(compositor.ratio_contraste((10, 10, 10), (10, 10, 10)), 1.0, places=3)


def png_con_franja_cargada(alto_franja=(290, 900), paso=6):
    """PNG oscuro con una franja de rayas finas: mucha estructura, como un
    rostro o un encaje, en el sitio donde el compositor pondra el texto."""
    import io

    from PIL import Image, ImageDraw
    img = Image.new("RGB", (1080, 1920), (30, 20, 18))
    d = ImageDraw.Draw(img)
    for y in range(alto_franja[0], alto_franja[1], paso):
        d.line([(0, y), (1080, y)], fill=(150, 140, 130), width=2)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


class TestDetalleBajoElTexto(unittest.TestCase):
    """La skill prohibe texto sobre rostros y manos decisivas. Reconocer un
    rostro es imposible aqui; medir si el texto cae sobre la zona mas cargada
    de la escena, no."""

    def plan(self, anchor="SUPERIOR"):
        """Anclaje fijado a proposito: aqui se prueba LA MEDIDA. Que el anclaje
        automatico huya de la zona cargada se prueba aparte, en
        TestComposicionEditorial."""
        p = composition.build_typography_plan(FRASE, AUTOR, 1080, 1920, "maxima")
        p.anchor = anchor
        return p

    def test_el_plan_transporta_el_umbral_de_la_politica(self):
        self.assertEqual(composition.build_typography_plan(
            FRASE, AUTOR, 1080, 1920, "maxima").detalle_maximo_relativo,
                         POLICY.data["tipografia"]["detalle_maximo_relativo_bajo_texto"])

    def test_superficie_plana_no_tiene_energia_de_borde(self):
        from PIL import Image
        plana = Image.new("RGB", (400, 400), (30, 20, 18))
        self.assertAlmostEqual(compositor.energia_de_borde(plana), 0.0, places=3)

    def test_la_zona_cargada_mide_mas_que_la_calmada(self):
        import io

        from PIL import Image
        img = Image.open(io.BytesIO(png_con_franja_cargada())).convert("RGB")
        cargada = compositor.detalle_relativo(img, (80, 300, 1000, 880))
        calmada = compositor.detalle_relativo(img, (80, 1000, 1000, 1600))
        self.assertGreater(cargada, 1.35)
        self.assertLess(calmada, 1.0)

    def test_texto_sobre_zona_cargada_pide_revision(self):
        r = compositor.compose(png_con_franja_cargada(), self.plan(), BRAND,
                               compositor.ReservedSurface(120, 1450, 500, 90))
        self.assertIn("TEXT_OVER_BUSY_AREA", r.reason_codes)
        self.assertTrue(any("mas cargada de la escena" in w for w in r.warnings))
        self.assertGreater(r.text_busyness["QUOTE"], 1.35)

    def test_texto_sobre_fondo_limpio_no_avisa(self):
        """La carga esta abajo; el texto cae en la zona despejada de arriba."""
        raw = png_con_franja_cargada(alto_franja=(1100, 1600))
        r = compositor.compose(raw, self.plan(), BRAND,
                               compositor.ReservedSurface(120, 1000, 500, 90))
        self.assertNotIn("TEXT_OVER_BUSY_AREA", r.reason_codes)
        self.assertLess(r.text_busyness["QUOTE"], 1.0)

    def test_la_medida_es_del_fondo_no_del_texto_ya_pintado(self):
        """Si se midiera despues de dibujar, el propio texto dispararia el aviso
        en cualquier pieza y la medida no valdria nada."""
        raw = png_con_franja_cargada(alto_franja=(1100, 1600))
        r = compositor.compose(raw, self.plan(), BRAND,
                               compositor.ReservedSurface(120, 1000, 500, 90))
        self.assertLess(r.text_busyness["QUOTE"], 0.5)

    def test_imagen_sin_detalle_no_produce_proporcion_inventada(self):
        """Sobre un color solido no hay detalle medio con que comparar: la
        medida no existe y no se finge una."""
        r = compositor.compose(png_bytes(1080, 1920, (30, 20, 18)), self.plan(), BRAND,
                               compositor.ReservedSurface(120, 1450, 500, 90))
        self.assertEqual(r.text_busyness, {})
        self.assertNotIn("TEXT_OVER_BUSY_AREA", r.reason_codes)

    def test_se_traduce_a_hallazgo_de_direccion_de_arte(self):
        r = compositor.compose(png_con_franja_cargada(), self.plan("SUPERIOR"), BRAND,
                               compositor.ReservedSurface(120, 1450, 500, 90))
        rep = art_direction.auditar_composicion(r, POLICY)
        self.assertIn("TEXT_OVER_BUSY_AREA", codigos(rep))
        self.assertTrue(rep.sin_bloqueos)      # escala a humano, nunca rechaza


class TestComposicionEditorial(unittest.TestCase):
    """Politica 1.3: comillas colgantes, filete, versalitas y anclaje medido.

    La regla que gobierna todo esto: un adorno que desplaza el texto no es un
    adorno. La primera version de este sistema sangraba la columna para hacer
    sitio a la comilla, el texto ganaba una linea y el autor terminaba sobre el
    rostro de la escena con 1,34:1 de contraste. Se midio y se corrigio.
    """

    def sin_ornamentos(self):
        import copy
        pol = VisualPolicy(version=POLICY.version, data=copy.deepcopy(POLICY.data))
        pol.data["tipografia"]["ornamentos"] = {}
        return pol

    def plan(self, policy=None, texto=FRASE, autor=AUTOR, ct="maxima"):
        return composition.build_typography_plan(texto, autor, 1080, 1920, ct,
                                                 policy=policy or POLICY)

    def test_los_ornamentos_no_mueven_el_texto(self):
        con, sin = self.plan(), self.plan(self.sin_ornamentos())
        self.assertEqual(con.blocks[0].lines, sin.blocks[0].lines)
        self.assertEqual(con.blocks[0].size_px, sin.blocks[0].size_px)
        self.assertEqual(con.safe_area, sin.safe_area)
        self.assertEqual(con.blocks[0].indent_px, 0)

    def test_los_ornamentos_no_cambian_ni_una_medida_de_la_pieza(self):
        """Mismo fondo, mismas cajas: el contraste y la carga medidos deben ser
        identicos con y sin adornos. Si cambian, algo se movio."""
        raw = png_con_franja_cargada(alto_franja=(1200, 1500))
        s = compositor.ReservedSurface(120, 1000, 400, 80)
        con = compositor.compose(raw, self.plan(), BRAND, s)
        sin = compositor.compose(raw, self.plan(self.sin_ornamentos()), BRAND, s)
        self.assertEqual(con.text_contrast, sin.text_contrast)
        self.assertEqual(con.text_busyness, sin.text_busyness)
        self.assertNotEqual(con.composed_sha256, sin.composed_sha256)   # pero se ven distintas

    def test_comillas_solo_en_citas(self):
        self.assertEqual(self.plan().quotes, ("«", "»"))
        self.assertEqual(self.plan(ct="concepto").quotes, ())
        self.assertEqual(self.plan(ct="mito").quotes, ())

    def test_las_comillas_no_son_texto(self):
        """Son ornamento dibujado aparte: el texto exacto no las lleva dentro."""
        p = self.plan()
        self.assertEqual(p.rendered_text(), FRASE)
        self.assertNotIn("«", p.blocks[0].text)
        composition.assert_exact_copy_preserved(FRASE, p)

    def test_autor_en_versalitas_con_tracking(self):
        autor = self.plan().blocks[1]
        self.assertTrue(autor.versalitas)
        self.assertGreater(autor.tracking_em, 0)
        # El texto del bloque NO se altera: las mayusculas son de dibujo.
        self.assertEqual(autor.text, AUTOR)

    def test_el_filete_se_dibuja_en_laton(self):
        from PIL import Image
        import io
        r = compositor.compose(png_bytes(1080, 1920, (20, 14, 12)), self.plan(), BRAND,
                               compositor.ReservedSurface(620, 1500, 380, 90))
        img = Image.open(io.BytesIO(r.composed_bytes)).convert("RGB")
        laton = sum(1 for x in range(80, 80 + self.plan().rule_width)
                    for y in range(290, 1630)
                    if img.getpixel((x, y))[0] > 120 and img.getpixel((x, y))[2] < 130)
        self.assertGreater(laton, 100, "no se encontro el filete de laton")

    def test_anclaje_elige_la_posicion_menos_cargada(self):
        """Carga arriba, calma abajo: el texto baja. Antes caia siempre arriba."""
        raw = png_con_franja_cargada(alto_franja=(290, 1000))
        r = compositor.compose(raw, self.plan(), BRAND,
                               compositor.ReservedSurface(620, 200, 380, 80))
        self.assertEqual(r.anchor, "INFERIOR")
        self.assertLess(r.anchor_metrics["evaluacion"]["INFERIOR"]["peor_detalle"],
                        r.anchor_metrics["evaluacion"]["SUPERIOR"]["peor_detalle"])

    def test_empate_conserva_la_lectura_natural(self):
        r = compositor.compose(png_bytes(1080, 1920, (30, 20, 18)), self.plan(), BRAND,
                               compositor.ReservedSurface(620, 1500, 380, 90))
        self.assertEqual(r.anchor, "SUPERIOR")

    def test_el_anclaje_se_decide_por_el_peor_bloque(self):
        """Promediar la banda entera dejaba el autor sobre un rostro con la banda
        'limpia' de media. Se evalua bloque a bloque."""
        raw = png_con_franja_cargada(alto_franja=(290, 1000))
        r = compositor.compose(raw, self.plan(), BRAND,
                               compositor.ReservedSurface(620, 200, 380, 80))
        for posicion in ("SUPERIOR", "INFERIOR"):
            self.assertIn("peor_detalle", r.anchor_metrics["evaluacion"][posicion])
            self.assertIn("peor_contraste", r.anchor_metrics["evaluacion"][posicion])


class TestInspectorDeDetalle(unittest.TestCase):
    def setUp(self):
        self.insp = inspection.ArtDetailInspector(POLICY)

    def test_negros_empastados_se_detectan(self):
        rep = self.insp.inspect(png_bytes(64, 64, (0, 0, 0)))
        self.assertIn("BLACK_CLIPPING_RISK", rep.reason_codes)
        self.assertEqual(rep.metrics["clipped_black_ratio"], 1.0)

    def test_acento_frio_ausente(self):
        rep = self.insp.inspect(png_bytes(64, 64, (180, 140, 90)))
        self.assertIn("COLD_ACCENT_ABSENT", rep.reason_codes)

    def test_acento_frio_presente(self):
        rep = self.insp.inspect(png_bytes(64, 64, (15, 37, 55)))
        self.assertNotIn("COLD_ACCENT_ABSENT", rep.reason_codes)

    def test_nunca_rechaza_por_si_solo(self):
        for color in ((0, 0, 0), (255, 255, 255), (180, 140, 90), (15, 37, 55)):
            rep = self.insp.inspect(png_bytes(32, 32, color))
            self.assertIn(rep.state, (inspection.PASS, inspection.NEEDS_HUMAN_REVIEW))
            self.assertNotEqual(rep.state, inspection.FAIL)

    def test_asset_ilegible_no_se_inventa_medida(self):
        rep = self.insp.inspect(b"no-soy-una-imagen")
        self.assertEqual(rep.state, inspection.NOT_EVALUATED)
        self.assertEqual(rep.metrics, {})


class TestPipelineConAuditoria(unittest.TestCase):
    def test_recurso_quemado_no_gasta_una_sola_llamada(self):
        prov = FakeImageProvider()
        run = pipeline.generate_visual(
            PROC, make_brief(subject="una balanza dorada sobre marmol"), POLICY, prov,
            handoff=HANDOFF, family=FAMS.get("claroscuro_de_museo"))
        self.assertEqual(run.receipt.status, "ARTE_BLOQUEADO")
        self.assertEqual(prov.llamadas, 0)
        self.assertEqual(run.item_state, pipeline.BLOCKED)
        self.assertTrue(any("RECURSO_QUEMADO" in m for m in run.receipt.motivos))

    def test_la_auditoria_viaja_en_el_receipt(self):
        run = pipeline.generate_visual(PROC, make_brief(), POLICY, FakeImageProvider(),
                                       handoff=HANDOFF, dry_run=True)
        arte = run.receipt.art_direction
        self.assertIn("hallazgos", arte)
        self.assertIn("sin_bloqueos", arte)
        self.assertIn("aprobacion visual es humana", arte["nota"])

    def test_una_auditoria_sin_bloqueos_no_aprueba_nada(self):
        run = pipeline.generate_visual(
            PROC, make_brief(escuela="vitral gotico",
                             mecanismo_revelacion="la luz que cruza una grieta"),
            POLICY, FakeImageProvider(), handoff=HANDOFF,
            family=FAMS.get("claroscuro_de_museo"),
            exact_copy=FRASE, author=AUTOR, content_type="maxima",
            reserved_surface=compositor.ReservedSurface(120, 1600, 500, 70))
        self.assertEqual(run.receipt.status, "PENDIENTE_REVISION_HUMANA")
        self.assertTrue(run.receipt.art_direction["sin_bloqueos"])
        self.assertEqual(run.receipt.human_visual_approval, "PENDIENTE")

    def test_la_escuela_queda_en_la_memoria_visual(self):
        entry = pipeline._entry_desde_brief(
            "LM-TEST-001", make_brief(escuela="xilografia de gubia"), "gen-1")
        self.assertEqual(entry.escuela, "xilografia de gubia")
        m = VisualMemory()
        m.record(entry)
        self.assertTrue(rotation.verificar_rotacion_de_escuela(
            "Xilografia de Gubia", m.recent()).repetida)


class TestMemoriaCompatible(unittest.TestCase):
    def test_memoria_1_0_se_sigue_leyendo(self):
        import json
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "mem.json"
            p.write_text(json.dumps({
                "schema_version": "1.0", "ventana": 12,
                "entries": [{"content_id": "c", "generation_id": "g",
                             "visual_family": "oleo_narrativo"}]}), encoding="utf-8")
            m = VisualMemory.load(p)
            self.assertEqual(len(m), 1)
            self.assertEqual(m.recent()[0].escuela, "")


if __name__ == "__main__":
    unittest.main()
