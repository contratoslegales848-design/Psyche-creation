"""El almacen tiene que negarse. Estas pruebas comprueban las negativas.

Una prueba que solo verifica el camino feliz no dice nada de un sistema
fail-closed: lo que hay que demostrar es que una pieza incompleta NO entra.
Por eso casi todas estas pruebas parten de una pieza valida y le QUITAN una
cosa, comprobando que el rechazo aparece — la mutacion la hace la prueba, no
la esperanza.

Tres cosas mas que se comprueban aqui y no son obvias:
  - Que la barrera de Python y las restricciones SQL de la migracion dicen lo
    MISMO. Si divergen, la divergencia es el fallo.
  - Que sin variables de entorno el estado es CONFIGURATION_REQUIRED y nunca
    se simula una conexion.
  - Que el seed sintetico es realmente sintetico (nada de dominios reales,
    ninguna persona).

Sin red. Sin base de datos. Determinista.
"""

import copy
import re
import sys
import unittest
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))

import config  # noqa: E402
import fail_closed  # noqa: E402
import seed_sintetico  # noqa: E402

MIGRACION = (AQUI / "migrations" / "0001_almacen_piezas_aprobadas.sql").read_text(encoding="utf-8")


def pieza_valida():
    return copy.deepcopy(seed_sintetico.pieza_con_gate_abierto())


def pieza_bloqueada():
    return copy.deepcopy(seed_sintetico.pieza_bloqueada())


class TestElCaminoFelizExiste(unittest.TestCase):
    """Si nada pasa nunca, el sistema no es estricto: esta roto."""

    def test_la_pieza_completa_se_acepta(self):
        self.assertEqual(fail_closed.revisar_pieza(pieza_valida()), [])

    def test_la_pieza_bloqueada_tambien_es_escribible(self):
        """Registrar una pieza con el gate cerrado es legitimo y necesario:
        el almacen guarda el trabajo en curso, no solo lo aprobado."""
        self.assertEqual(fail_closed.revisar_pieza(pieza_bloqueada()), [])


class TestSinLoImprescindibleNoEntra(unittest.TestCase):
    """Requisito 5: sin fuente, jurisdiccion, hash, claim, evidencia,
    aprobacion humana o estado requerido, no se guarda como aprobada."""

    def _rechaza(self, pieza, fragmento):
        motivos = fail_closed.revisar_pieza(pieza)
        self.assertTrue(motivos, "la pieza deberia haber sido rechazada")
        self.assertTrue(any(fragmento.lower() in m.lower() for m in motivos),
                        f"ningun motivo menciona {fragmento!r}: {motivos}")

    def test_sin_claims_no_entra(self):
        p = pieza_valida(); p["claims"] = []
        self._rechaza(p, "ningun claim")

    def test_sin_fuentes_no_entra(self):
        p = pieza_valida(); p["claims"][0]["fuentes"] = []
        self._rechaza(p, "sin ninguna fuente")

    def test_sin_hash_no_abre_el_gate(self):
        p = pieza_valida(); p["contenido_hash_sha256"] = None
        self._rechaza(p, "sin contenido_hash_sha256")

    def test_sin_aprobacion_humana_no_abre_el_gate(self):
        p = pieza_valida()
        p["claims"][0]["revision_estado"] = "PENDIENTE"
        self._rechaza(p, "gate_arte ABIERTO sin la conjuncion exigida")

    def test_aprobacion_sin_revisor_no_entra(self):
        p = pieza_valida(); p["claims"][0]["revision_revisor"] = ""
        self._rechaza(p, "aprobacion humana incompleta")

    def test_aprobacion_sin_fecha_no_entra(self):
        p = pieza_valida(); p["claims"][0]["revision_fecha"] = None
        self._rechaza(p, "aprobacion humana incompleta")

    def test_aprobacion_sin_hash_no_entra(self):
        p = pieza_valida(); p["claims"][0]["revision_hash_sha256"] = None
        self._rechaza(p, "aprobacion humana incompleta")

    def test_hash_con_forma_invalida_no_entra(self):
        p = pieza_valida(); p["claims"][0]["revision_hash_sha256"] = "no-es-un-hash"
        self._rechaza(p, "no es sha256")

    def test_estado_no_apto_no_abre_el_gate(self):
        p = pieza_valida(); p["claims"][0]["estado"] = "APTO_CON_MATICES"
        self._rechaza(p, "gate_arte ABIERTO sin la conjuncion exigida")

    def test_apto_sin_fuente_de_nivel_1_no_entra(self):
        p = pieza_valida()
        for f in p["claims"][0]["fuentes"]:
            f["texto_exacto_consultado"] = False
        self._rechaza(p, "sin ninguna fuente de Nivel 1")

    def test_fuente_oficial_sin_registro_no_alcanza_nivel_1(self):
        """Una fuente oficial cuyo organismo no esta en el registro cerrado no
        puede sostener el nivel maximo, aunque los tres booleanos sean true."""
        p = pieza_valida()
        for f in p["claims"][0]["fuentes"]:
            f["registro_oficial_id"] = None
        self._rechaza(p, "sin registro_oficial_id")

    def test_fuente_oficial_sin_localizador_no_entra(self):
        p = pieza_valida(); p["claims"][0]["fuentes"][0]["localizador"] = ""
        self._rechaza(p, "sin localizador concreto")

    def test_comprobado_sin_fecha_no_entra(self):
        p = pieza_valida(); p["claims"][0]["fuentes"][0]["fecha_comprobacion"] = None
        self._rechaza(p, "sin fecha_comprobacion")


