"""Hotfix memoria fuerte (autorización del Founder, 16-sep-2026): tests del
módulo de ingestión de la fuente #5 y de las reglas de rechazo — casos
normal, límite y adversarial (Contrato v4 §8)."""

import unittest

import memoria_fuerte as mf
from semantic_fingerprint import SemanticFingerprint
from semantic_memory import PRESELECCIONADA, PUBLICADA, SemanticMemory
from visual_fingerprint import VisualFingerprint


class TestIngestionNormal(unittest.TestCase):
    """Caso normal: la fuente #5 se puebla completa y con los estados
    correctos."""

    def setUp(self):
        self.memoria = mf.cargar_memoria_fuerte()

    def test_dieciseis_piezas_en_total(self):
        self.assertEqual(len(self.memoria), 16)

    def test_doce_publicadas_cuatro_preseleccionadas(self):
        self.assertEqual(len(self.memoria.entries(PUBLICADA)), 12)
        self.assertEqual(len(self.memoria.entries(PRESELECCIONADA)), 4)

    def test_todos_los_content_id_de_la_fuente_estan_presentes(self):
        ids = {e.fingerprint.get("content_id") for e in self.memoria.entries()}
        esperados = {r["content_id"] for r in mf.PIEZAS_PUBLICADAS + mf.PIEZAS_PRESELECCIONADAS}
        self.assertEqual(ids, esperados)

    def test_metricas_reales_no_se_pierden_en_el_registro_original(self):
        """Las cifras verbatim (vistas/interacciones/likes/compartidos) viven
        en PIEZAS_PUBLICADAS, no se inventan ni se pierden al construir la
        huella (que no tiene campo de métricas)."""
        carnelutti = next(r for r in mf.PIEZAS_PUBLICADAS if r["content_id"] == "MF-10-CARNELUTTI")
        self.assertEqual(carnelutti["metricas"], {"likes": 2224, "compartidos": 1195})

    def test_cargar_memoria_fuerte_es_independiente_de_memoria_de_ejecucion(self):
        """No debe mezclarse con la memoria de una corrida (production_run.py):
        cada llamada construye su propia instancia desde cero."""
        m1 = mf.cargar_memoria_fuerte()
        m2 = mf.cargar_memoria_fuerte()
        self.assertIsNot(m1, m2)
        self.assertEqual(len(m1), len(m2))


class TestDeteccionDeTemaNormal(unittest.TestCase):
    """Caso normal: un candidato que repite el tema de una pieza real de
    memoria fuerte SÍ debe bloquearse — probar que el mecanismo detecta,
    no sólo que nunca dispara."""

    def setUp(self):
        self.memoria = mf.cargar_memoria_fuerte()

    def test_repetir_servidumbre_de_paso_bloquea(self):
        # necesidad/familia_editorial se dejan vacías a propósito: la fuente
        # #5 no las declara para las piezas de la sección 1 (sólo título y
        # cifras reales) — inventarlas sería fabricar dato, no estructurar
        # uno real (ver docstring de memoria_fuerte.py).
        candidato = SemanticFingerprint(
            content_id="NUEVO-1", materia="civil", submateria="servidumbres",
            concepto_nucleo="servidumbre de paso frente a propiedad")
        veredicto = self.memoria.evaluar(candidato)
        self.assertTrue(veredicto.bloquea, veredicto.motivo)
        self.assertEqual(veredicto.contra, "MF-01-SERVIDUMBRE-PASO")
        self.assertEqual(veredicto.estado_contra, PUBLICADA)


class TestLimiteMismaMateriaConceptoDistinto(unittest.TestCase):
    """Caso límite: misma materia que una pieza aprobada, concepto
    sustancialmente distinto — NO debe bloquearse. Memoria fuerte impide
    repetir lo ya contado, nunca cierra una materia entera (mismo principio
    de diseño que semantic_memory.py declara para DESCARTADA)."""

    def test_civil_pero_tema_distinto_no_bloquea(self):
        memoria = mf.cargar_memoria_fuerte()
        candidato = SemanticFingerprint(
            content_id="NUEVO-2", materia="civil", submateria="contratos",
            concepto_nucleo="requisitos de validez de un contrato de compraventa",
            necesidad="prepararse", familia_editorial="checklist")
        veredicto = memoria.evaluar(candidato)
        self.assertFalse(veredicto.bloquea, veredicto.motivo)


class TestEvaluarVisualFuerte(unittest.TestCase):
    """Extensión añadida a SemanticMemory: distancia VISUAL contra memoria
    fuerte, no sólo distancia de tema."""

    def setUp(self):
        self.memoria = mf.cargar_memoria_fuerte()

    def test_memoria_vacia_no_bloquea(self):
        vacia = SemanticMemory()
        fp = SemanticFingerprint(content_id="x", direccion_artistica="óleo dramático")
        v = vacia.evaluar_visual_fuerte(fp)
        self.assertFalse(v.bloquea)
        self.assertIn("vacía", v.motivo)

    def test_repetir_puesta_en_escena_de_carnelutti_bloquea(self):
        candidato = SemanticFingerprint(
            content_id="NUEVO-3", direccion_artistica="pergamino dorado con cita larga legible",
            composicion="pergamino con cita larga + dos abogados de espaldas mirándolo",
            material="pergamino / banda dorada")
        v = self.memoria.evaluar_visual_fuerte(candidato)
        self.assertTrue(v.bloquea, v.motivo)
        self.assertEqual(v.contra, "MF-10-CARNELUTTI")

    def test_puesta_en_escena_distinta_no_bloquea(self):
        candidato = SemanticFingerprint(
            content_id="NUEVO-4", direccion_artistica="fotografía documental contemporánea",
            composicion="calle urbana de noche, luces de neón", material="vidrio y acero")
        v = self.memoria.evaluar_visual_fuerte(candidato)
        self.assertFalse(v.bloquea, v.motivo)

    def test_no_altera_evaluar_existente(self):
        """evaluar() (tema) sigue funcionando exactamente igual — método
        nuevo, additivo, no una reescritura."""
        fp = SemanticFingerprint(content_id="x", materia="penal", concepto_nucleo="algo nuevo")
        v = self.memoria.evaluar(fp)
        self.assertFalse(v.bloquea)


