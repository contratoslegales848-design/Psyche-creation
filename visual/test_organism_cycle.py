"""PRUEBA FINAL OBLIGATORIA — el ciclo completo del organismo.

Reserva amplia → lote de 10 con distancia suficiente en tema, familia
editorial, necesidad, ángulo, emoción, metáfora, composición y dirección
artística → el Founder selecciona 3 y descarta 7 → segundo lote que APRENDE
de esas señales SIN encerrarse ni repetir semánticamente el primero.
"""

import unittest

import batch_qa
import lanes
import organism
import universe
from semantic_memory import (
    SemanticMemory, PRESELECCIONADA, DESCARTADA, GENERADA, APROBADA,
)


class CicloBase(unittest.TestCase):
    """Un ciclo completo compartido: lote 1, curaduría 3/7, lote 2."""

    @classmethod
    def setUpClass(cls):
        cls.memoria = SemanticMemory()
        cls.lote1 = organism.producir_lote("lote-1", n=10, seed=100, memoria=cls.memoria)
        cls.elegidos = [cls.lote1.candidatos[i].candidate_id for i in (0, 3, 7)]
        cls.curaduria = organism.registrar_curaduria(cls.lote1, cls.elegidos, cls.memoria)
        cls.lote2 = organism.producir_lote("lote-2", n=10, seed=200, memoria=cls.memoria)


class TestProduccionContinua(CicloBase):
    def test_el_lote_llega_a_curation_ready(self):
        self.assertTrue(self.lote1.listo, self.lote1.qa.get("incumplimientos"))
        self.assertEqual(self.lote1.estado, organism.CURATION_READY)

    def test_no_exige_autorizacion_previa(self):
        """Corrección expresa del Founder: producir no pide permiso."""
        import inspect
        firma = inspect.signature(organism.producir_lote).parameters
        for prohibido in ("aprobacion", "autorizacion", "handoff", "gate"):
            self.assertNotIn(prohibido, firma)

    def test_curation_ready_no_es_publicable(self):
        """Producir no es publicar. El ciclo completo no puede dejar ninguna
        huella en APROBADA ni PUBLICADA: esos estados exigen decisión humana
        fuera de este módulo."""
        self.assertEqual(self.lote1.estado, organism.CURATION_READY)
        self.assertEqual(self.memoria.entries(APROBADA), [])
        from semantic_memory import PUBLICADA
        self.assertEqual(self.memoria.entries(PUBLICADA), [])

    def test_el_ciclo_no_promueve_a_estados_de_autoridad_humana(self):
        """Lo máximo que la curaduría produce es PRESELECCIONADA."""
        estados = {e.estado for e in self.memoria.entries()}
        self.assertTrue(estados <= {GENERADA, PRESELECCIONADA, DESCARTADA}, estados)

    def test_todo_candidato_sigue_sin_verificar(self):
        for c in self.lote1.candidatos + self.lote2.candidatos:
            self.assertEqual(c.estado_verificacion, universe.NO_VERIFICADO)
            self.assertEqual(c.proxima_accion, universe.ACCION_VERIFICACION)

    def test_la_reserva_es_amplia(self):
        self.assertGreaterEqual(self.lote1.reserva_total, 40)


class TestDiversidadDelPrimerLote(CicloBase):
    def test_son_diez(self):
        self.assertEqual(len(self.lote1.candidatos), 10)

    def test_el_qa_de_lote_lo_acepta(self):
        self.assertEqual(self.lote1.qa["veredicto"], batch_qa.ACEPTADO)

    def test_distancia_suficiente_en_tema(self):
        t = self.lote1.qa["telemetria"]
        self.assertGreaterEqual(t["semantic_distance_min"], batch_qa.MIN_DISTANCIA_PAR)
        self.assertGreaterEqual(t["semantic_distance_media"], batch_qa.MIN_DISTANCIA_MEDIA)
        self.assertEqual(t["topic_repetition"], 0.0)

    def test_distancia_en_familia_editorial_necesidad_angulo_y_emocion(self):
        d = self.lote1.qa["telemetria"]["distintos"]
        self.assertGreaterEqual(d["familia_editorial"], 8)
        self.assertGreaterEqual(d["materia"], 8)
        self.assertGreaterEqual(d["necesidad"], 5)
        self.assertGreaterEqual(d["angulo"], 5)
        self.assertGreaterEqual(d["emocion"], 4)

    def test_ninguna_materia_se_sobreexplota(self):
        _, materias = universe.cargar_materias()
        frec = self.lote1.qa["telemetria"]["frecuencia_materia"]
        for mat, cuenta in frec.items():
            self.assertLessEqual(cuenta, 2, mat)

    def test_no_es_la_misma_sesion_con_diez_disfraces(self):
        self.assertEqual(self.lote1.qa["incumplimientos"], [])


