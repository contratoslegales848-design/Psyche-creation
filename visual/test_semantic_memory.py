"""Estados, memoria fuerte/corta, cooldown y aprendizaje desde la curaduría."""

import tempfile
import unittest
from pathlib import Path

from semantic_memory import (
    SemanticMemory, SemanticMemoryError, GENERADA, PRESELECCIONADA, APROBADA,
    PUBLICADA, DESCARTADA, COOLDOWN, MEMORIA_FUERTE, ESTADOS,
)
from semantic_fingerprint import SemanticFingerprint


def fp(cid, **kw):
    base = dict(content_id=cid, materia="civil", submateria="arrendamiento",
                concepto_nucleo="deposito en garantia", relacion="dinero retenido",
                familia_editorial="mito", necesidad="corregir",
                pregunta_resuelta="puede el arrendador quedarse el deposito",
                angulo="critico", contexto_funcional="despues_del_dano",
                rol_lector="persona", consecuencia="se pierde dinero")
    base.update(kw)
    return SemanticFingerprint(**base)


def otra_rama(cid):
    return fp(cid, familia_editorial="checklist", necesidad="prepararse",
              pregunta_resuelta="que revisar antes de entregar el deposito",
              angulo="procedimental", contexto_funcional="antes_de_firmar")


class TestEstados(unittest.TestCase):
    def test_estados_canonicos(self):
        self.assertEqual(set(ESTADOS),
                         {GENERADA, PRESELECCIONADA, APROBADA, PUBLICADA, DESCARTADA})

    def test_rechaza_estado_inventado(self):
        with self.assertRaises(SemanticMemoryError):
            SemanticMemory().record(fp("a"), "CASI_APROBADA")

    def test_generar_no_es_aprobar(self):
        """La distinción central: producir no equivale a aprobar."""
        m = SemanticMemory()
        m.record(fp("a"))
        self.assertEqual(m.entries()[0].estado, GENERADA)
        self.assertEqual(m.entries(APROBADA), [])

    def test_promocion_explicita(self):
        m = SemanticMemory()
        m.record(fp("a"))
        self.assertEqual(m.promover("a", APROBADA), 1)
        self.assertEqual(m.entries(APROBADA)[0].fingerprint["content_id"], "a")

    def test_no_se_promueve_lo_que_no_se_genero(self):
        with self.assertRaises(SemanticMemoryError):
            SemanticMemory().promover("fantasma", APROBADA)


class TestCooldown(unittest.TestCase):
    def test_el_descarte_tiene_la_ventana_mas_corta(self):
        """Un descarte es fatiga de un ángulo, no una rama cancelada."""
        self.assertEqual(COOLDOWN[DESCARTADA], min(COOLDOWN.values()))
        for fuerte in MEMORIA_FUERTE:
            self.assertGreater(COOLDOWN[fuerte], COOLDOWN[DESCARTADA])

    def test_aprobada_y_publicada_son_la_memoria_mas_larga(self):
        self.assertEqual(COOLDOWN[APROBADA], max(COOLDOWN.values()))
        self.assertEqual(COOLDOWN[PUBLICADA], max(COOLDOWN.values()))


