"""Compilador causal de dirección artística — continuación del Mandato
Maestro (17-sep-2026). Prueba el orden CONCEPTO → TENSIÓN → SIGNIFICADO →
RESTRICCIÓN DEL CATÁLOGO (realism/visual_mechanism) → SELECCIÓN, sin tabla
fija concepto→estilo."""

import unittest

import direccion_causal as dc
import universe
from visual_fingerprint import FingerprintMemory, MasterCatalog


def candidato(**kw):
    base = dict(candidate_id="X", materia="civil", submateria="s",
               familia_editorial="concepto", necesidad="entender", rol_lector="persona",
               angulo="a", contexto_funcional="c", profundidad="base", formato="frase",
               concepto_nucleo="n", relacion="r", pregunta_resuelta="p")
    base.update(kw)
    return universe.TopicCandidate(**base)


class TestTextoLibre(unittest.TestCase):
    """El bug real encontrado durante la construcción: memory.normaliza()
    colapsa frases con '/' a cadena vacía, que como substring "coincide"
    con cualquier texto — filtro que deja de filtrar en silencio."""

    def test_memory_normaliza_no_sirve_para_esto_bug_documentado(self):
        from memory import normaliza
        self.assertEqual(normaliza("umbral/puerta"), "")

    def test_texto_libre_no_colapsa_frases_con_barra(self):
        self.assertEqual(dc._texto_libre("umbral/puerta"), "umbral puerta")
        self.assertIn("umbral", dc._texto_libre("umbral/puerta"))
        self.assertIn("puerta", dc._texto_libre("umbral/puerta"))

    def test_clave_vacia_nunca_se_usa_como_comodin(self):
        """Si una palabra clave normalizara a vacío, NO debe hacer que todo
        el pool 'coincida' — regresión directa del bug encontrado."""
        catalogo = MasterCatalog.load()
        sig = type("S", (), {"movimiento_juridico": "X_INEXISTENTE"})()
        self.assertIsNone(dc._valores_permitidos_mecanismo(catalogo, sig))


class TestDerivarSignificado(unittest.TestCase):
    def test_grado_abstraccion_viene_de_profundidad_real(self):
        for prof, esperado in (("base", "CONCRETO"), ("media", "INTERMEDIO"), ("alta", "ABSTRACTO")):
            sig = dc.derivar_significado(candidato(profundidad=prof))
            self.assertEqual(sig.grado_abstraccion, esperado)

    def test_movimiento_juridico_viene_de_necesidad_real(self):
        casos = {"actuar": "TRANSFORMACION", "decidir": "RUPTURA_TENSION",
                "entender": "REVELACION", "cumplir": "CONSERVACION",
                "prevenir": "PREVENCION_UMBRAL", "acordar": "VINCULO",
                "distinguir": "CONTRASTE"}
        for nec, esperado in casos.items():
            sig = dc.derivar_significado(candidato(necesidad=nec))
            self.assertEqual(sig.movimiento_juridico, esperado)

    def test_las_15_necesidades_reales_tienen_categoria(self):
        import editorial
        universo = editorial.EditorialUniverse.load()
        for nec in universo.necesidades:
            sig = dc.derivar_significado(candidato(necesidad=nec))
            self.assertNotEqual(sig.movimiento_juridico, "SIN_CLASIFICAR", nec)

    def test_tension_es_literalmente_la_relacion_declarada(self):
        sig = dc.derivar_significado(candidato(relacion="oportunidad vs cierre"))
        self.assertEqual(sig.tension, "oportunidad vs cierre")

    def test_objeto_protagonista_queda_pendiente_no_se_fabrica(self):
        sig = dc.derivar_significado(candidato())
        self.assertEqual(sig.objeto_protagonista, "PENDIENTE_CONTENIDO")

    def test_es_determinista(self):
        c = candidato()
        self.assertEqual(dc.derivar_significado(c).to_dict(), dc.derivar_significado(c).to_dict())


