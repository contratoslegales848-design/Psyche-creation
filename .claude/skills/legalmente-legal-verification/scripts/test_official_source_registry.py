"""Integridad del registro oficial unico y de las fuentes que lo invocan.

El registro (`references/official-source-registry.json`) es la unica autoridad
sobre que hostname puede respaldar que organismo, con que tipo de fuente y en
que jurisdiccion. Si el registro se corrompe, todo el control fail-closed de la
skill se corrompe con el: una entrada mal formada puede conceder Nivel 1 a una
fuente que no lo merece.

Estas pruebas cubren dos planos distintos a proposito:

- El registro EN SI: identificadores, autoridades, jurisdicciones, URLs, sin
  duplicados. Si esto falla, no hay que mirar los packets: hay que arreglar el
  registro.
- El USO del registro desde las fuentes reales de `content/claim-packets/`:
  resolucion, verificacion y territorio. Aqui se comprueba que nadie use una
  fuente fuera del territorio que el registro le autoriza.

Sin red. Deterministas.
"""

import importlib.util
import json
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
REPO = SCRIPTS.parent.parent.parent.parent
PACKETS_DIR = REPO / "content" / "claim-packets"


def _cargar_validador():
    """El validador se llama con guiones, asi que no es importable con `import`."""
    ruta = SCRIPTS / "validate-claim-packet.py"
    spec = importlib.util.spec_from_file_location("vcp_registry_tests", ruta)
    if spec is None or spec.loader is None:  # pragma: no cover - defensivo
        raise RuntimeError(f"no se pudo cargar el validador desde {ruta}")
    modulo = importlib.util.module_from_spec(spec)
    sys.modules["vcp_registry_tests"] = modulo
    spec.loader.exec_module(modulo)
    return modulo


V = _cargar_validador()
REGISTRO = V.load_official_source_registry()
ENTRADAS = REGISTRO["sources"] if isinstance(REGISTRO, dict) else REGISTRO

TIPOS_OFICIALES = set(V.TIPOS_FUENTE_OFICIAL)


def _packets():
    if not PACKETS_DIR.is_dir():
        return []
    return sorted(PACKETS_DIR.glob("*.json"))


def _fuentes_reales():
    """Toda fuente declarada en los claim packets del repositorio."""
    for ruta in _packets():
        datos = json.loads(ruta.read_text(encoding="utf-8"))
        for claim in datos.get("claims", []):
            for fuente in claim.get("fuentes", []):
                yield ruta.name, claim["claim_id"], fuente


