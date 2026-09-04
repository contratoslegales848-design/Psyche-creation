"""Pruebas del pipeline visual. Sin red, sin credenciales, sin creditos."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import gates  # noqa: E402
import pipeline  # noqa: E402
import receipts as receipts_mod  # noqa: E402
from brief import VisualBrief, VisualPolicy  # noqa: E402
from compiler import compile_request  # noqa: E402
from providers import FakeImageProvider  # noqa: E402
from providers.base import NormalizedImageRequest, negotiate  # noqa: E402
from qa import structural_qa  # noqa: E402

POLICY = VisualPolicy.load()

HANDOFF = {
    "record_type": "ProductionHandoff",
    "handoff_id": "HO-001",
    "content_id": "LM-TEST-001",
    "status": "APROBADO_QA",
}

PROC = {
    "modo": "GOBERNADO",
    "content_id": "LM-TEST-001",
    "publicable": True,
    "jurisdiction_layer": "CAPA_A_TRANSVERSAL",
    "handoff_id": "HO-001",
    "claims": [{"claim_id": "c1", "approved_claim_hash": "a" * 64}],
}


def compile_prompt(brief, policy, capabilities=None, recent_memory=(), **kw):
    """Adaptador SOLO DE PRUEBAS a la forma antigua de 4 tuplas."""
    req = compile_request(brief, policy, capabilities=capabilities, **kw)
    negs = list(req.negative_constraints)
    for e in sorted({str(x) for x in recent_memory if str(x).strip()}):
        if f"repetir: {e}" not in negs:
            negs.append(f"repetir: {e}")
    return req.positive_prompt, ", ".join(negs), req.provider_parameters, req.metadata


def make_brief(**kw):
    campos = dict(
        content_id="LM-TEST-001",
        formato="VERTICAL_9_16",
        visual_family="claroscuro_de_museo",
        subject="un escritorio de nogal con un contrato cerrado",
        environment="despacho en penumbra al amanecer",
        camera="35mm, ligeramente picada",
        focal_point="el lacre sin sellar",
        acento_frio_objeto="un tintero de vidrio azul petroleo",
        marca_superficie="sello de lacre",
    )
    campos.update(kw)
    return VisualBrief(**campos)


class TestGate(unittest.TestCase):
    def test_gate_abre_con_handoff_aprobado(self):
        self.assertTrue(gates.can_enter_visual_generation(PROC, HANDOFF).permitido)

    def test_ejemplo_tecnico_nunca_entra(self):
        d = gates.can_enter_visual_generation({"modo": "EJEMPLO_TECNICO", "content_id": "X"}, None)
        self.assertFalse(d.permitido)

    def test_sin_procedencia_cierra(self):
        self.assertFalse(gates.can_enter_visual_generation(None).permitido)
        self.assertFalse(gates.can_enter_visual_generation({}).permitido)

    def test_modo_desconocido_cierra(self):
        self.assertFalse(gates.can_enter_visual_generation({"modo": "INVENTADO"}).permitido)

    def test_gobernado_sin_handoff_aportado_cierra(self):
        """El pipeline no infiere el estado de produccion que no puede leer."""
        self.assertFalse(gates.can_enter_visual_generation(PROC, None).permitido)

    def test_handoff_no_aprobado_cierra(self):
        for status in ("PENDIENTE", "EN_PRODUCCION", "LISTO_PARA_QA"):
            h = dict(HANDOFF, status=status)
            self.assertFalse(gates.can_enter_visual_generation(PROC, h).permitido, status)

    def test_handoff_de_otra_pieza_cierra(self):
        h = dict(HANDOFF, content_id="LM-OTRA-999")
        self.assertFalse(gates.can_enter_visual_generation(PROC, h).permitido)

    def test_handoff_id_distinto_cierra(self):
        self.assertFalse(gates.can_enter_visual_generation(PROC, dict(HANDOFF, handoff_id="HO-999")).permitido)

    def test_gobernado_sin_claims_cierra(self):
        p = dict(PROC); p.pop("claims")
        self.assertFalse(gates.can_enter_visual_generation(p, HANDOFF).permitido)

    def test_claim_sin_hash_cierra(self):
        p = dict(PROC, claims=[{"claim_id": "c1"}])
        self.assertFalse(gates.can_enter_visual_generation(p, HANDOFF).permitido)

    def test_no_aplica_exige_autorizacion_humana(self):
        base = {"modo": "NO_APLICA", "content_id": "LM-NA-1"}
        self.assertFalse(gates.can_enter_visual_generation(base).permitido)
        completo = dict(base, motivo_no_aplica="cita historica",
                        autorizado_por="FUNDADOR", fecha_autorizacion="2026-08-31")
        self.assertTrue(gates.can_enter_visual_generation(completo).permitido)

    def test_produccion_exige_firma_humana(self):
        g = gates.can_enter_visual_generation(PROC, HANDOFF)
        rep = structural_qa(*_gen_ok())
        self.assertTrue(rep.passed)
        self.assertFalse(gates.can_enter_production(g, rep, False).permitido)
        self.assertFalse(gates.can_enter_production(g, rep, None).permitido)
        self.assertTrue(gates.can_enter_production(g, rep, True).permitido)

    def test_revision_humana_siempre_requerida(self):
        rep = structural_qa(*_gen_ok())
        self.assertTrue(gates.requires_human_visual_review(rep))


def _gen_ok():
    prov = FakeImageProvider()
    prompt, neg, params, _ = compile_prompt(make_brief(), POLICY, prov.capabilities())
    req = NormalizedImageRequest("LM-TEST-001", prompt, neg, params["width"],
                                 params["height"], params["aspect_ratio"], params.get("seed"))
    return prov.generate(req), params


class TestBriefYPolitica(unittest.TestCase):
    def test_brief_valido(self):
        self.assertEqual(make_brief().validate(POLICY), [])

    def test_familia_fuera_de_catalogo(self):
        self.assertTrue(make_brief(visual_family="anime_pastel").validate(POLICY))

    def test_formato_no_permitido(self):
        self.assertTrue(make_brief(formato="CUADRADO_1_1").validate(POLICY))

    def test_acento_frio_debe_ser_objeto_fisico(self):
        e = make_brief(acento_frio_objeto="").validate(POLICY)
        self.assertTrue(any("objeto fisico" in x for x in e))

    def test_marca_exige_superficie_permitida(self):
        self.assertTrue(make_brief(marca_superficie="").validate(POLICY))
        self.assertTrue(make_brief(marca_superficie="valla publicitaria").validate(POLICY))

    def test_texto_juridico_no_lo_escribe_el_generador(self):
        e = make_brief(text_rendering_mode="NATIVE_TEXT", tiene_carga_juridica=True).validate(POLICY)
        self.assertTrue(e)

    def test_decision_de_marca_aplicada(self):
        """Decision del fundador 2026-08-31: el generador no escribe la marca."""
        self.assertEqual(POLICY.marca_escribe_generador, "NO")
        self.assertTrue(POLICY.data["marca"]["integracion_fisica_requerida"])
        self.assertTrue(POLICY.data["marca"]["post_composite_brand_text"])
        self.assertFalse(POLICY.data["marca"]["generator_writes_brand_text"])

    def test_politica_de_marca_ilegible_bloquea(self):
        import copy
        from brief import VisualPolicy as VP
        d = copy.deepcopy(POLICY.data)
        d["marca"]["texto_marca_lo_escribe_el_generador"] = "QUIZAS"
        p = VP(version="x", data=d)
        self.assertTrue(make_brief(marca_texto_en_imagen=True).validate(p))

    def test_politica_sin_version_es_rechazada(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "mala.json"
            p.write_text(json.dumps({"formatos": {}}), encoding="utf-8")
            with self.assertRaises(Exception):
                VisualPolicy.load(p)


class TestCompilador(unittest.TestCase):
    def test_deterministico(self):
        a = compile_prompt(make_brief(), POLICY)
        b = compile_prompt(make_brief(), POLICY)
        self.assertEqual(a[0], b[0])
        self.assertEqual(a[3]["prompt_sha256"], b[3]["prompt_sha256"])

    def test_no_compila_brief_invalido(self):
        with self.assertRaises(ValueError):
            compile_prompt(make_brief(visual_family="inventada"), POLICY)

    def test_negativos_incluyen_prohibiciones_de_politica(self):
        _, neg, _, _ = compile_prompt(make_brief(), POLICY)
        for esperado in ("collage", "grid", "sepia dominante", "watermark", "logo flotante"):
            self.assertIn(esperado, neg)

    def test_modo_no_nativo_prohibe_texto(self):
        _, neg, _, _ = compile_prompt(make_brief(), POLICY)
        self.assertIn("letras", neg)

    def test_marca_no_resuelta_pide_superficie_vacia(self):
        prompt, _, _, _ = compile_prompt(make_brief(), POLICY)
        self.assertIn("COMPLETAMENTE VACIA", prompt)
        self.assertNotIn("'LegalMente' aparece grabada", prompt)

    def test_memoria_visual_entra_en_negativos(self):
        _, neg, _, _ = compile_prompt(make_brief(), POLICY, recent_memory=["balanza de bronce"])
        self.assertIn("repetir: balanza de bronce", neg)

    def test_parametros_del_formato(self):
        _, _, params, _ = compile_prompt(make_brief(), POLICY)
        self.assertEqual((params["width"], params["height"]), (1080, 1920))
        self.assertEqual(params["aspect_ratio"], "9:16")

    def test_versiones_registradas(self):
        _, _, _, meta = compile_prompt(make_brief(), POLICY)
        self.assertEqual(meta["visual_policy_version"], POLICY.version)
        self.assertTrue(meta["prompt_compiler_version"])

    def test_sin_acento_frio_no_deja_frase_rota(self):
        """Si una politica futura no exige objeto fisico para el acento frio y el
        brief llega sin el (el guardia de validate() es condicional, ver
        brief.py:123), el prompt no debe terminar en 'de la escena: .'."""
        import copy
        pol_sin_exigencia = copy.deepcopy(POLICY)
        pol_sin_exigencia.data["paleta"]["acento_frio_debe_ser_objeto_fisico"] = False
        prompt, _, _, _ = compile_prompt(make_brief(acento_frio_objeto=""), pol_sin_exigencia)
        self.assertNotIn("de la escena: .", prompt)
        self.assertNotIn("acento azul petroleo debe proceder", prompt)


class TestNegociacion(unittest.TestCase):
    def test_aspect_ratio_no_soportado(self):
        prov = FakeImageProvider(aspect_ratios=("1:1",))
        _, neg, params, _ = compile_prompt(make_brief(), POLICY, prov.capabilities())
        req = NormalizedImageRequest("x", "p", neg, 1080, 1920, "9:16")
        self.assertTrue(negotiate(req, prov.capabilities()))

    def test_texto_nativo_sin_capacidad(self):
        prov = FakeImageProvider(supports_reliable_text=False)
        req = NormalizedImageRequest("x", "p", "", 1080, 1920, "9:16", requires_text_rendering=True)
        self.assertTrue(negotiate(req, prov.capabilities()))

    def test_compatible_no_da_problemas(self):
        prov = FakeImageProvider()
        _, neg, params, _ = compile_prompt(make_brief(), POLICY, prov.capabilities())
        req = NormalizedImageRequest("x", "p", neg, params["width"], params["height"],
                                     params["aspect_ratio"], params.get("seed"))
        self.assertEqual(negotiate(req, prov.capabilities()), [])


class TestQA(unittest.TestCase):
    def test_qa_ok(self):
        self.assertTrue(structural_qa(*_gen_ok()).passed)

    def test_dimensiones_cambiadas(self):
        prov = FakeImageProvider("wrong_dimensions")
        _, neg, params, _ = compile_prompt(make_brief(), POLICY, prov.capabilities())
        req = NormalizedImageRequest("x", "p", neg, params["width"], params["height"],
                                     params["aspect_ratio"])
        self.assertFalse(structural_qa(prov.generate(req), params).passed)

    def test_respuesta_corrupta(self):
        prov = FakeImageProvider("corrupt_response")
        _, neg, params, _ = compile_prompt(make_brief(), POLICY, prov.capabilities())
        req = NormalizedImageRequest("x", "p", neg, params["width"], params["height"],
                                     params["aspect_ratio"])
        self.assertFalse(structural_qa(prov.generate(req), params).passed)

    def test_metadata_invalida(self):
        prov = FakeImageProvider("bad_metadata")
        _, neg, params, _ = compile_prompt(make_brief(), POLICY, prov.capabilities())
        req = NormalizedImageRequest("x", "p", neg, params["width"], params["height"],
                                     params["aspect_ratio"])
        self.assertFalse(structural_qa(prov.generate(req), params).passed)

    def test_duplicado_detectado(self):
        result, params = _gen_ok()
        rep1 = structural_qa(result, params)
        rep2 = structural_qa(result, params, known_hashes=[rep1.asset_sha256])
        self.assertFalse(rep2.passed)


class TestPipeline(unittest.TestCase):
    def test_camino_feliz_se_detiene_en_gate_humano(self):
        run = pipeline.generate_visual(PROC, make_brief(), POLICY, FakeImageProvider(), HANDOFF)
        self.assertEqual(run.receipt.status, "PENDIENTE_REVISION_HUMANA")
        self.assertEqual(run.receipt.human_visual_approval, "PENDIENTE")
        self.assertTrue(run.asset_bytes)
        self.assertTrue(run.receipt.asset_id)

    def test_ningun_camino_produce_aprobado(self):
        self.assertNotIn("APROBADO_PARA_PRODUCCION", receipts_mod.STATUS)

    def test_gate_cerrado_no_llama_al_proveedor(self):
        prov = FakeImageProvider()
        run = pipeline.generate_visual(PROC, make_brief(), POLICY, prov, handoff=None)
        self.assertEqual(run.receipt.status, "GATE_CERRADO")
        self.assertEqual(prov.llamadas, 0)

    def test_brief_invalido_no_llama_al_proveedor(self):
        prov = FakeImageProvider()
        run = pipeline.generate_visual(PROC, make_brief(visual_family="anime_pastel"),
                                       POLICY, prov, HANDOFF)
        self.assertEqual(run.receipt.status, "BRIEF_INVALIDO")
        self.assertEqual(prov.llamadas, 0)

    def test_incompatible_no_llama_al_proveedor(self):
        prov = FakeImageProvider(aspect_ratios=("1:1",))
        run = pipeline.generate_visual(PROC, make_brief(), POLICY, prov, HANDOFF)
        self.assertEqual(run.receipt.status, "PROVEEDOR_INCOMPATIBLE")
        self.assertEqual(prov.llamadas, 0)

    def test_fallos_de_proveedor(self):
        for modo, esperado in (("provider_failure", "GENERACION_FALLIDA"),
                               ("timeout", "GENERACION_FALLIDA"),
                               ("corrupt_response", "QA_FALLIDO"),
                               ("wrong_dimensions", "QA_FALLIDO"),
                               ("bad_metadata", "QA_FALLIDO")):
            run = pipeline.generate_visual(PROC, make_brief(), POLICY,
                                           FakeImageProvider(modo), HANDOFF)
            self.assertEqual(run.receipt.status, esperado, modo)
            self.assertFalse(run.ok, modo)

    def test_receipt_en_todos_los_desenlaces(self):
        casos = [
            pipeline.generate_visual(PROC, make_brief(), POLICY, FakeImageProvider(), None),
            pipeline.generate_visual(PROC, make_brief(marca_texto_en_imagen=True), POLICY,
                                     FakeImageProvider(), HANDOFF),
            pipeline.generate_visual(PROC, make_brief(), POLICY,
                                     FakeImageProvider("timeout"), HANDOFF),
            pipeline.generate_visual(PROC, make_brief(), POLICY, FakeImageProvider(), HANDOFF),
        ]
        for run in casos:
            self.assertIsNotNone(run.receipt)
            self.assertTrue(run.receipt.generation_id)
            self.assertTrue(run.receipt.created_at)
            self.assertEqual(run.receipt.content_id, "LM-TEST-001")

    def test_lote_detecta_duplicado_entre_piezas(self):
        prov = FakeImageProvider("duplicate_asset")
        items = [pipeline.BatchItem(PROC, make_brief(), HANDOFF),
                 pipeline.BatchItem(PROC, make_brief(subject="otra escena distinta"), HANDOFF)]
        batch = pipeline.run_batch(items, POLICY, prov)
        self.assertTrue(batch.items[0].run.ok)
        self.assertEqual(batch.items[1].run.receipt.status, "QA_FALLIDO")
        self.assertTrue(any("duplicado" in p for p in batch.items[1].run.receipt.qa_problemas))

    def test_lote_expone_diversidad_real_de_rotacion(self):
        """rotation.py existia, estaba probado en aislamiento, pero ningun
        camino de ejecucion lo llamaba contra un lote real -- mismo patron
        que negative_space. Aqui se comprueba que run_batch() ya deja el
        dato disponible."""
        items = [pipeline.BatchItem(PROC, make_brief(), HANDOFF),
                 pipeline.BatchItem(PROC, make_brief(subject="otra escena distinta"), HANDOFF)]
        batch = pipeline.run_batch(items, POLICY, FakeImageProvider())
        reporte = batch.diversity_report()
        self.assertEqual(reporte.total, 2)

    def test_lote_expone_variacion_entre_piezas_consecutivas(self):
        items = [pipeline.BatchItem(PROC, make_brief(), HANDOFF),
                 pipeline.BatchItem(PROC, make_brief(subject="otra escena distinta"), HANDOFF)]
        batch = pipeline.run_batch(items, POLICY, FakeImageProvider())
        checks = batch.variation_checks()
        self.assertEqual(len(checks), 2)
        self.assertTrue(checks[0].minimo_alcanzado)  # sin pieza anterior: nada que verificar

    def test_diversidad_no_cuenta_items_fallidos(self):
        prov = FakeImageProvider("duplicate_asset")
        items = [pipeline.BatchItem(PROC, make_brief(), HANDOFF),
                 pipeline.BatchItem(PROC, make_brief(subject="otra escena distinta"), HANDOFF)]
        batch = pipeline.run_batch(items, POLICY, prov)
        self.assertEqual(batch.diversity_report().total, 1)  # el duplicado no cuenta

    def test_receipt_registra_procedencia_y_versiones(self):
        run = pipeline.generate_visual(PROC, make_brief(), POLICY, FakeImageProvider(), HANDOFF)
        r = run.receipt
        self.assertEqual(r.procedencia["handoff_id"], "HO-001")
        self.assertEqual(r.procedencia["claims"][0]["approved_claim_hash"], "a" * 64)
        self.assertEqual(r.visual_policy_version, POLICY.version)
        self.assertTrue(r.prompt_sha256)
        self.assertEqual(r.provider, "fake")


class TestReceipts(unittest.TestCase):
    def test_status_desconocido_rechazado(self):
        with self.assertRaises(ValueError):
            receipts_mod.GenerationReceipt(content_id="x", status="APROBADO")

    def test_no_se_sobrescribe(self):
        r = receipts_mod.GenerationReceipt(content_id="x", status="GATE_CERRADO")
        with tempfile.TemporaryDirectory() as d:
            r.write(d)
            with self.assertRaises(FileExistsError):
                r.write(d)

    def test_serializa_a_json(self):
        r = receipts_mod.GenerationReceipt(content_id="x", status="GATE_CERRADO")
        with tempfile.TemporaryDirectory() as d:
            data = json.loads(Path(r.write(d)).read_text(encoding="utf-8"))
            self.assertEqual(data["schema_version"], receipts_mod.RECEIPT_SCHEMA_VERSION)
            self.assertEqual(data["human_visual_approval"], "PENDIENTE")


if __name__ == "__main__":
    unittest.main(verbosity=2)
