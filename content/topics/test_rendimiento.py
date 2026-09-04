"""El ranking de rendimiento no puede inventar una cifra que la skill no dio.

Dos riesgos:
  1. Que una forma editorial sin evidencia citada reciba un rango de todos
     modos (falsa precision editorial, el analogo de la falsa
     universalizacion juridica que el resto del repo ya vigila).
  2. Que el dato de Facebook se lea como si aplicara a otra superficie
     (LinkedIn, sitio web) sin datos propios.

Sin red. Determinista.
"""

import sys
import unittest
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))

import rendimiento as R  # noqa: E402
import transversality as T  # noqa: E402


class TestRangoDeForma(unittest.TestCase):
    def test_formas_documentadas_tienen_rango(self):
        for forma, rango_esperado, _ in R.RENDIMIENTO_DOCUMENTADO:
            rango, detalle = R.rango_de_forma(forma)
            self.assertEqual(rango, rango_esperado)
            self.assertNotEqual(detalle, R.SIN_DATO_HISTORICO)

    def test_forma_sin_evidencia_no_recibe_rango_inventado(self):
        rango, detalle = R.rango_de_forma("GUIA_O_CHECKLIST")
        self.assertIsNone(rango)
        self.assertEqual(detalle, R.SIN_DATO_HISTORICO)

    def test_forma_vacia_no_recibe_rango(self):
        rango, detalle = R.rango_de_forma("")
        self.assertIsNone(rango)
        self.assertEqual(detalle, R.SIN_DATO_HISTORICO)

    def test_forma_desconocida_no_recibe_rango(self):
        rango, _ = R.rango_de_forma("FORMA_QUE_NO_EXISTE")
        self.assertIsNone(rango)

    def test_no_distingue_mayusculas_de_minusculas(self):
        a, _ = R.rango_de_forma("mito")
        b, _ = R.rango_de_forma("MITO")
        self.assertEqual(a, b)


class TestOrdenarPorRendimiento(unittest.TestCase):
    def test_mejor_rango_primero(self):
        candidatos = [
            {"id": "a", "forma_editorial": "CONCEPTO"},
            {"id": "b", "forma_editorial": "LISTADO"},
            {"id": "c", "forma_editorial": "MITO"},
        ]
        ordenados = R.ordenar_por_rendimiento(candidatos)
        self.assertEqual([c["id"] for c in ordenados], ["b", "c", "a"])

    def test_sin_dato_va_al_final_sin_reordenarse_entre_si(self):
        """Estabilidad: dos candidatos sin cifra no compiten por un rango que
        no existe, mantienen su orden de entrada."""
        candidatos = [
            {"id": "x", "forma_editorial": "REFLEXION"},
            {"id": "y", "forma_editorial": "MITO"},
            {"id": "z", "forma_editorial": "PREGUNTA_COMUN"},
        ]
        ordenados = R.ordenar_por_rendimiento(candidatos)
        self.assertEqual([c["id"] for c in ordenados], ["y", "x", "z"])

    def test_lista_vacia_no_falla(self):
        self.assertEqual(R.ordenar_por_rendimiento([]), [])

    def test_no_muta_los_candidatos_originales(self):
        original = [{"id": "a", "forma_editorial": "MITO"}]
        R.ordenar_por_rendimiento(original)
        self.assertEqual(original, [{"id": "a", "forma_editorial": "MITO"}])


class TestAnotar(unittest.TestCase):
    def test_no_muta_el_candidato_original(self):
        candidato = {"id": "a", "forma_editorial": "MITO"}
        R.anotar(candidato)
        self.assertNotIn("_rendimiento_documentado", candidato)

    def test_incluye_fuente_y_alcance_siempre(self):
        anotado = R.anotar({"id": "a", "forma_editorial": "MITO"})
        campo = anotado["_rendimiento_documentado"]
        self.assertEqual(campo["fuente"], R.FUENTE)
        self.assertEqual(campo["alcance"], R.ALCANCE)

    def test_el_alcance_declara_explicitamente_que_no_es_generalizable(self):
        """El campo mas facil de ignorar es el que evita que alguien lea el
        rango de Facebook como si describiera LinkedIn."""
        anotado = R.anotar({"id": "a", "forma_editorial": "MITO"})
        alcance = anotado["_rendimiento_documentado"]["alcance"].lower()
        self.assertIn("facebook", alcance)
        self.assertIn("no se extrapola", alcance)

    def test_forma_sin_dato_queda_marcada_como_tal_no_omitida(self):
        anotado = R.anotar({"id": "a", "forma_editorial": "REFLEXION"})
        campo = anotado["_rendimiento_documentado"]
        self.assertIsNone(campo["rango"])
        self.assertEqual(campo["detalle"], R.SIN_DATO_HISTORICO)


class TestNoDecidePublicacion(unittest.TestCase):
    """El ranking reordena revision humana, nunca decide ni abre nada."""

    def test_anotar_no_introduce_ningun_campo_de_aprobacion_o_publicacion(self):
        anotado = R.anotar({"id": "a", "forma_editorial": "MITO"})
        for prohibido in ("gate_arte", "publicacion", "revision_humana", "aprobado"):
            self.assertNotIn(prohibido, anotado)

    def test_el_orden_no_altera_el_contenido_del_candidato(self):
        catalogo = T.cargar_catalogo()
        temas = catalogo["temas"]
        ordenados = R.ordenar_por_rendimiento(temas)
        self.assertEqual(sorted(t["id"] for t in temas), sorted(t["id"] for t in ordenados))


class TestContraElCatalogoReal(unittest.TestCase):
    """El catalogo real de 24 candidatos no debe romper el ordenamiento."""

    def test_ordena_los_24_candidatos_sin_perder_ninguno(self):
        catalogo = T.cargar_catalogo()
        temas = catalogo["temas"]
        ordenados = R.ordenar_por_rendimiento(temas)
        self.assertEqual(len(ordenados), len(temas))

    def test_mito_queda_antes_que_concepto_en_el_catalogo_real(self):
        """Prueba de integracion minima contra datos reales del repo, no solo
        fixtures fabricados."""
        catalogo = T.cargar_catalogo()
        ordenados = R.ordenar_por_rendimiento(catalogo["temas"])
        formas_en_orden = [t["forma_editorial"] for t in ordenados]
        idx_mito = next(i for i, f in enumerate(formas_en_orden) if f == "MITO")
        idx_concepto = next(i for i, f in enumerate(formas_en_orden) if f == "CONCEPTO")
        self.assertLess(idx_mito, idx_concepto)


if __name__ == "__main__":
    unittest.main()
