"""Puente emoción → argumento visual → dirección de arte.

Incluye la prueba CAUSAL que exige el mandato de reconciliación: cambiar
`emotion` debe cambiar cámara/composición, nunca dejar la imagen "exactamente
igual" bajo una etiqueta distinta.
"""

import unittest

import art_direction as ad
import emotion
import families
import memoria_fuerte as mf
import universe
import visual_fingerprint as vf
from memory import VisualMemory, VisualMemoryEntry


class TestDerivarFuncionVisual(unittest.TestCase):
    def test_familia_con_mapeo_directo(self):
        f, razon = ad.derivar_funcion_visual("mito", "corregir")
        self.assertEqual(f, "REVEAL")
        self.assertIn("familia editorial", razon)

    def test_sin_mapeo_de_familia_cae_a_necesidad(self):
        f, razon = ad.derivar_funcion_visual("familia_sin_mapeo", "prevenir")
        self.assertEqual(f, "WARN")
        self.assertIn("necesidad", razon)

    def test_sin_evidencia_alguna_devuelve_funcion_neutra(self):
        f, razon = ad.derivar_funcion_visual("nada", "nada")
        self.assertEqual(f, "EXPLAIN")
        self.assertIn("por defecto", razon)

    def test_es_determinista(self):
        self.assertEqual(ad.derivar_funcion_visual("mito", "corregir"),
                         ad.derivar_funcion_visual("mito", "corregir"))

    def test_toda_funcion_pertenece_al_vocabulario_declarado(self):
        for fam in ad.FUNCION_POR_FAMILIA.values():
            self.assertIn(fam, ad.VISUAL_FUNCTIONS)
        for nec in ad.FUNCION_POR_NECESIDAD.values():
            self.assertIn(nec, ad.VISUAL_FUNCTIONS)


class TestElegirFamiliaVisual(unittest.TestCase):
    def setUp(self):
        self.registro = families.VisualFamilyRegistry.load()

    def test_sin_memoria_elige_determinista(self):
        a = ad.elegir_familia_visual(self.registro)
        b = ad.elegir_familia_visual(self.registro)
        self.assertEqual(a.name, b.name)

    def test_rota_lejos_de_la_familia_mas_usada(self):
        mem = VisualMemory()
        usada = self.registro.names()[0]
        for i in range(5):
            mem.record(VisualMemoryEntry(content_id=f"c{i}", generation_id=f"g{i}",
                                         visual_family=usada))
        elegida = ad.elegir_familia_visual(self.registro, mem)
        self.assertNotEqual(elegida.name, usada)

    def test_nunca_una_regla_fija_materia_estilo(self):
        """No existe ningún parámetro 'materia' en la firma: la elección no
        puede depender de la materia jurídica."""
        import inspect
        params = inspect.signature(ad.elegir_familia_visual).parameters
        self.assertNotIn("materia", params)


class TestDraftVisualBrief(unittest.TestCase):
    def setUp(self):
        self.registro = families.VisualFamilyRegistry.load()
        self.catalogo = vf.MasterCatalog.load()

    def candidato(self, **kw):
        base = dict(candidate_id="X", materia="civil", submateria="s",
                   familia_editorial="mito", necesidad="corregir", rol_lector="persona",
                   angulo="a", contexto_funcional="c", profundidad="base", formato="frase",
                   concepto_nucleo="n", relacion="r", pregunta_resuelta="p")
        base.update(kw)
        return universe.TopicCandidate(**base)

    def test_produce_los_campos_declarados(self):
        c = self.candidato()
        perfil = emotion.derivar(necesidad=c.necesidad, familia_editorial=c.familia_editorial)
        d = ad.draft_visual_brief(c, perfil.to_dict(), self.catalogo, registro_familias=self.registro)
        self.assertEqual(d.content_id, "X")
        self.assertTrue(d.visual_function)
        self.assertTrue(d.familia_visual)
        self.assertTrue(d.composicion)
        self.assertTrue(d.camara)

    def test_nunca_esta_autorizado(self):
        c = self.candidato()
        perfil = emotion.derivar(necesidad=c.necesidad, familia_editorial=c.familia_editorial)
        d = ad.draft_visual_brief(c, perfil.to_dict(), self.catalogo, registro_familias=self.registro)
        self.assertFalse(d.autorizado)

    def test_escena_y_metafora_quedan_pendientes_de_contenido(self):
        """No se inventa una escena ni una metáfora concreta: es contenido
        creativo verificable, no infraestructura."""
        c = self.candidato()
        perfil = emotion.derivar(necesidad=c.necesidad, familia_editorial=c.familia_editorial)
        d = ad.draft_visual_brief(c, perfil.to_dict(), self.catalogo, registro_familias=self.registro)
        self.assertEqual(d.escena, ad.PENDIENTE_CONTENIDO)
        self.assertEqual(d.metafora, ad.PENDIENTE_CONTENIDO)

    def test_no_reinfiere_lo_que_emotion_py_ya_decidio(self):
        """El perfil emocional se propaga, no se recalcula aquí."""
        c = self.candidato()
        perfil = emotion.derivar(necesidad="actuar", familia_editorial="plazo_prescripcion",
                                 consecuencia="se pierde el derecho")
        d = ad.draft_visual_brief(c, perfil.to_dict(), self.catalogo, registro_familias=self.registro)
        self.assertEqual(d.composicion, perfil.composicion)
        self.assertEqual(d.camara, perfil.camara)
        self.assertEqual(d.luz, perfil.luz)


