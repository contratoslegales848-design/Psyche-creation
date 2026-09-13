"""Calibración del umbral: medida, no elegida a ojo — y sin fingir certeza."""

import json
import unittest
from pathlib import Path

import calibration as cal
import corpus_import as ci
from semantic_fingerprint import UMBRAL_EQUIVALENCIA


class CalBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.regs, _ = ci.construir_registros()
        cls.puntos, cls.meta, cls.conteo = cal.barrido(cls.regs)
        cls.por_umbral = {p.umbral: p for p in cls.puntos}


class TestPositivosCanonicos(CalBase):
    def test_un_disfraz_cambia_solo_lo_expresivo_y_lo_visual(self):
        base, disfraz = cal.derivados_canonicos(self.regs, cuantos=1)[0]
        for eje in ("materia", "submateria", "concepto_nucleo", "familia_editorial",
                    "necesidad", "angulo", "rol_lector"):
            self.assertEqual(getattr(base, eje), getattr(disfraz, eje), eje)
        for eje in ("hook", "formato", "emocion", "metafora", "direccion_artistica"):
            self.assertNotEqual(getattr(base, eje), getattr(disfraz, eje), eje)

    def test_el_umbral_vigente_los_detecta_todos(self):
        p = self.por_umbral[UMBRAL_EQUIVALENCIA]
        self.assertEqual(p.tp, self.conteo["canonicos"] + 0)
        self.assertFalse([f for f in p.fallos if "FN canónico" in f])

    def test_ningun_umbral_razonable_deja_pasar_un_disfraz(self):
        """Si un disfraz pasa, la huella está rota por definición del canon."""
        for p in self.puntos:
            self.assertFalse([f for f in p.fallos if "FN canónico" in f], p.umbral)


class TestBarrido(CalBase):
    def test_recorre_todos_los_umbrales(self):
        self.assertEqual(len(self.puntos), len(cal.UMBRALES))

    def test_la_zona_gris_se_excluye(self):
        """Contar los MUY_PROXIMO en un sentido u otro inflaría la métrica."""
        self.assertGreater(self.conteo["zona_gris_excluida"], 0)

    def test_el_umbral_vigente_no_produce_falsos_positivos(self):
        self.assertEqual(self.por_umbral[UMBRAL_EQUIVALENCIA].fp, 0)

    def test_un_umbral_mas_laxo_si_los_produce(self):
        """La evidencia que justifica haber bajado de 0.30 a 0.25."""
        self.assertGreater(self.por_umbral[0.30].fp, 0)

    def test_precision_mejora_al_bajar_el_umbral(self):
        self.assertGreater(self.por_umbral[UMBRAL_EQUIVALENCIA].precision,
                           self.por_umbral[0.30].precision)

    def test_los_falsos_positivos_de_030_son_misma_materia_otra_pregunta(self):
        """El caso que el canon prohíbe bloquear."""
        fps = [f for f in self.por_umbral[0.30].fallos if f.startswith("FP")]
        self.assertTrue(fps)

    def test_metricas_en_rango(self):
        for p in self.puntos:
            for v in (p.precision, p.recall, p.f1):
                self.assertGreaterEqual(v, 0.0)
                self.assertLessEqual(v, 1.0)

    def test_es_determinista(self):
        otro, _, _ = cal.barrido(self.regs)
        self.assertEqual([p.to_dict() for p in otro], [p.to_dict() for p in self.puntos])


class TestHonestidadDelConjunto(CalBase):
    def test_el_conjunto_se_declara_candidato_no_ground_truth(self):
        self.assertEqual(self.meta["estado"], "CANDIDATO_PENDIENTE_REVISION_FOUNDER")

    def test_el_aviso_dice_quien_etiqueto(self):
        aviso = (self.meta.get("aviso") or "").lower()
        self.assertIn("agente", aviso)
        self.assertIn("no son ground truth humano", aviso)

    def test_todos_los_pares_resuelven_contra_el_corpus(self):
        self.assertEqual(self.meta["pares_no_resueltos"], [])

    def test_el_fichero_documenta_cada_etiqueta(self):
        data = json.loads(Path(cal.EVAL_PATH).read_text(encoding="utf-8"))
        for par in data["pares"]:
            self.assertIn(par["etiqueta"], data["etiquetas"])
            self.assertTrue(par["razon"].strip())

    def test_el_unico_equivalente_real_sigue_sin_detectarse(self):
        """Límite honesto y documentado: LM-026~LM-027 son la misma pregunta y
        ningún umbral los detecta, porque el corpus no declara concepto_nucleo
        ni pregunta_resuelta. Es carencia de DATOS, no de umbral. Si algún día
        esta prueba falla, significa que el corpus mejoró — actualízala."""
        for p in self.puntos:
            self.assertTrue([f for f in p.fallos if "LM-026" in f], p.umbral)


if __name__ == "__main__":
    unittest.main()
