"""Tabla real CONCEPTO -> DIRECCIÓN ARTÍSTICA con evidencia empírica
(autorización del Founder, 18-sep-2026). Casos normal/límite/adversarial
sobre `concepto_direccion.py` y su wiring en `direccion_causal.py`/
`art_direction.py`."""

import unittest

import art_direction as ad
import concepto_direccion as cd
import direccion_causal as dc
import memoria_fuerte as mf
import universe
from visual_fingerprint import MasterCatalog


def candidato(**kw):
    base = dict(candidate_id="X", materia="civil", submateria="s",
               familia_editorial="concepto", necesidad="entender", rol_lector="persona",
               angulo="a", contexto_funcional="c", profundidad="base", formato="frase",
               concepto_nucleo="n", relacion="r", pregunta_resuelta="p")
    base.update(kw)
    return universe.TopicCandidate(**base)


class TestTablaEsEvidenciaRealNoInventada(unittest.TestCase):
    def test_la_tabla_tiene_exactamente_4_filas(self):
        """De las 16 piezas reales de memoria fuerte, sólo 4 documentan
        `direccion_artistica` -- verificado por grep directo sobre
        memoria_fuerte.py, no una cifra elegida a mano."""
        self.assertEqual(len(cd.TABLA_CONCEPTO_DIRECCION), 4)

    def test_cada_fila_cita_un_content_id_real_de_memoria_fuerte(self):
        ids_reales = {r["content_id"] for r in
                     list(mf.PIEZAS_PUBLICADAS) + list(mf.PIEZAS_PRESELECCIONADAS)}
        for evidencia in cd.TABLA_CONCEPTO_DIRECCION:
            self.assertIn(evidencia.content_id, ids_reales)

    def test_la_direccion_artistica_es_texto_verbatim_de_la_fuente(self):
        carnelutti = next(e for e in cd.TABLA_CONCEPTO_DIRECCION
                          if e.content_id == "MF-10-CARNELUTTI")
        self.assertEqual(carnelutti.direccion_artistica,
                         "pergamino dorado con cita larga legible")

    def test_ninguna_fila_sin_direccion_artistica_entra_a_la_tabla(self):
        """MF-01 (servidumbre de paso, la pieza MÁS VIRAL) no tiene
        direccion_artistica documentada -- no debe aparecer, por muy
        importante que sea la pieza en otros aspectos."""
        ids_tabla = {e.content_id for e in cd.TABLA_CONCEPTO_DIRECCION}
        self.assertNotIn("MF-01-SERVIDUMBRE-PASO", ids_tabla)

    def test_la_tabla_no_documenta_tension_ni_metafora(self):
        """Honestidad declarada del módulo: la fuente real no tiene esos
        dos eslabones para ninguna pieza -- no se fabrican para completar
        la forma de 4 eslabones que el mandato imaginó."""
        self.assertNotIn("tension", cd.EvidenciaConceptoDireccion.__dataclass_fields__)
        self.assertNotIn("metafora", cd.EvidenciaConceptoDireccion.__dataclass_fields__)


class TestBuscarEvidenciaConceptoCasoNormal(unittest.TestCase):
    def test_concepto_identico_a_uno_real_encuentra_evidencia(self):
        evidencia, similitud = cd.buscar_evidencia_concepto(
            "el abogado no defiende al culpable ni al inocente: defiende al hombre")
        self.assertIsNotNone(evidencia)
        self.assertEqual(evidencia.content_id, "MF-10-CARNELUTTI")
        self.assertEqual(similitud, 1.0)

    def test_concepto_muy_parecido_tambien_encuentra_evidencia(self):
        """Sin ser idéntico -- parafraseado real, mismo núcleo temático."""
        evidencia, similitud = cd.buscar_evidencia_concepto(
            "el abogado no defiende al inocente ni al culpable: defiende al hombre y su dignidad")
        self.assertIsNotNone(evidencia)
        self.assertEqual(evidencia.content_id, "MF-10-CARNELUTTI")
        self.assertGreaterEqual(similitud, cd.UMBRAL_COINCIDENCIA_CONCEPTO)


