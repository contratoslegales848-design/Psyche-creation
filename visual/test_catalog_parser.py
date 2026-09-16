"""Catálogo maestro de dirección artística (Founder, 16-sep-2026) — el
parser debe reproducir exactamente lo que el propio documento declara
(767 módulos = 504 direcciones + 263 auxiliares), nunca menos, nunca una
lista manual reducida."""

import unittest

import catalog_parser as cp


class TestParseoCompleto(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalogo = cp.parse_catalogo()

    def test_total_direcciones_coincide_con_lo_declarado_por_el_documento(self):
        """El documento declara '504 direcciones/estilos base' — el parser
        debe encontrar exactamente eso, ni una lista recortada."""
        self.assertEqual(self.catalogo.total_direcciones, 504)

    def test_total_auxiliares_coincide_con_lo_declarado(self):
        self.assertEqual(self.catalogo.total_auxiliares, 263)

    def test_las_diez_categorias_de_direccion_estan_presentes(self):
        self.assertEqual(set(self.catalogo.direcciones), set(cp.SECCIONES_DIRECCIONES.values()))

    def test_las_siete_dimensiones_auxiliares_estan_presentes(self):
        self.assertEqual(set(self.catalogo.auxiliares), set(cp.SECCIONES_AUXILIARES.values()))

    def test_ninguna_categoria_de_direccion_esta_vacia(self):
        for cat, entradas in self.catalogo.direcciones.items():
            self.assertGreater(len(entradas), 0, cat)

    def test_ninguna_dimension_auxiliar_esta_vacia(self):
        for dim, entradas in self.catalogo.auxiliares.items():
            self.assertGreater(len(entradas), 0, dim)

    def test_no_hay_entradas_duplicadas_dentro_de_una_categoria(self):
        for cat, entradas in self.catalogo.direcciones.items():
            self.assertEqual(len(entradas), len(set(entradas)), cat)

    def test_entradas_conocidas_aparecen_en_su_categoria(self):
        self.assertIn("óleo narrativo", self.catalogo.direcciones["pintura_y_tecnicas_pictoricas"])
        self.assertIn("fotografía editorial contemporánea", self.catalogo.direcciones["fotografia"])
        self.assertIn("CGI fotorrealista", self.catalogo.direcciones["digital_cgi_y_visualizacion"])

    def test_paleta_auxiliar_no_se_reduce_a_los_cuatro_tokens_historicos(self):
        """Regresión directa del Hallazgo 2/3 de la auditoría: la paleta
        real del catálogo maestro tiene decenas de combinaciones, no 4."""
        self.assertGreaterEqual(len(self.catalogo.auxiliares["palette"]), 30)

    def test_version_y_fecha_se_extraen_del_documento(self):
        self.assertTrue(self.catalogo.version_fuente)
        self.assertTrue(self.catalogo.fecha_fuente)


class TestFailClosed(unittest.TestCase):
    def test_documento_inexistente_falla_explicitamente(self):
        with self.assertRaises(cp.CatalogParseError):
            cp.parse_catalogo(path="/no/existe/nada.md")

    def test_documento_con_pocas_direcciones_se_rechaza(self):
        import tempfile
        contenido = "# X\n\n### 3.1 Fotografia\n\n- una sola entrada\n"
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
            f.write(contenido)
            ruta = f.name
        with self.assertRaises(cp.CatalogParseError):
            cp.parse_catalogo(path=ruta)

    def test_seccion_de_direccion_vacia_se_rechaza(self):
        import tempfile
        # Todas las secciones de dirección menos una tienen contenido de sobra;
        # una queda deliberadamente vacía para probar el fail-closed.
        bloques = []
        for numero, cat in cp.SECCIONES_DIRECCIONES.items():
            bloques.append(f"### {numero} {cat}\n")
            if cat != "fotografia":
                bloques.extend(f"- entrada {cat} {i}\n" for i in range(15))
        for numero, dim in cp.SECCIONES_AUXILIARES.items():
            bloques.append(f"### {numero} {dim}\n")
            bloques.extend(f"- aux {dim} {i}\n" for i in range(15))
        contenido = "# X\n\n" + "\n".join(bloques)
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
            f.write(contenido)
            ruta = f.name
        with self.assertRaises(cp.CatalogParseError):
            cp.parse_catalogo(path=ruta)


class TestGenerarJson(unittest.TestCase):
    def test_genera_json_valido_reproducible(self):
        import json
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as d:
            destino = Path(d) / "out.json"
            c = cp.generar_json(path_json=destino)
            data = json.loads(destino.read_text(encoding="utf-8"))
            self.assertEqual(data["total_direcciones"], c.total_direcciones)
            self.assertEqual(data["total_auxiliares"], c.total_auxiliares)
            self.assertIn("generado_por", data)

    def test_es_determinista(self):
        a = cp.parse_catalogo()
        b = cp.parse_catalogo()
        self.assertEqual(a.direcciones, b.direcciones)
        self.assertEqual(a.auxiliares, b.auxiliares)


if __name__ == "__main__":
    unittest.main()
