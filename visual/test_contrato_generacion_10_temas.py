"""Hotfix post-implementación (16-sep-2026), secciones 11-12: prueba de
aceptación real sobre el lote de 10 ya existente + manifiesto JSON."""

import json
import unittest

import demo_contrato_generacion_10_temas as dc
from providers.base import DELIVERY_COMPILED, GENERATION_MODE_TEXT_TO_IMAGE


class TestPruebaDeAceptacionReal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifiesto, cls.problemas = dc.ejecutar()

    def test_cumple_el_criterio_de_exito_del_mandato(self):
        self.assertEqual(self.problemas, [], self.problemas)

    def test_diez_items(self):
        self.assertEqual(self.manifiesto["count"], 10)
        self.assertEqual(len(self.manifiesto["items"]), 10)

    def test_los_diez_son_text_to_image(self):
        for it in self.manifiesto["items"]:
            self.assertEqual(it["generation_mode"], GENERATION_MODE_TEXT_TO_IMAGE)

    def test_los_diez_sin_source_image(self):
        for it in self.manifiesto["items"]:
            self.assertIsNone(it["source_image"])

    def test_los_diez_sin_reference_images(self):
        for it in self.manifiesto["items"]:
            self.assertEqual(it["reference_images"], [])

    def test_los_diez_sin_edit_instruction(self):
        for it in self.manifiesto["items"]:
            self.assertIsNone(it["edit_instruction"])

    def test_los_diez_son_independientes_content_id_unico(self):
        ids = [it["content_id"] for it in self.manifiesto["items"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_reusa_el_mismo_lote_no_inventa_otros_10(self):
        """Debe coincidir exactamente con los content_id de
        docs/prueba-real-produccion-10-temas-2026-09-16.md -- la corrida
        de esta sesión, no una lista nueva."""
        from pathlib import Path
        doc = (Path(__file__).resolve().parent.parent / "docs" /
              "prueba-real-produccion-10-temas-2026-09-16.md").read_text(encoding="utf-8")
        for it in self.manifiesto["items"]:
            self.assertIn(it["content_id"], doc)

    def test_cada_item_declara_formato_9_16(self):
        for it in self.manifiesto["items"]:
            self.assertEqual(it["format"]["aspect_ratio"], "9:16")
            self.assertEqual(it["format"]["width"], 1080)
            self.assertEqual(it["format"]["height"], 1920)
            self.assertTrue(it["format"]["single_scene"])

    def test_cada_item_trae_su_propio_fingerprint_completo(self):
        for it in self.manifiesto["items"]:
            fp = it["fingerprint"]
            for campo in ("primary_direction", "medium", "lighting", "palette",
                         "composition", "materiality", "camera_optics", "realism",
                         "visual_mechanism"):
                self.assertTrue(fp[campo], f"{it['content_id']}: {campo} vacío")

    def test_estado_de_entrega_declarado_es_compiled_nunca_generated(self):
        """No se afirma que se generaron imágenes -- ver mandato §15."""
        self.assertEqual(self.manifiesto["delivery_status"], DELIVERY_COMPILED)
        self.assertFalse(self.manifiesto["provider_connected"])
        for it in self.manifiesto["items"]:
            self.assertEqual(it["delivery_status"], DELIVERY_COMPILED)


class TestManifiestoEsJsonLimpio(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifiesto, _ = dc.ejecutar()

    def test_serializa_sin_perder_ningun_campo_de_contrato(self):
        recargado = json.loads(json.dumps(self.manifiesto, ensure_ascii=False))
        self.assertEqual(recargado["count"], 10)
        for it in recargado["items"]:
            self.assertIn("generation_mode", it)
            self.assertIn("source_image", it)

    def test_no_contiene_bytes_de_imagen(self):
        """Ningún valor del manifiesto debe parecer un blob binario/base64
        largo -- el mandato exige explícitamente 'NO incluyas bytes de
        imágenes'."""
        texto = json.dumps(self.manifiesto, ensure_ascii=False)
        # Un PNG/JPEG en base64 de una pieza real mide miles de caracteres
        # seguidos sin espacios; el manifiesto entero no debería acercarse.
        self.assertLess(len(texto), 50_000, "el manifiesto es sospechosamente grande")

    def test_manifiesto_declara_marca_canal_y_operacion(self):
        self.assertEqual(self.manifiesto["brand"], "LegalMente")
        self.assertEqual(self.manifiesto["channel"], "general")
        self.assertEqual(self.manifiesto["operation"], "batch_generation")


class TestVerificarInvariante(unittest.TestCase):
    def test_detecta_generation_mode_incorrecto(self):
        m = {"items": [{"content_id": "x", "generation_mode": "IMAGE_EDIT",
                        "source_image": None, "edit_instruction": None}]}
        problemas = dc.verificar_invariante(m)
        self.assertTrue(any("TEXT_TO_IMAGE" in p for p in problemas))

    def test_detecta_source_image_presente(self):
        m = {"items": [{"content_id": "x", "generation_mode": "TEXT_TO_IMAGE",
                        "source_image": "algo", "edit_instruction": None}]}
        problemas = dc.verificar_invariante(m)
        self.assertTrue(any("source_image" in p for p in problemas))

    def test_detecta_content_id_repetido(self):
        item = {"content_id": "x", "generation_mode": "TEXT_TO_IMAGE",
                "source_image": None, "edit_instruction": None}
        m = {"items": [item, dict(item)]}
        problemas = dc.verificar_invariante(m)
        self.assertTrue(any("independientes" in p for p in problemas))

    def test_lote_limpio_no_produce_problemas(self):
        m = {"items": [{"content_id": f"x{i}", "generation_mode": "TEXT_TO_IMAGE",
                        "source_image": None, "edit_instruction": None}
                       for i in range(10)]}
        self.assertEqual(dc.verificar_invariante(m), [])


if __name__ == "__main__":
    unittest.main()
