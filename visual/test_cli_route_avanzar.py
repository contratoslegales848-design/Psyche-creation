"""route-avanzar conecta route_sync/route_engine al CLI real.

Antes de esto, `avanzar_desde_content_id()` y el resto de `route_sync.py`
estaban implementados y probados en aislamiento, pero ningun camino de
ejecucion los llamaba: `cli.py` no los importaba, `command_center.py`
tampoco. Mismo patron que `rotation.py`: codigo real, sin conectar.

Sin red. Determinista. No toca ningun gate de arte.
"""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

AQUI = Path(__file__).resolve().parent
CLI = AQUI / "cli.py"


def _correr(*args, env_extra=None):
    import os
    env = dict(os.environ)
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        [sys.executable, str(CLI), *args], cwd=str(AQUI),
        capture_output=True, text=True, env=env)


class TestRouteAvanzar(unittest.TestCase):
    def test_avanza_y_persiste_entre_llamadas(self):
        with tempfile.TemporaryDirectory() as tmp:
            matriz = str(Path(tmp) / "route-matrix.json")
            r1 = _correr("route-avanzar", "LM-PIEZA-01-REALES", "--matriz", matriz)
            self.assertEqual(r1.returncode, 0, r1.stderr)
            self.assertIn("proxima_accion", r1.stdout)
            self.assertTrue(Path(matriz).is_file())

            r2 = _correr("route-avanzar", "LM-PIEZA-01-REALES", "--matriz", matriz)
            self.assertEqual(r2.returncode, 0, r2.stderr)
            # La segunda llamada avanza un nodo mas: mas lineas de nodo_actual
            # que la primera, nunca repite la misma arista.
            self.assertGreater(r2.stdout.count("nodo_actual"), r1.stdout.count("nodo_actual"))

    def test_content_id_desconocido_falla_con_claridad(self):
        with tempfile.TemporaryDirectory() as tmp:
            matriz = str(Path(tmp) / "route-matrix.json")
            r = _correr("route-avanzar", "LM-NO-EXISTE-000", "--matriz", matriz)
            self.assertNotEqual(r.returncode, 0)


if __name__ == "__main__":
    unittest.main()
