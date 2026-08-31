"""Pruebas del adapter HTTP real. Cero llamadas externas: transporte inyectado."""

import base64
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pipeline  # noqa: E402
from brief import VisualPolicy  # noqa: E402
from providers.base import NormalizedImageRequest, ProviderCapabilities  # noqa: E402
from providers.fake import png_bytes  # noqa: E402
from providers.http_provider import (  # noqa: E402
    HttpImageProvider, HttpProviderConfig, HttpTransportError,
)
from providers.selection import ACCEPT, ADAPT, REJECT, evaluate  # noqa: E402
from test_visual_pipeline import HANDOFF, PROC, make_brief  # noqa: E402

POLICY = VisualPolicy.load()
PNG = png_bytes(8, 8, (43, 27, 23))
B64 = base64.b64encode(PNG).decode()


def cfg(**kw):
    base = dict(provider_id="generic-http", endpoint="https://ejemplo.invalid/v1/images",
                model="modelo-1")
    base.update(kw)
    return HttpProviderConfig(**base)


def req(w=1080, h=1920, ar="9:16", neg="sin collage", seed=7):
    return NormalizedImageRequest("LM-TEST-001", "un escritorio de nogal", neg, w, h, ar, seed=seed)


def transporte_ok(url, payload, headers, timeout):
    return {"data": [{"b64_json": B64}]}


def transporte_que_falla(kind, msg="fallo", status=None):
    def t(url, payload, headers, timeout):
        raise HttpTransportError(kind, msg, status=status)
    return t


class TestCapacidades(unittest.TestCase):
    def test_declara_capacidades(self):
        c = HttpImageProvider(cfg()).capabilities()
        self.assertEqual(c.provider_id, "generic-http")
        self.assertIn("9:16", c.aspect_ratios)
        self.assertGreater(c.max_width, 0)

    def test_capacidades_configurables_no_hardcodeadas(self):
        c = HttpImageProvider(cfg(aspect_ratios=("1:1",), supports_seed=False)).capabilities()
        self.assertEqual(c.aspect_ratios, ("1:1",))
        self.assertFalse(c.supports_seed)


class TestTraduccion(unittest.TestCase):
    def test_traduce_al_vocabulario_del_proveedor(self):
        capturado = {}

        def t(url, payload, headers, timeout):
            capturado.update(payload=payload, url=url, headers=headers)
            return {"data": [{"b64_json": B64}]}

        HttpImageProvider(cfg(), transport=t).generate(req())
        self.assertEqual(capturado["payload"]["prompt"], "un escritorio de nogal")
        self.assertEqual(capturado["payload"]["width"], 1080)
        self.assertEqual(capturado["payload"]["seed"], 7)
        self.assertEqual(capturado["payload"]["model"], "modelo-1")

    def test_field_map_personalizado(self):
        capturado = {}

        def t(url, payload, headers, timeout):
            capturado.update(payload)
            return {"data": [{"b64_json": B64}]}

        c = cfg(field_map={"prompt": "texto", "negative_prompt": "evitar",
                           "width": "ancho", "height": "alto", "seed": "semilla",
                           "model": "modelo"})
        HttpImageProvider(c, transport=t).generate(req())
        self.assertIn("texto", capturado)
        self.assertIn("ancho", capturado)
        self.assertNotIn("prompt", capturado)

    def test_omite_negativo_si_no_se_soporta(self):
        capturado = {}

        def t(url, payload, headers, timeout):
            capturado.update(payload)
            return {"data": [{"b64_json": B64}]}

        HttpImageProvider(cfg(supports_negative_prompt=False), transport=t).generate(req())
        self.assertNotIn("negative_prompt", capturado)


class TestRespuestas(unittest.TestCase):
    def test_base64_embebido(self):
        r = HttpImageProvider(cfg(), transport=transporte_ok).generate(req())
        self.assertTrue(r.ok)
        self.assertEqual(r.image_bytes, PNG)
        self.assertEqual(r.mime_type, "image/png")

    def test_url_con_descargador(self):
        t = lambda u, p, h, to: {"data": [{"url": "https://cdn.invalid/a.png"}]}
        r = HttpImageProvider(cfg(), transport=t, image_fetcher=lambda u: PNG).generate(req())
        self.assertTrue(r.ok)
        self.assertEqual(r.image_bytes, PNG)

    def test_url_sin_descargador_falla_limpio(self):
        t = lambda u, p, h, to: {"data": [{"url": "https://cdn.invalid/a.png"}]}
        r = HttpImageProvider(cfg(), transport=t).generate(req())
        self.assertFalse(r.ok)
        self.assertIn("TRANSPORT", r.error)

    def test_forma_alternativa_images(self):
        t = lambda u, p, h, to: {"images": [B64]}
        self.assertTrue(HttpImageProvider(cfg(), transport=t).generate(req()).ok)


