"""El prompt tiene que reservar la banda donde caera el texto juridico.

El defecto que estas pruebas fijan. El plan tipografico se calculaba en el paso 8
del pipeline, DESPUES de generar la imagen, asi que el prompt nunca sabia donde
iba a caer la copia exacta. El generador colocaba objetos, luz y detalle
justamente ahi, y el texto acababa montado sobre una zona ocupada.

En la practica es la causa mas frecuente de "la imagen no salio bien": no es que
el arte sea malo, es que compite con el texto que tiene que sostener.

El campo `negative_space` ya existia en VisualBrief y `compiler.py` ya lo emitia
al prompt. Nadie lo rellenaba nunca: ni `brief_desde()`, ni el brief revisado por
un humano de GEN3. Estaba cableado a medias desde el principio.

Sin red. Determinista.
"""

import json
import sys
import unittest
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))

import canonical  # noqa: E402
import cli  # noqa: E402
import composition  # noqa: E402
import pipeline  # noqa: E402
from brief import VisualPolicy  # noqa: E402
from compositor import ReservedSurface  # noqa: E402
from families import VisualFamilyRegistry  # noqa: E402
from providers.fake import FakeImageProvider  # noqa: E402

REPO = AQUI.parent
SKILL = REPO / ".claude" / "skills" / "legalmente-legal-verification"


def _cargar():
    art = json.loads((REPO / "content" / "pieza-01-reales.json").read_text(encoding="utf-8"))
    ho = json.loads((SKILL / "publication" / "records" / "handoff-pieza-01-reales.json")
                    .read_text(encoding="utf-8"))
    cp = json.loads((SKILL / "pilot" / "claim-packets" / "pieza-01-reales.json")
                    .read_text(encoding="utf-8"))
    return art, ho, cp


def _ejecutar(brief=None):
    art, ho, cp = _cargar()
    vi = canonical.build_visual_input(art, ho)
    pol, fams = VisualPolicy.load(), VisualFamilyRegistry.load()
    br = brief if brief is not None else cli.brief_desde(vi, pol, fams)
    return pipeline.generate_visual(
        art["procedencia"], br, pol, FakeImageProvider(), handoff=ho, claim_packet=cp,
        exact_copy=vi.exact_copy, author=vi.author, content_type=vi.content_type,
        families_version=fams.version,
        reserved_surface=ReservedSurface(120, 1500, 840, 180))


class TestLaBandaSeDerivaDelTextoReal(unittest.TestCase):
    def test_la_zona_sale_de_los_bloques_no_del_safe_area(self):
        """La distincion importa: el safe_area de una pieza 9:16 cubre casi todo
        el lienzo (153..1767 de 1920). Usarlo equivaldria a pedir que el 89 % de
        la imagen quede vacia — eso no reserva una zona, mata la escena."""
        art, ho, _ = _cargar()
        vi = canonical.build_visual_input(art, ho)
        typo = composition.build_typography_plan(
            vi.exact_copy, vi.author, 1080, 1920, content_type=vi.content_type)
        _x, inicio, _w, alto = pipeline._zona_ocupada_por_el_texto(typo, 1080, 1920)

        _sx, sy, _sw, sh = typo.safe_area
        alto_safe = int(100 * sh / 1920)
        self.assertLess(alto, alto_safe,
                        "la banda derivada no puede ser tan ancha como el safe_area")
        self.assertLess(alto, 60, "reservar mas de media imagen no deja escena")
        self.assertGreater(alto, 10, "una banda demasiado estrecha no protege el texto")
        self.assertLess(inicio, 20, "el texto de esta pieza empieza arriba")

    def test_sin_metricas_de_bloque_no_se_inventa_una_banda(self):
        """Devolver None y dejar el prompt como estaba es mejor que inventar una
        banda estrecha que no protege nada."""
        class PlanVacio:
            blocks = []
            safe_area = (86, 153, 908, 1614)
        self.assertIsNone(pipeline._zona_ocupada_por_el_texto(PlanVacio(), 1080, 1920))

    def test_un_texto_mas_largo_reserva_mas_banda(self):
        """Prueba de que la derivacion mide de verdad y no devuelve una constante."""
        corto = composition.build_typography_plan(
            "Poseer no es ser dueno.", "Nota", 1080, 1920, content_type="concepto")
        largo = composition.build_typography_plan(
            "Poseer no es ser dueno. " * 12, "Nota", 1080, 1920, content_type="concepto")
        z_corto = pipeline._zona_ocupada_por_el_texto(corto, 1080, 1920)
        z_largo = pipeline._zona_ocupada_por_el_texto(largo, 1080, 1920)
        self.assertGreater(z_largo[3], z_corto[3])


