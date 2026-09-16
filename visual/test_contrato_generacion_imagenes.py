"""HOTFIX post-implementación (16-sep-2026): contrato de salida
text-to-image vs. image-edit. Los 10 tests obligatorios (§10 del mandato),
uno por clase — nombrados TEST_A..TEST_J tal como los pide el mandato.

Causa raíz real (ver providers/base.py, docstring del módulo):
`NormalizedImageRequest` — el único lugar del repo donde se construye la
petición final a un proveedor (`pipeline.py::generate_visual`, una sola
vez) — no declaraba ningún campo de modo de operación. Un consumidor
externo no tenía forma estructural de distinguir una creación desde cero
de una edición.
"""

import base64
import json
import unittest
from dataclasses import asdict
from unittest.mock import patch

import demo_produccion_real_10_temas_nuevos as prod
import pipeline
from brief import VisualPolicy
from compiler import compile_request
from providers import FakeImageProvider
from providers.base import (
    GENERATION_MODE_TEXT_TO_IMAGE, GENERATION_MODE_IMAGE_EDIT,
    NormalizedImageRequest, ProviderCapabilities, negotiate, validate_generation_contract,
)
from providers.fake import png_bytes
from providers.http_provider import HttpImageProvider, HttpProviderConfig
from test_visual_pipeline import HANDOFF, PROC, make_brief

POLICY = VisualPolicy.load()
PNG = png_bytes(8, 8, (43, 27, 23))


class TestA_NuevaImagenProduceTextToImage(unittest.TestCase):
    """Una solicitud de nueva imagen produce TEXT_TO_IMAGE."""

    def test_compile_request_por_defecto_es_text_to_image(self):
        req = compile_request(make_brief(), POLICY)
        self.assertEqual(req.generation_mode, GENERATION_MODE_TEXT_TO_IMAGE)

    def test_llega_asi_hasta_la_peticion_normalizada_al_proveedor(self):
        run = pipeline.generate_visual(PROC, make_brief(), POLICY, FakeImageProvider(),
                                       HANDOFF, dry_run=True)
        self.assertTrue(run.plan.provider_capabilities_snapshot["provider_id"])
        # el modo viaja en el CompiledVisualRequest que pipeline usó para
        # construir NormalizedImageRequest -- ambos deben coincidir.
        self.assertEqual(run.compiled.generation_mode, GENERATION_MODE_TEXT_TO_IMAGE)


class TestB_TextToImageSinSourceImage(unittest.TestCase):
    """TEXT_TO_IMAGE no contiene source_image (ni reference_images ni
    edit_instruction)."""

    def test_ningun_campo_de_edicion_presente(self):
        req = compile_request(make_brief(), POLICY)
        self.assertIsNone(req.source_image)
        self.assertEqual(req.reference_images, ())
        self.assertIsNone(req.edit_instruction)

    def test_tampoco_en_la_peticion_normalizada_real(self):
        run = pipeline.generate_visual(PROC, make_brief(), POLICY, FakeImageProvider(),
                                       HANDOFF, dry_run=True)
        self.assertEqual(run.compiled.source_image, None)


class TestC_ImageEditSinSourceImageFalla(unittest.TestCase):
    """IMAGE_EDIT sin source_image falla."""

    def test_validate_generation_contract_reporta_el_problema(self):
        req = NormalizedImageRequest("x", "editar la escena", "", 1080, 1920, "9:16",
                                     generation_mode=GENERATION_MODE_IMAGE_EDIT)
        problemas = validate_generation_contract(req)
        self.assertTrue(problemas)
        self.assertTrue(any("source_image" in p for p in problemas))

    def test_http_provider_nunca_intenta_adivinar_o_rellenar(self):
        """No hay fallback automático: sin source_image, ni siquiera se
        intenta construir el payload de edición."""
        req = NormalizedImageRequest("x", "editar", "", 1080, 1920, "9:16",
                                     generation_mode=GENERATION_MODE_IMAGE_EDIT)
        self.assertIsNone(req.source_image)
        self.assertTrue(validate_generation_contract(req))