class TestBuscarEvidenciaConceptoCasoLimite(unittest.TestCase):
    def test_concepto_sin_relacion_no_encuentra_evidencia(self):
        evidencia, similitud = cd.buscar_evidencia_concepto(
            "la responsabilidad civil por hecho ajeno en el trabajo domestico")
        self.assertIsNone(evidencia)
        self.assertLess(similitud, cd.UMBRAL_COINCIDENCIA_CONCEPTO)

    def test_concepto_vacio_no_rompe_nada(self):
        evidencia, similitud = cd.buscar_evidencia_concepto("")
        self.assertIsNone(evidencia)
        self.assertEqual(similitud, 0.0)

    def test_tabla_vacia_no_rompe_nada(self):
        evidencia, similitud = cd.buscar_evidencia_concepto("cualquier cosa", tabla=())
        self.assertIsNone(evidencia)
        self.assertEqual(similitud, 0.0)

    def test_direcciones_informadas_puede_ser_vacia_de_verdad(self):
        """Onassis: su dirección artística histórica ('retrato con frase en
        mayúsculas bold superpuesta') no comparte ninguna palabra real con
        el catálogo maestro de 504 direcciones -- resultado honesto, no un
        error del mecanismo."""
        catalogo = MasterCatalog.load()
        onassis = next(e for e in cd.TABLA_CONCEPTO_DIRECCION if e.content_id == "MF-11-ONASSIS")
        self.assertEqual(cd.direcciones_informadas_por_evidencia(catalogo, onassis), [])

    def test_direcciones_informadas_no_vacia_cuando_hay_vocabulario_real(self):
        catalogo = MasterCatalog.load()
        carnelutti = next(e for e in cd.TABLA_CONCEPTO_DIRECCION
                          if e.content_id == "MF-10-CARNELUTTI")
        informadas = cd.direcciones_informadas_por_evidencia(catalogo, carnelutti)
        self.assertTrue(informadas)
        # todas las entradas devueltas son reales del catálogo, no inventadas.
        todas_reales = set(catalogo.todas_las_direcciones())
        for par in informadas:
            self.assertIn(par, todas_reales)


class TestCoberturaEsPrecisaNoInflada(unittest.TestCase):
    def test_cobertura_reporta_16_piezas_fuente_y_4_con_direccion(self):
        c = cd.cobertura()
        self.assertEqual(c["piezas_fuente_5"], 16)
        self.assertEqual(c["piezas_con_direccion_artistica_documentada"], 4)
        self.assertEqual(c["ratio_piezas_con_evidencia"], 0.25)

    def test_cobertura_nunca_afirma_cubrir_el_catalogo_completo(self):
        c = cd.cobertura()
        self.assertIn("504", str(c["total_direcciones_catalogo_maestro"]))
        self.assertIn("NO cubre el catálogo maestro", c["nota"])