class TestPruebaCausal(unittest.TestCase):
    """El caso central del Paso 6: 'no permitas emotion=tension si después la
    imagen se genera exactamente igual'."""

    def setUp(self):
        self.registro = families.VisualFamilyRegistry.load()
        self.catalogo = vf.MasterCatalog.load()

    def draft_para(self, necesidad, familia, consecuencia=""):
        c = universe.TopicCandidate(
            candidate_id="X", materia="civil", submateria="s", familia_editorial=familia,
            necesidad=necesidad, rol_lector="persona", angulo="a", contexto_funcional="c",
            profundidad="base", formato="frase", concepto_nucleo="n", relacion="r",
            pregunta_resuelta="p", consecuencia=consecuencia)
        perfil = emotion.derivar(necesidad=necesidad, familia_editorial=familia,
                                 consecuencia=consecuencia)
        return ad.draft_visual_brief(c, perfil.to_dict(), self.catalogo,
                                     registro_familias=self.registro), perfil

    def test_emociones_distintas_producen_composicion_distinta(self):
        d1, p1 = self.draft_para("reflexionar", "doctrina")
        d2, p2 = self.draft_para("actuar", "plazo_prescripcion", consecuencia="se pierde el plazo")
        self.assertNotEqual(p1.emocion, p2.emocion)
        self.assertNotEqual(d1.composicion, d2.composicion)

    def test_emociones_distintas_producen_camara_distinta(self):
        d1, p1 = self.draft_para("reflexionar", "doctrina")
        d2, p2 = self.draft_para("actuar", "plazo_prescripcion", consecuencia="se pierde el plazo")
        self.assertNotEqual(p1.emocion, p2.emocion)
        self.assertNotEqual(d1.camara, d2.camara)

    def test_la_imagen_nunca_se_genera_exactamente_igual_bajo_otra_emocion(self):
        """Recorre pares de necesidades con emociones distintas y exige que
        al menos composición o cámara difieran siempre que la emoción
        difiera — el brief nunca es idéntico bajo otra etiqueta emocional."""
        casos = [("entender", "concepto", ""), ("actuar", "plazo_prescripcion", "vence el plazo"),
                 ("reflexionar", "doctrina", ""), ("reclamar", "derecho", "se ignoró el derecho")]
        drafts = [self.draft_para(n, f, c) for n, f, c in casos]
        for i in range(len(drafts)):
            for j in range(i + 1, len(drafts)):
                (d1, p1), (d2, p2) = drafts[i], drafts[j]
                if p1.emocion != p2.emocion:
                    self.assertTrue(d1.composicion != d2.composicion or d1.camara != d2.camara,
                                    f"{p1.emocion} vs {p2.emocion}: misma composición y cámara")


