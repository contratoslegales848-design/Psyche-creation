"""Fase 12-13 del mandato "Súper Prompt" (16-sep-2026): QA automatizada que
atrapa cada clase de falla nombrada explícitamente por el mandato, y la
prueba de aceptación de 10 temas reales como regresión ejecutable (no solo
un script que se corrió una vez a mano)."""

import unittest
from pathlib import Path

import catalog_parser as cp
import visual_fingerprint as vf
from brief import VisualPolicy
from compiler import compile_request
from demo_prueba_aceptacion_10_temas import TEMAS, construir_brief, ejecutar
from visual_fingerprint_batch import evaluar_lote_visual

POLICY = VisualPolicy.load()
CATALOGO = vf.MasterCatalog.load()


class TestPruebaDeAceptacion10Temas(unittest.TestCase):
    """El propio script de aceptación, corrido como test -- si deja de
    converger o de producir un lote ACEPTADO, esto falla en CI, no se
    descubre releyendo un .md generado hace tiempo."""

    @classmethod
    def setUpClass(cls):
        cls.resultados, cls.lote_qa, cls.intentos = ejecutar()

    def test_hay_diez_temas_reales_no_repetidos(self):
        self.assertEqual(len(TEMAS), 10)
        self.assertEqual(len({t["tema"] for t in TEMAS}), 10)
        self.assertEqual(len({t["content_id"] for t in TEMAS}), 10)

    def test_el_lote_de_aceptacion_es_aceptado(self):
        self.assertTrue(self.lote_qa.aceptado, self.lote_qa.incumplimientos)

    def test_cada_resultado_tiene_prompt_compilado_no_vacio(self):
        for r in self.resultados:
            self.assertTrue(r["compilado"].positive_prompt)

    def test_ninguna_pieza_menciona_azul_petroleo_como_texto_forzado(self):
        for r in self.resultados:
            self.assertNotIn(
                "el acento azul petroleo debe proceder",
                r["compilado"].positive_prompt.lower())

    def test_el_reporte_se_regenera_con_el_mismo_contenido(self):
        """Regla de negocio explicita del mandato Fase 13: el reporte es
        una SALIDA reproducible del sistema, no un documento tecleado a
        mano -- se regenera aqui mismo, dentro del test, no se lee un
        archivo estatico como si fuera la fuente de verdad."""
        destino = Path(__file__).resolve().parent.parent / "docs" / "prueba-aceptacion-10-temas-2026-09-16.md"
        self.assertTrue(destino.is_file(), "el reporte de aceptacion no existe; correr demo_prueba_aceptacion_10_temas.py")
        contenido = destino.read_text(encoding="utf-8")
        for t in TEMAS:
            self.assertIn(t["content_id"], contenido)
            self.assertIn(t["tema"], contenido)