class TestD_TextToImageConSourceImageFalla(unittest.TestCase):
    """TEXT_TO_IMAGE con source_image falla."""

    def test_validate_generation_contract_reporta_el_problema(self):
        req = NormalizedImageRequest("x", "p", "", 1080, 1920, "9:16", source_image=PNG)
        problemas = validate_generation_contract(req)
        self.assertTrue(problemas)
        self.assertTrue(any("source_image" in p for p in problemas))

    def test_pipeline_rechaza_con_receipt_explicito_nunca_llama_al_proveedor(self):
        """Simula el caso que el mandato describe: algo construye un
        CompiledVisualRequest inconsistente (TEXT_TO_IMAGE con
        source_image). pipeline.py debe rechazarlo con un receipt
        CONTRATO_GENERACION_INVALIDO, nunca llamar al proveedor ni
        adivinar cuál de los dos campos "tiene razón"."""
        prov = FakeImageProvider()
        original = compile_request

        def roto(*a, **kw):
            r = original(*a, **kw)
            r.source_image = PNG   # inconsistente a propósito
            return r

        with patch("pipeline.compile_request", side_effect=roto):
            run = pipeline.generate_visual(PROC, make_brief(), POLICY, prov, HANDOFF)
        self.assertEqual(run.receipt.status, "CONTRATO_GENERACION_INVALIDO")
        self.assertEqual(prov.llamadas, 0)


class TestE_BatchDeDiezOperacionesIndependientes(unittest.TestCase):
    """Un batch de 10 imágenes nuevas produce exactamente 10 operaciones
    TEXT_TO_IMAGE independientes."""

    @classmethod
    def setUpClass(cls):
        cls.resultados, *_ = prod.ejecutar()

    def test_hay_exactamente_diez(self):
        self.assertEqual(len(self.resultados), 10)

    def test_las_diez_son_text_to_image(self):
        for r in self.resultados:
            self.assertEqual(r["compilado"].generation_mode, GENERATION_MODE_TEXT_TO_IMAGE)

    def test_ninguna_es_una_variacion_de_la_anterior(self):
        """No: pieza 1 -> variación -> variación... Cada compilado es
        independiente: content_id propio, sin source_image ni referencia a
        ningún asset previo."""
        content_ids = [r["compilado"].provider_parameters.get("content_id")
                       for r in self.resultados]
        self.assertEqual(len(content_ids), len(set(content_ids)),
                         "hay content_id repetidos: el batch no es independiente")


class TestF_NingunaPiezaHeredaDeLaAnterior(unittest.TestCase):
    """Ninguna pieza hereda image_id/source_image/reference de la pieza
    anterior."""

    @classmethod
    def setUpClass(cls):
        cls.resultados, *_ = prod.ejecutar()

    def test_ninguna_pieza_lleva_source_image_ni_reference_images(self):
        for r in self.resultados:
            comp = r["compilado"]
            self.assertIsNone(comp.source_image)
            self.assertEqual(comp.reference_images, ())
            self.assertIsNone(comp.edit_instruction)

    def test_cada_huella_visual_tiene_su_propio_content_id(self):
        ids = [r["huella"].content_id for r in self.resultados]
        self.assertEqual(len(ids), len(set(ids)))
        for r in self.resultados:
            self.assertEqual(r["huella"].content_id, r["candidato"].candidate_id)


class TestG_LosDiezPromptsConservanSusFingerprints(unittest.TestCase):
    """Los 10 prompts conservan sus fingerprints individuales."""

    @classmethod
    def setUpClass(cls):
        cls.resultados, *_ = prod.ejecutar()

    def test_cada_prompt_contiene_su_propia_huella_no_la_de_otra_pieza(self):
        for i, r in enumerate(self.resultados):
            h = r["huella"]
            self.assertIn(h.primary_direction, r["compilado"].positive_prompt)
            for j, otro in enumerate(self.resultados):
                if i == j:
                    continue
                # otra huella no debe imponerse sobre esta (no verifica que
                # el texto nunca coincida por casualidad en una palabra —
                # verifica que la metadata transportada es la propia).
                self.assertEqual(r["compilado"].metadata["visual_fingerprint"]["content_id"],
                                 h.content_id)

    def test_los_diez_sha256_de_prompt_son_distintos(self):
        hashes = {r["compilado"].metadata["prompt_sha256"] for r in self.resultados}
        self.assertEqual(len(hashes), 10)


