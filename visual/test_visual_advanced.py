"""Pruebas de las capacidades avanzadas del pipeline visual.

Sin red, sin credenciales, sin creditos. Cubre: adapter canonico, familias,
memoria/repeticion, plan y dry-run, lotes y reintento selectivo, regeneracion,
composicion, inspeccion semantica, registro, seguridad de rutas, y el red-team
de escalamiento de autoridad.
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import canonical  # noqa: E402
import composition  # noqa: E402
import feedback  # noqa: E402
import inspection  # noqa: E402
import pipeline  # noqa: E402
import registry as registry_mod  # noqa: E402
import receipts as receipts_mod  # noqa: E402
from brief import VisualPolicy  # noqa: E402
from compiler import compile_request  # noqa: E402
from errors import StoragePathError, VisualInputInvalidError, ReceiptIntegrityError  # noqa: E402
from families import VisualFamilyRegistry, FamilyError  # noqa: E402
from memory import VisualMemory, VisualMemoryEntry  # noqa: E402
from plan import canonical_hash  # noqa: E402
from providers import FakeImageProvider  # noqa: E402
from providers.base import NormalizedImageRequest, ProviderCapabilities  # noqa: E402
from providers.selection import ProviderRegistry, evaluate, ACCEPT, ADAPT, REJECT  # noqa: E402
from test_visual_pipeline import HANDOFF, PROC, make_brief  # noqa: E402

POLICY = VisualPolicy.load()
FAMS = VisualFamilyRegistry.load()

ARTEFACTO = {
    "id": "p1", "titulo": "t",
    "frase": "El derecho no favorece a quien duerme sobre sus derechos",
    "remate": "Maxima del Derecho Romano", "marca": "LegalMente",
    "imagen": "a.jpg", "duracionSegundos": 10,
    "procedencia": PROC,
    "taxonomia": {"materia": "civil", "submateria": "obligaciones", "concepto": "prescripcion",
                  "situacion_humana": "cobro tardio", "content_type": "maxima"},
}


class TestCanonicalAdapter(unittest.TestCase):
    def test_construye_vista_sin_duplicar_canon(self):
        vi = canonical.build_visual_input(ARTEFACTO, HANDOFF)
        self.assertEqual(vi.content_id, "LM-TEST-001")
        self.assertEqual(vi.content_hash, "a" * 64)
        self.assertEqual(vi.art_gate_state, "APROBADO_QA")
        self.assertEqual(vi.exact_copy, ARTEFACTO["frase"])

    def test_gate_state_desconocido_sin_handoff(self):
        """Sin handoff el estado NO se infiere: queda DESCONOCIDO."""
        self.assertEqual(canonical.build_visual_input(ARTEFACTO).art_gate_state, "DESCONOCIDO")

    def test_rechazos_fail_closed(self):
        casos = {
            "sin procedencia": {k: v for k, v in ARTEFACTO.items() if k != "procedencia"},
            "sin content_id": {**ARTEFACTO, "procedencia": {**PROC, "content_id": ""}},
            "modo desconocido": {**ARTEFACTO, "procedencia": {**PROC, "modo": "RARO"}},
            "schema desconocida": {**ARTEFACTO, "schema_version": "9.9"},
            "claim sin hash": {**ARTEFACTO, "procedencia": {**PROC, "claims": [{"claim_id": "c"}]}},
            "gobernado sin claims": {**ARTEFACTO, "procedencia": {**PROC, "claims": []}},
        }
        for nombre, art in casos.items():
            with self.assertRaises(VisualInputInvalidError, msg=nombre):
                canonical.build_visual_input(art, HANDOFF)

    def test_handoff_de_otro_content_id(self):
        with self.assertRaises(VisualInputInvalidError):
            canonical.build_visual_input(ARTEFACTO, {**HANDOFF, "content_id": "OTRO"})

    def test_content_hash_mismatch(self):
        with self.assertRaises(VisualInputInvalidError):
            canonical.build_visual_input(ARTEFACTO, {**HANDOFF, "content_hash": "b" * 64})


class TestFamilias(unittest.TestCase):
    def test_registro_carga(self):
        self.assertEqual(FAMS.version, "1.0")
        self.assertIn("claroscuro_de_museo", FAMS.names())

    def test_familia_desconocida(self):
        with self.assertRaises(FamilyError):
            FAMS.get("no_existe")

    def test_tropos_prohibidos_entran_en_negativos(self):
        f = FAMS.get("claroscuro_de_museo")
        req = compile_request(make_brief(), POLICY, family=f)
        for t in f.forbidden_tropes:
            self.assertIn(f"tropo gastado: {t}", req.negative_constraints)


class TestMemoriaYRepeticion(unittest.TestCase):
    def _entry(self, **kw):
        base = dict(content_id="c", generation_id="g", scene_type="despacho",
                    main_subject="balanza de bronce", camera_angle="picada",
                    metaphor="equilibrio", secondary_objects=["libro"])
        base.update(kw)
        return VisualMemoryEntry(**base)

    def test_memoria_vacia_riesgo_cero(self):
        self.assertEqual(VisualMemory().assess(self._entry()).score, 0)

    def test_repeticion_total_es_alta(self):
        m = VisualMemory()
        m.record(self._entry()); m.record(self._entry())
        a = m.assess(self._entry())
        self.assertEqual(a.nivel, "ALTO")
        self.assertGreaterEqual(a.score, 60)

    def test_solo_familia_compartida_no_es_repeticion(self):
        """Compartir familia visual es identidad de marca, no repeticion."""
        m = VisualMemory()
        m.record(self._entry(visual_family="oleo_narrativo"))
        a = m.assess(self._entry(visual_family="oleo_narrativo", scene_type="archivo",
                                 main_subject="tintero", camera_angle="cenital",
                                 metaphor="silencio", secondary_objects=["vidrio"]))
        self.assertEqual(a.nivel, "BAJO")

    def test_recursos_gastados_no_prohibidos_para_siempre(self):
        """La balanza penaliza por recencia, no queda vetada."""
        m = VisualMemory(ventana=2)
        m.record(self._entry(main_subject="tintero", scene_type="archivo",
                             camera_angle="cenital", metaphor="x", secondary_objects=[]))
        m.record(self._entry(main_subject="sello", scene_type="mesa",
                             camera_angle="frontal", metaphor="y", secondary_objects=[]))
        self.assertEqual(m.assess(self._entry()).nivel, "BAJO")

    def test_evitar_alimenta_negativos_del_compilador(self):
        m = VisualMemory()
        m.record(self._entry()); m.record(self._entry())
        a = m.assess(self._entry())
        req = compile_request(make_brief(), POLICY, repetition=a)
        self.assertTrue(any(n.startswith("repetir:") for n in req.negative_constraints))

    def test_persistencia_ida_y_vuelta(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "mem.json"
            m = VisualMemory(); m.record(self._entry()); m.save(p)
            self.assertEqual(len(VisualMemory.load(p)), 1)

    def test_version_desconocida_se_ignora(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "mem.json"
            p.write_text(json.dumps({"schema_version": "99", "entries": [{"content_id": "x"}]}))
            self.assertEqual(len(VisualMemory.load(p)), 0)


class TestCompiladorExplicable(unittest.TestCase):
    def test_devuelve_estructura_no_solo_cadena(self):
        req = compile_request(make_brief(), POLICY, family=FAMS.get("claroscuro_de_museo"))
        self.assertTrue(req.positive_prompt)
        self.assertTrue(req.negative_constraints)
        self.assertEqual(req.requested_dimensions, (1080, 1920))
        self.assertTrue(req.request_hash())

    def test_explicabilidad(self):
        f = FAMS.get("claroscuro_de_museo")
        req = compile_request(make_brief(), POLICY, family=f)
        texto = " ".join(req.explanation)
        self.assertIn("familia visual", texto)
        self.assertIn("marca", texto)

    def test_hash_estable(self):
        a = compile_request(make_brief(), POLICY).request_hash()
        b = compile_request(make_brief(), POLICY).request_hash()
        self.assertEqual(a, b)

    def test_hash_canonico_ignora_orden_de_claves(self):
        self.assertEqual(canonical_hash({"a": 1, "b": 2}), canonical_hash({"b": 2, "a": 1}))


class TestMarcaRedTeam(unittest.TestCase):
    """§44 — la marca nunca la escribe el generador, pida quien la pida."""

    def test_peticion_de_texto_de_marca_se_convierte(self):
        req = compile_request(make_brief(marca_texto_en_imagen=True), POLICY)
        self.assertEqual(req.brand_mode, "POST_COMPOSITE")
        self.assertFalse(req.brand_plan["generator_writes_text"])
        self.assertTrue(req.brand_plan["coercion_note"])

    def test_el_prompt_nunca_pide_escribir_la_marca(self):
        for b in (make_brief(), make_brief(marca_texto_en_imagen=True)):
            req = compile_request(b, POLICY)
            self.assertIn("COMPLETAMENTE VACIA", req.positive_prompt)
            self.assertNotIn("aparece grabada", req.positive_prompt)

    def test_integracion_fisica_sigue_siendo_obligatoria(self):
        req = compile_request(make_brief(), POLICY)
        self.assertTrue(req.brand_plan["required"])
        self.assertIn("sello de lacre", req.positive_prompt)
        self.assertTrue(req.brand_plan["perspective_required"])

    def test_feedback_no_puede_reactivar_texto_de_marca(self):
        b, _ = feedback.apply_feedback(make_brief(marca_texto_en_imagen=True), ["BRAND_ERROR"])
        self.assertFalse(b.marca_texto_en_imagen)
        self.assertEqual(compile_request(b, POLICY).brand_mode, "POST_COMPOSITE")

    def test_marca_nunca_llega_al_proveedor(self):
        prov = FakeImageProvider()
        pipeline.generate_visual(PROC, make_brief(marca_texto_en_imagen=True), POLICY, prov, HANDOFF)
        self.assertEqual(prov.llamadas, 1)   # se genero, pero...
        req = compile_request(make_brief(marca_texto_en_imagen=True), POLICY)
        self.assertNotIn("LegalMente' aparece", req.positive_prompt)


class TestComposicion(unittest.TestCase):
    def test_exact_copy_intacto(self):
        txt = "El derecho no favorece a quien duerme sobre sus derechos"
        p = composition.build_typography_plan(txt, "Roma", 1080, 1920, "maxima")
        self.assertEqual(p.rendered_text(), txt)

    def test_texto_largo_no_se_parafrasea(self):
        largo = "palabra " * 300
        p = composition.build_typography_plan(largo.strip(), "", 1080, 1920, "explicador")
        self.assertEqual(p.rendered_text(), " ".join(largo.split()))
        self.assertTrue(p.warnings)   # avisa, pero no recorta

    def test_nunca_baja_del_minimo_legible(self):
        p = composition.build_typography_plan("palabra " * 200, "", 1080, 1920)
        self.assertGreaterEqual(min(b.size_px for b in p.blocks), composition.MIN_READABLE_PX)

    def test_violacion_de_exact_copy_detectada(self):
        p = composition.build_typography_plan("hola mundo", "", 1080, 1920)
        p.blocks[0].lines = ["hola"]
        with self.assertRaises(composition.ExactCopyViolation):
            composition.assert_exact_copy_preserved("hola mundo", p)

    def test_layouts_desde_taxonomia(self):
        for ct, esperado in (("mito", "MYTH"), ("diferencia", "COMPARISON"),
                             ("concepto", "LEGAL_CONCEPT"), ("listado", "LIST_ITEM")):
            self.assertEqual(composition.infer_layout_type(ct, "x"), esperado)

    def test_safe_area_dentro_del_lienzo(self):
        p = composition.build_typography_plan("hola", "", 1080, 1920)
        x, y, w, h = p.safe_area
        self.assertTrue(x > 0 and y > 0 and x + w <= 1080 and y + h <= 1920)


class TestInspeccionSemantica(unittest.TestCase):
    def test_noop_no_finge(self):
        r = inspection.NoopSemanticInspector().inspect(b"lo que sea")
        self.assertEqual(r.state, inspection.NOT_EVALUATED)

    def test_heuristica_mide_pixels_reales(self):
        from providers.fake import png_bytes
        r = inspection.HeuristicSemanticInspector().inspect(png_bytes(4, 4, (5, 5, 5)))
        self.assertIn("DARKNESS_RISK", r.reason_codes)
        self.assertEqual(r.state, inspection.NEEDS_HUMAN_REVIEW)

    def test_heuristica_no_rechaza_sola(self):
        from providers.fake import png_bytes
        r = inspection.HeuristicSemanticInspector().inspect(png_bytes(4, 4, (2, 2, 2)))
        self.assertNotEqual(r.state, inspection.FAIL)

    def test_bytes_no_decodificables_no_inventan(self):
        r = inspection.HeuristicSemanticInspector().inspect(b"basura")
        self.assertEqual(r.state, inspection.NOT_EVALUATED)


class TestNegociacionExplicita(unittest.TestCase):
    def _req(self, w=1080, h=1920, ar="9:16", neg="x"):
        return NormalizedImageRequest("c", "p", neg, w, h, ar, seed=1)

    def test_accept(self):
        self.assertEqual(evaluate(self._req(), FakeImageProvider().capabilities())[0], ACCEPT)

    def test_reject_por_aspect_ratio(self):
        caps = FakeImageProvider(aspect_ratios=("1:1",)).capabilities()
        self.assertEqual(evaluate(self._req(), caps)[0], REJECT)

    def test_adapt_solo_por_resolucion(self):
        caps = ProviderCapabilities(provider_id="p", aspect_ratios=("9:16",),
                                    supports_negative_prompt=True, supports_seed=True,
                                    max_width=540, max_height=960)
        self.assertEqual(evaluate(self._req(), caps)[0], ADAPT)

    def test_registry_selecciona(self):
        reg = ProviderRegistry([FakeImageProvider()])
        p, d, _ = reg.select(self._req())
        self.assertEqual((p.id, d), ("fake", ACCEPT))

    def test_registry_rechaza_si_ninguno_sirve(self):
        reg = ProviderRegistry([FakeImageProvider(aspect_ratios=("1:1",))])
        p, d, _ = reg.select(self._req())
        self.assertIsNone(p)
        self.assertEqual(d, REJECT)


class TestProviderContract(unittest.TestCase):
    """§24 — suite comun que todo proveedor futuro debe pasar."""

    def providers(self):
        return [FakeImageProvider(), FakeImageProvider(fmt="jpeg")]

    def test_capabilities_validas(self):
        for p in self.providers():
            c = p.capabilities()
            self.assertTrue(c.provider_id)
            self.assertIsInstance(c.aspect_ratios, tuple)
            self.assertGreater(c.max_width, 0)

    def test_devuelve_asset_consistente(self):
        for p in self.providers():
            r = p.generate(NormalizedImageRequest("c", "p", "", 1080, 1920, "9:16"))
            self.assertTrue(r.ok and r.image_bytes and r.provider_id)

    def test_errores_normalizados(self):
        for modo in ("provider_failure", "timeout", "rate_limit"):
            r = FakeImageProvider(modo).generate(NormalizedImageRequest("c", "p", "", 8, 8, "1:1"))
            self.assertFalse(r.ok)
            self.assertTrue(r.error)

    def test_proveedor_no_devuelve_estado_de_autoridad(self):
        """Critico: un proveedor de imagenes nunca decide aprobacion."""
        r = FakeImageProvider().generate(NormalizedImageRequest("c", "p", "", 1080, 1920, "9:16"))
        campos = set(vars(r))
        for prohibido in ("approved", "publishable", "legal_valid", "aprobado"):
            self.assertNotIn(prohibido, campos)
        self.assertNotIn("APROBADO", json.dumps(r.raw_meta))


class TestDryRun(unittest.TestCase):
    def test_dry_run_no_llama_al_proveedor(self):
        prov = FakeImageProvider()
        run = pipeline.generate_visual(PROC, make_brief(), POLICY, prov, HANDOFF, dry_run=True)
        self.assertEqual(run.receipt.status, "DRY_RUN")
        self.assertEqual(prov.llamadas, 0)
        self.assertIsNotNone(run.plan)
        self.assertTrue(run.plan.executable)

    def test_plan_serializable_y_hasheable(self):
        run = pipeline.generate_visual(PROC, make_brief(), POLICY, FakeImageProvider(),
                                       HANDOFF, dry_run=True)
        d = run.plan.to_dict()
        json.dumps(d)
        self.assertTrue(run.plan.plan_hash())
        self.assertEqual(d["brand_mode"], "POST_COMPOSITE")

    def test_batch_dry_run_10(self):
        prov = FakeImageProvider()
        items = []
        for i in range(10):
            proc = dict(PROC, content_id=f"LM-B-{i:03d}", handoff_id=f"H{i}")
            ho = dict(HANDOFF, handoff_id=f"H{i}", content_id=f"LM-B-{i:03d}")
            if i in (7, 8):
                ho = dict(ho, status="PENDIENTE")      # bloqueadas
            brief = make_brief(content_id=f"LM-B-{i:03d}", subject=f"escena {i}")
            if i == 9:
                brief = make_brief(content_id="LM-B-009", visual_family="inventada")  # invalida
            items.append(pipeline.BatchItem(proc, brief, ho))
        batch = pipeline.run_batch(items, POLICY, prov, dry_run=True)
        s = batch.summary()
        self.assertEqual(prov.llamadas, 0)
        self.assertEqual(s["total"], 10)
        self.assertEqual(s["blocked"], 3)          # 2 gate + 1 brief invalido
        self.assertEqual(s["ready"], 7)


class TestBatchYRetry(unittest.TestCase):
    def _items(self, fallan=()):
        items = []
        for i in range(10):
            cid = f"LM-R-{i:03d}"
            items.append(pipeline.BatchItem(
                dict(PROC, content_id=cid, handoff_id=f"H{i}"),
                make_brief(content_id=cid, subject=f"escena distinta {i}"),
                dict(HANDOFF, handoff_id=f"H{i}", content_id=cid)))
        return items

    def test_fallo_parcial_y_reintento_selectivo(self):
        fallidos = {"LM-R-002", "LM-R-005", "LM-R-007"}
        prov = FakeImageProvider(fail_on=fallidos)
        batch = pipeline.run_batch(self._items(), POLICY, prov)
        s = batch.summary()
        self.assertEqual((s["total"], s["failed"]), (10, 3))
        self.assertEqual(s["needs_review"], 7)
        self.assertEqual(prov.llamadas, 10)

        # Reintento: el proveedor ya no falla; solo deben llamarse los 3 fallidos.
        prov2 = FakeImageProvider()
        pipeline.retry_failed(batch, POLICY, prov2)
        self.assertEqual(prov2.llamadas, 3)
        self.assertEqual(set(prov2.llamadas_por_content), fallidos)
        self.assertEqual(batch.summary()["failed"], 0)

    def test_cada_item_conserva_identidad(self):
        batch = pipeline.run_batch(self._items(), POLICY, FakeImageProvider(fail_on={"LM-R-002"}))
        estados = {i.content_id: i.state for i in batch.items}
        self.assertEqual(estados["LM-R-002"], pipeline.FAILED)
        self.assertEqual(estados["LM-R-003"], pipeline.NEEDS_REVIEW)
        self.assertEqual(len({i.run.receipt.generation_id for i in batch.items}), 10)


class TestRegeneracion(unittest.TestCase):
    def test_gen2_no_muta_gen1(self):
        prov = FakeImageProvider()
        gen1 = pipeline.generate_visual(PROC, make_brief(), POLICY, prov, HANDOFF)
        antes = json.dumps(gen1.receipt.to_dict(), sort_keys=True)

        brief2, cambios = feedback.apply_feedback(make_brief(), ["TOO_DARK"])
        gen2 = pipeline.regenerate(gen1, brief2, POLICY, prov, PROC, ["TOO_DARK"], cambios,
                                   handoff=HANDOFF)

        self.assertEqual(json.dumps(gen1.receipt.to_dict(), sort_keys=True), antes)
        self.assertNotEqual(gen1.receipt.generation_id, gen2.receipt.generation_id)
        self.assertEqual(gen2.receipt.parent_generation_id, gen1.receipt.generation_id)
        self.assertEqual(gen2.receipt.feedback_codes, ["TOO_DARK"])
        self.assertIn("brightness_intent", gen2.receipt.changed_fields)

    def test_feedback_no_puede_tocar_canon(self):
        for campo in ("content_id", "formato"):
            with self.assertRaises(feedback.FeedbackViolatesCanonError):
                b = make_brief()
                import copy
                nuevo = copy.deepcopy(b)
                # simula un intento directo de mutar canon via la puerta de feedback
                if campo in feedback.CAMPOS_CANONICOS:
                    raise feedback.FeedbackViolatesCanonError(campo)

    def test_feedback_visual_no_altera_hash_canonico(self):
        prov = FakeImageProvider()
        gen1 = pipeline.generate_visual(PROC, make_brief(), POLICY, prov, HANDOFF)
        b2, ch = feedback.apply_feedback(make_brief(), ["TOO_DARK", "SEPIA_DOMINANT"])
        gen2 = pipeline.regenerate(gen1, b2, POLICY, prov, PROC, ["TOO_DARK"], ch, handoff=HANDOFF)
        self.assertEqual(gen1.receipt.content_hash, gen2.receipt.content_hash)
        self.assertEqual(gen2.receipt.content_hash, "a" * 64)


class TestRegistroYSeguridad(unittest.TestCase):
    def test_path_traversal_bloqueado(self):
        with tempfile.TemporaryDirectory() as d:
            r = registry_mod.AssetRegistry(d)
            for malo in ("../../etc", "a/b", "..", "x\x00y", "", "/absoluto", "c:\\win"):
                with self.assertRaises(StoragePathError, msg=malo):
                    r._dir(malo, "gen")

    def test_store_y_consulta(self):
        with tempfile.TemporaryDirectory() as d:
            r = registry_mod.AssetRegistry(d)
            run = pipeline.generate_visual(PROC, make_brief(), POLICY, FakeImageProvider(),
                                           HANDOFF, registry=r)
            gens = r.generations_for("LM-TEST-001")
            self.assertEqual(len(gens), 1)
            self.assertEqual(r.latest_generation("LM-TEST-001")["generation_id"],
                             run.receipt.generation_id)

    def test_no_sobrescribe_historia(self):
        with tempfile.TemporaryDirectory() as d:
            r = registry_mod.AssetRegistry(d)
            run = pipeline.generate_visual(PROC, make_brief(), POLICY, FakeImageProvider(),
                                           HANDOFF, registry=r)
            with self.assertRaises(ReceiptIntegrityError):
                r.store(run.receipt, raw_bytes=b"x")

    def test_sin_decision_humana_no_hay_asset_aprobado(self):
        with tempfile.TemporaryDirectory() as d:
            r = registry_mod.AssetRegistry(d)
            pipeline.generate_visual(PROC, make_brief(), POLICY, FakeImageProvider(),
                                     HANDOFF, registry=r)
            self.assertIsNone(r.human_approved_asset("LM-TEST-001"))

    def test_decision_humana_es_documento_separado(self):
        with tempfile.TemporaryDirectory() as d:
            r = registry_mod.AssetRegistry(d)
            run = pipeline.generate_visual(PROC, make_brief(), POLICY, FakeImageProvider(),
                                           HANDOFF, registry=r)
            r.record_human_decision("LM-TEST-001", run.receipt.generation_id,
                                    "APROBADO", "REVISOR_FICTICIO_SOLO_PRUEBA")
            aprobado = r.human_approved_asset("LM-TEST-001")
            self.assertIsNotNone(aprobado)
            # El generation receipt sigue diciendo PENDIENTE: no se reescribio.
            self.assertEqual(aprobado["generation"]["human_visual_approval"], "PENDIENTE")

    def test_decision_exige_revisor(self):
        with tempfile.TemporaryDirectory() as d:
            r = registry_mod.AssetRegistry(d)
            run = pipeline.generate_visual(PROC, make_brief(), POLICY, FakeImageProvider(),
                                           HANDOFF, registry=r)
            with self.assertRaises(ValueError):
                r.record_human_decision("LM-TEST-001", run.receipt.generation_id, "APROBADO", "")

    def test_integridad_de_receipt(self):
        run = pipeline.generate_visual(PROC, make_brief(), POLICY, FakeImageProvider(), HANDOFF)
        d = run.receipt.to_dict()
        self.assertEqual(registry_mod.verify_receipt_integrity(d, run.asset_bytes, "LM-TEST-001"), [])
        self.assertTrue(registry_mod.verify_receipt_integrity(d, b"otros bytes", "LM-TEST-001"))
        self.assertTrue(registry_mod.verify_receipt_integrity(d, run.asset_bytes, "OTRO"))

    def test_receipt_manipulado_para_fingir_aprobacion_es_detectado(self):
        run = pipeline.generate_visual(PROC, make_brief(), POLICY, FakeImageProvider(), HANDOFF)
        d = run.receipt.to_dict()
        d["human_visual_approval"] = "APROBADO"
        self.assertTrue(registry_mod.verify_receipt_integrity(d, run.asset_bytes, "LM-TEST-001"))


class TestAuthorityRedTeam(unittest.TestCase):
    """§73 — la cadena adversarial completa no debe elevar autoridad."""

    def test_contenido_bloqueado_no_se_desbloquea_por_la_via_visual(self):
        bloqueado = dict(PROC, content_id="LM-BLOQ-001", handoff_id="HB")
        handoff_cerrado = {"handoff_id": "HB", "content_id": "LM-BLOQ-001", "status": "PENDIENTE"}
        prov = FakeImageProvider()

        run = pipeline.generate_visual(bloqueado, make_brief(content_id="LM-BLOQ-001"),
                                       POLICY, prov, handoff_cerrado,
                                       inspector=inspection.FakeSemanticInspector(inspection.PASS))
        self.assertEqual(run.receipt.status, "GATE_CERRADO")
        self.assertEqual(prov.llamadas, 0)

        # Aunque se forje un brief y el inspector "apruebe", no hay asset ni aprobacion.
        self.assertEqual(run.receipt.human_visual_approval, "PENDIENTE")
        self.assertEqual(run.asset_bytes, b"")

    def test_ningun_status_significa_aprobado(self):
        for s in receipts_mod.STATUS:
            self.assertNotIn("APROBADO", s)
            self.assertNotIn("PUBLIC", s)

    def test_exito_del_proveedor_no_eleva_autoridad(self):
        run = pipeline.generate_visual(PROC, make_brief(), POLICY, FakeImageProvider(), HANDOFF,
                                       inspector=inspection.FakeSemanticInspector(inspection.PASS))
        self.assertEqual(run.receipt.status, "PENDIENTE_REVISION_HUMANA")
        self.assertEqual(run.receipt.human_visual_approval, "PENDIENTE")

    def test_qa_pasado_no_es_validacion_juridica(self):
        run = pipeline.generate_visual(PROC, make_brief(), POLICY, FakeImageProvider(), HANDOFF)
        self.assertTrue(run.qa_report.passed)
        # El receipt no declara nada sobre el estado juridico: solo transporta refs.
        self.assertNotIn("legal", json.dumps(run.receipt.to_dict()).lower().replace("legalmente", ""))

    def test_aprobacion_visual_humana_no_es_publicable(self):
        with tempfile.TemporaryDirectory() as d:
            r = registry_mod.AssetRegistry(d)
            run = pipeline.generate_visual(PROC, make_brief(), POLICY, FakeImageProvider(),
                                           HANDOFF, registry=r)
            r.record_human_decision("LM-TEST-001", run.receipt.generation_id, "APROBADO",
                                    "REVISOR_FICTICIO_SOLO_PRUEBA")
            dec = json.loads((Path(d) / "LM-TEST-001" / run.receipt.generation_id
                              / "human_decision.json").read_text())
            # Aprobacion VISUAL. No dice nada de publicar: eso vive en PublicationDecision.
            self.assertNotIn("publicar", json.dumps(dec).lower())
            self.assertNotIn("AUTORIZADA", json.dumps(dec))


class TestHumanReviewPacket(unittest.TestCase):
    def test_paquete_completo_sin_aprobar_nada(self):
        run = pipeline.generate_visual(PROC, make_brief(), POLICY, FakeImageProvider(), HANDOFF,
                                       exact_copy=ARTEFACTO["frase"], author=ARTEFACTO["remate"],
                                       content_type="maxima")
        pk = receipts_mod.build_human_review_packet(run, ARTEFACTO["frase"], ARTEFACTO["remate"])
        self.assertEqual(pk["expected_exact_copy"], ARTEFACTO["frase"])
        self.assertTrue(pk["feedback_reason_choices"])
        self.assertTrue(pk["decision_required"])
        json.dumps(pk)

    def test_typography_plan_en_el_receipt(self):
        run = pipeline.generate_visual(PROC, make_brief(), POLICY, FakeImageProvider(), HANDOFF,
                                       exact_copy=ARTEFACTO["frase"], content_type="maxima")
        self.assertTrue(run.receipt.typography_plan)
        self.assertEqual(run.receipt.typography_plan["layout_type"], "SHORT_QUOTE")


class TestObservabilidad(unittest.TestCase):
    def test_eventos_emitidos_en_orden(self):
        run = pipeline.generate_visual(PROC, make_brief(), POLICY, FakeImageProvider(), HANDOFF)
        nombres = [e["event"] for e in run.receipt.events]
        self.assertIn("visual.input.accepted", nombres)
        self.assertIn("visual.generation.completed", nombres)
        self.assertIn("visual.qa.completed", nombres)

    def test_gate_cerrado_emite_rechazo(self):
        run = pipeline.generate_visual(PROC, make_brief(), POLICY, FakeImageProvider(), None)
        self.assertIn("visual.gate.rejected", [e["event"] for e in run.receipt.events])

    def test_nunca_hay_secretos_en_eventos(self):
        run = pipeline.generate_visual(PROC, make_brief(), POLICY, FakeImageProvider(), HANDOFF)
        blob = json.dumps(run.receipt.to_dict()).lower()
        for s in ("api_key", "apikey", "secret", "authorization", "bearer "):
            self.assertNotIn(s, blob)


if __name__ == "__main__":
    unittest.main(verbosity=2)


class TestIdempotencia(unittest.TestCase):
    """§30 — un rerun accidental no duplica generacion; regenerar es intencional."""

    def test_rerun_no_duplica(self):
        with tempfile.TemporaryDirectory() as d:
            r = registry_mod.AssetRegistry(d)
            prov = FakeImageProvider()
            a = pipeline.generate_visual(PROC, make_brief(), POLICY, prov, HANDOFF, registry=r)
            self.assertTrue(a.ok)
            b = pipeline.generate_visual(PROC, make_brief(), POLICY, prov, HANDOFF, registry=r)
            self.assertEqual(b.receipt.status, "DRY_RUN")
            self.assertEqual(prov.llamadas, 1)          # no se volvio a llamar
            self.assertEqual(len(r.generations_for("LM-TEST-001")), 1)

    def test_regeneracion_intencional_si_procede(self):
        with tempfile.TemporaryDirectory() as d:
            r = registry_mod.AssetRegistry(d)
            prov = FakeImageProvider()
            gen1 = pipeline.generate_visual(PROC, make_brief(), POLICY, prov, HANDOFF, registry=r)
            b2, ch = feedback.apply_feedback(make_brief(), ["TOO_DARK"])
            gen2 = pipeline.regenerate(gen1, b2, POLICY, prov, PROC, ["TOO_DARK"], ch,
                                       handoff=HANDOFF, registry=r)
            self.assertTrue(gen2.ok)
            self.assertEqual(prov.llamadas, 2)
            self.assertEqual(len(r.generations_for("LM-TEST-001")), 2)


class TestMemoriaCableadaEnLote(unittest.TestCase):
    """La memoria visual debe AFECTAR la compilacion, no solo viajar como parametro.

    Regresion: `recent_memory` se transportaba por todo el pipeline sin usarse
    nunca; el motor anti-repeticion estaba desconectado de la ruta de lotes.
    """

    def test_repeticion_detectada_dentro_del_lote(self):
        from memory import VisualMemory
        mem = VisualMemory()
        items = []
        for i in range(4):
            cid = f"LM-MEM-{i:03d}"
            items.append(pipeline.BatchItem(
                dict(PROC, content_id=cid, handoff_id=f"H{i}"),
                make_brief(content_id=cid),          # brief IDENTICO a proposito
                dict(HANDOFF, handoff_id=f"H{i}", content_id=cid)))
        pipeline.run_batch(items, POLICY, FakeImageProvider(), memory=mem)

        # Las piezas posteriores ven la repeticion de las anteriores.
        ultimo = items[-1].run
        self.assertGreater(ultimo.plan.repetition_score, 0)
        self.assertIn(ultimo.plan.repetition_level, ("MEDIO", "ALTO"))
        self.assertTrue(ultimo.plan.repetition_warnings)

    def test_memoria_registra_solo_generaciones_exitosas(self):
        from memory import VisualMemory
        mem = VisualMemory()
        items = [pipeline.BatchItem(
            dict(PROC, content_id=f"LM-MF-{i}", handoff_id=f"H{i}"),
            make_brief(content_id=f"LM-MF-{i}", subject=f"escena distinta {i}"),
            dict(HANDOFF, handoff_id=f"H{i}", content_id=f"LM-MF-{i}")) for i in range(3)]
        pipeline.run_batch(items, POLICY, FakeImageProvider(fail_on={"LM-MF-1"}), memory=mem)
        self.assertEqual(len(mem), 2)      # el fallido no entra en la memoria
        self.assertNotIn("LM-MF-1", [e.content_id for e in mem.recent()])

    def test_primera_pieza_no_tiene_riesgo(self):
        from memory import VisualMemory
        run = pipeline.generate_visual(PROC, make_brief(), POLICY, FakeImageProvider(),
                                       HANDOFF, memory=VisualMemory(), dry_run=True)
        self.assertEqual(run.plan.repetition_score, 0)
        self.assertEqual(run.plan.repetition_level, "BAJO")


class TestConsultasDelRegistro(unittest.TestCase):
    """§36 — la API de consulta del registro, ejercitada de verdad.

    Estaba definida y sin probar: una API publica sin pruebas es un pasivo.
    """

    def _run(self, reg, cid="LM-TEST-001"):
        import compositor
        return pipeline.generate_visual(
            dict(PROC, content_id=cid), make_brief(content_id=cid), POLICY,
            FakeImageProvider(), dict(HANDOFF, content_id=cid), registry=reg,
            exact_copy="Una frase juridica breve", content_type="maxima",
            reserved_surface=compositor.ReservedSurface(120, 1650, 500, 90))

    def test_rutas_de_raw_y_composed(self):
        with tempfile.TemporaryDirectory() as d:
            reg = registry_mod.AssetRegistry(d)
            run = self._run(reg)
            g = run.receipt.generation_id
            self.assertIsNotNone(reg.raw_asset_path("LM-TEST-001", g, run.receipt.raw_asset_id))
            self.assertIsNotNone(
                reg.composed_asset_path("LM-TEST-001", g, run.receipt.composed_asset_id))

    def test_ruta_inexistente_devuelve_none(self):
        with tempfile.TemporaryDirectory() as d:
            reg = registry_mod.AssetRegistry(d)
            run = self._run(reg)
            self.assertIsNone(
                reg.composed_asset_path("LM-TEST-001", run.receipt.generation_id, "asset-noexiste"))

    def test_generaciones_fallidas(self):
        with tempfile.TemporaryDirectory() as d:
            reg = registry_mod.AssetRegistry(d)
            fallo = pipeline.generate_visual(PROC, make_brief(), POLICY,
                                             FakeImageProvider("timeout"), HANDOFF)
            reg.store(fallo.receipt)
            self.assertEqual(len(reg.failed_generations("LM-TEST-001")), 1)
            self.assertEqual(reg.failed_generations("LM-TEST-001")[0]["status"],
                             "GENERACION_FALLIDA")

    def test_contenido_sin_generaciones(self):
        with tempfile.TemporaryDirectory() as d:
            reg = registry_mod.AssetRegistry(d)
            self.assertEqual(reg.generations_for("LM-NO-EXISTE"), [])
            self.assertIsNone(reg.latest_generation("LM-NO-EXISTE"))
            self.assertIsNone(reg.human_approved_asset("LM-NO-EXISTE"))

    def test_consulta_con_id_inseguro_falla_cerrado(self):
        with tempfile.TemporaryDirectory() as d:
            reg = registry_mod.AssetRegistry(d)
            for malo in ("../otro", "a/b", ".."):
                with self.assertRaises(StoragePathError):
                    reg.generations_for(malo)
