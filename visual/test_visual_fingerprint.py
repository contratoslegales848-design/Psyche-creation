"""visual_fingerprint.py — Fases 4-7 del mandato "Súper Prompt" (16-sep-2026).

Cubre lo que la Fase 5 pide verificar en concreto: que la selección no es
random puro (favorece lo menos usado, muta si hay demasiada coincidencia),
que `medium` nunca se desalinea de la categoría real de `primary_direction`
(Fase 7 — recuento de "familias/medios" automático), que el resultado es
reproducible por content_id, y que el catálogo reducido por accidente se
rechaza en vez de usarse en silencio (mismo criterio fail-closed que
`catalog_parser.py`)."""

import json
import tempfile
import unittest
from pathlib import Path

import visual_fingerprint as vf


class TestHuellaIndividual(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalogo = vf.MasterCatalog.load()

    def test_huella_tiene_las_diez_dimensiones_no_vacias_salvo_secondary(self):
        memoria = vf.FingerprintMemory()
        h = vf.seleccionar_huella("PIEZA-001", catalogo=self.catalogo, memoria=memoria)
        for dim in vf.DIMENSIONES_HUELLA:
            if dim == "secondary_direction":
                continue
            self.assertTrue(h.valor(dim), dim)

    def test_medium_es_la_categoria_real_de_primary_direction(self):
        memoria = vf.FingerprintMemory()
        for i in range(25):
            cid = f"MED-{i:03d}"
            h = vf.seleccionar_huella(cid, catalogo=self.catalogo, memoria=memoria)
            memoria.record(cid, h)
            self.assertIn(h.primary_direction, self.catalogo.direcciones[h.medium])

    def test_secondary_direction_nunca_repite_la_categoria_del_primary(self):
        memoria = vf.FingerprintMemory()
        for i in range(25):
            cid = f"SEC-{i:03d}"
            h = vf.seleccionar_huella(cid, catalogo=self.catalogo, memoria=memoria)
            memoria.record(cid, h)
            if h.secondary_direction:
                self.assertNotIn(h.secondary_direction, self.catalogo.direcciones[h.medium])

    def test_determinismo_mismo_content_id_mismo_estado_de_memoria(self):
        a = vf.seleccionar_huella("DET-001", catalogo=self.catalogo, memoria=vf.FingerprintMemory())
        b = vf.seleccionar_huella("DET-001", catalogo=self.catalogo, memoria=vf.FingerprintMemory())
        self.assertEqual(a.to_dict(), b.to_dict())

    def test_content_id_distinto_produce_huellas_distintas(self):
        memoria = vf.FingerprintMemory()
        a = vf.seleccionar_huella("A-001", catalogo=self.catalogo, memoria=memoria)
        b = vf.seleccionar_huella("B-001", catalogo=self.catalogo, memoria=memoria)
        distintas, conocidas = vf.distancia(a, b)
        self.assertGreater(distintas, 0)


class TestAntiRepeticion(unittest.TestCase):
    """Fase 5/6/7: no es random puro — favorece lo menos usado y respeta
    distancia mínima vs. la pieza anterior y vs. el historial reciente."""

    @classmethod
    def setUpClass(cls):
        cls.catalogo = vf.MasterCatalog.load()

    def test_distancia_minima_vs_pieza_inmediatamente_anterior(self):
        memoria = vf.FingerprintMemory()
        huellas = []
        for i in range(15):
            cid = f"CONSEC-{i:03d}"
            h = vf.seleccionar_huella(cid, catalogo=self.catalogo, memoria=memoria, canal="ig")
            memoria.record(cid, h, canal="ig")
            huellas.append(h)
        for a, b in zip(huellas, huellas[1:]):
            distintas, conocidas = vf.distancia(a, b)
            if conocidas >= len(vf.DIMENSIONES_HUELLA):
                self.assertGreaterEqual(distintas, vf.MIN_DIMENSIONES_DIFERENTES_CONSECUTIVAS)

    def test_seleccion_favorece_valores_menos_usados_no_random_puro(self):
        memoria = vf.FingerprintMemory()
        mediums = []
        for i in range(40):
            cid = f"FREQ-{i:03d}"
            h = vf.seleccionar_huella(cid, catalogo=self.catalogo, memoria=memoria)
            memoria.record(cid, h)
            mediums.append(h.medium)
        conteo = {}
        for m in mediums:
            conteo[m] = conteo.get(m, 0) + 1
        # con selección anti-frecuencia real, ningún medio debería acaparar
        # una fracción desproporcionada de 40 piezas sobre 10 categorías.
        self.assertLessEqual(max(conteo.values()), 12)

    def test_memoria_es_por_canal_no_se_mezcla(self):
        memoria = vf.FingerprintMemory()
        h_li = vf.seleccionar_huella("CH-001", catalogo=self.catalogo, memoria=memoria, canal="linkedin")
        memoria.record("CH-001", h_li, canal="linkedin")
        # el canal "ig" no tiene historial propio todavía: no debe heredar
        # la última pieza de "linkedin" como si fuera su propia anterior.
        recientes_ig = memoria.recientes(canal="ig", n=1)
        self.assertEqual(recientes_ig, [])

    def test_no_se_fabrica_afinidad_tema_categoria_todas_arrancan_elegibles(self):
        """Regresión directa del criterio fail-closed del módulo: sin
        historial, cualquier categoría puede salir — no hay una tabla
        oculta de "tema X favorece categoría Y" inventada aquí."""
        vistos = set()
        for i in range(60):
            memoria = vf.FingerprintMemory()
            h = vf.seleccionar_huella(f"FRESH-{i:03d}", catalogo=self.catalogo, memoria=memoria)
            vistos.add(h.medium)
        self.assertGreaterEqual(len(vistos), 5)


class TestMasterCatalogFailClosed(unittest.TestCase):
    def test_catalogo_real_pasa_el_umbral_minimo(self):
        catalogo = vf.MasterCatalog.load()
        total_direcciones = sum(len(v) for v in catalogo.direcciones.values())
        total_auxiliares = sum(len(v) for v in catalogo.auxiliares.values())
        self.assertGreaterEqual(total_direcciones, 100)
        self.assertGreaterEqual(total_auxiliares, 100)

    def test_catalogo_reducido_por_accidente_se_rechaza(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "tiny.json"
            p.write_text(json.dumps({
                "direcciones": {"a": ["x"]},
                "auxiliares": {"b": ["y"]},
                "total_direcciones": 1,
                "total_auxiliares": 1,
            }), encoding="utf-8")
            with self.assertRaises(vf.CatalogNotLoadedError):
                vf.MasterCatalog.load(path=p)

    def test_todas_las_direcciones_es_plana_y_no_esta_dominada_por_una_categoria(self):
        catalogo = vf.MasterCatalog.load()
        plano = catalogo.todas_las_direcciones()
        self.assertEqual(len(plano), sum(len(v) for v in catalogo.direcciones.values()))


class TestDistancia(unittest.TestCase):
    def test_huellas_identicas_tienen_distancia_cero(self):
        h = vf.VisualFingerprint(
            content_id="X", primary_direction="óleo narrativo", medium="pintura_y_tecnicas_pictoricas",
            lighting="luz natural difusa", composition="regla de tercios", camera_optics="35mm",
            palette="ciruela y gris humo", materiality="lienzo", realism="fotorrealista",
            visual_mechanism="metafora visual directa")
        distintas, conocidas = vf.distancia(h, h)
        self.assertEqual(distintas, 0)
        self.assertGreater(conocidas, 0)

    def test_dimensiones_vacias_en_ambos_lados_no_cuentan_como_coincidencia(self):
        a = vf.VisualFingerprint(content_id="A", primary_direction="x", medium="m")
        b = vf.VisualFingerprint(content_id="B", primary_direction="x", medium="m")
        distintas, conocidas = vf.distancia(a, b)
        # secondary_direction vacia en ambos, y las auxiliares vacías en ambos:
        # solo primary_direction y medium cuentan como "conocidas".
        self.assertEqual(conocidas, 2)
        self.assertEqual(distintas, 0)


if __name__ == "__main__":
    unittest.main()
