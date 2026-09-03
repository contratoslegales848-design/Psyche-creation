"""Los claim packets usan el registro oficial como manda el contrato.

Estas pruebas NO comprueban el registro —eso lo hace
`.claude/skills/legalmente-legal-verification/scripts/test_official_source_registry.py`,
que es su dueño único— sino el USO que los packets hacen de él: que cada
`registro_oficial_id` resuelva, que ninguna fuente se invoque fuera del
territorio que tiene autorizado, y que ningún claim se declare transversal
apoyado en un solo país.

Vivían junto al registro y se han traído aquí, junto a los packets, porque
mezclarlas duplicaba diez pruebas de integridad del registro que ya existían
allí. El registro tiene un solo dueño; los packets, otro.

Sin red. Determinista.
"""

import importlib.util
import json
import unittest
from pathlib import Path
from urllib.parse import urlparse

REPO = Path(__file__).resolve().parent.parent
SKILL = REPO / ".claude" / "skills" / "legalmente-legal-verification"
PACKETS_DIR = REPO / "content" / "claim-packets"
REGISTRO_PATH = SKILL / "references" / "official-source-registry.json"

REGISTRO = json.loads(REGISTRO_PATH.read_text(encoding="utf-8"))
ENTRADAS = REGISTRO["sources"]
POR_ID = {e["id"]: e for e in ENTRADAS}

def _cargar_validador():
    ruta = SKILL / "scripts" / "validate-claim-packet.py"
    spec = importlib.util.spec_from_file_location("validate_claim_packet", ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


V = _cargar_validador()
TIPOS_OFICIALES = V.TIPOS_FUENTE_OFICIAL



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