class TestIntegridadDelRegistro(unittest.TestCase):
    """El registro en si mismo, antes de que nadie lo use."""

    def test_identificadores_unicos(self):
        ids = [e["id"] for e in ENTRADAS]
        duplicados = {i for i in ids if ids.count(i) > 1}
        self.assertEqual(duplicados, set(), f"ids repetidos: {duplicados}")

    def test_toda_entrada_declara_autoridad(self):
        """Sin organismo canonico, la comparacion exacta no puede hacerse."""
        for e in ENTRADAS:
            with self.subTest(id=e["id"]):
                self.assertTrue(str(e.get("organismo_canonico", "")).strip(),
                                "organismo_canonico vacio")

    def test_toda_entrada_declara_jurisdiccion(self):
        """Una entrada sin jurisdiccion no puede limitar el territorio de nada."""
        for e in ENTRADAS:
            with self.subTest(id=e["id"]):
                juris = e.get("jurisdicciones")
                self.assertIsInstance(juris, list)
                self.assertTrue(juris, "lista de jurisdicciones vacia")
                for j in juris:
                    self.assertTrue(str(j).strip(), "jurisdiccion vacia")

    def test_tipos_de_fuente_permitidos_son_del_enum_cerrado(self):
        for e in ENTRADAS:
            with self.subTest(id=e["id"]):
                tipos = e.get("tipos_fuente_permitidos")
                self.assertTrue(tipos, "sin tipos_fuente_permitidos")
                for t in tipos:
                    self.assertIn(t, V.VALID_TIPO_FUENTE)

    def test_los_hostnames_son_parseables_y_no_vacios(self):
        for e in ENTRADAS:
            with self.subTest(id=e["id"]):
                hosts = e.get("hostnames")
                self.assertTrue(hosts, "sin hostnames")
                for h in hosts:
                    self.assertTrue(str(h).strip())
                    self.assertNotIn("/", h, "el hostname no debe llevar ruta")
                    self.assertNotIn(" ", h)

    def test_ningun_hostname_pertenece_a_dos_entradas(self):
        """Un mismo dominio con dos organismos haria ambigua la resolucion."""
        visto = {}
        for e in ENTRADAS:
            for h in e.get("hostnames", []):
                clave = h.strip().lower()
                self.assertNotIn(clave, visto,
                    f"hostname '{clave}' declarado por '{e['id']}' y por '{visto.get(clave)}'")
                visto[clave] = e["id"]

    def test_ningun_organismo_canonico_se_repite(self):
        nombres = [V.normalize_org(e["organismo_canonico"]) for e in ENTRADAS]
        dup = {n for n in nombres if nombres.count(n) > 1}
        self.assertEqual(dup, set(), f"organismos repetidos: {dup}")

    def test_los_alias_no_colisionan_con_otro_organismo_canonico(self):
        """Un alias que coincida con el canonico de otra entrada permitiria
        declarar el organismo equivocado sin que el validador lo note."""
        canonicos = {V.normalize_org(e["organismo_canonico"]): e["id"] for e in ENTRADAS}
        for e in ENTRADAS:
            for alias in e.get("organismo_aliases", []) or []:
                duenio = canonicos.get(V.normalize_org(alias))
                if duenio is not None:
                    self.assertEqual(duenio, e["id"],
                        f"el alias '{alias}' de '{e['id']}' es el canonico de '{duenio}'")

    def test_las_cuatro_autoridades_nuevas_estan_registradas(self):
        """AEPD, INAI, SIC y OIT, anadidas el 2026-09-03 por orden del fundador."""
        ids = {e["id"] for e in ENTRADAS}
        for esperado in ("aepd-es", "inai-org-mx", "sic-gov-co", "ilo-org"):
            self.assertIn(esperado, ids)

    def test_la_oit_no_respalda_ninguna_jurisdiccion_nacional(self):
        """Un convenio solo obliga en el pais que lo ratifico: la entrada de la
        OIT debe respaldar un ambito internacional, nunca un pais suelto."""
        oit = next(e for e in ENTRADAS if e["id"] == "ilo-org")
        self.assertEqual(oit["ambito"], "SUPRANACIONAL")
        for j in oit["jurisdicciones"]:
            self.assertNotIn(V.normalize_country(j),
                             {V.normalize_country(x) for x in ("España", "México", "Colombia", "Argentina")})