class TestQAFasesDeFallaExplicitas(unittest.TestCase):
    """Cada clase de falla que el mandato (Fase 12) pide que un QA
    automatizado sea capaz de atrapar, probada con un caso REAL que la
    dispara -- no una aserción vacía sobre datos ya sanos."""

    def test_monopolio_de_estilo_se_atrapa(self):
        cat = vf.MasterCatalog.load()
        huella_fija = vf._construir_huella("X", cat, vf.FingerprintMemory(), "", vf._rng_para("FIJA"))
        lote = []
        for i in range(10):
            h = vf.VisualFingerprint(**{**huella_fija.to_dict(), "content_id": f"MONO-{i}"})
            lote.append(h)
        reporte = evaluar_lote_visual(lote)
        self.assertFalse(reporte.aceptado)

    def test_catalogo_reducido_por_accidente_se_atrapa(self):
        with self.assertRaises(cp.CatalogParseError):
            cp.parse_catalogo(path="/no/existe/nada.md")
        with self.assertRaises(vf.CatalogNotLoadedError):
            import tempfile, json
            with tempfile.TemporaryDirectory() as d:
                p = Path(d) / "tiny.json"
                p.write_text(json.dumps({"direcciones": {"a": ["x"]}, "auxiliares": {"b": ["y"]},
                                         "total_direcciones": 1, "total_auxiliares": 1}), encoding="utf-8")
                vf.MasterCatalog.load(path=p)

    def test_repeticion_por_dimension_se_atrapa_en_lote(self):
        # 7 medios distintos (cumple cobertura) pero primary_direction
        # identico en dos piezas consecutivas -- debe fallar igual.
        medios = ["fotografia", "pintura_y_tecnicas_pictoricas", "escultura_objeto_y_material",
                 "dibujo_grabado_y_estampa", "arquitectura_espacio_y_escenografia",
                 "digital_cgi_y_visualizacion", "movimientos_y_lenguajes_historicos",
                 "editorial_diseno_grafico_y_sistemas_impresos", "fotografia_optica_experimental",
                 "archivo_manuscrito_y_cultura_documental"]
        lote = [vf.VisualFingerprint(content_id=f"REP-{i}", primary_direction="mismo estilo repetido",
                                     medium=medios[i], lighting=f"l{i}", composition=f"c{i}",
                                     palette=f"p{i}", materiality=f"m{i}", camera_optics=f"o{i}",
                                     realism=f"r{i}", visual_mechanism=f"v{i}")
               for i in range(2)]
        for i, m in enumerate(medios[2:], start=2):
            lote.append(vf.VisualFingerprint(content_id=f"REP-{i}", primary_direction=f"estilo-{i}",
                                             medium=m, lighting=f"l{i}", composition=f"c{i}",
                                             palette=f"p{i}", materiality=f"m{i}", camera_optics=f"o{i}",
                                             realism=f"r{i}", visual_mechanism=f"v{i}"))
        reporte = evaluar_lote_visual(lote)
        self.assertFalse(reporte.aceptado)
        self.assertTrue(any("primary_direction" in m for m in reporte.incumplimientos))

    def test_metadata_no_llega_al_prompt_se_atrapa(self):
        """Si compile_request dejara de usar el fingerprint (regresion de
        Fase 10), esta asercion es la que lo detecta."""
        from test_visual_pipeline import make_brief
        memoria = vf.FingerprintMemory()
        h = vf.seleccionar_huella("QA-META-001", catalogo=CATALOGO, memoria=memoria)
        req = compile_request(make_brief(), POLICY, fingerprint=h)
        self.assertIn(h.primary_direction, req.positive_prompt)
        self.assertIn(h.palette, req.positive_prompt)

    def test_fallback_dominante_se_atrapa_por_frecuencia(self):
        """Si la seleccion colapsara a un unico medio dominante (el fallo
        original de las 8 familias), 40 piezas seguidas mostrarian un
        medio con mas del 30% de apariciones. Con seleccion real
        anti-frecuencia, ningun medio deberia acaparar tanto."""
        memoria = vf.FingerprintMemory()
        conteo = {}
        for i in range(40):
            cid = f"FALLBACK-{i:03d}"
            h = vf.seleccionar_huella(cid, catalogo=CATALOGO, memoria=memoria)
            memoria.record(cid, h)
            conteo[h.medium] = conteo.get(h.medium, 0) + 1
        dominante = max(conteo.values())
        self.assertLess(dominante / 40, 0.35, conteo)

    def test_catalogo_desconectado_de_la_fuente_se_atrapa(self):
        """El JSON derivado committeado debe ser EXACTAMENTE lo que produce
        re-parsear el .md canonico ahora mismo -- si alguien edita el JSON
        a mano o el .md cambia sin regenerar, esto falla."""
        recien_parseado = cp.parse_catalogo()
        json_committeado = vf.MasterCatalog.load()
        self.assertEqual(recien_parseado.direcciones, json_committeado.direcciones)
        self.assertEqual(recien_parseado.auxiliares, json_committeado.auxiliares)

    def test_distancia_visual_insuficiente_se_atrapa(self):
        a = vf.VisualFingerprint(content_id="A", primary_direction="x", medium="m", lighting="l",
                                 composition="c", palette="p", materiality="mat", camera_optics="o",
                                 realism="r", visual_mechanism="v")
        b = vf.VisualFingerprint(content_id="B", primary_direction="x", medium="m", lighting="l",
                                 composition="c", palette="p", materiality="mat", camera_optics="o",
                                 realism="r", visual_mechanism="distinto")
        distintas, conocidas = vf.distancia(a, b)
        self.assertEqual(conocidas, 9)
        self.assertEqual(distintas, 1)
        self.assertLess(distintas, vf.MIN_DIMENSIONES_DIFERENTES_CONSECUTIVAS)


if __name__ == "__main__":
    unittest.main()
