"""Reglas de lote de 10 sobre el visual_fingerprint — Fases 6-7 del mandato
"Súper Prompt" (16-sep-2026). Cada test de "detecta X" construye a mano un
lote que viola exactamente una regla, para probar que evaluar_lote_visual
la atrapa — no basta con que un lote real generado pase, porque eso no
prueba que la regla exista."""

import unittest

import visual_fingerprint as vf
import visual_fingerprint_batch as vfb


def _huella(cid, primary="óleo narrativo", medium="pintura_y_tecnicas_pictoricas",
           secondary="", lighting="luz natural difusa", composition="regla de tercios",
           camera_optics="35mm", palette="ciruela y gris humo", materiality="lienzo",
           realism="fotorrealista", visual_mechanism="metafora visual directa"):
    return vf.VisualFingerprint(
        content_id=cid, primary_direction=primary, secondary_direction=secondary,
        medium=medium, lighting=lighting, composition=composition,
        camera_optics=camera_optics, palette=palette, materiality=materiality,
        realism=realism, visual_mechanism=visual_mechanism)


class TestLoteRealGenerado(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalogo = vf.MasterCatalog.load()

    def test_lote_generado_converge_y_es_aceptado(self):
        ids = [f"REAL-{i:03d}" for i in range(10)]
        lote, reporte, intentos = vfb.generar_lote_visual(ids, catalogo=self.catalogo, canal="ig")
        self.assertTrue(reporte.aceptado, reporte.incumplimientos)
        self.assertEqual(len(lote), 10)
        self.assertLessEqual(intentos, vfb.MAX_INTENTOS_LOTE)

    def test_lote_generado_respeta_memoria_previa_real(self):
        memoria_previa = vf.FingerprintMemory()
        semilla = vf.seleccionar_huella("PUBLICADA-001", catalogo=self.catalogo, memoria=vf.FingerprintMemory())
        memoria_previa.record("PUBLICADA-001", semilla, canal="ig")
        ids = [f"NUEVO-{i:03d}" for i in range(10)]
        lote, reporte, _ = vfb.generar_lote_visual(
            ids, catalogo=self.catalogo, memoria_previa=memoria_previa, canal="ig")
        self.assertTrue(reporte.aceptado, reporte.incumplimientos)
        # la primera pieza del lote nuevo no puede ser idéntica a la ya publicada
        distintas, conocidas = vf.distancia(lote[0], semilla)
        if conocidas >= len(vf.DIMENSIONES_HUELLA):
            self.assertGreaterEqual(distintas, vf.MIN_DIMENSIONES_DIFERENTES_CONSECUTIVAS)


class TestReglasIndividualesDelLote(unittest.TestCase):
    def test_lote_vacio_se_rechaza(self):
        reporte = vfb.evaluar_lote_visual([])
        self.assertFalse(reporte.aceptado)
        self.assertEqual(reporte.total, 0)

    def test_detecta_huellas_no_distintas(self):
        # 10 piezas, pero 5 son copias idénticas de la primera -> menos de 7 distintas.
        base = _huella("A")
        lote = [base] + [_huella(f"DUP-{i}") for i in range(4)] + \
               [_huella(f"X-{i}", primary=f"estilo-{i}", medium="fotografia") for i in range(5)]
        reporte = vfb.evaluar_lote_visual(lote)
        self.assertFalse(reporte.aceptado)
        self.assertTrue(any("distintas" in m for m in reporte.incumplimientos))

    def test_detecta_pocos_medios_distintos(self):
        # 10 piezas, todas del mismo medium -> 1 medio, mínimo real es 5.
        lote = [_huella(f"M-{i}", primary=f"estilo-{i}") for i in range(10)]
        reporte = vfb.evaluar_lote_visual(lote)
        self.assertFalse(reporte.aceptado)
        self.assertTrue(any("medios/familias distintos" in m for m in reporte.incumplimientos))

    def test_detecta_sobreexplotacion_de_un_medio(self):
        medios = (["pintura_y_tecnicas_pictoricas"] * 3 + ["fotografia"] * 2 +
                  ["escultura_objeto_y_material"] * 2 + ["dibujo_grabado_y_estampa"] * 1 +
                  ["arquitectura_espacio_y_escenografia"] * 1 + ["digital_cgi_y_visualizacion"] * 1)
        lote = [_huella(f"OV-{i}", primary=f"estilo-{i}", medium=medios[i]) for i in range(10)]
        reporte = vfb.evaluar_lote_visual(lote)
        self.assertFalse(reporte.aceptado)
        self.assertTrue(any("sobreexplotación" in m for m in reporte.incumplimientos))

    def test_detecta_repeticion_consecutiva_de_primary_direction(self):
        medios = ["fotografia", "pintura_y_tecnicas_pictoricas", "escultura_objeto_y_material",
                 "dibujo_grabado_y_estampa", "arquitectura_espacio_y_escenografia",
                 "digital_cgi_y_visualizacion", "movimientos_y_lenguajes_historicos"]
        lote = [
            _huella("REP-0", primary="mismo estilo", medium=medios[0], lighting="l0", composition="c0", palette="p0"),
            _huella("REP-1", primary="mismo estilo", medium=medios[1], lighting="l1", composition="c1", palette="p1"),
        ]
        for i, m in enumerate(medios[2:], start=2):
            lote.append(_huella(f"REP-{i}", primary=f"estilo-{i}", medium=m,
                                lighting=f"l{i}", composition=f"c{i}", palette=f"p{i}"))
        reporte = vfb.evaluar_lote_visual(lote)
        self.assertFalse(reporte.aceptado)
        self.assertTrue(any("primary_direction" in m and "REP-0" in m and "REP-1" in m
                            for m in reporte.incumplimientos))

    def test_detecta_distancia_insuficiente_vs_pieza_anterior(self):
        medios = ["fotografia", "pintura_y_tecnicas_pictoricas", "escultura_objeto_y_material",
                 "dibujo_grabado_y_estampa", "arquitectura_espacio_y_escenografia",
                 "digital_cgi_y_visualizacion", "movimientos_y_lenguajes_historicos"]
        # REP-0 y REP-1 difieren solo en primary_direction y medium (2 dimensiones) -> < 4.
        # secondary_direction se rellena en ambas para que las 10 dimensiones cuenten
        # como "conocidas" (mismo criterio fail-closed que distancia()/seleccionar_huella).
        lote = [
            _huella("VEC-0", primary="estilo-A", medium=medios[0], secondary="misma-secundaria",
                    lighting="misma-luz", composition="misma-comp", palette="misma-paleta",
                    camera_optics="mismo-lente", materiality="misma-material",
                    realism="mismo-realismo", visual_mechanism="mismo-mecanismo"),
            _huella("VEC-1", primary="estilo-B", medium=medios[1], secondary="misma-secundaria",
                    lighting="misma-luz", composition="misma-comp", palette="misma-paleta",
                    camera_optics="mismo-lente", materiality="misma-material",
                    realism="mismo-realismo", visual_mechanism="mismo-mecanismo"),
        ]
        for i, m in enumerate(medios[2:], start=2):
            lote.append(_huella(f"VEC-{i}", primary=f"estilo-{i}", medium=m,
                                lighting=f"l{i}", composition=f"c{i}", palette=f"p{i}"))
        reporte = vfb.evaluar_lote_visual(lote)
        self.assertFalse(reporte.aceptado)
        self.assertTrue(any("VEC-0" in m and "VEC-1" in m and "dimensiones distintas" in m
                            for m in reporte.incumplimientos))

    def test_lote_incompleto_se_rechaza(self):
        medios = ["fotografia", "pintura_y_tecnicas_pictoricas", "escultura_objeto_y_material",
                 "dibujo_grabado_y_estampa", "arquitectura_espacio_y_escenografia"]
        lote = [_huella(f"INC-{i}", primary=f"estilo-{i}", medium=medios[i],
                        lighting=f"l{i}", composition=f"c{i}", palette=f"p{i}")
               for i in range(5)]
        reporte = vfb.evaluar_lote_visual(lote, objetivo=10)
        self.assertFalse(reporte.aceptado)
        self.assertTrue(any("incompleto" in m for m in reporte.incumplimientos))


if __name__ == "__main__":
    unittest.main()
