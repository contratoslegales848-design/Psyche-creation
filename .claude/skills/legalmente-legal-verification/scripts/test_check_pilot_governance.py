#!/usr/bin/env python3
"""Pruebas unitarias para check_pilot_governance.py (control de CI del piloto).

Cubre la semántica corregida del gate de arte (deadlock resuelto, 2026-08-27):
la gobernanza ya NO congela todos los gates en CERRADO — comprueba que cada
gate declarado coincida EXACTAMENTE con el que las reglas fail-closed del
validador permiten, y que el gate global coincida con el agregado canónico.

Recordatorio de semántica: `gate_arte = ABIERTO` habilita narrativa y
producción visual; NO autoriza publicación. La publicación sigue siendo una
decisión humana posterior, externa y separada.

Ningún revisor de prueba puede llevar un nombre real (ver SKILL.md): se usa
siempre REVISOR_FICTICIO_SOLO_PRUEBA.
"""
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_pilot_governance import (  # noqa: E402
    check_pilot_governance,
    load_validator,
    main,
)

# Reutiliza los constructores de claims/piezas ya probados del validador, en
# vez de mantener una segunda batería de fixtures sintéticos aquí.
import test_validate_claim_packet as tvcp  # noqa: E402

SCRIPT = Path(__file__).resolve().parent / "check_pilot_governance.py"
VALIDATOR_SCRIPT = Path(__file__).resolve().parent / "validate-claim-packet.py"
PILOT_DIR = Path(__file__).resolve().parent.parent / "pilot" / "claim-packets"
PILOT_PACKETS = [
    PILOT_DIR / "pieza-01-reales.json",
    PILOT_DIR / "pieza-02-laboral.json",
    PILOT_DIR / "pieza-03-honor.json",
]

REVISOR_FICTICIO = tvcp.REVISOR_FICTICIO
FORBIDDEN_REAL_NAMES = tvcp.FORBIDDEN_REAL_NAMES
vcp = tvcp.vcp

BASE_CLAIM = {
    "claim_id": "c1",
    "estado": "REQUIERE_INVESTIGACION",
    "revision_humana": {"estado": "PENDIENTE"},
    "gate_arte": "CERRADO",
}

BASE_PIECE = {
    "schema_version": "4.0",
    "piece_id": "PIEZA-TEST",
    "claims": [BASE_CLAIM],
    "gate_global_arte": "CERRADO",
}


def run_script(script, path):
    return subprocess.run(
        [sys.executable, str(script), str(path)], capture_output=True, text=True
    )