class TestUsoDelRegistroEnFuentesReales(unittest.TestCase):
    """Como las fuentes de content/claim-packets/ invocan el registro."""

    def test_hay_packets_que_auditar(self):
        self.assertTrue(_packets(), "no se encontro ningun claim packet")

    def test_toda_fuente_oficial_con_registro_resuelve_a_una_entrada_real(self):
        for archivo, claim_id, f in _fuentes_reales():
            rid = f.get("registro_oficial_id")
            if rid is None:
                continue
            with self.subTest(archivo=archivo, fuente=f["id"]):
                self.assertIn(rid, {e["id"] for e in ENTRADAS},
                              f"registro_oficial_id '{rid}' no existe en el registro")

    def test_ninguna_fuente_se_usa_fuera_del_territorio_autorizado(self):
        """La regla que impide que una fuente espanola cubra Mexico, y que una
        fuente de la UE cubra Espana como jurisdiccion nacional."""
        por_id = {e["id"]: e for e in ENTRADAS}
        for archivo, claim_id, f in _fuentes_reales():
            rid = f.get("registro_oficial_id")
            if rid is None or rid not in por_id:
                continue
            autorizadas = {V.normalize_country(j) for j in por_id[rid]["jurisdicciones"]}
            declaradas = {V.normalize_country(j) for j in f.get("jurisdicciones_cubiertas", [])}
            with self.subTest(archivo=archivo, fuente=f["id"]):
                self.assertTrue(declaradas <= autorizadas,
                    f"{f['id']} declara {sorted(declaradas - autorizadas)}, "
                    f"fuera de lo autorizado para '{rid}' ({sorted(autorizadas)})")

    def test_toda_fuente_declara_fecha_de_consulta_valida(self):
        for archivo, claim_id, f in _fuentes_reales():
            with self.subTest(archivo=archivo, fuente=f["id"]):
                self.assertTrue(V.is_valid_iso_date(f.get("fecha_consulta")),
                                f"fecha_consulta invalida: {f.get('fecha_consulta')!r}")

    def test_toda_url_declarada_es_parseable(self):
        for archivo, claim_id, f in _fuentes_reales():
            url = f.get("url")
            if not url:
                continue
            with self.subTest(archivo=archivo, fuente=f["id"]):
                self.assertIsNotNone(V.parse_official_url(url), f"URL rechazada: {url}")

    def test_una_fuente_sin_verificar_jamas_alcanza_nivel_1(self):
        """El control central: sin texto leido y vigencia comprobada, ninguna
        fuente puede sostener APTO_PARA_NARRATIVA por muy oficial que parezca."""
        for archivo, claim_id, f in _fuentes_reales():
            v = f.get("verificacion_fuente", {})
            if v.get("texto_exacto_consultado") and v.get("vigencia_comprobada"):
                continue
            with self.subTest(archivo=archivo, fuente=f["id"]):
                self.assertNotEqual(V.compute_fuente_nivel(f), 1,
                    f"{f['id']} alcanza Nivel 1 sin lectura ni vigencia comprobadas")

    def test_ninguna_fuente_se_declara_dos_veces_en_el_mismo_claim(self):
        for ruta in _packets():
            datos = json.loads(ruta.read_text(encoding="utf-8"))
            for claim in datos.get("claims", []):
                ids = [f["id"] for f in claim.get("fuentes", [])]
                with self.subTest(archivo=ruta.name, claim=claim["claim_id"]):
                    self.assertEqual(len(ids), len(set(ids)), f"fuentes duplicadas: {ids}")


