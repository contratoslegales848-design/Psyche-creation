"""Conjunto de calibración positiva sintética (Founder, 2026-09-14) — Pasos 1 y 2."""

import unittest

import calibration_positive_set as cps


class TestCargaDeSemillas(unittest.TestCase):
    def test_carga_ocho_semillas(self):
        semillas, aviso = cps.cargar_semillas()
        self.assertEqual(len(semillas), 8)
        self.assertTrue(aviso)

    def test_cada_semilla_trae_los_campos_nucleo(self):
        semillas, _ = cps.cargar_semillas()
        for s in semillas:
            for campo in ("id", "materia", "submateria", "necesidad", "rol_lector",
                         "angulo", "contexto_funcional", "concepto_nucleo",
                         "pregunta_resuelta", "relacion", "texto_a", "texto_b"):
                self.assertIn(campo, s, s.get("id"))
                self.assertTrue(str(s[campo]).strip(), f"{s.get('id')}.{campo} vacío")

    def test_ids_unicos(self):
        semillas, _ = cps.cargar_semillas()
        ids = [s["id"] for s in semillas]
        self.assertEqual(len(ids), len(set(ids)))

    def test_texto_a_y_texto_b_difieren_en_cada_semilla(self):
        """El propio hook YA es la mutación mínima — si coincidieran, no
        habría nada que distinga base de mutado en 'solo_hook'."""
        semillas, _ = cps.cargar_semillas()
        for s in semillas:
            self.assertNotEqual(s["texto_a"], s["texto_b"], s["id"])

    def test_rechaza_un_conjunto_sin_la_marca_synthetic(self):
        import json
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "bad.json"
            p.write_text(json.dumps({"estado": "CORPUS_REAL", "semillas": []}), encoding="utf-8")
            with self.assertRaises(ValueError):
                cps.cargar_semillas(path=p)


class TestGeneracionDePares(unittest.TestCase):
    def test_genera_32_pares_8_semillas_por_4_mutaciones(self):
        pares = cps.generar_pares()
        self.assertEqual(len(pares), 8 * len(cps.MUTACIONES))

    def test_cada_semilla_tiene_las_cuatro_mutaciones(self):
        pares = cps.generar_pares()
        por_semilla = {}
        for p in pares:
            por_semilla.setdefault(p.semilla_id, set()).add(p.mutacion)
        for semilla_id, mutaciones in por_semilla.items():
            self.assertEqual(mutaciones, set(cps.MUTACIONES), semilla_id)

    def test_el_nucleo_semantico_nunca_cambia_entre_base_y_mutado(self):
        """Las mutaciones tocan SÓLO capas expresivas/visuales — nunca
        concepto_nucleo/pregunta_resuelta/relacion, el contrato mismo que
        hace que la prueba de contaminación tenga sentido."""
        pares = cps.generar_pares()
        for p in pares:
            self.assertEqual(p.base.concepto_nucleo, p.mutado.concepto_nucleo, p.semilla_id)
            self.assertEqual(p.base.pregunta_resuelta, p.mutado.pregunta_resuelta, p.semilla_id)
            self.assertEqual(p.base.relacion, p.mutado.relacion, p.semilla_id)

    def test_mutacion_total_realmente_cambia_las_capas_expresivas(self):
        pares = [p for p in cps.generar_pares() if p.mutacion == "mutacion_total_expresiva_y_visual"]
        for p in pares:
            for campo, valor in cps.MUTACIONES["mutacion_total_expresiva_y_visual"].items():
                self.assertEqual(getattr(p.mutado, campo), valor, (p.semilla_id, campo))

    def test_par_to_dict(self):
        p = cps.generar_pares()[0]
        d = p.to_dict()
        for clave in ("semilla_id", "mutacion", "base", "mutado"):
            self.assertIn(clave, d)


class TestPruebaDeContaminacion(unittest.TestCase):
    """Regresión: al momento de escribir este archivo, 0/32 pares estaban
    contaminados en las cuatro mutaciones, incluida la mutación total
    expresiva y visual. Si esta prueba empieza a fallar, la memoria
    semántica dejó de ser inmune a cambios puramente expresivos/visuales —
    exactamente lo que este conjunto existe para vigilar."""

    @classmethod
    def setUpClass(cls):
        cls.resultados = cps.prueba_de_contaminacion()
        cls.resumen = cps.resumen_contaminacion(cls.resultados)

    def test_ningun_par_esta_contaminado(self):
        self.assertEqual(self.resumen["contaminados"], 0, self.resumen["detalle_contaminados"])
        self.assertTrue(self.resumen["limpio"])

    def test_se_evaluaron_los_32_pares(self):
        self.assertEqual(self.resumen["total"], 32)

    def test_las_cuatro_mutaciones_estan_representadas_en_el_resumen(self):
        self.assertEqual(set(self.resumen["por_mutacion"]), set(cps.MUTACIONES))
        for m, datos in self.resumen["por_mutacion"].items():
            self.assertEqual(datos["total"], 8, m)
            self.assertEqual(datos["contaminados"], 0, m)

    def test_resultado_individual_declara_equivalencia_y_distancia(self):
        r = self.resultados[0]
        self.assertTrue(r.equivalente)
        self.assertFalse(r.contaminado)
        self.assertIsNotNone(r.distancia)

    def test_es_determinista(self):
        otro = cps.resumen_contaminacion(cps.prueba_de_contaminacion())
        self.assertEqual(otro, self.resumen)


if __name__ == "__main__":
    unittest.main()