class TestLaBandaLlegaAlPrompt(unittest.TestCase):
    def _prompt(self, run):
        import dataclasses
        c = run.compiled
        d = c if isinstance(c, dict) else dataclasses.asdict(c)
        return d.get("positive_prompt", "")

    def test_el_prompt_reserva_la_banda_del_texto(self):
        """El control central de este archivo."""
        run = _ejecutar()
        prompt = self._prompt(run)
        self.assertIn("Espacio negativo reservado", prompt)
        self.assertIn("queda en calma", prompt)
        self.assertIn("% de la altura", prompt)

    def test_la_derivacion_queda_registrada(self):
        """Cambia lo que se le pide al proveedor: sin traza, un cambio de banda
        seria indistinguible de un cambio de arte."""
        run = _ejecutar()
        eventos = [e for e in run.events if e["event"] == "visual.negative_space.derived"]
        self.assertEqual(len(eventos), 1)
        self.assertIn("%", eventos[0]["banda"])

    def test_un_negative_space_escrito_a_mano_no_se_pisa(self):
        """La direccion de arte humana manda sobre la derivacion automatica."""
        art, ho, _ = _cargar()
        vi = canonical.build_visual_input(art, ho)
        pol, fams = VisualPolicy.load(), VisualFamilyRegistry.load()
        from dataclasses import replace
        br = replace(cli.brief_desde(vi, pol, fams),
                     negative_space="el tercio inferior, decidido por direccion de arte")
        run = _ejecutar(br)
        prompt = self._prompt(run)
        self.assertIn("decidido por direccion de arte", prompt)
        self.assertNotIn("queda en calma", prompt)

    def test_sin_copia_exacta_no_se_reserva_nada(self):
        """Una pieza sin texto montado no necesita banda, y reservarla le quitaria
        escena sin motivo.

        Se comprueba el PROMPT, no solo el evento: sin copia exacta la derivacion
        fallaria de todos modos al construir el plan tipografico, asi que mirar
        solo el evento no distinguiria "el guardia funciona" de "fallo por otro
        motivo". Lo que se exige es que el prompt salga sin banda reservada.
        """
        art, ho, cp = _cargar()
        vi = canonical.build_visual_input(art, ho)
        pol, fams = VisualPolicy.load(), VisualFamilyRegistry.load()
        run = pipeline.generate_visual(
            art["procedencia"], cli.brief_desde(vi, pol, fams), pol, FakeImageProvider(),
            handoff=ho, claim_packet=cp, exact_copy="", author="",
            content_type=vi.content_type, families_version=fams.version)
        self.assertEqual(
            [e for e in run.events if e["event"] == "visual.negative_space.derived"], [])
        import dataclasses
        prompt = dataclasses.asdict(run.compiled)["positive_prompt"]
        self.assertNotIn("Espacio negativo reservado", prompt)
        self.assertNotIn("queda en calma", prompt)


class TestNoDebilitaNingunControl(unittest.TestCase):
    def test_la_reserva_no_abre_gates_ni_aprueba(self):
        run = _ejecutar()
        self.assertEqual(run.receipt.human_visual_approval, "PENDIENTE")
        self.assertEqual(run.receipt.status, "PENDIENTE_REVISION_HUMANA")

    def test_el_texto_exacto_no_se_toca(self):
        """La banda cambia el PROMPT, nunca la copia juridica."""
        art, ho, _ = _cargar()
        vi = canonical.build_visual_input(art, ho)
        run = _ejecutar()
        self.assertEqual(run.typography_plan.rendered_text().count(vi.exact_copy[:40]), 1)

    def test_el_generador_sigue_sin_escribir_texto(self):
        """Reservar espacio para el texto no es pedirle al generador que lo
        escriba: sigue prohibido."""
        import dataclasses
        run = _ejecutar()
        d = dataclasses.asdict(run.compiled)
        self.assertIn("texto", [n.lower() for n in d["negative_constraints"]])
        self.assertEqual(d["text_mode"], "POST_COMPOSITE")


if __name__ == "__main__":
    unittest.main()