class TestProhibicionDeFalsaUniversalizacion(unittest.TestCase):
    """El control que faltaba: no declarar cobertura panhispanica con fuentes
    de un solo pais.

    Es el hallazgo del lote de diez: cuatro piezas venian declaradas
    'Panhispanico' aportando solo fuentes mexicanas. Esta prueba lo convierte en
    una barrera automatica en vez de un juicio que hay que recordar hacer.
    """

    MIN_PAISES_CAPA_A = 3

    def _paises_realmente_cubiertos(self, claim):
        paises = set()
        for f in claim.get("fuentes", []):
            for j in f.get("jurisdicciones_cubiertas", []):
                paises.add(V.normalize_country(j))
        return paises

    def test_capa_a_exige_tres_paises_con_fuente_propia(self):
        for ruta in _packets():
            datos = json.loads(ruta.read_text(encoding="utf-8"))
            for claim in datos.get("claims", []):
                if claim.get("alcance") != "CAPA_A_TRANSVERSAL":
                    continue
                revisadas = claim.get("jurisdicciones_revisadas") or []
                with self.subTest(archivo=ruta.name, claim=claim["claim_id"]):
                    self.assertGreaterEqual(len(revisadas), self.MIN_PAISES_CAPA_A,
                        "Capa A con menos de 3 jurisdicciones revisadas")
                    for entrada in revisadas:
                        self.assertTrue(entrada.get("fuente_ids"),
                            f"{entrada.get('pais')} declarado sin fuente_ids propios")

    def test_ningun_claim_transversal_se_sostiene_en_un_solo_pais(self):
        """El corazon de la prohibicion: contar paises REALMENTE cubiertos por
        las fuentes, no paises nombrados en la prosa."""
        for ruta in _packets():
            datos = json.loads(ruta.read_text(encoding="utf-8"))
            for claim in datos.get("claims", []):
                if claim.get("alcance") != "CAPA_A_TRANSVERSAL":
                    continue
                paises = self._paises_realmente_cubiertos(claim)
                with self.subTest(archivo=ruta.name, claim=claim["claim_id"]):
                    self.assertGreaterEqual(len(paises), self.MIN_PAISES_CAPA_A,
                        f"declarado transversal pero sus fuentes solo cubren {sorted(paises)}")

    def test_un_claim_sin_alcance_determinado_nunca_esta_apto(self):
        """NO_DETERMINADO significa falta de investigacion: no puede ir mas
        alla de REQUIERE_INVESTIGACION."""
        for ruta in _packets():
            datos = json.loads(ruta.read_text(encoding="utf-8"))
            for claim in datos.get("claims", []):
                if claim.get("alcance") != "NO_DETERMINADO":
                    continue
                with self.subTest(archivo=ruta.name, claim=claim["claim_id"]):
                    self.assertEqual(claim.get("estado"), "REQUIERE_INVESTIGACION")
                    self.assertEqual(claim.get("gate_arte"), "CERRADO")

    def test_las_cuatro_piezas_monopais_siguen_sin_declararse_transversales(self):
        """Fija el hallazgo del lote: LM-EVG-002, LM-EVG-003, LM-CORP-002 y
        LM-CORP-004 llegaron declaradas panhispanicas con fuentes de un solo
        pais. Si alguien las promueve sin anadir jurisdicciones, esto falla."""
        esperadas = {"LM-EVG-002", "LM-CORP-002", "LM-CORP-004", "LM-EVG-003"}
        vistas = set()
        for ruta in _packets():
            datos = json.loads(ruta.read_text(encoding="utf-8"))
            if datos.get("piece_id") not in esperadas:
                continue
            vistas.add(datos["piece_id"])
            for claim in datos.get("claims", []):
                with self.subTest(pieza=datos["piece_id"]):
                    self.assertNotEqual(claim.get("alcance"), "CAPA_A_TRANSVERSAL",
                        "promovida a transversal sin ampliar jurisdicciones")
                    paises = self._paises_realmente_cubiertos(claim)
                    self.assertLessEqual(len(paises), 1,
                        f"ya cubre {sorted(paises)}: actualiza esta prueba y el handoff")
        self.assertEqual(vistas, esperadas, f"faltan piezas del lote: {esperadas - vistas}")


class TestGatesDelLote(unittest.TestCase):
    def test_ningun_packet_del_lote_tiene_el_gate_abierto(self):
        for ruta in _packets():
            datos = json.loads(ruta.read_text(encoding="utf-8"))
            with self.subTest(archivo=ruta.name):
                self.assertEqual(datos.get("gate_global_arte"), "CERRADO")
                for claim in datos.get("claims", []):
                    self.assertEqual(claim.get("gate_arte"), "CERRADO")

    def test_ninguna_revision_humana_del_lote_esta_aprobada(self):
        """El modelo nunca se autoaprueba: todas nacen PENDIENTE."""
        for ruta in _packets():
            datos = json.loads(ruta.read_text(encoding="utf-8"))
            for claim in datos.get("claims", []):
                with self.subTest(archivo=ruta.name, claim=claim["claim_id"]):
                    self.assertEqual(claim["revision_humana"]["estado"], "PENDIENTE")
                    self.assertIsNone(claim["revision_humana"]["revisor"])


if __name__ == "__main__":
    unittest.main()