class TestPalabrasClaveSonReales(unittest.TestCase):
    """Cada palabra clave debe existir de verdad en el vocabulario real del
    catálogo — nunca inventada."""

    def test_toda_palabra_clave_existe_en_el_catalogo_real(self):
        catalogo = MasterCatalog.load()
        pool = [dc._texto_libre(v) for v in catalogo.valores("visual_mechanism")]
        for categoria, palabras in dc.PALABRAS_CLAVE_MECANISMO.items():
            for p in palabras:
                clave = dc._texto_libre(p)
                self.assertTrue(clave, f"{categoria}: {p!r} normaliza a vacío")
                self.assertTrue(any(clave in v for v in pool),
                                f"{categoria}: {p!r} no aparece en ningún valor real de visual_mechanism")

    def test_cada_categoria_de_movimiento_produce_al_menos_un_valor_real(self):
        catalogo = MasterCatalog.load()
        for categoria in dc.PALABRAS_CLAVE_MECANISMO:
            sig = type("S", (), {"movimiento_juridico": categoria})()
            permitidos = dc._valores_permitidos_mecanismo(catalogo, sig)
            self.assertTrue(permitidos, categoria)

    def test_toda_categoria_de_realism_usa_valores_reales_del_catalogo(self):
        catalogo = MasterCatalog.load()
        pool = set(catalogo.valores("realism"))
        vistos = set()
        for _, valores in dc.REALISM_POR_GRADO.items():
            for v in valores:
                self.assertIn(v, pool, v)
                vistos.add(v)
        self.assertEqual(vistos, pool, "los 20 valores reales deben quedar cubiertos exactamente una vez")


class TestLaMateriaNoDeterminaElEstilo(unittest.TestCase):
    """Exigencia explícita del mandato: cambiar la materia, con todo lo
    demás igual, no debe cambiar la restricción causal — materia nunca
    entra a `derivar_significado()` ni a `_catalogo_causal()`."""

    def test_materia_no_es_parametro_de_ningun_paso_causal(self):
        import inspect
        self.assertNotIn("materia", inspect.signature(dc.derivar_significado).parameters)
        self.assertNotIn("materia", inspect.signature(dc._catalogo_causal).parameters)

    def test_misma_necesidad_y_profundidad_distinta_materia_mismo_filtro(self):
        catalogo = MasterCatalog.load()
        sig_civil = dc.derivar_significado(candidato(materia="civil", necesidad="actuar", profundidad="alta"))
        sig_penal = dc.derivar_significado(candidato(materia="penal", necesidad="actuar", profundidad="alta"))
        _, exp_civil = dc._catalogo_causal(catalogo, sig_civil)
        _, exp_penal = dc._catalogo_causal(catalogo, sig_penal)
        self.assertEqual(exp_civil, exp_penal)


class TestCambiarLaTensionCambiaLaPropuesta(unittest.TestCase):
    """Cambiar necesidad/profundidad (que codifican tensión/movimiento y
    grado de abstracción) debe poder cambiar el pool compatible, incluso
    con la misma materia."""

    def test_distinta_necesidad_misma_materia_distinto_pool_de_mecanismo(self):
        catalogo = MasterCatalog.load()
        sig_a = dc.derivar_significado(candidato(materia="civil", necesidad="actuar"))
        sig_b = dc.derivar_significado(candidato(materia="civil", necesidad="cumplir"))
        pool_a = set(dc._valores_permitidos_mecanismo(catalogo, sig_a))
        pool_b = set(dc._valores_permitidos_mecanismo(catalogo, sig_b))
        self.assertNotEqual(pool_a, pool_b)

    def test_distinta_profundidad_misma_materia_distinto_pool_de_realism(self):
        catalogo = MasterCatalog.load()
        sig_base = dc.derivar_significado(candidato(materia="civil", profundidad="base"))
        sig_alta = dc.derivar_significado(candidato(materia="civil", profundidad="alta"))
        pool_base = set(dc._valores_permitidos_realism(sig_base))
        pool_alta = set(dc._valores_permitidos_realism(sig_alta))
        self.assertEqual(pool_base & pool_alta, set())


class TestMecanismoPrecedeALaSeleccion(unittest.TestCase):
    """'La metáfora precede a la escuela/técnica' — aquí: el mecanismo
    visual requerido (derivado del movimiento jurídico) se fija ANTES de
    que la selección de huella toque nada; la selección sólo puede elegir
    DENTRO de lo ya permitido, nunca al revés."""

    def test_la_huella_elegida_siempre_respeta_el_pool_permitido(self):
        catalogo = MasterCatalog.load()
        for necesidad in ("actuar", "decidir", "entender", "cumplir", "prevenir", "acordar", "distinguir"):
            c = candidato(candidate_id=f"cid-{necesidad}", necesidad=necesidad)
            huella, sig, _ = dc.seleccionar_direccion_causal(c, catalogo=catalogo)
            permitidos = dc._valores_permitidos_mecanismo(catalogo, sig)
            if permitidos:
                self.assertIn(huella.visual_mechanism, permitidos)


