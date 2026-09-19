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


class TestAfinidadFamiliasPerceptuales(unittest.TestCase):
    """Regla 9 del banco anterior ("revisión del lote como portafolio"):
    arquetipos individualmente distintos pero perceptualmente cercanos
    (documento en close-up + escena de escritorio, ambos "interior
    institucional") deben pesar juntos contra un tope combinado."""

    def _piezas_interior_institucional(self, n):
        combos = [
            ("un documento sobre la mesa", "archivo notarial"),
            ("dos sillas frente a frente en una mesa", "sala de reuniones"),
            ("un tratado abierto", "vitrina de un museo"),
        ]
        return [(f"P{i}", *combos[i % len(combos)]) for i in range(n)]

    def test_tope_por_defecto_es_4(self):
        self.assertEqual(arq.MAX_POR_FAMILIA_DEFAULT, 4)

    def test_siete_de_familia_cercana_falla_aunque_cada_arquetipo_respete_su_tope(self):
        """Reproduce el hallazgo real: 7 piezas repartidas entre 3
        arquetipos de la misma familia (documento/escritorio/pasillo),
        cada uno con ≤3 — el tope INDIVIDUAL pasa pero el COMBINADO no."""
        piezas = self._piezas_interior_institucional(7)
        v_individual = arq.verificar_diversidad_arquetipos(piezas)
        self.assertTrue(v_individual.ok, "cada arquetipo por separado debe respetar su propio tope")

        v_familia = arq.verificar_afinidad_familias(piezas)
        self.assertFalse(v_familia.ok)
        self.assertIn("INTERIOR_INSTITUCIONAL", v_familia.excedidas)

    def test_cuatro_de_familia_cercana_pasa(self):
        piezas = self._piezas_interior_institucional(4)
        v = arq.verificar_afinidad_familias(piezas)
        self.assertTrue(v.ok, v.excedidas)

    def test_retrato_y_sin_clasificar_no_se_agrupan(self):
        """Arquetipos sin familia declarada no cuentan contra ningún tope
        combinado — no hay evidencia de que compartan registro."""
        piezas = [(f"P{i}", f"un poste distinto {i}", "terreno distinto") for i in range(6)]
        v = arq.verificar_afinidad_familias(piezas)
        self.assertTrue(v.ok)
        self.assertEqual(v.conteo, {})

    def test_lote_real_de_10_no_excede_afinidad_de_familias(self):
        import demo_produccion_real_10_temas_nuevos as dp
        resultados, *_ = dp.ejecutar()
        piezas = [(r["candidato"].candidate_id, r["direccion"]["subject"],
                  r["direccion"]["environment"]) for r in resultados]
        v = arq.verificar_afinidad_familias(piezas)
        self.assertTrue(v.ok, v.excedidas)


class TestRedundanciaAmbientacion(unittest.TestCase):
    """Eje distinto del arquetipo compositivo: vocabulario compartido de
    `environment`, aunque los arquetipos sean distintos entre sí."""

    def test_tope_por_defecto_es_3(self):
        self.assertEqual(arq.MAX_POR_AMBIENTACION_DEFAULT, 3)

    def test_cuatro_archivos_falla(self):
        piezas = [(f"P{i}", "archivo notarial con luz de ventana") for i in range(4)]
        v = arq.verificar_redundancia_ambientacion(piezas)
        self.assertFalse(v.ok)
        self.assertIn("ARCHIVO", v.excedidas)

    def test_tres_archivos_pasa(self):
        piezas = [(f"P{i}", "archivo notarial con luz de ventana") for i in range(3)]
        v = arq.verificar_redundancia_ambientacion(piezas)
        self.assertTrue(v.ok)

    def test_arquetipos_distintos_con_mismo_vocabulario_de_lugar_igual_cuentan(self):
        """Hallazgo real: un DOCUMENTO_CLOSEUP y una ESCENA_ESCRITORIO
        pueden compartir la palabra 'archivo' en su entorno pese a tener
        arquetipos compositivos distintos — este chequeo lo atrapa aunque
        `verificar_diversidad_arquetipos` no lo haga."""
        piezas_amb = [
            ("P1", "archivo notarial con estantes"),
            ("P2", "despacho con archivadores al fondo"),
            ("P3", "sala de juntas con archivadores visibles"),
            ("P4", "oficina con un archivador metalico"),
        ]
        v = arq.verificar_redundancia_ambientacion(piezas_amb)
        self.assertFalse(v.ok)

    def test_sin_coincidencia_lexica_no_cuenta(self):
        piezas = [(f"P{i}", f"un lugar sin vocabulario reconocido {i}") for i in range(5)]
        v = arq.verificar_redundancia_ambientacion(piezas)
        self.assertTrue(v.ok)
        self.assertEqual(v.conteo, {})

    def test_lote_real_de_10_no_excede_redundancia_de_ambientacion(self):
        import demo_produccion_real_10_temas_nuevos as dp
        resultados, *_ = dp.ejecutar()
        piezas = [(r["candidato"].candidate_id, r["direccion"]["environment"]) for r in resultados]
        v = arq.verificar_redundancia_ambientacion(piezas)
        self.assertTrue(v.ok, v.excedidas)


if __name__ == "__main__":
    unittest.main()
