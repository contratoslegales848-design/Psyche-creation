"""Safe zone multiformato 9:16 -> 4:5 (tarea 78, 17-sep-2026).

Regla canónica: "9:16 visualmente amplio; 4:5 semánticamente completo".
Cubre las 5 propiedades del mandato: geometría, contenido crítico,
formatos, regresión y determinismo."""

import unittest

import safe_zone as sz
from brief import VisualBrief, VisualPolicy
from compiler import compile_request


class SafeZoneBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy = VisualPolicy.load()
        cls.geo = sz.calcular_geometria(cls.policy)

    def brief(self, formato="VERTICAL_9_16", **over):
        base = dict(
            content_id="x", formato=formato, visual_family="oleo_cinematografico",
            subject="una placa de bronce con un nombre a medio borrar",
            environment="archivo corporativo con estantes de expedientes",
            camera="50mm, plano cerrado", focal_point="el nombre a medio borrar",
            metaphor="una firma que se disuelve en la institucion",
            acento_objeto="un sello corporativo de metal sin usar",
            marca_superficie="placa de bronce")
        base.update(over)
        return VisualBrief(**base)


class TestGeometria(SafeZoneBase):
    def test_el_canvas_9_16_contiene_un_crop_central_4_5(self):
        self.assertEqual((self.geo.canvas_width, self.geo.canvas_height), (1080, 1920))
        self.assertEqual((self.geo.crop_width, self.geo.crop_height), (1080, 1350))
        self.assertEqual(self.geo.crop_width, self.geo.canvas_width,
                         "el recorte central conserva todo el ancho.")
        self.assertLess(self.geo.crop_height, self.geo.canvas_height)

    def test_offsets_top_y_bottom_son_correctos_y_simetricos(self):
        self.assertEqual(self.geo.crop_offset_top, self.geo.crop_offset_bottom)
        self.assertEqual(self.geo.crop_offset_top, 285)
        self.assertEqual(self.geo.crop_top, 285)
        self.assertEqual(self.geo.crop_bottom, 1635)

    def test_safe_zone_interna_es_coherente(self):
        # margen interno adicional: la safe zone es estrictamente MAS
        # pequeña que el crop bruto — nunca coincide con su borde exacto.
        self.assertGreater(self.geo.safe_top, self.geo.crop_top)
        self.assertLess(self.geo.safe_bottom, self.geo.crop_bottom)
        self.assertGreater(self.geo.safe_height, 0)
        self.assertLess(self.geo.safe_height, self.geo.crop_height)

    def test_padding_interno_viene_de_la_politica_no_hardcodeado_aparte(self):
        ratio_politico = self.policy.data["safe_zone"]["padding_interno_ratio"]
        self.assertEqual(self.geo.padding_interno_ratio, ratio_politico)
        self.assertEqual(self.geo.padding_interno_px, int(self.geo.crop_height * ratio_politico))

    def test_formato_sin_crop_safe_for_lanza_error_explicito(self):
        with self.assertRaises(sz.SafeZoneError):
            sz.calcular_geometria(self.policy, formato_maestro="SOCIAL_4_5",
                                  formato_crop="VERTICAL_9_16")

    def test_recorte_mas_alto_que_el_maestro_lanza_error(self):
        class PolicyFalsa:
            data = {"formatos": {"A": {"width": 1080, "height": 1000, "crop_safe_for": "B"},
                                 "B": {"width": 1080, "height": 1200}}}

            def formato(self, nombre):
                return self.data["formatos"][nombre]

        with self.assertRaises(sz.SafeZoneError):
            sz.calcular_geometria(PolicyFalsa(), formato_maestro="A")

    def test_recorte_con_ancho_distinto_lanza_error(self):
        class PolicyFalsa:
            data = {"formatos": {"A": {"width": 1080, "height": 1920, "crop_safe_for": "B"},
                                 "B": {"width": 900, "height": 1350}}}

            def formato(self, nombre):
                return self.data["formatos"][nombre]

        with self.assertRaises(sz.SafeZoneError):
            sz.calcular_geometria(PolicyFalsa(), formato_maestro="A")