class TestMemoriaEvitaRepeticion(unittest.TestCase):
    def test_dos_candidatos_consecutivos_con_mismo_significado_no_repiten_todo(self):
        catalogo = MasterCatalog.load()
        memoria = FingerprintMemory()
        c1 = candidato(candidate_id="c1", necesidad="entender", profundidad="alta")
        c2 = candidato(candidate_id="c2", necesidad="entender", profundidad="alta")
        h1, _, _ = dc.seleccionar_direccion_causal(c1, catalogo=catalogo, memoria=memoria)
        memoria.record(c1.candidate_id, h1)
        h2, _, _ = dc.seleccionar_direccion_causal(c2, catalogo=catalogo, memoria=memoria)
        # mismo significado -> mismo pool permitido, pero la huella completa
        # (10 dimensiones) no puede ser idéntica por la anti-repetición ya
        # probada en visual_fingerprint.py.
        self.assertNotEqual(h1.to_dict(), h2.to_dict())


class TestDeterminismoYDiversidad(unittest.TestCase):
    def test_mismo_content_id_mismo_significado_es_reproducible(self):
        catalogo = MasterCatalog.load()
        c = candidato(candidate_id="det-1", necesidad="reflexionar", profundidad="media")
        h1, s1, _ = dc.seleccionar_direccion_causal(c, catalogo=catalogo)
        h2, s2, _ = dc.seleccionar_direccion_causal(c, catalogo=catalogo)
        self.assertEqual(h1.to_dict(), h2.to_dict())
        self.assertEqual(s1.to_dict(), s2.to_dict())

    def test_diez_candidatos_reales_no_repiten_la_misma_direccion(self):
        catalogo = MasterCatalog.load()
        memoria = FingerprintMemory()
        reserva = universe.build_reserve(objetivo_lote=10, seed=777, factor=15)[:10]
        direcciones = []
        for c in reserva:
            h, _, _ = dc.seleccionar_direccion_causal(c, catalogo=catalogo, memoria=memoria)
            memoria.record(c.candidate_id, h)
            direcciones.append(h.primary_direction)
        self.assertEqual(len(set(direcciones)), len(direcciones), direcciones)

    def test_diversidad_real_entre_tandas(self):
        catalogo = MasterCatalog.load()
        resultados = []
        for seed in (901, 902, 903):
            memoria = FingerprintMemory()
            reserva = universe.build_reserve(objetivo_lote=5, seed=seed, factor=15)[:5]
            huellas = []
            for c in reserva:
                h, _, _ = dc.seleccionar_direccion_causal(c, catalogo=catalogo, memoria=memoria)
                memoria.record(c.candidate_id, h)
                huellas.append((h.realism, h.visual_mechanism))
            resultados.append(huellas)
        self.assertNotEqual(resultados[0], resultados[1])
        self.assertNotEqual(resultados[1], resultados[2])


class TestUnaSolaDireccionNoDomina(unittest.TestCase):
    def test_en_un_lote_real_ninguna_direccion_es_mayoria(self):
        catalogo = MasterCatalog.load()
        memoria = FingerprintMemory()
        reserva = universe.build_reserve(objetivo_lote=10, seed=888, factor=15)[:10]
        primarias = []
        for c in reserva:
            h, _, _ = dc.seleccionar_direccion_causal(c, catalogo=catalogo, memoria=memoria)
            memoria.record(c.candidate_id, h)
            primarias.append(h.primary_direction)
        from collections import Counter
        conteo = Counter(primarias)
        self.assertLessEqual(conteo.most_common(1)[0][1], 2, conteo)


class TestNuncaLanzaExcepcionPorDatoFaltante(unittest.TestCase):
    def test_necesidad_desconocida_no_rompe_la_seleccion(self):
        c = candidato(necesidad="necesidad-inexistente-xyz")
        huella, sig, exp = dc.seleccionar_direccion_causal(c)
        self.assertEqual(sig.movimiento_juridico, "SIN_CLASIFICAR")
        self.assertTrue(huella.visual_mechanism)  # sigue eligiendo, sin restricción

    def test_profundidad_desconocida_no_rompe_la_seleccion(self):
        c = candidato(profundidad="profundidad-inexistente")
        huella, sig, exp = dc.seleccionar_direccion_causal(c)
        self.assertEqual(sig.grado_abstraccion, "SIN_CLASIFICAR")
        self.assertTrue(huella.realism)


if __name__ == "__main__":
    unittest.main()