class TestSeleccionCausalCasoNormalConEvidencia(unittest.TestCase):
    """El concepto del candidato coincide con evidencia real -> la
    selección de primary_direction/secondary_direction se restringe al
    vocabulario informado, y Significado lo deja auditable."""

    def test_evidencia_se_expone_en_significado(self):
        catalogo = MasterCatalog.load()
        c = candidato(
            concepto_nucleo="el abogado no defiende al culpable ni al inocente: defiende al hombre")
        huella, sig, exp = dc.seleccionar_direccion_causal(
            c, catalogo=catalogo, tabla_concepto_direccion=cd.TABLA_CONCEPTO_DIRECCION)
        self.assertEqual(sig.evidencia_concepto_id, "MF-10-CARNELUTTI")
        self.assertEqual(sig.evidencia_concepto_similitud, 1.0)
        self.assertEqual(sig.evidencia_concepto_direccion_artistica,
                         "pergamino dorado con cita larga legible")

    def test_la_huella_elegida_respeta_el_pool_informado(self):
        catalogo = MasterCatalog.load()
        c = candidato(
            concepto_nucleo="el abogado no defiende al culpable ni al inocente: defiende al hombre")
        huella, sig, exp = dc.seleccionar_direccion_causal(
            c, catalogo=catalogo, tabla_concepto_direccion=cd.TABLA_CONCEPTO_DIRECCION)
        carnelutti = next(e for e in cd.TABLA_CONCEPTO_DIRECCION
                          if e.content_id == "MF-10-CARNELUTTI")
        informadas = {e for _, e in cd.direcciones_informadas_por_evidencia(catalogo, carnelutti)}
        self.assertIn(huella.primary_direction, informadas)

    def test_la_explicacion_documenta_la_fuente_y_el_rendimiento(self):
        catalogo = MasterCatalog.load()
        c = candidato(
            concepto_nucleo="el abogado no defiende al culpable ni al inocente: defiende al hombre")
        _, _, exp = dc.seleccionar_direccion_causal(
            c, catalogo=catalogo, tabla_concepto_direccion=cd.TABLA_CONCEPTO_DIRECCION)
        texto = " ".join(exp)
        self.assertIn("MF-10-CARNELUTTI", texto)
        self.assertIn("memoria fuerte real", texto)


class TestSeleccionCausalCasoLimiteSinEvidencia(unittest.TestCase):
    """Sin evidencia real (concepto no relacionado, o tabla no pasada):
    cero cambio de comportamiento respecto a antes de este módulo."""

    def test_sin_tabla_comportamiento_identico_al_de_siempre(self):
        catalogo = MasterCatalog.load()
        c = candidato(concepto_nucleo="usucapión y prescripción adquisitiva de dominio")
        huella, sig, _ = dc.seleccionar_direccion_causal(c, catalogo=catalogo)
        self.assertEqual(sig.evidencia_concepto_id, "")
        self.assertEqual(sig.evidencia_concepto_similitud, 0.0)

    def test_concepto_no_relacionado_con_tabla_pasada_no_encuentra_nada(self):
        catalogo = MasterCatalog.load()
        c = candidato(concepto_nucleo="usucapión y prescripción adquisitiva de dominio")
        huella, sig, exp = dc.seleccionar_direccion_causal(
            c, catalogo=catalogo, tabla_concepto_direccion=cd.TABLA_CONCEPTO_DIRECCION)
        self.assertEqual(sig.evidencia_concepto_id, "")
        self.assertIn("sin evidencia", " ".join(exp).lower())

    def test_direcciones_disponibles_no_se_reducen_sin_evidencia(self):
        """El catálogo completo (504 direcciones) sigue abierto -- no se
        restringe nada cuando no hay evidencia real de concepto."""
        catalogo = MasterCatalog.load()
        c = candidato(concepto_nucleo="usucapión y prescripción adquisitiva de dominio")
        catalogo_causal, _ = dc._catalogo_causal(catalogo, dc.derivar_significado(c), None)
        self.assertEqual(len(catalogo_causal.todas_las_direcciones()),
                         len(catalogo.todas_las_direcciones()))

    def test_evidencia_encontrada_pero_sin_vocabulario_no_restringe(self):
        """Caso intermedio real: Onassis SÍ coincide como concepto, pero su
        dirección histórica no comparte vocabulario con el catálogo -- el
        pool debe quedar tan abierto como sin evidencia."""
        catalogo = MasterCatalog.load()
        onassis = next(e for e in cd.TABLA_CONCEPTO_DIRECCION if e.content_id == "MF-11-ONASSIS")
        c = candidato(concepto_nucleo=onassis.concepto_nucleo)
        catalogo_causal, exp = dc._catalogo_causal(catalogo, dc.derivar_significado(c), onassis)
        self.assertEqual(len(catalogo_causal.todas_las_direcciones()),
                         len(catalogo.todas_las_direcciones()))
        self.assertIn("no se restringe", " ".join(exp).lower())