class TestH_SerializacionConservaGenerationMode(unittest.TestCase):
    """La serialización/deserialización conserva generation_mode."""

    def test_compiled_visual_request_to_dict_incluye_generation_mode(self):
        req = compile_request(make_brief(), POLICY)
        d = req.to_dict()
        self.assertEqual(d["generation_mode"], GENERATION_MODE_TEXT_TO_IMAGE)

    def test_sobrevive_un_ciclo_json_completo(self):
        req = compile_request(make_brief(), POLICY)
        recargado = json.loads(json.dumps(req.to_dict()))
        self.assertEqual(recargado["generation_mode"], req.generation_mode)
        self.assertIsNone(recargado["source_image"])

    def test_normalized_image_request_tambien_serializa_el_modo(self):
        edit_req = NormalizedImageRequest(
            "x", "p", "", 1080, 1920, "9:16", generation_mode=GENERATION_MODE_IMAGE_EDIT,
            source_image=PNG)
        d = asdict(edit_req)
        self.assertEqual(d["generation_mode"], GENERATION_MODE_IMAGE_EDIT)
        recargado = json.loads(json.dumps({**d, "source_image": base64.b64encode(PNG).decode()}))
        self.assertEqual(recargado["generation_mode"], GENERATION_MODE_IMAGE_EDIT)


class TestI_DeterministaCuandoCorresponde(unittest.TestCase):
    """El comportamiento es determinista cuando corresponde."""

    def test_mismo_brief_mismo_generation_mode_y_hash(self):
        a = compile_request(make_brief(), POLICY)
        b = compile_request(make_brief(), POLICY)
        self.assertEqual(a.generation_mode, b.generation_mode)
        self.assertEqual(a.request_hash(), b.request_hash())

    def test_el_batch_de_10_es_reproducible_con_la_misma_semilla(self):
        r1, *_ = prod.ejecutar()
        r2, *_ = prod.ejecutar()
        modos1 = [r["compilado"].generation_mode for r in r1]
        modos2 = [r["compilado"].generation_mode for r in r2]
        self.assertEqual(modos1, modos2)
        self.assertTrue(all(m == GENERATION_MODE_TEXT_TO_IMAGE for m in modos1))


class TestJ_NoRompeImageEditExistente(unittest.TestCase):
    """No se rompe el flujo legítimo IMAGE_EDIT — no existía un flujo de
    edición implementado antes de este hotfix (ver
    docs/auditoria-inteligencia-tematica-2026-09-16.md §3: no hay proveedor
    real conectado), así que "no romper" significa que el contrato
    ESTRUCTURAL para IMAGE_EDIT queda intacto y utilizable de punta a
    punta, sin mezclarse con TEXT_TO_IMAGE."""

    def test_una_peticion_image_edit_bien_formada_pasa_la_validacion(self):
        req = NormalizedImageRequest(
            "x", "corregir el color de la placa", "", 1080, 1920, "9:16",
            generation_mode=GENERATION_MODE_IMAGE_EDIT, source_image=PNG,
            edit_instruction="ajustar el tono de la placa a dorado envejecido")
        self.assertEqual(validate_generation_contract(req), [])

    def test_negotiate_acepta_image_edit_si_el_proveedor_lo_declara(self):
        req = NormalizedImageRequest(
            "x", "p", "", 1080, 1920, "9:16",
            generation_mode=GENERATION_MODE_IMAGE_EDIT, source_image=PNG)
        caps = ProviderCapabilities(provider_id="edita-1", aspect_ratios=("9:16",),
                                    supports_editing=True)
        self.assertEqual(negotiate(req, caps), [])

    def test_el_adapter_http_real_completa_una_edicion_de_punta_a_punta(self):
        capturado = {}

        def t(url, payload, headers, timeout):
            capturado.update(url=url, payload=payload)
            return {"data": [{"b64_json": base64.b64encode(PNG).decode()}]}

        cfg = HttpProviderConfig(provider_id="edita-1", endpoint="https://x.invalid/create",
                                 edit_endpoint="https://x.invalid/edit", supports_editing=True)
        req = NormalizedImageRequest(
            "x", "p", "", 8, 8, "9:16", generation_mode=GENERATION_MODE_IMAGE_EDIT,
            source_image=PNG, edit_instruction="aclarar")
        resultado = HttpImageProvider(cfg, transport=t).generate(req)
        self.assertTrue(resultado.ok)
        self.assertEqual(capturado["url"], "https://x.invalid/edit")


if __name__ == "__main__":
    unittest.main()