class TestNormalizacionDeErrores(unittest.TestCase):
    """§34 — todo error del proveedor se traduce al vocabulario del dominio."""

    def test_todos_los_modos_de_fallo(self):
        casos = {
            "AUTH": "credencial invalida",
            "RATE_LIMIT": "429",
            "TIMEOUT": "se agoto el tiempo",
            "INVALID_REQUEST": "parametro invalido",
            "UNAVAILABLE": "503",
            "CONTENT_REJECTED": "rechazado por politica",
        }
        for kind, msg in casos.items():
            r = HttpImageProvider(cfg(), transport=transporte_que_falla(kind, msg)).generate(req())
            self.assertFalse(r.ok, kind)
            self.assertIn(kind, r.error)

    def test_respuesta_vacia(self):
        r = HttpImageProvider(cfg(), transport=lambda *a: {"data": []}).generate(req())
        self.assertFalse(r.ok)

    def test_asset_malformado(self):
        t = lambda u, p, h, to: {"data": [{"b64_json": "!!!no-es-base64!!!"}]}
        r = HttpImageProvider(cfg(), transport=t).generate(req())
        self.assertFalse(r.ok)
        self.assertIn("TRANSPORT", r.error)

    def test_error_en_el_cuerpo(self):
        t = lambda u, p, h, to: {"error": {"message": "blocked by safety policy"}}
        r = HttpImageProvider(cfg(), transport=t).generate(req())
        self.assertFalse(r.ok)
        self.assertIn("CONTENT_REJECTED", r.error)

    def test_forma_inesperada(self):
        r = HttpImageProvider(cfg(), transport=lambda *a: ["lista"]).generate(req())
        self.assertFalse(r.ok)

    def test_excepcion_inesperada_no_filtra_detalles(self):
        def t(u, p, h, to):
            raise RuntimeError("token=SECRETO-NO-DEBE-SALIR")
        r = HttpImageProvider(cfg(), transport=t).generate(req())
        self.assertFalse(r.ok)
        self.assertNotIn("SECRETO", r.error)


class TestCredenciales(unittest.TestCase):
    def test_falta_credencial_es_error_auth(self):
        p = HttpImageProvider(cfg(api_key_env="PROVEEDOR_INEXISTENTE_KEY"),
                              transport=transporte_ok)
        r = p.generate(req())
        self.assertFalse(r.ok)
        self.assertIn("AUTH", r.error)

    def test_credencial_no_aparece_en_el_resultado(self):
        import os
        os.environ["PRUEBA_KEY_TEMPORAL"] = "sk-SECRETO-123"
        try:
            capturado = {}

            def t(u, p, h, to):
                capturado.update(h)
                return {"data": [{"b64_json": B64}]}

            r = HttpImageProvider(cfg(api_key_env="PRUEBA_KEY_TEMPORAL"), transport=t).generate(req())
            self.assertTrue(r.ok)
            # Va en la cabecera (donde debe) y en ningun campo del resultado.
            self.assertIn("sk-SECRETO-123", capturado["Authorization"])
            import json as _j
            self.assertNotIn("SECRETO", _j.dumps(r.raw_meta) + (r.error or ""))
        finally:
            del os.environ["PRUEBA_KEY_TEMPORAL"]


class TestNegociacionConAdapterReal(unittest.TestCase):
    """§35 — nunca degrada 9:16 a 1:1 en silencio."""

    def test_accept(self):
        self.assertEqual(evaluate(req(), HttpImageProvider(cfg()).capabilities())[0], ACCEPT)

    def test_reject_si_el_proveedor_no_hace_9_16(self):
        caps = HttpImageProvider(cfg(aspect_ratios=("1:1",))).capabilities()
        d, notas = evaluate(req(), caps)
        self.assertEqual(d, REJECT)
        self.assertTrue(notas)

    def test_adapt_solo_por_resolucion(self):
        caps = HttpImageProvider(cfg(max_width=540, max_height=960)).capabilities()
        self.assertEqual(evaluate(req(), caps)[0], ADAPT)

    def test_pipeline_rechaza_sin_llamar(self):
        p = HttpImageProvider(cfg(aspect_ratios=("1:1",)), transport=transporte_ok)
        run = pipeline.generate_visual(PROC, make_brief(), POLICY, p, HANDOFF)
        self.assertEqual(run.receipt.status, "PROVEEDOR_INCOMPATIBLE")
        self.assertEqual(p.llamadas, 0)


class TestPlugInSinTocarElDominio(unittest.TestCase):
    """§63 — sustituir el proveedor no exige tocar gates, policy, receipts ni registry."""

    def test_mismo_pipeline_con_adapter_real(self):
        p = HttpImageProvider(cfg(), transport=transporte_ok)
        run = pipeline.generate_visual(PROC, make_brief(), POLICY, p, HANDOFF)
        self.assertEqual(run.receipt.status, "PENDIENTE_REVISION_HUMANA")
        self.assertEqual(run.receipt.provider, "generic-http")
        self.assertEqual(run.receipt.human_visual_approval, "PENDIENTE")

    def test_el_proveedor_no_puede_elevar_autoridad(self):
        def t(u, p, h, to):
            # Un proveedor malicioso intenta colar estado de autoridad.
            return {"data": [{"b64_json": B64}], "status": "APROBADO",
                    "legal_valid": True, "publishable": True}

        run = pipeline.generate_visual(PROC, make_brief(), POLICY,
                                       HttpImageProvider(cfg(), transport=t), HANDOFF)
        self.assertEqual(run.receipt.status, "PENDIENTE_REVISION_HUMANA")
        self.assertEqual(run.receipt.human_visual_approval, "PENDIENTE")
        import json as _j
        blob = _j.dumps(run.receipt.to_dict())
        self.assertNotIn("publishable", blob)
        self.assertNotIn("legal_valid", blob)


if __name__ == "__main__":
    unittest.main(verbosity=2)
