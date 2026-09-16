"""compile_request — Fases 8-10 del mandato "Súper Prompt" (16-sep-2026).

Fase 8: el prompt YA NO fuerza "azul petroleo" en cada pieza ni imprime la
paleta de marca como obligación de escena. Fase 10: cuando se aporta una
huella visual (visual_fingerprint.py), sus 10 dimensiones deben llegar
verificablemente al prompt final — no basta con que el metadata las
transporte si el texto que el proveedor recibe no cambia."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import visual_fingerprint as vf  # noqa: E402
from brief import VisualPolicy  # noqa: E402
from compiler import compile_request  # noqa: E402
from test_visual_pipeline import make_brief  # noqa: E402

POLICY = VisualPolicy.load()
CATALOGO = vf.MasterCatalog.load()


def _huella(content_id="HUELLA-TEST-001", **kw):
    memoria = vf.FingerprintMemory()
    return vf.seleccionar_huella(content_id, catalogo=CATALOGO, memoria=memoria, **kw)


class TestSinDefaultForzado(unittest.TestCase):
    """Hallazgo 1/2 de la auditoría: nada hardcodea 'azul petroleo' ni una
    paleta de marca obligatoria en cada pieza."""

    def test_ya_no_existe_la_frase_hardcodeada_de_acento_azul(self):
        # la marca_de_referencia puede seguir citando azul_petroleo como UNA
        # de sus 4 referencias (es un color de marca legitimo) -- lo que ya
        # no existe es la frase vieja que lo imponia como EL UNICO acento,
        # incondicional, en cada pieza sin excepcion.
        req = compile_request(make_brief(), POLICY)
        self.assertNotIn("el acento azul petroleo debe proceder", req.positive_prompt.lower())

    def test_paleta_de_marca_ya_no_es_obligatoria_sin_huella(self):
        # sin huella, la paleta cae a la de marca como referencia -- pero ya
        # no es la unica fuente posible, y el flag de politica que la forzaba
        # (paleta.requerida) ya no existe con ese nombre/semantica.
        self.assertNotIn("requerida", POLICY.data.get("paleta", {}))
        self.assertIn("marca_de_referencia", POLICY.data.get("paleta", {}))

    def test_acento_objeto_presente_produce_la_frase_de_acento(self):
        req = compile_request(make_brief(acento_objeto="algo"), POLICY)
        self.assertIn("El acento de color", req.positive_prompt)


class TestHuellaLlegaAlPromptFinal(unittest.TestCase):
    """Fase 10: verificacion explicita de que cambiar la huella cambia el
    prompt compilado de forma sustantiva, no solo el metadata."""

    def test_primary_direction_aparece_literalmente_en_el_prompt(self):
        h = _huella("LIT-001")
        req = compile_request(make_brief(), POLICY, fingerprint=h)
        self.assertIn(h.primary_direction, req.positive_prompt)

    def test_medium_lighting_composition_aparecen_en_el_prompt(self):
        h = _huella("LIT-002")
        req = compile_request(make_brief(), POLICY, fingerprint=h)
        self.assertIn(h.medium.replace("_", " "), req.positive_prompt)
        self.assertIn(h.lighting, req.positive_prompt)
        self.assertIn(h.composition, req.positive_prompt)

    def test_palette_de_la_huella_reemplaza_la_paleta_de_marca(self):
        h = _huella("LIT-003")
        # acento_objeto neutro: sin palabras de marca, para que la unica
        # fuente posible de esos tokens en el prompt sea la paleta forzada
        # (que ya no debe imprimirse cuando hay huella), no un dato de brief.
        req = compile_request(make_brief(acento_objeto="un pisapapeles de piedra"), POLICY, fingerprint=h)
        self.assertIn(h.palette, req.positive_prompt)
        # las 4 marcas de referencia de POLITICA no deben imprimirse cuando
        # hay huella -- la paleta real es la de la huella, no la de marca.
        for token in POLICY.data["paleta"]["marca_de_referencia"]:
            self.assertNotIn(token.replace("_", " "), req.positive_prompt)

    def test_dos_huellas_distintas_producen_prompts_distintos(self):
        h_a = _huella("DIFF-A")
        h_b = _huella("DIFF-B")
        req_a = compile_request(make_brief(), POLICY, fingerprint=h_a)
        req_b = compile_request(make_brief(), POLICY, fingerprint=h_b)
        self.assertNotEqual(req_a.positive_prompt, req_b.positive_prompt)
        self.assertNotEqual(req_a.metadata["prompt_sha256"], req_b.metadata["prompt_sha256"])

    def test_misma_huella_mismo_brief_produce_el_mismo_prompt(self):
        h = _huella("STABLE-001")
        req_a = compile_request(make_brief(), POLICY, fingerprint=h)
        req_b = compile_request(make_brief(), POLICY, fingerprint=h)
        self.assertEqual(req_a.positive_prompt, req_b.positive_prompt)

    def test_metadata_transporta_la_huella_completa(self):
        h = _huella("META-001")
        req = compile_request(make_brief(), POLICY, fingerprint=h)
        self.assertEqual(req.metadata["visual_fingerprint"]["primary_direction"], h.primary_direction)
        self.assertEqual(req.metadata["visual_fingerprint"]["content_id"], h.content_id)

    def test_composition_intent_incluye_la_composicion_de_la_huella(self):
        h = _huella("COMP-001")
        req = compile_request(make_brief(), POLICY, fingerprint=h)
        self.assertIn(h.composition, req.composition_intent)

    def test_sin_huella_el_comportamiento_anterior_se_mantiene(self):
        # backward-compat explicito: fingerprint=None (el default) no rompe
        # nada de lo que ya dependia de compile_request.
        req = compile_request(make_brief(), POLICY)
        self.assertTrue(req.positive_prompt)
        self.assertNotIn("visual_fingerprint", req.metadata)


if __name__ == "__main__":
    unittest.main()