class TestAdversarial(unittest.TestCase):
    """La tabla NUNCA gana contra una regla ya vigente de rechazo o de
    memoria fuerte -- sólo puede influir en QUÉ direcciones se consideran
    ANTES de seleccionar; los bloqueos corren después, sin cambios."""

    def test_memoria_fuerte_sigue_bloqueando_aunque_la_tabla_informe_la_misma_pieza(self):
        """El intento más directo de 'ganarle' a memoria fuerte: pedir
        exactamente el concepto de MF-10 con la tabla activa. La tabla SÍ
        informa (y hasta guía) la dirección hacia el vocabulario histórico
        de Carnelutti -- pero memoria_fuerte.evaluar() debe bloquear la
        repetición de todos modos, exactamente como si la tabla no
        existiera."""
        import emotion
        memoria_fuerte_real = mf.cargar_memoria_fuerte()
        # Réplica fiel de los campos EJES_SEMANTICOS reales de MF-10 (materia,
        # submateria, concepto_nucleo) — el resto queda vacío como en la
        # fuente, para que la comparación sea comparable de verdad (ver
        # semantic_fingerprint._similitud: un lado con dato y el otro sin
        # él cuenta como diferencia, no como "sin evidencia").
        c = candidato(
            candidate_id="ADV-1", materia="historia_del_derecho", submateria="juristas",
            familia_editorial="", necesidad="", rol_lector="", angulo="", contexto_funcional="",
            relacion="", pregunta_resuelta="",
            concepto_nucleo="el abogado no defiende al culpable ni al inocente: defiende al hombre")
        perfil = emotion.derivar(necesidad=c.necesidad, familia_editorial=c.familia_editorial).to_dict()

        draft_sin_tabla = ad.draft_visual_brief(c, perfil, memoria_fuerte=memoria_fuerte_real)
        draft_con_tabla = ad.draft_visual_brief(
            c, perfil, memoria_fuerte=memoria_fuerte_real,
            tabla_concepto_direccion=cd.TABLA_CONCEPTO_DIRECCION)

        self.assertTrue(draft_sin_tabla.bloqueado_memoria_fuerte)
        self.assertTrue(draft_con_tabla.bloqueado_memoria_fuerte,
                        "la tabla de evidencia no puede desbloquear una repetición real")

    def test_regla_de_rechazo_del_founder_bloquea_aunque_el_pool_este_restringido_a_esa_direccion(self):
        """Construcción directa: un catálogo minúsculo cuya ÚNICA dirección
        disponible es justo una que dispara RECHAZO-4 (flat illustration +
        bold) -- la huella resultante SIEMPRE cae en esa dirección (no hay
        otra opción en el pool), y aun así verificar_rechazos_founder()
        debe seguir bloqueándola. Demuestra que restringir el pool nunca
        desactiva el chequeo posterior, que es independiente."""
        catalogo_pequeno = MasterCatalog(
            direcciones={"digital": ["flat illustration bold"]},
            auxiliares={dim: ["valor real"] for dim in
                       ("lighting", "composition", "camera_optics", "palette",
                        "materiality", "realism", "visual_mechanism")})
        evidencia_sintetica = cd.EvidenciaConceptoDireccion(
            content_id="TEST-SOLO-PARA-ESTE-CASO", concepto_nucleo="cualquier concepto de prueba",
            materia="civil", direccion_artistica="flat illustration bold")
        huella, sig, exp = dc.seleccionar_direccion_causal(
            candidato(concepto_nucleo="cualquier concepto de prueba"),
            catalogo=catalogo_pequeno,
            tabla_concepto_direccion=(evidencia_sintetica,))
        self.assertEqual(huella.primary_direction, "flat illustration bold")
        violaciones = mf.verificar_rechazos_founder(huella)
        self.assertTrue(violaciones, "RECHAZO-4 debe seguir disparando pese a que el pool "
                                    "informado por la tabla sólo ofrecía esa dirección")
        self.assertTrue(any("RECHAZO-4" in v for v in violaciones))


if __name__ == "__main__":
    unittest.main()