class TestCheckPilotGovernance(unittest.TestCase):
    """Pruebas históricas sobre paquetes mínimos (claims estructuralmente
    incompletos): el gate canónico de un claim que ni siquiera puede evaluarse
    es CERRADO, que es la lectura fail-closed correcta."""

    def test_pieza_conforme_sin_problemas(self):
        self.assertEqual(check_pilot_governance(copy.deepcopy(BASE_PIECE)), [])

    def test_schema_version_incorrecta(self):
        piece = copy.deepcopy(BASE_PIECE)
        piece["schema_version"] = "3.0"
        problems = check_pilot_governance(piece)
        self.assertTrue(any("schema_version" in p for p in problems))

    def test_gate_global_abierto_rechazado(self):
        piece = copy.deepcopy(BASE_PIECE)
        piece["gate_global_arte"] = "ABIERTO"
        problems = check_pilot_governance(piece)
        self.assertTrue(any("gate_global_arte" in p for p in problems))

    def test_revision_humana_aprobada_rechazada_en_piloto(self):
        piece = copy.deepcopy(BASE_PIECE)
        piece["claims"][0]["revision_humana"]["estado"] = "APROBADO"
        problems = check_pilot_governance(piece)
        self.assertTrue(any("revision_humana" in p for p in problems))

    def test_gate_arte_de_claim_abierto_rechazado(self):
        piece = copy.deepcopy(BASE_PIECE)
        piece["claims"][0]["gate_arte"] = "ABIERTO"
        problems = check_pilot_governance(piece)
        self.assertTrue(any("gate_arte" in p for p in problems))

    def test_revision_humana_aprobada_con_firma_completa_y_gates_cerrados_aceptada(self):
        piece = copy.deepcopy(BASE_PIECE)
        piece["claims"][0]["revision_humana"] = {
            "estado": "APROBADO",
            "revisor": REVISOR_FICTICIO,
            "fecha": "2026-08-26",
            "contenido_hash_sha256": "a" * 64,
        }
        # El claim sigue en REQUIERE_INVESTIGACION, así que el gate canónico es
        # CERRADO y el declarado también: coherente.
        self.assertEqual(check_pilot_governance(piece), [])

    def test_revision_humana_aprobada_con_gate_arte_abierto_rechazada(self):
        piece = copy.deepcopy(BASE_PIECE)
        piece["claims"][0]["revision_humana"] = {
            "estado": "APROBADO",
            "revisor": REVISOR_FICTICIO,
            "fecha": "2026-08-26",
            "contenido_hash_sha256": "a" * 64,
        }
        piece["claims"][0]["gate_arte"] = "ABIERTO"
        problems = check_pilot_governance(piece)
        self.assertTrue(any("gate_arte" in p for p in problems))

    def test_revision_humana_aprobada_sin_hash_valido_rechazada(self):
        piece = copy.deepcopy(BASE_PIECE)
        piece["claims"][0]["revision_humana"] = {
            "estado": "APROBADO",
            "revisor": REVISOR_FICTICIO,
            "fecha": "2026-08-26",
            "contenido_hash_sha256": "no-es-un-hash-hex",
        }
        problems = check_pilot_governance(piece)
        self.assertTrue(any("contenido_hash_sha256" in p for p in problems))

    def test_cli_exit_0_para_pieza_conforme(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "pieza.json"
            path.write_text(json.dumps(BASE_PIECE), encoding="utf-8")
            result = run_script(SCRIPT, path)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_cli_exit_1_para_gate_abierto(self):
        with tempfile.TemporaryDirectory() as tmp:
            piece = copy.deepcopy(BASE_PIECE)
            piece["gate_global_arte"] = "ABIERTO"
            path = Path(tmp) / "pieza.json"
            path.write_text(json.dumps(piece), encoding="utf-8")
            result = run_script(SCRIPT, path)
            self.assertEqual(result.returncode, 1)

    def test_cli_exit_1_sin_argumentos(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT)], capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 1)

    def test_cli_exit_1_para_json_invalido(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "roto.json"
            path.write_text("{not json", encoding="utf-8")
            result = run_script(SCRIPT, path)
            self.assertEqual(result.returncode, 1)


class TestGateCoherenciaConValidador(unittest.TestCase):
    """Deadlock corregido: la gobernanza compara el gate declarado contra el
    gate canónico del validador, en las dos direcciones."""

    # 1 — APTO + PENDIENTE + gate CERRADO → válido
    def test_apto_pendiente_gate_cerrado_valido(self):
        claim = tvcp.base_claim()
        piece = tvcp.base_piece([claim])
        self.assertEqual(claim["estado"], "APTO_PARA_NARRATIVA")
        self.assertEqual(claim["revision_humana"]["estado"], "PENDIENTE")
        self.assertEqual(claim["gate_arte"], "CERRADO")
        self.assertEqual(check_pilot_governance(piece), [])

    # 2 — APTO + APROBADO firmado + hash canónico + gate ABIERTO → válido
    def test_apto_aprobado_firmado_hash_canonico_gate_abierto_valido(self):
        claim = tvcp.approved_claim()
        piece = tvcp.base_piece([claim], gate_global_arte="ABIERTO")
        self.assertEqual(claim["gate_arte"], "ABIERTO")
        self.assertEqual(claim["revision_humana"]["revisor"], REVISOR_FICTICIO)
        self.assertEqual(check_pilot_governance(piece), [])

    # 3 — APTO + APROBADO + hash correcto + gate CERRADO → rechazo
    def test_apto_aprobado_hash_correcto_gate_cerrado_rechazado(self):
        claim = tvcp.approved_claim()
        claim["gate_arte"] = "CERRADO"
        piece = tvcp.base_piece([claim])
        problems = check_pilot_governance(piece)
        self.assertTrue(
            any("obligan a 'ABIERTO'" in p for p in problems),
            f"esperaba rechazo por gate incoherente, se obtuvo: {problems}",
        )

    # 4 — APTO + PENDIENTE + gate ABIERTO → rechazo
    def test_apto_pendiente_gate_abierto_rechazado(self):
        claim = tvcp.base_claim(gate_arte="ABIERTO")
        piece = tvcp.base_piece([claim])
        problems = check_pilot_governance(piece)
        self.assertTrue(any("gate_arte declarado 'ABIERTO'" in p for p in problems))
        self.assertTrue(any("revision_humana.estado" in p for p in problems))

    # 5 — APROBADO sin revisor + gate ABIERTO → rechazo
    def test_aprobado_sin_revisor_gate_abierto_rechazado(self):
        claim = tvcp.approved_claim()
        claim["revision_humana"]["revisor"] = None
        piece = tvcp.base_piece([claim], gate_global_arte="ABIERTO")
        problems = check_pilot_governance(piece)
        self.assertTrue(any("'revisor' no vacío" in p for p in problems))
        self.assertTrue(any("gate_arte declarado 'ABIERTO'" in p for p in problems))

    # 6 — APROBADO sin fecha + gate ABIERTO → rechazo
    def test_aprobado_sin_fecha_gate_abierto_rechazado(self):
        claim = tvcp.approved_claim()
        claim["revision_humana"]["fecha"] = None
        piece = tvcp.base_piece([claim], gate_global_arte="ABIERTO")
        problems = check_pilot_governance(piece)
        self.assertTrue(any("'fecha' ISO válida" in p for p in problems))
        self.assertTrue(any("gate_arte declarado 'ABIERTO'" in p for p in problems))

    # 7 — APROBADO con hash incorrecto + gate ABIERTO → rechazo
    def test_aprobado_hash_incorrecto_gate_abierto_rechazado(self):
        claim = tvcp.approved_claim()
        claim["revision_humana"]["contenido_hash_sha256"] = "b" * 64
        piece = tvcp.base_piece([claim], gate_global_arte="ABIERTO")
        problems = check_pilot_governance(piece)
        self.assertTrue(any("gate_arte declarado 'ABIERTO'" in p for p in problems))
        self.assertTrue(
            any("no coincide con el hash canónico" in p for p in problems),
            f"esperaba el motivo de hash no coincidente, se obtuvo: {problems}",
        )

    # 7b — un hash que cambia porque cambió el contenido invalida la aprobación
    def test_aprobado_y_luego_contenido_modificado_rechazado(self):
        claim = tvcp.approved_claim()
        claim["texto_exacto"] = "Texto alterado despues de aprobar."
        piece = tvcp.base_piece([claim], gate_global_arte="ABIERTO")
        problems = check_pilot_governance(piece)
        self.assertTrue(any("no coincide con el hash canónico" in p for p in problems))

    # 8 — APTO_CON_MATICES + aprobación + gate ABIERTO → rechazo
    def test_apto_con_matices_aprobado_gate_abierto_rechazado(self):
        claim = tvcp.base_claim(estado="APTO_CON_MATICES")
        claim["revision_humana"] = tvcp.base_revision_humana(
            "APROBADO", revisor=REVISOR_FICTICIO, fecha=tvcp.TODAY
        )
        claim["revision_humana"]["contenido_hash_sha256"] = vcp.compute_content_hash(claim)
        claim["gate_arte"] = "ABIERTO"
        piece = tvcp.base_piece([claim], gate_global_arte="ABIERTO")
        problems = check_pilot_governance(piece)
        self.assertTrue(any("gate_arte declarado 'ABIERTO'" in p for p in problems))
        self.assertTrue(
            any("APTO_PARA_NARRATIVA" in p for p in problems),
            f"esperaba el motivo de estado insuficiente, se obtuvo: {problems}",
        )

    # 9 — gate_global_arte incoherente → rechazo (en las dos direcciones)
    def test_gate_global_cerrado_cuando_debe_estar_abierto_rechazado(self):
        claim = tvcp.approved_claim()
        piece = tvcp.base_piece([claim], gate_global_arte="CERRADO")
        problems = check_pilot_governance(piece)
        self.assertTrue(any("gate_global_arte declarado 'CERRADO'" in p for p in problems))

    def test_gate_global_abierto_cuando_debe_estar_cerrado_rechazado(self):
        claim = tvcp.base_claim()
        piece = tvcp.base_piece([claim], gate_global_arte="ABIERTO")
        problems = check_pilot_governance(piece)
        self.assertTrue(any("gate_global_arte declarado 'ABIERTO'" in p for p in problems))

    def test_gate_global_invalido_rechazado(self):
        claim = tvcp.base_claim()
        piece = tvcp.base_piece([claim], gate_global_arte="QUIZAS")
        problems = check_pilot_governance(piece)
        self.assertTrue(any("gate_global_arte inválido" in p for p in problems))

    def test_gate_arte_invalido_rechazado(self):
        claim = tvcp.base_claim(gate_arte="QUIZAS")
        piece = tvcp.base_piece([claim])
        problems = check_pilot_governance(piece)
        self.assertTrue(any("gate_arte inválido" in p for p in problems))

    def test_un_claim_abierto_y_otro_cerrado_no_abren_el_gate_global(self):
        abierto = tvcp.approved_claim()
        cerrado = tvcp.base_claim(claim_id="c2")
        piece = tvcp.base_piece([abierto, cerrado], gate_global_arte="CERRADO")
        self.assertEqual(check_pilot_governance(piece), [])

    def test_claims_vacio_rechazado(self):
        piece = copy.deepcopy(BASE_PIECE)
        piece["claims"] = []
        problems = check_pilot_governance(piece)
        self.assertTrue(any("claims" in p for p in problems))


class TestGobernanciaNoDivergeDelValidador(unittest.TestCase):
    """La gobernanza no puede aceptar lo que el validador rechaza por gate, ni
    al revés: si alguien cambia la regla del gate global en el validador, esta
    prueba se rompe en vez de dejar que ambos programas diverjan en silencio."""

    def _validator_ok(self, piece):
        errors, _warnings = load_validator().validate_piece(copy.deepcopy(piece), "test")
        return not errors

    def test_gobernanza_y_validador_coinciden_en_gate_global(self):
        casos = [
            ("pendiente/cerrado", tvcp.base_piece([tvcp.base_claim()])),
            (
                "aprobado/abierto",
                tvcp.base_piece([tvcp.approved_claim()], gate_global_arte="ABIERTO"),
            ),
            (
                "aprobado/global-cerrado-incoherente",
                tvcp.base_piece([tvcp.approved_claim()], gate_global_arte="CERRADO"),
            ),
            (
                "pendiente/global-abierto-incoherente",
                tvcp.base_piece([tvcp.base_claim()], gate_global_arte="ABIERTO"),
            ),
        ]
        for nombre, piece in casos:
            with self.subTest(caso=nombre):
                gobernanza_ok = check_pilot_governance(copy.deepcopy(piece)) == []
                self.assertEqual(
                    gobernanza_ok,
                    self._validator_ok(piece),
                    f"gobernanza y validador difieren en el caso {nombre!r}",
                )


class TestPaquetesRealesDelPiloto(unittest.TestCase):
    # 10 — los tres paquetes reales vigentes siguen siendo válidos
    def test_tres_paquetes_reales_pasan_gobernanza(self):
        validator = load_validator()
        for path in PILOT_PACKETS:
            with self.subTest(paquete=path.name):
                self.assertTrue(path.is_file(), f"falta el paquete del piloto: {path}")
                piece = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(check_pilot_governance(piece, validator), [])

    def test_tres_paquetes_reales_siguen_pendientes_y_cerrados(self):
        for path in PILOT_PACKETS:
            with self.subTest(paquete=path.name):
                piece = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(piece["gate_global_arte"], "CERRADO")
                for claim in piece["claims"]:
                    self.assertEqual(claim["gate_arte"], "CERRADO")
                    self.assertEqual(claim["revision_humana"]["estado"], "PENDIENTE")

    def test_cli_acepta_los_tres_paquetes_reales(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), *[str(p) for p in PILOT_PACKETS]],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


