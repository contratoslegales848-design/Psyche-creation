"""Diversidad de arquetipo compositivo — Regla 3 del banco artístico
anterior (Drive, 8-sep-2026), recuperada en la continuación del motor
visual (17-sep-2026, 3ª pasada)."""

import unittest

import arquetipo_compositivo as arq


class TestClasificarArquetipo(unittest.TestCase):
    def test_escena_de_escritorio(self):
        a, razon = arq.clasificar_arquetipo(
            "dos sillas frente a frente en una mesa", "sala de negociacion")
        self.assertEqual(a, arq.ESCENA_ESCRITORIO)
        self.assertTrue(razon)

    def test_documento_en_closeup(self):
        a, _ = arq.clasificar_arquetipo(
            "un sobre lacrado con el sello corporativo intacto", "oficina")
        # "sobre" no coincide con documento_closeup por sí solo; probar con
        # un caso real que sí declara un documento explícito.
        a2, _ = arq.clasificar_arquetipo(
            "un diccionario etimologico abierto junto a una escritura", "archivo")
        self.assertEqual(a2, arq.DOCUMENTO_CLOSEUP)

    def test_pasillo_arquitectura_central(self):
        a, _ = arq.clasificar_arquetipo(
            "un tratado abierto", "vitrina de un museo de medicina legal")
        self.assertEqual(a, arq.PASILLO_ARQUITECTURA_CENTRAL)

    def test_objeto_sobre_superficie(self):
        a, _ = arq.clasificar_arquetipo(
            "una balanza de laboratorio con un platillo cargado", "laboratorio")
        self.assertEqual(a, arq.OBJETO_SOBRE_SUPERFICIE)

    def test_sin_clasificar_no_se_inventa(self):
        a, razon = arq.clasificar_arquetipo(
            "un poste de deslinde a medio clavar", "borde de un terreno")
        self.assertEqual(a, arq.SIN_CLASIFICAR)
        self.assertTrue(razon)

    def test_es_determinista(self):
        self.assertEqual(
            arq.clasificar_arquetipo("un documento sobre la mesa", "oficina"),
            arq.clasificar_arquetipo("un documento sobre la mesa", "oficina"))

    def test_sala_de_negociacion_prevalece_sobre_documento(self):
        """Una escena de mesa de negociación con papeles encima es
        ESCENA_ESCRITORIO, no DOCUMENTO_CLOSEUP — el orden de evaluación
        prioriza el arquetipo más específico (mesa de reunión) sobre el
        genérico (hay texto en la escena)."""
        a, _ = arq.clasificar_arquetipo(
            "dos propuestas salariales impresas, una junto a la otra",
            "sala de reuniones de recursos humanos antes de una firma")
        self.assertEqual(a, arq.ESCENA_ESCRITORIO)


class TestVerificarDiversidadArquetipos(unittest.TestCase):
    def test_tope_por_defecto_es_3(self):
        self.assertEqual(arq.MAX_POR_ARQUETIPO_DEFAULT, 3)

    def test_cuatro_del_mismo_arquetipo_falla(self):
        piezas = [(f"P{i}", "dos sillas frente a frente en una mesa", "sala de negociacion")
                 for i in range(4)]
        v = arq.verificar_diversidad_arquetipos(piezas)
        self.assertFalse(v.ok)
        self.assertIn(arq.ESCENA_ESCRITORIO, v.excedidos)
        self.assertEqual(v.excedidos[arq.ESCENA_ESCRITORIO], 4)

    def test_tres_del_mismo_arquetipo_pasa(self):
        piezas = [(f"P{i}", "dos sillas frente a frente en una mesa", "sala de negociacion")
                 for i in range(3)]
        v = arq.verificar_diversidad_arquetipos(piezas)
        self.assertTrue(v.ok)

    def test_sin_clasificar_nunca_cuenta_contra_el_tope(self):
        """Cinco piezas SIN_CLASIFICAR no deben fallar — no hay evidencia
        de que compartan arquetipo, sólo de que el clasificador no supo
        etiquetarlas."""
        piezas = [(f"P{i}", f"un poste distinto numero {i}", "terreno distinto") for i in range(5)]
        v = arq.verificar_diversidad_arquetipos(piezas)
        self.assertTrue(v.ok)
        self.assertEqual(v.conteo.get(arq.SIN_CLASIFICAR), 5)

    def test_tope_configurable(self):
        piezas = [(f"P{i}", "dos sillas frente a frente en una mesa", "sala de negociacion")
                 for i in range(4)]
        v = arq.verificar_diversidad_arquetipos(piezas, max_por_arquetipo=5)
        self.assertTrue(v.ok)

    def test_lote_real_de_10_diverso_pasa(self):
        """El lote real (10 piezas, motor editorial + autoría real de
        dirección visual) tras la corrección de arquetipos: ningún
        arquetipo supera el tope."""
        import demo_produccion_real_10_temas_nuevos as dp
        resultados, *_ = dp.ejecutar()
        piezas = [(r["candidato"].candidate_id, r["direccion"]["subject"],
                  r["direccion"]["environment"]) for r in resultados]
        v = arq.verificar_diversidad_arquetipos(piezas)
        self.assertTrue(v.ok, v.excedidos)


if __name__ == "__main__":
    unittest.main()