class TestContenidoCritico(SafeZoneBase):
    def test_elementos_criticos_dentro_de_safe_zone_pasa(self):
        ok, codes, _ = sz.crop_safe_4_5(self.brief(), policy=self.policy, geometria=self.geo)
        self.assertTrue(ok)
        self.assertEqual(codes, [])

    def test_titulo_esencial_marcado_extremo_superior_falla(self):
        """FAIL del mandato: 'título marcado como esencial + placement extremo superior'."""
        b = self.brief(subject="el titulo pegado arriba de toda la composicion")
        ok, codes, detalle = sz.crop_safe_4_5(b, policy=self.policy, geometria=self.geo)
        self.assertFalse(ok)
        self.assertIn("subject", detalle["campos_esenciales_en_riesgo"])
        self.assertTrue(any("EXTREMO_SUPERIOR" in c for c in codes))

    def test_explicacion_esencial_extremo_inferior_falla(self):
        """FAIL del mandato: 'explicación esencial extrema inferior'."""
        b = self.brief(focal_point="el documento resuelto en el borde inferior extremo")
        ok, codes, detalle = sz.crop_safe_4_5(b, policy=self.policy, geometria=self.geo)
        self.assertFalse(ok)
        self.assertIn("focal_point", detalle["campos_esenciales_en_riesgo"])
        self.assertTrue(any("EXTREMO_INFERIOR" in c for c in codes))

    def test_elemento_critico_declarado_fuera_del_crop_falla(self):
        b = self.brief(metaphor="una metafora que queda fuera del recorte")
        ok, codes, detalle = sz.crop_safe_4_5(b, policy=self.policy, geometria=self.geo)
        self.assertFalse(ok)
        self.assertIn("metaphor", detalle["campos_esenciales_en_riesgo"])

    def test_marca_que_desaparece_en_4_5_falla_cuando_la_marca_es_requerida(self):
        b = self.brief(marca_superficie="placa que desaparece en 4:5")
        ok, codes, detalle = sz.crop_safe_4_5(b, policy=self.policy, geometria=self.geo)
        self.assertFalse(ok)
        self.assertIn("marca_superficie", detalle["campos_esenciales_en_riesgo"])
        self.assertTrue(any("MARCA_EN_ZONA_DE_RIESGO" in c for c in codes))

    def test_atmosfera_decorativa_fuera_del_encuadre_pasa(self):
        """PASS del mandato: 'extensiones solo atmosféricas' pueden vivir
        fuera de la zona segura sin que eso sea un fallo."""
        b = self.brief(environment="cielo que se pierde en el borde superior extremo, sin "
                                   "informacion relevante ahi")
        ok, codes, detalle = sz.crop_safe_4_5(b, policy=self.policy, geometria=self.geo)
        self.assertTrue(ok)
        self.assertIn("environment", detalle["campos_decorativos_en_extension"])

    def test_camara_decorativa_mencionando_zona_de_riesgo_pasa(self):
        b = self.brief(camera="picado extremo desde la parte superior extrema, fuera de campo")
        ok, _, detalle = sz.crop_safe_4_5(b, policy=self.policy, geometria=self.geo)
        self.assertTrue(ok)


class TestFormatos(SafeZoneBase):
    def test_una_pieza_9_16_puede_declarar_compatibilidad_4_5(self):
        fmt = self.policy.formato("VERTICAL_9_16")
        self.assertEqual(fmt.get("crop_safe_for"), "SOCIAL_4_5")

    def test_no_obliga_a_generar_un_segundo_asset(self):
        """El brief sigue siendo UN solo VisualBrief formato=VERTICAL_9_16 —
        crop_safe_4_5() no produce ni exige un segundo VisualBrief/asset."""
        b = self.brief()
        ok, _, detalle = sz.crop_safe_4_5(b, policy=self.policy, geometria=self.geo)
        self.assertEqual(b.formato, "VERTICAL_9_16")
        self.assertNotIn("segundo_brief", detalle)
        self.assertNotIn("segundo_asset", detalle)

    def test_formato_nativo_4_5_no_aplica_la_regla(self):
        """No se fuerza el formato pedido explícitamente: SOCIAL_4_5 no
        declara crop_safe_for, así que la regla se marca 'no aplica', nunca
        se rechaza ni se reinterpreta como VERTICAL_9_16."""
        b = self.brief(formato="SOCIAL_4_5")
        ok, codes, detalle = sz.crop_safe_4_5(b, policy=self.policy, geometria=None)
        self.assertTrue(ok)
        self.assertFalse(detalle["aplica"])
        self.assertEqual(codes, [])

    def test_compile_request_no_instruye_safe_zone_para_formato_sin_crop_safe_for(self):
        b = self.brief(formato="SOCIAL_4_5")
        r = compile_request(b, self.policy)
        self.assertNotIn("safe_zone_geometry", r.metadata)
        self.assertNotIn("área central segura", r.positive_prompt)


