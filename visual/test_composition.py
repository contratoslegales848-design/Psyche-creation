"""Pruebas del compositor determinista.

Invariantes, no snapshots fragiles: la rasterizacion cambia entre plataformas y
versiones de fuente, pero las dimensiones, el area segura, la inmutabilidad del
raw y la del texto exacto no.
"""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import composition  # noqa: E402
import inspection  # noqa: E402
import compositor  # noqa: E402
import pipeline  # noqa: E402
import registry as registry_mod  # noqa: E402
from brief import VisualPolicy  # noqa: E402
from providers import FakeImageProvider  # noqa: E402
from providers.fake import png_bytes  # noqa: E402
from test_visual_pipeline import HANDOFF, PROC, make_brief  # noqa: E402

POLICY = VisualPolicy.load()
FRASE = "El derecho no favorece a quien duerme sobre sus derechos"
AUTOR = "Maxima del Derecho Romano"
BRAND = {"required": True, "text": "LegalMente", "generator_writes_text": False}


def raw(w=1080, h=1920):
    return png_bytes(w, h, (30, 20, 18))


def plan(texto=FRASE, autor=AUTOR, ct="maxima", w=1080, h=1920):
    return composition.build_typography_plan(texto, autor, w, h, ct)


def surface():
    return compositor.ReservedSurface(120, 1650, 500, 90)


class TestCompositorBasico(unittest.TestCase):
    def test_produce_asset_compuesto_real(self):
        r = compositor.compose(raw(), plan(), BRAND, surface())
        self.assertEqual(r.state, compositor.COMPOSED)
        self.assertTrue(r.composed_bytes.startswith(b"\x89PNG"))
        self.assertGreater(len(r.composed_bytes), 1000)

    def test_raw_no_se_modifica(self):
        original = raw()
        copia = bytes(original)
        r = compositor.compose(original, plan(), BRAND, surface())
        self.assertEqual(original, copia)
        self.assertEqual(r.raw_sha256, compositor._sha(copia))

    def test_hash_compuesto_difiere_del_bruto(self):
        r = compositor.compose(raw(), plan(), BRAND, surface())
        self.assertNotEqual(r.composed_sha256, r.raw_sha256)

    def test_dimensiones_preservadas(self):
        r = compositor.compose(raw(), plan(), BRAND, surface())
        self.assertEqual((r.width, r.height), (1080, 1920))

    def test_formato_4_5(self):
        p = plan(w=1080, h=1350)
        r = compositor.compose(raw(1080, 1350), p, BRAND,
                               compositor.ReservedSurface(120, 1150, 500, 80))
        self.assertEqual((r.width, r.height), (1080, 1350))

    def test_determinista(self):
        a = compositor.compose(raw(), plan(), BRAND, surface())
        b = compositor.compose(raw(), plan(), BRAND, surface())
        self.assertEqual(a.composed_sha256, b.composed_sha256)

    def test_lineage_registrado(self):
        r = compositor.compose(raw(), plan(), BRAND, surface())
        for campo in (r.typography_plan_hash, r.brand_plan_hash,
                      r.composition_plan_hash, r.compositor_version):
            self.assertTrue(campo)

    def test_fuentes_registradas(self):
        r = compositor.compose(raw(), plan(), BRAND, surface())
        self.assertIn("QUOTE", r.fonts_used)
        self.assertIn("BRAND", r.fonts_used)