class TestDiversidadDeEstilos(unittest.TestCase):
    def setUp(self):
        self.registro = families.VisualFamilyRegistry.load()
        self.catalogo = vf.MasterCatalog.load()

    def draft(self, familia_visual):
        return ad.VisualBriefDraft(content_id="x", familia_visual=familia_visual)

    def test_compatibilidad_retroactiva_con_registro_de_familias(self):
        """El techo por families.py (8 familias) se conserva vía
        registro_familias= sólo para compatibilidad de llamadas antiguas."""
        drafts = [self.draft(n) for n in self.registro.names()]
        ok, detalle = ad.verificar_diversidad_de_estilos(
            drafts, n_esperado=10, registro_familias=self.registro)
        self.assertTrue(ok, detalle)
        self.assertIn(f"{len(self.registro.names())}/{len(self.registro.names())}", detalle)

    def test_detecta_concentracion_de_estilo(self):
        drafts = [self.draft(self.registro.names()[0]) for _ in range(5)]
        ok, detalle = ad.verificar_diversidad_de_estilos(
            drafts, n_esperado=5, registro_familias=self.registro)
        self.assertFalse(ok, detalle)

    def test_con_catalogo_maestro_el_techo_real_es_n_no_ocho(self):
        """CORRECCIÓN CENTRAL de la Parte XII: con el catálogo maestro real
        (504 direcciones), el techo de un lote de 10 ya no es 8 — es 10.
        La 'biblioteca artística abierta' que antes era aspiracional
        (ver commit anterior, families.py de 8 entradas) ya existe."""
        drafts = [self.draft(f"estilo-{i}") for i in range(10)]
        ok, detalle = ad.verificar_diversidad_de_estilos(drafts, self.catalogo, n_esperado=10)
        self.assertTrue(ok, detalle)
        self.assertIn("10/10", detalle)
        self.assertIn("504", detalle)

    def test_con_catalogo_maestro_sigue_detectando_concentracion_real(self):
        drafts = [self.draft("mismo-estilo-repetido") for _ in range(10)]
        ok, detalle = ad.verificar_diversidad_de_estilos(drafts, self.catalogo, n_esperado=10)
        self.assertFalse(ok, detalle)
        self.assertIn("1/10", detalle)

    def test_sin_ninguna_fuente_lanza_error_explicito(self):
        with self.assertRaises(ValueError):
            ad.verificar_diversidad_de_estilos([self.draft("x")], n_esperado=1)


