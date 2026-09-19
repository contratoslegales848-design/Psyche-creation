"""Integridad del descubrimiento automático de pruebas.

CI pasó de una lista escrita a mano (5 de 17 suites, así que memoria, rotación,
motor de rutas e inventario nunca se ejecutaban) a `unittest discover`. Eso
cierra la deriva, pero abre un riesgo nuevo: **el falso verde por ausencia**.
`discover` termina con éxito si no encuentra NADA — un patrón mal escrito, un
módulo que no importa o un directorio equivocado darían CI en verde con cero
pruebas ejecutadas.

Estas comprobaciones son el guardia de ese guardia.
"""

import unittest
from pathlib import Path

VISUAL = Path(__file__).resolve().parent

# Suelo deliberadamente por debajo del total real: protege contra un colapso
# silencioso (a 0, o a un puñado) sin romperse cada vez que se añade una suite.
MINIMO_PRUEBAS = 400
MINIMO_SUITES = 20


def _ficheros_de_prueba():
    return sorted(p.name for p in VISUAL.glob("test_*.py"))


def _descubiertas():
    return unittest.defaultTestLoader.discover(str(VISUAL), pattern="test_*.py")


def _aplanar(suite):
    for t in suite:
        if isinstance(t, unittest.TestSuite):
            yield from _aplanar(t)
        else:
            yield t


class TestDescubrimiento(unittest.TestCase):
    def test_hay_suites_que_descubrir(self):
        self.assertGreaterEqual(len(_ficheros_de_prueba()), MINIMO_SUITES)

    def test_el_descubrimiento_encuentra_pruebas_de_verdad(self):
        """Un CI que ejecuta 0 pruebas y sale en verde es peor que uno rojo."""
        total = len(list(_aplanar(_descubiertas())))
        self.assertGreaterEqual(total, MINIMO_PRUEBAS)

    def test_ningun_modulo_falla_al_importarse(self):
        """unittest convierte un fallo de importación en un _FailedTest. Si se
        colara uno, la suite entera de ese módulo desaparecería del recuento."""
        fallos = [str(t) for t in _aplanar(_descubiertas())
                  if type(t).__name__ == "_FailedTest"
                  or "ModuleImportFailure" in type(t).__name__]
        self.assertEqual(fallos, [])

    def test_todo_fichero_de_prueba_aporta_al_menos_una_prueba(self):
        """Un fichero con un nombre de clase mal escrito no aporta nada y nadie
        se entera: el recuento global sigue siendo alto."""
        descubiertos = {t.__class__.__module__ for t in _aplanar(_descubiertas())}
        vacios = [f for f in _ficheros_de_prueba() if f[:-3] not in descubiertos]
        self.assertEqual(vacios, [])

    def test_cada_fichero_define_al_menos_un_testcase(self):
        import importlib
        sin_casos = []
        for f in _ficheros_de_prueba():
            mod = importlib.import_module(f[:-3])
            if not [v for v in vars(mod).values()
                    if isinstance(v, type) and issubclass(v, unittest.TestCase)
                    and v is not unittest.TestCase]:
                sin_casos.append(f)
        self.assertEqual(sin_casos, [])

    def test_el_patron_de_ci_es_el_mismo_que_aqui(self):
        """Si el workflow cambiara de patrón o de directorio, esta prueba deja
        de reflejar lo que CI ejecuta realmente."""
        wf = (VISUAL.parent / ".github" / "workflows" /
              "legalmente-legal-verification.yml").read_text(encoding="utf-8")
        self.assertIn('unittest discover -p "test_*.py"', wf)
        self.assertIn("working-directory: visual", wf)


if __name__ == "__main__":
    unittest.main()
