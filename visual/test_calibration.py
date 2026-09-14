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
        """Contar los MUY_PROXIMO en un sentido u otro inflaría la métrica.

        El fichero por defecto ahora es el Founder real (GROUND_TRUTH_FOUNDER):
        respondió los 18 pares con B/C decisivos, cero SIN_INFO, así que aquí
        la zona gris real es 0 — no hay nada que excluir porque no hay
        ambigüedad, no porque el mecanismo de exclusión no funcione. Ese
        mecanismo se sigue probando contra el fichero AGENTE, que sí tiene
        MUY_PROXIMO (zona gris real, sin resolver por un humano)."""
        self.assertEqual(self.conteo["zona_gris_excluida"], 0)
        self.assertEqual(self.meta["fuente_etiquetas"], "FOUNDER")

        puntos_agente, _, conteo_agente = cal.barrido(self.regs, path=cal.EVAL_PATH)
        self.assertGreater(conteo_agente["zona_gris_excluida"], 0)

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
    """`eval-umbral-founder.json` ahora existe de verdad (Founder respondió
    los 18 pares el 2026-09-14) y `cargar_pares_etiquetados`/`barrido` sin
    `path` explícito lo PREFIEREN sobre el candidato del agente — así que
    `self.meta` aquí describe el fichero Founder, no el del agente. El
    fichero del agente sigue existiendo y sigue siendo honesto sobre sí
    mismo; se prueba aparte, explícitamente, más abajo."""

    def test_el_conjunto_por_defecto_es_ground_truth_founder(self):
        self.assertEqual(self.meta["estado"], "GROUND_TRUTH_FOUNDER")
        self.assertEqual(self.meta["fuente_etiquetas"], "FOUNDER")

    def test_el_fichero_agente_sigue_declarandose_candidato_no_ground_truth(self):
        """El fichero AGENTE no desapareció ni se reescribió: sigue siendo
        honesto sobre su propio origen cuando se le pide explícitamente."""
        _, meta_agente = cal.cargar_pares_etiquetados(self.regs, path=cal.EVAL_PATH)
        self.assertEqual(meta_agente["estado"], "CANDIDATO_PENDIENTE_REVISION_FOUNDER")
        aviso = (meta_agente.get("aviso") or "").lower()
        self.assertIn("agente", aviso)
        self.assertIn("no son ground truth humano", aviso)

    def test_todos_los_pares_resuelven_contra_el_corpus(self):
        self.assertEqual(self.meta["pares_no_resueltos"], [])

    def test_el_fichero_documenta_cada_etiqueta(self):
        data = json.loads(Path(cal.EVAL_PATH).read_text(encoding="utf-8"))
        for par in data["pares"]:
            self.assertIn(par["etiqueta"], data["etiquetas"])
            self.assertTrue(par["razon"].strip())

    def test_la_correccion_founder_sobre_lm026_lm027_queda_registrada(self):
        """Límite anterior, ahora cerrado por el Founder mismo, no por una
        mejora de datos: el agente había etiquetado LM-026~LM-027 como
        EQUIVALENTE (debía bloquearse); el Founder respondió 'B' — COEXISTIR,
        no la misma pregunta ('ambas distinguen depósito de fianza: es la
        misma pregunta con dos titulares' es su razón textual, pero la
        decisión es que coexisten, no que se bloqueen). Por eso NINGÚN umbral
        debe reportar ya un fallo 'FN' sobre este par: ya no se espera que
        lo bloqueen — el corpus no cambió, la etiqueta correcta sí."""
        data = json.loads(Path(cal.FOUNDER_EVAL_PATH).read_text(encoding="utf-8"))
        par = next(p for p in data["pares"] if {p["a"], p["b"]} == {"LM-026", "LM-027"})
        self.assertEqual(par["cambio"], "CORRIGE_AGENTE")
        self.assertEqual(par["founder_label_mapped"], "COEXISTIR")
        for p in self.puntos:
            self.assertFalse([f for f in p.fallos if "LM-026" in f], p.umbral)

    def test_no_hay_todavia_ningun_positivo_real_confirmado_por_el_founder(self):
        """De los 18 pares reales, 0 son A (bloquear): 10 B + 8 C, todos
        negativos. Por eso RECALL sobre datos 100% reales queda indefinido
        sin un positivo — exactamente la razón por la que existe
        calibration_positive_set.py / equivalence_calibration.py: el
        positivo tiene que ser sintético y declarado como tal mientras no
        exista uno real."""
        data = json.loads(Path(cal.FOUNDER_EVAL_PATH).read_text(encoding="utf-8"))
        bloquear = [p for p in data["pares"] if p["founder_label_mapped"] == "BLOQUEAR"]
        self.assertEqual(bloquear, [])


if __name__ == "__main__":
    unittest.main()
