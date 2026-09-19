"""Distancia visual estricta: 8 dimensiones, mínimo 5 cambiadas, 3 vecinos
por ámbito. Fail-closed sobre evidencia incompleta."""

import unittest

import visual_distance as vd
from memory import VisualMemoryEntry as E


def entry(cid, **kw):
    base = dict(content_id=cid, generation_id=f"g-{cid}", visual_family="oleo_narrativo",
               scene_type="oficina", metaphor="llave", dominant_materials=["laton"],
               lighting_type="dura", human_presence="ninguna", camera_angle="cenital",
               shot_distance="medio", brand_surface="placa")
    base.update(kw)
    return E(**base)


class TestDistanciaEstricta(unittest.TestCase):
    def test_identicas_dan_cero_cambiadas_ocho_conocidas(self):
        a, b = entry("a"), entry("b")
        self.assertEqual(vd.distancia_estricta(a, b), (0, 8))

    def test_todo_distinto_da_ocho_cambiadas(self):
        a = entry("a")
        b = entry("b", visual_family="foto_impasto", scene_type="patio", metaphor="grieta",
                  dominant_materials=["piedra"], lighting_type="difusa",
                  human_presence="una persona", camera_angle="contrapicado",
                  shot_distance="general", brand_surface="vidrio")
        self.assertEqual(vd.distancia_estricta(a, b), (8, 8))

    def test_dato_ausente_en_un_lado_no_cuenta_como_conocido(self):
        a, b = entry("a"), entry("b", scene_type="")
        cambiadas, conocidas = vd.distancia_estricta(a, b)
        self.assertEqual(conocidas, 7)

    def test_material_compara_por_conjunto_no_por_orden(self):
        a = entry("a", dominant_materials=["laton", "vidrio"])
        b = entry("b", dominant_materials=["vidrio", "laton"])
        cambiadas, _ = vd.distancia_estricta(a, b)
        self.assertEqual(cambiadas, 0)

    def test_camara_y_encuadre_se_combinan_en_una_sola_dimension(self):
        """8 dimensiones, no 9: cámara+encuadre cuentan una vez, como en la
        rama de referencia (framing|composition)."""
        self.assertEqual(len(vd.DIMENSIONES), 8)


class TestVecinosMasCercanos(unittest.TestCase):
    def test_ordena_por_menos_cambios_primero(self):
        base = entry("base")
        casi = entry("casi", scene_type="patio")            # 1 dimension distinta
        lejos = entry("lejos", visual_family="foto_impasto", scene_type="patio",
                      metaphor="grieta", dominant_materials=["piedra"],
                      lighting_type="difusa", human_presence="una persona",
                      camera_angle="contrapicado", brand_surface="vidrio")
        vecinos = vd.vecinos_mas_cercanos(base, [lejos, casi], n=2)
        self.assertEqual(vecinos[0][1].content_id, "casi")

    def test_no_se_compara_consigo_misma(self):
        base = entry("base")
        vecinos = vd.vecinos_mas_cercanos(base, [base, entry("otra")])
        ids = [o.content_id for _, o in vecinos]
        self.assertNotIn("base", ids)


class TestVerificarLoteContraHistoria(unittest.TestCase):
    def test_lote_diverso_sin_problemas(self):
        a, b, c = (entry("a"),
                   entry("b", visual_family="foto_impasto", scene_type="patio", metaphor="grieta",
                        dominant_materials=["piedra"], lighting_type="difusa",
                        human_presence="una persona", camera_angle="contrapicado",
                        shot_distance="general", brand_surface="vidrio"),
                   entry("c", visual_family="claroscuro_de_museo", scene_type="taller",
                        metaphor="reloj", dominant_materials=["bronce"], lighting_type="tenue",
                        human_presence="silueta", camera_angle="picado", shot_distance="cercano",
                        brand_surface="madera"))
        v = vd.verificar_lote_contra_historia([a, b, c])
        self.assertTrue(v.ok, v.problemas)

    def test_detecta_casi_duplicado_dentro_del_lote(self):
        a, b = entry("a"), entry("b", scene_type="patio")   # sólo 1 dimensión distinta
        v = vd.verificar_lote_contra_historia([a, b])
        self.assertFalse(v.ok)
        self.assertTrue(any("LOTE" in p for p in v.problemas))

    def test_detecta_casi_duplicado_contra_la_historia(self):
        historica = entry("h")
        nueva = entry("n", scene_type="patio")               # sólo 1 dimensión distinta
        v = vd.verificar_lote_contra_historia([nueva], historia=[historica])
        self.assertFalse(v.ok)
        self.assertTrue(any("HISTORIA" in p for p in v.problemas))

    def test_evidencia_incompleta_falla_cerrado(self):
        """Menos de 8 dimensiones conocidas: nunca pasa por omisión."""
        a = entry("a")
        b = entry("b", scene_type="", metaphor="", lighting_type="")
        v = vd.verificar_lote_contra_historia([a, b])
        self.assertFalse(v.ok)
        self.assertTrue(any("evidencia visual incompleta" in p for p in v.problemas))

    def test_un_historial_grande_no_esconde_repeticion_del_lote(self):
        a, b = entry("a"), entry("b", scene_type="patio")
        historia_diversa = [entry(f"h{i}", visual_family="foto_impasto", scene_type=f"lugar{i}",
                                  metaphor=f"m{i}", dominant_materials=[f"mat{i}"],
                                  lighting_type="difusa", human_presence="varia",
                                  camera_angle="picado", brand_surface="vidrio")
                            for i in range(20)]
        v = vd.verificar_lote_contra_historia([a, b], historia=historia_diversa)
        self.assertFalse(v.ok)

    def test_es_determinista(self):
        a, b, c = entry("a"), entry("b", scene_type="patio"), entry("c", metaphor="grieta")
        v1 = vd.verificar_lote_contra_historia([a, b, c])
        v2 = vd.verificar_lote_contra_historia([a, b, c])
        self.assertEqual(v1.problemas, v2.problemas)


if __name__ == "__main__":
    unittest.main()