class TestJurisdiccion(unittest.TestCase):
    def test_capa_c_sin_pais_no_entra(self):
        p = pieza_valida()
        c = p["claims"][0]
        c["alcance"] = "CAPA_C_NACIONAL"
        c["jurisdiccion"] = []
        motivos = fail_closed.revisar_pieza(p)
        self.assertTrue(any("sin jurisdiccion declarada" in m for m in motivos), motivos)

    def test_capa_a_con_menos_de_tres_jurisdicciones_no_entra(self):
        """La falsa universalizacion que el resto del sistema ya vigila,
        vigilada tambien en el almacen."""
        p = pieza_valida()
        p["claims"][0]["jurisdiccion"] = ["Sinteticolandia"]
        motivos = fail_closed.revisar_pieza(p)
        self.assertTrue(any("minimo comparado" in m for m in motivos), motivos)


class TestElTechoEsElMinimo(unittest.TestCase):
    def test_un_claim_cerrado_cierra_la_pieza(self):
        """El gate global es el minimo de sus claims, nunca el maximo."""
        p = pieza_valida()
        p["claims"].append({
            **copy.deepcopy(p["claims"][0]),
            "claim_id": "LM-SINTETICO-002-claim-2",
            "estado": "REQUIERE_INVESTIGACION",
            "gate_arte": "CERRADO",
            "revision_estado": "PENDIENTE",
        })
        motivos = fail_closed.revisar_pieza(p)
        self.assertTrue(any("minimo de sus claims" in m for m in motivos), motivos)


class TestPublicacion(unittest.TestCase):
    """Publicar es un cuarto estado: aprobar no autoriza publicar."""

    def _publicada(self, **cambios):
        p = pieza_valida()
        p["publicacion"] = "PUBLISHED"
        d = p["derivadas"][0]
        d.update({"publicada_en": "2026-09-03T12:00:00Z",
                  "url_publicada": "https://example.invalid/pieza",
                  "autorizacion_publicacion": "AUTORIZADA",
                  "autorizacion_responsable": "rol:autorizador-sintetico",
                  "autorizacion_fecha": "2026-09-03T11:00:00Z"})
        d.update(cambios)
        return p

    def test_publicada_completa_se_acepta(self):
        self.assertEqual(fail_closed.revisar_pieza(self._publicada()), [])

    def test_published_sin_derivada_publicada_no_entra(self):
        p = pieza_valida(); p["publicacion"] = "PUBLISHED"
        motivos = fail_closed.revisar_pieza(p)
        self.assertTrue(any("sin ninguna derivada publicada" in m for m in motivos), motivos)

    def test_publicada_sin_autorizacion_humana_no_entra(self):
        motivos = fail_closed.revisar_pieza(
            self._publicada(autorizacion_publicacion="PENDIENTE"))
        self.assertTrue(any("sin autorizacion humana" in m for m in motivos), motivos)

    def test_publicada_sin_responsable_no_entra(self):
        motivos = fail_closed.revisar_pieza(self._publicada(autorizacion_responsable=""))
        self.assertTrue(any("sin responsable y fecha" in m for m in motivos), motivos)

    def test_publicada_sin_url_no_entra(self):
        motivos = fail_closed.revisar_pieza(self._publicada(url_publicada=""))
        self.assertTrue(any("no es trazable" in m for m in motivos), motivos)


class TestSeReportanTodosLosMotivos(unittest.TestCase):
    def test_el_rechazo_lista_todo_lo_que_falta(self):
        """Descubrir los fallos de uno en uno cuesta una ronda por fallo."""
        p = pieza_valida()
        p["claims"][0]["fuentes"] = []
        p["contenido_hash_sha256"] = None
        p["titulo_de_trabajo"] = ""
        with self.assertRaises(fail_closed.EscrituraRechazada) as ctx:
            fail_closed.asegurar_escribible(p)
        self.assertGreaterEqual(len(ctx.exception.motivos), 3)


