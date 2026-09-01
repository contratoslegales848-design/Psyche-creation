import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import importlib
check = importlib.import_module("check-unittest-main-guard-position")


REPO = Path(__file__).resolve().parent.parent

BIEN = '''
import unittest


class TestA(unittest.TestCase):
    def test_x(self):
        pass


class TestB(unittest.TestCase):
    def test_y(self):
        pass


if __name__ == "__main__":
    unittest.main()
'''

MAL = '''
import unittest


class TestA(unittest.TestCase):
    def test_x(self):
        pass


if __name__ == "__main__":
    unittest.main()


class TestB(unittest.TestCase):
    def test_y(self):
        pass
'''

SIN_GUARD = '''
import unittest


class TestA(unittest.TestCase):
    def test_x(self):
        pass
'''


class TestDeteccionDeGuardMalUbicado(unittest.TestCase):
    def test_archivo_correcto_no_reporta_violaciones(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "test_bien.py"
            p.write_text(BIEN, encoding="utf-8")
            self.assertEqual(check.encontrar_violaciones(p), [])

    def test_archivo_con_clase_despues_del_guard_se_detecta(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "test_mal.py"
            p.write_text(MAL, encoding="utf-8")
            problemas = check.encontrar_violaciones(p)
            self.assertEqual(len(problemas), 1)
            self.assertIn("TestB", problemas[0])

    def test_archivo_sin_guard_no_reporta_nada(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "test_sin_guard.py"
            p.write_text(SIN_GUARD, encoding="utf-8")
            self.assertEqual(check.encontrar_violaciones(p), [])

    def test_repo_completo_esta_limpio_ahora(self):
        """Regresion directa: los 3 archivos reales que causaron 614 vs 644
        deben quedar limpios tras la correccion de este PR."""
        problemas = []
        for archivo in check.archivos_de_prueba(REPO):
            problemas.extend(check.encontrar_violaciones(archivo))
        self.assertEqual(problemas, [], "\n".join(problemas))


if __name__ == "__main__":
    unittest.main(verbosity=2)