class TestLayouts(unittest.TestCase):
    def test_renderiza_todos_los_layouts(self):
        casos = {
            "SHORT_QUOTE": ("Nadie da lo que no tiene", "aforismo"),
            "LONG_QUOTE": (FRASE + ", y por eso la prescripcion extingue la accion "
                           "aunque el derecho parezca intacto", "maxima"),
            "LEGAL_CONCEPT": ("Comodato: prestamo de uso, se devuelve la misma cosa", "concepto"),
            "COMPARISON": ("Comodato devuelve la cosa; mutuo devuelve otro tanto", "diferencia"),
            "MYTH": ("Es falso que un contrato verbal no valga nunca", "mito"),
        }
        for esperado, (texto, ct) in casos.items():
            p = plan(texto, AUTOR, ct)
            self.assertEqual(p.layout_type, esperado, texto[:30])
            r = compositor.compose(raw(), p, BRAND, surface())
            self.assertEqual(r.state, compositor.COMPOSED, esperado)

    def test_nunca_fuente_cero_ni_negativa(self):
        for texto in ("corto", FRASE, "palabra " * 60):
            p = plan(texto, AUTOR, "maxima")
            self.assertTrue(all(b.size_px > 0 for b in p.blocks))
            self.assertGreaterEqual(min(b.size_px for b in p.blocks),
                                    composition.MIN_READABLE_PX)

    def test_area_segura_dentro_del_lienzo(self):
        r = compositor.compose(raw(), plan(), BRAND, surface())
        p = plan()
        sx, sy, sw, sh = p.safe_area
        self.assertGreaterEqual(sx, 0)
        self.assertLessEqual(sx + sw, r.width)
        self.assertLessEqual(sy + sh, r.height)


class TestExactCopyInmutable(unittest.TestCase):
    def test_desbordamiento_no_muta_el_texto(self):
        largo = "palabra " * 400
        p = plan(largo.strip(), AUTOR, "explicador")
        # El plan ya transporta el texto intacto...
        self.assertEqual(p.rendered_text(), " ".join(largo.split()))
        # ...y el compositor prefiere desbordar antes que tocarlo.
        with self.assertRaises(compositor.CompositionOverflow):
            compositor.compose(raw(), p, BRAND, surface())

    def test_mensaje_de_desbordamiento_es_explicito(self):
        p = plan("palabra " * 400, AUTOR, "explicador")
        try:
            compositor.compose(raw(), p, BRAND, surface())
            self.fail("debio desbordar")
        except compositor.CompositionOverflow as exc:
            self.assertIn("COMPOSITION_OVERFLOW", str(exc))
            self.assertIn("NO se acorta", str(exc))

    def test_qa_detecta_plan_que_no_lleva_el_texto_esperado(self):
        p = plan()
        r = compositor.compose(raw(), p, BRAND, surface())
        self.assertEqual(compositor.composition_qa(r, raw(), p, FRASE), [])
        self.assertTrue(compositor.composition_qa(r, raw(), p, "otro texto distinto"))

    def test_autor_no_se_pierde(self):
        p = plan()
        roles = [b.role for b in p.blocks]
        self.assertIn("AUTHOR", roles)


class TestMarcaCompositor(unittest.TestCase):
    def test_marca_aplicada_en_superficie_plana(self):
        r = compositor.compose(raw(), plan(), BRAND, surface())
        self.assertTrue(r.brand_applied)
        self.assertEqual(r.state, compositor.COMPOSED)

    def test_sin_superficie_declarada_pide_revision(self):
        r = compositor.compose(raw(), plan(), BRAND, reserved_surface=None)
        self.assertEqual(r.state, compositor.NEEDS_HUMAN_REVIEW)
        self.assertFalse(r.brand_applied)
        self.assertIn("BRAND_SURFACE_NOT_DECLARED", r.reason_codes)

    def test_superficie_no_plana_pide_revision(self):
        s = compositor.ReservedSurface(120, 1650, 500, 90, flat=False)
        r = compositor.compose(raw(), plan(), BRAND, s)
        self.assertEqual(r.state, compositor.NEEDS_HUMAN_REVIEW)
        self.assertIn("BRAND_SURFACE_NOT_FLAT", r.reason_codes)

    def test_superficie_muy_rotada_pide_revision(self):
        s = compositor.ReservedSurface(120, 1650, 500, 90, rotation_deg=25)
        r = compositor.compose(raw(), plan(), BRAND, s)
        self.assertEqual(r.state, compositor.NEEDS_HUMAN_REVIEW)

    def test_nunca_degrada_a_watermark(self):
        """Sin superficie usable NO se pinta la marca en ninguna esquina."""
        for s in (None, compositor.ReservedSurface(0, 0, 500, 90, flat=False)):
            r = compositor.compose(raw(), plan(), BRAND, s)
            self.assertFalse(r.brand_applied)
            self.assertEqual(r.state, compositor.NEEDS_HUMAN_REVIEW)
            self.assertTrue(any("watermark" in w or "revision humana" in w for w in r.warnings))

    def test_marca_que_no_cabe_pide_revision(self):
        s = compositor.ReservedSurface(10, 10, 12, 6)
        r = compositor.compose(raw(), plan(), BRAND, s)
        self.assertEqual(r.state, compositor.NEEDS_HUMAN_REVIEW)
        self.assertIn("BRAND_DOES_NOT_FIT", r.reason_codes)

    def test_marca_delegada_al_generador_no_se_compone(self):
        b = dict(BRAND, generator_writes_text=True)
        r = compositor.compose(raw(), plan(), b, surface())
        self.assertEqual(r.state, compositor.NEEDS_HUMAN_REVIEW)
        self.assertIn("BRAND_DELEGATED_TO_GENERATOR", r.reason_codes)

    def test_texto_de_marca_exacto(self):
        r = compositor.compose(raw(), plan(), dict(BRAND, text="LegalMente"), surface())
        self.assertTrue(r.brand_applied)