class TestReglasRechazoFounderAdversarial(unittest.TestCase):
    """Caso adversarial (Contrato v4 §8): un candidato que reproduce un
    rechazo explícito de la sección 4 debe detectarse ANTES de generar."""

    def huella(self, **kw):
        base = dict(content_id="x", primary_direction="", secondary_direction="",
                   medium="", lighting="", composition="", camera_optics="",
                   palette="", materiality="", realism="", visual_mechanism="")
        base.update(kw)
        return VisualFingerprint(**base)

    def test_huella_limpia_no_dispara_ninguna_regla(self):
        h = self.huella(primary_direction="óleo narrativo mediterráneo",
                        medium="óleo sobre lienzo", palette="tierras cálidas",
                        composition="axial simétrica", materiality="lienzo texturado")
        self.assertEqual(mf.verificar_rechazos_founder(h), [])

    def test_rechazo_1_paleta_limpia_inventada(self):
        # Sin comas: normaliza() (memory.py) descarta tokens con puntuación
        # pegada en vez de sólo despuntuarlos — comportamiento existente del
        # helper compartido, no algo que este módulo deba corregir.
        h = self.huella(palette="azul tinta con acentos teal ambar y oro")
        v = mf.verificar_rechazos_founder(h)
        self.assertTrue(any("RECHAZO-1" in x for x in v), v)

    def test_rechazo_2_hiperrealista_capas_de_texto(self):
        h = self.huella(realism="hiperrealista", visual_mechanism="cuatro capas de texto superpuestas")
        v = mf.verificar_rechazos_founder(h)
        self.assertTrue(any("RECHAZO-2" in x for x in v), v)

    def test_rechazo_3_objeto_frio_sin_figura_humana(self):
        h = self.huella(composition="primer plano de unas manos sobre una mesa vacía")
        v = mf.verificar_rechazos_founder(h)
        self.assertTrue(any("RECHAZO-3" in x for x in v), v)

    def test_rechazo_3_no_dispara_si_hay_figura_humana(self):
        h = self.huella(composition="manos de una persona con rostro visible en primer plano")
        v = mf.verificar_rechazos_founder(h)
        self.assertFalse(any("RECHAZO-3" in x for x in v), v)

    def test_rechazo_4_flat_illustration_bold(self):
        h = self.huella(medium="flat illustration", palette="colores bold saturados")
        v = mf.verificar_rechazos_founder(h)
        self.assertTrue(any("RECHAZO-4" in x for x in v), v)

    def test_rechazo_5_sepia_murky(self):
        h = self.huella(palette="sepia envejecido")
        v = mf.verificar_rechazos_founder(h)
        self.assertTrue(any("RECHAZO-5" in x for x in v), v)

    def test_rechazo_5_no_dispara_con_negacion_explicita(self):
        """Falso positivo real encontrado en el catálogo maestro:
        'fotografía de hora dorada sin dominante sepia' NO es una pieza
        sepia — es una que lo excluye explícitamente."""
        h = self.huella(palette="fotografía de hora dorada sin dominante sepia")
        v = mf.verificar_rechazos_founder(h)
        self.assertFalse(any("RECHAZO-5" in x for x in v), v)

    def test_rechazo_6_negative_space_bands(self):
        h = self.huella(composition="negative space en banda superior e inferior")
        v = mf.verificar_rechazos_founder(h)
        self.assertTrue(any("RECHAZO-6" in x for x in v), v)

    def test_rechazo_7_collage_grid_multipanel(self):
        h = self.huella(composition="collage tipo grid multipanel")
        v = mf.verificar_rechazos_founder(h)
        self.assertTrue(any("RECHAZO-7" in x for x in v), v)

    def test_cada_violacion_cita_el_documento_fuente(self):
        h = self.huella(palette="sepia")
        v = mf.verificar_rechazos_founder(h)
        self.assertTrue(v)
        for motivo in v:
            self.assertIn(mf.FUENTE_DOCUMENTO_URL, motivo)

    def test_perfil_emocional_tambien_se_revisa(self):
        h = self.huella()
        perfil = {"composicion": "formato collage con grid multipanel", "camara": "", "luz": "",
                  "escala": "", "textura": "", "ritmo": ""}
        v = mf.verificar_rechazos_founder(h, perfil)
        self.assertTrue(any("RECHAZO-7" in x for x in v), v)


if __name__ == "__main__":
    unittest.main()