class TestConfiguracion(unittest.TestCase):
    """Requisito 4: sin variables, CONFIGURATION_REQUIRED y ninguna conexion."""

    def test_sin_variables_es_configuration_required(self):
        info = config.estado("lectura", entorno={})
        self.assertEqual(info["estado"], config.CONFIGURACION_REQUERIDA)
        self.assertIn(config.VAR_URL, info["faltan"])

    def test_escritura_exige_la_clave_de_servicio(self):
        env = {config.VAR_URL: "https://ejemplo.supabase.co", config.VAR_ANON: "x"}
        info = config.estado("escritura", entorno=env)
        self.assertEqual(info["estado"], config.CONFIGURACION_REQUERIDA)
        self.assertIn(config.VAR_SERVICE_ROLE, info["faltan"])

    def test_configuracion_completa_se_reconoce(self):
        env = {config.VAR_URL: "https://ejemplo.supabase.co",
               config.VAR_ANON: "x", config.VAR_SERVICE_ROLE: "y"}
        self.assertTrue(config.listo("escritura", entorno=env))

    def test_una_url_que_no_es_supabase_no_se_acepta_en_silencio(self):
        env = {config.VAR_URL: "https://algo.example.com",
               config.VAR_ANON: "x", config.VAR_SERVICE_ROLE: "y"}
        with self.assertRaises(config.ConfiguracionInvalida):
            config.estado("escritura", entorno=env)

    def test_el_proyecto_de_la_otra_cuenta_se_rechaza(self):
        """La decision del fundador excluye expresamente ese proyecto; una
        variable copiada por inercia no debe crear la dependencia sin ruido."""
        env = {config.VAR_URL: f"https://{config.PROYECTO_EXCLUIDO}.supabase.co",
               config.VAR_ANON: "x", config.VAR_SERVICE_ROLE: "y"}
        with self.assertRaises(config.ConfiguracionInvalida) as ctx:
            config.estado("escritura", entorno=env)
        self.assertIn("legallmente-alt", str(ctx.exception))

    def test_nunca_se_devuelve_un_cliente_todavia(self):
        with self.assertRaises(NotImplementedError):
            config.cliente("lectura", entorno={})

    def test_el_informe_no_imprime_ninguna_credencial(self):
        import os
        os.environ[config.VAR_ANON] = "CLAVE-SECRETA-DE-PRUEBA"
        try:
            texto = config.informe()
        finally:
            del os.environ[config.VAR_ANON]
        self.assertNotIn("CLAVE-SECRETA-DE-PRUEBA", texto)
        self.assertIn("presente", texto)


class TestLasDosBarrerasDicenLoMismo(unittest.TestCase):
    """Si Python y SQL divergen, la divergencia es el fallo."""

    def test_los_estados_de_claim_coinciden(self):
        for estado in fail_closed.ESTADOS_CLAIM:
            self.assertIn(estado, MIGRACION, f"la migracion no conoce el estado {estado}")

    def test_los_alcances_coinciden(self):
        for alcance in fail_closed.ALCANCES:
            self.assertIn(alcance, MIGRACION, f"la migracion no conoce el alcance {alcance}")

    def test_los_campos_de_aprobacion_coinciden(self):
        for campo in fail_closed.CAMPOS_APROBACION:
            self.assertIn(campo, MIGRACION)

    def test_el_minimo_de_capa_a_coincide(self):
        self.assertIn(f"array_length(jurisdiccion, 1) >= {fail_closed.MINIMO_JURISDICCIONES_CAPA_A}",
                      MIGRACION)

    def test_el_minimo_de_capa_a_coincide_con_el_motor_de_temas(self):
        """La otra copia del mismo numero vive en content/topics."""
        ruta = AQUI.parent / "content" / "topics" / "transversality.py"
        texto = ruta.read_text(encoding="utf-8")
        self.assertIn(f"MINIMO_JURISDICCIONES_COMPARADAS = {fail_closed.MINIMO_JURISDICCIONES_CAPA_A}",
                      texto)