class TestLimitesDeRecursos(unittest.TestCase):
    def test_imagen_gigante_rechazada(self):
        with self.assertRaises(compositor.CompositionError):
            compositor.compose(png_bytes(9000, 10, (0, 0, 0)),
                               plan(w=9000, h=10), None, None)

    def test_texto_gigante_rechazado(self):
        p = plan("a" * (compositor.MAX_TEXT_CHARS + 1), "", "explicador")
        with self.assertRaises(compositor.CompositionError):
            compositor.compose(raw(), p, None, None)

    def test_raw_ilegible_rechazado(self):
        with self.assertRaises(compositor.CompositionError):
            compositor.compose(b"no soy una imagen", plan(), None, None)

    def test_raw_vacio_rechazado(self):
        with self.assertRaises(compositor.CompositionError):
            compositor.compose(b"", plan(), None, None)


class TestPipelineConComposicion(unittest.TestCase):
    def test_pipeline_produce_raw_y_composed_en_disco(self):
        with tempfile.TemporaryDirectory() as d:
            reg = registry_mod.AssetRegistry(d)
            run = pipeline.generate_visual(
                PROC, make_brief(), POLICY, FakeImageProvider(), HANDOFF, registry=reg,
                exact_copy=FRASE, author=AUTOR, content_type="maxima",
                reserved_surface=surface())
            self.assertTrue(run.ok)
            self.assertTrue(run.composed_bytes)
            raws = list(Path(d).rglob("raw/*.png"))
            comps = list(Path(d).rglob("composed/*.png"))
            self.assertEqual(len(raws), 1)
            self.assertEqual(len(comps), 1)
            self.assertGreater(comps[0].stat().st_size, raws[0].stat().st_size)

    def test_receipt_lleva_lineage_de_composicion(self):
        run = pipeline.generate_visual(
            PROC, make_brief(), POLICY, FakeImageProvider(), HANDOFF,
            exact_copy=FRASE, author=AUTOR, content_type="maxima",
            reserved_surface=surface())
        r = run.receipt
        self.assertTrue(r.composed_sha256)
        self.assertNotEqual(r.composed_sha256, r.asset_sha256)
        self.assertTrue(r.raw_asset_id and r.composed_asset_id)
        self.assertEqual(r.compositor_version, compositor.COMPOSITOR_VERSION)
        self.assertTrue(r.composition["typography_plan_hash"])

    def test_desbordamiento_es_estado_propio(self):
        run = pipeline.generate_visual(
            PROC, make_brief(), POLICY, FakeImageProvider(), HANDOFF,
            exact_copy="palabra " * 400, content_type="explicador",
            reserved_surface=surface())
        self.assertEqual(run.receipt.status, "COMPOSICION_DESBORDADA")
        self.assertEqual(run.item_state, pipeline.BLOCKED)

    def test_sin_exact_copy_no_compone(self):
        run = pipeline.generate_visual(PROC, make_brief(), POLICY, FakeImageProvider(), HANDOFF)
        self.assertTrue(run.ok)
        self.assertEqual(run.composed_bytes, b"")

    def test_no_sobrescribe_composed(self):
        with tempfile.TemporaryDirectory() as d:
            reg = registry_mod.AssetRegistry(d)
            run = pipeline.generate_visual(
                PROC, make_brief(), POLICY, FakeImageProvider(), HANDOFF, registry=reg,
                exact_copy=FRASE, content_type="maxima", reserved_surface=surface())
            with self.assertRaises(registry_mod.ReceiptIntegrityError):
                reg.store(run.receipt, raw_bytes=b"x", composed_bytes=b"y")

    def test_marca_sin_superficie_marca_revision_en_el_receipt(self):
        run = pipeline.generate_visual(
            PROC, make_brief(), POLICY, FakeImageProvider(), HANDOFF,
            exact_copy=FRASE, content_type="maxima", reserved_surface=None)
        self.assertTrue(run.ok)
        self.assertTrue(any("watermark" in m or "revision humana" in m
                            for m in run.receipt.motivos))