class TestEvaluar(unittest.TestCase):
    def test_memoria_vacia_no_bloquea(self):
        self.assertFalse(SemanticMemory().evaluar(fp("a")).bloquea)

    def test_bloquea_el_equivalente_de_memoria_fuerte(self):
        m = SemanticMemory()
        m.record(fp("a"), APROBADA)
        v = m.evaluar(fp("b", hook="otro hook", formato="historia"))
        self.assertTrue(v.bloquea)
        self.assertEqual(v.estado_contra, APROBADA)
        self.assertIn("memoria fuerte", v.motivo)

    def test_bloquea_lo_generado_recientemente(self):
        m = SemanticMemory()
        m.record(fp("a"), GENERADA)
        v = m.evaluar(fp("b", hook="otro"))
        self.assertTrue(v.bloquea)
        self.assertEqual(v.estado_contra, GENERADA)

    def test_el_descarte_no_cancela_la_rama(self):
        """La regla que impide que el sistema se encierre."""
        m = SemanticMemory()
        m.record(fp("a"), DESCARTADA)
        self.assertTrue(m.evaluar(fp("b")).bloquea)          # mismo ángulo exacto
        self.assertFalse(m.evaluar(otra_rama("c")).bloquea)  # otra puerta, misma materia

    def test_el_motivo_del_descarte_lo_explica(self):
        m = SemanticMemory()
        m.record(fp("a"), DESCARTADA)
        self.assertIn("siguen disponibles", m.evaluar(fp("b")).motivo)

    def test_no_bloquea_otra_familia_editorial(self):
        m = SemanticMemory()
        m.record(fp("a"), PUBLICADA)
        self.assertFalse(m.evaluar(otra_rama("c")).bloquea)

    def test_huella_incomparable_no_bloquea(self):
        """Ausencia de dato no es prueba de repetición."""
        m = SemanticMemory()
        m.record(fp("a"), APROBADA)
        self.assertFalse(m.evaluar(SemanticFingerprint(content_id="vacia")).bloquea)

    def test_informa_la_distancia_aunque_no_bloquee(self):
        m = SemanticMemory()
        m.record(fp("a"), APROBADA)
        v = m.evaluar(otra_rama("c"))
        self.assertFalse(v.bloquea)
        self.assertLess(v.distancia, 1.0)


class TestAprendizaje(unittest.TestCase):
    def test_registrar_seleccion_es_posterior_a_generar(self):
        m = SemanticMemory()
        r = m.registrar_seleccion([fp("a"), fp("b", familia_editorial="checklist")],
                                  [fp("c", familia_editorial="proceso")], "lote-1")
        self.assertEqual(r["preseleccionadas"], 2)
        self.assertEqual(r["descartadas"], 1)
        self.assertAlmostEqual(r["selection_rate"], 2 / 3, places=3)

    def test_selection_rate_de_tres_de_diez(self):
        m = SemanticMemory()
        sel = [fp(f"s{i}", familia_editorial=f"fam{i}") for i in range(3)]
        des = [fp(f"d{i}", familia_editorial=f"otra{i}") for i in range(7)]
        self.assertEqual(m.registrar_seleccion(sel, des, "l1")["selection_rate"], 0.3)

    def test_las_preferencias_son_sesgo_y_no_filtro(self):
        """Un descarte baja el peso, nunca lo elimina: si excluyera, el
        sistema se encerraría en lo ya premiado."""
        m = SemanticMemory()
        m.record(fp("a", familia_editorial="mito"), APROBADA)
        m.record(fp("b", familia_editorial="mito"), DESCARTADA)
        pref = m.preferencias()["familia_editorial"]
        self.assertIn("mito", pref)
        self.assertEqual(pref["mito"], 0.5)

    def test_la_preferencia_positiva_pesa_mas_que_el_descarte(self):
        m = SemanticMemory()
        m.record(fp("a", familia_editorial="checklist"), APROBADA)
        m.record(fp("b", familia_editorial="mito"), DESCARTADA)
        pref = m.preferencias()["familia_editorial"]
        self.assertGreater(pref["checklist"], pref["mito"])

    def test_cubre_los_ejes_de_aprendizaje(self):
        m = SemanticMemory()
        m.record(fp("a", emocion="urgencia"), APROBADA)
        for eje in ("materia", "familia_editorial", "necesidad", "angulo",
                    "emocion", "rol_lector"):
            self.assertIn(eje, m.preferencias())


class TestPersistencia(unittest.TestCase):
    def test_ida_y_vuelta(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "mem.json"
            m = SemanticMemory()
            m.record(fp("a"), APROBADA)
            m.record(fp("b", familia_editorial="proceso"), DESCARTADA)
            m.save(p)
            otra = SemanticMemory.load(p)
            self.assertEqual(len(otra), 2)
            self.assertTrue(otra.evaluar(fp("c", hook="otro")).bloquea)

    def test_fichero_inexistente_da_memoria_vacia(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(len(SemanticMemory.load(Path(d) / "no.json")), 0)

    def test_esquema_desconocido_se_ignora_en_vez_de_malinterpretarse(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "mem.json"
            p.write_text('{"schema_version":"99.0","entries":[{"fingerprint":{},'
                         '"estado":"APROBADA"}]}', encoding="utf-8")
            self.assertEqual(len(SemanticMemory.load(p)), 0)


if __name__ == "__main__":
    unittest.main()