class TestSimulacionIntegralPieza1(unittest.TestCase):
    """11 — una Pieza 1 aprobada correctamente debe pasar SIMULTÁNEAMENTE el
    validador y la gobernanza. Es la prueba de regresión del deadlock: antes
    del arreglo, ninguna combinación conseguía exit 0 en los dos programas.

    La simulación se construye sobre una copia en memoria; el paquete real del
    repositorio nunca se modifica.
    """

    def _simular_pieza1_aprobada(self):
        validator = load_validator()
        original = json.loads(PILOT_PACKETS[0].read_text(encoding="utf-8"))
        sim = copy.deepcopy(original)
        for claim in sim["claims"]:
            claim["revision_humana"] = {
                "estado": "APROBADO",
                "revisor": REVISOR_FICTICIO,
                "fecha": "2026-08-27",
                "observaciones": "SIMULACION DE PRUEBA — no es una aprobación real.",
                "contenido_hash_sha256": validator.compute_content_hash(claim),
            }
        # Gates y campos derivados calculados con las funciones reales.
        for idx, claim in enumerate(sim["claims"]):
            _e, _w, _t, gate = validator.validate_claim(claim, f"claims[{idx}]")
            claim["gate_arte"] = gate
        sim["estado_agregado"] = validator.compute_estado_agregado(
            [c["estado"] for c in sim["claims"]]
        )
        sim["revisiones_pendientes"] = sorted(
            validator.compute_revisiones_pendientes(sim["claims"])
        )
        sim["gate_global_arte"] = (
            "ABIERTO"
            if all(c["gate_arte"] == "ABIERTO" for c in sim["claims"])
            else "CERRADO"
        )
        return original, sim

    def test_simulacion_aprobada_abre_el_gate_de_arte(self):
        _original, sim = self._simular_pieza1_aprobada()
        self.assertEqual(sim["estado_agregado"], "APTO_PARA_NARRATIVA")
        self.assertEqual(sim["gate_global_arte"], "ABIERTO")
        for claim in sim["claims"]:
            self.assertEqual(claim["gate_arte"], "ABIERTO")

    def test_simulacion_aprobada_pasa_validador_y_gobernanza(self):
        _original, sim = self._simular_pieza1_aprobada()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "pieza-01-simulada.json"
            path.write_text(json.dumps(sim, ensure_ascii=False), encoding="utf-8")

            validador = run_script(VALIDATOR_SCRIPT, path)
            self.assertEqual(
                validador.returncode,
                0,
                f"el validador rechazó la simulación:\n{validador.stdout}{validador.stderr}",
            )

            gobernanza = run_script(SCRIPT, path)
            self.assertEqual(
                gobernanza.returncode,
                0,
                f"la gobernanza rechazó la simulación:\n{gobernanza.stdout}{gobernanza.stderr}",
            )

    def test_simulacion_con_gate_cerrado_es_rechazada_por_ambos(self):
        """La combinación que ANTES estaba obligada (aprobado + gate cerrado)
        ahora la rechazan los dos programas, no solo uno."""
        _original, sim = self._simular_pieza1_aprobada()
        for claim in sim["claims"]:
            claim["gate_arte"] = "CERRADO"
        sim["gate_global_arte"] = "CERRADO"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "pieza-01-simulada-cerrada.json"
            path.write_text(json.dumps(sim, ensure_ascii=False), encoding="utf-8")
            self.assertEqual(run_script(VALIDATOR_SCRIPT, path).returncode, 1)
            self.assertEqual(run_script(SCRIPT, path).returncode, 1)

    def test_el_paquete_real_no_se_modifica_al_simular(self):
        antes = PILOT_PACKETS[0].read_text(encoding="utf-8")
        self._simular_pieza1_aprobada()
        despues = PILOT_PACKETS[0].read_text(encoding="utf-8")
        self.assertEqual(antes, despues)


class TestSinNombresReales(unittest.TestCase):
    """SKILL.md prohíbe nombres reales en fixtures, pruebas y ejemplos. La
    comprobación equivalente del validador cubre fixtures, SKILL.md y
    references/; esta cubre los scripts, que antes quedaban fuera."""

    def test_no_hay_nombres_reales_en_los_scripts(self):
        offenders = []
        for path in sorted(Path(__file__).resolve().parent.glob("*.py")):
            for lineno, line in enumerate(
                path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1
            ):
                # La línea que DECLARA la lista negra contiene los nombres por
                # necesidad; se omite para no reportarse a sí misma.
                if "FORBIDDEN_REAL_NAMES" in line:
                    continue
                for name in FORBIDDEN_REAL_NAMES:
                    if name in line:
                        offenders.append((path.name, lineno, name))
        self.assertEqual(offenders, [], f"Nombres reales encontrados en scripts: {offenders}")


if __name__ == "__main__":
    unittest.main()