class TestRegresion(SafeZoneBase):
    def test_compile_request_con_brief_real_sigue_compilando(self):
        b = self.brief()
        r = compile_request(b, self.policy)
        self.assertTrue(r.positive_prompt)
        self.assertTrue(r.crop_safe_4_5_ok)

    def test_el_campo_es_informativo_nunca_bloquea_la_compilacion(self):
        """Aunque crop_safe_4_5 falle, compile_request() NO lanza excepción
        — mismo patrón no-exclusión-silenciosa que memoria_fuerte_ok."""
        b = self.brief(subject="el titulo pegado arriba de todo")
        r = compile_request(b, self.policy)
        self.assertFalse(r.crop_safe_4_5_ok)
        self.assertTrue(r.positive_prompt)

    def test_diversidad_artistica_no_se_ve_afectada(self):
        """La instrucción de safe zone se añade al prompt, pero la
        dirección artística (fingerprint) sigue siendo la del catálogo
        maestro, no una versión reducida/forzada a centrado."""
        import visual_fingerprint as vf
        catalogo = vf.MasterCatalog.load()
        memoria = vf.FingerprintMemory()
        huella = vf.seleccionar_huella("safe-zone-regresion", catalogo=catalogo, memoria=memoria)
        b = self.brief()
        r = compile_request(b, self.policy, fingerprint=huella)
        self.assertIn(huella.primary_direction, r.positive_prompt)
        self.assertNotIn("sujeto centrado", r.positive_prompt.lower())
        self.assertNotIn("fondo vacio", r.positive_prompt.lower())


class TestDeterminismo(SafeZoneBase):
    def test_misma_entrada_produce_la_misma_geometria(self):
        geo1 = sz.calcular_geometria(self.policy)
        geo2 = sz.calcular_geometria(self.policy)
        self.assertEqual(geo1.to_dict(), geo2.to_dict())

    def test_misma_entrada_produce_la_misma_instruccion(self):
        i1 = sz.instruccion_compilada(self.geo)
        i2 = sz.instruccion_compilada(self.geo)
        self.assertEqual(i1, i2)

    def test_mismo_brief_produce_el_mismo_veredicto_crop_safe(self):
        b1, b2 = self.brief(), self.brief()
        r1 = sz.crop_safe_4_5(b1, policy=self.policy, geometria=self.geo)
        r2 = sz.crop_safe_4_5(b2, policy=self.policy, geometria=self.geo)
        self.assertEqual(r1[0], r2[0])
        self.assertEqual(r1[1], r2[1])

    def test_mismo_brief_produce_el_mismo_prompt_compilado(self):
        b1, b2 = self.brief(), self.brief()
        r1 = compile_request(b1, self.policy)
        r2 = compile_request(b2, self.policy)
        self.assertEqual(r1.positive_prompt, r2.positive_prompt)
        self.assertEqual(r1.request_hash(), r2.request_hash())


class TestNormalizaTextoLibreConDosPuntos(unittest.TestCase):
    """Regresión puntual: safe_zone.py necesita comparar frases con
    proporciones ('4:5') — memory.normaliza_texto_libre() debe tratar ':'
    como separador, igual que '-'/'_'/'/'."""

    def test_dos_puntos_se_tratan_como_separador(self):
        from memory import normaliza_texto_libre
        self.assertEqual(normaliza_texto_libre("desaparece en 4:5"), "desaparece en 4 5")
        self.assertIn("4", normaliza_texto_libre("desaparece en 4:5"))
        self.assertIn("5", normaliza_texto_libre("desaparece en 4:5"))


if __name__ == "__main__":
    unittest.main()
