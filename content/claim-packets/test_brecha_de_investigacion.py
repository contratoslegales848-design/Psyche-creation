"""El listado de brechas no puede inventar ni ocultar el estado real de una fuente.

Sin red. Determinista.
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))

import brecha_de_investigacion as V  # noqa: E402


def _paquete(claims):
    return {"piece_id": "LM-TEST-000", "claims": claims}


def _claim(claim_id, fuentes, estado="REQUIERE_INVESTIGACION"):
    return {"claim_id": claim_id, "estado": estado, "fuentes": fuentes}


def _fuente(fid, **verificacion):
    v = {"origen_oficial_confirmado": False, "texto_exacto_consultado": False,
         "vigencia_comprobada": False, "observaciones": ""}
    v.update(verificacion)
    obs = v.pop("observaciones")
    return {"id": fid, "titulo": f"fuente {fid}", "verificacion_fuente": {**v, "observaciones": obs}}


class TestFuentesPendientes(unittest.TestCase):
    def test_fuente_completa_no_aparece_como_pendiente(self):
        claim = _claim("c1", [_fuente("f1", origen_oficial_confirmado=True,
                                       texto_exacto_consultado=True, vigencia_comprobada=True)])
        self.assertEqual(V._fuentes_pendientes(claim), [])

    def test_un_solo_booleano_en_false_ya_cuenta_como_pendiente(self):
        claim = _claim("c1", [_fuente("f1", origen_oficial_confirmado=True,
                                       texto_exacto_consultado=True, vigencia_comprobada=False)])
        pendientes = V._fuentes_pendientes(claim)
        self.assertEqual(len(pendientes), 1)
        self.assertEqual(pendientes[0]["campos_pendientes"], ["vigencia_comprobada"])

    def test_fuente_sin_verificacion_alguna_reporta_los_tres_campos(self):
        claim = _claim("c1", [_fuente("f1")])
        pendientes = V._fuentes_pendientes(claim)
        self.assertEqual(set(pendientes[0]["campos_pendientes"]), set(V.CAMPOS_NIVEL_1))

    def test_claim_sin_fuentes_no_falla(self):
        claim = {"claim_id": "c1", "estado": "REQUIERE_INVESTIGACION"}
        self.assertEqual(V._fuentes_pendientes(claim), [])


class TestBrechaDelPaquete(unittest.TestCase):
    def test_solo_reporta_claims_con_algo_pendiente(self):
        paquete = _paquete([
            _claim("completo", [_fuente("f1", origen_oficial_confirmado=True,
                                         texto_exacto_consultado=True, vigencia_comprobada=True)]),
            _claim("incompleto", [_fuente("f2")]),
        ])
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "paquete.json"
            p.write_text(json.dumps(paquete), encoding="utf-8")
            resultado = V.brecha_del_paquete(p)
        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado[0]["claim_id"], "incompleto")

    def test_no_muta_el_archivo_leido(self):
        paquete = _paquete([_claim("c1", [_fuente("f1")])])
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "paquete.json"
            original = json.dumps(paquete)
            p.write_text(original, encoding="utf-8")
            V.brecha_del_paquete(p)
            self.assertEqual(p.read_text(encoding="utf-8"), original)


class TestBrechaDelDirectorio(unittest.TestCase):
    def test_agrega_varios_archivos(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            (tmp / "a.json").write_text(
                json.dumps(_paquete([_claim("a1", [_fuente("fa")])])), encoding="utf-8")
            (tmp / "b.json").write_text(
                json.dumps(_paquete([_claim("b1", [_fuente("fb")])])), encoding="utf-8")
            filas = V.brecha_del_directorio(tmp)
        self.assertEqual({f["claim_id"] for f in filas}, {"a1", "b1"})

    def test_directorio_vacio_no_falla(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(V.brecha_del_directorio(tmp), [])


class TestContraElRepositorioReal(unittest.TestCase):
    """Los claim-packets reales del repo no deben romper el agregador."""

    def test_corre_sin_error_sobre_los_paquetes_reales(self):
        filas = V.brecha_del_directorio(AQUI)
        self.assertIsInstance(filas, list)

    def test_todo_lo_reportado_tiene_estado_de_investigacion_pendiente(self):
        """Si algo aparece en la brecha, su claim no puede estar ya aprobado
        -- eso significaria que el gate se abrio con una fuente incompleta."""
        for fila in V.brecha_del_directorio(AQUI):
            self.assertNotEqual(fila["estado"], "APROBADO")


if __name__ == "__main__":
    unittest.main()
