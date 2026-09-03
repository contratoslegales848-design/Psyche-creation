"""Integridad adversarial del registro oficial único.

El registro es la pieza de la que cuelga todo lo demás: si una entrada miente,
el validador acepta como Nivel 1 una fuente que no lo es, y el gate de arte se
abre sobre evidencia inexistente. Estas pruebas no comprueban que el registro
"esté bien escrito": comprueban que NO se pueda usar para colar autoridad.

Tres ejes se mantienen deliberadamente separados y ninguna prueba los colapsa:

  identidad  — el dominio pertenece al organismo declarado
  contenido  — un texto jurídico concreto fue leído literalmente en ese dominio
  vigencia   — el organismo sigue existiendo y siendo competente

Verificar el primero NO acredita los otros dos. Un registro que confundiera
identidad con contenido convertiría "el dominio es el correcto" en "la norma
dice lo que afirmo", que es precisamente el fallo que este proyecto no puede
permitirse.

Sin red. Determinista. Solo lee el registro y el validador reales.
"""

import importlib.util
import json
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
REGISTRY_PATH = SKILL / "references" / "official-source-registry.json"


def _cargar_validador():
    """El validador se llama con guiones; no es importable por nombre."""
    ruta = SKILL / "scripts" / "validate-claim-packet.py"
    spec = importlib.util.spec_from_file_location("validate_claim_packet", ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


V = _cargar_validador()
REGISTRY = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
SOURCES = REGISTRY["sources"]

# Los 26 identificadores que ya existían en el registro antes de esta
# convergencia. Se listan literalmente, no se derivan del propio archivo: una
# lista derivada no puede detectar que el archivo perdió una entrada.
IDS_PRESERVADOS = [
    "boe-es", "poderjudicial-es", "congreso-es", "senado-es",
    "diputados-gob-mx", "senado-gob-mx", "dof-gob-mx", "scjn-gob-mx",
    "gob-mx-generico", "congresoqroo-gob-mx", "infoleg-gob-ar",
    "argentina-gob-ar-normativa", "csjn-gov-ar", "boletinoficial-gob-ar",
    "minjus-gob-pe", "spij-minjus-gob-pe", "tc-gob-pe", "pj-gob-pe", "bcn-cl",
    "funcionpublica-gov-co", "corteconstitucional-gov-co", "eur-lex-europa-eu",
    "secretariasenado-gov-co", "tribunalconstitucional-es", "oas-org",
    "corteidh-or-cr",
]

# Ámbitos que por definición no pueden respaldar el derecho interno de un país.
AMBITOS_NO_NACIONALES = {"SUPRANACIONAL", "INTERNACIONAL"}
JURISDICCIONES_NO_NACIONALES = {
    "unión europea", "sistema interamericano", "ámbito internacional",
    "sistema universal", "organización de los estados americanos",
}


class TestPreservacion(unittest.TestCase):
    """Una convergencia que borra entradas es una regresión silenciosa."""

    def test_ninguna_entrada_previa_desaparecio(self):
        ids = {s["id"] for s in SOURCES}
        faltan = [i for i in IDS_PRESERVADOS if i not in ids]
        self.assertEqual(faltan, [], f"el registro perdió entradas: {faltan}")

    def test_el_registro_solo_crece_por_adicion(self):
        self.assertGreaterEqual(len(SOURCES), len(IDS_PRESERVADOS))

    def test_los_ids_son_unicos(self):
        ids = [s["id"] for s in SOURCES]
        self.assertEqual(len(ids), len(set(ids)))


class TestAdversarialIdentidad(unittest.TestCase):
    """Cada prueba modela una forma concreta de suplantar autoridad."""

    def test_ningun_hostname_pertenece_a_dos_organismos(self):
        """Secuestro de dominio: dos entradas reclamando el mismo host."""
        visto = {}
        for s in SOURCES:
            for h in s["hostnames"]:
                self.assertNotIn(
                    h, visto,
                    f"{h!r} está declarado por {visto.get(h)!r} y por {s['id']!r}")
                visto[h] = s["id"]

    def test_ningun_organismo_canonico_se_repite(self):
        """Dos entradas con el mismo nombre canónico hacen ambigua la
        comprobación de 'organismo_autor'."""
        nombres = [V.normalize_org(s["organismo_canonico"]) for s in SOURCES]
        self.assertEqual(len(nombres), len(set(nombres)))

    def test_ningun_alias_colisiona_con_otra_entrada(self):
        """Suplantación por alias. Se comprueban las dos direcciones: un alias
        no puede ser el canónico de otra entrada NI el alias de otra entrada.
        Solo la primera comprobación dejaría pasar el caso más plausible —
        'AEPD' declarado también como alias de la SIC—, porque 'AEPD' no es el
        nombre canónico de nadie, solo un alias."""
        dueno_de = {}
        for s in SOURCES:
            for nombre in [s["organismo_canonico"], *(s.get("organismo_aliases") or [])]:
                clave = V.normalize_org(nombre)
                previo = dueno_de.setdefault(clave, s["id"])
                self.assertEqual(
                    previo, s["id"],
                    f"el nombre {nombre!r} lo reclaman {previo!r} y {s['id']!r}")

    def test_los_hostnames_son_hosts_desnudos(self):
        """Un 'hostname' con esquema, ruta, puerto, comodín o mayúsculas
        rompería el emparejamiento por límite de subdominio."""
        for s in SOURCES:
            for h in s["hostnames"]:
                with self.subTest(entrada=s["id"], hostname=h):
                    self.assertEqual(h, h.lower())
                    for prohibido in ("/", ":", "*", " ", "?", "@"):
                        self.assertNotIn(prohibido, h)
                    ok, host, _ = V.parse_official_url(f"https://{h}/")
                    self.assertTrue(ok, f"{h!r} no produce una URL parseable")
                    self.assertEqual(host, h)

    def test_gana_siempre_el_hostname_mas_especifico(self):
        """La entrada genérica 'gob.mx' no puede tragarse a las específicas:
        si lo hiciera, cualquier subdominio del Estado mexicano heredaría los
        tipos de fuente permitidos de la genérica."""
        casos = [
            ("https://www.dof.gob.mx/nota.php", "dof-gob-mx"),
            ("https://anticorrupcionybg.gob.mx/datospersonales/", "sabg-buengobierno-mx"),
            ("https://normlex.ilo.org/dyn/nrmlx_es/", "ilo-org"),
            ("https://home.inai.org.mx/", "inai-org-mx"),
            ("https://www.aepd.es/agencia/", "aepd-es"),
            ("https://sedeelectronica.sic.gov.co/", "sic-gov-co"),
        ]
        for url, esperado in casos:
            with self.subTest(url=url):
                entrada = V.match_registry_entry_for_url(url, REGISTRY)
                self.assertIsNotNone(entrada, f"{url} no resolvió a ninguna entrada")
                self.assertEqual(entrada["id"], esperado)

    def test_un_dominio_ajeno_no_resuelve_por_subcadena(self):
        """'boe.es.ejemplo.com' contiene 'boe.es' — y no debe resolver a nada."""
        impostores = [
            "https://boe.es.ejemplo.com/",
            "https://aepd.es.phishing.net/",
            "https://noaepd.es/",
            "https://ilo.org.fake.io/",
            "https://inai.org.mx.mirror.co/",
        ]
        for url in impostores:
            with self.subTest(url=url):
                self.assertIsNone(V.match_registry_entry_for_url(url, REGISTRY))


class TestAdversarialAutoridad(unittest.TestCase):
    def test_ninguna_entrada_permite_un_tipo_de_fuente_inexistente(self):
        for s in SOURCES:
            with self.subTest(entrada=s["id"]):
                permitidos = s["tipos_fuente_permitidos"]
                self.assertTrue(permitidos, "una entrada sin tipos permitidos no autoriza nada")
                self.assertTrue(set(permitidos) <= V.VALID_TIPO_FUENTE)

    def test_ninguna_entrada_supranacional_respalda_un_pais(self):
        """Falsa universalización en dirección inversa: la OIT o EUR-Lex
        respaldando 'España' convertirían una norma internacional en derecho
        interno sin pasar por la ratificación ni por la transposición."""
        for s in SOURCES:
            if s["ambito"] not in AMBITOS_NO_NACIONALES:
                continue
            with self.subTest(entrada=s["id"]):
                for j in s["jurisdicciones"]:
                    self.assertIn(
                        V.normalize_country(j), JURISDICCIONES_NO_NACIONALES,
                        f"{s['id']} (ámbito {s['ambito']}) declara la jurisdicción "
                        f"nacional {j!r}")

    def test_toda_entrada_declara_jurisdiccion_y_autoridad(self):
        for s in SOURCES:
            with self.subTest(entrada=s["id"]):
                self.assertTrue(s.get("jurisdicciones"))
                self.assertTrue(s.get("organismo_canonico"))
                if s.get("verificacion_identidad"):
                    # Convención vigente: toda entrada que declare cómo se
                    # verificó su identidad debe decir en prosa qué se
                    # comprobó y qué NO. Las entradas anteriores a esta
                    # convención no se reescriben aquí — hacerlo mezclaría una
                    # convergencia del registro con una reedición de notas.
                    self.assertTrue(s.get("_nota"), "una entrada sin nota no es auditable")


class TestVigenciaInstitucional(unittest.TestCase):
    """Un organismo extinguido sigue siendo fuente histórica válida, pero no
    puede sostener una afirmación en presente."""

    def test_la_vigencia_declarada_es_de_un_enum_cerrado(self):
        for s in SOURCES:
            v = s.get("vigencia_institucional")
            if v is None:
                continue
            with self.subTest(entrada=s["id"]):
                self.assertIn(v, {"VIGENTE", "HISTORICO"})

    def test_todo_organismo_historico_declara_su_sucesor(self):
        for s in SOURCES:
            if s.get("vigencia_institucional") != "HISTORICO":
                continue
            with self.subTest(entrada=s["id"]):
                self.assertTrue(
                    s.get("sucedido_por"),
                    "un organismo extinguido sin sucesor deja un hueco de competencia")

    def test_la_sucesion_apunta_a_entradas_reales_y_vigentes(self):
        por_id = {s["id"]: s for s in SOURCES}
        for s in SOURCES:
            for sucesor_id in s.get("sucedido_por", []) or []:
                with self.subTest(entrada=s["id"], sucesor=sucesor_id):
                    sucesor = por_id.get(sucesor_id)
                    self.assertIsNotNone(sucesor, "el sucesor no existe en el registro")
                    self.assertEqual(sucesor.get("vigencia_institucional"), "VIGENTE")

    def test_la_sucesion_es_simetrica(self):
        """Si A declara ser sucedida por B, B declara suceder a A. Una cadena
        rota permitiría citar al extinguido sin encontrar nunca al vigente."""
        por_id = {s["id"]: s for s in SOURCES}
        for s in SOURCES:
            for sucesor_id in s.get("sucedido_por", []) or []:
                with self.subTest(entrada=s["id"], sucesor=sucesor_id):
                    self.assertIn(s["id"], por_id[sucesor_id].get("sucede_a", []) or [])

    def test_el_inai_esta_registrado_como_historico(self):
        """Caso concreto y comprobado: el INAI fue extinguido y sus funciones
        de datos personales pasaron a la Secretaría Anticorrupción y Buen
        Gobierno. Citarlo en presente sería afirmar una competencia que ya no
        existe."""
        inai = next(s for s in SOURCES if s["id"] == "inai-org-mx")
        self.assertEqual(inai["vigencia_institucional"], "HISTORICO")
        self.assertIn("sabg-buengobierno-mx", inai["sucedido_por"])


class TestIdentidadNoEsContenido(unittest.TestCase):
    """El eje que este proyecto no puede permitirse colapsar."""

    def test_ninguna_entrada_afirma_haber_verificado_el_contenido(self):
        """SOURCE_CONTENT_VERIFIED significaría que el modelo leyó el texto
        jurídico literal. Hoy WebFetch está EGRESS_BLOCKED: ninguna entrada
        puede afirmarlo, y el día que una lo afirme tendrá que ser un humano
        quien lo sostenga."""
        for s in SOURCES:
            with self.subTest(entrada=s["id"]):
                self.assertNotEqual(
                    s.get("verificacion_contenido"), "SOURCE_CONTENT_VERIFIED")

    def test_la_verificacion_de_identidad_es_de_un_enum_cerrado(self):
        for s in SOURCES:
            v = s.get("verificacion_identidad")
            if v is None:
                continue
            with self.subTest(entrada=s["id"]):
                self.assertIn(
                    v, {"SOURCE_IDENTITY_VERIFIED", "SOURCE_IDENTITY_NOT_VERIFIED"})

    def test_el_registro_documenta_la_distincion(self):
        nota = REGISTRY.get("_nota_verificacion", "")
        self.assertIn("SOURCE_IDENTITY_VERIFIED", nota)
        self.assertIn("SOURCE_CONTENT_VERIFIED", nota)

    def test_identidad_verificada_no_abre_ningun_gate(self):
        """Comprobación estructural, no retórica: el registro no contiene
        ningún campo capaz de conceder aprobación, gate o nivel."""
        prohibidos = ("gate", "aprobado", "approved", "nivel_1", "nivel1",
                      "revision_humana", "publicable")
        for s in SOURCES:
            for clave in s:
                with self.subTest(entrada=s["id"], clave=clave):
                    self.assertNotIn(clave.lower(), prohibidos)


class TestFailClosed(unittest.TestCase):
    """Un registro corrupto nunca puede abrir nada."""

    def test_un_id_duplicado_descarta_ambas_entradas(self):
        falso = {"registry_version": "x", "sources": [
            {"id": "dup", "hostnames": ["a.example"], "organismo_canonico": "A"},
            {"id": "dup", "hostnames": ["b.example"], "organismo_canonico": "B"},
        ]}
        self.assertNotIn("dup", V._build_registry_by_id(falso))

    def test_un_registro_ilegible_produce_registro_vacio(self):
        vacio = V.load_official_source_registry(SKILL / "references" / "no-existe.json")
        self.assertEqual(vacio["sources"], [])

    def test_un_registro_con_forma_inesperada_produce_registro_vacio(self):
        ruta = Path(__file__).resolve().parent / "_registro_malformado_tmp.json"
        ruta.write_text('{"sources": "no soy una lista"}', encoding="utf-8")
        try:
            self.assertEqual(V.load_official_source_registry(ruta)["sources"], [])
        finally:
            ruta.unlink()

    def test_el_registro_real_carga_intacto(self):
        cargado = V.load_official_source_registry(REGISTRY_PATH)
        self.assertEqual(len(cargado["sources"]), len(SOURCES))
        self.assertEqual(len(V._build_registry_by_id(cargado)), len(SOURCES))


if __name__ == "__main__":
    unittest.main()