if __name__ == "__main__":
    unittest.main(verbosity=2)


class TestSuperficiesDeMarcaVariadas(unittest.TestCase):
    """§32 — BrandCompositionPlan no esta atado a una sola ubicacion."""

    VARIANTES = {
        "placa_plana_inferior": compositor.ReservedSurface(120, 1650, 500, 90),
        "lomo_de_libro_lateral": compositor.ReservedSurface(60, 700, 90, 420),
        "carpeta_centro": compositor.ReservedSurface(340, 980, 400, 120),
        "chapa_pequena_esquina_de_escena": compositor.ReservedSurface(700, 1500, 260, 70),
    }

    def test_todas_las_superficies_componen_la_marca(self):
        for nombre, s in self.VARIANTES.items():
            r = compositor.compose(raw(), plan(), BRAND, s)
            self.assertEqual(r.state, compositor.COMPOSED, nombre)
            self.assertTrue(r.brand_applied, nombre)

    def test_cada_superficie_produce_un_asset_distinto(self):
        hashes = {n: compositor.compose(raw(), plan(), BRAND, s).composed_sha256
                  for n, s in self.VARIANTES.items()}
        self.assertEqual(len(set(hashes.values())), len(self.VARIANTES),
                         "la marca deberia caer en sitios distintos, no en uno fijo")


class TestHeuristicasDeImagen(unittest.TestCase):
    """§36/§37 — un riesgo heuristico no es una certeza semantica."""

    FIXTURES = {
        "muy_oscura": ((6, 5, 5), "DARKNESS_RISK"),
        "sepia_dominante": ((150, 110, 60), "SEPIA_DOMINANCE_RISK"),
        "normal_clara": ((236, 232, 220), None),
    }

    def test_fixtures_de_riesgo(self):
        insp = inspection.HeuristicSemanticInspector()
        for nombre, (rgb, esperado) in self.FIXTURES.items():
            rep = insp.inspect(png_bytes(6, 6, rgb))
            if esperado:
                self.assertIn(esperado, rep.reason_codes, nombre)

    def test_el_riesgo_nunca_es_VISUAL_FAIL(self):
        insp = inspection.HeuristicSemanticInspector()
        for rgb, _ in self.FIXTURES.values():
            rep = insp.inspect(png_bytes(6, 6, rgb))
            self.assertNotEqual(rep.state, inspection.FAIL,
                                "una heuristica no puede fingir un fallo semantico")
            self.assertIn(rep.state, (inspection.PASS, inspection.NEEDS_HUMAN_REVIEW))

    def test_el_riesgo_se_declara_como_heuristica(self):
        rep = inspection.HeuristicSemanticInspector().inspect(png_bytes(6, 6, (5, 5, 5)))
        self.assertTrue(any("no equivalen a comprension visual" in n for n in rep.notes))

    def test_riesgo_no_bloquea_el_pipeline_pero_pide_revision(self):
        run = pipeline.generate_visual(
            PROC, make_brief(), POLICY, FakeImageProvider(), HANDOFF,
            inspector=inspection.HeuristicSemanticInspector(),
            exact_copy=FRASE, content_type="maxima", reserved_surface=surface())
        self.assertTrue(run.ok)   # estructuralmente pasa
        self.assertEqual(run.receipt.semantic_qa["state"], inspection.NEEDS_HUMAN_REVIEW)