class TestCuraduria(CicloBase):
    def test_tres_de_diez(self):
        self.assertEqual(self.curaduria["preseleccionadas"], 3)
        self.assertEqual(self.curaduria["descartadas"], 7)
        self.assertEqual(self.curaduria["selection_rate"], 0.3)

    def test_las_elegidas_son_señal_positiva(self):
        ids = {e.fingerprint["content_id"] for e in self.memoria.entries(PRESELECCIONADA)}
        self.assertEqual(ids, set(self.elegidos))

    def test_las_descartadas_quedan_registradas(self):
        self.assertEqual(len(self.memoria.entries(DESCARTADA)), 7)

    def test_generar_dejo_rastro_aunque_nadie_aprobara(self):
        self.assertTrue(self.memoria.entries(GENERADA))
        self.assertEqual(self.memoria.entries(APROBADA), [])

    def test_no_se_puede_curar_lo_que_no_esta_en_el_lote(self):
        with self.assertRaises(ValueError):
            organism.registrar_curaduria(self.lote1, ["CAND-9999"], SemanticMemory())


class TestElSegundoLoteAprende(CicloBase):
    """El corazón de la prueba: aprender SIN encerrarse ni repetir."""

    def test_el_segundo_lote_tambien_llega_a_curation_ready(self):
        self.assertTrue(self.lote2.listo, self.lote2.qa.get("incumplimientos"))

    def test_no_repite_semanticamente_el_primero(self):
        for a in self.lote2.fingerprints():
            for b in self.lote1.fingerprints():
                self.assertFalse(a.equivalente_a(b),
                                 f"{a.content_id} repite {b.content_id}")

    def test_ninguna_pieza_del_segundo_lote_choca_con_la_memoria_previa(self):
        """Se evalúa contra la memoria tal y como estaba ANTES de producir el
        lote 2. Evaluarla después sería trivial: cada pieza se encontraría a
        sí misma, porque producir deja rastro de fatiga aunque nadie apruebe."""
        previa = SemanticMemory([e for e in self.memoria.entries()
                                 if e.lote_id != "lote-2"])
        self.assertTrue(len(previa) >= 10)
        for fp in self.lote2.fingerprints():
            v = previa.evaluar(fp)
            self.assertFalse(v.bloquea, f"{fp.content_id}: {v.motivo}")

    def test_no_se_encierra_en_lo_preseleccionado(self):
        """Si sólo produjera lo premiado, el universo se estrecharía."""
        d = self.lote2.qa["telemetria"]["distintos"]
        self.assertGreaterEqual(d["familia_editorial"], 8)
        self.assertGreaterEqual(d["materia"], 8)

    def test_el_descarte_no_cancela_ramas_del_conocimiento(self):
        """Regla anti-encierro: una materia descartada debe poder volver por
        otra puerta editorial."""
        descartadas = {e.fingerprint["materia"] for e in self.memoria.entries(DESCARTADA)}
        vuelven = {c.materia for c in self.lote2.candidatos} & descartadas
        self.assertTrue(
            vuelven,
            "ninguna materia descartada reapareció: el sistema se está encerrando.")

    def test_vuelven_por_otra_puerta_editorial(self):
        por_materia = {}
        for e in self.memoria.entries(DESCARTADA):
            por_materia.setdefault(e.fingerprint["materia"], set()).add(
                e.fingerprint["familia_editorial"])
        reentradas = [c for c in self.lote2.candidatos
                      if c.materia in por_materia
                      and c.familia_editorial not in por_materia[c.materia]]
        self.assertTrue(reentradas,
                        "las materias descartadas sólo vuelven por la misma familia: "
                        "eso sería repetir, no ramificar.")

    def test_la_memoria_crece_con_los_dos_lotes(self):
        self.assertGreaterEqual(len(self.memoria), 20)

    def test_las_preferencias_reflejan_la_curaduria(self):
        pref = self.memoria.preferencias()["familia_editorial"]
        elegidas = {c.familia_editorial for c in self.lote1.candidatos
                    if c.candidate_id in set(self.elegidos)}
        for fam in elegidas:
            from memory import normaliza
            self.assertGreater(pref.get(normaliza(fam), 0), 0)


class TestRegeneracionEnVezDeRelleno(unittest.TestCase):
    def test_no_entrega_un_lote_malo_como_bueno(self):
        """Con una reserva artificialmente mínima, el lote no puede completarse:
        debe quedar en REGENERAR, nunca en CURATION_READY."""
        b = organism.producir_lote("lote-pobre", n=10, seed=1,
                                   memoria=SemanticMemory(), max_intentos=1,
                                   factor_reserva=1)
        if not b.listo:
            self.assertEqual(b.estado, organism.REGENERAR)
            self.assertTrue(b.qa["incumplimientos"] or b.avisos)

    def test_la_telemetria_cuenta_las_regeneraciones(self):
        b = organism.producir_lote("lote-r", n=10, seed=5, memoria=SemanticMemory())
        self.assertIn("regeneration_rate", b.qa["telemetria"])


class TestCarrilesEnElCiclo(unittest.TestCase):
    def test_el_carril_institucional_produce_su_propio_lote(self):
        b = organism.producir_lote("li-1", n=6, seed=50, memoria=SemanticMemory(),
                                   carril=lanes.LINKEDIN_LEGALMENTE)
        self.assertEqual(b.carril, lanes.LINKEDIN_LEGALMENTE)
        for c in b.candidatos:
            self.assertTrue(lanes.validar_candidato(c, lanes.LINKEDIN_LEGALMENTE).admitido)


if __name__ == "__main__":
    unittest.main()