class TestMemoriaFuerteEnDraftVisualBrief(unittest.TestCase):
    """Hotfix memoria fuerte (autorización del Founder, 16-sep-2026) —
    integración de la fuente #5 en `draft_visual_brief()`. Casos normal,
    límite y adversarial (Contrato v4 §8)."""

    def setUp(self):
        self.registro = families.VisualFamilyRegistry.load()
        self.catalogo = vf.MasterCatalog.load()

    def candidato(self, **kw):
        base = dict(candidate_id="X", materia="civil", submateria="s",
                   familia_editorial="mito", necesidad="corregir", rol_lector="persona",
                   angulo="a", contexto_funcional="c", profundidad="base", formato="frase",
                   concepto_nucleo="n", relacion="r", pregunta_resuelta="p")
        base.update(kw)
        return universe.TopicCandidate(**base)

    def test_normal_sin_memoria_fuerte_no_cambia_el_comportamiento_previo(self):
        """`memoria_fuerte=None` (por omisión) preserva el comportamiento de
        antes del Hotfix: nunca bloquea por tema/escena repetidos, sólo por
        los 7 rechazos permanentes del Founder (que sí corren por defecto)."""
        c = self.candidato()
        perfil = emotion.derivar(necesidad=c.necesidad, familia_editorial=c.familia_editorial)
        d = ad.draft_visual_brief(c, perfil.to_dict(), self.catalogo, registro_familias=self.registro)
        self.assertIsInstance(d.bloqueado_memoria_fuerte, bool)
        self.assertIsInstance(d.motivos_bloqueo_memoria_fuerte, list)

    def test_normal_memoria_fuerte_poblada_no_bloquea_un_candidato_distinto(self):
        memoria = mf.cargar_memoria_fuerte()
        c = self.candidato(concepto_nucleo="un concepto jurídico sin relación con la fuente #5")
        perfil = emotion.derivar(necesidad=c.necesidad, familia_editorial=c.familia_editorial)
        d = ad.draft_visual_brief(c, perfil.to_dict(), self.catalogo, registro_familias=self.registro,
                                  memoria_fuerte=memoria)
        self.assertFalse(d.bloqueado_memoria_fuerte, d.motivos_bloqueo_memoria_fuerte)

    def test_limite_repetir_tema_de_pieza_publicada_bloquea_antes_de_compilar(self):
        """Caso límite: el candidato reproduce el tema exacto de una pieza
        real ya PUBLICADA (servidumbre de paso, MF-01) — debe bloquearse
        ANTES de que el llamador compile el prompt final, nunca después."""
        # angulo/contexto_funcional/rol_lector/pregunta_resuelta/relacion se
        # dejan vacíos porque la fuente #5 no los declara para MF-01 (sólo
        # título y cifras reales, ver memoria_fuerte.py) — dejar el default
        # del helper ("a"/"c"/"persona"/"p"/"r") compararía datos reales
        # contra datos inventados por este test, no una repetición honesta.
        memoria = mf.cargar_memoria_fuerte()
        c = self.candidato(materia="civil", submateria="servidumbres",
                           concepto_nucleo="servidumbre de paso frente a propiedad",
                           familia_editorial="", necesidad="", angulo="",
                           contexto_funcional="", rol_lector="", pregunta_resuelta="",
                           relacion="")
        perfil = emotion.derivar(necesidad=c.necesidad, familia_editorial=c.familia_editorial)
        d = ad.draft_visual_brief(c, perfil.to_dict(), self.catalogo, registro_familias=self.registro,
                                  memoria_fuerte=memoria)
        self.assertTrue(d.bloqueado_memoria_fuerte)
        self.assertTrue(any("memoria fuerte" in m for m in d.motivos_bloqueo_memoria_fuerte))
        self.assertTrue(any(mf.FUENTE_DOCUMENTO_URL in m for m in d.motivos_bloqueo_memoria_fuerte))

    def test_adversarial_reproducir_rechazo_explicito_bloquea_sin_necesidad_de_memoria_fuerte(self):
        """Caso adversarial (Contrato v4 §8): un candidato cuya dirección
        reproduce un rechazo explícito de la sección 4 debe rechazarse antes
        de generar — incluso sin pasar `memoria_fuerte` (los 7 rechazos son
        reglas de diseño permanentes, no memoria de piezas)."""
        c = self.candidato()
        # Perfil emocional crafteado para reproducir RECHAZO-7 (collage/grid
        # multipanel) de forma determinista, sin depender de qué huella real
        # elija el catálogo maestro para este content_id.
        perfil_dict = emotion.derivar(necesidad=c.necesidad, familia_editorial=c.familia_editorial).to_dict()
        perfil_dict["composicion"] = "formato collage tipo grid multipanel"
        d = ad.draft_visual_brief(c, perfil_dict, self.catalogo, registro_familias=self.registro)
        self.assertTrue(d.bloqueado_memoria_fuerte)
        self.assertTrue(any("RECHAZO-7" in m for m in d.motivos_bloqueo_memoria_fuerte), d.motivos_bloqueo_memoria_fuerte)

    def test_adversarial_se_puede_desactivar_explicitamente_reglas_de_rechazo(self):
        """`reglas_rechazo_founder=()` desactiva la verificación — opción
        explícita para el llamador, nunca el comportamiento por omisión."""
        c = self.candidato()
        perfil_dict = emotion.derivar(necesidad=c.necesidad, familia_editorial=c.familia_editorial).to_dict()
        perfil_dict["composicion"] = "formato collage tipo grid multipanel"
        d = ad.draft_visual_brief(c, perfil_dict, self.catalogo, registro_familias=self.registro,
                                  reglas_rechazo_founder=())
        self.assertFalse(d.bloqueado_memoria_fuerte)

    def test_nunca_lanza_excepcion_el_llamador_decide(self):
        """Mismo patrón que validate_generation_contract()/negotiate(): el
        bloqueo se reporta, nunca se lanza como excepción."""
        memoria = mf.cargar_memoria_fuerte()
        c = self.candidato(materia="civil", submateria="servidumbres",
                           concepto_nucleo="servidumbre de paso frente a propiedad",
                           familia_editorial="", necesidad="", angulo="",
                           contexto_funcional="", rol_lector="", pregunta_resuelta="",
                           relacion="")
        perfil = emotion.derivar(necesidad=c.necesidad, familia_editorial=c.familia_editorial)
        try:
            d = ad.draft_visual_brief(c, perfil.to_dict(), self.catalogo, registro_familias=self.registro,
                                      memoria_fuerte=memoria)
        except Exception as e:  # noqa: BLE001 — la prueba es justamente que NO debe lanzar
            self.fail(f"draft_visual_brief() lanzó una excepción en vez de reportar el bloqueo: {e}")
        self.assertTrue(d.bloqueado_memoria_fuerte)


if __name__ == "__main__":
    unittest.main()
