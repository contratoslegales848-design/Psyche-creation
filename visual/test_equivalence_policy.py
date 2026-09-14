"""Política de dos niveles del Founder (2026-09-14) — PROPUESTA, no activada."""

import inspect
import unittest

import equivalence_policy as ep
import semantic_memory
from semantic_fingerprint import SemanticFingerprint


def fp(**kw):
    base = dict(content_id="x", materia="civil", submateria="obligaciones",
                concepto_nucleo="firma como manifestacion de consentimiento",
                relacion="acto formal frente a voluntad real", familia_editorial="mito",
                necesidad="distinguir", pregunta_resuelta="basta firmar para consentir",
                angulo="contrastivo", contexto_funcional="antes_de_firmar",
                rol_lector="persona", hook="hook")
    base.update(kw)
    return SemanticFingerprint(**base)


class TestNoActivada(unittest.TestCase):
    def test_semantic_memory_no_importa_ni_llama_la_politica_nueva(self):
        """Invariante explícita del mandato: 'PROPONER cutoff. NO activarlo
        automáticamente.' semantic_memory.evaluar() debe seguir usando
        equivalente_a(), nunca nivel_equivalencia()."""
        fuente_modulo = inspect.getsource(semantic_memory)
        self.assertNotIn("equivalence_policy", fuente_modulo)
        self.assertNotIn("nivel_equivalencia", fuente_modulo)

    def test_generator_no_llama_la_politica_nueva(self):
        import generator
        fuente = inspect.getsource(generator)
        self.assertNotIn("equivalence_policy", fuente)

    def test_el_modulo_se_declara_propuesta(self):
        doc = ep.__doc__ or ""
        self.assertIn("PROPUESTA", doc)
        self.assertIn("NO ACTIVADA", doc)


class TestBloqueo(unittest.TestCase):
    def test_par_identico_salvo_hook_bloquea(self):
        a = fp(content_id="a", hook="Firmar no siempre significa consentir")
        b = fp(content_id="b", hook="Una firma no sustituye un consentimiento válido")
        v = ep.nivel_equivalencia(a, b)
        self.assertEqual(v.nivel, ep.BLOQUEO)
        self.assertTrue(v.bloquea)
        self.assertFalse(v.requiere_revision_humana)
        self.assertEqual(set(v.campos_corroborados), set(ep.CAMPOS_CORROBORACION))

    def test_bloqueo_exige_distancia_bajo_el_minimo_y_los_tres_campos(self):
        a = fp(content_id="a")
        b = fp(content_id="b", concepto_nucleo="algo completamente distinto y sin relación")
        v = ep.nivel_equivalencia(a, b)
        self.assertNotEqual(v.nivel, ep.BLOQUEO)


class TestAlertaDeProximidad(unittest.TestCase):
    def test_distancia_baja_sin_corroboracion_completa_es_alerta_no_bloqueo(self):
        """El núcleo de la decisión del Founder: una distancia agregada baja
        NUNCA basta sola para bloquear."""
        a = fp(content_id="a")
        b = fp(content_id="b", pregunta_resuelta="una pregunta claramente distinta y no relacionada")
        v = ep.nivel_equivalencia(a, b)
        self.assertIn(v.nivel, (ep.ALERTA_DE_PROXIMIDAD, ep.NO_RELACIONADO))
        self.assertNotEqual(v.nivel, ep.BLOQUEO)

    def test_zona_de_alerta_por_rango_de_distancia(self):
        """Fabrica un veredicto directamente en el rango [0.28, 0.40] variando
        alerta_minimo/alerta_maximo alrededor de una distancia real conocida,
        sin depender de qué combinación exacta de campos la produce."""
        a = fp(content_id="a")
        b = fp(content_id="b", relacion="otra relación jurídica distinta")
        d = a.distancia_semantica(b)
        if not d.comparable:
            self.skipTest("par sin evidencia comparable en este fixture")
        v = ep.nivel_equivalencia(a, b, alerta_minimo=d.valor - 0.01, alerta_maximo=d.valor + 0.01)
        self.assertEqual(v.nivel, ep.ALERTA_DE_PROXIMIDAD)
        self.assertTrue(v.requiere_revision_humana)
        self.assertFalse(v.bloquea)

    def test_alerta_nunca_descarta_automaticamente(self):
        """requiere_revision_humana es cierto exactamente cuando nivel es
        ALERTA_DE_PROXIMIDAD — nunca se auto-resuelve en bloqueo ni en paso."""
        a = fp(content_id="a")
        b = fp(content_id="b", relacion="otra relación jurídica distinta")
        d = a.distancia_semantica(b)
        if not d.comparable:
            self.skipTest("par sin evidencia comparable en este fixture")
        v = ep.nivel_equivalencia(a, b, alerta_minimo=d.valor - 0.01, alerta_maximo=d.valor + 0.01)
        self.assertEqual(v.requiere_revision_humana, v.nivel == ep.ALERTA_DE_PROXIMIDAD)


class TestNoRelacionado(unittest.TestCase):
    def test_sin_ningun_eje_en_comun_es_no_relacionado(self):
        a = SemanticFingerprint(content_id="a")
        b = SemanticFingerprint(content_id="b")
        v = ep.nivel_equivalencia(a, b)
        self.assertEqual(v.nivel, ep.NO_RELACIONADO)
        self.assertFalse(v.comparable)
        self.assertFalse(v.bloquea)
        self.assertFalse(v.requiere_revision_humana)

    def test_distinta_materia_con_distancia_maxima_es_no_relacionado(self):
        a = SemanticFingerprint(content_id="a", materia="civil", submateria="obligaciones")
        b = SemanticFingerprint(content_id="b", materia="penal", submateria="otra")
        v = ep.nivel_equivalencia(a, b)
        self.assertEqual(v.nivel, ep.NO_RELACIONADO)
        self.assertEqual(v.distancia, 1.0)
        self.assertFalse(v.bloquea)
        self.assertFalse(v.requiere_revision_humana)

    def test_distancia_por_encima_del_maximo_es_no_relacionado(self):
        a = fp(content_id="a")
        b = fp(content_id="b", materia="penal", submateria="delitos",
              concepto_nucleo="tipicidad penal", relacion="conducta y sanción",
              pregunta_resuelta="cuándo hay delito", angulo="explicativo",
              contexto_funcional="proceso_penal")
        v = ep.nivel_equivalencia(a, b, alerta_minimo=0.05, alerta_maximo=0.10)
        self.assertEqual(v.nivel, ep.NO_RELACIONADO)


class TestVerdictoToDict(unittest.TestCase):
    def test_to_dict_expone_los_campos_clave(self):
        a = fp(content_id="a")
        b = fp(content_id="b")
        d = ep.nivel_equivalencia(a, b).to_dict()
        for clave in ("nivel", "distancia", "comparable", "bloquea",
                     "requiere_revision_humana", "campos_corroborados",
                     "campos_sin_corroborar", "razon"):
            self.assertIn(clave, d)


if __name__ == "__main__":
    unittest.main()
