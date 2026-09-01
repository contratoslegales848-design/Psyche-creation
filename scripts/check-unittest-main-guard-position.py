"""Verifica que ningun archivo de pruebas tenga `unittest.main()` a mitad de archivo.

`unittest.main()` llama `sys.exit()`. Si el guard `if __name__ == "__main__":`
aparece antes de que termine el archivo, cualquier `class ...(TestCase)`
definida despues nunca se registra cuando el archivo se ejecuta como script
(`python3 archivo.py`) -- solo se descubre en modo import/discovery
(`python3 -m unittest modulo`). Eso produjo una discrepancia real de conteo
(614 vs 644 casos) en este repositorio: tres archivos tenian el guard antes
de clases finales que quedaban invisibles en modo script.

Este chequeo evita que vuelva a ocurrir: falla si un archivo `test_*.py`
tiene codigo top-level (una definicion de clase o funcion) despues de su
guard `if __name__ == "__main__":`.
"""

import ast
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def _es_guard_main(nodo):
    if not isinstance(nodo, ast.If):
        return False
    test = nodo.test
    if not isinstance(test, ast.Compare):
        return False
    izq = test.left
    return (
        isinstance(izq, ast.Name)
        and izq.id == "__name__"
        and len(test.ops) == 1
        and isinstance(test.ops[0], ast.Eq)
        and len(test.comparators) == 1
        and isinstance(test.comparators[0], ast.Constant)
        and test.comparators[0].value == "__main__"
    )


def encontrar_violaciones(ruta_archivo):
    """Devuelve una lista de mensajes de error; vacia si el archivo esta bien."""
    arbol = ast.parse(ruta_archivo.read_text(encoding="utf-8"), filename=str(ruta_archivo))
    indice_guard = None
    for i, nodo in enumerate(arbol.body):
        if _es_guard_main(nodo):
            indice_guard = i
            break
    if indice_guard is None:
        return []

    problemas = []
    for nodo in arbol.body[indice_guard + 1:]:
        if isinstance(nodo, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            problemas.append(
                f"{ruta_archivo}: '{nodo.name}' (linea {nodo.lineno}) esta definido "
                f"DESPUES de 'if __name__ == \"__main__\":' (linea "
                f"{arbol.body[indice_guard].lineno}). Sera invisible en modo script."
            )
    return problemas


def archivos_de_prueba(raiz=REPO):
    return sorted(raiz.rglob("test_*.py"))


def main():
    todas = []
    for archivo in archivos_de_prueba():
        todas.extend(encontrar_violaciones(archivo))
    if todas:
        for msg in todas:
            print(msg, file=sys.stderr)
        print(f"\n{len(todas)} violacion(es). Mueve el guard 'if __name__ == \"__main__\":' "
              "al final del archivo, despues de todas las clases de prueba.", file=sys.stderr)
        return 1
    print(f"OK: {len(archivos_de_prueba())} archivos de prueba, ningun guard mal ubicado.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