class TestLaMigracionEsFailClosed(unittest.TestCase):
    def test_rls_activado_en_todas_las_tablas(self):
        tablas = ("piezas", "claims", "fuentes", "investigaciones",
                  "piezas_derivadas", "metricas", "aprendizajes")
        for t in tablas:
            with self.subTest(tabla=t):
                self.assertRegex(MIGRACION,
                                 rf"alter table legalmente\.{t}\s+enable row level security")

    def test_no_hay_policy_de_lectura_sobre_tablas_base(self):
        """Sin policies, RLS deniega. Una policy permisiva aqui abriria las
        fuentes y la investigacion al navegador."""
        self.assertNotIn("create policy", MIGRACION.lower())

    def test_solo_la_vista_es_legible_desde_fuera(self):
        self.assertIn("grant select on legalmente.piezas_publicables to anon, authenticated",
                      MIGRACION)
        for tabla in ("piezas", "claims", "fuentes", "investigaciones"):
            self.assertRegex(MIGRACION, rf"revoke all on legalmente\.{tabla}\s+from anon, authenticated")

    def test_la_vista_exige_las_cuatro_condiciones(self):
        vista = MIGRACION[MIGRACION.index("create or replace view"):]
        for condicion in ("publicacion = 'PUBLISHED'", "gate_global_arte = 'ABIERTO'",
                          "contenido_hash_sha256 is not null",
                          "autorizacion_publicacion = 'AUTORIZADA'"):
            self.assertIn(condicion, vista)

    def test_no_hay_tablas_de_pii_ni_de_pagos(self):
        """Requisito 7: nada de PII, documentos, casos personales ni pagos."""
        prohibidas = ("create table legalmente.usuarios", "create table legalmente.clientes",
                      "create table legalmente.pagos", "create table legalmente.documentos",
                      "create table legalmente.casos")
        for p in prohibidas:
            self.assertNotIn(p, MIGRACION.lower())

    def test_no_se_usa_supabase_storage(self):
        """Requisito 8: nada de Storage hasta cerrar privacidad y retencion."""
        self.assertNotIn("storage.buckets", MIGRACION.lower())
        self.assertNotIn("storage.objects", MIGRACION.lower())

    def test_los_triggers_del_minimo_existen(self):
        for fn in ("fn_gate_global_es_el_minimo", "fn_apto_exige_fuente_nivel_1",
                   "fn_published_exige_derivada"):
            self.assertIn(fn, MIGRACION)

    def test_las_funciones_fijan_search_path(self):
        """Sin search_path fijo, una funcion security-sensitive es secuestrable."""
        self.assertEqual(MIGRACION.count("set search_path = legalmente, pg_temp"),
                         MIGRACION.count("language plpgsql"))


class TestElSeedEsRealmenteSintetico(unittest.TestCase):
    def test_todo_content_id_lleva_el_prefijo(self):
        for p in seed_sintetico.piezas():
            self.assertTrue(p["content_id"].startswith(seed_sintetico.PREFIJO))

    def test_ninguna_url_apunta_a_un_dominio_real(self):
        """example.invalid esta reservado por RFC 2606: no resuelve nunca."""
        for p in seed_sintetico.piezas():
            for c in p["claims"]:
                for f in c["fuentes"]:
                    if f.get("url"):
                        self.assertIn("example.invalid", f["url"])

    def test_ningun_revisor_parece_una_persona(self):
        for p in seed_sintetico.piezas():
            for c in p["claims"]:
                revisor = c.get("revision_revisor")
                if revisor:
                    self.assertTrue(revisor.startswith("rol:"), revisor)

    def test_ninguna_pieza_sintetica_llega_a_published(self):
        """Un seed que simule una publicacion ensena a saltarse la
        autorizacion humana."""
        for p in seed_sintetico.piezas():
            self.assertEqual(p["publicacion"], "NOT_PUBLISHED")

    def test_el_hash_del_seed_es_real_no_una_constante(self):
        """Un hash inventado haria pasar el camino feliz sin demostrar nada."""
        import hashlib
        p = seed_sintetico.pieza_con_gate_abierto()
        texto = p["claims"][0]["texto_exacto"]
        self.assertEqual(p["contenido_hash_sha256"],
                         hashlib.sha256(texto.encode("utf-8")).hexdigest())

    def test_todo_texto_sintetico_se_declara_como_tal(self):
        for p in seed_sintetico.piezas():
            for c in p["claims"]:
                self.assertIn("DATO SINTETICO", c["texto_exacto"])

    def test_el_seed_pasa_su_propia_barrera(self):
        for p in seed_sintetico.piezas():
            self.assertEqual(fail_closed.revisar_pieza(p), [], p["content_id"])


class TestNoHaySecretosEnElRepositorio(unittest.TestCase):
    def test_ningun_archivo_del_almacen_lleva_una_clave(self):
        sospechosos = re.compile(r"(eyJ[A-Za-z0-9_-]{20,}|sbp_[A-Za-z0-9]{20,}|"
                                 r"service_role_key\s*=\s*['\"][A-Za-z0-9]{10,})")
        for ruta in sorted(AQUI.rglob("*")):
            if ruta.is_file() and ruta.suffix in (".py", ".sql", ".md"):
                with self.subTest(archivo=ruta.name):
                    self.assertIsNone(sospechosos.search(ruta.read_text(encoding="utf-8")))


if __name__ == "__main__":
    unittest.main()
